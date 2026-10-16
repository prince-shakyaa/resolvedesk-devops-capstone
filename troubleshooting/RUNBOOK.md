# Troubleshooting runbook

Four deliberately broken manifests live in this folder. Apply one, diagnose it with the commands
below, then clean up with `kubectl delete -f <file>`.

Universal first steps:

```bash
kubectl get pods -n resolvedesk                      # what state is it in?
kubectl describe pod <pod> -n resolvedesk            # Events section at the bottom
kubectl logs <pod> -n resolvedesk --previous         # logs from the crashed container
kubectl get events -n resolvedesk --sort-by=.lastTimestamp
```

| # | File | Pod state | Diagnose | Root cause | Fix |
|---|------|-----------|----------|------------|-----|
| 1 | `01-broken-image.yaml` | `ImagePullBackOff` | `describe pod` -> `Failed to pull image ... manifest unknown` | Image tag does not exist | Use a tag that CI pushed (git SHA or `latest`); check `imagePullSecrets` if the package is private |
| 2 | `02-broken-service.yaml` | pods fine, Service has **no endpoints** | `kubectl get endpoints broken-service -n resolvedesk` shows `<none>`; compare `kubectl get pods --show-labels` with `spec.selector` | Selector typo (`backnd`) matches no pods | Correct the selector labels |
| 3 | `03-broken-readiness.yaml` | `Running` but `0/1 READY` | `describe pod` -> `Readiness probe failed: HTTP probe failed with statuscode: 404` | Probe path wrong | Point the probe at `/healthz` (frontend) or `/ready` (backend) |
| 4 | `04-broken-config.yaml` | `CrashLoopBackOff` | `kubectl logs <pod>` -> `could not translate host name "no-such-postgres"` | Wrong `DATABASE_URL` | Fix the host (`resolvedesk-postgres`), or restore the Secret the chart generates |

## Worked example: broken Service

```bash
kubectl apply -f troubleshooting/02-broken-service.yaml
kubectl get svc,endpoints broken-service -n resolvedesk
# NAME                     ENDPOINTS   <- empty
kubectl get pods -n resolvedesk --show-labels | grep backend
# ... app.kubernetes.io/component=backend ...
kubectl get svc broken-service -n resolvedesk -o jsonpath='{.spec.selector}'
# {"app.kubernetes.io/component":"backnd", ...}   <- mismatch
kubectl patch svc broken-service -n resolvedesk -p '{"spec":{"selector":{"app.kubernetes.io/name":"resolvedesk","app.kubernetes.io/component":"backend"}}}'
kubectl get endpoints broken-service -n resolvedesk
# now lists the backend pod IPs
kubectl delete -f troubleshooting/02-broken-service.yaml
```

## Other things that go wrong in this project

| Symptom | Likely cause | Check |
|---------|--------------|-------|
| Backend `0/1 Ready`, `/ready` returns 503 | PostgreSQL not up yet or wrong credentials | `kubectl logs sts/resolvedesk-postgres`, `kubectl get secret resolvedesk-backend -o yaml` |
| PostgreSQL pod `Pending` | No default StorageClass / EBS CSI driver missing | `kubectl get pvc -n resolvedesk`, `kubectl get sc` |
| Frontend shows "Backend unavailable" | `BACKEND_URL` env does not resolve | `kubectl exec deploy/resolvedesk-frontend -- cat /etc/nginx/conf.d/default.conf` |
| Ingress returns 404 | No ingress controller or wrong `ingressClassName` | `kubectl get ingressclass`, `kubectl get ingress -n resolvedesk` |
| HPA shows `<unknown>` CPU | Metrics Server not installed | `kubectl top pods -n resolvedesk` |
| Prometheus target missing | ServiceMonitor label does not match the release | `kubectl get servicemonitor -A -o yaml \| grep release` |
| CI Trivy gate fails | New CVE in a base image or dependency | Read the table in the job log; bump the package or base image |
