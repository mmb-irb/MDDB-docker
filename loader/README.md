# Loader

The **data loader** is a  **node JS script** made for load, list and remove data from a mongodb database.

For this project, the following repo has been used:

https://github.com/mmb-irb/MDDB-loader/

## Dockerfile

This Dockerfile is used taking as a starting point the **repository** of the loader.

```Dockerfile
# Base docker with miniconda
FROM docker.io/continuumio/miniconda3:latest

# Define working dir
WORKDIR /app

# Install Node.js
RUN apt-get update && \
    apt-get install -y curl && \
    curl -sL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# Clone loader repo
RUN git clone https://github.com/mmb-irb/MDDB-loader.git

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
```