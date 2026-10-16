# Architecture

## Request flow

```text
Browser ──HTTP──> Ingress (nginx)  host: resolvedesk.local
                    │  /api, /docs, /openapi.json
                    ├──────────────> Service resolvedesk-backend:8000 ──> backend pods (FastAPI)
                    │  /                                                         │
                    └──────────────> Service resolvedesk-frontend:80 ──> frontend pods (nginx)
                                                                         │ /api/* proxied via BACKEND_URL
                                                                         └──> resolvedesk-backend:8000
backend pods ──SQL──> Service resolvedesk-postgres:5432 (headless) ──> StatefulSet pod ──> PVC
```

Two paths reach the API on purpose:

- **Through the Ingress** (`/api` rule) - the normal production path, short and cacheable.
- **Through the frontend's Nginx** (`location /api/`) - lets the exact same image work with Docker
  Compose (no Ingress) and in Kubernetes. The upstream is injected at container start by `envsubst`
  from `BACKEND_URL`, so no rebuild is needed between environments.

## Why each component exists

| Component | Reason |
|-----------|--------|
| `/health` vs `/ready` | Liveness answers "is the process alive?"; readiness answers "can it serve traffic?" and checks the database. Kubernetes restarts on liveness failure but only stops routing on readiness failure. |
| Alembic in the entrypoint | The schema is versioned with the code; every image applies its own migrations on boot, so a rollback to an older image is explicit rather than silent drift. |
| Non-root containers | Backend runs as uid 10001, frontend as uid 101 (`nginx-unprivileged`). The chart adds `runAsNonRoot`, drops all capabilities and disables privilege escalation. |
| Commit-SHA image tags | `ghcr.io/.../resolvedesk-backend:<sha>` maps every running pod to the exact commit that built it. `latest` is published for convenience only. |
| Trivy gate before push | A vulnerable image never reaches the registry, so it can never be deployed by mistake. |
| StatefulSet for PostgreSQL | Stable network identity and a `volumeClaimTemplate`; fine for a classroom cluster. For production, flip `postgres.enabled=false` and point `externalDatabaseUrl` at Amazon RDS. |
| HPA on the backend only | The API does the work; the frontend is static files. Backend `replicas` is omitted when the HPA is on so Helm upgrades do not fight the autoscaler. |
| ServiceMonitor | Declarative scrape config: the Prometheus Operator discovers the backend Service by label instead of hand-editing `prometheus.yml`. |
| Terraform modules | `terraform-aws-modules/vpc` and `/eks` encode AWS best practices (subnet tagging, IAM, access entries) so the repo stays focused on intent. |

## Environments

| | Docker Compose | minikube (`values-dev.yaml`) | EKS (`values-prod.yaml`) |
|---|---|---|---|
| Images | built locally | GHCR or `BUILD_LOCAL=true` | GHCR (`image.tag=<sha>` from CI) |
| Database | container + named volume | StatefulSet, 1Gi PVC | StatefulSet, 10Gi gp2 PVC (or RDS) |
| Entry point | `localhost:3000` | Ingress `resolvedesk.local` | Ingress + AWS NLB/ALB |
| Autoscaling | - | HPA 2-4 | HPA 2-8 |
| Monitoring | `/metrics` only | kube-prometheus-stack | kube-prometheus-stack |

## Data model

```text
tickets                          ticket_comments
───────                          ───────────────
id            PK                 id          PK
subject                          ticket_id   FK -> tickets.id (ON DELETE CASCADE)
description                      author
category      SOFTWARE|...       body
priority      LOW|...|URGENT     created_at
status        OPEN|...|CLOSED  (indexed)
requester
assignee      nullable
created_at / updated_at
resolved_at   set when status -> RESOLVED/CLOSED
```
