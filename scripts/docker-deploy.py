#!/usr/bin/env python3
"""Create the storage folders and the .env of a new node, then build and deploy the Docker Swarm stack.

    python3 scripts/docker-deploy.py [-r]

Run it from the root of the repository. Without a .env it asks for the main values (storage path,
certificates, node name, domain, users...) and creates the .env from .env.docker.git; review the whole
file afterwards against readme/config.md. With a .env it uses it as it is.

Then it initialises the swarm, creates the networks, builds the images and deploys the stack with
scripts/stack-deploy.py (which checks the paths and the MongoDB image, and adds docker-compose.node.yml).

-r first REMOVES the stack, leaves the swarm and deletes all the Docker cache (images, build cache,
unused volumes and networks). Never use it on a node with services you want to keep.
"""

import argparse
import os
import secrets
import shutil
import subprocess
import sys
import time

TEMPLATE = '.env.docker.git'
ENV = '.env'
NETWORKS = ['data_network', 'minio_network', 'web_network']


def run(cmd, **kwargs):
    """Run a command and stop on any error."""
    print('+ ' + (cmd if isinstance(cmd, str) else ' '.join(cmd)), flush=True)
    return subprocess.run(cmd, check=True, **kwargs)


def read_env_file(file_path):
    env_vars = {}
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env_vars[key] = value
    return env_vars


def write_env_file(template, values, file_path):
    """Write the template with the given values, keeping its comments and order."""
    lines, done = [], set()
    with open(template) as f:
        for line in f:
            key = line.split('=', 1)[0].strip()
            if '=' in line and not line.lstrip().startswith('#') and key in values:
                line = f"{key}={values[key]}\n"
                done.add(key)
            lines.append(line)
    missing = set(values) - done
    if missing:
        raise KeyError(f"{', '.join(sorted(missing))} not found in {template}")
    with open(file_path, 'w') as f:
        f.writelines(lines)
    os.chmod(file_path, 0o600)   # it holds passwords
    owner = os.environ.get('SUDO_USER')
    if owner:
        shutil.chown(file_path, owner, owner)


def ask(label, default=None):
    """Ask for a value; without a default it cannot be empty."""
    prompt = f"{label} (default: {default}): " if default is not None else f"{label}: "
    while True:
        value = input(prompt).strip()
        if value:
            return value
        if default is not None:
            return default
        print("It can't be empty.")


def ask_password(label):
    """Ask for a password; by default, a random one."""
    value = input(f"{label} (press Enter to generate a random one): ").strip()
    return value or secrets.token_urlsafe(18)


def ask_existing_path(label):
    while True:
        path = ask(label)
        if os.path.isdir(path):
            return os.path.abspath(path)
        print(f"{path} is not an existing folder. Create it first, or enter another one.")


def make_dir(path, use_sudo):
    run((['sudo'] if use_sudo else []) + ['mkdir', '-p', path])


def copy_cert(label, certs_path, use_sudo, private=False):
    """Copy a certificate file into certs_path and return its name, or None to skip it."""
    while True:
        src = input(f"{label} (Enter to skip, copy it into {certs_path} later): ").strip()
        if not src:
            print(f"Remember to copy it into {certs_path} and set its name in {ENV} before deploying.")
            return None
        if os.path.isfile(src):
            break
        print(f"{src} does not exist.")
    dst = os.path.join(certs_path, os.path.basename(src))
    prefix = ['sudo'] if use_sudo else []
    run(prefix + ['cp', src, dst])
    if private:
        run(prefix + ['chmod', '600', dst])
    return os.path.basename(src)


