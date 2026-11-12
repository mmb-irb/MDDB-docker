# Stage 1: Build the NodeJS REST API
FROM docker.io/library/nginx:alpine AS build

# Install necessary packages
RUN apk --no-cache add nodejs npm git curl

# Define working dir
WORKDIR /app

# Verify installation
RUN node --version && npm --version && git --version

# Version argument
ARG VERSION

# If version is set, wget the specific version of the rest API
# Otherwise, use the latest version
RUN if [ -z "$VERSION" ]; then \
        echo "No VERSION provided, fetching latest release..." && \
        LATEST_TAG=$(curl -s "https://api.github.com/repos/mmb-irb/MDDB-REST-API/releases/latest" \
            | grep -m 1 '"tag_name":' \
            | sed -E 's/.*"tag_name": "v?([^"]+)".*/\1/') && \
        if [ -z "$LATEST_TAG" ]; then \
            echo "No releases found, fetching latest tag..." && \
            LATEST_TAG=$(curl -s "https://api.github.com/repos/mmb-irb/MDDB-REST-API/tags?per_page=100" \
                | grep '"name":' \
                | sed -E 's/.*"name": "v?([^"]+)".*/\1/' \
                | grep -E '^[0-9]+(\.[0-9]+)*$' \
                | sort -V | tail -n 1); \
        fi && \
        if [ -z "$LATEST_TAG" ]; then \
            echo "Failed to fetch latest tag, using master branch" && \
            git clone --branch master --depth 1 https://github.com/mmb-irb/MDDB-REST-API.git && \
            echo "master" > version.txt; \
        else \
            echo "Using latest tag: $LATEST_TAG" && \
            echo "$LATEST_TAG" > version.txt && \
            git clone --branch "v$LATEST_TAG" --depth 1 https://github.com/mmb-irb/MDDB-REST-API.git; \
        fi; \
    else \
        git clone --branch "v${VERSION}" --depth 1 https://github.com/mmb-irb/MDDB-REST-API.git; \
        echo "$VERSION" > version.txt; \
    fi

# Define environment variables
ARG DB_SERVER
ARG DB_PORT
ARG DB_NAME
ARG DB_AUTHSOURCE
ARG DB_AUTH_USER
ARG DB_AUTH_PASSWORD
ARG REST_INNER_PORT
ARG HOST
ARG NODE_NAME
ARG REST_OTEL_ENDPOINT

# Create .env file with environment variables
RUN echo "DB_SERVER=${DB_SERVER}" > /app/MDDB-REST-API/.env && \
    echo "DB_PORT=${DB_PORT}" >> /app/MDDB-REST-API/.env && \
    echo "DB_NAME=${DB_NAME}" >> /app/MDDB-REST-API/.env && \
    echo "DB_AUTHSOURCE=${DB_AUTHSOURCE}" >> /app/MDDB-REST-API/.env && \
    echo "DB_AUTH_USER=${DB_AUTH_USER}" >> /app/MDDB-REST-API/.env && \
    echo "DB_AUTH_PASSWORD=${DB_AUTH_PASSWORD}" >> /app/MDDB-REST-API/.env && \
    echo "LISTEN_PORT=${REST_INNER_PORT}" >> /app/MDDB-REST-API/.env && \
    echo "HOST=${HOST}" >> /app/MDDB-REST-API/.env && \
    echo "NODE_NAME=${NODE_NAME}" >> /app/MDDB-REST-API/.env && \
    echo "OTEL_ENDPOINT=${REST_OTEL_ENDPOINT}" >> /app/MDDB-REST-API/.env

# Node host configuration file (rest/config.yml), see the README
# The wildcard lets the COPY work without config.yml (COPY only fails when none of its sources exist), so the check below explains the problem
COPY Dockerfile config.ym[l] /app/context/
# APIs after v0.0.20 (example-config.yml) require it: root keys are the host names
# v0.0.20 (example-single-config.yml) uses it if there is one
# APIs up to v0.0.19 do not support it: they keep the configuration of every node in their own config.yml
RUN if [ -f /app/MDDB-REST-API/example-config.yml ]; then \
        if [ ! -f /app/context/config.yml ]; then \
            echo "ERROR: Missing rest/config.yml, which is required by REST API v$(cat /app/version.txt) (see rest/README.md)"; \
            exit 1; \
        fi; \
        echo "Using the node host configuration file"; \
        install -m 644 /app/context/config.yml /app/MDDB-REST-API/config.yml; \
    elif [ -f /app/MDDB-REST-API/example-single-config.yml ]; then \
        if [ -f /app/context/config.yml ]; then \
            echo "Using the node host configuration file"; \
            install -m 644 /app/context/config.yml /app/MDDB-REST-API/config.yml; \
        else \
            echo "No config.yml found: using the REST API default host configuration"; \
        fi; \
    else \
        echo "REST API v$(cat /app/version.txt) uses its own config.yml with every node, rest/config.yml is ignored"; \
    fi

# Change working directory to /app/MDDB-REST-API
WORKDIR /app/MDDB-REST-API

# Install packages
RUN npm ci

# Build the WebAssembly parsers
# Note that the chemfiles converter is not built here, since it is precompiled (see below)
RUN npm run asbuild:crdparse && npm run asbuild:binparse && npm run asbuild:f32parse

# Drop the development dependencies (jest, eslint, pm2...) once the parsers are built:
# they are not needed to serve the API and only add vulnerabilities to the image
RUN npm prune --omit=dev

# Copy the precompiled trajectory format converter, which relies in a customized chemfiles
# It is statically linked, so it does not depend on any library in the image
# See README.md to update it
COPY chemfiles_bin_converter /app/MDDB-REST-API/build/chemfiles_bin_converter

# Stage 2: Serve the REST API app with pm2
FROM docker.io/library/nginx:alpine

# Upgrade the base image system packages to get security fixes (e.g. brotli, openssl)
# 'apk add' alone does not upgrade packages already present in the base image
RUN apk upgrade --no-cache

# Install necessary packages
RUN apk --no-cache add nodejs npm curl

# Install pm2
RUN npm install pm2 -g

# Set working directory
WORKDIR /app

# Copy from the previous stage
COPY --from=build /app/MDDB-REST-API /app/MDDB-REST-API
COPY --from=build /app/version.txt /app/version.txt

# Change working directory to /app/MDDB-REST-API
WORKDIR /app/MDDB-REST-API

# Define environment variable
ARG REST_INNER_PORT

# Run as an unprivileged user (pm2 keeps its files in its home)
RUN adduser -D -u 65532 -h /home/rest rest
USER rest

# Expose the port where the app runs on
EXPOSE ${REST_INNER_PORT}

# Serve the app
CMD ["pm2-runtime", "start", "index.js", "-i", "4", "-n", "MDposit_API", "--node-args=", "\"--experimental-worker\""]