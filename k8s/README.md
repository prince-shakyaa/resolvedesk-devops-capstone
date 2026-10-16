# k8s/ - cluster bootstrap

Only cluster-level objects live here. Application objects are owned by the Helm chart in `helm/resolvedesk`.

```bash
kubectl apply -f k8s/namespace.yaml
```

Prerequisites installed per cluster (not per application):

| Component | minikube | EKS |
|-----------|----------|-----|
| Ingress controller | `minikube addons enable ingress` | `helm install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace` |
| Metrics Server (HPA) | `minikube addons enable metrics-server` | `kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml` |
| Prometheus + Grafana | see `monitoring/` | see `monitoring/` |
| EBS CSI driver (PVC) | built-in hostPath | provisioned by Terraform as an EKS add-on |
