#!/usr/bin/env bash
# Pre-flight checks of a VM before deploying an MDDB node. Run from the repo root on the VM.
#
#   preflight.sh [--storage PATH] [--domain NAME] [--compose FILE] [--multipart-test]
#
# Read-only, except --multipart-test: it starts a throwaway MinIO (the image from the compose file) on a
# temporary folder inside --storage, uploads a 100 MB object in parts, and removes the folder.
# Exit code: 0 if no FAIL, 1 otherwise.
set -u

STORAGE=""; DOMAIN=""; COMPOSE="docker-compose.yml"; MPU=0
while [ $# -gt 0 ]; do
  case "$1" in
    --storage) STORAGE="${2:-}"; shift ;;
    --domain) DOMAIN="${2:-}"; shift ;;
    --compose) COMPOSE="${2:-}"; shift ;;
    --multipart-test) MPU=1 ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

NFAIL=0; NWARN=0
ok()   { printf '  OK    %s\n' "$*"; }
info() { printf '  INFO  %s\n' "$*"; }
warn() { printf '  WARN  %s\n' "$*"; NWARN=$((NWARN+1)); }
fail() { printf '  FAIL  %s\n' "$*"; NFAIL=$((NFAIL+1)); }
section() { printf '\n== %s\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }
# free GB of the filesystem holding PATH (walks up to the first existing parent)
free_gb() { local p="$1"; while [ ! -e "$p" ] && [ "$p" != / ]; do p=$(dirname "$p"); done
            df -P -BG "$p" 2>/dev/null | awk 'NR==2{gsub("G","",$4); print $4}'; }

section "System"
[ -r /etc/os-release ] && info "OS: $(. /etc/os-release; echo "$PRETTY_NAME")"
info "CPUs: $(nproc), RAM: $(awk '/MemTotal/{printf "%.0f GB", $2/1048576}' /proc/meminfo)"
if grep -qw avx /proc/cpuinfo; then ok "CPU has AVX (needed by MongoDB 5+)"
else fail "CPU has no AVX: MongoDB 5+ will crash (Illegal instruction). VM admin: CPU type 'host' or 'x86-64-v3', then power-cycle"; fi
mem_gb=$(awk '/MemTotal/{printf "%d", $2/1048576}' /proc/meminfo)
[ "$mem_gb" -lt 15 ] && warn "less than 16 GB of RAM; check the *_MEMORY_LIMIT values in .env"
if have timedatectl; then
  [ "$(timedatectl show -p NTPSynchronized --value 2>/dev/null)" = yes ] && ok "clock synchronised (NTP)" \
    || warn "clock not NTP-synchronised: S3 signatures (MinIO) fail when the clock is off"
fi

section "Docker"
if ! have docker; then
  fail "docker not installed (scripts/docker-deploy.py -d, or the distribution's Docker packages)"
elif ! docker info >/dev/null 2>&1; then
  fail "cannot talk to the Docker daemon as $(id -un): add the user to the 'docker' group, then log in again"
else
  ok "Docker $(docker version -f '{{.Server.Version}}' 2>/dev/null)"
  if docker compose version >/dev/null 2>&1; then ok "$(docker compose version | head -1)"
  else fail "Docker Compose v2 plugin missing ('docker compose')"; fi
  root=$(docker info -f '{{.DockerRootDir}}' 2>/dev/null)
  for p in "$root" /var/lib/containerd; do
    g=$(free_gb "$p")
    if [ -n "$g" ] && [ "$g" -lt 50 ]; then warn "$p: only ${g} GB free; the images need tens of GB"
    else info "$p: ${g:-?} GB free"; fi
  done
  state=$(docker info -f '{{.Swarm.LocalNodeState}}' 2>/dev/null)
  if [ "$state" = active ]; then
    info "Swarm already active; stacks: $(docker stack ls --format '{{.Name}}' 2>/dev/null | tr '\n' ' ')"
    for n in web_network data_network minio_network metrics_network; do
      a=$(docker network inspect -f '{{.Attachable}}' "$n" 2>/dev/null)
      [ "$a" = true ] && ok "network $n exists (attachable)" || info "network $n missing or not attachable (step 6)"
    done
  else
    info "Swarm not initialised yet (step 6)"
  fi
fi

section "Network"
for url in https://github.com https://api.github.com https://registry-1.docker.io/v2/ \
           https://pypi.org/simple/ https://deb.nodesource.com/ https://conda.anaconda.org/; do
  code=$(curl -s -o /dev/null -m 15 -w '%{http_code}' "$url" 2>/dev/null)
  [ "$code" != 000 ] && ok "reach $url ($code)" || fail "cannot reach $url (builds download from it)"
done
if have ip; then
  ifc=$(ip route show default 2>/dev/null | awk '{print $5; exit}')
  hm=$(cat "/sys/class/net/$ifc/mtu" 2>/dev/null); dm=$(cat /sys/class/net/docker0/mtu 2>/dev/null)
  if [ -n "$hm" ] && [ -n "$dm" ] && [ "$hm" -lt "$dm" ]; then
    warn "MTU: $ifc=$hm < docker0=$dm; builds may hang (readme/update.md, Troubleshooting)"
  else info "MTU: ${ifc:-?}=${hm:-?}, docker0=${dm:-n/a}"; fi
fi
if have ss; then
  for p in 80 443 9000; do
    l=$(ss -ltnH "( sport = :$p )" 2>/dev/null | head -1)
    [ -n "$l" ] && warn "port $p already in use on this VM" || ok "port $p free"
  done
fi
for f in firewalld ufw; do
  have systemctl && [ "$(systemctl is-active "$f" 2>/dev/null)" = active ] && \
    info "$f active: allow 443 and the MinIO port (sudo); note Docker-published ports bypass it"
done
if [ -n "$DOMAIN" ]; then
  r=$(getent ahostsv4 "$DOMAIN" 2>/dev/null | awk '{print $1; exit}')
  [ -n "$r" ] && info "$DOMAIN resolves to $r (this VM: $(hostname -I 2>/dev/null | awk '{print $1}'))" \
              || warn "$DOMAIN does not resolve (DNS not set yet?)"
fi

section "Images"
MINIO_IMAGE=""
if [ -r "$COMPOSE" ] && have docker; then
  for img in $(grep -hE '^[[:space:]]+image:' "$COMPOSE" | awk '{print $2}' | grep -vE '_image$' | sort -u); do
    case "$img" in *minio*) MINIO_IMAGE="$img" ;; esac
    if docker image inspect "$img" >/dev/null 2>&1 || docker manifest inspect "$img" >/dev/null 2>&1; then
      ok "image available: $img"
    else fail "image cannot be pulled: $img"; fi
  done
