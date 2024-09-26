
# MDposit - MDDB Docker services

In this repository there are all the files needed for executing the different **MDposit - MDDB services**: **front-end**, **back-end**, **workflow**, **database** and **data loader**. All these services have been integrated into **docker containers** and connected between them via docker **network**. 

<div align="center" style="display:flex;align-items:center;justify-content:space-around;padding:20px 0;">
<a href="https://mdposit.mddbr.eu/"><img src="readme/logo-mdposit.png" alt="mdposit" width="200"/></a><a href="https://mddbr.eu"><img src="readme/logo-MDDB.png" alt="MDDB" width="300"/></a>
</div>

Schema of **MDposit - MDDB Docker** web services. Each box in the schema is a **service** encapsulated into a **docker container**. The **services** cover the entire process from the **raw data** to the **website analyses**. See the following figure:

<div align="center" style="display:flex;align-items:center;justify-content:space-around;">
<img src="readme/schema.png" alt="mdposit" />
</div>

## Services description

### VRE

The **VRE** is a **Nuxt** application.

For this project, the following repo has been used:

https://mmb.irbbarcelona.org/gitlab/gbayarri/mddb-vre

### REST API

The **REST API** is a **NodeJS + Express** application.

For this project, the following repo has been used:

https://mmb.irbbarcelona.org/gitlab/aluciani/MoDEL-CNS_REST_API

### Website client

The **website client** is a **React App**.

For this project, the following repo has been used:

https://mmb.irbbarcelona.org/gitlab/gbayarri/mdposit-client-build

### Data loader

The **data loader** is a  **node JS script** made for load, list and remove data from a mongodb database.

For this project, the following repo has been used:

https://mmb.irbbarcelona.org/gitlab/aluciani/MoDEL-CNS_DB_loader

### Workflow

The aim for this tool is to **process raw MD data** and obtain standard **structure** and **trajectory** files.

For this project, the following repo has been used:

https://mmb.irbbarcelona.org/gitlab/d.beltran.anadon/MoDEL-workflow

### Database

The database used is **mongodb** inside a docker container:

https://github.com/docker-library/mongo

For this project, the chosen version of **mongo** is **6**.

### Object Storage

In order to provide the users a way to **transfer big files** that can't be uploaded via web, a docker **MinIO** server is integrated into the infrastructure.

https://hub.docker.com/r/minio/minio

## Installation

Please execute the following steps for installing the **MDposit - MDDB Docker services**:

### Set Up Virtual Machine

Let's take a **clear** and **empty Virtual Machine** as a starting point for installing the **MDposit - MDDB Docker services**. It's highly recommended to have installed in it **Ubuntu 18.04 or superior**, though the services should work in other **Linux** distributions.

[**Click here for seeing the detailed instructions for setting up a Virtual Machine**](readme/setup.md)

### Set Up Configuration Files

First off, all the **environment files** must be created and updated as well as the **docker-compose.yml** and **mongo-init.js** files. 

[**Click here for seeing the detailed instructions for setting up the Configuration Files**](readme/config.md)

### Execute Docker Swarm

Once the Virtual Machine has all the **dependencies installed** and all the **config** files are **set up**, it's the moment of executing the **Docker Swarm** service. **Docker Swarm** is a **container orchestration** tool for **clustering** and **scheduling** Docker containers. 

[**Click here for seeing the detailed instructions for executing Docker Swarm**](readme/docker-swarm.md)

 or [Click here](readme/docker-compose.md) for the detailed instructions for executing Docker Compose.

### Tips

A list of **useful tips** for **developing** and **debugging** has been defined for the sake of easing all the process.

[**Click here for seeing the Tips**](readme/tips.md)

## Credits

Daniel Beltran, Genís Bayarri, Adam Hospital.

## Copyright & licensing

This website has been developed by the [MMB group](https://mmb.irbbarcelona.org) at the [IRB Barcelona](https://irbbarcelona.org).

© 2024 **Institute for Research in Biomedicine**

Licensed under the **Apache License 2.0**.