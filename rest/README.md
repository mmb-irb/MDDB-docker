# REST API

The **REST API** is a **NodeJS + Express** application.

For this project, the following repo has been used:

https://github.com/mmb-irb/MDDB-REST-API/

## Trajectory format converter

The REST API converts trajectories from its internal `.bin` format to other formats (XTC, TRR, NetCDF, DCD) with a small C++ executable that relies on a [customized chemfiles fork](https://github.com/d-beltran/chemfiles).

This executable is **precompiled** and stored in this folder (`chemfiles_bin_converter`), so the Dockerfiles just copy it into the REST API `build` folder. No chemfiles, cmake or compiler is needed to build the image.

The executable is fully statically linked, so it does not depend on any library in the image. It only runs on `linux/amd64`.

It must be rebuilt whenever the chemfiles fork or the converter source (`assembly/chemfiles_bin_converter.cpp` in the REST API) changes:

```bash
./build-chemfiles-converter.sh <chemfiles fork directory> <REST API directory>
```

The script builds it inside the same base image used by the Dockerfiles and prints the commits it was built from.

> [!WARNING]
> The executable must be compatible with the REST API version being deployed. Update it before (or together with) a REST API release which changes the converter arguments.

## Dockerfile

This Dockerfile is used taking as a starting point the **repository** of the REST API.

```Dockerfile
# Stage 1: Build the NodeJS REST API
FROM docker.io/library/nginx:alpine AS build

# Install necessary packages
RUN apk --no-cache add nodejs npm git curl
RUN apk add build-base
RUN apk add cmake

# Define working dir
WORKDIR /app

# Clone and install the chemfiles fork customized to support '.bin' format reading and streaming.
RUN git clone https://github.com/d-beltran/chemfiles --depth 1 && cd chemfiles && git fetch --unshallow  && mkdir build && cd build && cmake .. && make && make install

# Verify installation
RUN node --version && npm --version && git --version

# Version argument
ARG VERSION

# If version is set, wget the specific version of the rest API
# Otherwise, use the latest version
RUN if [ -z "$VERSION" ]; then \
        echo "No VERSION provided, fetching latest tag..." && \
        LATEST_TAG=$(curl -s "https://api.github.com/repos/mmb-irb/MDDB-REST-API/tags" \
            | grep -m 1 '"name":' \
            | sed -E 's/.*"name": "v?([^"]+)".*/\1/') && \
        if [ -z "$LATEST_TAG" ]; then \
            echo "Failed to fetch latest tag, using master branch" && \
            git clone --branch master --depth 1 https://github.com/mmb-irb/MDDB-REST-API.git && \
            echo "master" > version.txt; \
        else \
            echo "Using latest tag: $LATEST_TAG" && \
            echo "$LATEST_TAG" > version.txt && \
            git clone --branch "v$LATEST_TAG" --depth 1 https://github.com/mmb-irb/MDDB-REST-API.git; \
        fi; \
    else \
        git clone --branch "v${VERSION}" --depth 1 https://github.com/mmb-irb/MDDB-REST-API.git; \
        echo "$VERSION" > version.txt; \
    fi

# Define environment variables
ARG DB_SERVER
ARG DB_PORT
ARG DB_NAME
ARG DB_AUTHSOURCE
ARG DB_AUTH_USER
ARG DB_AUTH_PASSWORD
ARG REST_INNER_PORT

# Create .env file with environment variables
RUN echo "DB_SERVER=${DB_SERVER}" > /app/MDDB-REST-API/.env && \
    echo "DB_PORT=${DB_PORT}" >> /app/MDDB-REST-API/.env && \
    echo "DB_NAME=${DB_NAME}" >> /app/MDDB-REST-API/.env && \
    echo "DB_AUTHSOURCE=${DB_AUTHSOURCE}" >> /app/MDDB-REST-API/.env && \
    echo "DB_AUTH_USER=${DB_AUTH_USER}" >> /app/MDDB-REST-API/.env && \
    echo "DB_AUTH_PASSWORD=${DB_AUTH_PASSWORD}" >> /app/MDDB-REST-API/.env && \
    echo "LISTEN_PORT=${REST_INNER_PORT}" >> /app/MDDB-REST-API/.env

# Change working directory to /app/MDDB-REST-API
WORKDIR /app/MDDB-REST-API

# Install packages
RUN npm ci

# Build website
RUN npm run build

# Stage 2: Serve the REST API app with pm2
FROM docker.io/library/nginx:alpine

# Install necessary packages
RUN apk --no-cache add nodejs npm curl

# Install pm2
RUN npm install pm2 -g

# Set working directory
WORKDIR /app

# Copy from the previous stage
COPY --from=build /app/MDDB-REST-API /app/MDDB-REST-API
COPY --from=build /app/chemfiles /app/chemfiles
COPY --from=build /app/version.txt /app/version.txt

# Change working directory to /app/MDDB-REST-API
WORKDIR /app/MDDB-REST-API

# Define environment variable
ARG REST_INNER_PORT

# Expose the port where the app runs on
EXPOSE ${REST_INNER_PORT}

# Serve the app
CMD ["pm2-runtime", "start", "index.js", "-i", "4", "-n", "MDposit_API", "--node-args=", "\"--experimental-worker\""]
```