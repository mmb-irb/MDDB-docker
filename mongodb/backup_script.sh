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
# With tar and tar.gz, the dump directory gets its final name (<timestamp>/) as soon as the dump
# finishes, so it is a usable backup while it is packed. Once the archive is complete, the
# directory is removed. If packing fails or is interrupted, the directory stays as that backup
# and packing is retried on next start; the dump is only removed once its archive is complete.
# Anything left by an interrupted run (container killed, stack redeployed, error) keeps the
# ".partial" suffix and is removed on next start.
#
# After each successful backup, only the RETENTION_COUNT most recent complete backups (in any
# of the formats above, sorted by timestamp) are kept.
#
# Backups are scheduled from the timestamp of the last complete backup, so restarting the
# service does not trigger a new backup unless one is due.
#
# Errors and retries: any error makes the script wait RETRY_DELAY seconds (default 3600) and
# then exit with non-zero status, so the failure shows up in `docker service ps` and the swarm
# restart policy starts it again after that delay: a failed dump is done again from scratch,
# a failed packing is retried on the finished dump.
#
# Safety: the script refuses to run (before writing anything) when BACKUP_DIR, or a folder right inside it,
# is a MongoDB data folder (it has WiredTiger, mongod.lock... files), e.g. when DB_BACKUP_VOLUME_PATH is
# the same as DB_VOLUME_PATH in .env. scripts/paths_check.py also stops the deploy scripts in that case.
#
# Logs: the output of every run of this script is also written to
# $BACKUP_DIR/logs/<start time>.log. If the run fails, its log is renamed to
# <start time>.error.log; error logs are never removed automatically. Of the other logs, only the
# LOG_RETENTION_COUNT (default 20) most recent are kept.
#
# Consistency (LOCK): mongodump on a standalone mongod reads one collection after another, so
# writes made while it runs (e.g. a loader run) can leave the dump inconsistent between
# collections (such as fs.files and fs.chunks). With LOCK=yes the script runs db.fsyncLock()
# before the dump and db.fsyncUnlock() right after it, so the dump is a consistent snapshot:
# reads keep working, but every write waits until the dump finishes (hours on large
# databases). The lock is also released when the script exits or is stopped, and any lock
# left by a killed run is released on next start, so do not fsyncLock this mongod by hand
# while the backup service runs. With LOCK=no writes are not blocked.
#
# Waiting for writes to stop: before every backup, the script counts the operations that write
# to the database (every collection outside admin, config and local, which mongod writes to on
# its own) during WRITE_CHECK_WINDOW seconds (default 300). If there was any, someone is writing
# (e.g. a loader run), so the backup is postponed BUSY_RETRY_DELAY seconds (default 3600) and
# then checked again. This avoids locking writes in the middle of a loader run (LOCK=yes) or
# dumping data that is being changed (LOCK=no). A backup is not postponed for more than
# MAX_POSTPONE seconds (default 172800, 48 h) since the first check: past that, it starts even if
# someone is writing. Restarting the service starts the count again.
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
: "${LOCK:?Backup write lock (yes/no) not set}"
: "${MONGO_INITDB_ROOT_USERNAME:?Mongo DB root username not set}"
: "${MONGO_INITDB_ROOT_PASSWORD:?Mongo DB root password not set}"
RETRY_DELAY=${RETRY_DELAY:-3600}
LOG_RETENTION_COUNT=${LOG_RETENTION_COUNT:-20}
WRITE_CHECK_WINDOW=${WRITE_CHECK_WINDOW:-300}
BUSY_RETRY_DELAY=${BUSY_RETRY_DELAY:-3600}
MAX_POSTPONE=${MAX_POSTPONE:-172800}

if ! [[ "$RETENTION_COUNT" =~ ^[1-9][0-9]*$ ]]; then
    echo "RETENTION_COUNT must be a positive integer, got '$RETENTION_COUNT'" >&2
    exit 1
fi
if ! [[ "$BACKUP_INTERVAL" =~ ^[0-9]+$ ]]; then
    echo "BACKUP_INTERVAL must be a non-negative integer (seconds), got '$BACKUP_INTERVAL'" >&2
    exit 1
