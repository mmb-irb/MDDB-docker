import argparse
import os
import subprocess
import time


def get_os_info():
    os_info = {}
    with open('/etc/os-release') as f:
        for line in f:
            key, value = line.strip().split('=', 1)
            os_info[key] = value.strip('"')
    return os_info


def install_docker_ubuntu():
    # Install Docker
    print("Installing Docker.")
    subprocess.run(['sudo', 'apt-get', 'update'])
    subprocess.run(['sudo', 'apt-get install', 'apt-transport-https', 'ca-certificates', 'curl', 'software-properties-common', '-y'])
    subprocess.run(['curl', '-fsSL', 'https://download.docker.com/linux/ubuntu/gpg', '|', 'sudo', 'gpg', '--dearmor', '-o', '/usr/share/keyrings/docker-archive-keyring.gpg'])
    subprocess.run(['echo', '"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"', '|', 'sudo', 'tee', '/etc/apt/sources.list.d/docker.list', '>', '/dev/null'])
    subprocess.run(['sudo', 'apt-get', 'update'])
    subprocess.run(['sudo', 'apt-get', 'install', 'docker-ce', 'docker-ce-cli', 'containerd.io', '-y'])
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

    # Ask for main path
    main_path = input("Enter the main path for the storage system. This script will create a /docker folder where all the docker images will be stored: ")
    if not main_path:
        print("Error: No path provided.")
        return
    if not os.path.exists(main_path):
        print(f"Error: The path {main_path} does not exist.")
        return

    docker_path = os.path.join(main_path, 'docker')
    subprocess.run(['sudo', 'mkdir', docker_path])

    print("Changing Docker Root Dir.")
    subprocess.run(['sudo', 'systemctl', 'stop', 'docker'])
    subprocess.run(['sudo', 'mv', '/var/lib/docker', docker_path])
    subprocess.run(['sudo', 'ln', '-s', docker_path, '/var/lib/docker'])
    subprocess.run(['sudo', 'systemctl', 'start', 'docker'])
    subprocess.run(['sudo', 'docker', 'info', '|', 'grep', '"Docker Root Dir"'])


def install_docker_rocky():
    # Install Docker
    print("Installing Docker.")
    subprocess.run(['sudo', 'dnf', 'check-update'])
    subprocess.run(['sudo', 'dnf', 'config-manager', '--add-repo', 'https://download.docker.com/linux/centos/docker-ce.repo'])
    subprocess.run(['sudo', 'dnf', 'install', 'docker-ce', 'docker-ce-cli', 'containerd.io', 'docker-compose-plugin', '-y'])
    subprocess.run(['sudo', 'systemctl', 'start', 'docker'])
    subprocess.run(['sudo', 'systemctl', 'enable', 'docker'])
    print("Docker installed.")

    # Add user to docker group
    print("Add your user to the docker group")
    subprocess.run(['sudo', 'groupadd', 'docker'])
    subprocess.run(['sudo', 'usermod', '-aG', 'docker', '$USER'])
    subprocess.run(['newgrp', 'docker'])
    subprocess.run(['sudo', 'systemctl', 'restart', 'docker'])
    print("User added to docker group.")

    # Ask for main path
    main_path = input("Enter the main path for the storage system. This script will create a /docker folder where all the docker images will be stored: ")
    if not main_path:
        print("Error: No path provided.")
        return
    if not os.path.exists(main_path):
        print(f"Error: The path {main_path} does not exist.")
        return

    docker_path = os.path.join(main_path, 'docker')
    subprocess.run(['sudo', 'mkdir', docker_path])

    print("Changing Docker Root Dir.")
    subprocess.run(['sudo', 'systemctl', 'stop', 'docker'])
    subprocess.run(['sudo', 'mv', '/var/lib/docker', docker_path])
    subprocess.run(['sudo', 'ln', '-s', docker_path, '/var/lib/docker'])
    subprocess.run(['sudo', 'systemctl', 'start', 'docker'])
    subprocess.run(['sudo', 'docker', 'info', '|', 'grep', '"Docker Root Dir"'])


