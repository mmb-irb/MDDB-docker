---
name: deploy-node
description: Deploy the MDDB container services (this repo) on a new node, a fresh VM, with Docker Swarm. Use when someone asks to install, set up, deploy or bring up an MDDB / MDposit node, to check whether a VM is ready for it, or to verify a node after deploying. Covers prerequisites, storage, .env, Swarm, build, deploy and verification. Not for Podman (see readme/podman.md) nor for updating an existing node (see readme/update.md).
---

# Deploy a new MDDB node

Deploy this repository's stack on one VM with Docker Swarm, following the upstream procedure
(`README.md`, `readme/setup.md`, `readme/storage.md`, `readme/config.md`, `readme/docker-swarm.md`),
plus the checks that real deployments showed to be necessary.

The VM may be the machine Claude runs on, or a remote one reached through an SSH alias. In the remote case,
run every command below through `ssh <alias> '...'`, and copy the helper scripts first:
`scp .claude/skills/deploy-node/{preflight,verify}.sh <alias>:MDDB-docker/`.

## Ground rules

- **Never modify this repository for one node.** Node-specific values go in `.env` and the client
  configuration in `client/host-config.js` (both git-ignored). If a
  node needs a compose change, put it in an override file outside the repo and add it with `-f` / `-c`.
  A bug that affects every node is fixed upstream, by its maintainers.
- **Secrets**: `.env` holds passwords. Never print it, commit it, or paste its values into the chat.
  Generate passwords with `openssl rand -base64 24 | tr -d '/+='`.
- **sudo**: assume Claude has none. List the exact sudo commands for the user to run and wait for them.
- **Ask before anything destructive or shared**: `docker swarm leave`, `docker-deploy.py -r`, deleting data
  folders, opening firewall ports, starting the stack. Deploy only when the user says so.
- **Long builds**: run them detached on the VM (`setsid nohup … > ~/deploy.log 2>&1 &`) and poll the log,
  so a dropped SSH connection does not kill them.

## 1. Gather the facts (ask the user)

| Question | Why |
|---|---|
| Where does it run: this machine, or an SSH alias? | Every command depends on it |
| Public domain name(s) of the node (e.g. `mdposit-xx.mddbr.eu`) | `MINIO_URL`, `REST_URL`, certificate, DNS |
| Storage path(s) for data and for MinIO | `*_VOLUME_PATH` variables, capacity check |
| Is MongoDB in the stack (default) or an external server? | `DB_SERVER`, users, backups |
| Extensions: `mcp`, `metrics`, `grafana`? | Extra `-f` / `-c` files |
| Where are the TLS certificate (full chain) and key? | `certs/` folder |
| Which MinIO API port is opened publicly (default 9000)? | `APACHE_MINIO_OUTER_PORT` |
| Who runs sudo commands? | Step 2 hand-offs |

## 2. Pre-flight check of the VM

From the repo root on the VM:

```bash
bash .claude/skills/deploy-node/preflight.sh --storage <minio storage path> --domain <domain> --multipart-test
```

It is read-only except for `--multipart-test`, which starts a throwaway MinIO on a temporary folder in the
storage path, uploads a 100 MB file in parts, and deletes everything. Every `FAIL` must be fixed before
deploying; explain each `WARN` to the user. The most important checks, all learned the hard way:

- **CPU AVX** (MongoDB 5+ crashes with `Illegal instruction` without it). Fix: the VM admin sets the CPU type
  to `host` / `x86-64-v3` and power-cycles the VM.
- **MinIO storage can hold multipart uploads.** Some shared folders (seen with a virtiofs share) accept small
  files but fail every upload above 8 MB with `InvalidPart`. A directly mounted NFS export or a local disk
  works. Never point MinIO at storage that fails this test.
- **Images can be pulled** (`mongo`, MinIO). Third-party images do disappear.
- **Outbound access** to GitHub, Docker Hub, PyPI and NodeSource (builds clone and download), and the MTU
  of the host vs Docker bridge (`readme/update.md` → Troubleshooting).
- Docker, Compose, docker-group membership, free space where Docker keeps images, time sync, ports.

## 3. Install Docker (only if missing)

