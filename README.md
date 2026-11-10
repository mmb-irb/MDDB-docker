
# MDposit - MDDB container services

In this repository there are all the files needed for executing the different **MDposit - MDDB services**: **apache**, **front-end**, **back-end**, **workflow**, **database**, **data loader**, **Object storage** and **VRE lite**. All these services have been integrated into **containers** and connected between them via docker/podman **network**. 

<div align="center" style="display:flex;align-items:center;justify-content:space-around;padding:20px 0;">
<a href="https://mdposit.mddbr.eu/"><img src="readme/logo-mdposit.png" alt="mdposit" width="200"/></a><a href="https://mddbr.eu"><img src="readme/logo-MDDB.png" alt="MDDB" width="300"/></a>
</div>

Schema of **MDposit - MDDB container** web services. Each box in the schema is a **service** encapsulated into a **docker/podman container**. The **services** cover the entire process from the **raw data** to the **website analyses**. See the following figure:

<div align="center" style="display:flex;align-items:center;justify-content:space-around;">
<img src="readme/schema.png" alt="mdposit" />
</div>

## Services description

### Apache

The Apache HTTP Server, colloquially called Apache, is a **Web server** application notable for playing a key role in the initial growth of the World Wide Web:

https://hub.docker.com/_/httpd

### REST API

The **REST API** is a **NodeJS + Express** application.

For this project, the following repo has been used:

https://github.com/mmb-irb/MDDB-REST-API/

### Website client

The **website client** is a **React App**, built from its source code when the client image is built. Each node can have its own configuration in `client/host-config.js` (see the [client README](client/README.md)).

For this project, the following repo has been used:

https://github.com/mmb-irb/MDposit-client/

### Data loader

The **data loader** is a **Node.js** tool to load, list and remove data from the MongoDB database (its image also has GROMACS, from a conda environment).

For this project, the following repo has been used:

https://github.com/mmb-irb/MDDB-loader/

### Workflow

The aim for this tool is to **process raw MD data** and obtain standard **structure** and **trajectory** files.

For this project, the following repo has been used:

https://github.com/mmb-irb/MDDB-workflow/

### VRE lite

The **VRE lite** is a **Nuxt** application.

For this project, the following repo has been used:

https://github.com/mmb-irb/mddb-vre/

### Database

The database used is **mongodb** inside a docker container:

https://github.com/docker-library/mongo

For this project, the chosen version of **mongo** is **8.0** (the long-term support release). To upgrade an existing node from an older version, see [mongo-upgrade.md](readme/mongo-upgrade.md).

### Database backup

