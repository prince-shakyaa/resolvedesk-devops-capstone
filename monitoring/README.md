# monitoring/ - Prometheus + Grafana

```text
FastAPI /metrics  <--scrape--  Prometheus (Operator)  <--query--  Grafana
       ^                            ^
       |                            |
 prometheus-fastapi-          ServiceMonitor
 instrumentator               (helm/resolvedesk, label release=kube-prometheus-stack)
```

## Install

```bash
./monitoring/install.sh
```

What it does:

1. Installs `kube-prometheus-stack` into the `monitoring` namespace with `kube-prometheus-stack-values.yaml`.
   The important setting is `serviceMonitorSelectorNilUsesHelmValues: false`, so Prometheus discovers
   ServiceMonitors from *any* namespace (including `resolvedesk`).
2. Loads `dashboards/resolvedesk-dashboard.json` into a ConfigMap labelled `grafana_dashboard=1`; the
   Grafana sidecar imports it automatically.

Make sure the application chart was installed with `monitoring.serviceMonitor.enabled=true`
(already on in `values-dev.yaml` and `values-prod.yaml`).

## Verify

| Check | Command / URL |
|-------|---------------|
| Raw metrics | `kubectl port-forward -n resolvedesk svc/resolvedesk-backend 8000:8000` then `curl localhost:8000/metrics` |
| Prometheus target UP | `kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090` -> http://localhost:9090/targets (look for `resolvedesk-backend`) |
| Grafana dashboard | `kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3002:80` -> http://localhost:3002, login `admin`/`admin`, open **ResolveDesk API** |

Generate traffic so the panels are not empty: `scripts/load-test.sh`.

## Metrics exposed by the backend

| Metric | Type | Used for |
|--------|------|----------|
| `http_requests_total{handler,method,status}` | counter | request rate, error rate |
| `http_request_duration_seconds_bucket` | histogram | p50/p95/p99 latency |
| `http_request_size_bytes`, `http_response_size_bytes` | summary | payload sizes |
| `http_requests_inprogress` | gauge | concurrency |

Useful PromQL:

```promql
sum(rate(http_requests_total{namespace="resolvedesk"}[2m]))                                 # req/s
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))       # p95
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))      # error ratio
```
