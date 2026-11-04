# Single stage build with both Python and Node.js
# Node.js comes from the Alpine package instead of the node image: the official node binaries
# bundle their own brotli, while the Alpine package uses the system one, which gets security fixes
FROM docker.io/library/alpine:3.24

# Upgrade the base image system packages to get security fixes (e.g. brotli, openssl)
# 'apk add' alone does not upgrade packages already present in the base image
RUN apk upgrade --no-cache

# Install system packages needed for both Python and Node.js
RUN apk add --no-cache \
    nodejs \
    npm \
    python3 \
    python3-dev \
    py3-pip \
    dcron \
    curl \
    build-base \
    libffi-dev

# Set working directory
WORKDIR /app

# Copy Python scripts
COPY collector.py ./scripts/
COPY report_generator.py ./scripts/
COPY utils.py ./scripts/

# Install Python dependencies (using --break-system-packages for Docker environment)
RUN pip3 install --no-cache-dir --break-system-packages pymongo requests

# Copy Node.js application files
COPY package.json ./
COPY api/ ./api/

# Install Node.js dependencies
RUN npm install --omit=dev

# Define build arguments
ARG DB_SERVER
ARG DB_PORT
ARG DB_NAME
ARG DB_AUTH_USER
ARG DB_AUTH_PASSWORD
ARG DB_AUTHSOURCE
ARG API_PORT
ARG API_KEY
ARG SLACK_WEBHOOK_URL
ARG COLLECTOR_SCHEDULE_1
ARG COLLECTOR_SCHEDULE_2
ARG COLLECTOR_SCHEDULE_3

# Set environment variables
ENV DB_SERVER=${DB_SERVER}
ENV DB_PORT=${DB_PORT}
ENV DB_NAME=${DB_NAME}
ENV DB_AUTH_USER=${DB_AUTH_USER}
ENV DB_AUTH_PASSWORD=${DB_AUTH_PASSWORD}
ENV DB_AUTHSOURCE=${DB_AUTHSOURCE}
ENV API_PORT=${API_PORT}
ENV API_KEY=${API_KEY}
ENV SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}

# Create crontab with process locking to prevent duplicates
RUN echo "${COLLECTOR_SCHEDULE_1} flock -n /tmp/collector.lock -c 'cd /app/scripts && python3 collector.py' >> /var/log/services-monitor/collector.log 2>&1" > /etc/cron.d/services-monitor && \
    echo "${COLLECTOR_SCHEDULE_2} flock -n /tmp/collector.lock -c 'cd /app/scripts && python3 collector.py' >> /var/log/services-monitor/collector.log 2>&1" >> /etc/cron.d/services-monitor && \
    echo "${COLLECTOR_SCHEDULE_3} flock -n /tmp/report.lock -c 'cd /app/scripts && python3 report_generator.py' >> /var/log/services-monitor/report_generator.log 2>&1" >> /etc/cron.d/services-monitor && \
    chmod 0644 /etc/cron.d/services-monitor

# Create startup script
RUN echo '#!/bin/sh' > /usr/local/bin/start.sh && \
    echo 'mkdir -p /var/log/services-monitor' >> /usr/local/bin/start.sh && \
    echo 'touch /var/log/services-monitor/collector.log' >> /usr/local/bin/start.sh && \
    echo 'touch /var/log/services-monitor/report_generator.log' >> /usr/local/bin/start.sh && \
    echo 'touch /var/log/services-monitor/api.log' >> /usr/local/bin/start.sh && \
    echo 'echo "Starting cron daemon..."' >> /usr/local/bin/start.sh && \
    echo 'crond' >> /usr/local/bin/start.sh && \
    echo 'echo "Starting API server..."' >> /usr/local/bin/start.sh && \
    echo 'cd /app && nohup node api/server.js > /var/log/services-monitor/api.log 2>&1 &' >> /usr/local/bin/start.sh && \
    echo 'API_PID=$!' >> /usr/local/bin/start.sh && \
    echo 'echo "API server started with PID: $API_PID"' >> /usr/local/bin/start.sh && \
    echo 'sleep 2' >> /usr/local/bin/start.sh && \
    echo 'echo "Following log files..."' >> /usr/local/bin/start.sh && \
    echo 'tail -f /var/log/services-monitor/collector.log /var/log/services-monitor/report_generator.log /var/log/services-monitor/api.log' >> /usr/local/bin/start.sh && \
    chmod +x /usr/local/bin/start.sh

# Expose API port
EXPOSE ${API_PORT}

# Run the startup script
CMD ["/usr/local/bin/start.sh"]
