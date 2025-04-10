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

In order to execute the **long-term** tasks in **Docker Swarm** and the **one-off tasks**, such as the **loader** or the **workflow**, in **Docker Compose**, some of the **networks** are declared as **external** in the **docker-compose.yml** file, so they must be created before the `docker-compose build` and the `docker stak deploy`:

```sh
docker network create --driver overlay --attachable web_network
docker network create --driver overlay --attachable data_network
docker network create --driver overlay --attachable minio_network
```

> NOTE: **From July 2024 onwards**, the instruction for Docker Compose in **mac** is without hyphen, so from now on, `docker-compose build` is `docker compose build` when executing in **macOS**.

For building the services via **Docker Compose**, please execute the following instruction:

```sh
docker-compose build
```

Export environment variables defined in [**global .env file**](config.md#env-file) and deploy docker stack:

```sh
export $(grep -v '^#' .env | xargs)
docker stack deploy -c docker-compose.yml my_stack
```

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

## Execute services

Once the installation is finished, it's time to **execute** and **check** the different services.

### Use workflow

While the **mongodb**, **client** and **rest** containers will remain up, the **workflow** must be called every time is needed. As it is a **one-off task**, **Docker Compose** is used for running it.

Workflow **help**:

```sh
docker-compose run --rm workflow mwf -h
```

Or, if the above doesn't work:

```sh
docker run --rm workflow_image mwf -h
```

Please read carefully the [**workflow help**](../workflow) as it has an extensive documentation. 

#### Plain execution

Example of **running** the workflow downloading an already **loaded trajectory** and saving the results into an **OUTPUT_FOLDER** that must be already created inside **WORKFLOW_VOLUME_PATH** defined in [**global .env**](config.md#env-file).

```sh
docker-compose run --rm workflow mwf run -proj <ACCESSION ID> -smp -e clusters energies pockets -dir /data/<OUTPUT_FOLDER>
```

Or, if the above doesn't work:

```sh
docker run --rm workflow_image -v <WORKFLOW_VOLUME_PATH>:/data --cpus "${WORKFLOW_CPU_LIMIT}" --memory "${WORKFLOW_MEMORY_LIMIT}" mwf run -proj <ACCESSION ID> -smp -e clusters energies pockets -dir /data/<OUTPUT_FOLDER>
```

Note that this run excludes clusters, energies and pockets analyses. Adding the -smp flag it downloads only 10 frames of the trajectory. As this instruction is a test, this will save a lot of computational time.

#### Usual execution

Example of **running** the workflow from data **uploaded via VRE lite**:

```sh
docker-compose run --rm -e BUCKET=<BUCKET> workflow mwf run -dir /data/<OUTPUT_FOLDER> -md /data/<OUTPUT_FOLDER>/<REPLICA_FOLDER> /mnt/<FOLDER>/<TOPOLOGY> /mnt/<FOLDER>/<TRAJECTORY> -top /mnt/<FOLDER>/<TOPOLOGY> -inp /mnt/<FOLDER>/inputs.yaml -filt -ns
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
docker-compose run --rm loader list
```

Or, if the above doesn't work:

```sh
docker run --rm --network data_network --cpus "${LOADER_CPU_LIMIT}" --memory "${LOADER_MEMORY_LIMIT}" loader_image list
```

**Load** documents to database:

```sh
docker-compose run --rm loader load /data/<OUTPUT_FOLDER>
```

Or, if the above doesn't work:

```sh
docker run --rm --network data_network -v <WORKFLOW_VOLUME_PATH>:/data --cpus "${LOADER_CPU_LIMIT}" --memory "${LOADER_MEMORY_LIMIT}" loader_image load -a <ACCESSION> /data/<OUTPUT_FOLDER>
```

Take into account that **OUTPUT_FOLDER** must be inside **WORKFLOW_VOLUME_PATH**, defined in [**global .env**](config.md#env-file).

**Remove** database document:

```sh
docker-compose run --rm loader delete <project_id>
```

Or, if the above doesn't work:

```sh
docker run --rm --network data_network --cpus "${LOADER_CPU_LIMIT}" --memory "${LOADER_MEMORY_LIMIT}" loader_image delete <project_id>
```

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