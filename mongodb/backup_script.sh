#!/bin/bash
# Periodic full MongoDB backup.
#
# Every backup is named after the UTC time its dump started (e.g. 2026-10-21_17-05-31). The
# format depends on COMPRESS:
#   no      <timestamp>/         plain mongodump directory
#   gz      <timestamp>/         `mongodump --gzip` directory (each collection file gzipped)
#   tar     <timestamp>.tar      mongodump directory packed in an uncompressed tar
#   tar.gz  <timestamp>.tar.gz   mongodump directory packed in a gzipped tar
# Restore: `mongorestore --dir <dir>` (add --gzip for gz); extract tar/tar.gz first.
#
# Trade-offs measured on the MDDB production database (~4.9 TiB, almost all of it binary
# trajectories in GridFS fs.chunks):
#   - gzip only saves ~20% of disk, because binary trajectories barely compress.
#   - A plain dump runs at ~100 MB/s (~15 h). gzip is single-threaded and ran at ~10 MB/s in
#     `tar -czf`, so tar.gz took ~4 more days after the dump. With gz the compression happens
#     during the dump, so mongodump keeps reading from the database for days instead.
#   - tar and tar.gz write the full dump first and then pack it, so during the backup the
#     data is on disk twice. tar saves no space; it only produces a single file.
#
# Every backup is written under a ".partial" name and only renamed to its final name once all
# its steps succeed, so a file or directory with a final name is always a complete backup.
# Anything left by an interrupted run (container killed, stack redeployed, error) keeps the
# ".partial" suffix and is removed on next start.
#
# After each successful backup, only the RETENTION_COUNT most recent complete backups (in any
# of the formats above, sorted by timestamp) are kept.
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
: "${COMPRESS:?Backup compression (no/gz/tar/tar.gz) not set}"
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
    no|gz|tar|tar.gz) ;;
    *) echo "COMPRESS must be one of: no, gz, tar, tar.gz. Got '$COMPRESS'" >&2; exit 1 ;;
esac

TS_GLOB='[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]_[0-9][0-9]-[0-9][0-9]-[0-9][0-9]'

# Complete backups in any format, oldest first (timestamp names sort chronologically)
complete_backups() {
    local p
    for p in "$BACKUP_DIR"/$TS_GLOB/ "$BACKUP_DIR"/$TS_GLOB.tar "$BACKUP_DIR"/$TS_GLOB.tar.gz; do
        echo "${p%/}"
    done | sort
}

# Sleep until BACKUP_INTERVAL seconds have passed since the last complete backup started
wait_for_next_backup() {
    local last ts last_epoch remaining
    last=$(complete_backups | tail -n 1)
    if [ -z "$last" ]; then
        echo "No complete backup found"
        return
    fi
    ts=$(basename "$last")
    ts=${ts:0:19}  # e.g. 2026-10-21_17-05-31 (UTC)
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
    echo "Starting backup $TIMESTAMP (compress=$COMPRESS) at $(date)"

    case "$COMPRESS" in
        no|gz)
            DUMP_ARGS=()
            [ "$COMPRESS" = gz ] && DUMP_ARGS=(--gzip)
            mongodump --host "$DB_HOST" -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" "${DUMP_ARGS[@]}" --out "$BACKUP_DIR/$TIMESTAMP.partial"
            mv -- "$BACKUP_DIR/$TIMESTAMP.partial" "$BACKUP_DIR/$TIMESTAMP"
            BACKUP="$BACKUP_DIR/$TIMESTAMP"
            ;;
        tar|tar.gz)
            DUMP_DIR="$BACKUP_DIR/$TIMESTAMP.dump.partial"
            BACKUP="$BACKUP_DIR/$TIMESTAMP.$COMPRESS"
            TAR_ARGS=(-cf)
            [ "$COMPRESS" = tar.gz ] && TAR_ARGS=(-czf)
            mongodump --host "$DB_HOST" -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" --out "$DUMP_DIR"
            echo "Dump finished at $(date), packing into $COMPRESS"
            tar "${TAR_ARGS[@]}" "$BACKUP.partial" -C "$DUMP_DIR" .
            mv -- "$BACKUP.partial" "$BACKUP"
            rm -rf -- "$DUMP_DIR"
            ;;
    esac
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
