# Live demo script

Order follows the rubric's "Final presentation" flow. Each step lists what to show and the command.

| # | Show | Command / action |
|---|------|------------------|
| 1 | **Application** | `docker compose up --build` -> http://localhost:3000. Create a ticket, assign it, add a comment, move it to RESOLVED. |
| 2 | **API** | http://localhost:8000/docs -> run GET/POST/PUT/DELETE on `/api/tickets`. |
| 3 | **Database** | `docker exec resolvedesk-postgres psql -U resolvedesk -c '\dt' -c 'select id,subject,status from tickets;'` |
| 4 | **Tests** | `cd backend && pytest -v` (20 tests, SQLite in memory) |
| 5 | **Git** | `git log --oneline` - conventional, descriptive commits. Make a small change (e.g. a new category) and commit. |
| 6 | **CI** | `git push` -> Actions tab -> watch test, build, validate jobs. |
| 7 | **Docker** | `docker images | grep resolvedesk`; `docker exec resolvedesk-backend id` shows uid 10001. Show the multi-stage `frontend/Dockerfile`. |
| 8 | **Security** | Open the `build-scan-push` job -> Trivy table; Security tab -> Code scanning alerts. Explain one CVE from `docs/SECURITY.md`. |
| 9 | **Registry** | GitHub -> Packages -> `resolvedesk-backend` -> tags: full SHA, `sha-xxxxxxx`, `main`, `latest`. |
| 10 | **Terraform** | `cd terraform && terraform plan` (screenshot). AWS Console: VPC with 4 subnets, EKS cluster, node group. |
| 11 | **Kubernetes** | `kubectl get pods,svc -n resolvedesk` - all Running, 2 replicas each. |
| 12 | **Helm** | `helm list -n resolvedesk`; `helm history resolvedesk -n resolvedesk`; `helm test resolvedesk -n resolvedesk`. |
| 13 | **Ingress** | Open http://resolvedesk.local (minikube) or the EKS hostname. `/docs` also works through the Ingress. |
| 14 | **HPA** | `kubectl get hpa -n resolvedesk -w` in one terminal, `scripts/load-test.sh` in another; replicas climb from 2. |
| 15 | **Monitoring** | Prometheus targets page shows `resolvedesk-backend` UP; Grafana "ResolveDesk API" dashboard with live request rate / latency. |
| 16 | **Troubleshooting** | `kubectl apply -f troubleshooting/02-broken-service.yaml`, show empty endpoints, fix the selector, show endpoints populated. |
| 17 | **Commit -> deploy** | Change the dashboard title in `frontend/src/App.jsx`, push, wait for green, `helm upgrade ... --set image.tag=<new sha>` (or let the deploy job do it), refresh the browser. |
| 18 | **Teardown** | `helm uninstall resolvedesk -n resolvedesk && terraform destroy` - show completion to prove no runaway cost. |

## Local Kubernetes rehearsal (no AWS)

```bash
BUILD_LOCAL=true scripts/minikube-up.sh           # or omit BUILD_LOCAL to pull from GHCR
echo "$(minikube ip) resolvedesk.local" | sudo tee -a /etc/hosts
./monitoring/install.sh
helm upgrade --install resolvedesk helm/resolvedesk -n resolvedesk -f helm/resolvedesk/values-dev.yaml --reuse-values --set monitoring.serviceMonitor.enabled=true
URL=http://resolvedesk.local scripts/load-test.sh
```