fi
if ! [[ "$RETRY_DELAY" =~ ^[0-9]+$ ]]; then
    echo "RETRY_DELAY must be a non-negative integer (seconds), got '$RETRY_DELAY'" >&2
    exit 1
fi
if ! [[ "$WRITE_CHECK_WINDOW" =~ ^[1-9][0-9]*$ ]]; then
    echo "WRITE_CHECK_WINDOW must be a positive integer (seconds), got '$WRITE_CHECK_WINDOW'" >&2
    exit 1
fi
if ! [[ "$BUSY_RETRY_DELAY" =~ ^[1-9][0-9]*$ ]]; then
    echo "BUSY_RETRY_DELAY must be a positive integer (seconds), got '$BUSY_RETRY_DELAY'" >&2
    exit 1
fi
if ! [[ "$MAX_POSTPONE" =~ ^[0-9]+$ ]]; then
    echo "MAX_POSTPONE must be a non-negative integer (seconds), got '$MAX_POSTPONE'" >&2
    exit 1
fi
if ! [[ "$LOG_RETENTION_COUNT" =~ ^[1-9][0-9]*$ ]]; then
    echo "LOG_RETENTION_COUNT must be a positive integer, got '$LOG_RETENTION_COUNT'" >&2
    exit 1
fi
case "$COMPRESS" in
    no|gz|tar|tar.gz) ;;
    *) echo "COMPRESS must be one of: no, gz, tar, tar.gz. Got '$COMPRESS'" >&2; exit 1 ;;
esac
case "$LOCK" in
    yes|no) ;;
    *) echo "LOCK must be yes or no. Got '$LOCK'" >&2; exit 1 ;;
esac

