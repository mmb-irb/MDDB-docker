# Use the lightweight Python Alpine image
FROM python:3.9-alpine

# Define arguments passed from docker-compose
ARG LOG_PATH=
ARG TIME_DIFF=
ARG MINIO_ROOT_USER=
ARG MINIO_ROOT_PASSWORD=
ARG MINIO_PORT=

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY vrelite.py /app

# Install necessary packages
RUN apk update && apk add --no-cache \
    dcron \
    curl

# Install minio client
RUN curl -O https://dl.min.io/client/mc/release/linux-amd64/mc && \
    chmod +x mc && \
    mv mc /usr/local/bin/

# Create the crontab file using environment variables
RUN echo "30 0 * * * python /app/vrelite.py $LOG_PATH $TIME_DIFF $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD http://minio:$MINIO_PORT >> /var/log/cron_vrelite.log 2>&1" > /etc/cron.d/my-vrelite-cronjob

# more than one cron job
#RUN echo "30 0 * * * python /app/vrelite.py $LOG_PATH $TIME_DIFF $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD http://minio:$MINIO_PORT >> /var/log/cron_vrelite.log 2>&1" > /etc/cron.d/my-vrelite-cronjob && \
#    echo "9 11 * * * python /app/vrelite.py $LOG_PATH $TIME_DIFF $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD http://minio:$MINIO_PORT >> /var/log/cron2.log 2>&1" >> /etc/cron.d/my-vrelite-cronjob

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/my-vrelite-cronjob

# Apply the cron job
RUN crontab /etc/cron.d/my-vrelite-cronjob

# Create the log file to be able to run tail
RUN touch /var/log/cron_vrelite.log

# more than one log file
# RUN touch /var/log/cron_vrelite.log /var/log/cron2.log

# Run the command on container startup
CMD ["sh", "-c", "crond && tail -f /var/log/cron_vrelite.log"]

# more than one log file
# CMD ["sh", "-c", "crond && tail -f /var/log/cron_vrelite.log /var/log/cron2.log"]