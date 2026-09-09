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
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def docker_compose_script():
    """Determine which docker compose command is available."""
    # Try 'docker compose' (newer plugin version)
    if command_exists(['docker', 'compose', 'version']):
        return ['docker', 'compose']
    # Try 'docker-compose' (standalone binary)
    elif command_exists(['docker-compose', 'version']):
        return ['docker-compose']
    else:
        print("❌ Error: Neither 'docker compose' nor 'docker-compose' commands are available.")
        print("   Please install Docker Compose: https://docs.docker.com/compose/install/")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Rebuild and push one or more services from node.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-d', dest='mode', action='store_const', const='d', default='d', help='Use Docker (default)')
    group.add_argument('-p', dest='mode', action='store_const', const='p', help='Use Podman')
    parser.add_argument('-s', '--services', nargs='+', required=False, help='List of services to build and push into the stack.')
    parser.add_argument('-e', '--extensions', nargs='+', required=False, help='List of extension services to build and push into the stack.')
    parser.add_argument('-v', '--development', nargs='+', required=False, help='List of development services to build and push into the stack.')
    parser.add_argument('-t', '--stack', type=str, required=False, help='Name of the stack where the services are running (only for docker swarm).')
    parser.add_argument('--tag', type=str, required=False, help='Image tag to read the version from (e.g. prod, dev, test). If not provided, the latest local image is used.')

    args = parser.parse_args()

    if args.mode == 'd':

        if not args.stack:
            print("Error: Stack name is required when using Docker mode.")
            sys.exit(1)

        if not args.services and not args.extensions and not args.development:
            print("Error: At least one service must be specified.")
            sys.exit(1)

        subprocess.run("set -a && source .env && set +a", shell=True, check=True, executable='/bin/bash')

        # Build services with --no-cache
        build_command = docker_compose_script()
        build_command.extend(['-f', 'docker-compose.yml'])

        all_services = []
        if args.services:
            all_services.extend(args.services)
        if args.extensions:
            all_services.extend(args.extensions)
            for service in args.extensions:
                build_command.extend(['-f', f'extensions/{service}.yml'])
        if args.development:
            all_services.extend(args.development)
            for service in args.development:
                build_command.extend(['-f', f'development/{service}.yml'])

        build_command.append('build')

        if args.services:
            for service in args.services:
                build_command.extend(['--no-cache', service])
        if args.extensions:
            for service in args.extensions:
                build_command.extend(['--no-cache', service])
        if args.development:
            for service in args.development:
                build_command.extend(['--no-cache', service])

        print(f"Running command: {' '.join(build_command)}")
        run_command(build_command)

        # Update services
        for service in all_services:
            # update service in the stack
            update_command = ['docker', 'service', 'update', '--force', f'{args.stack}_{service}']
            run_command(update_command)

            # Get version of the service
            image = f'{service}_image:{args.tag}' if args.tag else f'{service}_image'
            version_command = ['docker', 'run', '--entrypoint', '', '--rm', image, 'sh', '-c', 'cat /app/version.txt']
            # Get result of version command
            try:
                result = subprocess.run(version_command, capture_output=True, text=True, check=True)
                version = result.stdout.strip()
                print(f"Version for {service}: {version}")

                # Run version_tracker.py to update the version in the database
                dc_command = docker_compose_script()
                dc_command.extend(['run', '--rm', 'utils', 'version_tracker.py', service, version])
                run_command(dc_command)
            except subprocess.CalledProcessError as e:
                print(f"Failed to get version for {service}: {e.stderr}")

        # Prune containers and images
        run_command(['docker', 'container', 'prune', '-f'])
        run_command(['docker', 'image', 'prune', '-f'])

    elif args.mode == 'p':

        if not args.services and not args.extensions and not args.development:
            print("Error: At least one service must be specified.")
            sys.exit(1)

        all_services = []
        if args.services:
            all_services.extend(args.services)
        if args.extensions:
            all_services.extend(args.extensions)
        if args.development:
            all_services.extend(args.development)

        # Parse .env file and update os.environ
        with open('.env') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value

        for service in all_services:
            if service != 'mongodb':
                subprocess.run(f"podman stop {service} || true && podman rm {service} || true", shell=True, check=True, executable='/bin/bash')
            b = get_podman_script('build', service)
            run_command_p(b)

        for service in all_services:
            r = get_podman_script('run', service)
            run_command_p(r)

        # Update services
        for service in all_services:
            # Get version of the service
            image = f'{service}_image:{args.tag}' if args.tag else f'{service}_image'
            version_command = ['podman', 'run', '--entrypoint', '', '--rm', image, 'sh', '-c', 'cat /app/version.txt']
            # Get result of version command
            try:
                result = subprocess.run(version_command, capture_output=True, text=True, check=True)
                version = result.stdout.strip()
                print(f"Version for {service}: {version}")

                # Run version_tracker.py to update the version in the database
                v = get_podman_script('run', 'utils', service, version)
                run_command_p(v)
            except subprocess.CalledProcessError as e:
                print(f"Failed to get version for {service}: {e.stderr}")


if __name__ == '__main__':
    main()
