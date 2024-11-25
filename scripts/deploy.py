import argparse
import os
import subprocess
import time


def create_folders():
    # Check if script was executed with sudo
    if 'SUDO_USER' not in os.environ:
        ask_sudo = input("Script was executed without sudo, in some cases you may need sudo permissions for create new folders in the storage system, do you want to continue? (y/n): ")
        if not ask_sudo.lower() == "y":
            return
    # Ask for main path
    main_path = input("Enter the main path for the storage system: ")
    if not main_path:
        print("Error: No path provided.")
        return
    if not os.path.exists(main_path):
        print(f"Error: The path {main_path} does not exist.")
        return

    docker_path = input("Enter the path for the docker directory (default: docker): ") or "docker"
    minio_path = input("Enter the path for the minio directory (default: minio): ") or "minio"
    db_path = input("Enter the path for the MondoDB data directory (default: db): ") or "db"
    data_path = input("Enter the path for the data directory (default: data): ") or "data"
    certs_path = input("Enter the path for the certificates directory (default: certs): ") or "certs"
    logs_path = input("Enter the path for the minio directory (default: logs): ") or "logs"

    # Create necessary folders
    os.makedirs(os.path.join(main_path, docker_path), exist_ok=True)
    os.makedirs(os.path.join(main_path, minio_path), exist_ok=True)
    os.makedirs(os.path.join(main_path, minio_path, "disk1"), exist_ok=True)
    os.makedirs(os.path.join(main_path, minio_path, "disk2"), exist_ok=True)
    os.makedirs(os.path.join(main_path, minio_path, "disk3"), exist_ok=True)
    os.makedirs(os.path.join(main_path, minio_path, "disk4"), exist_ok=True)
    os.makedirs(os.path.join(main_path, db_path), exist_ok=True)
    os.makedirs(os.path.join(main_path, data_path), exist_ok=True)
    os.makedirs(os.path.join(main_path, certs_path), exist_ok=True)
    cert_key = input(f"Enter where the private key is located, it will be copied into {os.path.join(main_path, certs_path)}: ")
    if not os.path.exists(cert_key):
        print(f"Warning! The private key {cert_key} does not exist.")
    else:
        subprocess.run(['cp', cert_key, os.path.join(main_path, certs_path)])
    cert_pem = input(f"Enter where the public certificate is located, it will be copied into {os.path.join(main_path, certs_path)}: ")
    if not os.path.exists(cert_pem):
        print(f"Warning! The public certificate {cert_pem} does not exist.")
    else:
        subprocess.run(['cp', cert_pem, os.path.join(main_path, certs_path)])
    os.makedirs(os.path.join(main_path, logs_path), exist_ok=True)

    print(f"Folders {os.path.join(main_path, docker_path)}, {os.path.join(main_path, minio_path)}, {os.path.join(main_path, db_path)}, {os.path.join(main_path, data_path)}, {os.path.join(main_path, certs_path)} and {os.path.join(main_path, logs_path)} created.")


def install_docker():
    # Install Docker
    print("Installing Docker.")
    subprocess.run(['sudo', 'apt-get', 'update'])
    subprocess.run(['sudo', 'apt-get install', 'apt-transport-https', 'ca-certificates', 'curl', 'software-properties-common'])
    subprocess.run(['curl', '-fsSL', 'https://download.docker.com/linux/ubuntu/gpg', '|', 'sudo', 'gpg', '--dearmor', '-o', '/usr/share/keyrings/docker-archive-keyring.gpg'])
    subprocess.run(['echo', '"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"', '|', 'sudo', 'tee', '/etc/apt/sources.list.d/docker.list', '>', '/dev/null'])
    subprocess.run(['sudo', 'apt-get', 'update'])
    subprocess.run(['sudo', 'apt-get', 'install', 'docker-ce', 'docker-ce-cli', 'containerd.io'])
    print("Docker installed.")

    # Add user to docker group
    print("Add your user to the docker group")
    subprocess.run(['sudo', 'groupadd', 'docker'])
    subprocess.run(['sudo', 'usermod', '-aG', 'docker', '$USER'])
    subprocess.run(['newgrp', 'docker'])
    subprocess.run(['sudo', 'systemctl', 'restart', 'docker'])
    print("User added to docker group.")

    # Install Docker Compose
    print("Installing Docker Compose.")
    subprocess.run(['sudo', 'apt-get', 'update'])
    subprocess.run(['sudo', 'curl', '-L', '"https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)"', '-o', '/usr/local/bin/docker-compose'])
    subprocess.run(['sudo', 'chmod', '+x', '/usr/local/bin/docker-compose'])
    subprocess.run(['sudo', 'ln', '-s', '/usr/local/bin/docker-compose', '/usr/bin/docker-compose'])
    print("Docker Compose installed.")

    print("For changing Docker Root Dir: \n sudo systemctl stop docker \n sudo mv /var/lib/docker /path/to/volume/docker \n sudo ln -s /path/to/volume/docker /var/lib/docker \n sudo systemctl start docker")


