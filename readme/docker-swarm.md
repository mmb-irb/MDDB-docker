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

In order to execute the **long-term** tasks in **Docker Swarm** and the **one-off tasks**, such as the **loader** or the **workflow**, in **Docker Compose**, the **network** is declared as **external** in the **docker-compose.yml** file, so it must be created before the `docker-compose build` and the `docker stak deploy`:

```sh
docker network create --driver overlay --attachable my_network
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
docker stack services my_stack
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
<ID>           rest_image:latest     "pm2-runtime start i…"   20 hours ago   Up 20 hours   3000/tcp    my_stack_rest.3.<ID>
<ID>           rest_image:latest     "pm2-runtime start i…"   20 hours ago   Up 20 hours   3000/tcp    my_stack_rest.1.<ID>
<ID>           mongo:6               "docker-entrypoint.s…"   20 hours ago   Up 20 hours   27017/tcp   my_stack_mongodb.1.<ID>
<ID>           rest_image:latest     "pm2-runtime start i…"   20 hours ago   Up 20 hours   3000/tcp    my_stack_rest.4.<ID>
<ID>           rest_image:latest     "pm2-runtime start i…"   20 hours ago   Up 20 hours   3000/tcp    my_stack_rest.2.<ID>
<ID>           client_image:latest   "/docker-entrypoint.…"   20 hours ago   Up 20 hours   80/tcp      my_stack_client.1.<ID>
<ID>           client_image:latest   "/docker-entrypoint.…"   20 hours ago   Up 20 hours   80/tcp      my_stack_client.2.<ID>
```

### Inspect docker network 

The **client**, **rest** and **mongodb** containers are in the same network. Execute the following instruction for inspecting the **docker network**:

```sh
docker network inspect my_network
```

It should show something like:

```json
[
    {
        "Name": "my_network",
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
            "lb-my_network": {
                "Name": "my_network-endpoint",
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
docker stats
```