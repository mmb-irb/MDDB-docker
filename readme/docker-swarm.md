# Deploy Docker Swarm

**Docker Swarm** is a native **clustering** and **orchestration tool** for Docker containers. It allows you to **manage** a group of Docker hosts as a **single virtual system**, simplifying container **orchestration**, **deployment**, and **management**. With **Docker Swarm**, you can **scale** up and down, **manage** multiple containers, and ensure **high availability** of your applications.

## Build services

For building the services via **Docker Swarm**, please execute the following instruction from the same folder where the [**docker-compose.yml**](../docker-compose.yml) file is:

First off, go to the root of the project. Then, init **Docker Swarm**:

```sh
docker swarm init
```

**Note:** when a system has **multiple network** interfaces with **different IP** addresses, Docker Swarm requires you to explicitly **specify which IP** address it should use for advertising:

```sh
docker swarm init --advertise-addr <IP_ADDRESS>
```

In order to execute the **long-term** tasks in **Docker Swarm** and the **one-off tasks**, such as the **loader** or the **workflow**, in **Docker Compose**, some of the **networks** are declared as **external** in the **docker-compose.yml** file, so they must be created before the `docker compose build` and the `docker stak deploy`:

```sh
docker network create --driver overlay --attachable web_network
docker network create --driver overlay --attachable data_network
docker network create --driver overlay --attachable minio_network
docker network create --driver overlay --attachable metrics_network
```

> NOTE: In **docker old versions** the instruction for Docker Compose is with hyphen, so instead of `docker compose build`, `docker-compose build` must be typed and executed.

⚠️ In some environments, where the **firewall policies** can be more **restrictives**, the build process can't be **unable to use the network**. In this case, please **enable** all the `# network: host  # Only during build` labels in the [**docker-compose.yml**](../docker-compose.yml) file. ⚠️ 

For building the services via **Docker Compose**, please execute the following instruction:

```sh
docker compose build
```

**Note:** for building **extension** services as well, please execute the following instruction instead:

```sh
docker compose -f docker-compose.yml -f extensions/extension1.yml build
```

⚠️ If `# network: host  # Only during build` labels were enabled in the [**docker-compose.yml**](../docker-compose.yml) file, please **disable** them again **before deploying** for the sake of preserving **network isolation**. ⚠️ 

