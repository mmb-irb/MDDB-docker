#!/bin/bash
# Periodic full MongoDB backup.
#
# Each backup is a mongodump output directory named after the UTC time the dump started
# (e.g. 2026-10-21_17-05-31/). It is written as <timestamp>.partial/ and only renamed once
# mongodump succeeds, so a directory named <timestamp> is always a complete backup. Anything
# left by an interrupted run (container killed, stack redeployed, error) keeps the ".partial"
# suffix and is removed on next start.
#
# COMPRESS=true runs `mongodump --gzip`, which gzips every collection file on the fly
# (restore with `mongorestore --gzip --dir <backup>`). Note on the trade-off, measured on the
# MDDB production database (~4.9 TiB, almost all of it GridFS fs.chunks): gzip only saves ~20%
# of disk because trajectories are binary data that barely compresses, while compression is
# single-threaded per collection and runs at ~10 MB/s vs ~100 MB/s for a plain dump. A plain
# dump takes ~15 h; a compressed one takes several days, during which mongodump keeps reading
# from the database.
#
# Backups are scheduled from the timestamp of the last complete backup, so restarting the
# service does not trigger a new backup unless one is due.
#
# Any error makes the script exit with non-zero status, so the failure shows up in
# `docker service ps` and the swarm restart policy starts it again.
set -euo pipefail
shopt -s nullglob

# Ensure required environment variables are set
: "${DB_HOST:?MongoDB host not set}"
: "${MONGO_PORT:?MongoDB port not set}"
: "${MONGO_INITDB_DATABASE:?MongoDB initDB not set}"
: "${BACKUP_DIR:?Backup directory not set}"
: "${RETENTION_COUNT:?Retention count not set}"
: "${BACKUP_INTERVAL:?Backup interval not set}"
: "${COMPRESS:?Backup compression (true/false) not set}"
: "${MONGO_INITDB_ROOT_USERNAME:?Mongo DB root username not set}"
: "${MONGO_INITDB_ROOT_PASSWORD:?Mongo DB root password not set}"

if ! [[ "$RETENTION_COUNT" =~ ^[1-9][0-9]*$ ]]; then
    echo "RETENTION_COUNT must be a positive integer, got '$RETENTION_COUNT'" >&2
    exit 1
fi
if ! [[ "$BACKUP_INTERVAL" =~ ^[0-9]+$ ]]; then
    echo "BACKUP_INTERVAL must be a non-negative integer (seconds), got '$BACKUP_INTERVAL'" >&2
    exit 1
fi

case "$COMPRESS" in
    true) DUMP_COMPRESSION_ARGS=(--gzip) ;;
    false) DUMP_COMPRESSION_ARGS=() ;;
    *) echo "COMPRESS must be 'true' or 'false', got '$COMPRESS'" >&2; exit 1 ;;
esac

# Complete backups, oldest first (timestamp names sort chronologically)
complete_backups() {
    local d
    for d in "$BACKUP_DIR"/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]_[0-9][0-9]-[0-9][0-9]-[0-9][0-9]/; do
        echo "${d%/}"
    done
}

# Sleep until BACKUP_INTERVAL seconds have passed since the last complete backup started
wait_for_next_backup() {
    local last ts last_epoch remaining
    last=$(complete_backups | tail -n 1)
    if [ -z "$last" ]; then
        echo "No complete backup found"
        return
    fi
    ts=$(basename "$last")  # e.g. 2026-10-21_17-05-31 (UTC)
    last_epoch=$(date -u -d "${ts:0:10} ${ts:11:2}:${ts:14:2}:${ts:17:2}" +%s)
    remaining=$(( last_epoch + BACKUP_INTERVAL - $(date -u +%s) ))
    if (( remaining > 0 )); then
        echo "Last complete backup: $last. Next backup in $remaining seconds"
        sleep "$remaining"
    fi
}

# Wait for MongoDB to be ready before starting first dump
until mongosh "mongodb://${MONGO_INITDB_ROOT_USERNAME}:${MONGO_INITDB_ROOT_PASSWORD}@${DB_HOST}:${MONGO_PORT}/${MONGO_INITDB_DATABASE}?authSource=admin" --eval "db.stats()" >/dev/null 2>&1; do
  echo "Waiting for MongoDB..."
  sleep 2
done

mkdir -p "$BACKUP_DIR"

# Remove leftovers of interrupted runs (only one backup replica writes to BACKUP_DIR)
for leftover in "$BACKUP_DIR"/*.partial; do
    echo "Removing incomplete backup: $leftover"
    rm -rf -- "$leftover"
done

while true; do
    wait_for_next_backup

    TIMESTAMP=$(date -u +%Y-%m-%d_%H-%M-%S)
    PARTIAL="$BACKUP_DIR/$TIMESTAMP.partial"
    BACKUP="$BACKUP_DIR/$TIMESTAMP"

    echo "Starting backup $TIMESTAMP (compress=$COMPRESS) at $(date)"
    mongodump --host "$DB_HOST" -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" "${DUMP_COMPRESSION_ARGS[@]}" --out "$PARTIAL"
    mv -- "$PARTIAL" "$BACKUP"
    echo "Backup completed at $(date): $BACKUP"

    # Rotational cleanup: keep the RETENTION_COUNT most recent complete backups
    echo "Applying retention policy (keeping $RETENTION_COUNT last backups)"
    mapfile -t backups < <(complete_backups)
    n_old=$(( ${#backups[@]} - RETENTION_COUNT ))
    for (( i = 0; i < n_old; i++ )); do
        echo "Removing old backup: ${backups[i]}"
        rm -rf -- "${backups[i]}"
    done
done
