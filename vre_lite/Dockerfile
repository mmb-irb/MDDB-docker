# Stage 1: Build the Nuxt app
FROM node:24.22.1 AS build

# Set working directory
WORKDIR /app

# Version argument
ARG VERSION

# If version is set, wget the specific version of the vre_lite
# Otherwise, use the latest version
RUN if [ -z "$VERSION" ]; then \
        echo "No VERSION provided, fetching latest release..." && \
        LATEST_TAG=$(curl -s "https://api.github.com/repos/mmb-irb/mddb-vre/releases/latest" \
            | grep -m 1 '"tag_name":' \
            | sed -E 's/.*"tag_name": "v?([^"]+)".*/\1/') && \
        if [ -z "$LATEST_TAG" ]; then \
            echo "No releases found, fetching latest tag..." && \
            LATEST_TAG=$(curl -s "https://api.github.com/repos/mmb-irb/mddb-vre/tags?per_page=100" \
                | grep '"name":' \
                | sed -E 's/.*"name": "v?([^"]+)".*/\1/' \
                | grep -E '^[0-9]+(\.[0-9]+)*$' \
                | sort -V | tail -n 1); \
        fi && \
        if [ -z "$LATEST_TAG" ]; then \
            echo "Failed to fetch latest tag, using main branch" && \
            git clone --branch main --depth 1 https://github.com/mmb-irb/mddb-vre.git && \
            echo "main" > version.txt; \
        else \
            echo "Using latest tag: $LATEST_TAG" && \
            echo "$LATEST_TAG" > version.txt && \
            git clone --branch "v$LATEST_TAG" --depth 1 https://github.com/mmb-irb/mddb-vre.git; \
        fi; \
    else \
        git clone --branch "v${VERSION}" --depth 1 https://github.com/mmb-irb/mddb-vre.git; \
        echo "$VERSION" > version.txt; \
    fi

# Define the build arguments
ARG VRE_LITE_BASE_URL_DEVELOPMENT
ARG VRE_LITE_BASE_URL_STAGING
ARG VRE_LITE_BASE_URL_PRODUCTION
ARG VRE_LITE_LOG_PATH
ARG VRE_LITE_MAX_FILE_SIZE
ARG VRE_LITE_TIME_DIFF
ARG MINIO_PROTOCOL
ARG MINIO_URL
ARG MINIO_PORT
ARG MINIO_USER
ARG DB_USER
ARG DB_PASS
ARG DB_SERVER
ARG DB_PORT
ARG DB_NAME
ARG PAT
ARG STACK_NAME
ARG NODE_NAME

RUN echo "BASE_URL_DEVELOPMENT=${VRE_LITE_BASE_URL_DEVELOPMENT}" > /app/mddb-vre/.env && \
    echo "BASE_URL_STAGING=${VRE_LITE_BASE_URL_STAGING}" >> /app/mddb-vre/.env && \
    echo "BASE_URL_PRODUCTION=${VRE_LITE_BASE_URL_PRODUCTION}" >> /app/mddb-vre/.env && \
    echo "LOG_PATH=${VRE_LITE_LOG_PATH}" >> /app/mddb-vre/.env && \
    echo "MAX_FILE_SIZE=${VRE_LITE_MAX_FILE_SIZE}" >> /app/mddb-vre/.env && \
    echo "TIME_DIFF=${VRE_LITE_TIME_DIFF}" >> /app/mddb-vre/.env && \
    echo "MINIO_PROTOCOL=${MINIO_PROTOCOL}" >> /app/mddb-vre/.env && \
    echo "MINIO_URL=${MINIO_URL}" >> /app/mddb-vre/.env && \
    echo "MINIO_PORT=${MINIO_PORT}" >> /app/mddb-vre/.env && \
    echo "MINIO_USER=${MINIO_USER}" >> /app/mddb-vre/.env && \
    echo "DB_USER=${DB_USER}" >> /app/mddb-vre/.env && \
    echo "DB_PASS=${DB_PASS}" >> /app/mddb-vre/.env && \
    echo "DB_SERVER=${DB_SERVER}" >> /app/mddb-vre/.env && \
    echo "DB_PORT=${DB_PORT}" >> /app/mddb-vre/.env && \
    echo "DB_NAME=${DB_NAME}" >> /app/mddb-vre/.env && \
    echo "PAT=${PAT}" >> /app/mddb-vre/.env && \
    echo "STACK_NAME=${STACK_NAME}" >> /app/mddb-vre/.env && \
    echo "NODE_NAME=${NODE_NAME}" >> /app/mddb-vre/.env