Export environment variables defined in [**global .env file**](config.md#env-file) and deploy docker stack:

```sh
set -a; source .env; set +a
docker stack deploy -c docker-compose.yml my_stack
```

**Note:** for deploying **extension** services as well, please execute the following instructions instead:

```sh
set -a; source .env; set +a
docker stack deploy -c docker-compose.yml -c extensions/extension1.yml my_stack 
```

### Redeploying a running stack

`docker stack deploy` rewrites every service from the compose files: anything changed by hand with
`docker service update` (a published port, a mount, an environment variable, the replicas, the stop grace
period...) is **lost** at the next deploy. So:

* **Settings of one node only go in `docker-compose.node.yml`**, never only in `docker service update`. Copy
  [docker-compose.node.yml.example](../docker-compose.node.yml.example): the file is ignored by git (it can
  say which ports a node opens, and this repository is public) and is added last, after `docker-compose.yml`
  and the extensions, by the scripts below, `scripts/docker-deploy.py` and `scripts/rebuild.py`.
* **Redeploy with the script**, which compares first and deploys with the same files:

```sh
python3 scripts/stack-deploy.py -t my_stack [-c docker-compose.yml -c extensions/extension1.yml ...]
```

It shows what would change in the running services and asks before deploying (`--yes` skips the question).
After the deploy it compares again: no running service should differ. To only compare, without deploying:

```sh
python3 scripts/stack-diff.py -t my_stack [-c docker-compose.yml -c extensions/extension1.yml ...]
```

`REMOVE` lines are settings that exist only in the running service (probably made by hand): the comparison
prints them as YAML to add to `docker-compose.node.yml`. Services that are not running yet are listed as
`[new]` (the deploy creates them), and services with fewer tasks than wanted as `[down]`: a deploy does not
restart a service whose spec does not change, use `docker service update --force <service>`.
`stack-diff.py` exits with 0 when the deploy would not change any running service.

If the deploy changes the `mongodb` image, `stack-deploy.py` first checks that it can run here
([scripts/mongo_check.py](../scripts/mongo_check.py)): it refuses a version jump that the data's
featureCompatibilityVersion does not allow (e.g. 6.0 data with `mongo:8.0`) and an image that does not start
on this host (tested in a throwaway container without network or data). And if a new `mongod` still dies while
it starts, Swarm rolls `mongodb` back to the previous image by itself (`update_config: failure_action: rollback`).
See [mongo-upgrade.md](mongo-upgrade.md).

A quick change with `docker service update` is fine, but if it must stay, add it to
`docker-compose.node.yml` too (or the next deploy undoes it).

Check services:

```sh
$ docker stack services my_stack
ID             NAME                MODE         REPLICAS               IMAGE                   PORTS
<ID>           my_stack_apache     replicated   1/1                    apache_image:latest     *:80->80/tcp, *:443->443/tcp, *:7000->7000/tcp
<ID>           my_stack_client     replicated   2/2                    client_image:latest     *:8080->80/tcp
<ID>           my_stack_loader     replicated   0/0                    loader_image:latest     
<ID>           my_stack_minio      replicated   1/1 (max 1 per node)   minio/minio:latest      *:9000-9001->9000-9001/tcp
<ID>           my_stack_mongodb    replicated   1/1                    mongo:6                 *:27017->27017/tcp
<ID>           my_stack_rest       replicated   4/4                    rest_image:latest       *:8081->3000/tcp
<ID>           my_stack_vre_lite   replicated   1/1                    vre_lite_image:latest   *:8082->3001/tcp
<ID>           my_stack_workflow   replicated   0/0                    workflow_image:latest  
```

Check nodes:

```sh
docker node ls
```

⚠️ In case the environment variables **MONGO_CONTAINER_USER** and **MONGO_CONTAINER_GROUP** in the [**global .env**](config.md#env-file) were set to a different user than the standars `mongo / 999` or `root / 0`, the [**mongo-init.js**](../mongodb/mongo-init.js) won't be executed because it doesn't have the necessary permissions and it must be executed manually once the deploy is finished: ⚠️

Get the **container id**:

```sh
docker ps --filter "label=com.docker.swarm.service.name=my_stack_mongodb"
```

Execute **mongo-init.js**:

```sh
docker exec -it \
  -e MONGO_INITDB_DATABASE=${DB_NAME} \
  -e LOADER_DB_LOGIN=${LOADER_DB_LOGIN} \
  -e LOADER_DB_PASSWORD=${LOADER_DB_PASSWORD} \
  -e REST_DB_LOGIN=${REST_DB_LOGIN} \
  -e REST_DB_PASSWORD=${REST_DB_PASSWORD} \
  -e VRE_LITE_MONGO_DATABASE=${VRE_LITE_MONGO_DATABASE} \
  -e VRE_LITE_DB_LOGIN=${VRE_LITE_DB_LOGIN} \
  -e VRE_LITE_DB_PASSWORD=${VRE_LITE_DB_PASSWORD} \
  <ID> \
  mongosh -u ${MONGO_INITDB_ROOT_USERNAME} -p ${MONGO_INITDB_ROOT_PASSWORD} /docker-entrypoint-initdb.d/mongo-init.js
```

**Update REST service** (as it was already running it needs to be restarted):

```sh
docker service update --force my_stack_rest
```

## Generate VRE lite database

The versions for **each service** of the stack are stored into a database. The **status** of these services is shown in the **VRE lite service**. After the **installation** and **deploy** of the services, this **database** must be **generated**:

```sh
python3 scripts/update-services-versions.py 
```

## Execute services

Once the installation is finished, it's time to **execute** and **check** the different services.

### Use workflow

While the **mongodb**, **client** and **rest** containers will remain up, the **workflow** must be called every time is needed. As it is a **one-off task**, **Docker Compose** is used for running it.

Workflow **help**:

```sh
docker compose run --rm workflow mwf -h
```

Or, if the above doesn't work:

```sh
docker run --rm workflow_image mwf -h
```

Please read carefully the [**workflow help**](../workflow) as it has an extensive documentation. 

#### Plain execution

Example of **running** the workflow downloading an already **loaded trajectory** and saving the results into an **OUTPUT_FOLDER** that must be already created inside **WORKFLOW_VOLUME_PATH** defined in [**global .env**](config.md#env-file).

```sh
docker compose run --rm workflow mwf run -proj <ACCESSION ID> -smp -e clusters energies pockets -dir /data/<OUTPUT_FOLDER>
```

Or, if the above doesn't work:

```sh
docker run --rm workflow_image -v <WORKFLOW_VOLUME_PATH>:/data --cpus "${WORKFLOW_CPU_LIMIT}" --memory "${WORKFLOW_MEMORY_LIMIT}" mwf run -proj <ACCESSION ID> -smp -e clusters energies pockets -dir /data/<OUTPUT_FOLDER>
```

Note that this run excludes clusters, energies and pockets analyses. Adding the -smp flag it downloads only 10 frames of the trajectory. As this instruction is a test, this will save a lot of computational time.

#### Usual execution

Example of **running** the workflow from data **uploaded via VRE lite**:

```sh
docker compose run --rm -e BUCKET=<BUCKET> workflow mwf run -dir /data/<OUTPUT_FOLDER> -md /data/<OUTPUT_FOLDER>/<REPLICA_FOLDER> /mnt/<FOLDER>/<TOPOLOGY> /mnt/<FOLDER>/<TRAJECTORY> -top /mnt/<FOLDER>/<TOPOLOGY> -inp /mnt/<FOLDER>/inputs.yaml -filt -ns
```

Or, if the above doesn't work:

```sh
docker run --rm -e BUCKET=<BUCKET> --network minio_network -v <WORKFLOW_VOLUME_PATH>:/data --cpus "${WORKFLOW_CPU_LIMIT}" --memory "${WORKFLOW_MEMORY_LIMIT}" --cap-add SYS_ADMIN --device /dev/fuse --security-opt apparmor:unconfined workflow_image mwf run -dir /data/<OUTPUT_FOLDER> -md /data/<OUTPUT_FOLDER>/<REPLICA_FOLDER> /mnt/<FOLDER>/<TOPOLOGY> /mnt/<FOLDER>/<TRAJECTORY> -top /mnt/<FOLDER>/<TOPOLOGY> -inp /mnt/<FOLDER>/inputs.yaml -filt -ns
```

* **BUCKET:** Bucket created in MinIO via **VRE lite**. Given along with the credentials by the **VRE lite** for **uploading** the data via **command line**. In format **YYYYMMDD**.
* **WORKFLOW_VOLUME_PATH:** Workflow output path defined in [**global .env**](config.md#env-file).
* **OUTPUT_FOLDER:** Folder inside **WORKFLOW_VOLUME_PATH**, it must be created beforehand.
* **FOLDER:** Folder inside **BUCKET**. Given along with the credentials when **uploading** the data via **command line**.
* **TOPOLOGY:** **Topology** file name. File uploaded via **VRE lite**.
* **TRAJECTORY:** **Trajectory** file name. File uploaded via **VRE lite**.
* **REPLICA_FOLDER:** Name **inside <WORKFLOW_VOLUME_PATH>/<OUTPUT_FOLDER>**. It's created automatically by the workflow. 
 
### Use loader

While the **mongodb**, **client** and **rest** containers will remain up, the **loader** must be called every time is needed. As it is a **one-off task**, **Docker Compose** is used for running it.

**List** database documents:

```sh
docker compose run --rm loader list
```

Or, if the above doesn't work:

```sh
docker run --rm --network data_network --cpus "${LOADER_CPU_LIMIT}" --memory "${LOADER_MEMORY_LIMIT}" loader_image list
```

**Load** documents to database:

```sh
docker compose run -it --rm loader load /data/<OUTPUT_FOLDER>
```

Or, if the above doesn't work:

```sh
docker run -it --rm --network data_network -v <WORKFLOW_VOLUME_PATH>:/data --cpus "${LOADER_CPU_LIMIT}" --memory "${LOADER_MEMORY_LIMIT}" loader_image load -a <ACCESSION> /data/<OUTPUT_FOLDER>
```

Take into account that **OUTPUT_FOLDER** must be inside **WORKFLOW_VOLUME_PATH**, defined in [**global .env**](config.md#env-file).

**Remove** database document:

```sh
docker compose run --rm loader delete <project_id>
```

Or, if the above doesn't work:

```sh
docker run --rm --network data_network --cpus "${LOADER_CPU_LIMIT}" --memory "${LOADER_MEMORY_LIMIT}" loader_image delete <project_id>
```

### MongoDB backup service

The MongoDB backup service performs a complete database backup every so often depending on a variable defined by the user (${DB_BACKUP_INTERVAL} seconds). To disable this service, define **DB_BACKUP_REPLICAS** to 0. This operation is only recommended for small databases, so if your database is large, please explore other options for doing backups of it.

Each backup is named after the UTC time its dump started. `DB_BACKUP_COMPRESS` sets its format:

| `DB_BACKUP_COMPRESS` | Backup | Restore |
|---|---|---|
| `no` | `<timestamp>/` plain `mongodump` directory | `mongorestore --dir <timestamp>` |
| `gz` | `<timestamp>/` `mongodump --gzip` directory | `mongorestore --gzip --dir <timestamp>` |
| `tar` | `<timestamp>.tar` (uncompressed) | extract, then `mongorestore --dir` |
| `tar.gz` | `<timestamp>.tar.gz` | extract, then `mongorestore --dir` |

Trade-offs measured on the MDDB production database (~4.9 TiB, mostly binary trajectories in GridFS):

* gzip only saves ~20% of disk, because binary trajectories barely compress.
* A plain dump took ~15 hours. gzip is single-threaded: `tar.gz` took ~4 more days after the dump. With `gz` the compression happens during the dump, so `mongodump` keeps reading from the database for days instead.
* `tar` and `tar.gz` write the full dump first and then pack it, so during the backup the data is on disk twice. `tar` saves no space; it only produces a single file.

**Consistency.** `mongodump` on a standalone `mongod` reads one collection after another, so writes made while it runs (e.g. a loader run) can leave the backup inconsistent between collections (such as `fs.files` and `fs.chunks`). With `DB_BACKUP_LOCK=yes` the service runs `db.fsyncLock()` before the dump and `db.fsyncUnlock()` right after it: reads keep working, but every write waits until the dump finishes (hours on large databases; plan loader runs accordingly). The lock is released when the service is stopped, and a lock left by a killed run (e.g. `SIGKILL`) is released on the next start, so do not `fsyncLock` the database by hand while the backup service runs. With `DB_BACKUP_LOCK=no` writes are never blocked.

**Waiting for writes to stop.** Before every backup, the service counts the write operations on the database (every collection outside `admin`, `config` and `local`) during `WRITE_CHECK_WINDOW` seconds (default 300). If there was any, someone is writing (e.g. a loader run), so the backup is postponed `BUSY_RETRY_DELAY` seconds (default 3600) and checked again. This avoids locking writes in the middle of a loader run, or dumping data while it changes. A backup is not postponed more than `MAX_POSTPONE` seconds (default 172800, 48 h) since the first check: past that, it starts even if someone is writing (the log says `starting the backup while someone is writing`). Restarting the service starts the count again.

To check whether the database is write-locked, and to release it by hand:

```sh
mongosh ... --eval 'db.adminCommand({currentOp: 1}).fsyncLock'   # true when locked
mongosh ... --eval 'while (db.adminCommand({currentOp: 1}).fsyncLock === true) db.fsyncUnlock()'
```

Every backup is written under a `.partial` name and only renamed once all its steps have succeeded, so a backup with a final name is always complete. Leftovers of interrupted runs are removed when the service starts. The next backup is scheduled `DB_BACKUP_INTERVAL` seconds after the start of the last complete one, so redeploying the stack does not trigger a new backup unless one is due. After each successful backup, only the `DB_BACKUP_RETENTION_COUNT` most recent complete backups are kept, in any of the formats above (so changing the format does not leave old backups behind). If a backup fails, the service waits `RETRY_DELAY` seconds (default 3600) and exits with an error (visible in `docker service ps <stack>_mongo-backup`), so swarm restarts it after that delay: a failed dump is done again from scratch. With `tar` and `tar.gz`, a dump that finished but could not be packed (e.g. an NFS error while writing the archive) is kept as a backup, and its packing is retried on the next start; the dump is only removed once its archive is complete.

**Logs.** The output of every run of the service is also written to `${DB_BACKUP_VOLUME_PATH}/logs/<start time>.log`, so it survives the container. If the run fails, its log is renamed to `<start time>.error.log`; error logs are never removed automatically. Of the other logs, only the 20 most recent are kept (`LOG_RETENTION_COUNT`).

For performing a **single mongodump**, please execute:

```sh
docker run --rm --name mongo-dump -e MONGO_INITDB_ROOT_USERNAME=${MONGO_INITDB_ROOT_USERNAME} -e MONGO_INITDB_ROOT_PASSWORD=${MONGO_INITDB_ROOT_PASSWORD} -e MONGO_PORT=${DB_OUTER_PORT} -e MONGO_INITDB_DATABASE=${DB_AUTHSOURCE} -e DB_HOST=${DB_SERVER} -e BACKUP_DIR=/backup -v ${DB_BACKUP_VOLUME_PATH}:/backup -v $(pwd)/mongodb/mongodump_script.sh:/mongodump_script.sh:ro --cpus "${DB_BACKUP_CPU_LIMIT}" --memory "${DB_BACKUP_MEMORY_LIMIT}" --network data_network --security-opt label=disable mongo:latest bash -c "sh /mongodump_script.sh"
```

> NOTE: Depending of the size of the database, this operation can take hours, days and even weeks.

### Check rest

Open a browser and type:

```
http://localhost:8081
```

Or modify the port 8081 by the one defined as **REST_OUTER_PORT** in the [**.env**](../.env.docker.git) file. 

If services are already online, go to:

    http(s)://your_server_ip/api/rest/

### Check client

Open a browser and type:

```
http://localhost:8080
```

Or modify the port 8080 by the one defined as **CLIENT_OUTER_PORT** in the [**.env**](../.env.docker.git) file. 

If services are already online, go to:

    http(s)://your_server_ip

### Check MinIO

#### WebUI

The **MinIo WebUI** interface only should be available in **development**.

Open a browser and type:

```
http://localhost:9001
```

Or modify the port 9001 by the one defined as **MINIO_UI_OUTER_PORT** in the [**.env**](../.env.docker.git) file. 

If services are already online, go to:

    http(s)://your_server_ip/minio

#### API

In terminal, do:

```
curl -f http://localhost:9000/minio/health/live
```

Or modify the port 9000 by the one defined as **MINIO_API_OUTER_PORT** in the [**.env**](../.env.docker.git) file. 

If services are already online, do:

    curl -f http(s)://your_server_ip:9000/minio/health/live

### Check VRE lite

This service **depends on MinIO**, so until the MinIO service is up & running, the VRE lite will apear as down.

Open a browser and type:

```
http://localhost:8082
```

Or modify the port 8082 by the one defined as **VRE_LITE_OUTER_PORT** in the [**.env**](../.env.docker.git) file. 

If services are already online, go to:

    http(s)://your_server_ip/vre_lite/

### Use utils

While the **mongodb**, **client** and **rest** containers will remain up, the **utils** must be called every time is needed. As it is a **one-off task**, **Docker Compose** is used for running it.

**Show help** for utils:

```sh
docker compose run --rm utils help
```

Or, if the above doesn't work:

```sh
docker run --rm utils_image help
```

**List** all available utils scripts:

```sh
docker compose run --rm utils list
```

Or, if the above doesn't work:

```sh
docker run --rm utils_image list
```

**Run** scripts:

```sh
docker compose run --rm run <script.py> [args]
```

For example, for updating the version of the client to 1.2.0 in the VRE lite DB:

```sh
docker compose run --rm utils run version_tracker.py client v1.2.0
```

Or, if the above doesn't work:

```sh
docker run --rm utils_image run <script.py> [args]
```

**Execute** container in shell:

```sh
docker compose run --rm utils shell
```

Or, if the above doesn't work:

```sh
docker run --rm utils_image shell
```

## Stop services

Remove stack:

```sh
docker stack rm my_stack
```

Leave swarm:

```sh
docker swarm leave --force
```

## Check

### Check containers

Check that at least the mongo, rest and client containers are up & running:

```sh
$ docker ps -a
CONTAINER ID   IMAGE                   COMMAND                  CREATED        STATUS                  PORTS                       NAMES
<ID>           rest_image:latest       "pm2-runtime start i…"   17 hours ago   Up 17 hours             3000/tcp                    my_stack_rest.2.<ID>
<ID>           rest_image:latest       "pm2-runtime start i…"   17 hours ago   Up 17 hours             3000/tcp                    my_stack_rest.1.<ID>
<ID>           rest_image:latest       "pm2-runtime start i…"   17 hours ago   Up 17 hours             3000/tcp                    my_stack_rest.3.<ID>
<ID>           rest_image:latest       "pm2-runtime start i…"   17 hours ago   Up 17 hours             3000/tcp                    my_stack_rest.4.<ID>
<ID>           mongo:6                 "docker-entrypoint.s…"   17 hours ago   Up 17 hours             27017/tcp                   my_stack_mongodb.1.<ID>
<ID>           client_image:latest     "/docker-entrypoint.…"   17 hours ago   Up 17 hours             80/tcp                      my_stack_client.2.<ID>
<ID>           client_image:latest     "/docker-entrypoint.…"   17 hours ago   Up 17 hours             80/tcp                      my_stack_client.1.<ID>
<ID>           minio/minio:latest      "/usr/bin/docker-ent…"   17 hours ago   Up 17 hours (healthy)   9000/tcp                    my_stack_minio.1.<ID>
<ID>           apache_image:latest     "httpd-foreground"       17 hours ago   Up 17 hours             80/tcp, 443/tcp, 7000/tcp   my_stack_apache.1.<ID>
<ID>           vre_lite_image:latest   "/app/entrypoint.sh"     17 hours ago   Up 17 hours             3001/tcp                    my_stack_vre_lite.1.<ID>
```

### Inspect docker network 

The **client**, **rest** and **mongodb** containers are in the same network. Execute the following instruction for inspecting the **docker network**:

```sh
docker network inspect data_network
```

It should show something like:

```json
[
    {
        "Name": "data_network",
        "Id": "<ID>",
        "Created": "<DATE>",
        "Scope": "swarm",
        "Driver": "overlay",
        "EnableIPv6": false,
        "IPAM": {
            "Driver": "default",
            "Options": null,
            "Config": [
                {
                    "Subnet": "<IP>",
                    "Gateway": "<IP>"
                }
            ]
        },
        "Internal": false,
        "Attachable": true,
        "Ingress": false,
        "ConfigFrom": {
            "Network": ""
        },
        "ConfigOnly": false,
        "Containers": {
            "<ID>": {
                "Name": "my_stack_rest.4.<ID>",
                "EndpointID": "<ID>",
                "MacAddress": "<MAC>",
                "IPv4Address": "<IP>",
                "IPv6Address": ""
            },
            "<ID>": {
                "Name": "my_stack_rest.2.<ID>",
                "EndpointID": "<ID>",
                "MacAddress": "<MAC>",
                "IPv4Address": "<IP>",
                "IPv6Address": ""
            },
            "<ID>": {
                "Name": "my_stack_rest.3.<ID>",
                "EndpointID": "<ID>",
                "MacAddress": "<MAC>",
                "IPv4Address": "<IP>",
                "IPv6Address": ""
            },
            "<ID>": {
                "Name": "my_stack_mongodb.1.<ID>",
                "EndpointID": "<ID>",
                "MacAddress": "<MAC>",
                "IPv4Address": "<IP>",
                "IPv6Address": ""
            },
            "<ID>": {
                "Name": "my_stack_rest.1.<ID>",
                "EndpointID": "<ID>",
                "MacAddress": "<MAC>",
                "IPv4Address": "<IP>",
                "IPv6Address": ""
            },
            "lb-data_network": {
                "Name": "data_network-endpoint",
                "EndpointID": "<ID>",
                "MacAddress": "<MAC>",
                "IPv4Address": "<IP>",
                "IPv6Address": ""
            }
        },
        "Options": {
            "com.docker.network.driver.overlay.vxlanid_list": "<ID>"
        },
        "Labels": {
            "com.docker.stack.namespace": "my_stack"
        },
        "Peers": [
            {
                "Name": "<ID>",
                "IP": "<IP>"
            }
        ]
    }
]
```

### Docker stats

Check resources consumption for all running containers:

```sh
$ docker stats
CONTAINER ID   NAME                                           CPU %     MEM USAGE / LIMIT   MEM %     NET I/O           BLOCK I/O     PIDS
<ID>           my_stack_rest.2.<ID>                           0.25%     69.8MiB / 10GiB     0.68%     5.37MB / 2.15MB   0B / 24.6kB   22
<ID>           my_stack_rest.1.<ID>                           0.19%     69.7MiB / 10GiB     0.68%     5.63MB / 1.81MB   0B / 24.6kB   22
<ID>           my_stack_rest.3.<ID>                           0.18%     69.14MiB / 10GiB    0.68%     5.5MB / 2.17MB    0B / 24.6kB   22
<ID>           my_stack_rest.4.<ID>                           0.25%     68.77MiB / 10GiB    0.67%     5.9MB / 2.63MB    0B / 24.6kB   22
<ID>           my_stack_mongodb.1.<ID>                        0.61%     75.12MiB / 8GiB     0.92%     6.69MB / 22.3MB   0B / 93.5MB   44
<ID>           my_stack_client.2.<ID>                         0.00%     12.7MiB / 8GiB      0.16%     90.5kB / 886kB    0B / 12.3kB   17
<ID>           my_stack_client.1.<ID>                         0.00%     12.87MiB / 8GiB     0.16%     86.1kB / 4.12MB   0B / 12.3kB   17
<ID>           my_stack_minio.1.<ID>                          0.04%     110MiB / 4GiB       2.68%     1.93GB / 1.38GB   0B / 2.14GB   21
<ID>           my_stack_apache.1.<ID>                         0.00%     25.78MiB / 1GiB     2.52%     57.8MB / 59.1MB   0B / 4.1kB    109
<ID>           my_stack_vre_lite.1.<ID>                       2.65%     384.5MiB / 4GiB     9.39%     1.5MB / 23kB      0B / 3.09MB   187
```