#!/bin/sh
# Drop-in replacement for gosu ("gosu user[:group] command [args...]"), which the official
# entrypoint uses to switch from root to the mongodb user. The gosu binary bundled in the
# image is built with an old Go and scanners flag its standard library; setpriv does the same.
set -e
spec="$1"
shift
user="${spec%%:*}"
group="${spec#*:}"
[ "$group" != "$spec" ] || group="$user"
exec setpriv --reuid="$user" --regid="$group" --init-groups "$@"
