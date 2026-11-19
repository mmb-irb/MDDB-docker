"""Control the mongo-backup service (mongodb/backup_script.sh) of a Docker swarm stack by hand.

    python3 scripts/mongo-backup.py status
    python3 scripts/mongo-backup.py cancel [--restart]
    python3 scripts/mongo-backup.py interval <N>[s|h|d]
    python3 scripts/mongo-backup.py start

Common options: --env FILE (default .env), --stack NAME (default my_stack).
Run it from the MDDB-docker folder, with sudo where docker needs it (e.g. `sudo python3 scripts/...`).

status    Service tasks, complete and incomplete backups, start-now trigger, whether the database is
          write-locked, and when the next backup is due.
cancel    Stops the backup service (0 replicas), so a running dump or packing is interrupted; then makes
          sure the database is not write-locked (db.fsyncUnlock until fsyncLock is false) and removes the
          incomplete backups (*.partial) and the start-now trigger. Complete backups are never touched.
          The service stays stopped: with --restart it goes back to DB_BACKUP_REPLICAS. If a backup is
          due (the cancelled one did not count), it will start again after its check for writes:
          raise the interval first if you do not want that (see the example below).
interval  Sets DB_BACKUP_INTERVAL in the env file and BACKUP_INTERVAL in the service. Changing the service
          restarts its task, which would kill a running backup: refused while one is running (cancel it
          first). The next backup is due <interval> after the start of the last complete backup.
start     Starts a backup now, without waiting for the interval: creates the start-now trigger in the
          backup folder, which the service checks every minute. The check for writes still applies.
          Needs the service task to run the backup_script.sh that knows the trigger (2026-11-19 or later).

Cancel the running backup and leave the next one for two months after the last complete one:
    sudo python3 scripts/mongo-backup.py cancel
    sudo python3 scripts/mongo-backup.py interval 60d     # the service is still at 0 replicas
    sudo python3 scripts/mongo-backup.py cancel --restart # nothing left to clean: just starts it again

Only for Docker swarm stacks (not for Podman nodes).
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time

TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})(/|\.tar|\.tar\.gz)?$")
UNITS = {"s": 1, "h": 3600, "d": 86400}
STOP_TIMEOUT_S = 300


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw).stdout


def env_values(env_file, names):
    """The values of the variables in env_file, read as 'set -a; source .env' (the deploys) reads them."""
    script = 'set -a && source "$0" && set +a && for n in "$@"; do printf "%s\\0" "${!n}"; done'
    out = run(["bash", "-c", script, env_file, *names])
    return dict(zip(names, out.split("\0")))


class Stack:
    def __init__(self, env_file, stack):
        self.env_file = env_file
        self.service = f"{stack}_mongo-backup"
        self.mongo_service = f"{stack}_mongodb"
        v = env_values(env_file, ["DB_BACKUP_VOLUME_PATH", "DB_BACKUP_REPLICAS", "DB_BACKUP_INTERVAL"])
        self.backup_path = v["DB_BACKUP_VOLUME_PATH"]
        if not self.backup_path:
            sys.exit(f"DB_BACKUP_VOLUME_PATH is not set in {env_file}")
        self.env_replicas = v["DB_BACKUP_REPLICAS"]
        self.env_interval = v["DB_BACKUP_INTERVAL"]
        self.spec = json.loads(run(["docker", "service", "inspect", self.service]))[0]["Spec"]

    # --- service ---

    def replicas(self):
        return self.spec["Mode"]["Replicated"]["Replicas"]

    def service_env(self):
        env = self.spec["TaskTemplate"]["ContainerSpec"].get("Env", [])
        return dict(e.split("=", 1) for e in env)

    def image(self):
        return self.spec["TaskTemplate"]["ContainerSpec"]["Image"]

    def running_container(self):
        ids = run(["docker", "ps", "-q", "-f", f"label=com.docker.swarm.service.name={self.service}"]).split()
        return ids[0] if ids else None

    def scale(self, replicas):
        print(f"Scaling {self.service} to {replicas} (waiting for the tasks to converge)...")
        subprocess.run(["docker", "service", "scale", "--detach=false", f"{self.service}={replicas}"],
                       check=True, stdout=subprocess.DEVNULL)

    # --- backup folder (root-owned on most nodes: read and written through the service image) ---

    def in_backup_dir(self, shell_cmd):
        return run(["docker", "run", "--rm", "--entrypoint", "sh", "-v", f"{self.backup_path}:/backup",
                    self.image(), "-c", shell_cmd])

    def backup_entries(self):
        return sorted(self.in_backup_dir("cd /backup && for f in * .[!.]*; do [ -e \"$f\" ] || continue; "
                                         "if [ -d \"$f\" ]; then echo \"$f/\"; else echo \"$f\"; fi; done")
                      .split())

    def complete_backups(self):
        return [e for e in self.backup_entries() if TS_RE.match(e)]

    # --- database lock ---

    def mongosh(self, js):
        ids = run(["docker", "ps", "-q", "-f", f"label=com.docker.swarm.service.name={self.mongo_service}"]).split()
        if len(ids) != 1:
            sys.exit(f"Expected one running {self.mongo_service} container here, found {len(ids)}")
        script = ('mongosh -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" '
                  '--authenticationDatabase admin --quiet --eval "$0"')
        return run(["docker", "exec", ids[0], "sh", "-c", script, js]).strip()

    def write_locked(self):
        out = self.mongosh("print(db.adminCommand({currentOp: 1}).fsyncLock === true)")
        if out not in ("true", "false"):
            sys.exit(f"Could not read the write lock state: {out!r}")
        return out == "true"

    def release_write_lock(self):
        self.mongosh("while (db.adminCommand({currentOp: 1}).fsyncLock === true) { db.fsyncUnlock() }")
        if self.write_locked():
            sys.exit("The database is still write-locked: run db.fsyncUnlock() until fsyncLock is false")


def backup_in_progress(stack, entries):
    return stack.running_container() is not None and any(e.rstrip("/").endswith(".partial") for e in entries)


def parse_interval(text):
    m = re.fullmatch(r"(\d+)([shd]?)", text)
    if not m:
        raise argparse.ArgumentTypeError(f"interval must be a number with an optional s/h/d unit, got {text!r}")
    return int(m.group(1)) * UNITS[m.group(2) or "s"]


def ts_epoch(entry):
    ts = TS_RE.match(entry).group(1)
    return datetime.datetime.strptime(ts, "%Y-%m-%d_%H-%M-%S").replace(tzinfo=datetime.timezone.utc).timestamp()


def fmt_time(epoch):
    return datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def cmd_status(stack, args):
    entries = stack.backup_entries()
    complete = [e for e in entries if TS_RE.match(e)]
    interval = int(stack.service_env()["BACKUP_INTERVAL"])
    print(f"Service {stack.service}: {stack.replicas()} replica(s), container "
          f"{stack.running_container() or 'not running'}, image {stack.image()}")
    print(f"Interval: service {interval} s ({interval / 86400:g} days), {stack.env_file} {stack.env_interval} s")
    print(f"Backup folder {stack.backup_path}:")
    for e in entries:
        print(f"  {e}")
    print(f"Backup in progress: {'yes' if backup_in_progress(stack, entries) else 'no'}")
    print(f"Database write-locked: {'YES' if stack.write_locked() else 'no'}")
    if complete:
        due = ts_epoch(complete[-1]) + interval
        print(f"Last complete backup: {complete[-1]}. Next due: {fmt_time(due)}"
              f"{' (overdue)' if due <= time.time() else ''}")
    else:
        print("No complete backup: the next one starts as soon as the service runs")
    if "start-now" in entries:
        print("start-now trigger present: the backup starts within a minute")


def cmd_cancel(stack, args):
    if stack.replicas() != 0:
        stack.scale(0)
    # The swarm reports the service converged while the container may still be stopping (releasing the lock)
    deadline = time.time() + STOP_TIMEOUT_S
    while stack.running_container():
        if time.time() > deadline:
            sys.exit(f"{stack.service} still has a running container {STOP_TIMEOUT_S} s after scaling to 0")
        time.sleep(5)
    if stack.write_locked():
        print("The database is write-locked: releasing the lock")
        stack.release_write_lock()
    print("Database write-locked: no")
    leftovers = [e for e in stack.backup_entries() if e.rstrip("/").endswith(".partial") or e == "start-now"]
    for e in leftovers:
        print(f"Removing {stack.backup_path}/{e}")
    if leftovers:
        stack.in_backup_dir("cd /backup && rm -rf -- *.partial start-now")
    print(f"Complete backups kept: {', '.join(stack.complete_backups()) or 'none'}")
    if args.restart:
        if not re.fullmatch(r"[1-9]\d*", stack.env_replicas):
            sys.exit(f"DB_BACKUP_REPLICAS in {stack.env_file} is {stack.env_replicas!r}: not restarting")
        stack.scale(int(stack.env_replicas))
    else:
        print(f"{stack.service} left at 0 replicas (--restart, or `docker service scale "
              f"{stack.service}={stack.env_replicas or 1}`, to start it again)")


def cmd_interval(stack, args):
    seconds = args.interval
    if backup_in_progress(stack, stack.backup_entries()):
        sys.exit("A backup is running: changing the service would kill it. Cancel it first (cancel).")
    with open(stack.env_file) as f:
        text = f.read()
    new_text, n = re.subn(r"(?m)^DB_BACKUP_INTERVAL=.*$", f"DB_BACKUP_INTERVAL={seconds}", text)
    if n != 1:
        sys.exit(f"Expected one DB_BACKUP_INTERVAL line in {stack.env_file}, found {n}")
    with open(stack.env_file, "w") as f:  # in place: keeps the owner and permissions of the file
        f.write(new_text)
    print(f"{stack.env_file}: DB_BACKUP_INTERVAL={seconds} ({seconds / 86400:g} days)")
    subprocess.run(["docker", "service", "update", "--detach=false", "--env-add", f"BACKUP_INTERVAL={seconds}",
                    stack.service], check=True, stdout=subprocess.DEVNULL)
    print(f"{stack.service}: BACKUP_INTERVAL={seconds}")
    complete = stack.complete_backups()
    if complete:
        print(f"Next backup due: {fmt_time(ts_epoch(complete[-1]) + seconds)} "
              f"(last complete: {complete[-1]})")


def cmd_start(stack, args):
    container = stack.running_container()
    if not container:
        sys.exit(f"{stack.service} is not running: scale it up first")
    if backup_in_progress(stack, stack.backup_entries()):
        sys.exit("A backup is already running")
    script = run(["docker", "exec", container, "cat", "/backup_script.sh"])
    if "START_NOW" not in script:
        sys.exit(f"The running {stack.service} task has an old backup_script.sh without the start-now trigger: "
                 f"update the repo and recreate the task (docker service update --force {stack.service})")
    stack.in_backup_dir("touch /backup/start-now")
    print(f"Created {stack.backup_path}/start-now: the backup starts within a minute, after the check for writes "
          f"(follow it with: docker service logs -f --tail 20 {stack.service})")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--env", default=".env", help="env file of the stack (default .env)")
    parser.add_argument("--stack", default="my_stack", help="stack name (default my_stack)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    p = sub.add_parser("cancel")
    p.add_argument("--restart", action="store_true", help="scale the service back to DB_BACKUP_REPLICAS")
    p = sub.add_parser("interval")
    p.add_argument("interval", type=parse_interval, help="seconds, or with a unit: 36h, 60d")
    sub.add_parser("start")
    args = parser.parse_args()
    if not os.path.isfile(args.env):
        sys.exit(f"{args.env} not found: run from the MDDB-docker folder or pass --env")
    stack = Stack(args.env, args.stack)
    {"status": cmd_status, "cancel": cmd_cancel, "interval": cmd_interval, "start": cmd_start}[args.command](
        stack, args)


if __name__ == "__main__":
    main()
