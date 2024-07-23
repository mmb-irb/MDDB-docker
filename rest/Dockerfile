# Use Alpine Linux as base image
FROM alpine:latest

# Install necessary packages
RUN apk --no-cache add nodejs npm git

# Verify installation
RUN node --version && npm --version && git --version

# Define working dir
WORKDIR /app

# Define a directory for the volume
VOLUME /data

# Clone MoDEL-CNS_REST_API repo
RUN git clone https://mmb.irbbarcelona.org/gitlab/aluciani/MoDEL-CNS_REST_API

# Copy the .env file into the Docker image
COPY .env /app/MoDEL-CNS_REST_API

# Change working directory to /app/MoDEL-CNS_REST_API
WORKDIR /app/MoDEL-CNS_REST_API

# Install packages
RUN npm install

# Build website
RUN npm run build

# remove node_modules folder
RUN rm -r node_modules

# Install pm2
RUN npm install pm2 -g

# Copy the pm2 configuration file
COPY ecosystem.config.cjs .

# Expose the port the app runs on
EXPOSE 3000

# Serve the app
CMD ["pm2-runtime", "start", "ecosystem.config.cjs", "--name", "rest"]
