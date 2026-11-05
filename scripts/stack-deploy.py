#!/usr/bin/env python3
"""Redeploy the stack without losing settings made by hand.

    python3 scripts/stack-deploy.py -t my_stack [-c docker-compose.yml -c extensions/mcp.yml ...]

1. Shows what the deploy would change in the running services (scripts/stack-diff.py), with the same
   compose files the deploy uses: the -c files (default docker-compose.yml) plus the node's own file,
   docker-compose.node.yml, when it exists.
2. If something would change, asks before deploying (--yes to skip the question; without a terminal
   and without --yes it stops). REMOVE lines are settings that exist only in the running service:
   put them in docker-compose.node.yml first (the comparison prints the YAML), or they are lost.
3. Runs 'docker stack deploy' with those files and the .env variables, and compares again: after the
   deploy no running service should differ from the compose files.
"""

import argparse
import importlib.util
import os
import subprocess
import sys

here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("stack_diff", os.path.join(here, "stack-diff.py"))
stack_diff = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stack_diff)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    stack_diff.add_arguments(parser)
    parser.add_argument("-y", "--yes", action="store_true", help="deploy even if running services would change")
    parser.add_argument("--prune", action="store_true", help="also remove running services that are in no compose file")
    args = parser.parse_args()
    files = stack_diff.compose_files(args.files, not args.no_node_file)
    stack_diff.check_files(files, args.env_file)

    print("== What the deploy would change\n")
    changed = stack_diff.diff(args.stack, files, args.env_file)
    if changed and not args.yes:
        if not sys.stdin.isatty():
            sys.exit("\nStopped: running services would change. Check the list above; use --yes to deploy anyway.")
        answer = input(f"\n{changed} running service(s) would change (see above). Deploy anyway? [y/N] ")
        if answer.strip().lower() not in ("y", "yes", "s", "si", "sí"):
            sys.exit("Not deployed.")

    print("\n== docker stack deploy\n")
    deploy = " ".join(f"-c {stack_diff.sh_quote(f)}" for f in files)
    prune = " --prune" if args.prune else ""
    cmd = (f"set -a && source {stack_diff.sh_quote(args.env_file)} && set +a && "
           f"exec docker stack deploy{prune} {deploy} {stack_diff.sh_quote(args.stack)}")
    subprocess.run(["bash", "-c", cmd], check=True)

    print("\n== After the deploy\n")
    if stack_diff.diff(args.stack, files, args.env_file, suggest=False):
        sys.exit("Error: some running services still differ from the compose files (see above).")


if __name__ == "__main__":
    main()
