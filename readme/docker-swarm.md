# Execute Docker Swarm

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

In order to execute the **long-term** tasks in **Docker Swarm** and the **one-off tasks**, such as the **loader** or the **workflow**, in **Docker Compose**, the **networks** are declared as **external** in the **docker-compose.yml** file, so they must be created before the `docker-compose build` and the `docker stak deploy`:

```sh
docker network create --driver overlay --attachable data_network
```

> NOTE: **From July 2024 onwards**, the instruction for Docker Compose in **mac** is without hyphen, so from now on, `docker-compose build` is `docker compose build` when executing in **macOS**.

For building the services via **Docker Compose**, please execute the following instruction:

```sh
docker-compose build
```

Export environment variables defined in [**global .env file**](config.md#global) and deploy docker stack:

```sh
export $(grep -v '^#' .env | xargs)
docker stack deploy -c docker-compose.yml my_stack
```

Check services:

```sh
$ docker stack services my_stack
ID             NAME                MODE         REPLICAS   IMAGE                   PORTS
<ID>           my_stack_client     replicated   2/2        client_image:latest     *:8080->80/tcp
<ID>           my_stack_loader     replicated   0/0        loader_image:latest     
<ID>           my_stack_minio      replicated   1/1        minio/minio:latest      *:9000-9001->9000-9001/tcp
<ID>           my_stack_mongodb    replicated   1/1        mongo:6                 *:27017->27017/tcp
<ID>           my_stack_rest       replicated   4/4        rest_image:latest       *:8081->3000/tcp
<ID>           my_stack_vre        replicated   1/1        vre_image:latest        *:8082->3001/tcp
<ID>           my_stack_workflow   replicated   0/0        workflow_image:latest
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

Please read carefully the [**workflow help**](../workflow) as it has an extensive documentation. 

Example of running the workflow downloading an already **loaded trajectory** and saving the results into a **folder** that must be already created inside **WORKFLOW_VOLUME_PATH** defined in [**global .env**](config.md#global).

```sh
docker-compose run --rm workflow mwf run -proj <ACCESSION ID> -smp -e clusters energies pockets -dir /data/<folder>
```

Note that this run excludes clusters, energies and pockets analyses. Adding the -smp flag it downloads only 10 frames of the trajectory. As this instruction is a test, this will save a lot of computational time.

### Use loader

While the **mongodb**, **client** and **rest** containers will remain up, the **loader** must be called every time is needed. As it is a **one-off task**, **Docker Compose** is used for running it.

**List** database documents:

```sh
docker-compose run --rm loader list
```

**Load** documents to database:

```sh
docker-compose run --rm loader load /data/<trajectory_dir>
```

Take into account that **trajectory_dir** must be inside **LOADER_VOLUME_PATH** defined in [**global .env**](config.md#global).

**Remove** database document:

```sh
docker-compose run --rm loader delete <project_id>
```

### Check rest

Open a browser and type:

```
http://localhost:8081
```

Or modify the port 8081 by the one defined as **ports** in the **rest service** of the [**docker-compose.yml**](../docker-compose.yml) file. 

If the server has [**apache already configured**](setup.md#installation-and-configuration-of-apache), go to:

    http(s)://your_server_ip/api/rest/

### Check client

Open a browser and type:

```
http://localhost:8080
```

Or modify the port 8080 by the one defined as **ports** in the **client service** of the [**docker-compose.yml**](../docker-compose.yml) file. 

If the server has [**apache already configured**](setup.md#installation-and-configuration-of-apache), go to:

    http(s)://your_server_ip

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
CONTAINER ID   IMAGE                 COMMAND                  CREATED        STATUS        PORTS       NAMES
<ID>           rest_image:latest     "pm2-runtime start i…"   17 hours ago   Up 17 hours             3000/tcp    my_stack_rest.2.<ID>
<ID>           rest_image:latest     "pm2-runtime start i…"   17 hours ago   Up 17 hours             3000/tcp    my_stack_rest.1.<ID>
<ID>           rest_image:latest     "pm2-runtime start i…"   17 hours ago   Up 17 hours             3000/tcp    my_stack_rest.3.<ID>
<ID>           rest_image:latest     "pm2-runtime start i…"   17 hours ago   Up 17 hours             3000/tcp    my_stack_rest.4.<ID>
<ID>           mongo:6               "docker-entrypoint.s…"   17 hours ago   Up 17 hours             27017/tcp   my_stack_mongodb.1.<ID>
<ID>           client_image:latest   "/docker-entrypoint.…"   17 hours ago   Up 17 hours             80/tcp      my_stack_client.2.<ID>
<ID>           client_image:latest   "/docker-entrypoint.…"   17 hours ago   Up 17 hours             80/tcp      my_stack_client.1.<ID>
<ID>           minio/minio:latest    "/usr/bin/docker-ent…"   17 hours ago   Up 17 hours (healthy)   9000/tcp    my_stack_minio.1.<ID>
<ID>           vre_image:latest      "/app/entrypoint.sh"     17 hours ago   Up 17 hours             3001/tcp    my_stack_vre.1.<ID>
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
            "2fc8e2f395ee804abaa8add31ac7e718ecf4fd47a71dbc68a8309a39d778f35a": {
                "Name": "my_stack_rest.4.<ID>",
                "EndpointID": "<ID>",
                "MacAddress": "<MAC>",
                "IPv4Address": "<IP>",
                "IPv6Address": ""
            },
            "4f3e4b457ac2781704e4e195f2ae10d0898287152d55cca828c29b262c122c11": {
                "Name": "my_stack_rest.2.<ID>",
                "EndpointID": "<ID>",
                "MacAddress": "<MAC>",
                "IPv4Address": "<IP>",
                "IPv6Address": ""
            },
            "5ec96d93cf872482e118900ba0cb8a42ff444491b122283dd79b3416c28b1059": {
                "Name": "my_stack_rest.3.<ID>",
                "EndpointID": "<ID>",
                "MacAddress": "<MAC>",
                "IPv4Address": "<IP>",
                "IPv6Address": ""
            },
            "a47a078c1b0d359726d6e5f322315504648e53f6c311e19d6d9b37457675e4ed": {
                "Name": "my_stack_mongodb.1.<ID>",
                "EndpointID": "<ID>",
                "MacAddress": "<MAC>",
                "IPv4Address": "<IP>",
                "IPv6Address": ""
            },
            "f09f5aabfdb253900d0f445f692b0d877f14473a3155b49559add968f76f8065": {
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
<ID>           my_stack_vre.1.<ID>                            2.65%     384.5MiB / 4GiB     9.39%     1.5MB / 23kB      0B / 3.09MB   187
```