# Troubleshooting a new node

Problems seen in real deployments, with how to recognise and fix each one. Fixes marked **upstream**
belong in this repository (or the service's repository) and help every node; do not patch them locally.

## Before deploying

| Symptom | Cause | Fix |
|---|---|---|
| `<stack>_mongodb` restarts in a loop; log: `MongoDB 5.0+ requires a CPU with AVX support`, `Illegal instruction (core dumped)` | The VM's virtual CPU model (e.g. "QEMU Virtual CPU") hides AVX | VM admin: CPU type `host` or `x86-64-v3`, then power off / on. Check: `grep -wo avx /proc/cpuinfo`. Afterwards, remove the core dumps in `/var/lib/systemd/coredump` (sudo). |
| Build steps hang on `git clone` / `curl` to GitHub, though the host has Internet | MTU of the host NIC (e.g. 1450) smaller than Docker's (1500) | `readme/update.md` → Troubleshooting: set `"mtu"` in `/etc/docker/daemon.json` |
| `docker manifest inspect` / pull of the MinIO image fails (`401`, `no such manifest`) | MinIO stopped publishing free images (late 2025) | **upstream**: use a maintained image; the repo now uses `docker.io/pgsty/minio`. Existing nodes keep their local copy |

## During the build

| Symptom | Cause | Fix |
|---|---|---|
| `npm error code EBADENGINE … Required: {"node":">=X"} Actual: {"node":"vY"}` | The service's repository raised its Node requirement and enforces it (`engine-strict=true` in its `.npmrc`); the Dockerfile installs an older Node | **upstream**: bump the Node base image / NodeSource `setup_X.x` in that service's `Dockerfile` (and `Dockerfile.dev`). A warning (`npm warn EBADENGINE`) does not stop the build |
| `Remote branch vX.Y.Z not found` while cloning a release | The release was tagged without the `v` prefix the Dockerfile adds | Service maintainers add the missing tag (`git tag vX.Y.Z X.Y.Z && git push origin vX.Y.Z`); **upstream** could fall back to the tag without `v` |
| `EnvironmentLocationNotFound: Not a conda environment: /opt/conda/envs/mwf_env` | The workflow repo renamed its conda environment | **upstream**: `conda env create -n mwf_env --file=…` (already applied) |
| `apk add` fails once with exit code 50, then works | Transient Alpine mirror error | Retry the build |
| The whole `docker compose build` stops at the first failing service | Normal Compose behaviour: the other services' builds are cancelled, not failed | Fix that one service and rebuild; finished layers are cached |

## After deploying

| Symptom | Cause | Fix |
|---|---|---|
| REST answers `500`; log: `Error: No client`, `ENOTFOUND <stack>_mongodb` | REST connects to Mongo once at start-up and does not retry; it started before Mongo was ready (first deploy, VM reboot) | When Mongo is `1/1`: `docker service update --force <stack>_rest` |
| Mongo will not start after changing its major version (e.g. 6 → 8) on existing data; log `UPGRADE PROBLEM … featureCompatibilityVersion` | Mongo only upgrades one major version at a time, with `featureCompatibilityVersion` set at each step | Follow `readme/mongo-upgrade.md` (skill `mongo-upgrade`). Only if the database is new and empty: stop the stack and empty the `db/` folder so the new version initialises it (`mongo-init.js` recreates the users) |
| VRE lite stays at `503`; log: `Could not resolve host: minio`, "Waiting for minio to be healthy" | MinIO is not running (image missing, storage problem) | Fix MinIO first: `docker service ps <stack>_minio --no-trunc` shows why |
| S3 uploads above 8 MB fail: `InvalidPart … One or more of the specified parts could not be found`; MinIO log `Specified part could not be found … Expected , got` | MinIO's storage does not keep multipart metadata consistent (seen on a virtiofs share; it also returned `Stale file handle`) | Move `MINIO_VOLUME_PATH1` to storage that passes `preflight.sh --multipart-test`: local disk, a virtual disk, or an NFS export mounted directly in the VM |
| MinIO folder and files owned by `nobody` (65534) | The share maps root to `nobody` (root squash) | Expected; fine as long as the multipart test passes |
| `docker compose run --rm loader …` cannot reach Mongo | The one-off container is not on `data_network` | The networks must be created `--attachable` (step 6) |
| Published service ports (8080, 8081, 9001, 9002…) reachable from the internal network despite the firewall | Docker inserts its own firewall rules ahead of firewalld / ufw | Restrict them in the `DOCKER-USER` chain (persisted), or have the network filter them |