def install_docker():
    os_info = get_os_info()
    os_name = os_info.get('NAME', '')

    if 'Ubuntu' in os_name:
        print("Running on Ubuntu")
        install_docker_ubuntu()
    elif 'Rocky' in os_name:
        print("Running on Rocky Linux")
        install_docker_rocky()
    else:
        print(f"Running on an unsupported OS: {os_name}")
        return


def check_file_exists(fname, warning=False):
    # Check if .env file exists and has all variables filled
    if not os.path.exists(fname):
        if warning:
            print(f"Error: {fname} file does not exist.")
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


def check_path(path):
    if not os.path.exists(path):
        print(f"Error: {path} does not exist.")
        return False
    return True


def set_main_path():
    while True:
        main_path = input("Enter the main path for the storage system. This script will create all the necessary folders for the services in this path: ")
        if main_path.strip():  # Check if the input is not empty or just whitespace
            if not os.path.exists(main_path):
                print(f"Error: The path {main_path} does not exist.")
                return False
            return main_path
        print("The main path cannot be empty. Please enter a valid value.")


def save_env_vars_to_file(env_vars, file_path):
    with open(file_path, 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    # Give 666 permissions to the .env file
    if 'SUDO_USER' in os.environ:
        subprocess.run(['sudo', 'chmod', '664', file_path])


def poll_minio(minio_port):
    # Poll until MinIO is up and running
    while True:
        result = subprocess.run(['curl', '-s', f'http://127.0.0.1:{minio_port}/minio/health/live'], capture_output=True)
        if result.returncode == 0:
            print("MinIO is up and running.")
            break
        print("Waiting for MinIO to be up...")
        time.sleep(5)


def get_mandatory_var(label):
    while True:
        var_name = input(f"Enter {label} name: ")
        if var_name.strip():  # Check if the input is not empty or just whitespace
            return var_name
        print(f"Please enter a valid {label} name, it can't be empty.")


def is_node_in_swarm():
    try:
        # Run `docker info` command
        result = subprocess.run(
            ["docker", "info", "--format", "{{.Swarm.LocalNodeState}}"],
            capture_output=True,
            text=True,
            check=True
        )
        # The output will be "active", "inactive", or "pending"
        node_state = result.stdout.strip()
        if node_state == "active":
            print("The node is already part of a Swarm.")
            return True
        elif node_state == "inactive":
            print("The node is not part of any Swarm.")
            return False
        else:
            print(f"The node is in a pending state: {node_state}.")
            return False
    except subprocess.CalledProcessError as e:
        print("Error running docker command:", e)
        return False


def check_network_exists(network_name):
    try:
        result = subprocess.run(
            ["docker", "network", "ls", "--filter", f"name={network_name}", "--format", "{{.Name}}"],
            capture_output=True, text=True, check=True
        )
        return network_name in result.stdout.strip()
    except subprocess.CalledProcessError:
        return False


def create_directory(minio_path, use_sudo):
    if use_sudo:
        subprocess.run(['sudo', 'mkdir', '-p', minio_path], check=True)
    else:
        subprocess.run(['mkdir', '-p', minio_path], check=True)


def deploy_stack(rm):
    # Check if script was executed with sudo
    if 'SUDO_USER' not in os.environ:
        sudo = True
        ask_sudo = input("The script was executed without sudo, in some cases you may need sudo permissions for create new folders in the storage system, do you want to continue? (y/n): ")
        if not ask_sudo.lower() == "y":
            print("Please run the script with sudo: sudo python3 scripts/docker-deploy.py -s")
            return
        else:
            print("Continuing without sudo permissions.")
            sudo = False

    if not check_file_exists('docker-compose.yml', warning=True):
        return

    if not check_file_exists('.env'):
        print("The file .env does not exist, creating it.")
        env_vars = read_env_file('.env.docker.git')
        main_path = set_main_path()
        if not main_path:
            return

        minio_path = os.path.join(main_path, 'minio')
        create_directory(minio_path, sudo)
        create_directory(os.path.join(minio_path, 'disk1'), sudo)
        create_directory(os.path.join(minio_path, 'disk2'), sudo)
        create_directory(os.path.join(minio_path, 'disk3'), sudo)
        create_directory(os.path.join(minio_path, 'disk4'), sudo)
        print(f"Created MinIO volumes: {minio_path}/disk1, {minio_path}/disk2, {minio_path}/disk3, {minio_path}/disk4.")
        env_vars["MINIO_VOLUME_PATH1"] = os.path.join(minio_path, 'disk1')
        env_vars["MINIO_VOLUME_PATH2"] = os.path.join(minio_path, 'disk2')
        env_vars["MINIO_VOLUME_PATH3"] = os.path.join(minio_path, 'disk3')
        env_vars["MINIO_VOLUME_PATH4"] = os.path.join(minio_path, 'disk4')

        db_path = os.path.join(main_path, 'db')
        create_directory(db_path, sudo)
        print(f"Created MongoDB volume: {db_path}.")
        env_vars["DB_VOLUME_PATH"] = db_path

        data_path = os.path.join(main_path, 'data')
        create_directory(data_path, sudo)
        print(f"Created data volume: {data_path}.")
        env_vars["LOADER_VOLUME_PATH"] = data_path
        env_vars["WORKFLOW_VOLUME_PATH"] = data_path

        logs_path = os.path.join(main_path, 'logs')
        create_directory(logs_path, sudo)
        print(f"Created logs volume: {logs_path}.")
        env_vars["VRE_LITE_VOLUME_PATH"] = logs_path

        certs_path = os.path.join(main_path, 'certs')
        create_directory(certs_path, sudo)
        print(f"Created certificates volume: {certs_path}.")
        env_vars["APACHE_CERTS_VOLUME_PATH"] = certs_path

        # Copy the certificates
        cert_pem = input(f"Enter where the SSL certificate file is located, it will be copied into {certs_path}: ")
        if not os.path.exists(cert_pem):
            print(f"Warning! The public certificate {cert_pem} does not exist.")
            cont = input("Do you want to continue? (y/n): ")
            if not cont.lower() == "y":
                return
        else:
            subprocess.run(['cp', cert_pem, certs_path])
            env_vars["SSL_CERTIFICATE"] = os.path.basename(cert_pem)
            print(f"{cert_pem} copied into {certs_path}.")
        cert_key = input(f"Enter where the private SSL certificate key file is located, it will be copied into {certs_path}: ")
        if not os.path.exists(cert_key):
            print(f"Warning! The private key {cert_key} does not exist.")
            cont = input("Do you want to continue? (y/n): ")
            if not cont.lower() == "y":
                return
        else:
            subprocess.run(['cp', cert_key, certs_path])
            env_vars["SSL_CERT_KEY"] = os.path.basename(cert_key)
            print(f"{cert_key} copied into {certs_path}.")

        env_vars["NODE"] = get_mandatory_var("node")
        stack_name = input("Enter stack name (default: my_stack): ") or "my_stack"
        env_vars["DB_SERVER"] = f"{stack_name}_mongodb"
        db_name = input("Enter the database name (default: mddb_db): ") or "mddb_db"
        env_vars["DB_NAME"] = db_name
        env_vars["DB_AUTHSOURCE"] = db_name
        env_vars["MONGO_INITDB_ROOT_USERNAME"] = input("Enter the root database user (default: root): ") or "root"
        env_vars["MONGO_INITDB_ROOT_PASSWORD"] = input("Enter the root database password (default: root): ") or "root"
        env_vars["LOADER_DB_LOGIN"] = input("Enter the R/W database user for the loader service (default: user_rw): ") or "user_rw"
        env_vars["LOADER_DB_PASSWORD"] = input("Enter the R/W database password for the loader service (default: pwd_rw): ") or "pwd_rw"
        env_vars["REST_DB_LOGIN"] = input("Enter the R database user for the REST API service (default: user_r): ") or "user_r"
        env_vars["REST_DB_PASSWORD"] = input("Enter the R database password for the REST API service (default: pwd_r): ") or "pwd_r"
        env_vars["MINIO_ROOT_USER"] = input("Enter the MinIO root user (default: admin): ") or "admin"
        env_vars["MINIO_ROOT_PASSWORD"] = input("Enter the MinIO root password (default: secretpassword): ") or "secretpassword"
        env_vars["MINIO_USER"] = input("Enter the MinIO user (default: minio_usr): ") or "minio_usr"
        env_vars["MINIO_PASSWORD"] = input("Enter the MinIO password (default: minio_pwd): ") or "minio_pwd"
        env_vars["APACHE_MINIO_OUTER_PORT"] = input("Enter the API MinIO port (default: 9000): ") or "9000"
        env_vars["APACHE_MINIO_INNER_PORT"] = env_vars["APACHE_MINIO_OUTER_PORT"]
        env_vars["MINIO_URL"] = f"{env_vars['NODE']}.mddbr.eu"
        env_vars["MINIO_BROWSER_REDIRECT_URL"] = f"https://{env_vars['NODE']}.mddbr.eu/minio"

        print("Creating .env file.")
        save_env_vars_to_file(env_vars, '.env')

    # Remove all cache before deploying the stack
    if rm:
        print("Removing all cache.")
        stack_name = get_mandatory_var("stack")
        # Check if the stack name exists
        result = subprocess.run(["docker", "stack", "ls"], capture_output=True, text=True, check=True)
        if stack_name not in result.stdout:
            print(f"Stack '{stack_name}' does not exist in this node.")
            return
        print(f"Removing {stack_name} stack and leaving swarm.")
        subprocess.run(['docker', 'stack', 'rm', stack_name])
        subprocess.run(['docker', 'swarm', 'leave', '--force'])
        print("Removing all cache.")
        subprocess.run(['docker', 'system', 'prune', '-f'])
        subprocess.run(['docker', 'builder', 'prune', '-a', '-f'])
        subprocess.run(['docker', 'system', 'prune', '--volumes', '-f'])
        subprocess.run(['docker', 'network', 'prune', '-f'])

    # ask for stack name if not provided
    if 'stack_name' not in locals():
        stack_name = input("Enter stack name (default: my_stack): ") or "my_stack"

    # Docker swarm, network create, build and deploy
    if not is_node_in_swarm():
        subprocess.run(['docker', 'swarm', 'init'])
    if not check_network_exists('data_network'):
        print("Creating data network.")
        subprocess.run("docker network create --driver overlay --attachable data_network", shell=True, check=True)
    if not check_network_exists('minio_network'):
        print("Creating MinIO network.")
        subprocess.run("docker network create --driver overlay --attachable minio_network", shell=True, check=True)
    if not check_network_exists('web_network'):
        print("Creating web network.")
        subprocess.run("docker network create --driver overlay --attachable web_network", shell=True, check=True)
    subprocess.run(['docker-compose', 'build'])
    subprocess.run(f"export $(grep -v '^#' .env | xargs) && docker stack deploy -c docker-compose.yml {stack_name}", shell=True, check=True, executable='/bin/bash')

    # Poll until MinIO is up and running
    if 'env_vars' not in locals():
        env_vars = read_env_file('.env')
    poll_minio(env_vars.get('MINIO_API_OUTER_PORT'))

    print(f"Stack {stack_name} deployed.")
    subprocess.run(['docker', 'stack', 'services', stack_name])


def main():
    parser = argparse.ArgumentParser(description='Storage creation, system setup and Docker Swarm deploying for an MDDB node.')
    parser.add_argument('-d', '--install-docker', action='store_true', help='Install docker and docker-compose. Sudo permissions are required.')
    parser.add_argument('-s', '--deploy-swarm', action='store_true', help='Deploy Docker Swarm stack. Sudo permissions may be required.')
    parser.add_argument('-r', '--remove-cache', action='store_true', help='Leave the swarm and remove all cache before deploying the stack (only when -s selected as well)')

    args = parser.parse_args()

    if not args.install_docker and not args.deploy_swarm:
        print('No arguments provided. Please add one of the options to the command line. Use -h for help.')
        return

    if args.install_docker:
        install_docker()

    if args.deploy_swarm:
        deploy_stack(args.remove_cache)


if __name__ == '__main__':
    main()
