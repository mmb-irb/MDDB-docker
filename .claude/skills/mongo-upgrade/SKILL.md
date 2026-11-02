---
name: mongo-upgrade
description: Upgrade a node's in-stack MongoDB from 6 to 8 (6.0 -> 7.0 -> 8.0) safely, including multi-terabyte databases. Use when someone asks to upgrade, migrate or update MongoDB / Mongo / the database on an existing MDDB node, when mongodb fails with "UPGRADE PROBLEM … featureCompatibilityVersion", or before redeploying a node created when the repo still used mongo:6.
---

# Upgrade MongoDB from 6 to 8 on a node

The procedure is [readme/mongo-upgrade.md](../../../readme/mongo-upgrade.md). Read it completely first and
follow its steps in order; this skill adds the rules for doing it on a real node, often with terabytes of
data that cannot be recreated.

## Rules

- **No backup, no upgrade.** Raising the FCV (steps 3 and 7) is irreversible except by restoring the backup.
  Do not run a `setFeatureCompatibilityVersion` with `confirm: true` until the user has confirmed, in this
  conversation, where the backup is and that it is complete.
- **Ask before every step that stops something or cannot be undone**: scaling services down, stopping
  `mongod`, each image change, each FCV change. Say what will happen and how to undo it, then wait.
- **Never `docker stack deploy` during the upgrade.** It would put back the compose file's image
  (`mongo:8`) and grace period. Until step 8, change only the `mongodb` service with `docker service update`.
- **Check after every step** with `check.sh` (below) and compare the document counts saved at step 0.
  If anything is unexpected (version, FCV, counts, `Detected unclean shutdown`, a crash loop), stop and
  report; do not improvise a fix on the production database.
- **Before any restart of `mongod`**, the stop grace period must be long (30m): Docker's default 10 s can
  kill a large `mongod` in the middle of its shutdown.
- **Long commands** (backups, copies) run detached on the node (`setsid nohup … > ~/mongo-upgrade.log 2>&1 &`)
  so that a dropped SSH connection does not interrupt them; check the log afterwards.
- **Secrets**: use the credentials already inside the container (as `check.sh` and the guide's `mongo_eval`
  do); never print `.env` or put passwords on a command line.
- The backup method (snapshot, copy, dump) and its location are the user's decision: offer the options in
  the guide's step 2 with the database size and free space from `check.sh`.
- Keep a short log of what was done and when (versions, FCV, counts, backup location), and give it to the
  user at the end.

## Where the node is

From the repository root on the node (with `ssh <alias> '…'` if it is remote):

```bash
bash .claude/skills/mongo-upgrade/check.sh --stack <STACK_NAME>
```

It prints the image, grace period, data folder and free space, `mongod` version, FCV, size, whether the
last start followed an unclean shutdown, and the next step of the guide. It is read-only.

## Not covered

- Podman nodes: the guide's "Podman nodes" section (same steps, container recreated each time).
- A MongoDB outside the stack (`DB_SERVER` pointing elsewhere), replica sets, or sharded clusters: their
  administrators follow MongoDB's official upgrade guides.
