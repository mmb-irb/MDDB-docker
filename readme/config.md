# Set Up Configuration Files

There are several **configuration files** that must be created and modified. As almost each of the different **docker blocks** of the project have **one or more** configuration files, this section is divided by these **blocks**:

* [Global](#global)
* [Client](#client)
* [Loader](#loader)
* [REST API](#rest-api)
* [VRE](#vre)
* [MongoDB](#mongodb)
* [Docker Compose](#docker-compose)

## Global

### .env file

⚠️ No sensible default value is provided for any of these fields, they **need to be defined** ⚠️

An `.env` file must be created in the **root** of the project. The file [**.env.git**](../.env.git) can be taken as an example. The file must contain the following environment variables:

| key              | value   | description                                     |
| ---------------- | ------- | ----------------------------------------------- |
| DOCKER_DEFAULT_PLATFORM         | string  | default platform (architecture and operating system), ie linux/amd64                               |
| NODE         | string  | node identifier to deploy                                     |
| LOADER_VOLUME_PATH         | string  | path where the loader will look for files                                        |
| LOADER_REPLICAS      | string  | number of replicas to deploy                                    |
| LOADER_CPU_LIMIT      | string  | loader limit number of CPUs                                    |
| LOADER_MEMORY_LIMIT          | string | loader limit memory                           |
| LOADER_CPU_RESERVATION          | string  | loader reserved number of CPUs                           |
| LOADER_MEMORY_RESERVATION      | string  | loader reserved memory                         |
| WORKFLOW_VOLUME_PATH         | string  | path where the workflow will save the files                                        |
| WORKFLOW_REPLICAS      | string  | number of replicas to deploy                                    |
| WORKFLOW_CPU_LIMIT      | string  | workflow limit number of CPUs                                    |
| WORKFLOW_MEMORY_LIMIT          | string | workflow limit memory                           |
| WORKFLOW_CPU_RESERVATION          | string  | workflow reserved number of CPUs                           |
| WORKFLOW_MEMORY_RESERVATION      | string  | workflow reserved memory                         |
| CLIENT_REPLICAS      | string  | number of replicas to deploy                                    |
| CLIENT_CPU_LIMIT    | string  | client limit number of CPUs                               |
| CLIENT_MEMORY_LIMIT    | string  | client limit memory                             |
| CLIENT_CPU_RESERVATION    | string  | client reserved number of CPUs                               |
| CLIENT_MEMORY_RESERVATION    | string  | client reserved memory                               |
| REST_REPLICAS      | string  | number of replicas to deploy                                    |
| REST_CPU_LIMIT    | string  | REST limit number of CPUs                               |
| REST_MEMORY_LIMIT    | string  | REST limit memory                             |
| REST_CPU_RESERVATION    | string  | REST reserved number of CPUs                               |
| REST_MEMORY_RESERVATION    | string  | REST reserved memory                               |
| DB_VOLUME_PATH         | string  | path where the DB will deploy the mongoDB file system                                        |
| DB_REPLICAS      | string  | number of replicas to deploy                                    |
| DB_CPU_LIMIT      | string  | DB limit number of CPUs                                    |
| DB_MEMORY_LIMIT          | string | DB limit memory                           |
| DB_CPU_RESERVATION          | string  | DB reserved number of CPUs                           |
| DB_MEMORY_RESERVATION      | string  | DB reserved memory                         |
| MINIO_VOLUME_PATH         | string  | path where MinIO will save / retrieve the files                                        |
| MINIO_REPLICAS      | string  | number of replicas to deploy                                    |
| MINIO_CPU_LIMIT      | string  | MinIO limit number of CPUs                                    |
| MINIO_MEMORY_LIMIT          | string | MinIO limit memory                           |
| MINIO_CPU_RESERVATION          | string  | MinIO reserved number of CPUs                           |
| MINIO_MEMORY_RESERVATION      | string  | MinIO reserved memory                         |
| VRE_VOLUME_PATH         | string  | path where the VRE will save the files                                        |
| VRE_REPLICAS      | string  | number of replicas to deploy                                    |
| VRE_CPU_LIMIT      | string  | VRE limit number of CPUs                                    |
| VRE_MEMORY_LIMIT          | string | VRE limit memory                           |
| VRE_CPU_RESERVATION          | string  | VRE reserved number of CPUs                           |
| VRE_MEMORY_RESERVATION      | string  | VRE reserved memory                         |
| MONGO_INITDB_ROOT_USERNAME      | string  | root user for the DB                         |
| MONGO_INITDB_ROOT_PASSWORD      | string  | root password for the DB                       |
| MINIO_ROOT_USER      | string  | MinIO user                         |
| MINIO_ROOT_PASSWORD      | string  | MinIO password                      |
| MINIO_BROWSER_REDIRECT_URL      | `<url>`  | MinIO base URL (full URI, ie http(s)://your-domain.com/minio)                      |

**Important:** the formats of **cpus** and **memory** must be in string format between single quotes, while **replicas** must be in integer format. Example:

```
VRE_VOLUME_PATH=/path/to/vre/data  # path to volume
VRE_REPLICAS=2  # number of replicas to deploy
VRE_CPU_LIMIT='4.00'  # cpus in float format
VRE_MEMORY_LIMIT='2G'  # memory indicating unit (G, M)
```

## Client

The client has its **own repository** with the builds for each node:

https://mmb.irbbarcelona.org/gitlab/gbayarri/mdposit-client-build

All the instructions for creating a **new build** are in this repository.

## Loader

### .env file

⚠️ No sensible default value is provided for any of these fields, they **need to be defined** ⚠️

An `.env` file must be created in the **loader** folder. The file [**.env.git**](../loader/.env.git) can be taken as an example. The file must contain the following environment variables (the DB user needs to have writing rights):

| key              | value   | description                                     |
| ---------------- | ------- | ----------------------------------------------- |
| DB_AUTH_USER         | string  | db user                                         |
| DB_AUTH_PASSWORD      | string  | db password                                     |
| DB_SERVER          | `<url>` | url of the db server                            |
| DB_PORT          | number  | port of the db server                           |
| DB_NAME      | string  | name of the dbcollection                        |
| DB_AUTHSOURCE    | string  | authentication db                               |

Example:

```
DB_SERVER=my_stack_mongodb
DB_PORT=27017
DB_NAME=mddb_db
DB_AUTH_USER=user_rw
DB_AUTH_PASSWORD=pwd_rw
DB_AUTHSOURCE=mddb_db
```

If deploying via **Docker Swarm**, the **DB_SERVER** must be **<stack_name>_<service_name>** where **stack_name** is the one used when [**deploying the stack**](docker-swarm.md#build-services) and **service_name** is the mongodb name of the service as defined in [**docker-compose.yml**](../docker-compose.yml) file.

If deploying via **Docker Compose**, the **DB_SERVER** must be the same name as the **mongodb container_name** in the [**docker-compose.yml**](../docker-compose-git.yml) file.

The **DB_NAME** and **DB_AUTHSOURCE** must be the same used in the [**mongo-init.js**](../mongo-init.js) file.

The credentials **DB_AUTH_USER** and **DB_AUTH_PASSWORD** must be the same defined in the [**mongo-init.js**](../mongo-init.js) file with the **readWrite** role.

## REST API

### .env file

⚠️ No sensible default value is provided for any of these fields, they **need to be defined** ⚠️

An `.env` file must be created in the **rest** folder. The file [**.env.git**](../rest/.env.git) can be taken as an example. The file must contain the following environment variables (the DB user needs to have reading rights):

| key              | value   | description                                     |
| ---------------- | ------- | ----------------------------------------------- |
| DB_AUTH_USER         | string  | db user                                         |
| DB_AUTH_PASSWORD      | string  | db password                                     |
| DB_SERVER          | `<url>` | url of the db server                            |
| DB_PORT          | number  | port of the db server                           |
| DB_NAME      | string  | name of the dbcollection                        |
| DB_AUTHSOURCE    | string  | authentication db                               |
| LISTEN_PORT    | number  | port to query the API                               |

Example:

```
DB_SERVER=my_stack_mongodb
DB_PORT=27017
DB_NAME=mddb_db
DB_AUTH_USER=user_r
DB_AUTH_PASSWORD=pwd_r
DB_AUTHSOURCE=mddb_db
LISTEN_PORT=3000
```

If deploying via **Docker Swarm**, the **DB_SERVER** must be **<stack_name>_<service_name>** where **stack_name** is the one used when [**deploying the stack**](docker-swarm.md#build-services) and **service_name** is the mongodb name of the service as defined in [**docker-compose.yml**](../docker-compose.yml) file.

If deploying via **Docker Compose**, the **DB_SERVER** must be the same name as the **mongodb container_name** in the [**docker-compose.yml**](../docker-compose-git.yml) file.

The **DB_NAME** and **DB_AUTHSOURCE** must be the same used in the [**mongo-init.js**](../mongo-init.js) file.

The credentials **DB_AUTH_USER** and **DB_AUTH_PASSWORD** must be the same defined in the [**mongo-init.js**](../mongo-init.js) file with the **read** role.

The **LISTEN_PORT** must be the same exposed in the [**REST Dockerfile**](../rest/Dockerfile).

## VRE

⚠️ No sensible default value is provided for any of these fields, they **need to be defined** ⚠️

An `.env` file must be created in the **vre** folder. The file [**.env.git**](../vre/.env.git) can be taken as an example. The file must contain the following environment variables:

| key              | value   | description                                     |
| ---------------- | ------- | ----------------------------------------------- |
| BASE_URL_DEVELOPMENT         | string  | baseURL for development                                        |
| BASE_URL_STAGING      | string  | baseURL for staging                                    |
| BASE_URL_PRODUCTION          | string | baseURL for production                            |
| DATA_PATH          | number  | path where the data will be saved (relative to the docker)                           |
| MAX_FILE_SIZE      | string  | maximum size for all the trajectory files in bytes                      |
| MINIO_URL    | `<url>`  | url for minio (ie localhost)                             |
| NODE_NAME    | number  | node identifier to deploy                               |

Example:

```
BASE_URL_DEVELOPMENT=/vre/
BASE_URL_STAGING=/vre/
BASE_URL_PRODUCTION=/vre/
DATA_PATH=/data
MAX_FILE_SIZE=1000000000
MINIO_URL=localhost
NODE_NAME=jsc
```

## MongoDB

### mongo-init.js file

This file is used for **initializing mongoDB** in docker-compose. It contains a script that **creates two users** in the **mddb_db** database: one with **read / write** permissions (it will be used by the **loader**) and the other with **read** permissions (it will be used by the **REST API**).

```js
// Switch to the desired database
db = db.getSiblingDB('mddb_db'); // Replace 'mddb_db' with your database name

// Create a user with readWrite permissions on 'mddb_db' database. This user will be used for the loader
db.createUser({
  user: 'user_rw',
  pwd: 'pwd_rw',
  roles: [
    { role: 'readWrite', db: 'mddb_db' }
  ]
});

// Create a user with read permissions on 'mddb_db' database. This user will be used for the REST API
db.createUser({
  user: 'user_r',
  pwd: 'pwd_r',
  roles: [
    { role: 'read', db: 'mddb_db' }
  ]
});
```

Please modify the values of **user** and **pwd** for both users and be sure that they match with the ones defined in the `.env` files of the **loader** and **rest** blocks.

## Docker Compose

Two **docker-compose.yml** files are provided for the sake of running the services either via **Docker Compose** or via **Docker Swarm**.

### docker-compose.yml file for Docker Swarm

For deploying via **Docker Swarm**, use the file [**docker-compose.yml**](../docker-compose.yml).

Take a look as well at the **client/rest ports**. They may change depending on the host configuration. Changing the ports **inside the containers** implies to change it as well in the [**client Dockerfile**](../client/Dockerfile) and in the [**REST API Dockerfile**](../rest/Dockerfile). If changing the ports **on the host machine**, take into account that they must mach with the ones defined in the [**Set Up of the Virtual Hosts**](setup.md#setting-up-virtual-hosts).

As for the **resources**, **paths** and client **NODE_ID**, all of these variables must be provided in the [**global .env file**](#global).

Finally, a root credentials **MONGO_INITDB_ROOT_USERNAME** and **MONGO_INITDB_ROOT_USERNAME** for the mongoDB database must be defined as well in the [**global .env file**](#global).

```yaml
services:
  loader:
    image: loader_image   # name of loader image
    build:
      context: ./loader   # folder to search Dockerfile for this image
    volumes:
      - loader_volume:/data   # path where the loader will look for files
    networks:
      - data_network
    deploy:
      replicas: ${LOADER_REPLICAS}  # Ensure this service is not deployed by default as it is a one-time task
      resources:
        limits:
          cpus: ${LOADER_CPU_LIMIT}   # Specify the limit number of CPUs
          memory: ${LOADER_MEMORY_LIMIT}   # Specify the limit memory
        reservations:
          cpus: ${LOADER_CPU_RESERVATION}   # Specify the reserved number of CPUs
          memory: ${LOADER_MEMORY_RESERVATION}   # Specify the reserved memory

  workflow:
    image: workflow_image
    build:
      context: ./workflow   # folder to search Dockerfile for this image
    volumes:
      - workflow_volume:/data  # path where the workflow will look for files
    deploy:
      replicas: ${WORKFLOW_REPLICAS}  # Ensure this service is not deployed by default as it is a one-time task
      resources:
        limits:
          cpus: ${WORKFLOW_CPU_LIMIT}   # Specify the limit number of CPUs
          memory: ${WORKFLOW_MEMORY_LIMIT}   # Specify the limit memory
        reservations:
          cpus: ${WORKFLOW_CPU_RESERVATION}   # Specify the reserved number of CPUs
          memory: ${WORKFLOW_MEMORY_RESERVATION}   # Specify the reserved memory

  client:
    image: client_image
    build:
      context: ./client  # folder to search Dockerfile for this image
      args:
        NODE_ID: ${NODE}  # Pass here the build argument with the node id
    ports:
      - "8080:80"  # port mapping, be aware that the second port is the same exposed in the client/Dockerfile
    deploy:
      replicas: ${CLIENT_REPLICAS}   # Specify the number of replicas for Docker Swarm
      resources:
        limits:
          cpus: ${CLIENT_CPU_LIMIT}   # Specify the limit number of CPUs
          memory: ${CLIENT_MEMORY_LIMIT}   # Specify the limit memory
        reservations:
          cpus: ${CLIENT_CPU_RESERVATION}   # Specify the reserved number of CPUs
          memory: ${CLIENT_MEMORY_RESERVATION}   # Specify the reserved memory
      restart_policy:
        condition: any   # Restart always
      update_config:
        order: start-first  # Priority over other services

  rest:
    image: rest_image
    build:
      context: ./rest   # folder to search Dockerfile for this image
    depends_on:
      - mongodb
    ports:
      - "8081:3000"   # port mapping, be aware that the second port is the same exposed in the rest/Dockerfile
    networks:
      - data_network
    deploy:
      replicas: ${REST_REPLICAS}   # Specify the number of replicas for Docker Swarm
      resources:
        limits:
          cpus: ${REST_CPU_LIMIT}   # Specify the limit number of CPUs
          memory: ${REST_MEMORY_LIMIT}   # Specify the limit memory
        reservations:
          cpus: ${REST_CPU_RESERVATION}   # Specify the reserved number of CPUs
          memory: ${REST_MEMORY_RESERVATION}   # Specify the reserved memory
      restart_policy:
        condition: any   # Restart always
      update_config:
        order: start-first  # Priority over other services

  mongodb:
    image: mongo:6
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_INITDB_ROOT_USERNAME}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_INITDB_ROOT_PASSWORD}
    ports:
      - "27017:27017"
    volumes:
      - ${DB_VOLUME_PATH}:/data/db  # path where the database will be stored (outside the container, in the host machine)
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro # path to the initialization script
    networks:
      - data_network
    deploy:
      replicas: ${DB_REPLICAS}   # Specify the number of replicas for Docker Swarm
      resources:
        limits:
          cpus: ${DB_CPU_LIMIT}    # Specify the limit number of CPUs
          memory: ${DB_MEMORY_LIMIT}   # Specify the limit memory
        reservations:
          cpus: ${DB_CPU_RESERVATION}   # Specify the reserved number of CPUs
          memory: ${DB_MEMORY_RESERVATION}   # Specify the reserved memory
      restart_policy:
        condition: on-failure   # Restart only on failure

 minio:
    image: minio/minio
    environment:
      - MINIO_ROOT_USER=${MINIO_ROOT_USER}
      - MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}
      - MINIO_SERVER_URL=${MINIO_SERVER_URL}  # Set the base URL for the Minio server
      - MINIO_BROWSER_REDIRECT_URL=${MINIO_BROWSER_REDIRECT_URL}  # Set the base URL for the Minio console
    volumes:
      - minio_volume:/data   # path where minio will store the data in object storage format (outside the container, in the host machine)
    ports:
      - "9000:9000"
      - "9001:9001"   # port for the minio console (only for development)
    networks:
      - vre_network
    deploy:
      replicas: ${MINIO_REPLICAS}   # Specify the number of replicas for Docker Swarm
      resources:
        limits:
          cpus: ${MINIO_CPU_LIMIT}    # Specify the limit number of CPUs
          memory: ${MINIO_MEMORY_LIMIT}   # Specify the limit memory
        reservations:
          cpus: ${MINIO_CPU_RESERVATION}   # Specify the reserved number of CPUs
          memory: ${MINIO_MEMORY_RESERVATION}   # Specify the reserved memory
      restart_policy:
        condition: on-failure   # Restart only on failure
    command: server /data --console-address ":9001"   # Command to run the minio console (only for development)
    healthcheck:  # Health check for the minio service
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 5

  vre:
    image: vre_image 
    build:
      context: ./vre
      args:
        MINIO_ROOT_USER: ${MINIO_ROOT_USER}
        MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - vre_volume:/data
    ports:
      - "8082:3001"
    networks:
      - vre_network
    depends_on:
      - minio
    deploy:
      replicas: ${VRE_REPLICAS}   # Specify the number of replicas for Docker Swarm
      resources:
        limits:
          cpus: ${VRE_CPU_LIMIT}   # Specify the limit number of CPUs
          memory: ${VRE_MEMORY_LIMIT}   # Specify the limit memory
        reservations:
          cpus: ${VRE_CPU_RESERVATION}   # Specify the reserved number of CPUs
          memory: ${VRE_MEMORY_RESERVATION}   # Specify the reserved memory
      restart_policy:
        condition: any   # Restart always
      update_config:
        order: start-first  # Priority over other services

volumes:
  loader_volume:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${LOADER_VOLUME_PATH}   # bind the volume to LOADER_VOLUME_PATH on the host
  workflow_volume:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${WORKFLOW_VOLUME_PATH}   # bind the volume to WORKFLOW_VOLUME_PATH on the host
  minio_volume:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${MINIO_VOLUME_PATH}   # bind the volume to MINIO_VOLUME_PATH on the host
  vre_volume:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${VRE_VOLUME_PATH}   # bind the volume to VRE_VOLUME_PATH on the host

networks:
  data_network: 
    external: true   # Use an external network
  vre_network: 
    external: true   # Use an external network
```

### docker-compose.yml file for Docker Compose

For deploying via **Docker Compose**, a`docker-compose.yml` file must be created in the root of the project. The file [**docker-compose-git.yml**](../docker-compose-git.yml) can be taken as an example.

Once created, open the **docker-compose.yml** with an editor and modify the volumes' routes.

Take a look as well at the **client/rest ports**. They may change depending on the host configuration. Changing the ports **inside the containers** implies to change it as well in the [**client Dockerfile**](../client/Dockerfile) and in the [**REST API Dockerfile**](../rest/Dockerfile). If changing the ports **on the host machine**, take into account that they must mach with the ones defined in the [**Set Up of the Virtual Hosts**](setup.md#setting-up-virtual-hosts).

As for the client, a **NODE_ID** with the **name of the node** must be provided.

Finally, a root credentials **MONGO_INITDB_ROOT_USERNAME** and **MONGO_INITDB_ROOT_USERNAME** for the mongoDB database must be defined as well in this file.

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
      - /path/to/loader/files:/data   # path in the host machine where the loader will look for files
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
      - /path/to/workflow/files:/data   # path in the host machine where the workflow will save the data

  client:
    image: client_image
    container_name: my_client
    platform: linux/amd64
    build:
      context: ./client  # folder to search Dockerfile for this image
      args:
        NODE_ID: NODE  # Pass here the build argument with the node id
    ports:
      - "8080:80"  # port mapping, be aware that the second port is the same exposed in the client/Dockerfile

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
    environment:
      MONGO_INITDB_ROOT_USERNAME: ROOT_USER
      MONGO_INITDB_ROOT_PASSWORD: ROOT_PASSWORD
    ports:
      - "27017:27017"
    volumes:
      - /path/to/db:/data/db  # path where the database will be stored (outside the container, in the host machine)
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro # path to the initialization script
    networks:
      - my_network

networks:
  my_network: 
    name: my_network    # network name
```