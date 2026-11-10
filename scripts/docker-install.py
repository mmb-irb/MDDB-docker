#!/usr/bin/env python3
"""Install Docker Engine and the Docker Compose plugin on a new node, and add the user to the docker group.

    python3 scripts/docker-install.py [--root-dir /path/to/volume]

It follows Docker's official instructions for Ubuntu / Debian (apt) and Rocky / AlmaLinux / RHEL /
CentOS / Fedora (dnf), and needs sudo. On any other system, or if a step fails, it stops and shows the
official installation guide: https://docs.docker.com/engine/install/

--root-dir moves /var/lib/docker and /var/lib/containerd (where Docker keeps the images, tens of GB)
into <root-dir>/docker and <root-dir>/containerd and leaves symbolic links in their place
(readme/setup.md, "Change Docker Root Dir").
"""

import argparse
import getpass
import os
import shutil
import subprocess
import sys

DOCS = "https://docs.docker.com/engine/install/"
PACKAGES = ['docker-ce', 'docker-ce-cli', 'containerd.io', 'docker-buildx-plugin', 'docker-compose-plugin']


def sudo(cmd):
    """Run a command as root (with sudo unless we already are root); stop on any error."""
    if os.geteuid() != 0:
        cmd = ['sudo'] + cmd
    print('+ ' + ' '.join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def os_release():
    info = {}
    with open('/etc/os-release') as f:
        for line in f:
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                info[key] = value.strip('"')
    return info


def install_apt(distro, codename):
    # https://docs.docker.com/engine/install/ubuntu/ and .../debian/
    arch = subprocess.run(['dpkg', '--print-architecture'], capture_output=True, text=True, check=True).stdout.strip()
    sudo(['apt-get', 'update'])
    sudo(['apt-get', 'install', '-y', 'ca-certificates', 'curl'])
    sudo(['install', '-m', '0755', '-d', '/etc/apt/keyrings'])
    sudo(['curl', '-fsSL', f'https://download.docker.com/linux/{distro}/gpg', '-o', '/etc/apt/keyrings/docker.asc'])
    sudo(['chmod', 'a+r', '/etc/apt/keyrings/docker.asc'])
    source = (f"deb [arch={arch} signed-by=/etc/apt/keyrings/docker.asc] "
              f"https://download.docker.com/linux/{distro} {codename} stable\n")
    sudo(['sh', '-c', f"printf '%s' '{source}' > /etc/apt/sources.list.d/docker.list"])
    sudo(['apt-get', 'update'])
    sudo(['apt-get', 'install', '-y'] + PACKAGES)


def install_dnf(repo):
    # https://docs.docker.com/engine/install/rhel/, .../centos/ and .../fedora/
    sudo(['dnf', '-y', 'install', 'dnf-plugins-core'])
    repo_url = f'https://download.docker.com/linux/{repo}/docker-ce.repo'
    # dnf 5 (Fedora 41+) changed the syntax of config-manager
    dnf5 = subprocess.run(['dnf', '--version'], capture_output=True, text=True).stdout.startswith('dnf5')
    if dnf5:
        sudo(['dnf', 'config-manager', 'addrepo', f'--from-repofile={repo_url}'])
    else:
        sudo(['dnf', 'config-manager', '--add-repo', repo_url])
    sudo(['dnf', '-y', 'install'] + PACKAGES)


def install_docker():
    info = os_release()
    distro = info.get('ID', '')
    family = (distro + ' ' + info.get('ID_LIKE', '')).split()
    print(f"System: {info.get('PRETTY_NAME', distro)}")
    if distro in ('ubuntu', 'debian'):
        codename = info.get('UBUNTU_CODENAME') or info.get('VERSION_CODENAME')
        if not codename:
            raise RuntimeError(f"Cannot find the release codename of {distro} in /etc/os-release")
        install_apt(distro, codename)
    elif distro == 'fedora':
        install_dnf('fedora')
    elif distro == 'centos':
        install_dnf('centos')
    elif 'rhel' in family:   # Rocky, AlmaLinux, RHEL...
        install_dnf('rhel')
    else:
        raise RuntimeError(f"This script does not know how to install Docker on '{distro}'")
    sudo(['systemctl', 'enable', '--now', 'containerd', 'docker'])


def add_to_docker_group():
    user = os.environ.get('SUDO_USER') or getpass.getuser()
    if user == 'root':
        print("Running as root: no user added to the docker group. Run the services as a non-root user "
              "and add it with: sudo usermod -aG docker <user>")
        return
    sudo(['groupadd', '-f', 'docker'])
    sudo(['usermod', '-aG', 'docker', user])
    print(f"User '{user}' added to the docker group: log out and back in (or run 'newgrp docker') to use docker without sudo.")


def move_root_dir(root_dir):
    if not os.path.isdir(root_dir):
        raise RuntimeError(f"{root_dir} does not exist")
    moves = [('/var/lib/docker', os.path.join(root_dir, 'docker')),
             ('/var/lib/containerd', os.path.join(root_dir, 'containerd'))]
    for src, dst in moves:
        if os.path.islink(src):
            raise RuntimeError(f"{src} is already a symbolic link (to {os.readlink(src)}): nothing moved")
        if os.path.exists(dst):
            raise RuntimeError(f"{dst} already exists: it must not be created beforehand")
    sudo(['systemctl', 'stop', 'docker', 'docker.socket', 'containerd'])
    for src, dst in moves:
        if os.path.exists(src):
            sudo(['mv', src, dst])
        else:
            sudo(['mkdir', '-p', dst])
        sudo(['ln', '-s', dst, src])
    sudo(['systemctl', 'start', 'containerd', 'docker'])


def main():
    sys.stdout.reconfigure(line_buffering=True)   # keep our messages in order with the commands' output
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--root-dir', help='move the Docker images and data into this folder (see above)')
    args = parser.parse_args()

    if shutil.which('docker'):
        print("Docker is already installed: skipping the installation.")
    else:
        try:
            install_docker()
        except (subprocess.CalledProcessError, RuntimeError, OSError) as e:
            raise SystemExit(f"\nERROR: {e}\nInstall Docker following the official guide for your system: {DOCS}\n"
                             "(Docker Engine and the Docker Compose plugin), then see readme/setup.md.") from e
    add_to_docker_group()
    if args.root_dir:
        move_root_dir(args.root_dir)

    print("\nDocker installed:")
    subprocess.run(['docker', '--version'], check=True)
    subprocess.run(['docker', 'compose', 'version'], check=True)


if __name__ == '__main__':
    sys.exit(main())
