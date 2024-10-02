# Stage 1: Build the Nuxt app
FROM node:18.19.0 AS build

# Set working directory
WORKDIR /app

# Clone mddb-vre repo
RUN git clone https://mmb.irbbarcelona.org/gitlab/gbayarri/mddb-vre.git

# Copy the .env file into the Docker image
COPY .env /app/mddb-vre

# Change working directory to /app/mddb-vre
WORKDIR /app/mddb-vre

# Install dependencies
RUN npm install

# Build website in production
RUN npm run build:production

# Stage 2: Serve the Nuxt app with pm2
FROM alpine:latest

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

# Expose the port the app runs on
EXPOSE 3001

# Define arguments passed from docker-compose
ARG MINIO_ROOT_USER
ARG MINIO_ROOT_PASSWORD
ARG MINIO_API_PORT

# Set the environment variables
ENV MINIO_ROOT_USER=$MINIO_ROOT_USER
ENV MINIO_ROOT_PASSWORD=$MINIO_ROOT_PASSWORD
ENV MINIO_API_PORT=$MINIO_API_PORT

# Create the entrypoint script
RUN echo '#!/bin/sh' > entrypoint.sh && \
    echo 'until curl -f http://minio:$MINIO_API_PORT/minio/health/live; do' >> entrypoint.sh && \
    echo '  echo "Waiting for minio to be healthy..."' >> entrypoint.sh && \
    echo '  sleep 5' >> entrypoint.sh && \
    echo 'done' >> entrypoint.sh && \
    echo 'mc alias set myminio http://minio:$MINIO_API_PORT $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD' >> entrypoint.sh && \
    echo 'exec pm2-runtime start ecosystem.config.cjs --name mddb-vre' >> entrypoint.sh && \
    chmod +x entrypoint.sh

# Serve the app
ENTRYPOINT ["/app/entrypoint.sh"]
