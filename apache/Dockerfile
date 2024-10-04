FROM httpd:2.4

# Copy the custom Apache configuration file
COPY apache-config.conf /usr/local/apache2/conf/conf.d/custom.conf

# Append IncludeOptional directive to the default httpd.conf
RUN echo "IncludeOptional /usr/local/apache2/conf/conf.d/custom.conf" >> /usr/local/apache2/conf/httpd.conf

# Optionally copy SSL certs if needed
COPY www_mddbr_eu_chain.pem /etc/ssl/certs/www_mddbr_eu_chain.pem
COPY www_mddbr_eu.key /etc/ssl/private/www_mddbr_eu.key

# EXPOSE ${APACHE_HTTP_INNER_PORT} ${APACHE_HTTPS_INNER_PORT}
EXPOSE 80 443