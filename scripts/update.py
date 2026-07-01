#!/usr/bin/env python3

import subprocess
import json
import urllib.request
import os
import sys
from typing import List, Tuple, Optional


class VersionChecker:
    def __init__(self):
        # Configuration: service_name -> (github_org, github_repo, docker_image)
        self.services = {
            "client": ("mmb-irb", "MDposit-client-build", "client_image"),
            "rest": ("mmb-irb", "MDDB-REST-API", "rest_image"),
            "vre_lite": ("mmb-irb", "MDDB-VRE", "vre_lite_image"),
            "loader": ("mmb-irb", "MDDB-loader", "loader_image"),
            "workflow": ("mmb-irb", "MDDB-workflow", "workflow_image"),
            # Add more services as needed
        }

        self.updatable_services = []
        self.service_versions = {}
        self.repo_versions = {}

    def command_exists(self, cmd):
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            return True
        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError:
            return False

    def run_command(self, command: List[str], shell: bool = False, stream_output: bool = False) -> Tuple[bool, str]:
        """Run a command and return success status and output."""
        try:
            if shell:
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
            else:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)

            output_lines = []

            if stream_output:
                # Stream output in real-time
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        print(output.strip())  # Print immediately
                        output_lines.append(output.strip())
            else:
                # Silent mode - collect output without printing
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        output_lines.append(output.strip())

            return_code = process.poll()
            full_output = '\n'.join(output_lines)

            if return_code == 0 and 'return code 1' not in full_output.lower():
                return True, full_output
            else:
                return False, full_output

        except Exception as e:
            print(f"Command execution error: {e}")
            return False, str(e)

    def get_repo_version(self, org: str, repo: str) -> Optional[str]:
        """Get the latest version from GitHub repo tags."""
        print(f"  📡 Fetching latest version for {org}/{repo}...")

        # Get GitHub token from environment if available
        env_vars = self.read_env_file('.env')
        github_token = env_vars.get('GH_PAT')
        credentials = f'-H "Authorization: Bearer {github_token}"' if github_token else ''
        # Use authorization header with token when possible
        command = f'curl -s {credentials} "https://api.github.com/repos/{org}/{repo}/tags" 2>/dev/null'
        success, output = self.run_command(command, shell=True, stream_output=False)

        if not success or not output:
            print(f"    ⚠️  Could not fetch version for {org}/{repo}")
            return "unknown"
        
        # Parse the response
        tags = json.loads(output)
        
        # Get the date of every tag from the last commit
        for tag in tags:

            # Ask the API for the commit data
            commit_url = tag['commit']['url']
            command = f'curl -s {credentials} "{commit_url}" 2>/dev/null'
            success, output = self.run_command(command, shell=True, stream_output=False)
            if not success or not output:
                raise RuntimeError(f'Could not fetch data from {commit_url}')
            
            # Extract and store the date
            commit = json.loads(output)
            tag['date'] = commit['commit']['author']['date']

        # Now sort tags according to their dates
        sorted_tags = sorted(tags, key=lambda tag: tag['date'], reverse=True)

        # Get the latest tag version
        latest_tag = sorted_tags[0]
        version = latest_tag['name']

        # Remove 'v' prefix if present (v1.1 -> 1.1)
        if version.startswith('v'):
            version = version[1:]

        print(f"    ✅ Latest version: {version}")
        return version

    def get_service_version(self, service_name: str, image_name: str) -> Optional[str]:
        """Get version from Docker service's version.txt file."""
        print(f"  🐳 Checking Docker service version for {service_name}...")

        # Check if Podman is available, otherwise use Docker
        # podman = self.command_exists(['podman', 'version'])
        # # Use the exact command from the prompt
        # if podman:
        #     command = f'podman run --entrypoint "" --rm {image_name} sh -c "cat /app/version.txt"'
        # else:
        #     command = f'docker run --entrypoint "" --rm {image_name} sh -c "cat /app/version.txt"'

        docker = self.command_exists(['docker', 'version'])
        if docker:
            command = f'docker run --entrypoint "" --rm {image_name} sh -c "cat /app/version.txt"'
        else:
            command = f'podman run --entrypoint "" --rm {image_name} sh -c "cat /app/version.txt"'

        success, output = self.run_command(command, shell=True, stream_output=False)

        if not success:
            print(f"    ⚠️  Could not get version for {service_name}: version.txt not found or service not built")
            return "unknown"

        version = output.strip()
        print(f"    ✅ Current version: {version}")
        return version

    def compare_versions(self, repo_version: str, service_version: str) -> bool:
        """Compare versions and return True if repo version is newer."""
        try:
            # Simple version comparison assuming format like "1.2.3"
            repo_parts = [int(x) for x in repo_version.split('.')]
            service_parts = [int(x) for x in service_version.split('.')]

            # Pad with zeros if different lengths
            max_len = max(len(repo_parts), len(service_parts))
            repo_parts.extend([0] * (max_len - len(repo_parts)))
            service_parts.extend([0] * (max_len - len(service_parts)))

            return repo_parts > service_parts
        except (ValueError, AttributeError):
            # If version comparison fails, assume update is available
            return True

    def check_all_versions(self):
        """Check versions for all configured services."""
        print("🔍 Checking versions for all services...\n")

        for service_name, (org, repo, image) in self.services.items():
            print(f"📋 Checking {service_name}:")

            # Get repo version
            repo_version = self.get_repo_version(org, repo)
            self.repo_versions[service_name] = repo_version

            # Get service version
            service_version = self.get_service_version(service_name, image)
            self.service_versions[service_name] = service_version

            # Compare versions
            if repo_version and service_version and service_version != "dev":
                if self.compare_versions(repo_version, service_version):
                    print(f"    🆙 UPDATE AVAILABLE: {service_version} -> {repo_version}")
                    self.updatable_services.append(service_name)
                else:
                    print(f"    ✅ UP TO DATE: {service_version}")
            elif repo_version and not service_version:
                print(f"    🆕 NEW SERVICE: can install {repo_version}")
                self.updatable_services.append(service_name)
            elif not repo_version and service_version:
                print("    ⚠️  Cannot check updates (repo version unavailable)")
            elif repo_version and service_version and service_version == "dev":
                print("    📦 Service in development mode")
            else:
                print("    ❓ Cannot determine versions")

            print()

    def read_env_file(self, file_path: str) -> dict:
        env_vars = {}
        with open(file_path) as f:
            for line in f:
                # Strip whitespace and ignore comments and empty lines
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key] = value
        return env_vars

    def send_slack_notification(self, message: str):
        """Send a notification to Slack using urllib (no external dependencies)."""

        print(f"🔔 Sending Slack notification: {message}")

        try:
            env_vars = self.read_env_file('.env')
            slack_webhook_url = env_vars.get('SLACK_WEBHOOK_URL')
            node = env_vars.get('NODE')

            if not slack_webhook_url:
                print("⚠️  SLACK_WEBHOOK_URL not found in .env file")
                return

            # Replace placeholder with actual node value
            message = message.replace("##node##", node if node else "unknown")

            # Prepare the payload
            payload = {"text": message}
            data = json.dumps(payload).encode('utf-8')

            # Create the request
            req = urllib.request.Request(
                slack_webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )

            # Send the request
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    print("✅ Slack notification sent successfully")
                else:
                    print(f"⚠️  Slack notification failed with status: {response.status}")

        except Exception as e:
            print(f"❌ Failed to send Slack notification: {e}")

    def display_summary(self):
        """Display a summary of version status."""
        print("=" * 60)
        print("📊 VERSION SUMMARY")
        print("=" * 60)

        print(f"{'Service':<15} {'Current':<12} {'Latest':<12} {'Status':<15}")
        print("-" * 60)

        for service_name in self.services.keys():
            current = self.service_versions.get(service_name, "Unknown")
            latest = self.repo_versions.get(service_name, "Unknown")

            if service_name in self.updatable_services:
                status = "🆙 Updatable"
            elif current == "dev":
                status = "📦 Development"
            elif current != "Unknown" and latest != "Unknown":
                status = "✅ Up to date"
            else:
                status = "❓ Unknown"

            print(f"{service_name:<15} {current:<12} {latest:<12} {status:<15}")

        print("\n" + "=" * 60)

        if self.updatable_services:
            print(f"🎯 {len(self.updatable_services)} service(s) can be updated:")
            for service in self.updatable_services:
                current = self.service_versions.get(service, "Unknown")
                latest = self.repo_versions.get(service, "Unknown")
                print(f"   • {service}: {current} -> {latest}")
        else:
            print("✅ All services are up to date!")

    def update_service(self, service_name: str, stack_name: str) -> bool:
        """Update a single service using rebuild.py script."""
        print(f"\n🔄 Updating {service_name}...")

        # Check if rebuild.py exists
        rebuild_script = os.path.join(os.path.dirname(__file__), "rebuild.py")
        if not os.path.exists(rebuild_script):
            print(f"❌ rebuild.py not found at {rebuild_script}")
            return False

        # Get the target version
        target_version = self.repo_versions.get(service_name)
        if not target_version:
            print(f"❌ No target version found for {service_name}")
            return False

        # Run rebuild.py for the service
        # podman = self.command_exists(['podman', 'version'])
        # if podman:
        #     print("   🐳 Using Podman for rebuilding")
        #     command = ["python3", rebuild_script, '-p', '-s', service_name, '-t', stack_name]
        # else:
        #     print("   🐳 Using Docker for rebuilding")
        #     command = ["python3", rebuild_script, '-s', service_name, '-t', stack_name]

        docker = self.command_exists(['docker', 'version'])
        if docker:
            print("   🐳 Using Docker for rebuilding")
            command = ["python3", rebuild_script, '-s', service_name, '-t', stack_name]
        else:
            print("   🐳 Using Podman for rebuilding")
            command = ["python3", rebuild_script, '-p', '-s', service_name, '-t', stack_name]

        print(f"   Running: {' '.join(command)}")
        success, output = self.run_command(command, shell=False, stream_output=True)

        if success:
            print(f"   ✅ Successfully updated {service_name}")
            # Update our local version tracking
            self.service_versions[service_name] = target_version
            if service_name in self.updatable_services:
                self.updatable_services.remove(service_name)

            # Send Slack notification about successful update
            self.send_slack_notification(f"✅ Service *{service_name}* successfully updated to version *{target_version}* in node *##node##*.")

            return True
        else:
            print(f"   ❌ Failed to update {service_name}: {output}")
            return False

    def update_all_services(self, stack_name: str) -> int:
        """Update all updatable services."""
        if not self.updatable_services:
            print("✅ No services need updating!")
            return 0

        print(f"\n🚀 Updating all {len(self.updatable_services)} services...")

        successful_updates = 0
        for service in self.updatable_services.copy():
            if self.update_service(service, stack_name):
                successful_updates += 1
            print()  # Add spacing between updates

        print(f"📊 Update Summary: {successful_updates}/{len(self.updatable_services)} services updated successfully")
        return successful_updates

    def interactive_menu(self):
        """Interactive menu for updating services."""
        while True:
            print("\n" + "=" * 60)
            print("🛠️  INTERACTIVE UPDATE MENU")
            print("=" * 60)

            if not self.updatable_services:
                print("✅ No services need updating!")
                print("\n1. Re-check versions")
                print("2. Exit")
                choice = input("\nEnter your choice (1-2): ").strip()

                if choice == "1":
                    self.__init__()  # Reset state
                    self.check_all_versions()
                    self.display_summary()
                elif choice == "2":
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice!")
                continue

            print("Available actions:")
            print("1. Update all services")
            print("2. Update specific service")
            print("3. Show version summary")
            print("4. Re-check versions")
            print("5. Exit")

            choice = input("\nEnter your choice (1-5): ").strip()

            if choice == "1":
                confirm = input(f"\n⚠️  Update all {len(self.updatable_services)} services? (y/N): ").strip().lower()
                if confirm in ['y', 'yes']:
                    stack_name = input("\n🧱 Enter stack name (default: 'my_stack'): ").strip() or "my_stack"
                    self.update_all_services(stack_name)
                else:
                    print("❌ Update cancelled")

            elif choice == "2":
                print("\nUpdatable services:")
                for i, service in enumerate(self.updatable_services, 1):
                    current = self.service_versions.get(service, "Unknown")
                    latest = self.repo_versions.get(service, "Unknown")
                    print(f"{i}. {service} ({current} -> {latest})")

                try:
                    service_choice = int(input(f"\nSelect service to update (1-{len(self.updatable_services)}): "))
                    if 1 <= service_choice <= len(self.updatable_services):
                        service_name = self.updatable_services[service_choice - 1]
                        confirm = input(f"\n⚠️  Update {service_name}? (y/N): ").strip().lower()
                        if confirm in ['y', 'yes']:
                            stack_name = input("\n🧱 Enter stack name (default: 'my_stack'): ").strip() or "my_stack"
                            self.update_service(service_name, stack_name)
                        else:
                            print("❌ Update cancelled")
                    else:
                        print("❌ Invalid selection!")
                except (ValueError, IndexError):
                    print("❌ Invalid input!")

            elif choice == "3":
                self.display_summary()

            elif choice == "4":
                print("🔄 Re-checking versions...")
                self.__init__()  # Reset state
                self.check_all_versions()
                self.display_summary()

            elif choice == "5":
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice!")


def main():
    """Main entry point."""
    print("🚀 Docker Service Version Checker & Updater")
    print("=" * 60)

    checker = VersionChecker()

    try:
        # Initial version check
        checker.check_all_versions()
        checker.display_summary()

        # Start interactive menu
        checker.interactive_menu()

    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
