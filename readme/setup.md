 # Set Up Virtual Machine

 It's highly recommended to have installed **Ubuntu 18.04 or superior** in this Virtual Machine, though the services should work in other **Linux** distributions. It is mandatory as well to have a **non-root** user with **sudo** privileges.

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

### Change Docker Root Dir (optional)

Sometimes the **VM** has not enough space to store all the docker images, so it could be a **good practice** to move the **Docker Root Dir**:

#### Stop docker

Before moving Docker's storage directory, you need to **stop** the Docker service:

    sudo systemctl stop docker

#### Move the Docker Root Dir

Now, move Docker's current storage directory (`/var/lib/docker`) to the external disk:

    sudo mv /var/lib/docker /mnt/external_disk/docker

#### Create a Symlink

Create a **symbolic link** so that Docker continues to look in `/var/lib/docker`, but the actual data is stored on the external disk:

    sudo ln -s /mnt/external_disk/docker /var/lib/docker

### Start docker

Now that Docker is configured to use the external disk, **start** the Docker service again:

    sudo systemctl start docker

#### Check the Docker Info

    docker info | grep "Docker Root Dir"

You should see the new location, e.g., `/mnt/external_disk/docker`.

## Installation and configuration of Apache

Though Apache will be installed in the Docker Swarm, [**click here**](apache.md) in case you want to install Apache separately in the VM.