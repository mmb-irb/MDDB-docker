# Use Alpine Linux as base image
FROM alpine:latest

# Install necessary packages
RUN apk --no-cache add nodejs npm git
RUN apk add build-base
RUN apk add cmake

# Define working dir
WORKDIR /app

# Clone and install the chemfiles fork customized to support '.bin' format reading and streaming.
RUN git clone https://github.com/d-beltran/chemfiles --depth 1 && cd chemfiles && git fetch --unshallow  && mkdir build && cd build && cmake .. && make && make install

# Verify installation
RUN node --version && npm --version && git --version

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

# Install pm2
RUN npm install pm2 -g

# Expose the port the app runs on
EXPOSE 3000

# Serve the app
#CMD ["pm2-runtime", "start", "index.js", "-i", "4", "-n", "MDposit_API", "--node-args=", "\"--experimental-worker\""]
CMD ["pm2-runtime", "start", "index.js", "-n", "MDposit_API", "--node-args=", "\"--experimental-worker\""]