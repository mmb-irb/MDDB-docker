# Installation and configuration of Apache

## Apache installation

These are the steps to install Apache on **Ubuntu 22.04** or superior. 

### Update the APT package index

    sudo apt-get update

### Install the apache2 package

    sudo apt install apache2

### Checking your web server

    sudo systemctl status apache2

Should ouput:

    ● apache2.service - The Apache HTTP Server
        Loaded: loaded (/usr/lib/systemd/system/apache2.service; enabled; preset: enabled)
        Active: active (running) since Mon 2024-07-29 08:39:37 UTC; 1 day 2h ago
          Docs: https://httpd.apache.org/docs/2.4/
       Process: 74130 ExecStart=/usr/sbin/apachectl start (code=exited, status=0/SUCCESS)
       Process: 126584 ExecReload=/usr/sbin/apachectl graceful (code=exited, status=0/SUCCESS)
      Main PID: <PID> (apache2)
         Tasks: 55 (limit: 154534)
        Memory: 22.7M (peak: 37.4M)
           CPU: 7.341s
        CGroup: /system.slice/apache2.service
                ├─<PID> /usr/sbin/apache2 -k start
                ├─<PID> /usr/sbin/apache2 -k start
                └─<PID> /usr/sbin/apache2 -k start

When you have your server’s IP address, enter it into your browser’s address bar:

    http://your_server_ip

And this should show the default Ubuntu Apache web page. This page indicates that Apache is working correctly. It also includes some basic information about important Apache files and directory locations.

## Managing the Apache process

### Stop web server

    sudo systemctl stop apache2

### Start web server when it is stopped

    sudo systemctl start apache2

### Stop and then start the service again

    sudo systemctl restart apache2

or 

    sudo /etc/init.d/apache2 restart

## Apache configuration

Now it's time to **configure Apache** as a reverse proxy in order to show the [**client docker**](../client) as the website instead of the Ubuntu Apache default web page seen before.

### Enable modules

Apache has many modules bundled with it that are available but not enabled in a fresh installation. We need to enable some of them:

#### mod_rewrite

Apache module that provides a powerful and flexible way to rewrite URLs:

    sudo a2enmod rewrite

#### mod_proxy

The main proxy module Apache module for redirecting connections; it allows Apache to act as a gateway to the underlying application servers:  

    sudo a2enmod proxy

#### mod_proxy_http

Which adds support for proxying HTTP connections:

    sudo a2enmod proxy_http 

#### mod_proxy_wstunnel

Apache module that allows Apache to act as a reverse proxy for WebSocket connections. WebSockets are a communication protocol that provides full-duplex (two-way) communication channels over a single, long-lived TCP connection between a client (usually a web browser) and a server.   

    sudo a2enmod proxy_wstunnel

#### mod_ssl

Enables HTTPS protocol with Apache:

    sudo a2enmod ssl

### Copy certificates into VM

Copy the **www_mddbr_eu_chain.pem** and **www_mddbr_eu.key** file certificates into the following folders:

    /etc/ssl/certs/www_mddbr_eu_chain.pem
    /etc/ssl/private/www_mddbr_eu.key

For obtaining these two files, please contact with the MDDB administrators.

### Setting Up Virtual Hosts

Though several **virtual hosts** can be configured in a single Apache web server, for this project **only one is needed**, so we will edit the **default configuration** file:

    sudo vim /etc/apache2/sites-enabled/000-default.conf

Once the file is opened with an editor (vim in this case), please remove all the content and **copy** the following code:

```apacheconf
<VirtualHost *:80>

    <Location / >
        ProxyPass http://localhost:8080/
        ProxyPassReverse http://localhost:8080/
    </Location>

    <Location /api/ >
        ProxyPass http://localhost:8081/
        ProxyPassReverse http://localhost:8081/
    </Location>

    <Location /vre/ >
        ProxyPass http://localhost:8082/vre/
        ProxyPassReverse http://localhost:8082/vre/
    </Location>

    # Recommended to disable it in production
    <Location /minio/ >
        ProxyPass http://localhost:9001/
        ProxyPassReverse http://localhost:9001/
    </Location>

    <Location /minioapi/ >
        ProxyPass http://127.0.0.1:9000/
        ProxyPassReverse http://127.0.0.1:9000/
    </Location>

    # WebSocket proxy settings
    RewriteEngine on
    RewriteCond %{HTTP:UPGRADE} WebSocket [NC]
    RewriteCond %{HTTP:CONNECTION} Upgrade [NC]
    RewriteRule /minio/(.*) ws://127.0.0.1:9001/$1 [P,L]

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

</VirtualHost>

<VirtualHost *:443>

    <Location / >
        ProxyPass http://localhost:8080/
        ProxyPassReverse http://localhost:8080/
    </Location>

    <Location /api/ >
        ProxyPass http://localhost:8081/
        ProxyPassReverse http://localhost:8081/
    </Location>

    <Location /vre/ >
        ProxyPass http://localhost:8082/vre/
        ProxyPassReverse http://localhost:8082/vre/
    </Location>

    # Recommended to disable it in production
    <Location /minio/ >
        ProxyPass http://localhost:9001/
        ProxyPassReverse http://localhost:9001/
    </Location>

    <Location /minioapi/ >
        ProxyPass http://127.0.0.1:9000/
        ProxyPassReverse http://127.0.0.1:9000/
    </Location>

    # WebSocket proxy settings
    RewriteEngine on
    RewriteCond %{HTTP:UPGRADE} WebSocket [NC]
    RewriteCond %{HTTP:CONNECTION} Upgrade [NC]
    RewriteRule /minio/(.*) ws://127.0.0.1:9001/$1 [P,L]

    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/www_mddbr_eu_chain.pem
    SSLCertificateKeyFile /etc/ssl/private/www_mddbr_eu.key
    SSLCertificateChainFile /etc/ssl/certs/www_mddbr_eu_chain.pem

</VirtualHost>
```

The first part, `<VirtualHost *:80>`, configures the **HTTP** Virtual Host, while the second one, `<VirtualHost *:443>`, configures the **HTTPS** Virtual Host.

Note the following ports:

* **8080** is the output port for the [**client docker**](../client)
* **8081** is the output port for the [**REST API docker**](../rest)
* **8082** is the output port for the [**VRE docker**](../vre)
* **9001** is the output port for the **MinIO WebUI**, not recommended for using in production
* **9000** is the output port for the **MinIO API**

These ports can be changed, but in this case, please change them as well in the [**.env**](../.env.git) file.

Finally, all that remains is restarting the Apache server:

    sudo systemctl restart apache2