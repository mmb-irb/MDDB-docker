#!/bin/sh

echo "Initializing MinIO client..."
echo "Root user: ${MINIO_ROOT_USER}"
echo "Root password: ${MINIO_ROOT_PASSWORD}"

# Start MinIO server in the background
minio server --address ":${MINIO_API_INNER_PORT}" --console-address ":${MINIO_UI_INNER_PORT}" http://minio/mnt/disk{1...4}

# Wait for MinIO to initialize
sleep 5

# Set up MinIO client alias
mc alias set myminio http://localhost:${MINIO_API_INNER_PORT} ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}

# Create a new user
mc admin user add myminio ${MINIO_USER} ${MINIO_PASSWORD}

# Set policy for the new user
mc admin policy attach myminio readwrite --user ${MINIO_USER}

# Wait for MinIO process to finish
wait