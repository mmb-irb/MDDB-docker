
# Monitoring Stack Overview

This monitoring stack collects **API logs** and **infrastructure metrics** for visualization in Grafana.

The stack is split into two **extensions**, run from the repo root and overlaid on the main [`docker-compose.yml`](../docker-compose.yml):

| Extension | Config folder | Services | Where to deploy |
|-----------|---------------|----------|-----------------|
| [`extensions/grafana.yml`](../extensions/grafana.yml) | [`metrics/grafana/`](grafana/) | OpenTelemetry Collector, Loki, Grafana | Central monitoring host only |
| [`extensions/metrics.yml`](../extensions/metrics.yml) | [`metrics/exporters/`](exporters/) | Prometheus, node-exporter, cAdvisor, blackbox-exporter | Every node (including central) |

## Grafana Stack Components (Central)

| Component         | Role                                      | How it's monitored           |
|-------------------|-------------------------------------------|------------------------------|
| OpenTelemetry     | Receives logs from all nodes, forwards to Loki | Metrics via Prometheus   |
| Loki              | Stores and serves logs (all nodes)         | Metrics via Prometheus       |
| Grafana           | Visualizes logs (Loki) and metrics (Prometheus) | -                       |

## Exporter Components (per node, also run on central)

| Component    | Role                                      |
|--------------|-------------------------------------------|
| REST API (nodes) | Sends logs to OpenTelemetry Collector  |
| Prometheus       | Scrapes local exporters; `remote` mode remote_writes to central Prometheus, `local` mode acts as the central backend |
| node-exporter    | Host hardware/OS metrics               |
| cAdvisor         | Container metrics                      |
| blackbox-exporter | HTTP probing of node endpoints        |

## Architecture

- The monitoring services run on a dedicated external Docker network named `metrics_network`. The REST API and Apache join the same network, so they can send logs directly to the OpenTelemetry Collector container by name.

| web_network  | Both           |  metrics_network |
|--------------|----------------|------------------|
| MDDB stack | REST API, Apache | Monitoring stack |

- **API Logs:**  
   The REST API sends logs directly to the shared [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/) over the `REST_OTEL_ENDPOINT`, which forwards them to a central [Loki](https://grafana.com/oss/loki/) instance.
- **Infrastructure Metrics:**  
   [Prometheus](https://prometheus.io/) scrapes metrics from:
   - **Loki** (log system health)
   - **node-exporter** (host hardware/OS metrics)
   - **Prometheus itself**
   - **cAdvisor** (container metrics)
   - **blackbox-exporter** (HTTP endpoint probing)
- **Visualization:**  
   [Grafana](https://grafana.com/) connects to both Loki (for logs) and Prometheus (for metrics).

```
------------------- Node ----------------------   ------------------ Central ---------------------
                   REST API ──────────────────────► OTel Collector ───► Loki ────────┐
node-exporter (host metrics) ─┐                                                      ├──► Grafana
                              ├─ Prometheus ──────────────────────────► Prometheus ──┘
cAdvisor (container metrics) ─┘ (remote_write)
```

## Setup

All commands are run from the **repo root** and overlay the extension on the main `docker-compose.yml`, as with any other extension.

1. **Configure the environment variables.** The metrics variables live in the [`.env.metrics.git`](../.env.metrics.git) template — copy them into the root `.env` (alongside the core and other extension variables) and adjust the values:

| Variable | Default | Purpose | Example |
|----------|---------|---------|---------|
| `PROMETHEUS_MODE` | `remote` | `remote` = remote_write to central Prometheus; `local` = act as the central backend | `remote` or `local` |
| `BLACKBOX_REPLICAS` | `0` | Optional blackbox exporter (HTTP probing): `0` = not deployed, `1` = deployed | `0` or `1` |
| `PROM_URL` | `http://monitoring-central:9090/api/v1/write` | `remote` mode only: central Prometheus remote_write endpoint the node pushes to (see the Apache receiver below) | `https://central.mddbr.eu/prometheus/api/v1/write` |
| `PROM_USER` | _(none)_ | basic_auth username for remote_write: sent by nodes, validated by Apache on the central host | `mddb_nodes` |
| `PROM_PASS` | _(none)_ | basic_auth password: sent by nodes (injected into prometheus-remote.yml); Apache generates its htpasswd file from this at startup | `s3cret` |
| `REST_OTEL_ENDPOINT` | `http://otel-collector:4318/v1/logs` | REST API logs destination (OTLP/HTTP endpoint) | `http://central-ip:4318/v1/logs` |
| `GF_AUTH_GOOGLE_*` | disabled | Grafana Google OAuth (central host only) | see template |
| `GF_SMTP_*` | disabled | Grafana SMTP for alert emails (central host only) | see template |

2. **Create the metrics network** (once, on every host):
    ```bash
    docker network create metrics_network 2>/dev/null
    ```

### Central Machine (Monitoring Host)

Runs both the Grafana stack (visualization) and the exporter stack in `local` Prometheus mode (acts as the central metrics backend).

1. Set `PROMETHEUS_MODE=local` in the root `.env` and fill in the `GF_*` values.
2. **Set the remote_write credentials.** Set `PROM_USER` and `PROM_PASS` in the root `.env`, then generate `apache/prometheus.htpasswd` (mounted as a volume into Apache — no image rebuild needed when rotating credentials):
    ```bash
    htpasswd -nb "${PROM_USER}" "${PROM_PASS}" > apache/prometheus.htpasswd
    ```
    Apache enforces basic_auth on `/prometheus/api/v1/write` using this file. Prometheus itself runs without auth — Grafana and local `curl` reach port 9090 freely.
3. **Start the stacks:**
    ```bash
    set -a; source .env; set +a
    docker stack deploy -c docker-compose.yml -c extensions/grafana.yml -c extensions/metrics.yml my_stack
    ```

### Per-Node Setup

Runs only the exporter stack in `remote` Prometheus mode, forwarding metrics to the central Prometheus via remote_write.

1. Set `PROMETHEUS_MODE=remote` in the root `.env`. The `NODE` variable is also used so metrics are differentiated per node in Grafana.
2. Point `remote_write` at your central host by setting `PROM_URL` in the root `.env`.
3. Set the remote_write credentials `PROM_USER` / `PROM_PASS` in the root `.env` to match the user configured on the central host (step 2 of the Central setup). All three tokens (`PROM_URL`, `PROM_USER`, `PROM_PASS`) are substituted into the config at container start.
4. **Start the exporter stack** on each node:
    ```bash
    set -a; source .env; set +a
    docker stack deploy -c docker-compose.yml -c extensions/metrics.yml my_stack
    ```
---

## Useful Commands

```bash
# Check Prometheus targets (Loki, node-exporter, cAdvisor, blackbox, itself):
curl http://127.0.0.1:9090/api/v1/targets | jq '.data.activeTargets'

# Check Loki health:
curl http://127.0.0.1:3100/ready

# Check Prometheus disk usage:
docker exec -it prometheus du -sh /prometheus

# Check logs for errors:
docker logs prometheus 2>&1 | grep -i "error"
docker logs loki 2>&1 | grep -i "error"
docker logs otel-collector 2>&1 | grep -i "error"

# Checks the services are running:
docker stack services my_stack

# Update service
docker service update --force my_stack_prometheus
```
