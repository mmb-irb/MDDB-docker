# Loader

The **data loader** is a  **node JS script** made for load, list and remove data from a mongodb database.

For this project, the following repo has been used:

https://mmb.irbbarcelona.org/gitlab/aluciani/MoDEL-CNS_DB_loader

## Config files

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
DB_SERVER=my_mongo_container
DB_PORT=27017
DB_NAME=mddb_db
DB_AUTH_USER=user_rw
DB_AUTH_PASSWORD=pwd_rw
DB_AUTHSOURCE=mddb_db
```

The **DB_SERVER** must be the same name as the **mongodb container_name** in the [**docker-compose.yml**](../docker-compose.yml) file.

The **DB_NAME** must be the same used in the [**mongo-init.js**](../mongo-init.js) file.

The credentials **DB_AUTH_USER** and **DB_AUTH_PASSWORD** must be the same defined in the [**mongo-init.js**](../mongo-init.js) file with the **readWrite role**.

## Dockerfile

This Dockerfile is used taking as a starting point the **repository** of the loader.

```Dockerfile
# Base docker with miniconda
FROM continuumio/miniconda3

# Define working dir
WORKDIR /app

# Define a directory for the volume
VOLUME /data

# Install Node.js
RUN apt-get update && \
    apt-get install -y curl && \
    curl -sL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# Clone loader repo
RUN git clone https://mmb.irbbarcelona.org/gitlab/aluciani/MoDEL-CNS_DB_loader.git

# Copy the .env file into the Docker image
COPY .env /app/MoDEL-CNS_DB_loader

# Copy the environment.yml file into the Docker image
COPY environment.yml /app

# Create new environment
RUN conda env create -f /app/environment.yml

# Change working directory to /app/MoDEL-CNS_DB_loader
WORKDIR /app/MoDEL-CNS_DB_loader

# Install loader
RUN npm install

# Change working directory to /app
WORKDIR /app

# Create the entrypoint script
RUN echo '#!/bin/bash' > entrypoint.sh && \
    echo 'source activate mwf_env' >> entrypoint.sh && \
    echo 'node /app/MoDEL-CNS_DB_loader/index.js "$@"' >> entrypoint.sh && \
    chmod +x entrypoint.sh

# Set the entrypoint script as the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
```