#!/bin/sh

# Set up MinIO client alias
mc alias set myminio http://localhost:${MINIO_API_INNER_PORT} ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}

# Create a new user
mc admin user add myminio ${MINIO_USER} ${MINIO_PASSWORD}

# Set policy for the new user
mc admin policy attach myminio readwrite --user ${MINIO_USER}