A specific service performs a complete database backup every `DB_BACKUP_INTERVAL` seconds. To disable it, set **DB_BACKUP_REPLICAS** to 0. See [MongoDB backup service](readme/docker-swarm.md#mongodb-backup-service).

### Utils

One-off utility scripts (e.g. updating the service versions shown in VRE lite). See the [utils README](utils/README.md).

### Object Storage

In order to provide the users a way to **transfer big files** that can't be uploaded via web, a docker **MinIO** server is integrated into the infrastructure.

https://hub.docker.com/r/pgsty/silo (a maintained fork of MinIO)

### Extensions

**Optional** services that may be **deployed** or **omitted**, depending on the node’s requirements: `mcp` (MCP server for the REST API), `metrics` (Prometheus exporters) and `grafana`. See [extensions](readme/config.md#extensions).

## Install a new node with Docker Swarm (recommended)

<div align="center" style="display:flex;align-items:center;justify-content:space-around;">
<img src="readme/docker.png" alt="mdposit" />
</div>

This is the complete path from an empty VM to a running node. Each step links to the detailed documentation. The commands use `my_stack` as the stack name: use the `STACK_NAME` of your `.env`.

### 0. Before starting

Have ready:

* A **VM** that meets the [requirements](readme/setup.md#requirements): Linux, a CPU with **AVX**, enough disk, outbound internet access and the clock synchronised (NTP).
* The **domain name** of the node (e.g. `mdposit.example.org`) pointing to the VM in the **DNS**.
* The **ports** 443, 80 and the MinIO API port (e.g. 9000) **open** from the internet to the VM ([firewall and ports](readme/setup.md#firewall-and-ports)).
* A **TLS certificate** (full chain) and its private key for that domain, or the plan to get a free one from Let's Encrypt ([certificates](readme/storage.md#certificates)).
* The **storage** for the database and the uploads ([storage](readme/storage.md)).

### 1. Install Docker

Install Docker Engine and the Docker Compose plugin, and add your user to the `docker` group: [Set Up Virtual Machine](readme/setup.md#installation-of-docker-and-docker-compose). Then check:

```sh
docker compose version
docker run --rm hello-world
```

### 2. Clone the repository

```sh
git clone https://github.com/mmb-irb/MDDB-docker.git
cd MDDB-docker
```

All the commands below are run from this folder.

### 3. Create the storage folders and copy the certificate

```sh
mkdir -p /path/to/volume/{certs,data,db,db_backup,logs,minio/disk1}
cp fullchain.pem privkey.pem /path/to/volume/certs/
chmod 600 /path/to/volume/certs/privkey.pem
```

Details, and what each folder is for: [Set Up Storage](readme/storage.md).

### 4. Configure the `.env` file

```sh
cp .env.docker.git .env
chmod 600 .env
```

Fill in every empty variable: node name, stack name, domain, paths of step 3, certificate file names, and a **different, generated password** for every user. Read the rules in [Set Up Configuration Files](readme/config.md#env-file) before, and validate the result:

```sh
docker compose -f docker-compose.yml config -q
```

### 5. Configure the website client (optional)

To give the website its own name, logos, colors and contacts, create `client/host-config.js` (and put its images in `client/images/`). Without it the client uses a generic MDposit look. See the [client README](client/README.md#host-configuration-file).

### 6. Start Docker Swarm and create the networks

```sh
docker swarm init --advertise-addr <private IP of the VM>
for n in web_network data_network minio_network metrics_network; do
  docker network create --driver overlay --attachable "$n"
done
```

### 7. Build the images and deploy the stack

The build clones and compiles every service, it takes a while:

```sh
docker compose -f docker-compose.yml build
python3 scripts/stack-deploy.py -t my_stack
```

With extensions, add the same `-f` / `-c extensions/<extension>.yml` files to both commands. Details: [Deploy Docker Swarm](readme/docker-swarm.md).

### 8. Check the node

```sh
docker stack services my_stack     # every service at its number of replicas (loader, workflow and utils at 0/0)
docker compose run --rm loader list   # the loader reaches the database
python3 scripts/update-services-versions.py   # store the versions shown in VRE lite
```

Then open `https://<your domain>/`, `https://<your domain>/api/rest/` and `https://<your domain>/vre_lite/` in a browser. If the REST API answers `500` right after the first deploy, restart it once MongoDB is up: `docker service update --force my_stack_rest`. More checks: [Execute services](readme/docker-swarm.md#execute-services).

### 9. After the installation

* **Load data:** run the [workflow](readme/docker-swarm.md#use-workflow) and the [loader](readme/docker-swarm.md#use-loader).
* **Backups:** check the [MongoDB backup service](readme/docker-swarm.md#mongodb-backup-service) and keep the backups on another disk.
* **Certificate renewal:** with Let's Encrypt, add [renew-certs.py](readme/storage.md#lets-encrypt-automatic-renewal) to the cron.
* **Settings of this node only** (extra ports, mounts...): put them in `docker-compose.node.yml`, never in `docker-compose.yml` ([why](readme/docker-swarm.md#redeploying-a-running-stack)).
* **Updates:** [Update services](readme/update.md).
* **Problems:** [Tips](readme/tips.md) and [troubleshooting of new nodes](.claude/skills/deploy-node/troubleshooting.md).

### Assisted deploy script

Two scripts can do most of these steps for you:

* [scripts/docker-install.py](scripts/docker-install.py) does **step 1**: it installs Docker Engine and the Compose plugin on Ubuntu, Debian, Rocky / AlmaLinux / RHEL, CentOS and Fedora, following Docker's official instructions, and adds your user to the `docker` group (needs sudo). With `--root-dir /path/to/volume` it also moves the Docker images to that disk. On any other system, or if something fails, it stops and points to [Docker's installation guide](https://docs.docker.com/engine/install/).
* [scripts/docker-deploy.py](scripts/docker-deploy.py) does **steps 3 to 8**: it creates the storage folders, copies the certificate, asks for the main values and creates the `.env` (with random passwords unless you type them), and then creates the swarm and the networks, builds, deploys and stores the service versions. Review the `.env` it creates against [the configuration](readme/config.md#env-file). If a `.env` already exists, it uses it as it is.

```sh
python3 scripts/docker-install.py      # then log out and back in, for the docker group
python3 scripts/docker-deploy.py
```

With `-r`, `docker-deploy.py` first **removes the stack, leaves the swarm and deletes all the Docker cache** (it asks to type the stack name to confirm): never use it on a node with services you want to keep.

### Using Claude Code

The repository has a [Claude Code](https://claude.com/claude-code) skill, [deploy-node](.claude/skills/deploy-node/SKILL.md), that follows these steps on a VM with pre-flight checks ([preflight.sh](.claude/skills/deploy-node/preflight.sh): AVX, MinIO multipart uploads, outbound access, ports...) and a verification script ([verify.sh](.claude/skills/deploy-node/verify.sh)). Both scripts can also be run by hand.

### Documentation

* [Set Up Virtual Machine](readme/setup.md)
* [Set Up Storage](readme/storage.md)
* [Set Up Configuration Files](readme/config.md)
* [Deploy Docker Swarm](readme/docker-swarm.md)
* [Update services](readme/update.md)
* [Upgrade MongoDB](readme/mongo-upgrade.md)
* [Tips](readme/tips.md)

## Installation via Podman

<div align="center" style="display:flex;align-items:center;justify-content:space-around;">
<img src="readme/podman.png" alt="mdposit" />
</div>

### Clone repository

First off, please **clone this repository** into the VM where the services will be deployed:

```sh
git clone https://github.com/mmb-irb/MDDB-docker.git
```

Then, enter the new folder:

```sh
cd MDDB-docker
```

Once the repository has been cloned, there are two ways to deploy it: [**via script**](#via-script) and [**manually, step by step**](#manually-step-by-step).

### Via script

A **deploy script** is provided for executing the **different steps** of the deploying process in an almost **automatic** way. Please execute the script, located in [**scripts/podman-deploy.py**](./scripts/podman-deploy.py). This script [**deploys all the services**](#deploy-podman-stack) with Podman.

How to execute the help script from the root of this repository:

```sh
python3 scripts/podman-deploy.py -h
```

#### Deploy Podman stack

Execute script for deploying Podman Stack:

```sh
python3 scripts/podman-deploy.py
```

Or, for a new clean installation (**remove all the containers** and **Podman cache** before deploying the stack):

```sh
python3 scripts/podman-deploy.py -r
```

Besides, a `.env` file will be created taking [**.env.podman.git**](./.env.podman.git) as a template. For more information about all the **environment** variables that are set in this file, please visit the [**configuration section**](./readme/config.md#env-file). Take into account that only the main environment variables will be created interactively. In some cases this `.env` file must be modified manually.

When executing the **deploy script**, the user will be prompted to answer some questions for filling some of the **variables** in the `.env` file:

⚠️ Review the defaults below: never keep example passwords such as `root` or `secretpassword` in a real node.

* **Main path for the storage system:** At the beginning of the execution of the script, you will be asked for the **main path of the storage system**. Inside this path the following **folder structure** will be generated:

  * [**certs/**](readme/storage.md#certificates) (apache **SSL/TLS** certificates)
  * [**data/**](readme/storage.md#workflow) (**workflow** output data and **loader** input data)
  * [**db/**](readme/storage.md#mongodb) (**MongoDB** data)
  * [**logs/**](readme/storage.md#logs) (**VRE lite** logs)
  * [**minio/**](readme/storage.md#minio) (**MinIO** data)
    * disk1/ (**MinIO** data)

* **SSL/TLS certificates:** If the **SSL/TLS** certificates are available, they can be copied into the **certs/** folder during the execution of the **script**. Be sure to have them located in the **same VM** where the script is being executed.
* **Node:** Node identifier, mandatory. 
* **Database name:** MongoDB database name. Default value: **mddb_db**.
* **Root database user:** MongoDB root database user. Default value: **root**.
* **Root database password:** MongoDB root database password. Default value: **root**.
* **R/W database user:** Read / Write database user for the loader service. Default value: **user_rw**.
* **R/W database password:** Read / Write database password for the loader service. Default value: **pwd_rw**.
* **R database user:** Read database user for the REST API service. Default value: **user_r**.
* **R database password:** Read database password for the REST API service. Default value: **pwd_r**.
* **MinIO root user:** MinIO root user. Default value: **admin**.
* **MinIO root password:** MinIO root password. Default value: **secretpassword**.
* **API MinIO port:** Port for the MinIO API. Default value: **9000**.

Once the deploy has finished, the services should be up and running and the one-off tasks ready to execute. For checking and/or executing all the services, [**please click here**](readme/podman.md#execute-services).

⚠️ **Although all the steps of the installation and deployment are automatic, it's highly recommended to read all the documentation before running this script** ⚠️ 

The different sections of the documentation are:

* [**Set Up Storage**](readme/storage.md)
* [**Set Up Configuration Files**](readme/config.md)
* [**Deploy Podman**](readme/podman.md)

### Manually step by step

Please execute the following steps for installing the **MDposit - MDDB container services** manually:

#### Set Up Storage

The **Object Storage** and **Mongo** services will need a **disk path** to save all the **data** generated. The **Workflow** and the **Loader** services will need **another disk path** as well for **saving** (in the case of the workflow) and **retrieving** (in the case of the loader) the data that will be **uploaded** to the **website** in the last instance.

[**Click here for seeing the detailed instructions for setting up the Storage**](readme/storage.md)

#### Set Up Configuration Files

First off, all the **environment files** must be created and updated as well as the **docker-compose.yml** and **mongo-init.js** files. 

[**Click here for seeing the detailed instructions for setting up the Configuration Files**](readme/config.md)

#### Deploy Podman

Once the Virtual Machine has all the **dependencies installed** and all the **config** files are **set up**, it's the moment of **building** and **running** the **Podman containers**.

[**Click here for seeing the detailed instructions for building and running Podman**](readme/podman.md)

### Tips

A list of **useful tips** for **developing** and **debugging** has been defined for the sake of easing all the process.

[**Click here for seeing the Tips**](readme/tips-podman.md)

## Credits

Daniel Beltran, Genís Bayarri, Adam Hospital, Rubén Chaves.

## Copyright & licensing

This website has been developed by the [MMB group](https://mmb.irbbarcelona.org) at the [IRB Barcelona](https://irbbarcelona.org).

© 2024 **Institute for Research in Biomedicine**

Licensed under the **Apache License 2.0**.