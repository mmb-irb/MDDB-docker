# Set Up Configuration Files

* [.env file](#env-file)
* [MongoDB](#mongodb)
* [Docker Compose](#docker-compose)

## .env file

⚠️ No sensible default value is provided for any of these fields, they **need to be defined** ⚠️

An `.env` file must be created in the **root** of the project. The file [**.env.git**](../.env.git) can be taken as an example. The file must contain the following environment variables:

| key              | value   | description                                     |
| ---------------- | ------- | ----------------------------------------------- |
| DOCKER_DEFAULT_PLATFORM         | string  | default platform (architecture and operating system), ie linux/amd64                               |
| NODE         | string  | node identifier to deploy                                     |
| &nbsp;
| APACHE_HTTP_OUTER_PORT         | number  | apache outer port for http protocol                                        |
| APACHE_HTTPS_OUTER_PORT         | number  | apache outer port for https protocol                                        |
| APACHE_MINIO_OUTER_PORT         | number  | apache outer port for MinIO API                                         |
| APACHE_HTTP_INNER_PORT         | number  | apache inner port for http protocol                                        |
| APACHE_HTTPS_INNER_PORT         | number  | apache inner port for https protocol                                        |
| APACHE_MINIO_INNER_PORT         | number  | apache inner port for MinIO API                                        |
| APACHE_CERTS_VOLUME_PATH         | string  | path where the SSL certificates are stored                                |
| APACHE_REPLICAS         | number  | apache number of replicas to deploy                                        |
| APACHE_CPU_LIMIT         | string  | apache limit number of CPUs                                        |
| APACHE_MEMORY_LIMIT         | string  | apache limit memory                                        |
| APACHE_CPU_RESERVATION         | string  | apache reserved number of CPUs                                        |
| APACHE_MEMORY_RESERVATION         | string  | apache reserved memory                                        |
| &nbsp;
| LOADER_VOLUME_PATH         | string  | path where the loader will look for files                                        |
| LOADER_REPLICAS      | string  | number of replicas to deploy                                    |
| LOADER_CPU_LIMIT      | string  | loader limit number of CPUs                                    |
| LOADER_MEMORY_LIMIT          | string | loader limit memory                           |
| LOADER_CPU_RESERVATION          | string  | loader reserved number of CPUs                           |
| LOADER_MEMORY_RESERVATION      | string  | loader reserved memory                         |
| LOADER_DB_LOGIN      | string  | db user for loader                         |
| LOADER_DB_PASSWORD      | string  | db password for loader                       |
| &nbsp;
| WORKFLOW_VOLUME_PATH         | string  | path where the workflow will save the files                                        |
| WORKFLOW_REPLICAS      | string  | number of replicas to deploy                                    |
| WORKFLOW_CPU_LIMIT      | string  | workflow limit number of CPUs                                    |
| WORKFLOW_MEMORY_LIMIT          | string | workflow limit memory                           |
| WORKFLOW_CPU_RESERVATION          | string  | workflow reserved number of CPUs                           |
| WORKFLOW_MEMORY_RESERVATION      | string  | workflow reserved memory                         |
| &nbsp;
| CLIENT_REPLICAS      | string  | number of replicas to deploy                                    |
| CLIENT_OUTER_PORT         | number  | client outer port                                         |
| CLIENT_INNER_PORT         | number  | client inner port                                         |
| CLIENT_CPU_LIMIT    | string  | client limit number of CPUs                               |
| CLIENT_MEMORY_LIMIT    | string  | client limit memory                             |
| CLIENT_CPU_RESERVATION    | string  | client reserved number of CPUs                               |
| CLIENT_MEMORY_RESERVATION    | string  | client reserved memory                               |
| &nbsp;
| REST_REPLICAS      | string  | number of replicas to deploy                                    |
| REST_OUTER_PORT         | number  | REST outer port                                         |
| REST_INNER_PORT         | number  | REST inner port                                         |
| REST_CPU_LIMIT    | string  | REST limit number of CPUs                               |
| REST_MEMORY_LIMIT    | string  | REST limit memory                             |
| REST_CPU_RESERVATION    | string  | REST reserved number of CPUs                               |
| REST_MEMORY_RESERVATION    | string  | REST reserved memory                               |
| REST_DB_LOGIN    | string  | db user for website REST API                               |
| REST_DB_PASSWORD    | string  | db password for website REST API                               |
| &nbsp;
| DB_VOLUME_PATH         | string  | path where the DB will deploy the mongoDB file system                                        |
| DB_REPLICAS      | string  | number of replicas to deploy                                    |
| DB_OUTER_PORT         | number  | DB outer port                                         |
| DB_INNER_PORT         | number  | DB inner port                                         |
| DB_CPU_LIMIT      | string  | DB limit number of CPUs                                    |
| DB_MEMORY_LIMIT          | string | DB limit memory                           |
| DB_CPU_RESERVATION          | string  | DB reserved number of CPUs                           |
| DB_MEMORY_RESERVATION      | string  | DB reserved memory                         |
| DB_SERVER      | `<url>`  | url of the db server                          |
| DB_NAME      | string  | name of the  DB collection                          |
| DB_AUTHSOURCE      | string  | the DB collection the user will attempt to authenticate to                           |
| &nbsp;
| MINIO_VOLUME_PATH         | string  | path where MinIO will save / retrieve the files                                        |
| MINIO_REPLICAS      | string  | number of replicas to deploy                                    |
| MINIO_API_OUTER_PORT         | number  | MinIO API outer port                                         |
| MINIO_API_INNER_PORT         | number  | MinIO API inner port                                         |
| MINIO_UI_OUTER_PORT         | number  | MinIO WebUI outer port                                         |
| MINIO_UI_INNER_PORT         | number  | MinIO WebUI inner port                                         |
| MINIO_CPU_LIMIT      | string  | MinIO limit number of CPUs                                    |
| MINIO_MEMORY_LIMIT          | string | MinIO limit memory                           |
| MINIO_CPU_RESERVATION          | string  | MinIO reserved number of CPUs                           |
| MINIO_MEMORY_RESERVATION      | string  | MinIO reserved memory                         |
| MINIO_PROTOCOL      | string  | MinIO API protocol (http|https)                        |
| MINIO_URL      | `<url>`  | url for MinIO (ie localhost)                          |
| &nbsp;
| VRE_LITE_VOLUME_PATH         | string  | path where the VRE lite will save the files                                        |
| VRE_LITE_REPLICAS      | string  | number of replicas to deploy                                    |
| VRE_LITE_OUTER_PORT         | number  | VRE lite outer port                                         |
| VRE_LITE_INNER_PORT         | number  | VRE lite inner port                                         |
| VRE_LITE_CPU_LIMIT      | string  | VRE lite limit number of CPUs                                    |
| VRE_LITE_MEMORY_LIMIT          | string | VRE lite limit memory                           |
| VRE_LITE_CPU_RESERVATION          | string  | VRE lite reserved number of CPUs                           |
| VRE_LITE_MEMORY_RESERVATION      | string  | VRE lite reserved memory                         |
| VRE_LITE_BASE_URL_DEVELOPMENT         | string  | VRE lite baseURL for development                                        |
| VRE_LITE_BASE_URL_STAGING      | string  | VRE lite baseURL for staging                                    |
| VRE_LITE_BASE_URL_PRODUCTION          | string | VRE lite baseURL for production                            |
| VRE_LITE_DATA_PATH          | string  | path where the data will be saved (relative to the docker)                           |
| VRE_LITE_MAX_FILE_SIZE      | number  | maximum size for all the trajectory files in bytes                      |
| &nbsp;
| MONGO_INITDB_ROOT_USERNAME      | string  | root user for the DB                         |
| MONGO_INITDB_ROOT_PASSWORD      | string  | root password for the DB                       |
| &nbsp;
| MINIO_ROOT_USER      | string  | MinIO user                         |
| MINIO_ROOT_PASSWORD      | string  | MinIO password                      |
| MINIO_BROWSER_REDIRECT_URL      | `<url>`  | MinIO base URL (full URI, ie http(s)://your-domain.com/minio)                      |

**Important:** the formats of **cpus** and **memory** must be in string format between single quotes, while **replicas** must be in integer format. Example:

```
VRE_LITE_VOLUME_PATH=/path/to/vre/data  # path to volume
VRE_LITE_REPLICAS=2  # number of replicas to deploy
VRE_LITE_CPU_LIMIT='4.00'  # cpus in float format
VRE_LITE_MEMORY_LIMIT='2G'  # memory indicating unit (G, M)
```

Tthe **DB_SERVER** must be **<stack_name>_<service_name>** where **stack_name** is the one used when [**deploying the stack**](docker-swarm.md#build-services) and **service_name** is the mongodb name of the service as defined in [**docker-compose.yml**](../docker-compose.yml) file.

The **DB_NAME** and **DB_AUTHSOURCE** must be the same used in the [**mongo-init.js**](../mongo-init.js) file.

The credentials **LOADER_DB_LOGIN** and **LOADER_DB_PASSWORD** must be the same defined in the [**mongo-init.js**](../mongo-init.js) file with the **readWrite** role.

The credentials **REST_DB_LOGIN** and **REST_DB_PASSWORD** must be the same defined in the **mongo-init.js** file with the **read** role.

Neither the **VRE_LITE_BASE_URL_DEVELOPMENT** nor the **VRE_LITE_BASE_URL_STAGING** shouldn't be used when running as a docker service. 

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

The [**docker-compose.yml**](./docker-compose.yml) is the file that specifies what **images** are required, what **ports** they need to expose, whether they have access to the host **filesystem**, what **commands** should be run when they start up, and so on.

All the configurable variables such as **resources**, **paths**, **ports** and so on must be defined in the [**global .env file**](#env-file).

```yaml
services:
  apache:
    image: apache_image   # name of apache image
    build:
      context: ./apache   # folder to search Dockerfile for this image
      args:
        APACHE_HTTP_INNER_PORT: ${APACHE_HTTP_INNER_PORT}
        APACHE_HTTPS_INNER_PORT: ${APACHE_HTTPS_INNER_PORT}
        APACHE_HTTP_OUTER_PORT: ${APACHE_HTTP_OUTER_PORT}
        APACHE_HTTPS_OUTER_PORT: ${APACHE_HTTPS_OUTER_PORT}
        APACHE_MINIO_OUTER_PORT: ${APACHE_MINIO_OUTER_PORT}
        APACHE_MINIO_INNER_PORT: ${APACHE_MINIO_INNER_PORT}
        CLIENT_INNER_PORT: ${CLIENT_INNER_PORT}
        REST_INNER_PORT: ${REST_INNER_PORT}
        VRE_LITE_INNER_PORT: ${VRE_LITE_INNER_PORT}
        MINIO_UI_INNER_PORT: ${MINIO_UI_INNER_PORT}
        MINIO_API_INNER_PORT: ${MINIO_API_INNER_PORT}
        SERVER_URL: ${MINIO_URL}
    ports:
      - "${APACHE_HTTP_OUTER_PORT}:${APACHE_HTTP_INNER_PORT}"   # http port mapping
      - "${APACHE_HTTPS_OUTER_PORT}:${APACHE_HTTPS_INNER_PORT}"   # https port mapping
      - "${APACHE_MINIO_OUTER_PORT}:${APACHE_MINIO_INNER_PORT}"      # minio console port mapping
    networks:
      - web_network
    deploy:
      replicas: ${APACHE_REPLICAS}  # Ensure this service is not deployed by default as it is a one-time task
      resources:
        limits:
          cpus: ${APACHE_CPU_LIMIT}   # Specify the limit number of CPUs
          memory: ${APACHE_MEMORY_LIMIT}   # Specify the limit memory
        reservations:
          cpus: ${APACHE_CPU_RESERVATION}   # Specify the reserved number of CPUs
          memory: ${APACHE_MEMORY_RESERVATION}   # Specify the reserved memory
      restart_policy:
        condition: any   # Restart always

  loader:
    image: loader_image   # name of loader image
    build:
      context: ./loader   # folder to search Dockerfile for this image
      args:
        DB_SERVER: ${DB_SERVER}
        DB_PORT: ${DB_OUTER_PORT}
        DB_NAME: ${DB_NAME}
        DB_AUTH_USER: ${LOADER_DB_LOGIN}
        DB_AUTH_PASSWORD: ${LOADER_DB_PASSWORD}
        DB_AUTHSOURCE: ${DB_AUTHSOURCE}
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
        CLIENT_INNER_PORT: ${CLIENT_INNER_PORT}
    ports:
      - "${CLIENT_OUTER_PORT}:${CLIENT_INNER_PORT}"  # port mapping
    networks:
      - web_network
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
      args:
        DB_SERVER: ${DB_SERVER}
        DB_PORT: ${DB_OUTER_PORT}
        DB_NAME: ${DB_NAME}
        DB_AUTH_USER: ${REST_DB_LOGIN}
        DB_AUTH_PASSWORD: ${REST_DB_PASSWORD}
        DB_AUTHSOURCE: ${DB_AUTHSOURCE}
        REST_INNER_PORT: ${REST_INNER_PORT}
    depends_on:
      - mongodb
    ports:
      - "${REST_OUTER_PORT}:${REST_INNER_PORT}"   # port mapping
    networks:
      - data_network
      - web_network
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
      - "${DB_OUTER_PORT}:${DB_INNER_PORT}"
    command: mongod --port ${DB_OUTER_PORT}
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
      - MINIO_BROWSER_REDIRECT_URL=${MINIO_BROWSER_REDIRECT_URL}  # Set the base URL for the Minio console
    volumes:
      - minio_volume:/data   # path where minio will store the data in object storage format (outside the container, in the host machine)
    ports:
      - "${MINIO_API_OUTER_PORT}:${MINIO_API_INNER_PORT}"
      - "${MINIO_UI_INNER_PORT}:${MINIO_UI_INNER_PORT}"   # port for the minio console (only for development)
    networks:
      - minio_network
      - web_network
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
    command: server --address ":${MINIO_API_INNER_PORT}" --console-address ":${MINIO_UI_INNER_PORT}" /data    # Remove the console-address flag for production
    healthcheck:  # Health check for the minio service
      test: ["CMD", "curl", "-f", "http://localhost:${MINIO_API_INNER_PORT}/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 5

  vre_lite:
    image: vre_lite_image 
    build:
      context: ./vre_lite
      args:
        MINIO_ROOT_USER: ${MINIO_ROOT_USER}
        MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
        MINIO_API_PORT: ${MINIO_API_INNER_PORT}
        VRE_LITE_INNER_PORT: ${VRE_LITE_INNER_PORT}
        VRE_LITE_BASE_URL_DEVELOPMENT: ${VRE_LITE_BASE_URL_DEVELOPMENT}
        VRE_LITE_BASE_URL_STAGING: ${VRE_LITE_BASE_URL_STAGING}
        VRE_LITE_BASE_URL_PRODUCTION: ${VRE_LITE_BASE_URL_PRODUCTION}
        VRE_LITE_DATA_PATH: ${VRE_LITE_DATA_PATH}
        VRE_LITE_MAX_FILE_SIZE: ${VRE_LITE_MAX_FILE_SIZE}
        MINIO_PROTOCOL: ${MINIO_PROTOCOL}
        MINIO_URL: ${MINIO_URL}
        MINIO_PORT: ${APACHE_MINIO_OUTER_PORT}
        NODE_NAME: ${NODE}
    volumes:
      - vre_lite_volume:/data
    ports:
      - "${VRE_LITE_OUTER_PORT}:${VRE_LITE_INNER_PORT}"
    networks:
      - minio_network
      - web_network
    depends_on:
      - minio
    deploy:
      replicas: ${VRE_LITE_REPLICAS}   # Specify the number of replicas for Docker Swarm
      resources:
        limits:
          cpus: ${VRE_LITE_CPU_LIMIT}   # Specify the limit number of CPUs
          memory: ${VRE_LITE_MEMORY_LIMIT}   # Specify the limit memory
        reservations:
          cpus: ${VRE_LITE_CPU_RESERVATION}   # Specify the reserved number of CPUs
          memory: ${VRE_LITE_MEMORY_RESERVATION}   # Specify the reserved memory
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
  vre_lite_volume:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${VRE_LITE_VOLUME_PATH}   # bind the volume to VRE_LITE_VOLUME_PATH on the host

networks:
  data_network: 
    external: true   # Use an external network
  minio_network: 
    name: minio_network 
    driver: overlay   # Use an overlay network
  web_network:
    name: web_network
    driver: overlay   # Use an overlay network
```