# Execute Docker Compose

Docker Compose is a tool for defining and running **multi-container applications**. It is the key to unlocking a streamlined and efficient development and deployment experience.

Compose **simplifies** the control of your entire application stack, making it easy to manage **services**, **networks**, and **volumes** in a single, comprehensible YAML configuration file. Then, with a single command, you **create** and **start** all the services from your configuration file.

## Build services

For building the services via **Docker Compose**, please execute the following instruction from the same folder where the [**docker-compose.yml**](../compose/docker-compose-git.yml) file is:

```sh
docker-compose up -d
```

This instruction will run **docker-compose** in **background** and it will create the **services** described in the first section.

> NOTE: **From July 2024 onwards**, the instruction for Docker Compose in **mac** is without hyphen, so from now on, `docker-compose up -d` is `docker compose up -d` when executing in **macOS**.

## Execute services

Once the installation is finished, it's time to **execute** and **check** the different services.

### Use workflow

While the **mongodb**, **client** and **rest** containers will remain up, the **workflow** must be called every time is needed.

Workflow **help**:

```sh
docker-compose run workflow mwf -h
```

Please read carefully the [**workflow help**](../workflow) as it has an extensive documentation. 

Example of running the workflow downloading an already **loaded trajectory** and saving the results into a **folder** that must be **inside the volume** defined in the [**docker-compose.yml**](../compose/docker-compose-git.yml) file.

```sh
docker-compose run workflow mwf run -proj <ACCESSION ID> -smp -e clusters energies pockets -dir <FOLDER>
```

Note that this run excludes clusters, energies and pockets analyses. Adding the -smp flag it downloads only 10 frames of the trajectory. As this instruction is a test, this will save a lot of computational time.

### Use loader

While the **mongodb**, **client** and **rest** containers will remain up, the **loader** must be called every time is needed.

**List** database documents:

```sh
docker-compose run loader list
```

**Load** documents to database:

```sh
docker-compose run loader load <trajectory_dir>
```

Take into account that **trajectory_dir** must be inside **/path/to/loader/files** defined in [**docker-compose.yml**](../compose/docker-compose-git.yml).

**Remove** database document:

```sh
docker-compose run loader delete <project_id>
```

### Check rest

Open a browser and type:

```
http://localhost:8081
```

Or modify the port 8081 by the one defined as **ports** in the **rest service** of the [**docker-compose.yml**](../compose/docker-compose-git.yml) file. 

If the server has [**apache already configured**](setup.md#installation-and-configuration-of-apache), go to:

    http(s)://your_server_ip/api/rest/

### Check client

Open a browser and type:

```
http://localhost:8080
```

Or modify the port 8080 by the one defined as **ports** in the **client service** of the [**docker-compose.yml**](../compose/docker-compose-git.yml) file. 

If the server has [**apache already configured**](setup.md#installation-and-configuration-of-apache), go to:

    http(s)://your_server_ip

## Stop / start services

For **stopping** all the services (client, rest and mongodb):

```sh
docker-compose stop
```

For **stopping** all the services (client, rest and mongodb) and **remove** all up images:

```sh
docker-compose down
```

For **starting** all the services (client, rest and mongodb):

```sh
docker-compose start
```

## Check

### Check containers

Check that at least the mongo, rest and client containers are up & running:

```sh
$ docker ps -a
CONTAINER ID   IMAGE            COMMAND                  CREATED              STATUS                          PORTS                                       NAMES
XXXXXXXXXXXX   rest_image       "pm2-runtime start i…"   About a minute ago   Up About a minute               0.0.0.0:8081->3000/tcp, :::8081->3000/tcp   my_rest
XXXXXXXXXXXX   loader_image     "/app/entrypoint.sh"     About a minute ago   Exited (1) About a minute ago                                               my_loader
XXXXXXXXXXXX   mongo:6          "docker-entrypoint.s…"   About a minute ago   Up About a minute               27017/tcp                                   my_mongo_container
XXXXXXXXXXXX   client_image     "/docker-entrypoint.…"   About a minute ago   Up About a minute               0.0.0.0:8080->80/tcp, :::8080->80/tcp       my_client
XXXXXXXXXXXX   workflow_image   "conda run --no-capt…"   About a minute ago   Exited (0) About a minute ago                                               my_workflow
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
        "Scope": "local",
        "Driver": "bridge",
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
        "Attachable": false,
        "Ingress": false,
        "ConfigFrom": {
            "Network": ""
        },
        "ConfigOnly": false,
        "Containers": {
            "<ID>": {
                "Name": "my_rest",
                "EndpointID": "<ID>",
                "MacAddress": "<MAC>",
                "IPv4Address": "<IP>",
                "IPv6Address": ""
            },
            "<ID>": {
                "Name": "my_mongo_container",
                "EndpointID": "<ID>",
                "MacAddress": "<MAC>",
                "IPv4Address": "<IP>",
                "IPv6Address": ""
            }
        },
        "Options": {},
        "Labels": {
            "com.docker.compose.network": "my_network",
            "com.docker.compose.project": "mddb-docker",
            "com.docker.compose.version": "2.29.0"
        }
    }
]
```