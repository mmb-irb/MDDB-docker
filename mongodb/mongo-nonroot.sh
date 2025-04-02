#!/bin/bash
set -eo pipefail

# Initialize only if /data/db is empty
if [ -z "$(ls -A /data/db)" ]; then
  echo "Initializing MongoDB..."
  
  # Start MongoDB in background without fork
  mongod --bind_ip 127.0.0.1 --dbpath /data/db &> /tmp/mongod.log &
  MONGO_PID=$!
  
  # Wait for server to be ready
  until mongosh --eval "db.adminCommand('ping')" &>/dev/null; do
    echo "Waiting for MongoDB to start..."
    sleep 1
  done
  
  # Create root user
  if [ -n "$MONGO_INITDB_ROOT_USERNAME" ] && [ -n "$MONGO_INITDB_ROOT_PASSWORD" ]; then
    echo "Creating root user..."
    mongosh admin --eval "
      db.createUser({
        user: '$MONGO_INITDB_ROOT_USERNAME',
        pwd: '$MONGO_INITDB_ROOT_PASSWORD',
        roles: ['root']
      })"
  fi
  
  # Execute initialization scripts
  if [ -d "/docker-entrypoint-initdb.d" ]; then
    for f in /docker-entrypoint-initdb.d/*.js; do
      [ -f "$f" ] && mongosh "$MONGO_INITDB_DATABASE" "$f"
    done
  fi
  
  # Shutdown temporary instance
  kill $MONGO_PID
  wait $MONGO_PID
fi

# Start MongoDB normally
exec mongod --dbpath /data/db --bind_ip_all --port $DB_OUTER_PORT "$@"