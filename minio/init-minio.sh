#!/bin/sh

echo "Initializing MinIO client..."

# Start MinIO server in the background
minio server --address ":${MINIO_API_INNER_PORT}" --console-address ":${MINIO_UI_INNER_PORT}" http://minio/mnt/disk{1...4} &

# minio server --address ":${MINIO_API_INNER_PORT}" --console-address ":${MINIO_UI_INNER_PORT}" http://minio{1...3}/mnt/disk{1...4}    # For multiple nodes (ie 3 nodes)

# Health check for the MinIO service
echo "Waiting for MinIO to be healthy..."
while ! curl -f "http://localhost:${MINIO_API_INNER_PORT}/minio/health/live"; do
  echo "MinIO is not healthy yet. Waiting..."
  sleep 5
done
echo "MinIO is healthy."

# Set up MinIO client alias
mc alias set myminio http://localhost:${MINIO_API_INNER_PORT} ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}
echo "MinIO client alias set."

# Create a new user
mc admin user add myminio ${MINIO_USER} ${MINIO_PASSWORD}
echo "New user created."

# Set policy for the new user
mc admin policy attach myminio readwrite --user ${MINIO_USER}
echo "Policy set for the new user."

# Wait for MinIO process to finish
wait