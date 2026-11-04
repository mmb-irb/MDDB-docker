# Upgrade MongoDB from 6 to 8

The `mongodb` service in [**docker-compose.yml**](../docker-compose.yml) now uses `mongo:8`. A node created
before that runs `mongo:6` on data written by MongoDB 6, and **MongoDB 8 refuses to start on that data**.
This guide upgrades such a node safely, including databases of several terabytes.

It covers the in-stack `mongodb` service (a single `mongod`, as defined in this repository) deployed with
**Docker Swarm**; [Podman nodes](#podman-nodes) and [external databases](#external-mongodb) are at the end.

## What you need to know first

Everything below was tested on a throwaway database (6.0.28 → 7.0.45 → 8.0.34):

* MongoDB upgrades **one major version at a time**: **6.0 → 7.0 → 8.0**. After each binary upgrade you
  raise the **featureCompatibilityVersion** (FCV), and the next major version only starts when the FCV is
  the previous one.
* Starting `mongo:8` directly on 6.0 data fails with `UPGRADE PROBLEM: Found an invalid
  featureCompatibilityVersion document … version: "6.0"`. The data is **not** damaged: go back to the
  right image and continue the procedure.
* Changing the image does **not rewrite the data**: each step takes the time of a clean shutdown plus a
  start-up, whatever the size of the database. What takes long with terabytes is the **backup**.
* **Raising the FCV is one-way.** MongoDB asks for `confirm: true` and warns that afterwards *"you will not
  be able to downgrade FCV and binary version without support assistance"*. From that moment, only the
  backup can take you back. Hence: **no backup, no upgrade**.
* Running MongoDB 8.0 with FCV still at 7.0 is reversible: going back to the 7.0 image works. This is
  the safe window to check the services before the last, irreversible step.
* The services' drivers already support MongoDB 8 (REST API `mongodb ^6.21`, VRE lite `^6.18`, services
  monitor `^6.3`, `mddb-database ^6.x`, `pymongo` in utils).
* **Docker stops a container after 10 seconds** and then kills it. A large `mongod` may need longer to shut
  down cleanly; a killed `mongod` recovers on the next start (safe, but it can take a long time). The
  procedure therefore raises the service's stop grace period first.

## ⚠️ Until the node is upgraded: do not redeploy with the new compose file

A `git pull` followed by `docker stack deploy` replaces the image with `mongo:8` and MongoDB will not start.
If you must redeploy the stack before upgrading, keep MongoDB 6 with an override file **outside** the
repository, e.g. `~/mongo-pin.yml`:

```yaml
services:
  mongodb:
    image: mongo:6.0
```

```sh
set -a; source .env; set +a
docker stack deploy -c docker-compose.yml [-c extensions/<ext>.yml ...] -c ~/mongo-pin.yml <stack>
```

## Overview

