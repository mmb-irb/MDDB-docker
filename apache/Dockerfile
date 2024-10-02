FROM debian:latest

# Update package list and install Apache HTTP Server and utilities
RUN apt-get update && \
    apt-get install -y apache2 apache2-utils && \
    a2enmod rewrite proxy proxy_http proxy_wstunnel ssl

# Copy your custom Apache configuration file
COPY apache-config.conf /etc/apache2/sites-available/000-default.conf

# Optionally copy SSL certs if needed
COPY www_mddbr_eu_chain.pem /etc/ssl/certs/www_mddbr_eu_chain.pem
COPY www_mddbr_eu.key /etc/ssl/private/www_mddbr_eu.key

# Expose ports 80 and 443
EXPOSE 80 443

# Start Apache HTTP Server in the foreground
CMD ["apache2ctl", "-D", "FOREGROUND"]