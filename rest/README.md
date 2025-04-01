# REST API

The **REST API** is a **NodeJS + Express** application.

For this project, the following repo has been used:

https://github.com/mmb-irb/MoDEL-CNS-REST-API/

## Dockerfile

This Dockerfile is used taking as a starting point the **repository** of the REST API.

```Dockerfile
# Stage 1: Build the NodeJS REST API
FROM docker.io/library/nginx:alpine AS build

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

# Clone MoDEL-CNS_REST_API repo
RUN git clone https://github.com/mmb-irb/MoDEL-CNS-REST-API.git

# Define environment variables
ARG DB_SERVER
ARG DB_PORT
ARG DB_NAME
ARG DB_AUTHSOURCE
ARG DB_AUTH_USER
ARG DB_AUTH_PASSWORD
ARG REST_INNER_PORT

# Create .env file with environment variables
RUN echo "DB_SERVER=${DB_SERVER}" > /app/MoDEL-CNS_REST_API/.env && \
    echo "DB_PORT=${DB_PORT}" >> /app/MoDEL-CNS_REST_API/.env && \
    echo "DB_NAME=${DB_NAME}" >> /app/MoDEL-CNS_REST_API/.env && \
    echo "DB_AUTHSOURCE=${DB_AUTHSOURCE}" >> /app/MoDEL-CNS_REST_API/.env && \
    echo "DB_AUTH_USER=${DB_AUTH_USER}" >> /app/MoDEL-CNS_REST_API/.env && \
    echo "DB_AUTH_PASSWORD=${DB_AUTH_PASSWORD}" >> /app/MoDEL-CNS_REST_API/.env && \
    echo "LISTEN_PORT=${REST_INNER_PORT}" >> /app/MoDEL-CNS_REST_API/.env

# Change working directory to /app/MoDEL-CNS_REST_API
WORKDIR /app/MoDEL-CNS_REST_API

# Install packages
RUN npm install

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
COPY --from=build /app/MoDEL-CNS_REST_API /app/MoDEL-CNS_REST_API
COPY --from=build /app/chemfiles /app/chemfiles

# Change working directory to /app/MoDEL-CNS_REST_API
WORKDIR /app/MoDEL-CNS_REST_API

# Define environment variable
ARG REST_INNER_PORT

# Expose the port where the app runs on
EXPOSE ${REST_INNER_PORT}

# Serve the app
CMD ["pm2-runtime", "start", "index.js", "-i", "4", "-n", "MDposit_API", "--node-args=", "\"--experimental-worker\""]
```