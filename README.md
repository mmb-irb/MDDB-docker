
# MDDB Docker web services

TODO description

## Services description

### Website

TODO

### Data loader

The data loader is a node **JS script** made for load, list and remove data from a mongodb database.

For this project, the following repo has been used:

https://mmb.irbbarcelona.org/gitlab/aluciani/MoDEL-CNS_DB_loader

### Database

The database used is **mongodb** inside a docker container:

https://github.com/docker-library/mongo

For this project, the choosen version of mongo is 6.

## Prepare configuration files

### docker-compose.yml

Copy docker-compose-git.yml into **docker-compose.yml** and modify the volumes' routes. 

Take a look as well at the **website ports**. They may change depending on the host configuration. Changing the port implies to change it as well in the [**website/Dockerfile**](website/Dockerfile). (TODO rest/client!!!)

```yaml


services:
  loader:
    image: loader_image   # name of loader image
    container_name: my_loader   # name of loader container
    platform: linux/amd64
    build:
      context: ./loader   # folder to search Dockerfile for this image
    depends_on:
      - mongodb
    working_dir: /data
    volumes:
      - /path/to/loader/files:/data   # path where the loader will look for files
    networks:
      - my_network

  workflow:
    image: workflow_image
    container_name: my_workflow
    platform: linux/amd64
    build:
      context: ./workflow   # folder to search Dockerfile for this image
    working_dir: /data
    volumes:
      - /path/to/workflow/files:/data

  rest:
    image: rest_image
    container_name: my_rest
    platform: linux/amd64
    build:
      context: ./rest   # folder to search Dockerfile for this image
    depends_on:
      - mongodb
    ports:
      - "8081:3000"   # port mapping, be aware that the second port is the same exposed in the rest/Dockerfile
    networks:
      - my_network

  mongodb:
    container_name: my_mongo_container
    image: mongo:6
    volumes:
      - /path/to/db:/data/db  # path where the database will be stored (outside the container, in the host machine)
    networks:
      - my_network

networks:
  my_network: 
    name: my_network    # network name
```

### .env file

⚠️ No sensible default value is provided for any of these fields, they **need to be defined** ⚠️

An `.env` file must be created both in the **loader**, **rest** and **client** folders. The file `.env.git` can be taken as an example. The file must contain the following environment variables (the DB user needs to have writing rights):

#### loader

| key              | value   | description                                     |
| ---------------- | ------- | ----------------------------------------------- |
| DB_AUTH_USER         | string  | db user                                         |
| DB_AUTH_PASSWORD      | string  | db password                                     |
| DB_SERVER          | `<url>` | url of the db server                            |
| DB_PORT          | number  | port of the db server                           |
| DB_NAME      | string  | name of the dbcollection                        |
| DB_AUTHSOURCE    | string  | authentication db                               |

Take into account that, by default, the **mongodb docker** is configured **without authentication**. So, if following the instructions of this README, leave **DB_AUTH_USER** and **DB_AUTH_PASSWORD** empty. Example:

```
DB_SERVER=my_mongo_container
DB_PORT=27017
DB_NAME=<DB NAME>
DB_AUTH_USER=
DB_AUTH_PASSWORD=
DB_AUTHSOURCE=<DB NAME>
```

The **DB_SERVER** must be the same name as the **mongodb container_name** in the **docker-compose.yml**.

#### rest 

| key              | value   | description                                     |
| ---------------- | ------- | ----------------------------------------------- |
| DB_AUTH_USER         | string  | db user                                         |
| DB_AUTH_PASSWORD      | string  | db password                                     |
| DB_SERVER          | `<url>` | url of the db server                            |
| DB_PORT          | number  | port of the db server                           |
| DB_NAME      | string  | name of the dbcollection                        |
| DB_AUTHSOURCE    | string  | authentication db                               |
| LISTEN_PORT    | number  | port to query the API                               |

Take into account that, by default, the **mongodb docker** is configured **without authentication**. So, if following the instructions of this README, leave **DB_AUTH_USER** and **DB_AUTH_PASSWORD** empty. Example:

```
DB_SERVER=my_mongo_container
DB_PORT=27017
DB_NAME=<DB NAME>
DB_AUTH_USER=
DB_AUTH_PASSWORD=
DB_AUTHSOURCE=<DB NAME>
LISTEN_PORT=3000
```

The **DB_SERVER** must be the same name as the **mongodb container_name** in the **docker-compose.yml**.

The **LISTEN_PORT** must be the same exposed in the [REST Dockerfile](rest/Dockerfile).

#### client

As of July 2024, an **empty .env file** must be provided in the **client folder**.

## Build services

For building the services via **docker compose**, please execute the following instruction from the root of this project:

```sh
docker-compose up -d
```

This instruction will run docker-compose in background and it will create the three services described in the first section.

## Execute services

### Use loader

While the mongodb and website containers will remain up, the loader must be called every time is needed.

**List** database documents:

```sh
docker-compose run loader list
```

**Load** documents to database:

```sh
docker-compose run loader load <trajectory_dir>
```

Take into account that **trajectory_dir** must be inside **/path/to/loader/files** defined in **docker-compose.yml**.

**Remove** database document:

```sh
docker-compose run loader delete <project_id>
```

### Check rest

Open a browser and type:

```
http://localhost:8081
```

Or modify the port 8081 by the one defined as **ports** in the **rest service** of the **docker-compose.yml** file.

### Check client

Open a browser and type:

```
http://localhost:8080
```

Or modify the port 8080 by the one defined as **ports** in the **client service** of the **docker-compose.yml** file.

## Stop / start services

For **stopping** all the services (website and mongodb):

```sh
docker-compose stop
```

For **stopping** all the services (website and mongodb) and **remove** all up images:

```sh
docker-compose down
```

For **starting** all the services (website and mongodb):

```sh
docker-compose start
```

## Tips

### Avoid cache for docker-compose

Ie when developing and doing changes in git repo.

1. Stop all containers and remove all images: 

    ```sh
    docker-compose down --rmi all
    ```

2. Rebuild images avoiding cache:

    ```sh
    docker-compose build --no-cache
    ```

3. Up services:
    ```sh
    docker-compose up -d
    ```

### Execute mongo docker in terminal mode

```sh
docker exec -it my_mongo_container bash
```

And then: 

```sh
mongosh 
```

For entering the database in terminal mode. By default, the mongodb docker is configured **without authentication**.

### Check containers

TODO

### Inspect docker network 

Execute the following instruction for inspecting the **docker network**:

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

### Docker logs

Show logs for a container:

```sh
docker logs my_rest
```

## Credits

Daniel Beltran, Genís Bayarri, Adam Hospital.

## Copyright & licensing

This website has been developed by the [MMB group](https://mmb.irbbarcelona.org) at the [IRB Barcelona](https://irbbarcelona.org).

© 2024 **Institute for Research in Biomedicine**

Licensed under the **Apache License 2.0**.