else
  warn "$COMPOSE not found: run from the repo root (or pass --compose)"
fi

if [ -n "$STORAGE" ]; then
  section "Storage: $STORAGE"
  if [ ! -d "$STORAGE" ]; then
    fail "$STORAGE does not exist"
  else
    fs=$(findmnt -no FSTYPE -T "$STORAGE" 2>/dev/null)
    info "filesystem: ${fs:-?}, $(free_gb "$STORAGE") GB free"
    [ -w "$STORAGE" ] && ok "writable by $(id -un)" || info "not writable by $(id -un) (containers run as root; see the multipart test)"
    case "$fs" in
      virtiofs|nfs*|cifs|smb*|fuse*|9p)
        if [ "$MPU" = 1 ]; then info "network/shared filesystem: the multipart test below decides"
        else warn "network/shared filesystem ($fs): run again with --multipart-test before using it for MinIO"; fi ;;
    esac
    if [ "$MPU" = 1 ]; then
      if [ -z "$MINIO_IMAGE" ]; then
        warn "multipart test skipped: no MinIO image found in $COMPOSE"
      else
        d=".mddb-preflight-$$"
        out=$(docker run --rm --entrypoint sh -v "$STORAGE:/s" \
              -e MINIO_ROOT_USER=preflight -e MINIO_ROOT_PASSWORD=preflight-pass-123 "$MINIO_IMAGE" -c '
          for t in minio mc curl; do command -v $t >/dev/null || { echo "NOTOOL $t"; exit 0; }; done
          d=/s/'"$d"'; mkdir -p "$d" || { echo "NOMKDIR"; exit 0; }
          minio server --quiet --address 127.0.0.1:9199 "$d" >/tmp/log 2>&1 & pid=$!
          i=0; until curl -sf http://127.0.0.1:9199/minio/health/live >/dev/null; do
            i=$((i+1)); [ $i -gt 60 ] && break; sleep 1; done
          if mc alias set p http://127.0.0.1:9199 preflight preflight-pass-123 >/dev/null 2>&1 &&
             mc mb p/preflight-bucket >/dev/null 2>&1; then
            head -c 100000000 /dev/urandom > /tmp/f
            if mc cp --quiet /tmp/f p/preflight-bucket/f >/tmp/cp 2>&1; then echo "MPU_OK"
            else echo "MPU_FAIL $(tail -1 /tmp/cp)"; fi
          else echo "NOSERVER $(tail -2 /tmp/log | tr "\n" " ")"; fi
          kill $pid 2>/dev/null; wait $pid 2>/dev/null
          for i in 1 2 3; do rm -rf "$d" 2>/dev/null; [ -e "$d" ] || break; sleep 2; done
          [ -e "$d" ] && echo "LEFTOVER $d" || true' 2>&1)
        case "$out" in
          *MPU_OK*)   ok "multipart upload (100 MB) works on this storage" ;;
          *MPU_FAIL*) fail "multipart upload FAILS on this storage: do not use it for MinIO (${out#*MPU_FAIL })" ;;
          *NOTOOL*)   warn "multipart test skipped: $MINIO_IMAGE lacks ${out#*NOTOOL }" ;;
          *)          fail "multipart test could not run: $(echo "$out" | tail -2 | tr '\n' ' ')" ;;
        esac
        case "$out" in *LEFTOVER*) warn "could not remove $STORAGE/$d; remove it by hand (sudo)" ;; esac
      fi
    fi
  fi
fi

printf '\n%s FAIL, %s WARN\n' "$NFAIL" "$NWARN"
[ "$NFAIL" -eq 0 ]
