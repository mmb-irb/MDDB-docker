import argparse
import subprocess


def run_command(command):
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command '{' '.join(command)}' failed with return code {e.returncode}")


def main():
    parser = argparse.ArgumentParser(description='Rebuild and push one or more services from MDDB node.')
    parser.add_argument('-s', '--services', nargs='+', help='List of services to build and update')

    args = parser.parse_args()

    # Build services with --no-cache
    build_command = ['docker-compose', 'build']
    for service in args.services:
        build_command.extend(['--no-cache', service])
    print(f"Running command: {' '.join(build_command)}")
    run_command(build_command)

    # Update services
    for service in args.services:
        update_command = ['docker', 'service', 'update', '--force', service]
        run_command(update_command)

    # Prune containers and images
    run_command(['docker', 'container', 'prune', '-f'])
    run_command(['docker', 'image', 'prune', '-f'])


if __name__ == '__main__':
    main()
