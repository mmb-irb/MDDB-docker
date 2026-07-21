#!/bin/sh
# Prometheus container entrypoint.
# Selects local (central backend) or remote (node agent) mode from PROMETHEUS_MODE,
# substitutes __UPPER__ tokens that Prometheus cannot expand itself, and execs the daemon.
set -e

case "${PROMETHEUS_MODE}" in
  local)
    # Copy the blackbox scrape job into the include dir only when the exporter is running.
    # scrape_config_files in prometheus-local.yml points at this dir; an empty dir means
    # the job is simply absent rather than permanently DOWN.
    mkdir -p /tmp/prometheus/scrape_configs
    if [ "${BLACKBOX_REPLICAS:-0}" != "0" ]; then
      cp /etc/prometheus/prometheus-blackbox.yml /tmp/prometheus/scrape_configs/blackbox.yml
    fi

    exec /bin/prometheus \
      --config.file=/etc/prometheus/prometheus-local.yml \
      --storage.tsdb.path=/prometheus \
      --storage.tsdb.retention.size=10GB \
      --storage.tsdb.retention.time=30d \
      --web.console.libraries=/etc/prometheus/console_libraries \
      --web.console.templates=/etc/prometheus/consoles \
      --web.enable-lifecycle \
      --enable-feature=expand-external-labels \
      --web.enable-remote-write-receiver
    ;;

  remote)
    # Substitute the remote_write URL and credentials into the node config.
    sed -e "s|__PROM_URL__|${PROM_URL}|g" \
        -e "s|__PROM_USER__|${PROM_USER}|g" \
        -e "s|__PROM_PASS__|${PROM_PASS}|g" \
        /etc/prometheus/prometheus-remote.yml > /tmp/prometheus.yml

    exec /bin/prometheus \
      --config.file=/tmp/prometheus.yml \
      --storage.tsdb.path=/prometheus \
      --storage.tsdb.retention.size=5GB \
      --storage.tsdb.retention.time=15d \
      --web.console.libraries=/etc/prometheus/console_libraries \
      --web.console.templates=/etc/prometheus/consoles \
      --web.enable-lifecycle \
      --enable-feature=expand-external-labels
    ;;

  *)
    echo "Invalid PROMETHEUS_MODE: '${PROMETHEUS_MODE}' (use 'local' or 'remote')" >&2
    exit 1
    ;;
esac
