# Base docker with miniconda
FROM docker.io/continuumio/miniconda3:latest

# Define working dir
WORKDIR /app

# Install libgl1 for avoiding problems with VMD and fuse for using fusermount and goofys
RUN apt-get update && \
    apt-get install -y libgl1 && \
    apt-get install -y fuse

# Download goofys and make it executable
# RUN wget https://github.com/kahing/goofys/releases/latest/download/goofys
COPY goofys .
RUN chmod +x goofys 

# Clone repo
RUN git clone https://mmb.irbbarcelona.org/gitlab/d.beltran.anadon/MoDEL-workflow.git

# Enable libmamba as solver
RUN conda config --set solver libmamba

# Create new environment
RUN conda env create --file=/app/MoDEL-workflow/environment.yml && conda clean -afy

# Re-install sqlite SW
RUN conda run -n mwf_env conda install sqlite --force-reinstall

# Install mwf SW
RUN conda run -n mwf_env python /app/MoDEL-workflow/setup.py develop

# Export python path
ENV PYTHONPATH="${PYTHONPATH}:/app/MoDEL-workflow"

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