def check_env_exists():
    # Check if .env file exists and has all variables filled
    if not os.path.exists('.env'):
        print("Error: .env file does not exist.")
        return False
    return True


def read_env_file(file_path):
    env_vars = {}
    with open(file_path) as f:
        for line in f:
            # Strip whitespace and ignore comments and empty lines
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env_vars[key] = value
    return env_vars


def check_env_paths(paths):
    for path in paths:
        if not os.path.exists(path):
            print(f"Error: {path} does not exist.")
            return False
    return True


def poll_minio(minio_port):
    # Poll until MinIO is up and running
    while True:
        result = subprocess.run(['curl', '-s', f'http://127.0.0.1:{minio_port}/minio/health/live'], capture_output=True)
        if result.returncode == 0:
            print("MinIO is up and running.")
            break
        print("Waiting for MinIO to be up...")
        time.sleep(5)


def deploy_stack(rm):
    ask_env = input("Do you have created the .env file in this same folder? (y/n): ")
    if not ask_env.lower() == "y":
        print("Please create the .env environment file first.")
        return
    if not check_env_exists():
        return
    env_vars = read_env_file('.env')

    # check that .env path variables exist
    paths = [env_vars.get('APACHE_CERTS_VOLUME_PATH'), env_vars.get('LOADER_VOLUME_PATH'), env_vars.get('WORKFLOW_VOLUME_PATH'), env_vars.get('DB_VOLUME_PATH'), env_vars.get('MINIO_VOLUME_PATH1'), env_vars.get('MINIO_VOLUME_PATH2'), env_vars.get('MINIO_VOLUME_PATH3'), env_vars.get('MINIO_VOLUME_PATH4'), env_vars.get('VRE_LITE_VOLUME_PATH')]
    if not check_env_paths(paths):
        return

    # check that there are at least two files in the certs folder
    certs_path = env_vars.get('APACHE_CERTS_VOLUME_PATH')
    cert_files = os.listdir(certs_path)
    if len(cert_files) < 2:
        print(f"Warning: The certificates path {certs_path} does not contain at least two files (private key and public certificate). This can give problems with the https acess to the services.")
        cont = input("Do you want to continue? (y/n): ")
        if not cont.lower() == "y":
            return

    # Remove all cache before deploying the stack
    if rm:
        print("Removing all cache.")
        subprocess.run(['docker', 'system', 'prune', '-f'])
        subprocess.run(['docker', 'builder', 'prune', '-a', '-f'])
        subprocess.run(['docker', 'system', 'prune', '--volumes', '-f'])
        subprocess.run(['docker', 'network', 'prune', '-f'])

    # ask for stack name
    stack_name = input("Enter stack name (default: my_stack): ") or "my_stack"

    # Docker swarm, network create, build and deploy
    subprocess.run(['docker', 'swarm', 'init'])
    subprocess.run(['docker', 'network', 'create', '--driver', 'overlay', 'data_network'])
    subprocess.run(['docker', 'network', 'create', '--driver', 'overlay', 'minio_network'])
    subprocess.run(['docker-compose', 'build'])
    subprocess.run(['export', "$(grep -v '^#' .env | xargs)", '&&', 'docker', 'stack', 'deploy', '-c', 'docker-compose.yml', stack_name])

    # Poll until MinIO is up and running
    poll_minio(env_vars.get('MINIO_API_OUTER_PORT'))

    print(f"Stack {stack_name} deployed.")
    subprocess.run(['docker', 'stack', 'services', stack_name])


def main():
    parser = argparse.ArgumentParser(description='Storage creation, system setup and Docker Swarm deploying for an MDDB node. If no arguments are provided, the script will run all the actions.')
    parser.add_argument('-c', '--create-folders', action='store_true', help='Create storage folders')
    parser.add_argument('-d', '--install-docker', action='store_true', help='Install docker and docker-compose')
    parser.add_argument('-s', '--deploy-swarm', action='store_true', help='Deploy Docker Swarm stack')
    parser.add_argument('-r', '--remove-cache', action='store_true', help='Remove all cache before deploying the stack')

    args = parser.parse_args()

    if not args.create_folders and not args.install_docker and not args.deploy_swarm:
        print('No arguments provided. Please add one of the options to the command line. Use -h for help.')
        return

    if args.create_folders:
        create_folders()

    if args.install_docker:
        install_docker()

    if args.deploy_swarm:
        deploy_stack(args.remove_cache)


if __name__ == '__main__':
    main()
