#!/usr/bin/env bash
# Where is this node in the MongoDB 6 -> 8 upgrade (readme/mongo-upgrade.md), and what is the next step?
#
#   check.sh --stack NAME
#
# Read-only. Uses the root credentials already set inside the <stack>_mongodb container.
set -u

STACK=""
while [ $# -gt 0 ]; do
  case "$1" in
    --stack) STACK="${2:-}"; shift ;;
    -h|--help) sed -n '2,6p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done
[ -n "$STACK" ] || { sed -n '2,6p' "$0" >&2; exit 2; }
SVC="${STACK}_mongodb"

line() { printf '  %-22s %s\n' "$1" "$2"; }
docker service inspect "$SVC" >/dev/null 2>&1 || { echo "service $SVC not found" >&2; exit 1; }

image=$(docker service inspect "$SVC" -f '{{.Spec.TaskTemplate.ContainerSpec.Image}}' | cut -d@ -f1)
# stop grace period in nanoseconds ("null" when not set: Docker's default, 10 s)
grace=$(docker service inspect "$SVC" -f '{{json .Spec.TaskTemplate.ContainerSpec.StopGracePeriod}}')
case "$grace" in ''|null) grace=0 ;; esac
replicas=$(docker service inspect "$SVC" -f '{{if .Spec.Mode.Replicated}}{{.Spec.Mode.Replicated.Replicas}}{{end}}')
volume=$(docker service inspect "$SVC" -f '{{range .Spec.TaskTemplate.ContainerSpec.Mounts}}{{if eq .Target "/data/db"}}{{.Source}}{{end}}{{end}}')
case "$volume" in /*) path="$volume" ;; *) path=$(docker volume inspect "${volume}" -f '{{index .Options "device"}}' 2>/dev/null) ;; esac

echo "== $SVC"
line "image" "$image"
line "replicas" "${replicas:-?}"
line "stop grace period" "$([ "$grace" -eq 0 ] && echo "default (10s)" || echo "$((grace / 1000000000))s")"
line "data folder" "${path:-?}"
if [ -n "$path" ] && [ -e "$path" ]; then
  line "free space there" "$(df -h --output=avail "$path" 2>/dev/null | tail -1 | tr -d ' ')"
fi

cid=$(docker ps -q -f label=com.docker.swarm.service.name="$SVC" | head -1)
if [ -z "$cid" ]; then
  echo; echo "mongod is not running (replicas ${replicas:-?}): version and FCV cannot be read."
  echo "If you are at step 2 (backup), that is expected. Otherwise check: docker service ps $SVC --no-trunc"
  exit 0
fi

ev() { docker exec "$cid" sh -c 'mongosh --quiet -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --eval "$0"' "$1" 2>&1 | tail -1; }
ver=$(ev 'db.version()')
fcv=$(ev 'db.adminCommand({getParameter: 1, featureCompatibilityVersion: 1}).featureCompatibilityVersion.version')
size=$(ev 'Math.round(db.adminCommand({listDatabases: 1}).totalSize / 1e9 * 10) / 10')
unclean=$(docker logs "$cid" 2>&1 | grep -c 'Detected unclean shutdown')
line "mongod version" "$ver"
line "FCV" "$fcv"
line "size on disk" "${size} GB"
line "last start" "$([ "$unclean" -gt 0 ] && echo "after an UNCLEAN shutdown (recovered)" || echo "clean")"

case "$ver" in [0-9]*) ;; *) echo; echo "Could not query mongod: $ver"; exit 1 ;; esac
major="${ver%%.*}"

echo; echo "== Next step (readme/mongo-upgrade.md)"
case "$major/$fcv" in
  6/5.0) echo "  Raise the FCV to 6.0 first: setFeatureCompatibilityVersion \"6.0\" (step 0)" ;;
  6/6.0) echo "  Steps 1-2: stop the services, raise the grace period, stop mongod and BACK IT UP; then step 3 (mongo:7.0)" ;;
  7/6.0) echo "  Step 3: check version/counts/clean shutdown, then FCV 7.0 (confirm: true) - IRREVERSIBLE without the backup" ;;
  7/7.0) echo "  Step 4: docker service update --image mongo:8.0 $SVC" ;;
  8/7.0) echo "  Steps 5-6: services back and trial period; when satisfied, step 7: FCV 8.0 (confirm: true) - IRREVERSIBLE without the backup" ;;
  8/8.0) echo "  Upgrade finished. Step 8: back to the normal 'docker stack deploy' (and delete any mongo-pin.yml)" ;;
  *)     echo "  Unexpected combination (version $ver, FCV $fcv): stop and read the guide's 'If something goes wrong'" ;;
esac
if [ "$major" -lt 8 ] || [ "$fcv" != 8.0 ]; then
  [ "$grace" -lt 300000000000 ] && echo "  Before restarting mongod: docker service update --stop-grace-period 30m $SVC"
fi
exit 0
