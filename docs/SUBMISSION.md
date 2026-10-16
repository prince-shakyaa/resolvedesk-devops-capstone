# Submission checklist (rubric -> evidence)

Repository: https://github.com/prince-shakyaa/resolvedesk-devops-capstone

Google Form answers: Full name *Prince Shakya*, roll number *24BCS10084*, GitHub URL above.

Screenshots are in `docs/screenshots/` using the file names below (all captured except the M7 AWS ones, which require an AWS account).

| Module | Requirement | Where in the repo | Screenshot to capture |
|--------|-------------|-------------------|-----------------------|
| M1 Application | `/health`, 4+ REST endpoints, Alembic, responsive React UI | `backend/app`, `backend/alembic/versions`, `frontend/src` | `m1-ui.png` (browser at :3000) |
| M2 Testing | pytest passes, 5+ tests on 3+ endpoints, test DB, `pytest.ini`/`conftest.py` | `backend/tests`, `backend/pytest.ini` | `m2-pytest.png` (`pytest -v`) |
| M3 Git | public repo, meaningful commits, `.gitignore` | `.gitignore`, `git log` | `m3-commits.png` (10+ commits) |
| M4 Docker | both Dockerfiles, multi-stage frontend, non-root, compose | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` | `m4-compose.png`, `m4-browser.png` |
| M5 CI/CD | workflow on push to main, pytest job, frontend build, both images, GHCR, SHA tags | `.github/workflows/ci-cd.yml` | `m5-actions-green.png`, `m5-ghcr-tags.png` |
| M6 DevSecOps | Trivy on both images, fail on HIGH/CRITICAL, explanation | `ci-cd.yml` (Trivy gate), `docs/SECURITY.md` | `m6-trivy.png` |
| M7 Terraform | valid HCL, init/plan, VPC 2 public subnets, EKS node group, destroy, tfvars.example | `terraform/` | `m7-plan.png`, `m7-aws-vpc.png`, `m7-aws-eks.png`, `m7-destroy.png` **(pending: needs AWS credentials)** |
| M8 K8s + Helm | namespace, chart, upgrade --install, 2 replicas, ClusterIP, Ingress `/` and `/api`, pods Running | `k8s/namespace.yaml`, `helm/resolvedesk` | `m8-pods.png`, `m8-svc.png`, `m8-helm-list.png`, `m8-ingress-browser.png` |
| M9 Observability | `/metrics`, Prometheus scraping, Grafana panel | `monitoring/` | `m9-metrics.png`, `m9-prom-targets.png`, `m9-grafana.png` |
| M10 Docs | README, live demo | `README.md`, `docs/DEMO.md` | - |

## GitHub settings to complete after the first push

1. **Packages visibility** - both GHCR packages (`resolvedesk-backend`, `resolvedesk-frontend`)
   are public, so clusters can pull them anonymously. If they are ever made private, Kubernetes
   needs an `imagePullSecret` (the deploy job creates one named `ghcr-pull`).
2. **Optional auto-deploy** - Settings -> Secrets and variables -> Actions:
   - variable `DEPLOY_ENABLED=true`, variable `INGRESS_HOST=<your hostname>`
   - secret `KUBE_CONFIG_DATA` = `base64 -w0 ~/.kube/config` (after `aws eks update-kubeconfig`)
3. **Optional Terraform from CI** - secrets `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, variable
   `AWS_REGION`; then run the *Terraform (manual)* workflow with `plan`, `apply` or `destroy`.
