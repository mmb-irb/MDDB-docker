# Stage 1: Download and build the client
FROM node:26.12.1-alpine AS build

# Install git and the build dependencies of canvas (needed by molstar)
RUN apk add --no-cache \
    git \
    curl \
    python3 \
    make \
    g++ \
    pkgconfig \
    cairo-dev \
    pango-dev \
    libjpeg-turbo-dev \
    giflib-dev \
    librsvg-dev \
    pixman-dev

WORKDIR /app

# Version argument
ARG VERSION

# If version is set, clone that version of the client
# Otherwise, use the latest release, or the latest version tag if there are no releases
RUN if [ -z "$VERSION" ]; then \
        VERSION=$(curl -s "https://api.github.com/repos/mmb-irb/MDposit-client/releases/latest" \
            | grep -m 1 '"tag_name":' \
            | sed -E 's/.*"tag_name": "v?([^"]+)".*/\1/'); \
        if [ -z "$VERSION" ]; then \
            VERSION=$(curl -s "https://api.github.com/repos/mmb-irb/MDposit-client/tags?per_page=100" \
                | grep '"name":' \
                | sed -E 's/.*"name": "v?([^"]+)".*/\1/' \
                | grep -E '^[0-9]+(\.[0-9]+)*$' \
                | sort -V | tail -n 1); \
        fi; \
        if [ -z "$VERSION" ]; then echo "Could not find the latest version of MDposit-client" >&2; exit 1; fi; \
    fi && \
    echo "Using MDposit-client v$VERSION" && \
    git clone --branch "v$VERSION" --depth 1 https://github.com/mmb-irb/MDposit-client.git && \
    echo "$VERSION" > version.txt

# Copy the build context, which may include the node host configuration file (client/host-config.js)
# and the node images (client/images/)
COPY . /context

WORKDIR /app/MDposit-client

# If there is a node host configuration file then the client uses it instead of its default one
# Since v0.0.22 the client takes it from host-config.js at its repository root and fills the missing fields with default values
# Older clients would ignore it without any warning, so stop the build instead
RUN if [ -f /context/host-config.js ]; then \
        if [ ! -f src/utils/constants/process-host-config.js ]; then \
            echo "client/host-config.js needs MDposit-client v0.0.22 or newer (this is v$(cat /app/version.txt))" >&2; exit 1; \
        fi; \
        echo "Using the node host configuration file"; \
        cp /context/host-config.js host-config.js; \
    else \
        echo "No host-config.js found: using the client default host configuration"; \
    fi

# Node specific images (e.g. footer logos), which host-config.js imports from 'src/images/untracked/...'
RUN if [ -d /context/images ]; then \
        mkdir -p src/images/untracked && cp -r /context/images/. src/images/untracked/; \
    fi

# Create an empty .env file
RUN touch .env

# Install packages
RUN npm ci

# Build website
RUN npm run build

# Stage 2: Serve the client app with nginx
FROM docker.io/library/nginx:alpine

# Upgrade the base image system packages to get security fixes (e.g. brotli, openssl)
# 'apk add' alone does not upgrade packages already present in the base image
RUN apk upgrade --no-cache

# Define the build arguments
ARG CLIENT_INNER_PORT

WORKDIR /app

# Copy the version and the build from the previous stage
COPY --from=build /app/version.txt /app/version.txt
COPY --from=build /app/MDposit-client/build /usr/share/nginx/html

# Publish the version so that vre_lite's status page can ask the running client for it
RUN cp /app/version.txt /usr/share/nginx/html/version.txt

# Expose port ${CLIENT_INNER_PORT}
EXPOSE ${CLIENT_INNER_PORT}

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
