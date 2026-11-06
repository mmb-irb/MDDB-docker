#!/bin/bash

# Ensure required environment variables are set
: "${DB_HOST:?MongoDB host not set}"
: "${MONGO_PORT:?MongoDB port not set}"
: "${MONGO_INITDB_DATABASE:?MongoDB initDB not set}"
: "${BACKUP_DIR:?Backup directory not set}"
: "${MONGO_INITDB_ROOT_USERNAME:?Mongo DB root username not set}"
: "${MONGO_INITDB_ROOT_PASSWORD:?Mongo DB root password not set}"

# Never write into a MongoDB data folder (e.g. DB_BACKUP_VOLUME_PATH = DB_VOLUME_PATH in .env)
for marker in WiredTiger WiredTiger.wt mongod.lock _mdb_catalog.wt; do
    for found in "$BACKUP_DIR/$marker" "$BACKUP_DIR"/*/"$marker"; do
        if [ -e "$found" ]; then
            echo "ERROR: $found exists: the backup folder $BACKUP_DIR is (or contains) a MongoDB data folder." >&2
            echo "Set DB_BACKUP_VOLUME_PATH in .env to a folder separate from DB_VOLUME_PATH. Nothing was written." >&2
            exit 1
        fi
    done
done

# Wait for MongoDB to be ready before starting first dump
until mongosh "mongodb://${MONGO_INITDB_ROOT_USERNAME}:${MONGO_INITDB_ROOT_PASSWORD}@${DB_HOST}:${MONGO_PORT}/${MONGO_INITDB_DATABASE}?authSource=admin" --eval "db.stats()" >/dev/null 2>&1; do 
  echo "Waiting for MongoDB..."
  sleep 2
done

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create timestamp
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"

echo "Starting backup at $(date)"

# Create backup
if ! mongodump --host "$DB_HOST" -u $MONGO_INITDB_ROOT_USERNAME -p $MONGO_INITDB_ROOT_PASSWORD --out "$BACKUP_PATH"; then
    echo "Backup failed!"
    exit 1
fi

echo "Backup completed: $BACKUP_PATH"
