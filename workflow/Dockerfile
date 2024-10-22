# Base docker with miniconda
FROM continuumio/miniconda3

# Define working dir
WORKDIR /app

# Install libgl1 for avoiding problems with VMD
RUN apt-get update && apt-get install -y libgl1

# Clone repo
RUN git clone https://mmb.irbbarcelona.org/gitlab/d.beltran.anadon/MoDEL-workflow.git

# Create new environment
RUN conda env create -f /app/MoDEL-workflow/environment.yml

# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "mwf_env", "/bin/bash", "-c"]

# Re-install sqlite SW
RUN conda install sqlite --force-reinstall

# Install mwf SW
RUN python /app/MoDEL-workflow/setup.py develop

# Export python path
ENV PYTHONPATH="${PYTHONPATH}:/app/MoDEL-workflow"

# Code to run when container is started
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "mwf_env"]