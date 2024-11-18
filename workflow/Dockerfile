# Base docker with miniconda
FROM continuumio/miniconda3

# Define working dir
WORKDIR /app

# Install libgl1 for avoiding problems with VMD
RUN apt-get update && apt-get install -y libgl1

RUN mkdir /mnt

# Download goofys and make it executable
RUN wget https://github.com/kahing/goofys/releases/latest/download/goofys
RUN chmod +x goofys 

# Clone repo
RUN git clone https://mmb.irbbarcelona.org/gitlab/d.beltran.anadon/MoDEL-workflow.git

# Create new environment
RUN conda env create -f /app/MoDEL-workflow/environment.yml && conda clean -afy

# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "mwf_env", "/bin/bash", "-c"]

# Re-install sqlite SW
RUN conda install sqlite --force-reinstall

# Install mwf SW
RUN python /app/MoDEL-workflow/setup.py develop

# Export python path
ENV PYTHONPATH="${PYTHONPATH}:/app/MoDEL-workflow"

# Define arguments passed from docker-compose
ARG MINIO_ROOT_USER
ARG MINIO_ROOT_PASSWORD
ARG MINIO_API_PORT

# Set the environment variables
ENV MINIO_ROOT_USER=$MINIO_ROOT_USER
ENV MINIO_ROOT_PASSWORD=$MINIO_ROOT_PASSWORD
ENV MINIO_API_PORT=$MINIO_API_PORT

# Code to run when container is started
#ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "mwf_env"]
RUN echo '#!/bin/sh' > entrypoint.sh && \
    echo 'if [ -n $BUCKET ]; then' >> entrypoint.sh && \
    echo '  export AWS_ACCESS_KEY_ID=$MINIO_ROOT_USER' >> entrypoint.sh && \
    echo '  export AWS_SECRET_ACCESS_KEY=$MINIO_ROOT_PASSWORD' >> entrypoint.sh && \
    echo '  /app/goofys --endpoint http://minio:$MINIO_API_PORT $BUCKET /mnt/' >> entrypoint.sh && \
    echo 'fi' >> entrypoint.sh && \
    echo 'conda run --no-capture-output -n mwf_env' >> entrypoint.sh && \
    echo 'if [ -n $BUCKET ]; then' >> entrypoint.sh && \
    echo '  fusermount -u /mnt' >> entrypoint.sh && \
    echo 'fi' >> entrypoint.sh && \
    chmod +x entrypoint.sh

# Serve the app
ENTRYPOINT ["/app/entrypoint.sh"]
