def get_podman_script(type, service):
    if service == 'rest':
        if type == 'build':
            cmd = "podman build -t rest_image --no-cache --build-arg DB_SERVER=${DB_SERVER} --build-arg DB_PORT=${DB_OUTER_PORT} --build-arg DB_NAME=${DB_NAME} --build-arg DB_AUTH_USER=${REST_DB_LOGIN} --build-arg DB_AUTH_PASSWORD=${REST_DB_PASSWORD} --build-arg DB_AUTHSOURCE=${DB_AUTHSOURCE} --build-arg REST_INNER_PORT=${REST_INNER_PORT} ./rest"
            return cmd.split(" ")
        elif type == 'run':
            cmd = "podman run -d --name rest -p ${REST_OUTER_PORT}:${REST_INNER_PORT} --cpus \"${REST_CPU_LIMIT}\" --memory \"${REST_MEMORY_LIMIT}\" --network data_network --network web_network rest_image"
            return cmd.split(" ")
    elif service == 'client':
        if type == 'build':
            cmd = "podman build -t client_image --no-cache --build-arg NODE_ID=${NODE} --build-arg CLIENT_INNER_PORT=${CLIENT_INNER_PORT} ./client"
            # return cmd.split(" ")
            return cmd
        elif type == 'run':
            cmd = 'podman run -d --name client -p ${CLIENT_OUTER_PORT}:${CLIENT_INNER_PORT} --cpus "${CLIENT_CPU_LIMIT}" --memory "${CLIENT_MEMORY_LIMIT}" --network web_network client_image'
            # return cmd.split(" ")
            return cmd
    elif service == 'vre_lite':
        if type == 'build':
            cmd = "podman build -t vre_lite_image --no-cache --build-arg MINIO_USER=${MINIO_USER} --build-arg MINIO_PASSWORD=${MINIO_PASSWORD} --build-arg MINIO_API_PORT=${MINIO_API_INNER_PORT} --build-arg VRE_LITE_INNER_PORT=${VRE_LITE_INNER_PORT} --build-arg VRE_LITE_BASE_URL_DEVELOPMENT=${VRE_LITE_BASE_URL_DEVELOPMENT} --build-arg VRE_LITE_BASE_URL_STAGING=${VRE_LITE_BASE_URL_STAGING} --build-arg VRE_LITE_BASE_URL_PRODUCTION=${VRE_LITE_BASE_URL_PRODUCTION} --build-arg VRE_LITE_LOG_PATH=${VRE_LITE_LOG_PATH} --build-arg VRE_LITE_MAX_FILE_SIZE=${VRE_LITE_MAX_FILE_SIZE} --build-arg VRE_LITE_TIME_DIFF=${VRE_LITE_TIME_DIFF} --build-arg MINIO_PROTOCOL=${MINIO_PROTOCOL} --build-arg MINIO_URL=${MINIO_URL} --build-arg MINIO_PORT=${APACHE_MINIO_OUTER_PORT} --build-arg NODE_NAME=${NODE} ./vre_lite"
            return cmd.split(" ")
        elif type == 'run':
            cmd = "podman run -d --name vre_lite -p ${VRE_LITE_OUTER_PORT}:${VRE_LITE_INNER_PORT} -v ${VRE_LITE_VOLUME_PATH}:/vre_lite:Z --cpus \"${MINIO_CPU_LIMIT}\" --memory \"${MINIO_MEMORY_LIMIT}\" --network minio_network --network web_network vre_lite_image"
            return cmd.split(" ")
    elif service == 'minio':
        if type == 'build':
            cmd = "echo No build for MinIO service"
            return cmd.split(" ")
        elif type == 'run':
            cmd = "podman run -d --name minio -e MINIO_ROOT_USER=${MINIO_ROOT_USER} -e MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD} -e MINIO_BROWSER_REDIRECT_URL=${MINIO_BROWSER_REDIRECT_URL} -e MINIO_API_INNER_PORT=${MINIO_API_INNER_PORT} -e MINIO_UI_INNER_PORT=${MINIO_UI_INNER_PORT} -e MINIO_USER=${MINIO_USER} -e MINIO_PASSWORD=${MINIO_PASSWORD} -p ${MINIO_API_OUTER_PORT}:${MINIO_API_INNER_PORT} -p ${MINIO_UI_INNER_PORT}:${MINIO_UI_INNER_PORT} -v ${MINIO_VOLUME_PATH1}:/mnt/disk1:Z -v ${MINIO_VOLUME_PATH2}:/mnt/disk2:Z -v ${MINIO_VOLUME_PATH3}:/mnt/disk3:Z -v ${MINIO_VOLUME_PATH4}:/mnt/disk4:Z -v $(pwd)/minio/init-minio.sh:/entrypoint.sh --cpus \"${MINIO_CPU_LIMIT}\" --memory \"${MINIO_MEMORY_LIMIT}\" --network minio_network --network web_network --hostname minio --entrypoint /entrypoint.sh --healthcheck-command \"curl -f http://localhost:${MINIO_API_INNER_PORT}/minio/health/live\" --healthcheck-interval 10s --healthcheck-timeout 2s --healthcheck-retries 5 docker.io/minio/minio:latest"
            return cmd.split(" ")
    elif service == 'apache':
        if type == 'build':
            cmd = "podman build -t apache_image --no-cache --build-arg APACHE_HTTP_INNER_PORT=${APACHE_HTTP_INNER_PORT} --build-arg APACHE_HTTPS_INNER_PORT=${APACHE_HTTPS_INNER_PORT} --build-arg APACHE_HTTP_OUTER_PORT=${APACHE_HTTP_OUTER_PORT} --build-arg APACHE_HTTPS_OUTER_PORT=${APACHE_HTTPS_OUTER_PORT} --build-arg APACHE_MINIO_OUTER_PORT=${APACHE_MINIO_OUTER_PORT} --build-arg APACHE_MINIO_INNER_PORT=${APACHE_MINIO_INNER_PORT} --build-arg CLIENT_INNER_PORT=${CLIENT_INNER_PORT} --build-arg REST_INNER_PORT=${REST_INNER_PORT} --build-arg VRE_LITE_INNER_PORT=${VRE_LITE_INNER_PORT} --build-arg MINIO_UI_INNER_PORT=${MINIO_UI_INNER_PORT} --build-arg MINIO_API_INNER_PORT=${MINIO_API_INNER_PORT} --build-arg SERVER_URL=${MINIO_URL} --build-arg SSL_CERTIFICATE=${SSL_CERTIFICATE} --build-arg SSL_CERT_KEY=${SSL_CERT_KEY} ./apache"
            return cmd.split(" ")
        elif type == 'run':
            cmd = "podman run -d --name apache -p ${APACHE_HTTP_OUTER_PORT}:${APACHE_HTTP_INNER_PORT} -p ${APACHE_HTTPS_OUTER_PORT}:${APACHE_HTTPS_INNER_PORT} -p ${APACHE_MINIO_OUTER_PORT}:${APACHE_MINIO_INNER_PORT} -v ${APACHE_CERTS_VOLUME_PATH}:/usr/local/apache2/conf/ssl:Z --cpus \"${APACHE_CPU_LIMIT}\" --memory \"${APACHE_MEMORY_LIMIT}\" --network web_network apache_image"
            return cmd.split(" ")
    elif service == 'workflow':
        if type == 'build':
            cmd = "podman build -t workflow_image --no-cache --build-arg MINIO_USER=${MINIO_USER} --build-arg MINIO_PASSWORD=${MINIO_PASSWORD} --build-arg MINIO_API_PORT=${MINIO_API_INNER_PORT} ./workflow"
            return cmd.split(" ")
        elif type == 'run':
            cmd = "echo No run for Workflow service"
            return cmd.split(" ")
    elif service == 'loader':
        if type == 'build':
            cmd = "podman build -t loader_image --no-cache --build-arg DB_SERVER=${DB_SERVER} --build-arg DB_PORT=${DB_OUTER_PORT} --build-arg DB_NAME=${DB_NAME} --build-arg DB_AUTH_USER=${LOADER_DB_LOGIN} --build-arg DB_AUTH_PASSWORD=${LOADER_DB_PASSWORD} --build-arg DB_AUTHSOURCE=${DB_AUTHSOURCE} ./loader"
            return cmd.split(" ")
        elif type == 'run':
            cmd = "echo No run for Loader service"
            return cmd.split(" ")
    elif service == 'mongodb':
        if type == 'build':
            cmd = "echo No build for MongoDB service"
            return cmd.split(" ")
        elif type == 'run':
            cmd = "echo Please, run MongoDB manually"
            return cmd.split(" ")