# Change working directory to /app/mddb-vre
WORKDIR /app/mddb-vre

# Copy package-lock.json to the working directory to fix dependencies versions
COPY package-lock.json .

# Install dependencies
RUN npm install --legacy-peer-deps

# Build website in production
RUN npm run build:production

# Stage 2: Serve the Nuxt app with pm2
FROM docker.io/library/nginx:alpine

# Upgrade the base image system packages to get security fixes (e.g. brotli, openssl)
# 'apk add' alone does not upgrade packages already present in the base image
RUN apk upgrade --no-cache

# Install necessary packages
RUN apk --no-cache add nodejs npm curl

# Install pm2
RUN npm install pm2 -g

# Set working directory
WORKDIR /app

# Copy the built Nuxt app from the previous stage
COPY --from=build /app/mddb-vre/.output /app/.output
# Copy the version file
COPY --from=build /app/version.txt /app/version.txt

# Copy the pm2 configuration file
COPY ecosystem.config.cjs .

# Install minio client: copy the statically linked mc from the pgsty/mc image, which is released
# more often than pgsty/minio, so it gets security fixes on every rebuild
# (MinIO no longer publishes community binaries)
COPY --from=docker.io/pgsty/mc:latest /usr/bin/mc /usr/local/bin/mc

# Define arguments passed from docker-compose
ARG VRE_LITE_INNER_PORT
ARG MINIO_USER
ARG MINIO_PASSWORD
ARG MINIO_API_PORT
ARG MINIO_ADDRESS

# Set the environment variables
ENV MINIO_USER=$MINIO_USER
ENV MINIO_PASSWORD=$MINIO_PASSWORD
ENV MINIO_API_PORT=$MINIO_API_PORT
ENV MINIO_ADDRESS=${MINIO_ADDRESS:-minio}

# Ports used to check the status of the other services over HTTP (mddb-vre server/utils/status.js).
# vre_lite has no access to the Docker socket.
ARG CLIENT_INNER_PORT
ARG REST_INNER_PORT
ARG SERVICES_MONITOR_API_INNER_PORT
ENV CLIENT_INNER_PORT=${CLIENT_INNER_PORT:-80}
ENV REST_INNER_PORT=${REST_INNER_PORT:-3000}
ENV SERVICES_MONITOR_API_INNER_PORT=${SERVICES_MONITOR_API_INNER_PORT:-3001}

# Create the entrypoint script
RUN echo '#!/bin/sh' > entrypoint.sh && \
    echo 'until curl -f http://$MINIO_ADDRESS:$MINIO_API_PORT/minio/health/live; do' >> entrypoint.sh && \
    echo '  echo "Waiting for minio to be healthy..."' >> entrypoint.sh && \
    echo '  sleep 5' >> entrypoint.sh && \
    echo 'done' >> entrypoint.sh && \
    echo 'mc alias set myminio http://$MINIO_ADDRESS:$MINIO_API_PORT $MINIO_USER $MINIO_PASSWORD' >> entrypoint.sh && \
    echo 'exec pm2-runtime start ecosystem.config.cjs --name mddb-vre' >> entrypoint.sh && \
    chmod +x entrypoint.sh

# Run as an unprivileged user (pm2 and mc keep their files in its home).
# The log volume mounted at /vre_lite must be writable by uid 65532: see readme/update.md
RUN adduser -D -u 65532 -h /home/vre vre
USER vre

# Expose the port the app runs on
EXPOSE ${VRE_LITE_INNER_PORT}

# Serve the app
ENTRYPOINT ["/app/entrypoint.sh"]
