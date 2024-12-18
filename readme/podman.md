# Deploy Podman containers

In computing, **Podman** (pod manager) is an open source **Open Container Initiative** (OCI)-compliant container management tool from **Red Hat** used for handling **containers**, **images**, **volumes**, and **pods**.

**Podman** lets containers run **without root privileges** (rootless), meaning they can be **created**, **run**, and **managed** by regular users **without administrator rights**.

## Before building

### Load environment variables

Export environment variables defined in [**global .env file**](config.md#env-file):

```sh
export $(grep -v '^#' .env | xargs)
```

### Create networks

Create the **networks** needed for connecting all the **services**:

```sh
podman network create web_network
podman network create data_network
podman network create minio_network
```

## Build services

Below there are all the instructions needed for **building** all the **services**:

### REST API

```sh
podman build -t rest_image --build-arg DB_SERVER=${DB_SERVER} --build-arg DB_PORT=${DB_OUTER_PORT} --build-arg DB_NAME=${DB_NAME} --build-arg DB_AUTH_USER=${REST_DB_LOGIN} --build-arg DB_AUTH_PASSWORD=${REST_DB_PASSWORD} --build-arg DB_AUTHSOURCE=${DB_AUTHSOURCE} --build-arg REST_INNER_PORT=${REST_INNER_PORT} ./rest
```

### client

```sh
podman build -t client_image --build-arg NODE_ID=${NODE} --build-arg CLIENT_INNER_PORT=${CLIENT_INNER_PORT} ./client
```

### VRE lite

```sh
podman build -t vre_lite_image --build-arg MINIO_USER=${MINIO_USER} --build-arg MINIO_PASSWORD=${MINIO_PASSWORD} --build-arg MINIO_API_PORT=${MINIO_API_INNER_PORT} --build-arg VRE_LITE_INNER_PORT=${VRE_LITE_INNER_PORT} --build-arg VRE_LITE_BASE_URL_DEVELOPMENT=${VRE_LITE_BASE_URL_DEVELOPMENT} --build-arg VRE_LITE_BASE_URL_STAGING=${VRE_LITE_BASE_URL_STAGING} --build-arg VRE_LITE_BASE_URL_PRODUCTION=${VRE_LITE_BASE_URL_PRODUCTION} --build-arg VRE_LITE_LOG_PATH=${VRE_LITE_LOG_PATH} --build-arg VRE_LITE_MAX_FILE_SIZE=${VRE_LITE_MAX_FILE_SIZE} --build-arg VRE_LITE_TIME_DIFF=${VRE_LITE_TIME_DIFF} --build-arg MINIO_PROTOCOL=${MINIO_PROTOCOL} --build-arg MINIO_URL=${MINIO_URL} --build-arg MINIO_PORT=${APACHE_MINIO_OUTER_PORT} --build-arg NODE_NAME=${NODE} ./vre_lite
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

## Run services

In this section there are the instructions needed for running the **long-running tasks**.

### MongoDB service

```sh
podman run -d --name mongodb -e MONGO_INITDB_ROOT_USERNAME=${MONGO_INITDB_ROOT_USERNAME} -e MONGO_INITDB_ROOT_PASSWORD=${MONGO_INITDB_ROOT_PASSWORD} -e MONGO_PORT=${DB_OUTER_PORT} -e MONGO_INITDB_DATABASE=${DB_NAME} -e LOADER_DB_LOGIN=${LOADER_DB_LOGIN} -e LOADER_DB_PASSWORD=${LOADER_DB_PASSWORD} -e REST_DB_LOGIN=${REST_DB_LOGIN} -e REST_DB_PASSWORD=${REST_DB_PASSWORD} -p ${DB_OUTER_PORT}:${DB_OUTER_PORT} -v ${DB_VOLUME_PATH}:/data/db:Z -v $(pwd)/mongodb/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro --cpus "${DB_CPU_LIMIT}" --memory "${DB_MEMORY_LIMIT}" --network data_network --security-opt label=disable docker.io/library/mongo:6
```

### REST API

```sh
podman run -d --name rest -p ${REST_OUTER_PORT}:${REST_INNER_PORT} --cpus "${REST_CPU_LIMIT}" --memory "${REST_MEMORY_LIMIT}" --network data_network --network web_network rest_image
```

### client

```sh
podman run -d --name client -p ${CLIENT_OUTER_PORT}:${CLIENT_INNER_PORT} --cpus "${CLIENT_CPU_LIMIT}" --memory "${CLIENT_MEMORY_LIMIT}" --network web_network client_image
```

### Minio

```sh
podman run -d --name minio -e MINIO_ROOT_USER=${MINIO_ROOT_USER} -e MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD} -e MINIO_BROWSER_REDIRECT_URL=${MINIO_BROWSER_REDIRECT_URL} -e MINIO_API_INNER_PORT=${MINIO_API_INNER_PORT} -e MINIO_UI_INNER_PORT=${MINIO_UI_INNER_PORT} -e MINIO_USER=${MINIO_USER} -e MINIO_PASSWORD=${MINIO_PASSWORD} -p ${MINIO_API_OUTER_PORT}:${MINIO_API_INNER_PORT} -p ${MINIO_UI_INNER_PORT}:${MINIO_UI_INNER_PORT} -v ${MINIO_VOLUME_PATH1}:/mnt/disk1:Z -v ${MINIO_VOLUME_PATH2}:/mnt/disk2:Z -v ${MINIO_VOLUME_PATH3}:/mnt/disk3:Z -v ${MINIO_VOLUME_PATH4}:/mnt/disk4:Z -v $(pwd)/minio/init-minio.sh:/entrypoint.sh --cpus "${MINIO_CPU_LIMIT}" --memory "${MINIO_MEMORY_LIMIT}" --network minio_network --network web_network --hostname minio --entrypoint /entrypoint.sh --healthcheck-command "curl -f http://localhost:${MINIO_API_INNER_PORT}/minio/health/live" --healthcheck-interval 10s --healthcheck-timeout 2s --healthcheck-retries 5 docker.io/minio/minio:latest
```

### VRE lite

```sh
podman run -d --name vre_lite -p ${VRE_LITE_OUTER_PORT}:${VRE_LITE_INNER_PORT} -v ${VRE_LITE_VOLUME_PATH}:/vre_lite:Z --cpus "${MINIO_CPU_LIMIT}" --memory "${MINIO_MEMORY_LIMIT}" --network minio_network --network web_network vre_lite_image
```

### Apache

```sh
podman run -d --name apache -p ${APACHE_HTTP_OUTER_PORT}:${APACHE_HTTP_INNER_PORT} -p ${APACHE_HTTPS_OUTER_PORT}:${APACHE_HTTPS_INNER_PORT} -p ${APACHE_MINIO_OUTER_PORT}:${APACHE_MINIO_INNER_PORT} -v ${APACHE_CERTS_VOLUME_PATH}:/usr/local/apache2/conf/ssl:Z --cpus "${APACHE_CPU_LIMIT}" --memory "${APACHE_MEMORY_LIMIT}" --network web_network apache_image
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

