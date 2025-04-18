# Stage 1: Build the NodeJS REST API
FROM docker.io/library/nginx:alpine AS build

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

# Clone MDDB-REST-API repo
RUN git clone https://github.com/mmb-irb/MDDB-REST-API.git

# Define environment variables
ARG DB_SERVER
ARG DB_PORT
ARG DB_NAME
ARG DB_AUTHSOURCE
ARG DB_AUTH_USER
ARG DB_AUTH_PASSWORD
ARG REST_INNER_PORT

# Create .env file with environment variables
RUN echo "DB_SERVER=${DB_SERVER}" > /app/MDDB-REST-API/.env && \
    echo "DB_PORT=${DB_PORT}" >> /app/MDDB-REST-API/.env && \
    echo "DB_NAME=${DB_NAME}" >> /app/MDDB-REST-API/.env && \
    echo "DB_AUTHSOURCE=${DB_AUTHSOURCE}" >> /app/MDDB-REST-API/.env && \
    echo "DB_AUTH_USER=${DB_AUTH_USER}" >> /app/MDDB-REST-API/.env && \
    echo "DB_AUTH_PASSWORD=${DB_AUTH_PASSWORD}" >> /app/MDDB-REST-API/.env && \
    echo "LISTEN_PORT=${REST_INNER_PORT}" >> /app/MDDB-REST-API/.env

# Change working directory to /app/MDDB-REST-API
WORKDIR /app/MDDB-REST-API

# Install packages
RUN npm install

# Build website
RUN npm run build

# Stage 2: Serve the REST API app with pm2
FROM docker.io/library/nginx:alpine

# Install necessary packages
RUN apk --no-cache add nodejs npm curl

# Install pm2
RUN npm install pm2 -g

# Set working directory
WORKDIR /app

# Copy from the previous stage
COPY --from=build /app/MDDB-REST-API /app/MDDB-REST-API
COPY --from=build /app/chemfiles /app/chemfiles

# Change working directory to /app/MDDB-REST-API
WORKDIR /app/MDDB-REST-API

# Define environment variable
ARG REST_INNER_PORT

# Expose the port where the app runs on
EXPOSE ${REST_INNER_PORT}

# Serve the app
CMD ["pm2-runtime", "start", "index.js", "-i", "4", "-n", "MDposit_API", "--node-args=", "\"--experimental-worker\""]