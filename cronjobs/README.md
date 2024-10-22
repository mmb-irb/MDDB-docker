### Cronjobs

For the sake of performing **automatic operations** such as cleaning or checking, there is a **cron jobs service**.

## Dockerfile

```Dockerfile
# Use the lightweight Python Alpine image
FROM python:3.9-alpine

# Define arguments passed from docker-compose
ARG VRE_LITE_LOG_PATH
ARG VRE_LITE_TIME_DIFF
ARG CJ_VRE_LITE_LOG_PATH
ARG MINIO_ROOT_USER
ARG MINIO_ROOT_PASSWORD
ARG MINIO_PORT

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
RUN echo "30 0 * * * python /app/vrelite.py $VRE_LITE_LOG_PATH $VRE_LITE_TIME_DIFF $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD http://minio:$MINIO_PORT >> $CJ_VRE_LITE_LOG_PATH 2>&1" > /etc/cron.d/my-vrelite-cronjob

# more than one cron job
#RUN echo "30 0 * * * python /app/vrelite.py $VRE_LITE_LOG_PATH $VRE_LITE_TIME_DIFF $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD http://minio:$MINIO_PORT >> $CJ_VRE_LITE_LOG_PATH 2>&1" > /etc/cron.d/my-vrelite-cronjob && \
#    echo "9 11 * * * python /app/vrelite.py $VRE_LITE_LOG_PATH $VRE_LITE_TIME_DIFF $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD http://minio:$MINIO_PORT >> $CJ_OPENVRE_LOG_PATH 2>&1" >> /etc/cron.d/my-vrelite-cronjob

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/my-vrelite-cronjob

# Apply the cron job
RUN crontab /etc/cron.d/my-vrelite-cronjob

# Set the environment variable
ENV CJ_VRE_LITE_LOG_PATH=$CJ_VRE_LITE_LOG_PATH

# Create the initialization script
RUN echo '#!/bin/sh' > /usr/local/bin/init.sh && \
    echo 'mkdir -p $(dirname $CJ_VRE_LITE_LOG_PATH)' >> /usr/local/bin/init.sh && \
    echo 'touch $CJ_VRE_LITE_LOG_PATH' >> /usr/local/bin/init.sh && \
    echo 'crond' >> /usr/local/bin/init.sh && \
    echo 'tail -f $CJ_VRE_LITE_LOG_PATH' >> /usr/local/bin/init.sh && \
    chmod +x /usr/local/bin/init.sh

# Run the initialization script on container startup
CMD ["/usr/local/bin/init.sh"]
```