 # Set Up Virtual Machine

 It's highly recommended to have installed **Ubuntu 18.04 or superior** in this Virtual Machine, though the services should work in other **Linux** distributions. It is mandarory as well to have a **non-root** user with **sudo** privileges.

 The Set up is divided into two parts: 

* [Installation of Docker and Docker Compose](#installation-of-docker-and-docker-compose)
* [Installation and configuration of Apache](#installation-and-configuration-of-apache)

## Installation of Docker and Docker Compose

### Docker installation

These are the steps to install Docker on **Ubuntu 24.04**. Note that the official documentation might be slightly different, specially if trying to install docker into another Ubuntu version, so always refer to [Docker's official installation guide](https://docs.docker.com/engine/install/) for the most up-to-date instructions.

#### Update the APT package index

    sudo apt-get update

#### Install required packages

Install packages that allow **apt** to use repositories over HTTPS:

    sudo apt-get install apt-transport-https ca-certificates curl software-properties-common

#### Add Docker’s official GPG key

    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

#### Set up the stable repository

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

#### Update the APT package index again

    sudo apt-get update

#### Install Docker Engine

    sudo apt-get install docker-ce docker-ce-cli containerd.io

### Post-installation steps

To run Docker commands without **sudo**, you need to add your user to the **docker** group:

#### Create the docker group if it doesn't exist

    sudo groupadd docker

#### Add your user to the docker group

    sudo usermod -aG docker $USER

You can perform the same action in order to add **other users** to the docker group.

#### Apply the new group membership

You need to **log out** and **log back in** so that your group membership is re-evaluated. **Alternatively**, you can use the following command to apply the group change **without logging out**:

    newgrp docker

#### Verify the docker group membership

You can verify that your user is part of the docker group by running:

    groups $USER

#### Restart Docker

    sudo systemctl restart docker

### Docker Compose installation

In Linux, Docker Compose is not included into the Docker installation, so please follow the next steps for installing it in your VM:

#### Update the package index

    sudo apt-get update

#### Download Docker Compose

You need to download the **specific version** of Docker Compose. You can find the latest version on the [Docker Compose releases page](https://github.com/docker/compose/releases). At the time of writing, the latest version is **v2.21.0**. Adjust the version number in the command below if there is a newer version.

    sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

#### Apply executable permissions to the binary

    sudo chmod +x /usr/local/bin/docker-compose

#### Create a symbolic link to /usr/bin for convenience 

    sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

#### Verify the installation

    docker-compose --version

## Installation and configuration of Apache

### Apache installation

These are the steps to install Apache on **Ubuntu 22.04** or superior. 

#### Update the APT package index

    sudo apt-get update

#### Install the apache2 package

    sudo apt install apache2

#### Checking your web server

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

### Managing the Apache process

#### Stop web server

    sudo systemctl stop apache2

#### Start web server when it is stopped

    sudo systemctl start apache2

#### Stop and then start the service again

    sudo systemctl restart apache2

or 

    sudo /etc/init.d/apache2 restart

### Apache configuration

Now it's time to **configure Apache** as a reverse proxy in order to show the [**client docker**](../client) as the website instead of the Ubuntu Apache default web page seen before.

#### Enable modules

Apache has many modules bundled with it that are available but not enabled in a fresh installation. We need to enable three of them for using Apache as a reverse proxy:

##### mod_proxy

The main proxy module Apache module for redirecting connections; it allows Apache to act as a gateway to the underlying application servers:  

    sudo a2enmod proxy

##### mod_proxy_http

Which adds support for proxying HTTP connections:

    sudo a2enmod proxy_http 

##### mod_ssl

Enables HTTPS protocol with Apache:

    sudo a2enmod ssl

#### Copy certificates into VM

Copy the **www_mddbr_eu_chain.pem** and **www_mddbr_eu.key** file certificates into the following folders:

    /etc/ssl/certs/www_mddbr_eu_chain.pem
    /etc/ssl/private/www_mddbr_eu.key

For obtaining these two files, please contact with the MDDB administrators.

#### Setting Up Virtual Hosts

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

  SSLEngine on
  SSLCertificateFile /etc/ssl/certs/www_mddbr_eu_chain.pem
  SSLCertificateKeyFile /etc/ssl/private/www_mddbr_eu.key
  SSLCertificateChainFile /etc/ssl/certs/www_mddbr_eu_chain.pem

</VirtualHost>
```

The first part, `<VirtualHost *:80>`, configures the **HTTP** Virtual Host, while the second one, `<VirtualHost *:443>`, configures the **HTTPS** Virtual Host.

Note that the port **8080** is the output port for the [**client docker**](../client), while the port 8081 is the output port for the [**REST API docker**](../rest). These two ports can be changed, but in this case, please change them as well in the [**docker-compose.yml**](../docker-compose-git.yml) file.

Finally, all that remains is restarting the Apache server:

    sudo systemctl restart apache2