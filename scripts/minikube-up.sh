#!/usr/bin/env bash
# One-shot local Kubernetes environment: minikube + ingress + metrics-server + ResolveDesk.
set -euo pipefail
cd "$(dirname "$0")/.."

TAG="${TAG:-latest}"
IMAGE_PREFIX="${IMAGE_PREFIX:-ghcr.io/prince-shakyaa/resolvedesk}"

minikube status >/dev/null 2>&1 || minikube start --cpus 2 --memory 4g
minikube addons enable ingress
minikube addons enable metrics-server

if [[ "${BUILD_LOCAL:-false}" == "true" ]]; then
  echo "Building images locally and loading into minikube"
  docker build -t "$IMAGE_PREFIX-backend:$TAG" backend
  docker build -t "$IMAGE_PREFIX-frontend:$TAG" frontend
  minikube image load "$IMAGE_PREFIX-backend:$TAG"
  minikube image load "$IMAGE_PREFIX-frontend:$TAG"
fi

kubectl apply -f k8s/namespace.yaml
helm upgrade --install resolvedesk helm/resolvedesk \
  --namespace resolvedesk \
  -f helm/resolvedesk/values-dev.yaml \
  --set image.tag="$TAG" \
  --set monitoring.serviceMonitor.enabled="${SERVICEMONITOR:-false}" \
  --wait --timeout 5m

echo
echo "Add this line to /etc/hosts:  $(minikube ip) resolvedesk.local"
echo "Then open http://resolvedesk.local  (API docs at /docs)"
kubectl get pods,svc,ingress,hpa -n resolvedesk
