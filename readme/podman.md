# Deploy Podman containers

In computing, **Podman** (pod manager) is an open source **Open Container Initiative** (OCI)-compliant container management tool from **Red Hat** used for handling **containers**, **images**, **volumes**, and **pods**.

**Podman** lets containers run **without root privileges** (rootless), meaning they can be **created**, **run**, and **managed** by regular users **without administrator rights**.

## Before building

### Load environment variables

Export environment variables defined in [**global .env file**](config.md#env-file):

```sh
set -a; source .env; set +a
```

### Check the network backend

Since **Podman 5**, the old **CNI** network backend is no longer supported and the CNI plugins are usually not installed anymore. Check which backend is in use:

```sh
podman info --format '{{.Host.NetworkBackend}}'
```

If it says `cni` (it happens when podman finds old CNI networks or containers), switch to **netavark** for your user:

```sh
mkdir -p ~/.config/containers
cat >> ~/.config/containers/containers.conf <<EOF
[network]
network_backend = "netavark"
EOF
```

Networks created with CNI are not migrated, so they must be **created again** (see below). Old CNI configuration files in `~/.config/cni` are ignored once netavark is active.

### Containers created with older podman versions

If podman is upgraded and the **runc** runtime is replaced by **crun**, containers created before the upgrade can not be started anymore (`OCI Runtime runc is in use by a container, but is not available`). They must be **removed** (`podman rm <name>`) and **run again** with the commands below. The data is kept, as it lives in the **host folders** mounted with `-v` (e.g. **DB_VOLUME_PATH**), which `podman rm` does not touch. Before removing them, it is a good idea to save their configuration with `podman inspect <name> > <name>.json`.

### Resource limits

In **rootless** podman, the `--cpus` and `--memory` flags only work if the system delegates the corresponding **cgroup controllers** to your user. Check which ones are delegated:

```sh
podman info --format '{{.Host.CgroupControllers}}'
```

In many systems only `[memory pids]` are delegated, so `--cpus` fails with an error like `crun: controller 'cpu' is not available`. For this reason, the commands in this document **do not set resource limits**. If your system delegates the `cpu` and `memory` controllers, you can add `--cpus "${<SERVICE>_CPU_LIMIT}" --memory "${<SERVICE>_MEMORY_LIMIT}"` to any `podman run` command.

Take into account that older podman versions (with the `cgroupfs` manager) silently **ignored** these limits in rootless mode, so containers created with them never had actual limits.

### Create networks

Create the **networks** needed for connecting all the **services**. Setting the **subnets explicitly** allows to give fixed IPs to **mongodb** and **minio** (see below), so they do not change when containers are recreated:

```sh
podman network create --subnet 10.89.0.0/24 web_network
podman network create --subnet 10.89.1.0/24 data_network
podman network create --subnet 10.89.2.0/24 minio_network
```

Any free private subnets can be used. Check that they do not collide with the existing ones with `podman network ls` and `podman network inspect <network>`.

## Deploy MongoDB

The **first service** to be deployed is **mongodb** because some other services such as the **REST API** and the **VRE lite** need to know the **mongodb IP** address **before starting** the building process.

Typical execution:

```sh
podman run -d --name mongodb -e MONGO_INITDB_ROOT_USERNAME=${MONGO_INITDB_ROOT_USERNAME} -e MONGO_INITDB_ROOT_PASSWORD=${MONGO_INITDB_ROOT_PASSWORD} -e MONGO_PORT=${DB_OUTER_PORT} -e MONGO_INITDB_DATABASE=${DB_NAME} -e LOADER_DB_LOGIN=${LOADER_DB_LOGIN} -e LOADER_DB_PASSWORD=${LOADER_DB_PASSWORD} -e MONGO_VRE_DATABASE=${VRE_LITE_MONGO_DATABASE} -e VRE_DB_LOGIN=${VRE_LITE_DB_LOGIN} -e VRE_DB_PASSWORD=${VRE_LITE_DB_PASSWORD} -e REST_DB_LOGIN=${REST_DB_LOGIN} -e REST_DB_PASSWORD=${REST_DB_PASSWORD} -v ${DB_VOLUME_PATH}:/data/db:Z -v $(pwd)/mongodb/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro --network data_network --security-opt label=disable docker.io/library/mongo:6
```

Sometimes, podman gives **problems with permissions**. Typically, these problems arise from using **NFS file systems** and **non-root permissions** in podman. Therefore, to avoid these problems, an alternative execution can be performed, using a [**mongo-nonroot.sh**](../mongodb/mongo-nonroot.sh) bash script for intialising the **mongodb** service:

```sh
podman run -d --name mongodb -e MONGO_INITDB_ROOT_USERNAME=${MONGO_INITDB_ROOT_USERNAME} -e MONGO_INITDB_ROOT_PASSWORD=${MONGO_INITDB_ROOT_PASSWORD} -e MONGO_PORT=${DB_OUTER_PORT} -e MONGO_INITDB_DATABASE=${DB_NAME} -e LOADER_DB_LOGIN=${LOADER_DB_LOGIN} -e LOADER_DB_PASSWORD=${LOADER_DB_PASSWORD} -e MONGO_VRE_DATABASE=${VRE_LITE_MONGO_DATABASE} -e VRE_DB_LOGIN=${VRE_LITE_DB_LOGIN} -e VRE_DB_PASSWORD=${VRE_LITE_DB_PASSWORD} -e REST_DB_LOGIN=${REST_DB_LOGIN} -e REST_DB_PASSWORD=${REST_DB_PASSWORD} -e DB_OUTER_PORT=${DB_OUTER_PORT} -v ${DB_VOLUME_PATH}:/data/db:Z -v $(pwd)/mongodb/mongo-nonroot.sh:/entrypoint.sh:Z --entrypoint /entrypoint.sh -v $(pwd)/mongodb/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro --network data_network --security-opt label=disable docker.io/library/mongo:6
```

**IMPORTANT**

In some podman implementations, the REST API gave some problems connecting to the mongo DB via service name. Therefore, in order to fix that, the **DB_SERVER** must be the **mongodb service IP**. So, for **setting this IP beforehand**, the **--ip flag** can be added:

```sh
podman run -d --name mongodb -e MONGO_INITDB_ROOT_USERNAME=${MONGO_INITDB_ROOT_USERNAME} -e MONGO_INITDB_ROOT_PASSWORD=${MONGO_INITDB_ROOT_PASSWORD} -e MONGO_PORT=${DB_OUTER_PORT} -e MONGO_INITDB_DATABASE=${DB_NAME} -e LOADER_DB_LOGIN=${LOADER_DB_LOGIN} -e LOADER_DB_PASSWORD=${LOADER_DB_PASSWORD} -e MONGO_VRE_DATABASE=${VRE_LITE_MONGO_DATABASE} -e VRE_DB_LOGIN=${VRE_LITE_DB_LOGIN} -e VRE_DB_PASSWORD=${VRE_LITE_DB_PASSWORD} -e REST_DB_LOGIN=${REST_DB_LOGIN} -e REST_DB_PASSWORD=${REST_DB_PASSWORD} -e DB_OUTER_PORT=${DB_OUTER_PORT} -v ${DB_VOLUME_PATH}:/data/db:Z -v $(pwd)/mongodb/mongo-nonroot.sh:/entrypoint.sh:Z --entrypoint /entrypoint.sh -v $(pwd)/mongodb/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro --network data_network --ip <IP ADDRESS> --security-opt label=disable docker.io/library/mongo:6
```

The **IP** must belong to the **subnet** of **data_network** (e.g. `10.89.1.109` for `10.89.1.0/24`). Fixing the IP is **recommended**: otherwise podman may assign a different IP when the container is recreated, and then the **REST API** and the **loader** (whose images are built with **DB_SERVER**) can no longer reach the database and they have to be rebuilt.

If the IP has been fixed, jump to the [**Build services**](#build-services) section, if not, execute the **following instruction** in order to get the **automatic IP** given to the **mongodb** service by podman:

```sh
podman inspect -f '{{.NetworkSettings.Networks.data_network.IPAddress}}' mongodb
```

## Build services

Below there are all the instructions needed for **building** all the **services**:

### REST API

```sh
podman build -t rest_image --build-arg DB_SERVER=${DB_SERVER} --build-arg DB_PORT=${DB_OUTER_PORT} --build-arg DB_NAME=${DB_NAME} --build-arg DB_AUTH_USER=${REST_DB_LOGIN} --build-arg DB_AUTH_PASSWORD=${REST_DB_PASSWORD} --build-arg DB_AUTHSOURCE=${DB_AUTHSOURCE} --build-arg REST_INNER_PORT=${REST_INNER_PORT} ./rest
```

### client

```sh
podman build -t client_image --build-arg CLIENT_INNER_PORT=${CLIENT_INNER_PORT} ./client
```

### Apache

```sh
podman build -t apache_image --build-arg APACHE_HTTP_INNER_PORT=${APACHE_HTTP_INNER_PORT} --build-arg APACHE_HTTPS_INNER_PORT=${APACHE_HTTPS_INNER_PORT} --build-arg APACHE_HTTP_OUTER_PORT=${APACHE_HTTP_OUTER_PORT} --build-arg APACHE_HTTPS_OUTER_PORT=${APACHE_HTTPS_OUTER_PORT} --build-arg APACHE_MINIO_OUTER_PORT=${APACHE_MINIO_OUTER_PORT} --build-arg APACHE_MINIO_INNER_PORT=${APACHE_MINIO_INNER_PORT} --build-arg CLIENT_INNER_PORT=${CLIENT_INNER_PORT} --build-arg REST_INNER_PORT=${REST_INNER_PORT} --build-arg VRE_LITE_INNER_PORT=${VRE_LITE_INNER_PORT} --build-arg MINIO_UI_INNER_PORT=${MINIO_UI_INNER_PORT} --build-arg MINIO_API_INNER_PORT=${MINIO_API_INNER_PORT} --build-arg SERVER_URL=${MINIO_URL} --build-arg SSL_CERTIFICATE=${SSL_CERTIFICATE} --build-arg SSL_CERT_KEY=${SSL_CERT_KEY} ./apache
```

### Workflow

```sh
podman build -t workflow_image --build-arg MINIO_USER=${MINIO_USER} --build-arg MINIO_PASSWORD=${MINIO_PASSWORD} --build-arg MINIO_API_PORT=${MINIO_API_INNER_PORT} ./workflow
```

### Loader

```sh
podman build -t loader_image --build-arg DB_SERVER=${DB_SERVER} --build-arg DB_PORT=${DB_OUTER_PORT} --build-arg DB_NAME=${DB_NAME} --build-arg DB_AUTH_USER=${LOADER_DB_LOGIN} --build-arg DB_AUTH_PASSWORD=${LOADER_DB_PASSWORD} --build-arg DB_AUTHSOURCE=${DB_AUTHSOURCE} ./loader
```

### Utils

```sh
podman build -t utils_image ./utils
```

## Deploy MinIO and build VRE lite

### Minio

**Before** building **VRE lite**, deploy **MinIO** in order to get the **IP address** of this service:

```sh
podman run -d --name minio -e MINIO_ROOT_USER=${MINIO_ROOT_USER} -e MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD} -e MINIO_BROWSER_REDIRECT_URL=${MINIO_BROWSER_REDIRECT_URL} -e MINIO_API_INNER_PORT=${MINIO_API_INNER_PORT} -e MINIO_UI_INNER_PORT=${MINIO_UI_INNER_PORT} -e MINIO_USER=${MINIO_USER} -e MINIO_PASSWORD=${MINIO_PASSWORD} -p ${MINIO_API_OUTER_PORT}:${MINIO_API_INNER_PORT} -p ${MINIO_UI_INNER_PORT}:${MINIO_UI_INNER_PORT} -v ${MINIO_VOLUME_PATH1}:/mnt/disk1:Z -v $(pwd)/minio/init-minio.sh:/entrypoint.sh --network minio_network --network web_network --hostname minio --entrypoint /entrypoint.sh --healthcheck-command "curl -f http://localhost:${MINIO_API_INNER_PORT}/minio/health/live" --healthcheck-interval 10s --healthcheck-timeout 2s --healthcheck-retries 5 docker.io/minio/minio:latest
```

### VRE lite

**IMPORTANT**

In some podman implementations, the VRE lite gave some problems connecting to the minio service via service name. Therefore, in order to fix that, get the MinIO IP executing the following instruction:

```sh
podman inspect -f '{{.NetworkSettings.Networks.minio_network.IPAddress}}' minio
```

And assign the value to **MINIO_ADDRESS** in the [**global .env**](config.md#env-file). 

Alternatively, if **MINIO_ADDRESS** is already defined (e.g. when redeploying with an existing **vre_lite_image**), the MinIO IP can be fixed when running it, replacing `--network minio_network` with `--network minio_network:ip=${MINIO_ADDRESS}` in the [**MinIO command**](#minio). The IP must belong to the **subnet** of **minio_network**.

After that, build the vre_lite service:

```sh
podman build -t vre_lite_image --build-arg MINIO_USER=${MINIO_USER} --build-arg MINIO_PASSWORD=${MINIO_PASSWORD} --build-arg MINIO_API_PORT=${MINIO_API_INNER_PORT}  --build-arg MINIO_ADDRESS=${MINIO_ADDRESS} --build-arg VRE_LITE_INNER_PORT=${VRE_LITE_INNER_PORT} --build-arg VRE_LITE_BASE_URL_DEVELOPMENT=${VRE_LITE_BASE_URL_DEVELOPMENT} --build-arg VRE_LITE_BASE_URL_STAGING=${VRE_LITE_BASE_URL_STAGING} --build-arg VRE_LITE_BASE_URL_PRODUCTION=${VRE_LITE_BASE_URL_PRODUCTION} --build-arg VRE_LITE_LOG_PATH=${VRE_LITE_LOG_PATH} --build-arg VRE_LITE_MAX_FILE_SIZE=${VRE_LITE_MAX_FILE_SIZE} --build-arg VRE_LITE_TIME_DIFF=${VRE_LITE_TIME_DIFF} --build-arg VERSION=${VRE_LITE_VERSION} --build-arg MINIO_PROTOCOL=${MINIO_PROTOCOL} --build-arg MINIO_URL=${MINIO_URL} --build-arg MINIO_PORT=${APACHE_MINIO_OUTER_PORT} --build-arg NODE_NAME=${NODE} --build-arg DB_USER=${VRE_LITE_DB_LOGIN} --build-arg DB_PASS=${VRE_LITE_DB_PASSWORD} --build-arg DB_SERVER=${VRE_LITE_DB_SERVER} --build-arg DB_PORT=${VRE_LITE_DB_OUTER_PORT} --build-arg DB_NAME=${VRE_LITE_MONGO_DATABASE} --build-arg PAT=${GH_PAT} ./vre_lite
```

## Run services

In this section there are the instructions needed for running the **long-running tasks**.

### MongoDB backup service

Take into account that this script performs a mongodump **every ${DB_BACKUP_INTERVAL} seconds**. So, if your database is large, please explore other options for doing backups of it.

```sh
podman run -d --name mongo-backup -e MONGO_INITDB_ROOT_USERNAME=${MONGO_INITDB_ROOT_USERNAME} -e MONGO_INITDB_ROOT_PASSWORD=${MONGO_INITDB_ROOT_PASSWORD} -e MONGO_PORT=${DB_OUTER_PORT} -e MONGO_INITDB_DATABASE=${DB_AUTHSOURCE} -e DB_HOST=${DB_SERVER} -e BACKUP_DIR=/backup -e RETENTION_COUNT=${DB_BACKUP_RETENTION_COUNT} -e BACKUP_INTERVAL=${DB_BACKUP_INTERVAL} -v ${DB_BACKUP_VOLUME_PATH}:/backup:Z -v $(pwd)/mongodb/backup_script.sh:/backup_script.sh:ro --network data_network --security-opt label=disable docker.io/library/mongo:6 bash -c "sh /backup_script.sh"
```

For performing a **single mongodump**, please execute:

```sh
podman run --rm --name mongo-dump -e MONGO_INITDB_ROOT_USERNAME=${MONGO_INITDB_ROOT_USERNAME} -e MONGO_INITDB_ROOT_PASSWORD=${MONGO_INITDB_ROOT_PASSWORD} -e MONGO_PORT=${DB_OUTER_PORT} -e MONGO_INITDB_DATABASE=${DB_AUTHSOURCE} -e DB_HOST=${DB_SERVER} -e BACKUP_DIR=/backup -v ${DB_BACKUP_VOLUME_PATH}:/backup:Z -v $(pwd)/mongodb/mongodump_script.sh:/mongodump_script.sh:ro --network data_network --security-opt label=disable docker.io/library/mongo:6 bash -c "sh /mongodump_script.sh"
```

> NOTE: Depending of the size of the database, this operation can take hours, days and even weeks.

### REST API

```sh
podman run -d --name rest -p ${REST_OUTER_PORT}:${REST_INNER_PORT} --network data_network --network web_network rest_image
```

### client

```sh
podman run -d --name client -p ${CLIENT_OUTER_PORT}:${CLIENT_INNER_PORT} --network web_network client_image
```

### VRE lite

Before launching VRE lite, please be sure that **Podman socket** is initialised:

```sh
systemctl --user status podman.socket
```

If the socket is **not running** (ie it says `Active: inactive (dead)`), you need to **start it**:

```sh
systemctl --user start podman.socket 
```

After that, **launch** the **vre_lite** service:

```sh
podman run -d --name vre_lite -p ${VRE_LITE_OUTER_PORT}:${VRE_LITE_INNER_PORT} -v ${VRE_LITE_VOLUME_PATH}:/vre_lite:Z -v /run/user/$(id -u)/podman/podman.sock:/var/run/docker.sock --network minio_network --network web_network --network data_network vre_lite_image
```

### Apache

```sh
podman run -d --name apache -p ${APACHE_HTTP_OUTER_PORT}:${APACHE_HTTP_INNER_PORT} -p ${APACHE_HTTPS_OUTER_PORT}:${APACHE_HTTPS_INNER_PORT} -p ${APACHE_MINIO_OUTER_PORT}:${APACHE_MINIO_INNER_PORT} -v ${APACHE_CERTS_VOLUME_PATH}:/usr/local/apache2/conf/ssl:Z --network web_network apache_image
```

## Execute services

In this section there are the instructions needed for executing the **one-off tasks**.

### Use workflow

While the **mongodb**, **client** and **rest** containers will remain up, the **workflow** must be called every time is needed.

Workflow **help**:

```sh
podman run --rm --name workflow workflow_image mwf -h
```

Please read carefully the [**workflow help**](../workflow) as it has an extensive documentation. 

#### Plain execution

Example of **running** the workflow downloading an **already loaded** trajectory and saving the results into an **OUTPUT_FOLDER** that must be already created inside **WORKFLOW_VOLUME_PATH** defined in [**global .env**](config.md#env-file).

```sh
podman run --rm --name workflow -v ${WORKFLOW_VOLUME_PATH}:/data workflow_image mwf run -proj <ACCESSION ID> -smp -e clusters energies pockets -dir /data/<OUTPUT_FOLDER>
```

Note that this run excludes clusters, energies and pockets analyses. Adding the -smp flag it downloads only 10 frames of the trajectory. As this instruction is a test, this will save a lot of computational time.

#### Usual execution

Example of **running** the workflow from data **uploaded via VRE lite**:

```sh
podman run --rm -e BUCKET=<BUCKET> --network minio_network -v ${WORKFLOW_VOLUME_PATH}:/data:Z --cap-add SYS_ADMIN --device /dev/fuse --security-opt apparmor:unconfined workflow_image mwf run -dir /data/<OUTPUT_FOLDER> -md /data/<OUTPUT_FOLDER>/<REPLICA_FOLDER> /mnt/<FOLDER>/<TOPOLOGY> /mnt/<FOLDER>/<TRAJECTORY> -top /mnt/<FOLDER>/<TOPOLOGY> -inp /mnt/<FOLDER>/inputs.yaml -filt -ns
```

* **BUCKET:** Bucket created in MinIO via **VRE lite**. Given along with the credentials by the **VRE lite** for **uploading** the data via **command line**. In format **YYYYMMDD**.
* **WORKFLOW_VOLUME_PATH:** Workflow output path defined in [**global .env**](config.md#env-file).
* **OUTPUT_FOLDER:** Folder inside **WORKFLOW_VOLUME_PATH**, it must be created beforehand.
* **FOLDER:** Folder inside **BUCKET**. Given along with the credentials when **uploading** the data via **command line**.
* **TOPOLOGY:** **Topology** file name. File uploaded via **VRE lite**.
* **TRAJECTORY:** **Trajectory** file name. File uploaded via **VRE lite**.
* **REPLICA_FOLDER:** Name **inside <WORKFLOW_VOLUME_PATH>/<OUTPUT_FOLDER>**. It's created automatically by the workflow. 
 
### Use loader

While the **mongodb**, **client** and **rest** containers will remain up, the **loader** must be called every time is needed. 

**List** database documents:

```sh
podman run --rm --name loader --network data_network loader_image list
```

**Load** documents to database:

```sh
podman run --rm --network data_network -v ${WORKFLOW_VOLUME_PATH}:/data:Z loader_image load /data/<OUTPUT_FOLDER>
```

Take into account that **OUTPUT_FOLDER** must be inside **WORKFLOW_VOLUME_PATH**, defined in [**global .env**](config.md#env-file).

**Remove** database document:

```sh
podman run --rm --name loader --network data_network loader_image delete <project_id>
```

### Use Utils

```sh
podman run --rm --name utils -e DB_SERVER=${VRE_LITE_DB_SERVER} -e DB_PORT=${VRE_LITE_DB_OUTER_PORT} -e DB_VRE_NAME=${VRE_LITE_MONGO_DATABASE} -e DB_VRE_AUTH_USER=${VRE_LITE_DB_LOGIN} -e DB_VRE_AUTH_PASSWORD=${VRE_LITE_DB_PASSWORD} -e DB_VRE_AUTHSOURCE=${VRE_LITE_MONGO_DATABASE} --network data_network utils_image version_tracker.py -h
```

### Check rest

Open a browser and type:

```
http://localhost:8081
```

Or modify the port 8081 by the one defined as **REST_OUTER_PORT** in the [**.env**](../.env.podman.git) file. 

If services are already online, go to:

    http(s)://your_server_ip/api/rest/

### Check client

Open a browser and type:

```
http://localhost:8080
```

Or modify the port 8080 by the one defined as **CLIENT_OUTER_PORT** in the [**.env**](../.env.podman.git) file. 

If services are already online, go to:

    http(s)://your_server_ip

### Check MinIO

#### WebUI

The **MinIo WebUI** interface only should be available in **development**.

Open a browser and type:

```
http://localhost:9001
```

Or modify the port 9001 by the one defined as **MINIO_UI_OUTER_PORT** in the [**.env**](../.env.podman.git) file. 

If services are already online, go to:

    http(s)://your_server_ip/minio

#### API

In terminal, do:

```
curl -f http://localhost:9000/minio/health/live
```

Or modify the port 9000 by the one defined as **MINIO_API_OUTER_PORT** in the [**.env**](../.env.podman.git) file. 

If services are already online, do:

    curl -f http(s)://your_server_ip:9000/minio/health/live

### Check VRE lite

This service **depends on MinIO**, so until the MinIO service is up & running, the VRE lite will apear as down.

Open a browser and type:

```
http://localhost:8082
```

Or modify the port 8082 by the one defined as **VRE_LITE_OUTER_PORT** in the [**.env**](../.env.podman.git) file. 

If services are already online, go to:

    http(s)://your_server_ip/vre_lite/

## Stop services

```sh
podman stop <service name or ID>
```

## Check

### Check containers

Check that at least the mongo, rest and client containers are up & running:

```sh
$ podman ps -a
CONTAINER ID  IMAGE                            COMMAND               CREATED         STATUS                PORTS                                                           NAMES
<ID>          docker.io/library/mongo:6                              2 hours ago     Up 2 hours            0.0.0.0:27017->27017/tcp                                        mongodb
<ID>          localhost/client_image:latest    nginx -g daemon o...  2 hours ago     Up 2 hours            0.0.0.0:8080->80/tcp                                            client
<ID>          docker.io/minio/minio:latest                           2 hours ago     Up 2 hours (healthy)  0.0.0.0:9001-9002->9001-9002/tcp                                minio
<ID>          localhost/apache_image:latest    httpd-foreground      2 hours ago     Up 2 hours            0.0.0.0:21402->21402/tcp, 0.0.0.0:21411-21412->21411-21412/tcp  apache
<ID>          localhost/rest_image:latest      pm2-runtime start...  58 minutes ago  Up 58 minutes         0.0.0.0:8081->3000/tcp                                          rest
<ID>          localhost/vre_lite_image:latest                        3 seconds ago   Up 4 seconds          0.0.0.0:8082->3001/tcp                                          vre_lite
<ID>          docker.io/library/mongo:6        bash -c sh /backu...  3 minutes ago   Up 3 minutes                                                                          mongo-backup
```

### Inspect podman network 

The **client**, **rest** and **mongodb** containers are in the same network. Execute the following instruction for inspecting the **podman network**:

```sh
podman network inspect data_network
```

It should show something like:

```json
[
     {
          "name": "data_network",
          "id": "<ID>",
          "driver": "bridge",
          "network_interface": "podman2",
          "created": "<DATE>",
          "subnets": [
               {
                    "subnet": "<IP>",
                    "gateway": "<IP>"
               }
          ],
          "ipv6_enabled": false,
          "internal": false,
          "dns_enabled": true,
          "ipam_options": {
               "driver": "host-local"
          }
     }
]
```

To verify container attachment:

```sh
podman inspect mongodb | grep -A5 Networks
```

Should yield:

```json
"Networks": {
    "data_network": {
        "EndpointID": "",
        "Gateway": "<IP>",
        "IPAddress": "<IP>",
        "IPPrefixLen": 24,
```

And **IPAddress** must be in the same **IP range** of **data_network**.

### Podman Stats

Check resources consumption for all running containers:

```sh
$ podman stats
ID            NAME        CPU %       MEM USAGE / LIMIT  MEM %       NET IO             BLOCK IO    PIDS        CPU TIME       AVG CPU %
<ID>          mongodb     0.54%       1.387GB / 8.59GB   16.15%      1.265GB / 432.2MB  0B / 0B     35          2m23.446427s   0.54%
<ID>          rest        0.34%       58.94MB / 10.74GB  0.55%       431.8MB / 3.166MB  0B / 0B     22          1m31.093332s   0.34%
<ID>          client      0.00%       11.12MB / 8.59GB   0.13%       241.8kB / 5.818MB  0B / 0B     17          110.229ms      0.00%
<ID>          minio       0.30%       183.4MB / 4.295GB  4.27%       965.7MB / 1.961GB  0B / 0B     47          1m20.610548s   0.30%
<ID>          vre_lite    3.61%       349.3MB / 4.295GB  8.13%       89.38kB / 3.219MB  0B / 0B     187         15m58.668698s  3.61%
<ID>          apache      0.03%       53.3MB / 1.074GB   4.96%       47.18MB / 964.3MB  0B / 0B     109         8.204261s      0.03%
```