import argparse
import os
import subprocess
import time


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


def check_network_exists(network_name):
    try:
        result = subprocess.run(
            ["podman", "network", "ls", "--filter", f"name={network_name}", "--format", "{{.Name}}"],
            capture_output=True, text=True, check=True
        )
        return network_name in result.stdout.strip()
    except subprocess.CalledProcessError:
        return False


def deploy_stack(rm):

    # Check if the .env file exists
    if not check_file_exists('.env'):
        print("The file .env does not exist, creating it.")
        env_vars = read_env_file('.env.podman.git')
        main_path = set_main_path()
        if not main_path:
            return

        minio_path = os.path.join(main_path, 'minio')
        subprocess.run(['mkdir', minio_path])
        subprocess.run(['mkdir', os.path.join(minio_path, 'disk1')])
        subprocess.run(['mkdir', os.path.join(minio_path, 'disk2')])
        subprocess.run(['mkdir', os.path.join(minio_path, 'disk3')])
        subprocess.run(['mkdir', os.path.join(minio_path, 'disk4')])
        print(f"Created MinIO volumes: {minio_path}/disk1, {minio_path}/disk2, {minio_path}/disk3, {minio_path}/disk4.")
        env_vars["MINIO_VOLUME_PATH1"] = os.path.join(minio_path, 'disk1')
        env_vars["MINIO_VOLUME_PATH2"] = os.path.join(minio_path, 'disk2')
        env_vars["MINIO_VOLUME_PATH3"] = os.path.join(minio_path, 'disk3')
        env_vars["MINIO_VOLUME_PATH4"] = os.path.join(minio_path, 'disk4')

        db_path = os.path.join(main_path, 'db')
        subprocess.run(['mkdir', db_path])
        print(f"Created MongoDB volume: {db_path}.")
        env_vars["DB_VOLUME_PATH"] = db_path

        data_path = os.path.join(main_path, 'data')
        subprocess.run(['mkdir', data_path])
        print(f"Created data volume: {data_path}.")
        env_vars["LOADER_VOLUME_PATH"] = data_path
        env_vars["WORKFLOW_VOLUME_PATH"] = data_path

        logs_path = os.path.join(main_path, 'logs')
        subprocess.run(['mkdir', logs_path])
        print(f"Created logs volume: {logs_path}.")
        env_vars["VRE_LITE_VOLUME_PATH"] = logs_path

        certs_path = os.path.join(main_path, 'certs')
        subprocess.run(['mkdir', certs_path])
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
        env_vars["DB_SERVER"] = "mongodb"
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
        env_vars["VRE_LITE_TIME_DIFF"] = input("Enter the expiration date in days for the Access Keys (default: 3): ") or "3"
        env_vars["APACHE_MINIO_INNER_PORT"] = env_vars["APACHE_MINIO_OUTER_PORT"]
        env_vars["MINIO_URL"] = f"{env_vars['NODE']}.mddbr.eu"
        env_vars["MINIO_BROWSER_REDIRECT_URL"] = f"https://{env_vars['NODE']}.mddbr.eu/minio"

        print("Creating .env file.")
        save_env_vars_to_file(env_vars, '.env')

    # Remove all cache before deploying the stack
    if rm:
        print("Stopping and removing all containers.")
        subprocess.run("podman stop $(podman ps -aq)", shell=True, check=True)
        subprocess.run("podman rm  -f $(podman ps -aq)", shell=True, check=True)
        print("Removing all images.")
        subprocess.run("podman rmi -f $(podman images -q)", shell=True, check=True)
        print("Removing all cache.")
        subprocess.run("podman system prune -a -f", shell=True, check=True)
        subprocess.run("podman system prune --volumes -f", shell=True, check=True)

    # Load variables from .env file
    subprocess.run("export $(grep -v '^#' .env | xargs)", shell=True, check=True, executable='/bin/bash')

    # Network create
    if not check_network_exists('data_network'):
        print("Creating data network.")
        subprocess.run("podman network create data_network", shell=True, check=True)
    if not check_network_exists('minio_network'):
        print("Creating MinIO network.")
        subprocess.run("podman network create minio_network", shell=True, check=True)
    if not check_network_exists('web_network'):
        print("Creating web network.")
        subprocess.run("podman network create web_network", shell=True, check=True)

    # Build all images
    print("Building all images.")
    subprocess.run("podman build -t rest_image --build-arg DB_SERVER=${DB_SERVER} --build-arg DB_PORT=${DB_OUTER_PORT} --build-arg DB_NAME=${DB_NAME} --build-arg DB_AUTH_USER=${REST_DB_LOGIN} --build-arg DB_AUTH_PASSWORD=${REST_DB_PASSWORD} --build-arg DB_AUTHSOURCE=${DB_AUTHSOURCE} --build-arg REST_INNER_PORT=${REST_INNER_PORT} ./rest", shell=True, check=True)

    subprocess.run("podman build -t client_image --build-arg NODE_ID=${NODE} --build-arg CLIENT_INNER_PORT=${CLIENT_INNER_PORT} ./client", shell=True, check=True)

    subprocess.run("podman build -t vre_lite_image --build-arg MINIO_USER=${MINIO_USER} --build-arg MINIO_PASSWORD=${MINIO_PASSWORD} --build-arg MINIO_API_PORT=${MINIO_API_INNER_PORT} --build-arg VRE_LITE_INNER_PORT=${VRE_LITE_INNER_PORT} --build-arg VRE_LITE_BASE_URL_DEVELOPMENT=${VRE_LITE_BASE_URL_DEVELOPMENT} --build-arg VRE_LITE_BASE_URL_STAGING=${VRE_LITE_BASE_URL_STAGING} --build-arg VRE_LITE_BASE_URL_PRODUCTION=${VRE_LITE_BASE_URL_PRODUCTION} --build-arg VRE_LITE_LOG_PATH=${VRE_LITE_LOG_PATH} --build-arg VRE_LITE_MAX_FILE_SIZE=${VRE_LITE_MAX_FILE_SIZE} --build-arg VRE_LITE_TIME_DIFF=${VRE_LITE_TIME_DIFF} --build-arg MINIO_PROTOCOL=${MINIO_PROTOCOL} --build-arg MINIO_URL=${MINIO_URL} --build-arg MINIO_PORT=${APACHE_MINIO_OUTER_PORT} --build-arg NODE_NAME=${NODE} ./vre_lite", shell=True, check=True)

    subprocess.run("podman build -t apache_image --build-arg APACHE_HTTP_INNER_PORT=${APACHE_HTTP_INNER_PORT} --build-arg APACHE_HTTPS_INNER_PORT=${APACHE_HTTPS_INNER_PORT} --build-arg APACHE_HTTP_OUTER_PORT=${APACHE_HTTP_OUTER_PORT} --build-arg APACHE_HTTPS_OUTER_PORT=${APACHE_HTTPS_OUTER_PORT} --build-arg APACHE_MINIO_OUTER_PORT=${APACHE_MINIO_OUTER_PORT} --build-arg APACHE_MINIO_INNER_PORT=${APACHE_MINIO_INNER_PORT} --build-arg CLIENT_INNER_PORT=${CLIENT_INNER_PORT} --build-arg REST_INNER_PORT=${REST_INNER_PORT} --build-arg VRE_LITE_INNER_PORT=${VRE_LITE_INNER_PORT} --build-arg MINIO_UI_INNER_PORT=${MINIO_UI_INNER_PORT} --build-arg MINIO_API_INNER_PORT=${MINIO_API_INNER_PORT} --build-arg SERVER_URL=${MINIO_URL} --build-arg SSL_CERTIFICATE=${SSL_CERTIFICATE} --build-arg SSL_CERT_KEY=${SSL_CERT_KEY} ./apache", shell=True, check=True)

    subprocess.run("podman build -t workflow_image --build-arg MINIO_USER=${MINIO_USER} --build-arg MINIO_PASSWORD=${MINIO_PASSWORD} --build-arg MINIO_API_PORT=${MINIO_API_INNER_PORT} ./workflow", shell=True, check=True)

    subprocess.run("podman build -t loader_image --build-arg DB_SERVER=${DB_SERVER} --build-arg DB_PORT=${DB_OUTER_PORT} --build-arg DB_NAME=${DB_NAME} --build-arg DB_AUTH_USER=${LOADER_DB_LOGIN} --build-arg DB_AUTH_PASSWORD=${LOADER_DB_PASSWORD} --build-arg DB_AUTHSOURCE=${DB_AUTHSOURCE} ./loader", shell=True, check=True)

    # Run containers
    print("Running containers.")
    subprocess.run("podman run -d --name mongodb -e MONGO_INITDB_ROOT_USERNAME=${MONGO_INITDB_ROOT_USERNAME} -e MONGO_INITDB_ROOT_PASSWORD=${MONGO_INITDB_ROOT_PASSWORD} -e MONGO_PORT=${DB_OUTER_PORT} -e MONGO_INITDB_DATABASE=${DB_NAME} -e LOADER_DB_LOGIN=${LOADER_DB_LOGIN} -e LOADER_DB_PASSWORD=${LOADER_DB_PASSWORD} -e REST_DB_LOGIN=${REST_DB_LOGIN} -e REST_DB_PASSWORD=${REST_DB_PASSWORD} -p ${DB_OUTER_PORT}:${DB_OUTER_PORT} -v ${DB_VOLUME_PATH}:/data:Z -v $(pwd)/mongodb/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro --cpus \"${DB_CPU_LIMIT}\" --memory \"${DB_MEMORY_LIMIT}\" --network data_network --security-opt label=disable docker.io/library/mongo:6", shell=True, check=True)

    subprocess.run("podman run -d --name rest -p ${REST_OUTER_PORT}:${REST_INNER_PORT} --cpus \"${REST_CPU_LIMIT}\" --memory \"${REST_MEMORY_LIMIT}\" --network data_network --network web_network rest_image", shell=True, check=True)

    subprocess.run("podman run -d --name client -p ${CLIENT_OUTER_PORT}:${CLIENT_INNER_PORT} --cpus \"${CLIENT_CPU_LIMIT}\" --memory \"${CLIENT_MEMORY_LIMIT}\" --network web_network client_image", shell=True, check=True)

    subprocess.run("podman run -d --name minio -e MINIO_ROOT_USER=${MINIO_ROOT_USER} -e MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD} -e MINIO_BROWSER_REDIRECT_URL=${MINIO_BROWSER_REDIRECT_URL} -e MINIO_API_INNER_PORT=${MINIO_API_INNER_PORT} -e MINIO_UI_INNER_PORT=${MINIO_UI_INNER_PORT} -e MINIO_USER=${MINIO_USER} -e MINIO_PASSWORD=${MINIO_PASSWORD} -p ${MINIO_API_OUTER_PORT}:${MINIO_API_INNER_PORT} -p ${MINIO_UI_INNER_PORT}:${MINIO_UI_INNER_PORT} -v ${MINIO_VOLUME_PATH1}:/mnt/disk1:Z -v ${MINIO_VOLUME_PATH2}:/mnt/disk2:Z -v ${MINIO_VOLUME_PATH3}:/mnt/disk3:Z -v ${MINIO_VOLUME_PATH4}:/mnt/disk4:Z -v $(pwd)/minio/init-minio.sh:/entrypoint.sh --cpus \"${MINIO_CPU_LIMIT}\" --memory \"${MINIO_MEMORY_LIMIT}\" --network minio_network --network web_network --hostname minio --entrypoint /entrypoint.sh --healthcheck-command \"curl -f http://localhost:${MINIO_API_INNER_PORT}/minio/health/live\" --healthcheck-interval 10s --healthcheck-timeout 2s --healthcheck-retries 5 docker.io/minio/minio:latest", shell=True, check=True)

    subprocess.run("podman run -d --name vre_lite -p ${VRE_LITE_OUTER_PORT}:${VRE_LITE_INNER_PORT} -v ${VRE_LITE_VOLUME_PATH}:/vre_lite:Z --cpus \"${MINIO_CPU_LIMIT}\" --memory \"${MINIO_MEMORY_LIMIT}\" --network minio_network --network web_network vre_lite_image", shell=True, check=True)

    subprocess.run("podman run -d --name apache -p ${APACHE_HTTP_OUTER_PORT}:${APACHE_HTTP_INNER_PORT} -p ${APACHE_HTTPS_OUTER_PORT}:${APACHE_HTTPS_INNER_PORT} -p ${APACHE_MINIO_OUTER_PORT}:${APACHE_MINIO_INNER_PORT} -v ${APACHE_CERTS_VOLUME_PATH}:/usr/local/apache2/conf/ssl:Z --cpus \"${APACHE_CPU_LIMIT}\" --memory \"${APACHE_MEMORY_LIMIT}\" --network web_network apache_image", shell=True, check=True)

    # Poll until MinIO is up and running
    if 'env_vars' not in locals():
        env_vars = read_env_file('.env')
    poll_minio(env_vars.get('MINIO_API_OUTER_PORT'))

    print("Stack deployed.")
    subprocess.run(['podman', 'ps', '-a'])


def main():
    parser = argparse.ArgumentParser(description='Storage creation and Podman deploying for an MDDB node.')
    parser.add_argument('-r', '--remove-cache', action='store_true', help='Remove all cache before deploying the stack')

    args = parser.parse_args()

    deploy_stack(args.remove_cache)


if __name__ == '__main__':
    main()
