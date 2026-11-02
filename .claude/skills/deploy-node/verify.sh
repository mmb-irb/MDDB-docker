#!/usr/bin/env bash
# Verify a deployed MDDB stack from the VM it runs on. Read-only.
#
#   verify.sh --stack NAME --domain NAME [--env FILE]
#
# The endpoints are requested through Apache on this VM (curl --resolve <domain>:<port>:127.0.0.1), so it
# works before the public DNS points here. Exit code: 0 if no FAIL, 1 otherwise.
set -u

STACK=""; DOMAIN=""; ENV_FILE=".env"
while [ $# -gt 0 ]; do
  case "$1" in
    --stack) STACK="${2:-}"; shift ;;
    --domain) DOMAIN="${2:-}"; shift ;;
    --env) ENV_FILE="${2:-}"; shift ;;
    -h|--help) sed -n '2,7p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done
[ -n "$STACK" ] && [ -n "$DOMAIN" ] || { sed -n '2,7p' "$0" >&2; exit 2; }

NFAIL=0; NWARN=0
ok()   { printf '  OK    %s\n' "$*"; }
info() { printf '  INFO  %s\n' "$*"; }
warn() { printf '  WARN  %s\n' "$*"; NWARN=$((NWARN+1)); }
fail() { printf '  FAIL  %s\n' "$*"; NFAIL=$((NFAIL+1)); }
section() { printf '\n== %s\n' "$*"; }
# value of a variable in the env file, without sourcing it
val() { [ -r "$ENV_FILE" ] && sed -n "s/^$1=//p" "$ENV_FILE" | tail -1 | tr -d "'\"[:space:]"; }

HTTPS_PORT=$(val APACHE_HTTPS_OUTER_PORT); HTTPS_PORT=${HTTPS_PORT:-443}
MINIO_PORT=$(val APACHE_MINIO_OUTER_PORT); MINIO_PORT=${MINIO_PORT:-9000}
[ -r "$ENV_FILE" ] || warn "$ENV_FILE not readable: assuming ports 443 and 9000"

section "Services of stack '$STACK'"
svcs=$(docker stack services "$STACK" --format '{{.Name}} {{.Replicas}}' 2>/dev/null)
if [ -z "$svcs" ]; then fail "no services found for stack '$STACK'"; fi
echo "$svcs" | while read -r name rep; do
  [ -z "$name" ] && continue
  have=${rep%%/*}; want=${rep#*/}; want=${want%% *}
  if [ "$have" = "$want" ]; then printf '  OK    %-32s %s\n' "$name" "$rep"
  else printf '  FAIL  %-32s %s\n' "$name" "$rep"; fi
done
NFAIL=$((NFAIL + $(echo "$svcs" | awk '{split($2,a,"/"); split(a[2],b," "); if (a[1]!=b[1]) n++} END{print n+0}')))
docker stack ps "$STACK" --no-trunc --format '{{.Name}}|{{.CurrentState}}|{{.Error}}' 2>/dev/null \
  | grep -E '\|(Rejected|Failed)' | awk -F'|' '!seen[$1]++' | head -5 | while IFS='|' read -r n s e; do
    printf '  INFO  recent task problem: %s: %s\n' "$n" "${e:-$s}"; done

section "Initialisation"
if docker service inspect "${STACK}_mongodb" >/dev/null 2>&1; then
  u=$(docker service logs "${STACK}_mongodb" 2>&1 | grep -oE "Successfully created user '[^']+'|User '[^']+' already exists" | sort -u | tr '\n' ' ')
  [ -n "$u" ] && ok "mongodb users: $u" || warn "no user creation found in ${STACK}_mongodb logs (mongo-init.js ran?)"
  docker service logs "${STACK}_mongodb" 2>&1 | grep -q 'Illegal instruction' && \
    fail "mongodb crashed with 'Illegal instruction': the CPU lacks AVX (troubleshooting.md)"
fi
if docker service inspect "${STACK}_minio" >/dev/null 2>&1; then
  docker service logs "${STACK}_minio" 2>&1 | grep -q 'Policy set for the new user' \
    && ok "minio initialised (user and policy created)" \
    || warn "minio initialisation not finished (no 'Policy set' in its logs)"
fi

section "Endpoints through Apache on this VM ($DOMAIN)"
code() { curl -s -o /dev/null -m 20 -w '%{http_code}' --resolve "$DOMAIN:$1:127.0.0.1" "https://$DOMAIN:$1$2" 2>/dev/null; }
for path in / /vre_lite/ /minio/; do
  c=$(code "$HTTPS_PORT" "$path")
  [ "$c" = 200 ] && ok "https $path -> $c" || fail "https $path -> $c"
done
body=$(curl -s -m 20 --resolve "$DOMAIN:$HTTPS_PORT:127.0.0.1" "https://$DOMAIN:$HTTPS_PORT/api/rest/v1/projects?limit=1" 2>/dev/null)
case "$body" in
  *'"projects"'*) ok "REST /api/rest/v1/projects answers ($(echo "$body" | grep -oE '"filteredCount":[0-9]+' || echo 'no count'))" ;;
  *)
    if docker service logs --since 30m "${STACK}_rest" 2>&1 | grep -qE 'No client|ENOTFOUND|connection error'; then
      fail "REST has no database connection: when mongodb is 1/1, run: docker service update --force ${STACK}_rest"
    else fail "REST /api/rest/v1/projects did not return projects: $(echo "$body" | head -c 120)"; fi ;;
esac
c=$(code "$MINIO_PORT" /minio/health/live)
[ "$c" = 200 ] && ok "MinIO API :$MINIO_PORT /minio/health/live -> $c" || fail "MinIO API :$MINIO_PORT /minio/health/live -> $c"
c=$(curl -s -o /dev/null -m 10 -w '%{http_code} %{redirect_url}' --resolve "$DOMAIN:80:127.0.0.1" "http://$DOMAIN/" 2>/dev/null)
info "http :80 -> $c"

section "Certificate served on :$HTTPS_PORT"
cert=$(echo | openssl s_client -connect "127.0.0.1:$HTTPS_PORT" -servername "$DOMAIN" 2>/dev/null | openssl x509 -noout -subject -enddate -ext subjectAltName 2>/dev/null)
if [ -z "$cert" ]; then fail "no certificate served on 127.0.0.1:$HTTPS_PORT"
else
  info "$(echo "$cert" | grep -E 'subject=' | sed 's/^ *//')"
  info "SAN: $(echo "$cert" | grep -A1 'Subject Alternative Name' | tail -1 | sed 's/^ *//')"
  end=$(echo "$cert" | sed -n 's/^notAfter=//p')
  if curl -s -o /dev/null -m 10 --resolve "$DOMAIN:$HTTPS_PORT:127.0.0.1" "https://$DOMAIN:$HTTPS_PORT/" 2>/dev/null; then
    ok "certificate valid for $DOMAIN (chain and name verified)"
  else fail "certificate does not verify for $DOMAIN (wrong name, expired, or chain file without intermediates)"; fi
  if echo | openssl s_client -connect "127.0.0.1:$HTTPS_PORT" -servername "$DOMAIN" 2>/dev/null \
       | openssl x509 -noout -checkend $((30*86400)) >/dev/null 2>&1; then
    ok "expires $end"
  else warn "expires $end: less than 30 days left"; fi
fi

printf '\n%s FAIL, %s WARN\n' "$NFAIL" "$NWARN"
[ "$NFAIL" -eq 0 ]
