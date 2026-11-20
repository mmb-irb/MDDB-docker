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
# development services
RUN sed -i "s/SERVICES_MONITOR_API_INNER_PORT/${SERVICES_MONITOR_API_INNER_PORT:-3001}/g" /usr/local/apache2/conf/conf.d/custom.conf

# TLS certificate: always from Let's Encrypt, got and renewed by apache itself (mod_md), see readme/storage.md#certificates.
# Only for configurations that terminate TLS (behind an external TLS proxy, e.g. apache-config-florida.conf, there is none).
#   CERT_EMAIL      required: contact of the Let's Encrypt account (expiry and problem notices)
#   CERT_DOMAINS    comma-separated names of the certificate (default: SERVER_URL); all of them must reach this apache
#   CERT_ACME_URL   ACME directory (default: Let's Encrypt production; the staging one is only for tests)
#   CERT_CHALLENGES ACME challenge (default: tls-alpn-01 http-01; mod_md uses the first one it can set up, it does not
#                   switch on failure; http-01 only behind a proxy that terminates TLS)
ARG CERT_EMAIL
ARG CERT_DOMAINS
ARG CERT_ACME_URL=https://acme-v02.api.letsencrypt.org/directory
ARG CERT_CHALLENGES="tls-alpn-01 http-01"
COPY apache-mod-md.conf /tmp/apache-mod-md.conf
RUN set -e; \
    CONF=/usr/local/apache2/conf/conf.d/custom.conf; \
    if grep -q '^[[:space:]]*SSLEngine[[:space:]]\+on' "$CONF"; then \
        if [ -z "${CERT_EMAIL}" ]; then \
            echo "ERROR: CERT_EMAIL is empty. Apache gets its TLS certificate from Let's Encrypt and needs a contact email: set CERT_EMAIL in .env (see readme/storage.md#certificates)." >&2; exit 1; \
        fi; \
        DOMAINS=$(echo "${CERT_DOMAINS:-$SERVER_URL}" | tr ',' ' '); \
        if [ -z "$(echo $DOMAINS)" ]; then \
            echo "ERROR: no names for the TLS certificate: set CERT_DOMAINS (or MINIO_URL) in .env." >&2; exit 1; \
        fi; \
        for d in $DOMAINS; do \
            if echo "$d" | grep -q '^[0-9.]*$\|:'; then \
                echo "ERROR: '$d' in CERT_DOMAINS/MINIO_URL is an IP address: Let's Encrypt only certifies DNS names. Use the DNS name that users type." >&2; exit 1; \
            fi; \
        done; \
        echo >> "$CONF"; \
        sed -e "s#CERT_ACME_URL#${CERT_ACME_URL}#" -e "s#CERT_EMAIL#${CERT_EMAIL}#" -e "s#CERT_CHALLENGES#${CERT_CHALLENGES}#" \
            -e "s#CERT_DOMAINS#$(echo $DOMAINS)#" \
            -e "s#APACHE_HTTP_OUTER_PORT#${APACHE_HTTP_OUTER_PORT}#" -e "s#APACHE_HTTPS_OUTER_PORT#${APACHE_HTTPS_OUTER_PORT}#" \
            /tmp/apache-mod-md.conf >> "$CONF"; \
        sed -i "s#CERT_ALIASES#$(echo $DOMAINS)#g" "$CONF"; \
    fi; \
    rm /tmp/apache-mod-md.conf

# Append IncludeOptional directive to the default httpd.conf
RUN echo "IncludeOptional /usr/local/apache2/conf/conf.d/custom.conf" >> /usr/local/apache2/conf/httpd.conf

EXPOSE ${APACHE_HTTP_INNER_PORT} ${APACHE_HTTPS_INNER_PORT} ${APACHE_MINIO_INNER_PORT}

# Apache, plus the activation of the certificates that mod_md gets or renews
COPY httpd-md-foreground /usr/local/bin/httpd-md-foreground
CMD ["httpd-md-foreground"]
