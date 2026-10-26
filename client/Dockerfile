# Use nginx Alpine Linux as base image
FROM docker.io/library/nginx:alpine

# Define the build arguments
ARG VERSION
ARG CLIENT_INNER_PORT

# Version argument
WORKDIR /app

# If version is set, wget the specific version of the client build
# Otherwise, use the latest version
RUN if [ -z "$VERSION" ]; then \
        wget https://github.com/mmb-irb/MDposit-client-build/raw/refs/heads/main/build.zip; \
        LATEST_TAG=$(curl -s "https://api.github.com/repos/mmb-irb/MDposit-client-build/releases/latest" \
            | grep -m 1 '"tag_name":' \
            | sed -E 's/.*"tag_name": "v?([^"]+)".*/\1/') && \
        if [ -z "$LATEST_TAG" ]; then \
            LATEST_TAG=$(curl -s "https://api.github.com/repos/mmb-irb/MDposit-client-build/tags?per_page=100" \
                | grep '"name":' \
                | sed -E 's/.*"name": "v?([^"]+)".*/\1/' \
                | grep -E '^[0-9]+(\.[0-9]+)*$' \
                | sort -V | tail -n 1); \
        fi && \
        echo "$LATEST_TAG" > version.txt; \
    else \
        wget https://raw.githubusercontent.com/mmb-irb/MDposit-client-build/v$VERSION/build.zip; \
        echo "$VERSION" > version.txt; \
    fi

# Unzip mdposit-client-build repo
RUN unzip build.zip

# Copy the built React app to nginx
RUN cp -r /app/build/* /usr/share/nginx/html

# Expose port ${CLIENT_INNER_PORT}
EXPOSE ${CLIENT_INNER_PORT}

# Start nginx
CMD ["nginx", "-g", "daemon off;"]