#### Usual execution

Example of **running** the workflow from data **uploaded via VRE lite**:

```sh
podman run --rm -e BUCKET=<BUCKET> --network minio_network -v <WORKFLOW_VOLUME_PATH>:/data:Z --cpus "${WORKFLOW_CPU_LIMIT}" --memory "${WORKFLOW_MEMORY_LIMIT}" --cap-add SYS_ADMIN --device /dev/fuse --security-opt apparmor:unconfined workflow_image mwf run -dir /data/<OUTPUT_FOLDER> -md /data/<OUTPUT_FOLDER>/<REPLICA_FOLDER> /mnt/<FOLDER>/<TOPOLOGY> /mnt/<FOLDER>/<TRAJECTORY> -top /mnt/<FOLDER>/<TOPOLOGY> -inp /mnt/<FOLDER>/inputs.yaml -filt -ns
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
podman run --rm --name loader --cpus "${LOADER_CPU_LIMIT}" --memory "${LOADER_MEMORY_LIMIT}" --network data_network loader_image list
```

**Load** documents to database:

```sh
podman run --rm --network data_network -v <WORKFLOW_VOLUME_PATH>:/data:Z --cpus "${LOADER_CPU_LIMIT}" --memory "${LOADER_MEMORY_LIMIT}" loader_image load /data/<OUTPUT_FOLDER>
```

Take into account that **OUTPUT_FOLDER** must be inside **WORKFLOW_VOLUME_PATH**, defined in [**global .env**](config.md#env-file).

**Remove** database document:

```sh
podman run --rm --name loader --cpus "${LOADER_CPU_LIMIT}" --memory "${LOADER_MEMORY_LIMIT}" --network data_network loader_image delete <project_id>
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
CONTAINER ID  IMAGE                            COMMAND               CREATED      STATUS                PORTS                                                             NAMES
<ID>          docker.io/library/mongo:6        mongod                7 hours ago  Up 7 hours            0.0.0.0:27017->27017/tcp                                          mongodb
<ID>          localhost/rest_image:latest      pm2-runtime start...  7 hours ago  Up 7 hours            0.0.0.0:8081->3000/tcp                                            rest
<ID>          localhost/client_image:latest    nginx -g daemon o...  7 hours ago  Up 7 hours            0.0.0.0:8080->80/tcp                                              client
<ID>          docker.io/minio/minio:latest     server --address ...  7 hours ago  Up 7 hours (healthy)  0.0.0.0:9001-9002->9001-9002/tcp                                  minio
<ID>          localhost/vre_lite_image:latest                        7 hours ago  Up 7 hours            0.0.0.0:8082->3001/tcp                                            vre_lite
<ID>          localhost/apache_image:latest    httpd-foreground      7 hours ago  Up 7 hours            0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp, 0.0.0.0:9000->9000/tcp  apache
```

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