`python3 scripts/docker-install.py [--root-dir <storage>]` (needs sudo; Ubuntu, Debian, RHEL family, Fedora) or the distribution's official Docker packages with the Compose plugin (`readme/setup.md`). The user must be in the `docker` group. Docker keeps images in **both**
`/var/lib/docker` and `/var/lib/containerd`; the builds need tens of GB there.

## 4. Storage and certificates

Create, under the storage path, the folders the `.env` will point to (`readme/storage.md`):
`certs/ data/ db/ db_backup/ logs/ minio/disk1/`. Usually needs sudo to create the parent and
`chown` it to the deploying user, after which the user can create the rest.

Copy the certificate chain and key into `certs/` (`chmod 600` the key) and check it covers the domain:

```bash
openssl x509 -in certs/<chain>.pem -noout -subject -enddate -ext subjectAltName
```

Note the expiry date for the user.

## 5. Configure `.env`

Start from `.env.docker.git` (copy to `.env`), or let `sudo python3 scripts/docker-deploy.py` ask for
the main values interactively; either way, review every variable against `readme/config.md`. Rules that
are easy to get wrong:

- `NODE`: the node identifier. `STACK_NAME`: the Swarm stack name; service names become `<stack>_<service>`.
- `MINIO_URL` and `REST_URL`: the **bare host name** (`mdposit-xx.mddbr.eu`, no `https://`).
- `APACHE_HTTPS_INNER_PORT` = `APACHE_HTTPS_OUTER_PORT` and `APACHE_MINIO_INNER_PORT` =
  `APACHE_MINIO_OUTER_PORT`: Apache listens on the outer number inside its container.
- `SSL_CERTIFICATE` / `SSL_CERT_KEY` (not `SSL_CERTIFICATE_KEY`): file names inside the certs folder.
- `DB_SERVER`: `<stack>_mongodb` for the in-stack Mongo, or the external server's address.
  `VRE_LITE_DB_SERVER`: always `<stack>_mongodb`.
- `*_VOLUME_PATH*`: the folders from step 4. `MINIO_VOLUME_PATH1` must have passed the multipart test.
- Every password: generated, different from the others, never a template default.

Client configuration: create `client/host-config.js` from one of the client examples
(`example-single-host-config.js` or `example-multiple-host-config.js` in MDposit-client) with the name, logo
label, colors, contacts and footers of this node, and put its own images in `client/images/`; see
`client/README.md`. Without it the client uses its generic default configuration (MDposit look, API in the
same domain). It needs MDposit-client v0.0.22 or newer.

Then validate without starting anything:

```bash
docker compose -f docker-compose.yml [-f extensions/<ext>.yml ...] config -q && echo OK
```

## 6. Swarm and networks

```bash
docker swarm init --advertise-addr <the VM's private IP>    # skip if already active
for n in web_network data_network minio_network metrics_network; do
  docker network create --driver overlay --attachable "$n"
done
```

## 7. Build and deploy (after the user's go-ahead)

```bash
docker compose -f docker-compose.yml [-f extensions/<ext>.yml ...] build
set -a; source .env; set +a
docker stack deploy -c docker-compose.yml [-c extensions/<ext>.yml ...] "$STACK_NAME"
```

The compose file names given to `build` and `deploy` must match. `docker stack deploy` ignores `build`,
`devices` and `security_opt`: the warnings about them are expected. If a build fails, read the first
`ERROR` in the log and look it up in [troubleshooting.md](troubleshooting.md) before retrying.

## 8. Verify

```bash
bash .claude/skills/deploy-node/verify.sh --stack "$STACK_NAME" --domain <domain> --env .env
```

It checks replicas, failing tasks, Mongo users and MinIO initialisation, the HTTPS endpoints through Apache
on the VM itself (`/`, REST, VRE lite, MinIO), the certificate actually served, and that the REST API is
connected to its database. Then:

```bash
docker compose run --rm loader list          # loader reaches the database
python3 scripts/update-services-versions.py  # fills the versions shown in VRE lite
```

Finally, from outside the VM: open `https://<domain>/` in a browser, and test an S3 upload of a file larger
than 8 MB (multipart) against `https://<domain>:<minio port>`.

## 9. Report to the user

State what is running, the endpoint results, the certificate expiry, anything skipped or left to them
(DNS, firewall, backups, sudo clean-ups), and every workaround applied with the reason.
