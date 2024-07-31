# REST API

The **REST API** is a **NodeJS + Express** application.

For this project, the following repo has been used:

https://mmb.irbbarcelona.org/gitlab/aluciani/MoDEL-CNS_REST_API

## Config files

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
DB_SERVER=my_mongo_container
DB_PORT=27017
DB_NAME=mddb_db
DB_AUTH_USER=user_r
DB_AUTH_PASSWORD=pwd_r
DB_AUTHSOURCE=mddb_db
LISTEN_PORT=3000
```

The **DB_SERVER** must be the same name as the **mongodb container_name** in the [**docker-compose.yml**](../docker-compose-git.yml) file.

The **DB_NAME** must be the same used in the [**mongo-init.js**](../mongo-init.js) file.

The credentials **DB_AUTH_USER** and **DB_AUTH_PASSWORD** must be the same defined in the [**mongo-init.js**](../mongo-init.js) file with the **read** role.

The **LISTEN_PORT** must be the same exposed in the [**REST Dockerfile**](Dockerfile).

## Dockerfile

This Dockerfile is used taking as a starting point the **repository** of the REST API.

```Dockerfile
# Use Alpine Linux as base image
FROM alpine:latest

# Install necessary packages
RUN apk --no-cache add nodejs npm git
RUN apk add build-base
RUN apk add cmake

# Define working dir
WORKDIR /app

# Clone and install the chemfiles fork customized to support '.bin' format reading and streaming.
RUN git clone https://github.com/d-beltran/chemfiles --depth 1 && cd chemfiles && git fetch --unshallow  && mkdir build && cd build && cmake .. && make && make install

# Verify installation
RUN node --version && npm --version && git --version

# Define a directory for the volume
VOLUME /data

# Clone MoDEL-CNS_REST_API repo
RUN git clone https://mmb.irbbarcelona.org/gitlab/aluciani/MoDEL-CNS_REST_API

# Copy the .env file into the Docker image
COPY .env /app/MoDEL-CNS_REST_API

# Change working directory to /app/MoDEL-CNS_REST_API
WORKDIR /app/MoDEL-CNS_REST_API

# Install packages
RUN npm install

# Build website
RUN npm run build

# Install pm2
RUN npm install pm2 -g

# Expose the port the app runs on
EXPOSE 3000

# Serve the app
CMD ["pm2-runtime", "start", "index.js", "-i", "4", "-n", "MDposit_API", "--node-args=", "\"--experimental-worker\""]
```