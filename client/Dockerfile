# Use nginx Alpine Linux as base image
FROM docker.io/library/nginx:alpine

# Define the build arguments
ARG CLIENT_INNER_PORT

# Define working dir
WORKDIR /app

# Download and unzip mdposit-client-build repo
RUN wget https://github.com/mmb-irb/MDposit-client-build/raw/refs/heads/main/build.zip
RUN unzip build.zip

# Copy the built React app to nginx
RUN cp -r /app/build/* /usr/share/nginx/html

# Expose port ${CLIENT_INNER_PORT}
EXPOSE ${CLIENT_INNER_PORT}

# Start nginx
CMD ["nginx", "-g", "daemon off;"]