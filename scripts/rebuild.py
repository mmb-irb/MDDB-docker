import argparse
import subprocess
import sys
import os
from podman_scripts import get_podman_script


def run_command(command):
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command '{' '.join(command)}' failed with return code {e.returncode}")


def run_command_p(command):
    try:
        subprocess.run(command, shell=True, check=True, executable='/bin/bash')
    except subprocess.CalledProcessError as e:
        print(f"Command '{command}' failed with return code {e.returncode}")


def command_exists(cmd):
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def main():
    parser = argparse.ArgumentParser(description='Rebuild and push one or more services from node.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-d', dest='mode', action='store_const', const='d', default='d', help='Use Docker (default)')
    group.add_argument('-p', dest='mode', action='store_const', const='p', help='Use Podman')
    parser.add_argument('-s', '--services', nargs='+', required=True, help='List of services to build and push into the stack.')
    parser.add_argument('-t', '--stack', type=str, required=False, help='Name of the stack where the services are running.')

    args = parser.parse_args()

    # Parse .env file and update os.environ
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value

    # check if works in runtime
    # subprocess.run("export $(grep -v '^#' .env | xargs)", shell=True, check=True, executable='/bin/bash')

    if (args.mode == 'd'):

        if not args.stack:
            print("Error: Stack name is required when using Docker mode.")
            sys.exit(1)

        # Build services with --no-cache
        build_command = []
        if command_exists(['docker-compose', 'version']):
            build_command = ['docker-compose', 'build']
        elif command_exists(['docker', 'compose', 'version']):
            build_command = ['docker', 'compose', 'build']
        else:
            print("Error: Neither 'docker-compose' nor 'docker compose' commands are available.")
            sys.exit(1)

        for service in args.services:
            build_command.extend(['--no-cache', service])
        print(f"Running command: {' '.join(build_command)}")
        run_command(build_command)

        # Update services
        for service in args.services:
            update_command = ['docker', 'service', 'update', '--force', f'{args.stack}_{service}']
            run_command(update_command)

        # Prune containers and images
        run_command(['docker', 'container', 'prune', '-f'])
        run_command(['docker', 'image', 'prune', '-f'])

    elif (args.mode == 'p'):

        for service in args.services:
            b = get_podman_script('build', service)
            run_command_p(b)

        for service in args.services:
            r = get_podman_script('run', service)
            print(r)
            run_command_p(r)


if __name__ == '__main__':
    main()
