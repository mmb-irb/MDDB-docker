# Base docker with miniconda
FROM docker.io/continuumio/miniconda3:latest

# Define working dir
WORKDIR /app

# Install Node.js
RUN apt-get update && \
    apt-get install -y curl && \
    curl -sL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# Version argument
ARG VERSION

# If version is set, wget the specific version of the loader
# Otherwise, use the latest version
RUN if [ -z "$VERSION" ]; then \
        echo "No VERSION provided, fetching latest release..." && \
        LATEST_TAG=$(curl -s "https://api.github.com/repos/mmb-irb/MDDB-loader/releases/latest" \
            | grep -m 1 '"tag_name":' \
            | sed -E 's/.*"tag_name": "v?([^"]+)".*/\1/') && \
        if [ -z "$LATEST_TAG" ]; then \
            echo "No releases found, fetching latest tag..." && \
            LATEST_TAG=$(curl -s "https://api.github.com/repos/mmb-irb/MDDB-loader/tags?per_page=100" \
                | grep '"name":' \
                | sed -E 's/.*"name": "v?([^"]+)".*/\1/' \
                | grep -E '^[0-9]+(\.[0-9]+)*$' \
                | sort -V | tail -n 1); \
        fi && \
        if [ -z "$LATEST_TAG" ]; then \
            echo "Failed to fetch latest tag, using master branch" && \
            git clone --branch master --depth 1 https://github.com/mmb-irb/MDDB-loader.git && \
            echo "master" > version.txt; \
        else \
            echo "Using latest tag: $LATEST_TAG" && \
            echo "$LATEST_TAG" > version.txt && \
            git clone --branch "v$LATEST_TAG" --depth 1 https://github.com/mmb-irb/MDDB-loader.git; \
        fi; \
    else \
        git clone --branch "v${VERSION}" --depth 1 https://github.com/mmb-irb/MDDB-loader.git; \
        echo "$VERSION" > version.txt; \
    fi

# Define environment variables
ARG DB_SERVER
ARG DB_PORT
ARG DB_NAME
ARG DB_AUTHSOURCE
ARG DB_AUTH_USER
ARG DB_AUTH_PASSWORD

# Create .env file with environment variables
RUN echo "DB_SERVER=${DB_SERVER}" > /app/MDDB-loader/.env && \
    echo "DB_PORT=${DB_PORT}" >> /app/MDDB-loader/.env && \
    echo "DB_NAME=${DB_NAME}" >> /app/MDDB-loader/.env && \
    echo "DB_AUTHSOURCE=${DB_AUTHSOURCE}" >> /app/MDDB-loader/.env && \
    echo "DB_AUTH_USER=${DB_AUTH_USER}" >> /app/MDDB-loader/.env && \
    echo "DB_AUTH_PASSWORD=${DB_AUTH_PASSWORD}" >> /app/MDDB-loader/.env

# Copy the environment.yml file into the Docker image
COPY environment.yml /app

# Create new environment
RUN conda env create -f /app/environment.yml && conda clean -afy

# Change working directory to /app/MDDB-loader
WORKDIR /app/MDDB-loader

# Install loader
RUN npm install

# Change working directory to /app
WORKDIR /app

# Create the entrypoint script
RUN echo '#!/bin/bash' > entrypoint.sh && \
    echo 'source activate mwf_env' >> entrypoint.sh && \
    echo 'node /app/MDDB-loader/index.js "$@"' >> entrypoint.sh && \
    chmod +x entrypoint.sh

# Set the entrypoint script as the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]