def create_env(use_sudo):
    print(f"\n{ENV} does not exist: creating it from {TEMPLATE}.\n")
    v = {}
    main_path = ask_existing_path("Main path for the storage system (the folders of the services are created inside)")
    folders = {
        'MINIO_VOLUME_PATH1': 'minio/disk1',
        'DB_VOLUME_PATH': 'db',
        'DB_BACKUP_VOLUME_PATH': 'db_backup',
        'LOADER_VOLUME_PATH': 'data',
        'WORKFLOW_VOLUME_PATH': 'data',
        'VRE_LITE_VOLUME_PATH': 'logs',
        'APACHE_CERTS_VOLUME_PATH': 'certs',
    }
    for key, folder in folders.items():
        v[key] = os.path.join(main_path, folder)
    for path in sorted(set(v.values())):
        make_dir(path, use_sudo)
    print("Note: the MongoDB backups are in the same storage as the database; better move "
          "DB_BACKUP_VOLUME_PATH to another disk (readme/storage.md).\n")

    cert = copy_cert("TLS certificate file (full chain)", v['APACHE_CERTS_VOLUME_PATH'], use_sudo)
    key = copy_cert("TLS private key file", v['APACHE_CERTS_VOLUME_PATH'], use_sudo, private=True)
    if cert:
        v['SSL_CERTIFICATE'] = cert
    if key:
        v['SSL_CERT_KEY'] = key

    v['NODE'] = ask("Node identifier (e.g. mdposit-xx)")
    domain = ask("Domain name of the node, without https:// (e.g. mdposit.example.org)")
    v['MINIO_URL'] = v['REST_URL'] = domain
    v['MINIO_BROWSER_REDIRECT_URL'] = f"https://{domain}/minio"
    stack = ask("Docker Swarm stack name", "my_stack")
    v['STACK_NAME'] = stack
    v['DB_SERVER'] = v['VRE_LITE_DB_SERVER'] = f"{stack}_mongodb"
    v['DB_NAME'] = v['DB_AUTHSOURCE'] = ask("Database name", "mddb_db")

    print("\nUsers: the passwords are saved in the .env file.")
    v['MONGO_INITDB_ROOT_USERNAME'] = ask("MongoDB root user", "root")
    v['MONGO_INITDB_ROOT_PASSWORD'] = ask_password("MongoDB root password")
    v['LOADER_DB_LOGIN'] = ask("MongoDB read/write user for the loader", "user_rw")
    v['LOADER_DB_PASSWORD'] = ask_password("Its password")
    v['REST_DB_LOGIN'] = ask("MongoDB read-only user for the REST API", "user_r")
    v['REST_DB_PASSWORD'] = ask_password("Its password")
    v['VRE_LITE_DB_LOGIN'] = ask("MongoDB user for VRE lite", "user_vre")
    v['VRE_LITE_DB_PASSWORD'] = ask_password("Its password")
    v['MINIO_ROOT_USER'] = ask("MinIO root user", "admin")
    v['MINIO_ROOT_PASSWORD'] = ask_password("MinIO root password")
    v['MINIO_USER'] = ask("MinIO user for VRE lite and the workflow", "minio_usr")
    v['MINIO_PASSWORD'] = ask_password("Its password")

    v['APACHE_MINIO_OUTER_PORT'] = v['APACHE_MINIO_INNER_PORT'] = ask("Public port of the MinIO API", "9000")
    v['VRE_LITE_TIME_DIFF'] = ask("Days before the VRE lite upload keys expire", "3")
    if input("Do you want periodic backups of the database? (y/n): ").strip().lower() == 'y':
        v['DB_BACKUP_REPLICAS'] = '1'
        v['DB_BACKUP_INTERVAL'] = ask("Seconds between backups", "604800")
    else:
        v['DB_BACKUP_REPLICAS'] = '0'

    write_env_file(TEMPLATE, v, ENV)
    print(f"\n{ENV} created. Review it against readme/config.md (e.g. CERT_DOMAINS, resources, GH_PAT).")
    if input("Continue with the build and the deploy now? (y/n): ").strip().lower() != 'y':
        sys.exit(f"Stopped. Run this script again to build and deploy with {ENV}.")


def remove_everything(stack):
    print(f"Removing the stack {stack}, leaving the swarm and removing all the Docker cache.")
    if input(f"This deletes the services of {stack} and all unused images and volumes. Type the stack name to confirm: ").strip() != stack:
        sys.exit("Not confirmed: nothing removed.")
    stacks = run(['docker', 'stack', 'ls', '--format', '{{.Name}}'], capture_output=True, text=True).stdout.split()
    if stack in stacks:
        run(['docker', 'stack', 'rm', stack])
    run(['docker', 'swarm', 'leave', '--force'])
    run(['docker', 'system', 'prune', '-f'])
    run(['docker', 'builder', 'prune', '-a', '-f'])
    run(['docker', 'system', 'prune', '--volumes', '-f'])
    run(['docker', 'network', 'prune', '-f'])


