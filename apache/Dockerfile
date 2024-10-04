FROM httpd:2.4

# Copy the custom Apache configuration file
COPY apache-config.conf /usr/local/apache2/conf/conf.d/custom.conf

# Append IncludeOptional directive to the default httpd.conf
RUN echo "IncludeOptional /usr/local/apache2/conf/conf.d/custom.conf" >> /usr/local/apache2/conf/httpd.conf

# Create the SSL directory
RUN mkdir -p /usr/local/apache2/conf/ssl

# Copy SSL certs into the container
COPY www_mddbr_eu_chain.pem /usr/local/apache2/conf/ssl/www_mddbr_eu_chain.pem
COPY www_mddbr_eu.key /usr/local/apache2/conf/ssl/www_mddbr_eu.key

# EXPOSE ${APACHE_HTTP_INNER_PORT} ${APACHE_HTTPS_INNER_PORT}
EXPOSE 80 443