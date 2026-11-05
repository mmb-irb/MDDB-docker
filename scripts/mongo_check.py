"""Check, before 'docker stack deploy', that the mongodb image of the compose files can run here.

A deploy that changes the mongodb image can leave the database down:
  * MongoDB upgrades one major version at a time: a binary only starts on data whose
    featureCompatibilityVersion (FCV) is its own version or the previous one (8.0 starts on FCV 7.0
    or 8.0, never on 6.0). See readme/mongo-upgrade.md.
  * Some versions refuse to start on some hosts (e.g. mongo 8.0 up to 8.0.36 and 8.3 on the Ubuntu 26.04
    kernel 7.0.0-NN: "Linux kernel versions 6.19 and newer has a known incompatibility").

So, when the image changes (or the service does not exist yet), this:
  1. reads the version and FCV of the running mongod and the version of the new image, and refuses a
     jump that MongoDB does not allow;
  2. starts the new image for a moment in a throwaway container (no network, empty in-memory data
     directory) to check that it starts on this host at all.
"""

import importlib.util
import os
import re
import subprocess
import sys
import time

_spec = importlib.util.spec_from_file_location(
    "stack_diff", os.path.join(os.path.dirname(os.path.abspath(__file__)), "stack-diff.py"))
stack_diff = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stack_diff)

TEST_TIMEOUT_S = 60


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw).stdout


def major_minor(version):
    m = re.match(r"(\d+)\.(\d+)", version)
    if not m:
        raise ValueError(f"cannot read the MongoDB version {version!r}")
    return int(m.group(1)), int(m.group(2))


def fmt(v):
    return f"{v[0]}.{v[1]}"


def fcv_accepted(binary):
    """The FCVs a binary starts on: its own and the previous release it upgrades from
    (X.0 -> (X-1).0; a rapid release X.Y -> X.0, the LTS it upgrades from)."""
    major, minor = binary
    previous = (major - 1, 0) if minor == 0 else (major, 0)
    return {binary, previous}


def image_version(image):
    """The MONGO_VERSION the official images (and images built from them) set; read from the image
    because some versions do not even run 'mongod --version' on some hosts."""
    if not run(["docker", "image", "ls", "-q", image]).strip():
        print(f"Pulling {image}...")
        run(["docker", "pull", "-q", image])
    env = run(["docker", "image", "inspect", image, "--format", "{{range .Config.Env}}{{println .}}{{end}}"])
    m = re.search(r"^MONGO_VERSION=(\S+)$", env, re.M)
    if not m:
        sys.exit(f"Error: {image} has no MONGO_VERSION variable: not an official mongo image or built from one. "
                 f"Check the version by hand, then use --skip-mongo-check.")
    return m.group(1)


def running_container(service):
    ids = run(["docker", "ps", "-q", "-f", f"label=com.docker.swarm.service.name={service}"]).split()
    return ids[0] if ids else None


def running_version_fcv(container):
    script = ("print(db.version() + ' ' + db.adminCommand({getParameter: 1, featureCompatibilityVersion: 1})"
              ".featureCompatibilityVersion.version)")
    out = run(["docker", "exec", container, "sh", "-c",
               'mongosh --quiet -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" '
               '--authenticationDatabase admin --eval "$0"', script])
    version, fcv = out.split()[-2:]
    return version, fcv


def mongo_images(stack, files, env_file):
    """(wanted, running) image of the mongodb service: wanted is None when the compose files have no
    mongodb service, running is None when the stack has no mongodb service yet."""
    svc = (stack_diff.compose_config(files, env_file, stack).get("services") or {}).get("mongodb")
    if svc is None:
        return None, None
    service = f"{stack}_mongodb"
    running = None
    if service in run(["docker", "service", "ls", "--filter", f"name={service}", "--format", "{{.Name}}"]).split():
        running = stack_diff.norm_image(run(["docker", "service", "inspect", service,
                                             "--format", "{{.Spec.TaskTemplate.ContainerSpec.Image}}"]).strip())
    return stack_diff.norm_image(svc["image"]), running


def test_start(image):
    """Start the image with an empty in-memory /data/db and no network; return (ok, its log)."""
    name = f"mongo-check-{int(time.time())}"
    run(["docker", "run", "-d", "--name", name, "--network", "none", "--tmpfs", "/data/db", image])
    try:
        for _ in range(TEST_TIMEOUT_S):
            time.sleep(1)
            running = run(["docker", "inspect", "-f", "{{.State.Running}}", name]).strip() == "true"
            logs = subprocess.run(["docker", "logs", name], capture_output=True, text=True).stdout
            if not running:
                return False, logs
            if "Waiting for connections" in logs:
                return True, logs
        return False, logs
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)


def check(stack, want_image, running_image):
    """Exit with an explanation if deploying want_image for the mongodb service would leave it down."""
    service = f"{stack}_mongodb"
    if running_image == want_image:
        return
    print(f"== MongoDB check: {running_image or '(no mongodb service yet)'} -> {want_image}\n")

    target = image_version(want_image)
    print(f"New image: MongoDB {target}")

    if running_image is not None:
        container = running_container(service)
        if container is None:
            sys.exit(f"Stopped: {service} has no running container, so its version and featureCompatibilityVersion "
                     f"cannot be checked. Start it with its current image first, or use --skip-mongo-check.")
        version, fcv = running_version_fcv(container)
        print(f"Running:   MongoDB {version}, featureCompatibilityVersion {fcv}")
        accepted = fcv_accepted(major_minor(target))
        if major_minor(fcv) not in accepted:
            sys.exit(f"\nStopped: MongoDB {target} does not start on data with featureCompatibilityVersion {fcv} "
                     f"(it needs {' or '.join(sorted(fmt(v) for v in accepted))}). Upgrade step by step "
                     f"(readme/mongo-upgrade.md), or keep the current image in docker-compose.node.yml:\n\n"
                     f"services:\n  mongodb:\n    image: {running_image}\n")

    print(f"Test start of {want_image} (throwaway container, no network, empty data)...")
    ok, logs = test_start(want_image)
    if not ok:
        fatal = [line for line in logs.splitlines() if '"s":"F"' in line or "cannot start" in line.lower()]
        print("\n".join((fatal or logs.splitlines())[-5:]))
        keep = (f"keep the current image in docker-compose.node.yml:\n\nservices:\n  mongodb:\n    image: {running_image}\n"
                if running_image else "pin an image that works here in docker-compose.node.yml (services: mongodb: image: ...).")
        sys.exit(f"\nStopped: {want_image} does not start on this host (log above). Its data was not touched. "
                 f"Fix the cause, or {keep}")
    print("It starts.\n")
