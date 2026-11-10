# Set Up Virtual Machine

## Requirements

* **Linux** with a **non-root** user with **sudo** privileges. **Ubuntu 22.04 / 24.04** is recommended; the services should work on any distribution supported by Docker.
* A **CPU with AVX** (MongoDB 5 and newer crash with `Illegal instruction` without it). Check it with `grep -wo avx /proc/cpuinfo | head -1`. On a virtual machine, if nothing is printed, ask the VM admin to set the CPU type to `host` (or `x86-64-v3`) and power-cycle the VM.
* **Disk**: tens of GB where Docker keeps its images (`/var/lib/docker` and `/var/lib/containerd`, see [Change Docker Root Dir](#change-docker-root-dir-optional)), plus the space for the data (see [storage](storage.md)).
* **Outbound internet access** to GitHub, Docker Hub, PyPI, npm and NodeSource: the images are built from the source code of each service.
* The **clock synchronised** (NTP): MinIO rejects requests from clients whose clock differs from the server's.

## Installation of Docker and Docker Compose

[scripts/docker-install.py](../scripts/docker-install.py) runs these steps for you (Ubuntu, Debian, Rocky / AlmaLinux / RHEL, CentOS and Fedora), adds your user to the `docker` group and, with `--root-dir /path/to/volume`, does the [Change Docker Root Dir](#change-docker-root-dir-optional) step too.

These are the steps to install Docker on **Ubuntu**. Always refer to [Docker's official installation guide](https://docs.docker.com/engine/install/) for other distributions or if the steps below fail. Docker Compose is installed as a Docker plugin (`docker compose`, with a space).

### Docker installation

    sudo apt-get update
    sudo apt-get install -y ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

Check the installation:

    docker --version
    docker compose version

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

### Change Docker Root Dir (optional)

Sometimes the **VM** has not enough space to store all the docker images, so it could be a **good practice** to move the **Docker Root Dir**:

#### Stop docker

Before moving Docker's storage directory, you need to **stop** the Docker service:

    sudo systemctl stop docker
    sudo systemctl stop containerd

#### Move the Docker Root Dir

Now, move Docker's current storage directories (`/var/lib/docker` and `/var/lib/containerd`) to a volume out of the docker. This volume has been created previously in the [**storage step**](./storage.md#docker):

    sudo mv /var/lib/docker /path/to/volume/docker
    sudo mv /var/lib/containerd /path/to/volume/containerd

> **IMPORTANT!**: the `docker` and `containerd` folders inside `/path/to/volume` **must not be created beforehand**.

#### Create Symlinks

Create **symbolic links** so that Docker continues to look in `/var/lib/docker` and `/var/lib/containerd`, but the actual data is stored on the external disk:

    sudo ln -s /path/to/volume/docker /var/lib/docker
    sudo ln -s /path/to/volume/containerd /var/lib/containerd

#### Start docker

Now that Docker is configured to use the external disk, **start** the Docker service again:

    sudo systemctl start containerd
    sudo systemctl start docker

#### Check the Docker Info

    docker info | grep "Docker Root Dir"

You should see the new location, e.g., `/path/to/volume/docker`.

## Firewall and ports

Open to the users only the ports served by the Apache container: **443** (website, REST API, VRE lite), **80** (redirect to https and Let's Encrypt), and the MinIO API port (`APACHE_MINIO_OUTER_PORT`, e.g. **9000**). Check them from outside the VM with:

    nc -zv <vm_ip> 443
    nc -zv <vm_ip> 9000

The other published ports (8080, 8081, 8082, 9001, 9002) are for debugging from the VM itself. Docker inserts its own firewall rules ahead of `ufw` / `firewalld`, so these do not block them: filter them in the `DOCKER-USER` iptables chain or in the network firewall.

## Apache outside Docker (optional)

Apache is already one of the services of the stack. Only if you want to use an Apache installed directly in the VM instead, see [these instructions](apache.md).