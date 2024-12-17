# Stage 1: Build the Nuxt app
FROM node:18.19.0 AS build

# Set working directory
WORKDIR /app

# Clone mddb-vre repo
RUN git clone https://mmb.irbbarcelona.org/gitlab/gbayarri/mddb-vre.git

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
    echo "NODE_NAME=${NODE_NAME}" >> /app/mddb-vre/.env

# Change working directory to /app/mddb-vre
WORKDIR /app/mddb-vre

# Install dependencies
RUN npm install

# Build website in production
RUN npm run build:production

# Stage 2: Serve the Nuxt app with pm2
FROM docker.io/library/nginx:alpine

# Install necessary packages
RUN apk --no-cache add nodejs npm curl

# Install pm2
RUN npm install pm2 -g

# Set working directory
WORKDIR /app

# Copy the built Nuxt app from the previous stage
COPY --from=build /app/mddb-vre/.output /app/.output

# Copy the pm2 configuration file
COPY ecosystem.config.cjs .

# Install minio client
RUN curl -O https://dl.min.io/client/mc/release/linux-amd64/mc && \
    chmod +x mc && \
    mv mc /usr/local/bin/

# Define arguments passed from docker-compose
ARG VRE_LITE_INNER_PORT
ARG MINIO_USER
ARG MINIO_PASSWORD
ARG MINIO_API_PORT

# Set the environment variables
ENV MINIO_USER=$MINIO_USER
ENV MINIO_PASSWORD=$MINIO_PASSWORD
ENV MINIO_API_PORT=$MINIO_API_PORT

# Create the entrypoint script
RUN echo '#!/bin/sh' > entrypoint.sh && \
    echo 'until curl -f http://minio:$MINIO_API_PORT/minio/health/live; do' >> entrypoint.sh && \
    echo '  echo "Waiting for minio to be healthy..."' >> entrypoint.sh && \
    echo '  sleep 5' >> entrypoint.sh && \
    echo 'done' >> entrypoint.sh && \
    echo 'mc alias set myminio http://minio:$MINIO_API_PORT $MINIO_PASSWORD $MINIO_PASSWORD' >> entrypoint.sh && \
    echo 'exec pm2-runtime start ecosystem.config.cjs --name mddb-vre' >> entrypoint.sh && \
    chmod +x entrypoint.sh

# Expose the port the app runs on
EXPOSE ${VRE_LITE_INNER_PORT}

# Serve the app
ENTRYPOINT ["/app/entrypoint.sh"]
