import os


def get_podman_script(type, service, svc=None, version=None):
    cmd = ''
    if service == 'rest':
        if type == 'build':
            cmd = "podman build -t rest_image --no-cache --build-arg DB_SERVER=${DB_SERVER} --build-arg DB_PORT=${DB_OUTER_PORT} --build-arg DB_NAME=${DB_NAME} --build-arg DB_AUTH_USER=${REST_DB_LOGIN} --build-arg DB_AUTH_PASSWORD=${REST_DB_PASSWORD} --build-arg DB_AUTHSOURCE=${DB_AUTHSOURCE} --build-arg REST_INNER_PORT=${REST_INNER_PORT} ./rest"
        elif type == 'run':
            cmd = "podman run -d --name rest -p ${REST_OUTER_PORT}:${REST_INNER_PORT} --memory ${REST_MEMORY_LIMIT} --network data_network --network web_network rest_image"
    elif service == 'client':
        if type == 'build':
            cmd = "podman build -t client_image --no-cache --build-arg CLIENT_INNER_PORT=${CLIENT_INNER_PORT} ./client"
        elif type == 'run':
            cmd = "podman run -d --name client -p ${CLIENT_OUTER_PORT}:${CLIENT_INNER_PORT} --memory ${CLIENT_MEMORY_LIMIT} --network web_network client_image"
    elif service == 'vre_lite':
        if type == 'build':
            cmd = "podman build -t vre_lite_image --no-cache --build-arg MINIO_USER=${MINIO_USER} --build-arg MINIO_PASSWORD=${MINIO_PASSWORD} --build-arg MINIO_API_PORT=${MINIO_API_INNER_PORT} --build-arg VRE_LITE_INNER_PORT=${VRE_LITE_INNER_PORT} --build-arg VRE_LITE_BASE_URL_DEVELOPMENT=${VRE_LITE_BASE_URL_DEVELOPMENT} --build-arg VRE_LITE_BASE_URL_STAGING=${VRE_LITE_BASE_URL_STAGING} --build-arg VRE_LITE_BASE_URL_PRODUCTION=${VRE_LITE_BASE_URL_PRODUCTION} --build-arg VRE_LITE_LOG_PATH=${VRE_LITE_LOG_PATH} --build-arg VRE_LITE_MAX_FILE_SIZE=${VRE_LITE_MAX_FILE_SIZE} --build-arg VRE_LITE_TIME_DIFF=${VRE_LITE_TIME_DIFF} --build-arg VERSION=${VRE_LITE_VERSION} --build-arg MINIO_PROTOCOL=${MINIO_PROTOCOL} --build-arg MINIO_URL=${MINIO_URL} --build-arg MINIO_PORT=${APACHE_MINIO_OUTER_PORT} --build-arg NODE_NAME=${NODE} --build-arg DB_USER=${VRE_LITE_DB_LOGIN} --build-arg DB_PASS=${VRE_LITE_DB_PASSWORD} --build-arg DB_SERVER=${VRE_LITE_DB_SERVER} --build-arg DB_PORT=${VRE_LITE_DB_OUTER_PORT} --build-arg DB_NAME=${VRE_LITE_MONGO_DATABASE} --build-arg PAT=${GH_PAT} --build-arg MINIO_ADDRESS=${MINIO_ADDRESS} ./vre_lite"
        elif type == 'run':
            cmd = "podman run -d --name vre_lite -p ${VRE_LITE_OUTER_PORT}:${VRE_LITE_INNER_PORT} -v ${VRE_LITE_VOLUME_PATH}:/vre_lite:Z -v /run/user/$(id -u)/podman/podman.sock:/var/run/docker.sock --memory ${MINIO_MEMORY_LIMIT} --network minio_network --network web_network --network data_network vre_lite_image"
    elif service == 'minio':
        if type == 'build':
            cmd = "echo No build for MinIO service"
        elif type == 'run':
            cmd = "podman run -d --name minio -e MINIO_ROOT_USER=${MINIO_ROOT_USER} -e MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD} -e MINIO_BROWSER_REDIRECT_URL=${MINIO_BROWSER_REDIRECT_URL} -e MINIO_API_INNER_PORT=${MINIO_API_INNER_PORT} -e MINIO_UI_INNER_PORT=${MINIO_UI_INNER_PORT} -e MINIO_USER=${MINIO_USER} -e MINIO_PASSWORD=${MINIO_PASSWORD} -p ${MINIO_API_OUTER_PORT}:${MINIO_API_INNER_PORT} -p ${MINIO_UI_INNER_PORT}:${MINIO_UI_INNER_PORT} -v ${MINIO_VOLUME_PATH1}:/mnt/disk1:Z -v $(pwd)/minio/init-minio.sh:/entrypoint.sh --memory ${MINIO_MEMORY_LIMIT} --network minio_network --network web_network --hostname minio --entrypoint /entrypoint.sh --healthcheck-command \"curl -f http://localhost:${MINIO_API_INNER_PORT}/minio/health/live\" --healthcheck-interval 10s --healthcheck-timeout 2s --healthcheck-retries 5 docker.io/minio/minio:latest"
    elif service == 'apache':
        if type == 'build':
            cmd = "podman build -t apache_image --no-cache --build-arg APACHE_HTTP_INNER_PORT=${APACHE_HTTP_INNER_PORT} --build-arg APACHE_HTTPS_INNER_PORT=${APACHE_HTTPS_INNER_PORT} --build-arg APACHE_HTTP_OUTER_PORT=${APACHE_HTTP_OUTER_PORT} --build-arg APACHE_HTTPS_OUTER_PORT=${APACHE_HTTPS_OUTER_PORT} --build-arg APACHE_MINIO_OUTER_PORT=${APACHE_MINIO_OUTER_PORT} --build-arg APACHE_MINIO_INNER_PORT=${APACHE_MINIO_INNER_PORT} --build-arg CLIENT_INNER_PORT=${CLIENT_INNER_PORT} --build-arg REST_INNER_PORT=${REST_INNER_PORT} --build-arg VRE_LITE_INNER_PORT=${VRE_LITE_INNER_PORT} --build-arg MINIO_UI_INNER_PORT=${MINIO_UI_INNER_PORT} --build-arg MINIO_API_INNER_PORT=${MINIO_API_INNER_PORT} --build-arg SERVER_URL=${MINIO_URL} --build-arg SSL_CERTIFICATE=${SSL_CERTIFICATE} --build-arg SSL_CERT_KEY=${SSL_CERT_KEY} ./apache"
        elif type == 'run':
            cmd = "podman run -d --name apache -p ${APACHE_HTTP_OUTER_PORT}:${APACHE_HTTP_INNER_PORT} -p ${APACHE_HTTPS_OUTER_PORT}:${APACHE_HTTPS_INNER_PORT} -p ${APACHE_MINIO_OUTER_PORT}:${APACHE_MINIO_INNER_PORT} -v ${APACHE_CERTS_VOLUME_PATH}:/usr/local/apache2/conf/ssl:Z --memory ${APACHE_MEMORY_LIMIT} --network web_network apache_image"
    elif service == 'workflow':
        if type == 'build':
            cmd = "podman build -t workflow_image --no-cache --build-arg MINIO_USER=${MINIO_USER} --build-arg MINIO_PASSWORD=${MINIO_PASSWORD} --build-arg MINIO_API_PORT=${MINIO_API_INNER_PORT} ./workflow"
        elif type == 'run':
            cmd = "echo No run for Workflow service"
    elif service == 'loader':
        if type == 'build':
            cmd = "podman build -t loader_image --no-cache --build-arg DB_SERVER=${DB_SERVER} --build-arg DB_PORT=${DB_OUTER_PORT} --build-arg DB_NAME=${DB_NAME} --build-arg DB_AUTH_USER=${LOADER_DB_LOGIN} --build-arg DB_AUTH_PASSWORD=${LOADER_DB_PASSWORD} --build-arg DB_AUTHSOURCE=${DB_AUTHSOURCE} ./loader"
        elif type == 'run':
            cmd = "echo No run for Loader service"
    elif service == 'mongodb':
        if type == 'build':
            cmd = "echo No build for MongoDB service"
        elif type == 'run':
            cmd = "echo Please, run MongoDB manually"
    elif service == 'mongo-backup':
        if type == 'build':
            cmd = "echo No build for MongoDB Backup service"
        elif type == 'run':
            cmd = "podman run -d --name mongo-backup -e MONGO_INITDB_ROOT_USERNAME=${MONGO_INITDB_ROOT_USERNAME} -e MONGO_INITDB_ROOT_PASSWORD=${MONGO_INITDB_ROOT_PASSWORD} -e MONGO_PORT=${DB_OUTER_PORT} -e MONGO_INITDB_DATABASE=${DB_AUTHSOURCE} -e DB_HOST=${DB_SERVER} -e BACKUP_DIR=/backup -e RETENTION_COUNT=${DB_BACKUP_RETENTION_COUNT} -e BACKUP_INTERVAL=${DB_BACKUP_INTERVAL} -v ${DB_BACKUP_VOLUME_PATH}:/backup:Z -v $(pwd)/mongodb/backup_script.sh:/backup_script.sh:ro --memory ${DB_BACKUP_MEMORY_LIMIT} --network data_network --security-opt label=disable docker.io/library/mongo:6 bash -c \"sh /backup_script.sh\""
    elif service == 'utils':
        if type == 'build':
            cmd = "podman build -t utils_image --no-cache ./utils"
        elif type == 'run':
            cmd = f"podman run --rm --name utils -e DB_SERVER=$VRE_LITE_DB_SERVER -e DB_PORT=$VRE_LITE_DB_OUTER_PORT -e DB_VRE_NAME=$VRE_LITE_MONGO_DATABASE -e DB_VRE_AUTH_USER=$VRE_LITE_DB_LOGIN -e DB_VRE_AUTH_PASSWORD=$VRE_LITE_DB_PASSWORD -e DB_VRE_AUTHSOURCE=$VRE_LITE_MONGO_DATABASE --memory $UTILS_MEMORY_LIMIT --network data_network utils_image version_tracker.py {svc} {version}"

    cmd = os.path.expandvars(cmd)
    return cmd
