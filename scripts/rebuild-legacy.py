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
    parser = argparse.ArgumentParser(description='Rebuild and push a concrete version service from node.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-d', dest='mode', action='store_const', const='d', default='d', help='Use Docker (default)')
    group.add_argument('-p', dest='mode', action='store_const', const='p', help='Use Podman')
    parser.add_argument('-s', '--service', type=str, required=True, help='Service to build and push into the stack.')
    parser.add_argument('-v', '--version', type=str, required=True, help='Version of the service.')
    parser.add_argument('-t', '--stack', type=str, required=False, help='Name of the stack where the service is running (only for docker swarm).')
    parser.add_argument('--tag', type=str, required=False, help='Image tag to read the version from (e.g. prod, dev, test). If not provided, the latest local image is used.')

    args = parser.parse_args()

    if args.mode == 'd':

        if not args.stack:
            print("Error: Stack name is required when using Docker mode.")
            sys.exit(1)

        subprocess.run("set -a && source .env && set +a", shell=True, check=True, executable='/bin/bash')

        # Build service with --no-cache
        build_command = []
        if command_exists(['docker-compose', 'version']):
            build_command = ['docker-compose', 'build', '--build-arg', f'VERSION={args.version}', '--no-cache', args.service]
        elif command_exists(['docker', 'compose', 'version']):
            build_command = ['docker', 'compose', 'build', '--build-arg', f'VERSION={args.version}', '--no-cache', args.service]
        else:
            print("Error: Neither 'docker-compose' nor 'docker compose' commands are available.")
            sys.exit(1)

        print(f"Running command: {' '.join(build_command)}")
        run_command(build_command)

        # Update service
        update_command = ['docker', 'service', 'update', '--force', f'{args.stack}_{args.service}']
        run_command(update_command)

        # Get version of the service
        image = f'{args.service}_image:{args.tag}' if args.tag else f'{args.service}_image'
        version_command = ['docker', 'run', '--entrypoint', '', '--rm', image, 'sh', '-c', 'cat /app/version.txt']
        # Get result of version command
        try:
            result = subprocess.run(version_command, capture_output=True, text=True, check=True)
            version = result.stdout.strip()
            print(f"Version for {args.service}: {version}")

            # Run version_tracker.py to update the version in the database
            dc_command = docker_compose_script()
            dc_command.extend(['run', '--rm', 'utils', 'version_tracker.py', args.service, version])
            run_command(dc_command)
        except subprocess.CalledProcessError as e:
            print(f"Failed to get version for {args.service}: {e.stderr}")

        # Prune containers and images
        run_command(['docker', 'container', 'prune', '-f'])
        run_command(['docker', 'image', 'prune', '-f'])

    elif args.mode == 'p':

        # Parse .env file and update os.environ
        with open('.env') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value

        if args.service != 'mongodb':
            subprocess.run(f"podman stop {args.service} || true && podman rm {args.service} || true", shell=True, check=True, executable='/bin/bash')
        b = get_podman_script('build', args.service)
        b = b.replace("--no-cache", f"--build-arg VERSION={args.version} --no-cache")
        run_command_p(b)

        r = get_podman_script('run', args.service)
        run_command_p(r)

        # Get version of the service
        image = f'{args.service}_image:{args.tag}' if args.tag else f'{args.service}_image'
        version_command = ['podman', 'run', '--entrypoint', '', '--rm', image, 'sh', '-c', 'cat /app/version.txt']
        # Get result of version command
        try:
            result = subprocess.run(version_command, capture_output=True, text=True, check=True)
            version = result.stdout.strip()
            print(f"Version for {args.service}: {version}")

            # Run version_tracker.py to update the version in the database
            v = get_podman_script('run', 'utils', args.service, version)
            run_command_p(v)
        except subprocess.CalledProcessError as e:
            print(f"Failed to get version for {args.service}: {e.stderr}")


if __name__ == '__main__':
    main()
