# Apache

The Apache HTTP Server, colloquially called Apache, is a **Web server** application notable for playing a key role in the initial growth of the World Wide Web:

https://hub.docker.com/_/httpd

## Dockerfile

Be aware of having the **public** and **private** ssl files in the **same folder** where the Dockerfile is:

```Dockerfile
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
ARG SSL_CERTIFICATE
ARG SSL_CERTIFICATE_KEY

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
RUN sed -i "s/SSL_CERTIFICATE_KEY/${SSL_CERTIFICATE_KEY}/g" /usr/local/apache2/conf/conf.d/custom.conf

# Append IncludeOptional directive to the default httpd.conf
RUN echo "IncludeOptional /usr/local/apache2/conf/conf.d/custom.conf" >> /usr/local/apache2/conf/httpd.conf

EXPOSE ${APACHE_HTTP_INNER_PORT} ${APACHE_HTTPS_INNER_PORT} ${APACHE_MINIO_INNER_PORT}
```

## Apache conf file

```apache
LoadModule rewrite_module /usr/local/apache2/modules/mod_rewrite.so
LoadModule proxy_module /usr/local/apache2/modules/mod_proxy.so
LoadModule proxy_http_module /usr/local/apache2/modules/mod_proxy_http.so
LoadModule proxy_wstunnel_module /usr/local/apache2/modules/mod_proxy_wstunnel.so
LoadModule ssl_module /usr/local/apache2/modules/mod_ssl.so

<VirtualHost *:APACHE_HTTP_OUTER_PORT>
  # Redirect all HTTP traffic to HTTPS
  RewriteEngine on
  RewriteCond %{SERVER_NAME} =SERVER_URL
  RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]
</VirtualHost>

<VirtualHost *:APACHE_HTTPS_OUTER_PORT>
  ServerName SERVER_URL

  # MDPosit front end
	<Location / >
    ProxyPass http://client:CLIENT_INNER_PORT/
    ProxyPassReverse http://client:CLIENT_INNER_PORT/
	</Location>

  # MDPosit REST API
	<Location /api/ >
    ProxyPass http://rest:REST_INNER_PORT/
    ProxyPassReverse http://rest:REST_INNER_PORT/
  </Location>

   # VRE lite (anonymous file upload)
	<Location /vre_lite/ >
    ProxyPass http://vre_lite:VRE_LITE_INNER_PORT/vre_lite/
    ProxyPassReverse http://vre_lite:VRE_LITE_INNER_PORT/vre_lite/
  </Location>

  # MinIO WebUI (object storage UI access, recommended to disable it in production)
  <Location /minio/ >
    ProxyPass http://minio:MINIO_UI_INNER_PORT/
    ProxyPassReverse http://minio:MINIO_UI_INNER_PORT/
    #Require ip TODO: Add IP range
  </Location>

  # Enable mod_rewrite
  RewriteEngine On
  # WebSocket proxy settings
  RewriteCond %{HTTP:UPGRADE} WebSocket [NC]
  RewriteCond %{HTTP:CONNECTION} Upgrade [NC]
  RewriteRule /minio/(.*) ws://minio:MINIO_UI_INNER_PORT/$1 [P,L]

  SSLEngine on
  SSLCertificateFile /usr/local/apache2/conf/ssl/SSL_CERTIFICATE
  SSLCertificateKeyFile /usr/local/apache2/conf/ssl/SSL_CERTIFICATE_KEY
</VirtualHost>

<VirtualHost *:APACHE_MINIO_OUTER_PORT>
    ServerName SERVER_URL
    
    SSLEngine on
    SSLCertificateFile /usr/local/apache2/conf/ssl/SSL_CERTIFICATE
    SSLCertificateKeyFile /usr/local/apache2/conf/ssl/SSL_CERTIFICATE_KEY
    SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1

    ProxyPreserveHost On
    ProxyPass / http://minio:MINIO_API_INNER_PORT/
    ProxyPassReverse / http://minio:MINIO_API_INNER_PORT/
</VirtualHost>

# Ensure Apache listens on port APACHE_HTTPS_OUTER_PORT and APACHE_MINIO_OUTER_PORT
Listen APACHE_HTTPS_OUTER_PORT
Listen APACHE_MINIO_OUTER_PORT
```