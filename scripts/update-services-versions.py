#!/usr/bin/env python3

import argparse
import subprocess
import sys
import os


def run_command(command, description=""):
    """Run a command and return the result."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip(), True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to {description}: {e.stderr}")
        return "", False


def command_exists(cmd):
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return True
    except subprocess.CalledProcessError:
        return False
    except (FileNotFoundError, PermissionError):
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


def get_service_version(service, podman=False, tag=None):
    """Get version from service image. Uses the given tag (e.g. prod, dev, test) if provided, otherwise the latest local image."""
    image = f'{service}_image:{tag}' if tag else f'{service}_image'
    if podman:
        version_command = ['podman', 'run', '--entrypoint', '', '--rm', image, 'sh', '-c', 'cat /app/version.txt']
    else:
        version_command = ['docker', 'run', '--entrypoint', '', '--rm', image, 'sh', '-c', 'cat /app/version.txt']
    print(f"🔍 Getting version for {service} ({image})...")

    version, success = run_command(version_command, f"get version for {service}")
    if success:
        print(f"📦 Version for {service}: {version}")
        return version
    return None


def update_version_tracker(service, version, podman=False):
    """Update version tracker with service version."""
    if podman:
        dc_command = ['podman', 'run', '--rm',
                      '--name', 'utils',
                      '-e', f"DB_SERVER={os.getenv('VRE_LITE_DB_SERVER')}",
                      '-e', f"DB_PORT={os.getenv('VRE_LITE_DB_OUTER_PORT')}",
                      '-e', f"DB_VRE_NAME={os.getenv('VRE_LITE_MONGO_DATABASE')}",
                      '-e', f"DB_VRE_AUTH_USER={os.getenv('VRE_LITE_DB_LOGIN')}",
                      '-e', f"DB_VRE_AUTH_PASSWORD={os.getenv('VRE_LITE_DB_PASSWORD')}",
                      '-e', f"DB_VRE_AUTHSOURCE={os.getenv('VRE_LITE_MONGO_DATABASE')}",
                      '--cpus', os.getenv('UTILS_CPU_LIMIT', '1.00'),
                      '--memory', os.getenv('UTILS_MEMORY_LIMIT', '1G'),
                      '--network', 'data_network',
                      'utils_image', 'version_tracker.py', service, version]
    else:
        dc_command = docker_compose_script()
        dc_command.extend(['run', '--rm', 'utils', 'version_tracker.py', service, version])

    print(f"📝 Updating version tracker for {service} v{version}...")

    output, success = run_command(dc_command, f"update version tracker for {service}")
    if success:
        print(f"✅ Successfully updated version tracker for {service}")
        if output:
            print(f"   Output: {output}")
    return success


def parse_args():
    parser = argparse.ArgumentParser(description='Update the tracked version for all services.')
    parser.add_argument('-t', '--tag', required=False,
                         help="Image tag to read the version from (e.g. prod, dev, test). If not provided, the latest local image is used.")
    return parser.parse_args()


def main():
    """Main function to update all service versions."""
    args = parse_args()
    services = ["client", "rest", "vre_lite", "loader", "workflow"]

    print("🚀 Starting service version update process")
    print("=" * 60)

    successful_updates = 0
    failed_updates = 0

    # Check if Podman is available, otherwise use Docker
    podman = command_exists(['podman', 'version'])

    for service in services:
        print(f"\n🔄 Processing service: {service}")
        print("-" * 40)

        # Get version from service image
        version = get_service_version(service, podman, args.tag)

        if version:
            # Update version tracker
            if update_version_tracker(service, version, podman):
                successful_updates += 1
            else:
                failed_updates += 1
        else:
            print(f"⚠️  Skipping version tracker update for {service} due to version retrieval failure")
            failed_updates += 1

    # Summary
    print("\n" + "=" * 60)
    print("📊 UPDATE SUMMARY")
    print("-" * 60)
    print(f"✅ Successful updates: {successful_updates}")
    print(f"❌ Failed updates: {failed_updates}")
    print(f"📦 Total services processed: {len(services)}")

    if failed_updates > 0:
        print(f"\n⚠️  {failed_updates} service(s) failed to update")
        sys.exit(1)
    else:
        print("\n🎉 All services updated successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
