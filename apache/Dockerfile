# Base docker with apache 2.4
FROM docker.io/library/httpd:2.4

# Upgrade the base image system packages to get security fixes (e.g. brotli, openssl, gnutls)
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Copy the custom Apache configuration file
# APACHE_CONFIG selects a node-specific configuration (e.g. apache-config-florida.conf)
ARG APACHE_CONFIG=apache-config.conf
COPY ${APACHE_CONFIG} /usr/local/apache2/conf/conf.d/custom.conf

# Define the build arguments
ARG APACHE_HTTP_INNER_PORT
ARG APACHE_HTTPS_INNER_PORT
ARG APACHE_MINIO_INNER_PORT
ARG APACHE_HTTP_OUTER_PORT
ARG APACHE_HTTPS_OUTER_PORT
ARG APACHE_MINIO_OUTER_PORT
ARG CLIENT_INNER_PORT
ARG REST_INNER_PORT
ARG VRE_LITE_INNER_PORT
ARG MINIO_UI_INNER_PORT
ARG MINIO_API_INNER_PORT
ARG SERVER_URL
ARG SSL_CERTIFICATE
ARG SSL_CERT_KEY
# extension services
ARG MCP_INNER_PORT
# development services
ARG SERVICES_MONITOR_API_INNER_PORT

# Perform search and replace using sed
RUN sed -i "s/APACHE_HTTP_OUTER_PORT/${APACHE_HTTP_OUTER_PORT}/g" /usr/local/apache2/conf/conf.d/custom.conf
RUN sed -i "s/APACHE_HTTPS_OUTER_PORT/${APACHE_HTTPS_OUTER_PORT}/g" /usr/local/apache2/conf/conf.d/custom.conf
RUN sed -i "s/APACHE_MINIO_OUTER_PORT/${APACHE_MINIO_OUTER_PORT}/g" /usr/local/apache2/conf/conf.d/custom.conf
RUN sed -i "s/CLIENT_INNER_PORT/${CLIENT_INNER_PORT}/g" /usr/local/apache2/conf/conf.d/custom.conf
RUN sed -i "s/REST_INNER_PORT/${REST_INNER_PORT}/g" /usr/local/apache2/conf/conf.d/custom.conf
RUN sed -i "s/VRE_LITE_INNER_PORT/${VRE_LITE_INNER_PORT}/g" /usr/local/apache2/conf/conf.d/custom.conf
RUN sed -i "s/MINIO_UI_INNER_PORT/${MINIO_UI_INNER_PORT}/g" /usr/local/apache2/conf/conf.d/custom.conf
RUN sed -i "s/MINIO_API_INNER_PORT/${MINIO_API_INNER_PORT}/g" /usr/local/apache2/conf/conf.d/custom.conf
RUN sed -i "s/SERVER_URL/${SERVER_URL}/g" /usr/local/apache2/conf/conf.d/custom.conf
RUN sed -i "s/SSL_CERTIFICATE/${SSL_CERTIFICATE}/g" /usr/local/apache2/conf/conf.d/custom.conf
RUN sed -i "s/SSL_CERT_KEY/${SSL_CERT_KEY}/g" /usr/local/apache2/conf/conf.d/custom.conf
# extension services
RUN sed -i "s/MCP_INNER_PORT/${MCP_INNER_PORT:-8000}/g" /usr/local/apache2/conf/conf.d/custom.conf
# development services
RUN sed -i "s/SERVICES_MONITOR_API_INNER_PORT/${SERVICES_MONITOR_API_INNER_PORT:-3001}/g" /usr/local/apache2/conf/conf.d/custom.conf

# Let's Encrypt with mod_md (tls-alpn-01, only port 443 needed) instead of certbot, see readme/storage.md#certificates
ARG CERT_METHOD=certbot
ARG CERT_DOMAINS
ARG CERT_EMAIL
ARG CERT_ACME_URL=https://acme-v02.api.letsencrypt.org/directory
COPY apache-mod-md.conf /tmp/apache-mod-md.conf
RUN if [ "${CERT_METHOD}" = "mod_md" ]; then \
        if [ -z "${CERT_DOMAINS}" ] || [ -z "${CERT_EMAIL}" ]; then \
            echo "CERT_METHOD=mod_md needs CERT_DOMAINS and CERT_EMAIL" >&2; exit 1; \
        fi; \
        sed -e "s#CERT_ACME_URL#${CERT_ACME_URL}#" -e "s#CERT_EMAIL#${CERT_EMAIL}#" \
            -e "s#CERT_DOMAINS#$(echo "${CERT_DOMAINS}" | tr ',' ' ')#" \
            /tmp/apache-mod-md.conf >> /usr/local/apache2/conf/conf.d/custom.conf; \
    elif [ "${CERT_METHOD}" != "certbot" ]; then \
        echo "Unknown CERT_METHOD=${CERT_METHOD} (certbot or mod_md)" >&2; exit 1; \
    fi; \
    rm /tmp/apache-mod-md.conf

# Append IncludeOptional directive to the default httpd.conf
RUN echo "IncludeOptional /usr/local/apache2/conf/conf.d/custom.conf" >> /usr/local/apache2/conf/httpd.conf

EXPOSE ${APACHE_HTTP_INNER_PORT} ${APACHE_HTTPS_INNER_PORT} ${APACHE_MINIO_INNER_PORT}