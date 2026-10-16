# ResolveDesk - IT Helpdesk Ticketing (DevOps Capstone)

[![CI/CD](https://github.com/prince-shakyaa/resolvedesk-devops-capstone/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/prince-shakyaa/resolvedesk-devops-capstone/actions/workflows/ci-cd.yml)

ResolveDesk is a small but complete IT helpdesk: employees raise tickets, agents triage, assign,
comment on and resolve them, and a dashboard shows the queue at a glance. The application exists to
exercise a full DevOps delivery path:

```text
developer laptop
   │  git push
   ▼
GitHub Actions ── pytest + ruff ── vite build ── helm lint / terraform validate
   │
   ├── docker build (backend, frontend)
   ├── Trivy scan  ── HIGH/CRITICAL => pipeline fails, nothing is pushed
   └── push to GHCR tagged with the git commit SHA
            │
            ▼
Terraform ── AWS VPC (2 public + 2 private subnets) ── EKS + managed nodes
            │
            ▼
Helm ── Namespace ── Deployments (2+ replicas) ── ClusterIP Services ── Ingress ── HPA
            │
            ▼
Prometheus (ServiceMonitor -> /metrics) ── Grafana dashboard
```

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + Vite, served by unprivileged Nginx (also proxies `/api`) |
| Backend | FastAPI, SQLAlchemy 2, Alembic migrations, Prometheus instrumentator |
| Database | PostgreSQL 16 (StatefulSet + PVC in-cluster; RDS-ready via `externalDatabaseUrl`) |
| Tests | pytest (20 tests, in-memory SQLite, dependency-injected session) |
| Containers | Multi-stage Dockerfiles, non-root users, healthchecks, Docker Compose |
| CI/CD | GitHub Actions: test -> build -> Trivy -> GHCR (SHA tags) -> Helm deploy |
| Security | Trivy image scanning with a HIGH/CRITICAL gate + SARIF to the Security tab, Dependabot |
| Infrastructure | Terraform: VPC, EKS 1.31, managed node group, EBS CSI (IRSA) |
| Kubernetes | Helm chart: Deployments, Services, Ingress, HPA, ServiceMonitor, helm test |
| Observability | kube-prometheus-stack + custom Grafana dashboard |

## Repository layout

```text
.
├── backend/                 FastAPI app, Alembic migrations, pytest suite, Dockerfile
├── frontend/                React/Vite SPA, Nginx config template, Dockerfile
├── docker-compose.yml       Full local stack (postgres + backend + frontend)
├── .github/workflows/       ci-cd.yml (main pipeline), terraform.yml (manual plan/apply/destroy)
├── terraform/               AWS VPC + EKS as code
├── k8s/                     Namespace and cluster-prerequisite notes
├── helm/resolvedesk/        Helm chart with values-dev.yaml (minikube) and values-prod.yaml (EKS)
├── monitoring/              kube-prometheus-stack values, Grafana dashboard, install script
├── troubleshooting/         Deliberately broken manifests + RUNBOOK.md
├── scripts/                 minikube-up.sh, load-test.sh, smoke-test.sh
└── docs/                    Architecture, security notes, demo script, submission checklist
```

## Run it locally (Docker Compose)

```bash
docker compose up --build
```

| URL | What |
|-----|------|
| http://localhost:3000 | ResolveDesk UI |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/health, `/ready`, `/metrics` | probes and Prometheus metrics |

Host ports clash with something? `BACKEND_PORT=8001 FRONTEND_PORT=3001 docker compose up`.
Stop with `docker compose down` (add `-v` to drop the database volume).

### Without Docker

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL=postgresql+psycopg://resolvedesk:resolvedesk@localhost:5432/resolvedesk
alembic upgrade head
uvicorn app.main:app --reload            # http://localhost:8000/docs

cd ../frontend && npm ci && npm run dev  # http://localhost:5173 (proxies /api to :8000)
```

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | liveness |
| GET | `/ready` | readiness (runs `SELECT 1`) |
| GET | `/metrics` | Prometheus exposition |
| GET | `/api/tickets?status=&priority=&q=&limit=` | list / filter / search tickets |
| POST | `/api/tickets` | create ticket |
| GET | `/api/tickets/{id}` | ticket detail |
| PUT | `/api/tickets/{id}` | update fields / move through workflow (sets `resolved_at`) |
| DELETE | `/api/tickets/{id}` | delete ticket (cascades comments) |
| GET | `/api/tickets/{id}/comments` | comment thread |
| POST | `/api/tickets/{id}/comments` | add a comment |
| GET | `/api/tickets/stats` | counts by status, category, urgent and unassigned |

Ticket workflow: `OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED`; priorities `LOW/MEDIUM/HIGH/URGENT`;
categories `HARDWARE/SOFTWARE/NETWORK/ACCESS/OTHER`.

## Tests

```bash
cd backend && pytest -v
```

Tests run against an in-memory SQLite database injected through FastAPI's dependency override, so
they never touch PostgreSQL. `pytest.ini` sets the path and options; `tests/conftest.py` holds the
fixtures.

## CI/CD pipeline

`.github/workflows/ci-cd.yml` runs on every push and pull request to `main`:

1. **test** - ruff lint, pytest with coverage.
2. **frontend-build** - `npm ci && npm run build`.
3. **validate-infra** - `helm lint`, `helm template`, `terraform fmt -check`, `terraform validate`.
4. **build-scan-push** (matrix: backend, frontend) - buildx build, Trivy SARIF upload, **Trivy gate
   (`exit-code: 1` on HIGH/CRITICAL)**, then push to `ghcr.io/prince-shakyaa/resolvedesk-{backend,frontend}`
   tagged `<full-sha>`, `sha-<short>`, `main`, `latest`.
5. **deploy** - `helm upgrade --install` with `--set image.tag=<sha>`; only runs when the repository
   variable `DEPLOY_ENABLED=true` and the `KUBE_CONFIG_DATA` secret are configured.

Nothing is pushed on pull requests; the scan still runs.

## Infrastructure (Terraform)

See [`terraform/README.md`](terraform/README.md). In short:

```bash
cd terraform && terraform init && terraform plan && terraform apply
aws eks update-kubeconfig --region ap-south-1 --name resolvedesk-dev-eks
# ... demo ...
terraform destroy
```

## Kubernetes + Helm

```bash
kubectl apply -f k8s/namespace.yaml
helm upgrade --install resolvedesk helm/resolvedesk -n resolvedesk -f helm/resolvedesk/values-dev.yaml
helm test resolvedesk -n resolvedesk
kubectl get pods,svc,ingress,hpa -n resolvedesk
```

`scripts/minikube-up.sh` does all of this on minikube (with ingress and metrics-server add-ons).
The Ingress routes `/api`, `/docs` and `/openapi.json` to the backend and everything else to the
frontend on host `resolvedesk.local` (dev) or whatever `ingress.host` is set to (prod).

## Monitoring

```bash
./monitoring/install.sh      # kube-prometheus-stack + ResolveDesk dashboard
scripts/load-test.sh         # generate traffic
```

Details, port-forward commands and PromQL in [`monitoring/README.md`](monitoring/README.md).

## Troubleshooting lab

`troubleshooting/` contains four broken manifests (bad image tag, Service selector typo, wrong
readiness path, wrong DATABASE_URL) with a [runbook](troubleshooting/RUNBOOK.md) explaining how to
diagnose each with `kubectl describe`, `logs`, `get endpoints` and `get events`.

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - request flow, networking, design decisions
- [docs/SECURITY.md](docs/SECURITY.md) - what Trivy scans, the CVEs it found and how they were fixed
- [docs/DEMO.md](docs/DEMO.md) - step-by-step live demo script matching the grading rubric
- [docs/SUBMISSION.md](docs/SUBMISSION.md) - rubric-to-evidence checklist

## Author

Prince Shakya - Scaler School of Technology, DevOps Final Capstone, October 2026.
