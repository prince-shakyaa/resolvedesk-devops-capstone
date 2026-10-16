#!/usr/bin/env bash
# Install Prometheus + Grafana (kube-prometheus-stack) and the ResolveDesk dashboard.
set -euo pipefail
cd "$(dirname "$0")"

NS="${MONITORING_NAMESPACE:-monitoring}"

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo update >/dev/null

helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace "$NS" --create-namespace \
  -f kube-prometheus-stack-values.yaml \
  --wait --timeout 10m

# Grafana's sidecar imports any ConfigMap labelled grafana_dashboard=1.
kubectl create configmap resolvedesk-dashboard \
  --namespace "$NS" \
  --from-file=resolvedesk-dashboard.json=dashboards/resolvedesk-dashboard.json \
  --dry-run=client -o yaml | kubectl label --local -f - grafana_dashboard=1 -o yaml | kubectl apply -f -

cat <<MSG

Prometheus:  kubectl port-forward -n $NS svc/kube-prometheus-stack-prometheus 9090:9090  -> http://localhost:9090/targets
Grafana:     kubectl port-forward -n $NS svc/kube-prometheus-stack-grafana 3002:80       -> http://localhost:3002 (admin / admin)
Dashboard:   Dashboards -> "ResolveDesk API"
MSG