# Never write into a MongoDB data folder (e.g. DB_BACKUP_VOLUME_PATH = DB_VOLUME_PATH in .env): the dumps,
# logs and retention cleanup would share the folder with the live database. Checked before writing anything,
# in BACKUP_DIR and in the folders right inside it (a backup folder that contains the database folder).
# Waits RETRY_DELAY before exiting, like any other error, so swarm does not restart it in a tight loop.
for marker in WiredTiger WiredTiger.wt mongod.lock _mdb_catalog.wt; do
    for found in "$BACKUP_DIR/$marker" "$BACKUP_DIR"/*/"$marker"; do
        if [ -e "$found" ]; then
            echo "ERROR: $found exists: the backup folder $BACKUP_DIR is (or contains) a MongoDB data folder." >&2
            echo "Set DB_BACKUP_VOLUME_PATH in .env to a folder separate from DB_VOLUME_PATH. Nothing was written." >&2
            echo "Exiting in $RETRY_DELAY seconds" >&2
            sleep "$RETRY_DELAY"
            exit 1
        fi
    done
done

TS_GLOB='[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]_[0-9][0-9]-[0-9][0-9]-[0-9][0-9]'

# Log this run to $BACKUP_DIR/logs/<start time>.log as well as to the container log
LOG_DIR="$BACKUP_DIR/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/$(date -u +%Y-%m-%d_%H-%M-%S).log"
exec > >(tee -a "$LOG") 2>&1
echo "Backup service started at $(date) (compress=$COMPRESS, lock=$LOCK, log: $LOG)"

# Keep only the LOG_RETENTION_COUNT most recent logs of runs that did not fail
ok_logs=()
for f in "$LOG_DIR"/$TS_GLOB.log; do
    [ "$f" = "$LOG" ] || ok_logs+=("$f")
done
n_old_logs=$(( ${#ok_logs[@]} - LOG_RETENTION_COUNT ))
for (( i = 0; i < n_old_logs; i++ )); do
    rm -- "${ok_logs[i]}"
done

MONGO_URI="mongodb://${MONGO_INITDB_ROOT_USERNAME}:${MONGO_INITDB_ROOT_PASSWORD}@${DB_HOST}:${MONGO_PORT}/${MONGO_INITDB_DATABASE}?authSource=admin"
mongo_eval() { mongosh "$MONGO_URI" --quiet --eval "$1"; }

# Whether the server is write-locked (note: mongosh's db.currentOp() helper does not return
# the fsyncLock field; the currentOp command does)
is_write_locked() {
    [ "$(mongo_eval 'db.adminCommand({currentOp: 1}).fsyncLock === true')" = true ]
}

# Release every fsyncLock held on the server (fsyncLock nests: each call needs an unlock)
release_write_lock() {
    mongo_eval 'while (db.adminCommand({currentOp: 1}).fsyncLock === true) { db.fsyncUnlock() }' >/dev/null
    if is_write_locked; then
        echo "Could not release the write lock: run db.fsyncUnlock() until it reports lockCount 0" >&2
        exit 1
    fi
    echo "Writes unlocked at $(date)"
}

# Run a command in the background and wait for it, so a SIGTERM (container stop) is handled
# right away instead of after the command finishes, and the EXIT trap releases the lock
run_interruptible() {
    "$@" &
    CHILD=$!
    wait "$CHILD"
    CHILD=
}
CHILD=
trap 'if [ -n "$CHILD" ]; then kill "$CHILD" 2>/dev/null || true; fi; exit 143' TERM INT

# On exit: release the write lock if this run holds it; if the run failed, keep its log as an
# error log and wait RETRY_DELAY seconds, so the swarm restarts the service after that delay
LOCKED=no
on_exit() {
    local status=$?
    if [ "$LOCKED" = yes ]; then
        if ! ( release_write_lock ); then
            status=1
        fi
    fi
    if [ "$status" -eq 0 ] || [ "$status" -eq 143 ]; then
        return
    fi
    local error_log="${LOG%.log}.error.log"
    mv -- "$LOG" "$error_log"
    echo "Backup run FAILED with status $status at $(date). Log kept in $error_log"
    echo "Retrying in $RETRY_DELAY seconds (the service will be restarted)"
    trap 'kill "$CHILD" 2>/dev/null; exit 143' TERM INT
    sleep "$RETRY_DELAY" &
    CHILD=$!
    wait "$CHILD"
    exit "$status"
}
trap on_exit EXIT

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
        run_interruptible sleep "$remaining"
    fi
}

# Number of operations that took a write lock on a user collection since mongod started (the
# `top` command; admin, config and local are left out because mongod writes there on its own)
write_count() {
    local n
    n=$(mongo_eval 'let n = 0;
        for (const [ns, t] of Object.entries(db.adminCommand({top: 1}).totals)) {
            if (ns !== "note" && !/^(admin|config|local)\./.test(ns)) n += Number(t.writeLock.count);
        }
        print(n)')
    if ! [[ "$n" =~ ^[0-9]+$ ]]; then
        echo "Could not count the writes to the database: top returned '$n'" >&2
        exit 1
    fi
    echo "$n"
}

# Wait until nobody writes to the database during WRITE_CHECK_WINDOW seconds, checking again
# every BUSY_RETRY_DELAY seconds, but not for more than MAX_POSTPONE seconds since the first check
wait_until_no_writes() {
    local before after now start deadline delay
    start=$(date -u +%s)
    deadline=$(( start + MAX_POSTPONE ))
    while true; do
        echo "Checking for writes to the database during $WRITE_CHECK_WINDOW seconds ($(date))"
        before=$(write_count)
        run_interruptible sleep "$WRITE_CHECK_WINDOW"
        after=$(write_count)
        if [ "$after" = "$before" ]; then
            echo "No writes to the database: starting the backup"
            return
        fi
        now=$(date -u +%s)
        if (( now >= deadline )); then
            echo "$(( after - before )) write operations in $WRITE_CHECK_WINDOW seconds, but the" \
                "backup has been postponed for $(( now - start )) seconds (MAX_POSTPONE is" \
                "$MAX_POSTPONE): starting the backup while someone is writing"
            return
        fi
        delay=$(( deadline - now < BUSY_RETRY_DELAY ? deadline - now : BUSY_RETRY_DELAY ))
        echo "$(( after - before )) write operations in $WRITE_CHECK_WINDOW seconds: someone is" \
            "writing to the database. Postponing the backup $delay seconds"
        run_interruptible sleep "$delay"
    done
}

# tar/tar.gz: pack a finished dump directory into its archive, then remove the directory.
# The directory is only removed once the archive is complete
pack_dump() {
    local dump_dir=$1
    local archive="$dump_dir.$COMPRESS"
    local tar_args=(-cf)
    [ "$COMPRESS" = tar.gz ] && tar_args=(-czf)
    echo "Packing $dump_dir into $archive at $(date)"
    run_interruptible tar "${tar_args[@]}" "$archive.partial" -C "$dump_dir" .
    mv -- "$archive.partial" "$archive"
    # Rename the dump before removing it, so an interrupted removal leaves a ".partial"
    # (removed on next start) instead of an incomplete directory with a final name
    mv -- "$dump_dir" "$dump_dir.dump.partial"
    rm -rf -- "$dump_dir.dump.partial"
    echo "Packed at $(date): $archive"
}

# Wait for MongoDB to be ready before starting first dump
until mongosh "$MONGO_URI" --eval "db.stats()" >/dev/null 2>&1; do
  echo "Waiting for MongoDB..."
  sleep 2
done

mkdir -p "$BACKUP_DIR"

# A run killed while holding the write lock (e.g. SIGKILL) leaves the database locked
if [ "$LOCK" = yes ] && is_write_locked; then
    echo "Database left write-locked by a previous run: releasing the lock"
    release_write_lock
fi

# Remove leftovers of interrupted runs (only one backup replica writes to BACKUP_DIR)
for leftover in "$BACKUP_DIR"/*.partial; do
    echo "Removing incomplete backup: $leftover"
    rm -rf -- "$leftover"
done

# tar/tar.gz: retry packing the dumps that a previous run finished but did not pack
if [ "$COMPRESS" = tar ] || [ "$COMPRESS" = tar.gz ]; then
    for dump_dir in "$BACKUP_DIR"/$TS_GLOB/; do
        pack_dump "${dump_dir%/}"
    done
fi

# Block writes for the duration of the dump (LOCK=yes); the EXIT trap releases the lock if
# the script stops while holding it
lock_writes() {
    [ "$LOCK" = yes ] || return 0
    LOCKED=yes
    mongo_eval 'db.fsyncLock()' >/dev/null
    if ! is_write_locked; then
        echo "db.fsyncLock() did not lock the server" >&2
        exit 1
    fi
    echo "Writes locked at $(date)"
}
unlock_writes() {
    [ "$LOCK" = yes ] || return 0
    release_write_lock
    LOCKED=no
}

while true; do
    wait_for_next_backup
    wait_until_no_writes

    TIMESTAMP=$(date -u +%Y-%m-%d_%H-%M-%S)
    echo "Starting backup $TIMESTAMP (compress=$COMPRESS) at $(date)"

    case "$COMPRESS" in
        no|gz)
            DUMP_ARGS=()
            [ "$COMPRESS" = gz ] && DUMP_ARGS=(--gzip)
            lock_writes
            run_interruptible mongodump --host "$DB_HOST" -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" "${DUMP_ARGS[@]}" --out "$BACKUP_DIR/$TIMESTAMP.partial"
            unlock_writes
            mv -- "$BACKUP_DIR/$TIMESTAMP.partial" "$BACKUP_DIR/$TIMESTAMP"
            BACKUP="$BACKUP_DIR/$TIMESTAMP"
            ;;
        tar|tar.gz)
            DUMP_DIR="$BACKUP_DIR/$TIMESTAMP"
            lock_writes
            run_interruptible mongodump --host "$DB_HOST" -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" --out "$DUMP_DIR.dump.partial"
            unlock_writes
            # The finished dump is already a complete backup: give it its final name before packing
            # (which can take days), so a failed or interrupted packing does not lose it
            mv -- "$DUMP_DIR.dump.partial" "$DUMP_DIR"
            echo "Dump finished at $(date): $DUMP_DIR"
            pack_dump "$DUMP_DIR"
            BACKUP="$DUMP_DIR.$COMPRESS"
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
