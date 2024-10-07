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
ARG APACHE_HTTP_OUTER_PORT
ARG APACHE_HTTPS_OUTER_PORT
ARG CLIENT_INNER_PORT
ARG REST_INNER_PORT
ARG VRE_LITE_INNER_PORT
ARG MINIO_UI_INNER_PORT

# Perform search and replace using sed
RUN sed -i "s/APACHE_HTTP_OUTER_PORT/${APACHE_HTTP_OUTER_PORT}/g" /usr/local/apache2/conf/conf.d/custom.conf
RUN sed -i "s/APACHE_HTTPS_OUTER_PORT/${APACHE_HTTPS_OUTER_PORT}/g" /usr/local/apache2/conf/conf.d/custom.conf
RUN sed -i "s/CLIENT_INNER_PORT/${CLIENT_INNER_PORT}/g" /usr/local/apache2/conf/conf.d/custom.conf
RUN sed -i "s/REST_INNER_PORT/${REST_INNER_PORT}/g" /usr/local/apache2/conf/conf.d/custom.conf
RUN sed -i "s/VRE_LITE_INNER_PORT/${VRE_LITE_INNER_PORT}/g" /usr/local/apache2/conf/conf.d/custom.conf
RUN sed -i "s/MINIO_UI_INNER_PORT/${MINIO_UI_INNER_PORT}/g" /usr/local/apache2/conf/conf.d/custom.conf

# Append IncludeOptional directive to the default httpd.conf
RUN echo "IncludeOptional /usr/local/apache2/conf/conf.d/custom.conf" >> /usr/local/apache2/conf/httpd.conf

# Create the SSL directory
RUN mkdir -p /usr/local/apache2/conf/ssl

# Copy SSL certs into the container
COPY www_mddbr_eu_chain.pem /usr/local/apache2/conf/ssl/www_mddbr_eu_chain.pem
COPY www_mddbr_eu.key /usr/local/apache2/conf/ssl/www_mddbr_eu.key

EXPOSE ${APACHE_HTTP_INNER_PORT} ${APACHE_HTTPS_INNER_PORT}
```

## Apache conf file

```apache
LoadModule rewrite_module /usr/local/apache2/modules/mod_rewrite.so
LoadModule proxy_module /usr/local/apache2/modules/mod_proxy.so
LoadModule proxy_http_module /usr/local/apache2/modules/mod_proxy_http.so
LoadModule proxy_wstunnel_module /usr/local/apache2/modules/mod_proxy_wstunnel.so
LoadModule ssl_module /usr/local/apache2/modules/mod_ssl.so

<VirtualHost *:APACHE_HTTP_OUTER_PORT>
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
  </Location>

	# Enable mod_rewrite
  RewriteEngine On
  # WebSocket proxy settings
  RewriteCond %{HTTP:UPGRADE} WebSocket [NC]
  RewriteCond %{HTTP:CONNECTION} Upgrade [NC]
  RewriteRule /minio/(.*) ws://minio:MINIO_UI_INNER_PORT/$1 [P,L]
</VirtualHost>

<VirtualHost *:APACHE_HTTPS_OUTER_PORT>
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
  </Location>

  # Enable mod_rewrite
  RewriteEngine On
  # WebSocket proxy settings
  RewriteCond %{HTTP:UPGRADE} WebSocket [NC]
  RewriteCond %{HTTP:CONNECTION} Upgrade [NC]
  RewriteRule /minio/(.*) ws://minio:MINIO_UI_INNER_PORT/$1 [P,L]
        
  SSLEngine on
  SSLCertificateFile /usr/local/apache2/conf/ssl/www_mddbr_eu_chain.pem
  SSLCertificateKeyFile /usr/local/apache2/conf/ssl/www_mddbr_eu.key
</VirtualHost>

# Ensure Apache listens on port 443
Listen APACHE_HTTPS_OUTER_PORT
```