def swarm_state():
    return run(['docker', 'info', '--format', '{{.Swarm.LocalNodeState}}'], capture_output=True, text=True).stdout.strip()


def network_exists(name):
    names = run(['docker', 'network', 'ls', '--format', '{{.Name}}'], capture_output=True, text=True).stdout.split()
    return name in names


def wait_for_service(stack, service, timeout=600):
    """Wait until the service has all its replicas running; stop if it takes too long."""
    name = f"{stack}_{service}"
    deadline = time.time() + timeout
    while True:
        replicas = run(['docker', 'service', 'ls', '--filter', f'name={name}', '--format', '{{.Name}} {{.Replicas}}'],
                       capture_output=True, text=True).stdout.split('\n')
        state = dict(r.split(' ', 1) for r in replicas if r)
        running = state.get(name, '').split(' ')[0]   # e.g. "1/1" (also "1/1 (max 1 per node)")
        if running and running.split('/')[0] == running.split('/')[1] != '0':
            print(f"{name} is running ({running}).")
            return
        if time.time() > deadline:
            sys.exit(f"{name} is not running after {timeout} s: see 'docker service ps {name} --no-trunc' "
                     f"and 'docker service logs {name}'.")
        print(f"Waiting for {name} ({running or 'not created'})...")
        time.sleep(10)


def deploy_stack(rm):
    if not os.path.isfile('docker-compose.yml'):
        sys.exit("Run this script from the root of the repository (docker-compose.yml not found).")
    for tool in (['docker', 'version'], ['docker', 'compose', 'version']):
        if subprocess.run(tool, capture_output=True).returncode != 0:
            sys.exit(f"'{' '.join(tool)}' does not work: install Docker and the Compose plugin "
                     "(scripts/docker-install.py, readme/setup.md) and check that your user is in the docker group.")

    use_sudo = False
    if not os.path.isfile(ENV):
        if os.geteuid() != 0:
            use_sudo = input("Use sudo to create the storage folders? (y/n): ").strip().lower() == 'y'
        create_env(use_sudo)

    env = read_env_file(ENV)
    stack = env.get('STACK_NAME') or ask("Docker Swarm stack name", "my_stack")

    if rm:
        remove_everything(stack)

    if swarm_state() != 'active':
        try:
            run(['docker', 'swarm', 'init'])
        except subprocess.CalledProcessError as e:
            raise SystemExit("docker swarm init failed. If the VM has several IP addresses, run "
                             "'docker swarm init --advertise-addr <private IP>' and this script again.") from e
    for network in NETWORKS:
        if not network_exists(network):
            run(['docker', 'network', 'create', '--driver', 'overlay', '--attachable', network])

    compose_files = ['docker-compose.yml'] + (['docker-compose.node.yml'] if os.path.isfile('docker-compose.node.yml') else [])
    run(['docker', 'compose'] + [a for f in compose_files for a in ('-f', f)] + ['build'])

    # stack-deploy.py checks the paths and the mongodb image, adds docker-compose.node.yml and deploys
    here = os.path.dirname(os.path.abspath(__file__))
    run([sys.executable, os.path.join(here, 'stack-deploy.py'), '-t', stack, '-c', 'docker-compose.yml'])

    # VRE lite shows the versions of the services, stored in its database
    wait_for_service(stack, 'mongodb')
    run([sys.executable, os.path.join(here, 'update-services-versions.py')])

    print(f"\nStack {stack} deployed.")
    run(['docker', 'stack', 'services', stack])
    print("\nNext: check the node as explained in README.md (step 8, 'Check the node').")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-r', '--remove-cache', action='store_true',
                        help='remove the stack, leave the swarm and remove all the Docker cache before deploying')
    args = parser.parse_args()
    deploy_stack(args.remove_cache)


if __name__ == '__main__':
    main()