| Step | What | Downtime | Can be undone by |
|---|---|---|---|
| [0](#0-check-the-starting-point) | Check versions, FCV, size, free space | none | - |
| [1](#1-stop-the-services-that-use-the-database) | Stop the services that use the database | starts here | scaling them up again |
| [2](#2-back-up) | Stop `mongod` cleanly and back it up | yes | - |
| [3](#3-mongodb-7) | `mongo:7.0`, then FCV 7.0 | yes | **only the backup** (after FCV 7.0) |
| [4](#4-mongodb-8) | `mongo:8.0` (FCV stays 7.0) | yes | going back to `mongo:7.0` |
| [5](#5-start-the-services-again-and-check) | Services back, checks | ends here | - |
| [6](#6-trial-period) | Run for some days | none | going back to `mongo:7.0` |
| [7](#7-fcv-80) | FCV 8.0 | none | **only the backup** |
| [8](#8-back-to-the-normal-deployment) | Back to the normal `docker stack deploy` | none | - |

Plan a maintenance window for steps 1 to 5. Its length is mostly the backup time.

In the commands, `<stack>` is your `STACK_NAME`. Load the `.env` values into your shell first (from the
repository root):

```sh
set -a; source .env; set +a
mongo_cid() { docker ps -q -f label=com.docker.swarm.service.name=${STACK_NAME}_mongodb | head -1; }
# run a mongosh command as root, with the credentials already set inside the mongodb container
mongo_eval() { docker exec "$(mongo_cid)" sh -c 'mongosh --quiet -u "$MONGO_INITDB_ROOT_USERNAME" \
  -p "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --eval "$0"' "$1"; }
```

## 0. Check the starting point

With Claude Code, `bash .claude/skills/mongo-upgrade/check.sh --stack "$STACK_NAME"` prints all of this and
the next step. By hand:

```sh
docker service inspect ${STACK_NAME}_mongodb -f '{{.Spec.TaskTemplate.ContainerSpec.Image}} grace={{.Spec.TaskTemplate.ContainerSpec.StopGracePeriod}}'
mongo_eval 'db.version()'
mongo_eval 'db.adminCommand({getParameter: 1, featureCompatibilityVersion: 1}).featureCompatibilityVersion'
mongo_eval 'db.adminCommand({listDatabases: 1}).totalSize / 1e9'     # GB on disk
df -h "$DB_VOLUME_PATH"
```

* The version must be **6.0.x** and the FCV **"6.0"**. If the FCV is `"5.0"` (a node upgraded earlier
  without this step), raise it first: `mongo_eval 'db.adminCommand({setFeatureCompatibilityVersion: "6.0"})'`.
* Save the number of documents per collection, to compare after the upgrade (fast: it reads metadata):

```sh
counts='db.adminCommand({listDatabases: 1}).databases.map(d => d.name)
  .filter(n => !["admin", "config", "local"].includes(n)).forEach(n => { const s = db.getSiblingDB(n);
  s.getCollectionInfos({type: "collection"}).filter(c => !c.name.startsWith("system.")).forEach(c => print(n + "." + c.name + " " + s.getCollection(c.name).estimatedDocumentCount())) })'
mongo_eval "$counts" | sort | tee ~/mongo-counts-before.txt
```

## 1. Stop the services that use the database

Note the current replicas (`docker stack services ${STACK_NAME}`), make sure no loader or workflow job is
running (`docker ps`), then:

```sh
for s in rest vre_lite mongo-backup services_monitor; do
  docker service scale -d ${STACK_NAME}_$s=0 2>/dev/null
done
```

## 2. Back up

Give `mongod` time to shut down cleanly, then stop it:

```sh
docker service update --stop-grace-period 30m ${STACK_NAME}_mongodb
docker service scale ${STACK_NAME}_mongodb=0
docker ps -f label=com.docker.swarm.service.name=${STACK_NAME}_mongodb   # wait until empty
```

With `mongod` stopped, `DB_VOLUME_PATH` holds a consistent copy of the database. Back it up with one of:

| Method | When | How |
|---|---|---|
| **Storage snapshot** | **Best for terabytes**: seconds, whatever the size | LVM / ZFS / storage-array / VM snapshot of the volume holding `DB_VOLUME_PATH`, taken now |
| **Cold copy** | Enough free space elsewhere; time grows with size | `sudo rsync -aHAX --info=progress2 "$DB_VOLUME_PATH"/ /backup/mongo6-$(date +%F)/` |
| **mongodump** | Small databases only (days for terabytes, restore even slower) | Before stopping `mongod`; see [docker-swarm.md](docker-swarm.md#mongodb-backup-service) |

Write down where the backup is and check it is complete (`du -s`, file count) before going on.

## 3. MongoDB 7

```sh
docker service update --image mongo:7.0 --replicas 1 ${STACK_NAME}_mongodb
docker service ps ${STACK_NAME}_mongodb          # wait until Running
mongo_eval 'db.version()'                         # 7.0.x
mongo_eval 'db.adminCommand({getParameter: 1, featureCompatibilityVersion: 1}).featureCompatibilityVersion'   # "6.0"
docker logs "$(mongo_cid)" 2>&1 | grep -c 'Detected unclean shutdown'   # 0: the shutdown was clean
```

Compare a few collection counts with `~/mongo-counts-before.txt`. Then raise the FCV
(**irreversible without the backup**):

```sh
mongo_eval 'db.adminCommand({setFeatureCompatibilityVersion: "7.0", confirm: true})'
```

## 4. MongoDB 8

```sh
docker service update --image mongo:8.0 ${STACK_NAME}_mongodb
docker service ps ${STACK_NAME}_mongodb          # wait until Running
mongo_eval 'db.version()'                         # 8.0.x
mongo_eval 'db.adminCommand({getParameter: 1, featureCompatibilityVersion: 1}).featureCompatibilityVersion'   # "7.0"
```

Save the counts again and compare (no output means identical):

```sh
mongo_eval "$counts" | sort > ~/mongo-counts-after.txt
diff ~/mongo-counts-before.txt ~/mongo-counts-after.txt
```

## 5. Start the services again and check

```sh
docker service scale ${STACK_NAME}_rest=<n> ${STACK_NAME}_vre_lite=1 ...   # the replicas noted in step 1
docker service update --force ${STACK_NAME}_rest   # REST connects to Mongo only at start-up
docker stack services ${STACK_NAME}
docker compose run --rm loader list
```

Check the website, `https://<domain>/api/rest/v1/projects?limit=1` and VRE lite. With Claude Code,
`.claude/skills/deploy-node/verify.sh` does it.

## 6. Trial period

Leave the node running on MongoDB 8.0 with FCV 7.0 for some days. If anything goes wrong, go back:
`docker service update --image mongo:7.0 ${STACK_NAME}_mongodb`.

## 7. FCV 8.0

When you are satisfied (**irreversible without the backup**):

```sh
mongo_eval 'db.adminCommand({setFeatureCompatibilityVersion: "8.0", confirm: true})'
mongo_eval 'db.adminCommand({getParameter: 1, featureCompatibilityVersion: 1}).featureCompatibilityVersion'   # "8.0"
```

## 8. Back to the normal deployment

Now `git pull` and deploy as usual; delete `~/mongo-pin.yml` if you created it. The compose file uses
`mongo:8`, the same major version.

`docker stack deploy` resets the stop grace period to 10 seconds, because the compose file does not set
one. Before any later restart of a large database, raise it again as in step 2.

Keep the backup until you are sure you will not need it.

## If something goes wrong

| Symptom | Meaning | What to do |
|---|---|---|
| `UPGRADE PROBLEM: Found an invalid featureCompatibilityVersion document … version: "6.0"` | `mongo:8` was started on 6.0 data (e.g. a redeploy with the new compose file) | Nothing is damaged. `docker service update --image mongo:6.0 …` (or `mongo:7.0` to continue from step 3) |
| Same message with `version: "7.0"` and a 6.0 image | The FCV is already 7.0 | Use `mongo:7.0` or `mongo:8.0` |
| `Once you have upgraded to 7.0, you will not be able to downgrade FCV…` | The FCV command needs the confirmation | Add `confirm: true` (after checking the backup) |
| `Detected unclean shutdown` in the log, slow start-up | `mongod` was killed before finishing its shutdown | Let the recovery finish; raise the grace period (step 2) before the next restart |
| REST `500`, log `No client` / `ENOTFOUND` | REST started before Mongo was ready | `docker service update --force ${STACK_NAME}_rest` |
| Anything unexpected after an FCV change | - | Stop, keep the logs, restore the backup into `DB_VOLUME_PATH` and start the previous image |

## Podman nodes

The Podman scripts and [podman.md](podman.md) use `mongo_image`, built from `mongo:8.0` (see
[Deploy MongoDB](podman.md#deploy-mongodb)). A node created before still runs `mongo:6`: the procedure is the
same, recreating the container instead of updating a service. Use the official `mongo:7.0` image for step 3
and `mongo_image` for step 4 (**not** `mongo:8`, which now points to newer short-lived releases). Keep each
old container (renamed) as the way back while the FCV allows it:

```sh
# the container's own environment, without putting passwords on a command line
(umask 077; podman inspect mongodb --format '{{range .Config.Env}}{{println .}}{{end}}' \
  | grep -E '^(MONGO_INITDB_|MONGO_PORT|MONGO_VRE_DATABASE|LOADER_DB_|VRE_DB_|REST_DB_|DB_OUTER_PORT)' > ~/mongodb.env)
podman stop -t 1800 mongodb && podman rename mongodb mongodb-6
# the same `podman run … --name mongodb …` you used (same volumes, same --ip), with
#   --env-file ~/mongodb.env instead of the -e options, ending in:
#   docker.io/library/mongo:7.0      then, at step 4, mongo_image
mongo_cid() { echo mongodb; }    # then mongo_eval works as above, through `podman exec`:
mongo_eval() { podman exec mongodb sh -c 'mongosh --quiet -u "$MONGO_INITDB_ROOT_USERNAME" \
  -p "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --eval "$0"' "$1"; }
```

* Run the long steps with `setsid nohup … &` from a normal shell, **never with `systemd-run --user`**: when the
  unit ends, systemd kills every container started from it (and its `fuse-overlayfs`). `mongod` dies without a
  clean shutdown and the container is left without its root filesystem (`/entrypoint.sh: No such file or
  directory`); remove it with `podman rm --storage --force <id>` and create it again.
* REST connects to MongoDB only at start-up: `podman restart rest` after each image change.
* Delete `~/mongodb.env` and the old `mongodb-6` / `mongodb-7` containers once the FCV is 8.0.

Tested on pubperez1 (730 GB): 6.0.27 → 7.0.45 → 8.0.34. Each image change took seconds; counting the
documents (`countDocuments` on every collection) took about 20 minutes.

## External MongoDB

If `DB_SERVER` points to a server outside the stack, its administrators upgrade it, following MongoDB's
own guides for [7.0](https://www.mongodb.com/docs/manual/release-notes/7.0-upgrade-standalone/) and
[8.0](https://www.mongodb.com/docs/manual/release-notes/8.0-upgrade-standalone/) (replica sets have their
own pages). The stack's own `mongodb` service, used by VRE lite, is upgraded with this guide.
