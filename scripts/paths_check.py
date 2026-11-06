"""Stop before deploying when the MongoDB backups would be written into the database folder.

The mongo-backup service writes its dumps and logs to DB_BACKUP_VOLUME_PATH and deletes old backups there.
If that folder is DB_VOLUME_PATH (the live mongod data), or one of them is inside the other, the backups
would fill and clutter the database folder. mongodb/backup_script.sh refuses to run in a MongoDB data
folder too, but only sees its own mount: this check also catches the nested cases.

    python3 scripts/paths_check.py [.env]
"""

import os
import subprocess
import sys


def env_values(env_file, names):
    """The values of the variables in env_file, read as 'set -a; source .env' (the deploys) reads them."""
    script = 'set -a && source "$0" && set +a && for n in "$@"; do printf "%s\\0" "${!n}"; done'
    out = subprocess.run(["bash", "-c", script, env_file, *names], check=True, capture_output=True, text=True).stdout
    return dict(zip(names, out.split("\0")))


def inside(path, folder):
    """Whether path is folder or something inside it (after resolving symlinks)."""
    path, folder = os.path.realpath(path), os.path.realpath(folder)
    return path == folder or path.startswith(folder.rstrip("/") + "/")


def check(env_file=".env"):
    v = env_values(env_file, ["DB_VOLUME_PATH", "DB_BACKUP_VOLUME_PATH"])
    db, backup = v["DB_VOLUME_PATH"], v["DB_BACKUP_VOLUME_PATH"]
    if not db or not backup:
        return
    if inside(backup, db) or inside(db, backup):
        sys.exit(f"Error in {env_file}: DB_BACKUP_VOLUME_PATH ({backup}) and DB_VOLUME_PATH ({db}) are the same "
                 "folder or one is inside the other.\nThe backups would be written into the MongoDB data folder. "
                 "Set DB_BACKUP_VOLUME_PATH to a separate folder (e.g. a 'db_backup' folder next to the database "
                 "one) and deploy again.")


if __name__ == "__main__":
    check(sys.argv[1] if len(sys.argv) > 1 else ".env")
    print("OK: DB_BACKUP_VOLUME_PATH and DB_VOLUME_PATH are separate folders")
