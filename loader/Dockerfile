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
RUN git clone https://github.com/mmb-irb/MoDEL-CNS-DB-loader.git

# Define environment variables
ARG DB_SERVER
ARG DB_PORT
ARG DB_NAME
ARG DB_AUTHSOURCE
ARG DB_AUTH_USER
ARG DB_AUTH_PASSWORD

# Create .env file with environment variables
RUN echo "DB_SERVER=${DB_SERVER}" > /app/MoDEL-CNS-DB-loader/.env && \
    echo "DB_PORT=${DB_PORT}" >> /app/MoDEL-CNS-DB-loader/.env && \
    echo "DB_NAME=${DB_NAME}" >> /app/MoDEL-CNS-DB-loader/.env && \
    echo "DB_AUTHSOURCE=${DB_AUTHSOURCE}" >> /app/MoDEL-CNS-DB-loader/.env && \
    echo "DB_AUTH_USER=${DB_AUTH_USER}" >> /app/MoDEL-CNS-DB-loader/.env && \
    echo "DB_AUTH_PASSWORD=${DB_AUTH_PASSWORD}" >> /app/MoDEL-CNS-DB-loader/.env

# Copy the environment.yml file into the Docker image
COPY environment.yml /app

# Create new environment
RUN conda env create -f /app/environment.yml && conda clean -afy

# Change working directory to /app/MoDEL-CNS-DB-loader
WORKDIR /app/MoDEL-CNS-DB-loader

# Install loader
RUN npm install

# Change working directory to /app
WORKDIR /app

# Create the entrypoint script
RUN echo '#!/bin/bash' > entrypoint.sh && \
    echo 'source activate mwf_env' >> entrypoint.sh && \
    echo 'node /app/MoDEL-CNS-DB-loader/index.js "$@"' >> entrypoint.sh && \
    chmod +x entrypoint.sh

# Set the entrypoint script as the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]