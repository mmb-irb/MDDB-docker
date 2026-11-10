# Set Up Configuration Files

* [.env file](#env-file)
* [Extensions .env file](#extensions-env-file)
* [MongoDB users](#mongodb)
* [Docker Compose](#docker-compose)
* [Extensions](#extensions)

## .env file

An `.env` file must be created in the **root** of the project by copying the template [**.env.docker.git**](../.env.docker.git):

```sh
cp .env.docker.git .env
chmod 600 .env   # it holds passwords
```

The template has sensible defaults for ports and resources, but every **empty** variable must be filled in (paths, names, users and passwords). Generate every password with, for example, `openssl rand -base64 24 | tr -d '/+='`, and use a different one for each user. **Never keep example passwords** such as `root` or `secretpassword`.

The rules that are easiest to get wrong:

* `MINIO_URL` and `REST_URL` are the **bare host name** of the node (`mdposit.example.org`), without `https://`.
* `APACHE_HTTPS_INNER_PORT` must be equal to `APACHE_HTTPS_OUTER_PORT`, and `APACHE_MINIO_INNER_PORT` equal to `APACHE_MINIO_OUTER_PORT`: Apache listens inside its container on the outer port number.
* `DB_SERVER` is `<STACK_NAME>_mongodb` when MongoDB runs in the stack (the default), or the address of an external MongoDB server. `VRE_LITE_DB_SERVER` is always `<STACK_NAME>_mongodb`.
* `DB_AUTHSOURCE` is the database where the loader and REST users are created, i.e. the same as `DB_NAME` (unless you use an external server with other users).
* `SSL_CERTIFICATE` and `SSL_CERT_KEY` are **file names** inside `APACHE_CERTS_VOLUME_PATH`, not full paths.
* `DB_BACKUP_VOLUME_PATH` must be a different folder from `DB_VOLUME_PATH` (better on another disk).
* `MINIO_BROWSER_REDIRECT_URL` is `https://<MINIO_URL>/minio`.

Before building, check that the `.env` and the compose files are valid (it prints nothing when everything is right):

```sh
docker compose -f docker-compose.yml config -q
```

The variables of the file are:

| key              | value   | description                                     |
| ---------------- | ------- | ----------------------------------------------- |
| DOCKER_DEFAULT_PLATFORM         | string  | default platform (architecture and operating system), ie linux/amd64                               |
| NODE         | string  | node identifier to deploy                                     |
| SLACK_WEBHOOK_URL         | string  | slack webhook used for sending update messages                                     |
| GH_PAT         | string  | GitHub personal access token used by VRE lite (optional)                                     |
| STACK_NAME         | string  | Docker Swarm stack name; services are named `<STACK_NAME>_<service>` (e.g. `my_stack_mongodb`)        |
| &nbsp;
| APACHE_CONFIG         | string  | apache configuration file in the apache folder (default `apache-config.conf`; `apache-config-florida.conf` for nodes behind an external TLS proxy) |
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
| SSL_CERTIFICATE         | string  | SSL certificate file name, full chain (inside APACHE_CERTS_VOLUME_PATH)                                       |
| SSL_CERT_KEY         | string  | SSL private key file name (inside APACHE_CERTS_VOLUME_PATH)                                        |
| CERT_DOMAINS         | string  | comma-separated names for the Let's Encrypt certificate (default: MINIO_URL), see [certificates](storage.md#certificates) |
| CERT_METHOD         | string  | `certbot` (default, HTTP-01, port 80) or `mod_md` (TLS-ALPN-01 in apache, only port 443) |
| CERT_EMAIL         | string  | contact email for the Let's Encrypt account, required with `CERT_METHOD=mod_md` |
| CERT_ACME_URL         | string  | ACME directory for `mod_md` (default: Let's Encrypt production) |
| &nbsp;
| LOADER_VOLUME_PATH         | string  | path where the loader will look for files                                        |
| LOADER_REPLICAS      | number  | number of replicas to deploy                                    |
| LOADER_CPU_LIMIT      | string  | loader limit number of CPUs                                    |
| LOADER_MEMORY_LIMIT          | string | loader limit memory                           |
| LOADER_CPU_RESERVATION          | string  | loader reserved number of CPUs                           |
| LOADER_MEMORY_RESERVATION      | string  | loader reserved memory                         |
| LOADER_DB_LOGIN      | string  | db user for loader                         |
| LOADER_DB_PASSWORD      | string  | db password for loader                       |
| &nbsp;
| WORKFLOW_VOLUME_PATH         | string  | path where the workflow will save the files                                        |
| WORKFLOW_REPLICAS      | number  | number of replicas to deploy                                    |
| WORKFLOW_CPU_LIMIT      | string  | workflow limit number of CPUs                                    |
| WORKFLOW_MEMORY_LIMIT          | string | workflow limit memory                           |
| WORKFLOW_CPU_RESERVATION          | string  | workflow reserved number of CPUs                           |
| WORKFLOW_MEMORY_RESERVATION      | string  | workflow reserved memory                         |
| &nbsp;
| CLIENT_REPLICAS      | number  | number of replicas to deploy                                    |
| CLIENT_OUTER_PORT         | number  | client outer port                                         |
| CLIENT_INNER_PORT         | number  | client inner port                                         |
| CLIENT_CPU_LIMIT    | string  | client limit number of CPUs                               |
| CLIENT_MEMORY_LIMIT    | string  | client limit memory                             |
| CLIENT_CPU_RESERVATION    | string  | client reserved number of CPUs                               |
| CLIENT_MEMORY_RESERVATION    | string  | client reserved memory                               |
| &nbsp;
| REST_REPLICAS      | number  | number of replicas to deploy                                    |
| REST_OUTER_PORT         | number  | REST outer port                                         |
| REST_INNER_PORT         | number  | REST inner port                                         |
| REST_CPU_LIMIT    | string  | REST limit number of CPUs                               |
| REST_MEMORY_LIMIT    | string  | REST limit memory                             |
| REST_CPU_RESERVATION    | string  | REST reserved number of CPUs                               |
| REST_MEMORY_RESERVATION    | string  | REST reserved memory                               |
| REST_DB_LOGIN    | string  | db user for website REST API                               |
| REST_DB_PASSWORD    | string  | db password for website REST API                               |
| REST_URL    | string  | host name of the node, without `https://` (e.g. mdposit.example.org)                               |
| REST_OTEL_ENDPOINT    | `<url>`  | OpenTelemetry endpoint for the REST API traces (optional, metrics extension)                               |
| &nbsp;
| DB_VOLUME_PATH         | string  | path where the DB will deploy the mongoDB file system                                        |
| DB_REPLICAS      | number  | number of replicas to deploy                                    |
| DB_OUTER_PORT         | number  | port where MongoDB listens (27017)                                         |
| DB_INNER_PORT         | number  | not used (MongoDB is not published; see `docker-compose.node.yml.example` to publish it)          |
| DB_CPU_LIMIT      | string  | DB limit number of CPUs                                    |
| DB_MEMORY_LIMIT          | string | DB limit memory                           |
| DB_CPU_RESERVATION          | string  | DB reserved number of CPUs                           |
| DB_MEMORY_RESERVATION      | string  | DB reserved memory                         |
| DB_SERVER      | string  | `<STACK_NAME>_mongodb`, or the address of an external MongoDB server                          |
| DB_NAME      | string  | name of the MDposit database (e.g. mddb_db)                          |
| DB_AUTHSOURCE      | string  | database where the loader and REST users authenticate (same as DB_NAME)                           |
| &nbsp;
| DB_BACKUP_VOLUME_PATH         | string  | path where the DB backups will be stored. **Must be a separate folder from DB_VOLUME_PATH** (not the same, not inside it, not containing it): the deploy scripts and the backup service refuse to run otherwise |
| DB_BACKUP_REPLICAS      | number  | number of replicas to deploy                                    |
| DB_BACKUP_RETENTION_COUNT         | number  | maximum number of DB backup copies to preserve                                          |
| DB_BACKUP_INTERVAL         | number  | interval in seconds between DB backups                                         |
| DB_BACKUP_COMPRESS         | string  | backup format: `no` (plain dump), `gz` (`mongodump --gzip`), `tar` or `tar.gz`. See [MongoDB backup service](docker-swarm.md#mongodb-backup-service) for the trade-offs |
| DB_BACKUP_LOCK         | string  | `yes` blocks writes (`db.fsyncLock`) while `mongodump` runs, so the backup is consistent; `no` does not. See [MongoDB backup service](docker-swarm.md#mongodb-backup-service) |
| DB_BACKUP_CPU_LIMIT      | string  | DB backup limit number of CPUs                                    |
| DB_BACKUP_MEMORY_LIMIT          | string | DB backup limit memory                           |
| DB_BACKUP_CPU_RESERVATION          | string  | DB backup reserved number of CPUs                           |
| DB_BACKUP_MEMORY_RESERVATION      | string  | DB backup reserved memory                         |
| &nbsp;
| MINIO_VOLUME_PATH1         | string  | path for the volume1 where MinIO will save / retrieve the files                              |
| MINIO_REPLICAS      | number  | number of replicas to deploy                                    |
| MINIO_API_OUTER_PORT         | number  | MinIO API outer port                                         |
| MINIO_API_INNER_PORT         | number  | MinIO API inner port                                         |
| MINIO_UI_OUTER_PORT         | number  | not used (the WebUI is published on MINIO_UI_INNER_PORT and served by Apache under /minio) |
| MINIO_UI_INNER_PORT         | number  | MinIO WebUI inner port                                         |
| MINIO_CPU_LIMIT      | string  | MinIO limit number of CPUs                                    |
| MINIO_MEMORY_LIMIT          | string | MinIO limit memory                           |
| MINIO_CPU_RESERVATION          | string  | MinIO reserved number of CPUs                           |
| MINIO_MEMORY_RESERVATION      | string  | MinIO reserved memory                         |
| MINIO_PROTOCOL      | string  | MinIO API protocol (http|https)                        |
| MINIO_URL      | string  | host name of the node, without `https://` (e.g. mdposit.example.org); also used for the certificate and Apache `ServerName` |
| MINIO_ADDRESS | string | IP of the MinIO service    |
| &nbsp;
| VRE_LITE_VOLUME_PATH         | string  | path where the VRE lite will save the logs                                        |
| VRE_LITE_REPLICAS      | number  | number of replicas to deploy                                    |
| VRE_LITE_OUTER_PORT         | number  | VRE lite outer port                                         |
| VRE_LITE_INNER_PORT         | number  | VRE lite inner port                                         |
| VRE_LITE_CPU_LIMIT      | string  | VRE lite limit number of CPUs                                    |
| VRE_LITE_MEMORY_LIMIT          | string | VRE lite limit memory                           |
| VRE_LITE_CPU_RESERVATION          | string  | VRE lite reserved number of CPUs                           |
| VRE_LITE_MEMORY_RESERVATION      | string  | VRE lite reserved memory                         |
| VRE_LITE_BASE_URL_DEVELOPMENT         | string  | VRE lite baseURL for development                                        |
| VRE_LITE_BASE_URL_STAGING      | string  | VRE lite baseURL for staging                                    |
| VRE_LITE_BASE_URL_PRODUCTION          | string | VRE lite baseURL for production                            |
| VRE_LITE_LOG_PATH          | string  | path where the logs will be saved (relative to the docker)                           |
| VRE_LITE_MAX_FILE_SIZE      | number  | maximum size for all the trajectory files in bytes                      |
| VRE_LITE_TIME_DIFF      | number  | number of days to be subtracted from now to run the cleaning jobs for the VRE lite          |
| VRE_LITE_DB_SERVER      | string  | always `<STACK_NAME>_mongodb`          |
| VRE_LITE_DB_OUTER_PORT      | number  | DB outer port for the VRE lite          |
| VRE_LITE_MONGO_DATABASE      | string  | name of the VRE lite database (e.g. vre_db)          |
| VRE_LITE_DB_LOGIN      | string  | db user for VRE lite data           |
| VRE_LITE_DB_PASSWORD      | string  | db password for VRE lite data           |
| &nbsp;
| UTILS_REPLICAS      | number  | number of replicas to deploy           |
| UTILS_CPU_LIMIT      | string  | utils limit number of CPUs           |
| UTILS_MEMORY_LIMIT      | string  | utils limit memory           |
| UTILS_CPU_RESERVATION      | string  | utils reserved number of CPUs           |
| UTILS_MEMORY_RESERVATION      | string  | utils reserved memory           |
| &nbsp;
| MONGO_INITDB_ROOT_USERNAME      | string  | root user for the DB                         |
| MONGO_INITDB_ROOT_PASSWORD      | string  | root password for the DB                       |
| MONGO_CONTAINER_USER      | string  | user ID that runs mongod (default `0`; `999` is the image's `mongodb` user). It must be able to write in DB_VOLUME_PATH |
| MONGO_CONTAINER_GROUP      | string  | group ID that runs mongod (default `0`)                        |
| &nbsp;
| MINIO_ROOT_USER      | string  | MinIO root user                         |
| MINIO_ROOT_PASSWORD      | string  | MinIO root password                      |
| MINIO_USER      | string  | MinIO user with permissions for creating access keys                        |
| MINIO_PASSWORD      | string  | MinIO password with permissions for creating access keys                     |
| MINIO_BROWSER_REDIRECT_URL      | `<url>`  | MinIO base URL (full URI, ie http(s)://your-domain.com/minio)                      |

**Important:** the formats of **cpus** and **memory** must be in string format between single quotes, while **replicas** must be in integer format. Example:

```
VRE_LITE_VOLUME_PATH=/path/to/vre/data  # path to volume
VRE_LITE_REPLICAS=2  # number of replicas to deploy
VRE_LITE_CPU_LIMIT='4.00'  # cpus in float format
VRE_LITE_MEMORY_LIMIT='2G'  # memory indicating unit (G, M)
```

Keep the template values of **VRE_LITE_BASE_URL_DEVELOPMENT** and **VRE_LITE_BASE_URL_STAGING**: only the production one is used when running as a Docker service.

Most values are **build arguments**: they are written into the images when they are built. After changing the `.env`, rebuild the affected services (see [Update services](update.md)), redeploying is not enough.

## Extensions .env file

In case some **extension** is added to the **core** services, the **environment variables** of each extension must be added to the main `.env` file created in the **root** of the project. The files [**.env.docker.extensions.git**](../.env.docker.extensions.git) (mcp) and [**.env.metrics.git**](../.env.metrics.git) (metrics and grafana) can be taken as templates.

## MongoDB

### mongo-init.js file

[**mongo-init.js**](../mongodb/mongo-init.js) runs **only the first time MongoDB starts with an empty `DB_VOLUME_PATH`**. It creates three users, taking their names and passwords from the `.env` file (there is nothing to edit in the script):

| User | Database | Role | Used by |
| --- | --- | --- | --- |
| `LOADER_DB_LOGIN` / `LOADER_DB_PASSWORD` | `DB_NAME` | readWrite | loader |
| `REST_DB_LOGIN` / `REST_DB_PASSWORD` | `DB_NAME` | read | REST API |
| `VRE_LITE_DB_LOGIN` / `VRE_LITE_DB_PASSWORD` | `VRE_LITE_MONGO_DATABASE` | readWrite | VRE lite, utils |

Changing these values in `.env` later **does not change the users** of an existing database: change them in MongoDB too (`mongosh` → `db.changeUserPassword(...)`), or run the script again by hand (see [Deploy Docker Swarm](docker-swarm.md#run-mongo-initjs-by-hand)).

## Docker Compose

The [**docker-compose.yml**](../docker-compose.yml) file defines the **images**, **ports**, **volumes**, **networks** and **resources** of every service. All the configurable values (resources, paths, ports, credentials...) come from the [**.env file**](#env-file), so **do not edit `docker-compose.yml`** for a single node.

If a node needs something different from the common configuration (an extra published port, an extra mount, more replicas than the `.env` allows, an older MongoDB image until it is upgraded...), copy [**docker-compose.node.yml.example**](../docker-compose.node.yml.example) to `docker-compose.node.yml` (ignored by git) and put it there. The deploy scripts add it after `docker-compose.yml` and the extensions. See [Redeploying a running stack](docker-swarm.md#redeploying-a-running-stack).

## Extensions

The [**extensions**](../extensions) files specify **complementary** services, which may be **deployed** with the main [**docker-compose.yml**](#docker-compose) file or **omitted**, depending on the node’s requirements.

All the configurable variables such as **resources**, **paths**, **ports** and so on must be defined in the [**extensions .env file**](#extensions-env-file).

List of available **extensions**:

* [**mcp**](../extensions/mcp.yml)
* [**metrics**](../extensions/metrics.yml)
* [**grafana**](../extensions/grafana.yml)
