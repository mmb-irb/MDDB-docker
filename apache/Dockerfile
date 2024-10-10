FROM httpd:2.4

# Copy the custom Apache configuration file
COPY apache-config.conf /usr/local/apache2/conf/conf.d/custom.conf

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

# Append IncludeOptional directive to the default httpd.conf
RUN echo "IncludeOptional /usr/local/apache2/conf/conf.d/custom.conf" >> /usr/local/apache2/conf/httpd.conf

# Create the SSL directory
RUN mkdir -p /usr/local/apache2/conf/ssl

# Copy SSL certs into the container
COPY www_mddbr_eu_chain.pem /usr/local/apache2/conf/ssl/www_mddbr_eu_chain.pem
COPY www_mddbr_eu.key /usr/local/apache2/conf/ssl/www_mddbr_eu.key

EXPOSE ${APACHE_HTTP_INNER_PORT} ${APACHE_HTTPS_INNER_PORT} ${APACHE_MINIO_INNER_PORT}