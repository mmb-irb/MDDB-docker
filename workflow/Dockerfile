# Base docker with miniconda
FROM docker.io/continuumio/miniconda3:latest

# Define working dir
WORKDIR /app

# Install libgl1 for avoiding problems with VMD and fuse for using fusermount and goofys
RUN apt-get update && \
    apt-get install -y libgl1 && \
    apt-get install -y fuse curl

# Download goofys and make it executable
# RUN wget https://github.com/kahing/goofys/releases/latest/download/goofys
COPY goofys .
RUN chmod +x goofys 

# Version argument
ARG VERSION

# If version is set, wget the specific version of the workflow
# Otherwise, use the latest version
RUN if [ -z "$VERSION" ]; then \
        echo "No VERSION provided, fetching latest release..." && \
        LATEST_TAG=$(curl -s "https://api.github.com/repos/mmb-irb/MDDB-workflow/releases/latest" \
            | grep -m 1 '"tag_name":' \
            | sed -E 's/.*"tag_name": "v?([^"]+)".*/\1/') && \
        if [ -z "$LATEST_TAG" ]; then \
            echo "No releases found, fetching latest tag..." && \
            LATEST_TAG=$(curl -s "https://api.github.com/repos/mmb-irb/MDDB-workflow/tags?per_page=100" \
                | grep '"name":' \
                | sed -E 's/.*"name": "v?([^"]+)".*/\1/' \
                | grep -E '^[0-9]+(\.[0-9]+)*$' \
                | sort -V | tail -n 1); \
        fi && \
        if [ -z "$LATEST_TAG" ]; then \
            echo "Failed to fetch latest tag, using master branch" && \
            git clone --branch master --depth 1 https://github.com/mmb-irb/MDDB-workflow.git && \
            echo "master" > version.txt; \
        else \
            echo "Using latest tag: $LATEST_TAG" && \
            echo "$LATEST_TAG" > version.txt && \
            git clone --branch "v$LATEST_TAG" --depth 1 https://github.com/mmb-irb/MDDB-workflow.git; \
        fi; \
    else \
        git clone --branch "v${VERSION}" --depth 1 https://github.com/mmb-irb/MDDB-workflow.git; \
        echo "$VERSION" > version.txt; \
    fi

# Enable libmamba as solver
RUN conda config --set solver libmamba

# Create new environment
RUN conda env create --file=/app/MDDB-workflow/envs/environment.yml && conda clean -afy

# Install mwf SW
WORKDIR /app/MDDB-workflow
RUN conda run -n mwf_env python -m pip install -e .

# Define working dir
WORKDIR /app

# Export python path
ENV PYTHONPATH="${PYTHONPATH}:/app/MDDB-workflow"

# Define arguments passed from docker-compose
ARG MINIO_USER
ARG MINIO_PASSWORD
ARG MINIO_API_PORT

# Set the environment variables
ENV MINIO_USER=$MINIO_USER
ENV MINIO_PASSWORD=$MINIO_PASSWORD
ENV MINIO_API_PORT=$MINIO_API_PORT

# Code to run when container is started
RUN echo '#!/bin/sh' > entrypoint.sh && \
    echo 'if [ -n "$BUCKET" ]; then' >> entrypoint.sh && \
    echo '  export AWS_ACCESS_KEY_ID=$MINIO_USER' >> entrypoint.sh && \
    echo '  export AWS_SECRET_ACCESS_KEY=$MINIO_PASSWORD' >> entrypoint.sh && \
    echo '  /app/goofys --endpoint http://minio:$MINIO_API_PORT $BUCKET /mnt' >> entrypoint.sh && \
    echo 'fi' >> entrypoint.sh && \
    echo 'conda run --no-capture-output -n mwf_env "$@"' >> entrypoint.sh && \
    echo 'if [ -n "$BUCKET" ]; then' >> entrypoint.sh && \
    echo '  fusermount -u /mnt' >> entrypoint.sh && \
    echo 'fi' >> entrypoint.sh && \
    chmod +x entrypoint.sh

# Serve the app
ENTRYPOINT ["/app/entrypoint.sh"]
