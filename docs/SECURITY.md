# Security notes (DevSecOps module)

## What Trivy scans

Trivy inspects each **built container image** layer by layer:

1. **OS packages** - the Debian (backend) or Alpine (frontend) package database, matched against
   distro security advisories.
2. **Application dependencies** - Python packages found in `site-packages` (backend) and, for the
   frontend, only what survives the multi-stage build (the Node toolchain is discarded, so only
   Nginx and Alpine remain).

The pipeline runs Trivy twice per image: once producing a SARIF report uploaded to the repository's
**Security -> Code scanning** tab, then once as a **gate** with `exit-code: 1` on `HIGH,CRITICAL`
(`ignore-unfixed: true`, so findings with no available patch do not block the build). If the gate
fails, the push step never runs.

## Findings from the first scan and how they were fixed

| Image | Finding | Severity | Fix |
|-------|---------|----------|-----|
| backend | CVE-2025-62727 Starlette DoS via `Range` header | HIGH | upgraded FastAPI/Starlette |
| backend | CVE-2026-48818 Starlette SSRF via UNC paths in StaticFiles | HIGH | upgraded FastAPI/Starlette |
| backend | CVE-2026-54283 Starlette form limits ignored (DoS) | HIGH | upgraded FastAPI/Starlette |
| frontend | musl, zlib, libtiff, nghttp2, libxml2 Alpine CVEs | HIGH | moved to `nginx-unprivileged:1.30-alpine` + `apk upgrade` |

Result after the fix: **0 HIGH, 0 CRITICAL** on both images.

Interpretation: none of the backend CVEs were in code paths ResolveDesk uses (it serves no static
files and parses no form data), but a scanner cannot know that. Patching is cheaper than arguing,
and it keeps the gate meaningful for the next CVE that *does* matter.

## Other controls in the repository

- **Secrets never committed** - `.gitignore` excludes `.env`, `terraform.tfvars`, kubeconfigs and
  state files; `terraform.tfvars.example` and `.env.example` carry placeholders only. AWS and
  kubeconfig credentials live in GitHub Actions secrets.
- **Least-privilege workflow tokens** - each job declares only the `permissions` it needs
  (`packages: write` only in the build job, `security-events: write` for SARIF upload).
- **Non-root, read-only-ish containers** - both images run as a dedicated UID; the Helm chart sets
  `runAsNonRoot`, `allowPrivilegeEscalation: false`, drops all capabilities and uses the
  `RuntimeDefault` seccomp profile. The namespace enforces the `baseline` Pod Security Standard.
- **Pinned dependencies** - `requirements.txt`, `package-lock.json`, Docker base tags and GitHub
  Action versions are pinned; Dependabot opens PRs for updates so the Trivy gate stays green.
- **Database credentials in a Secret** - the chart renders `DATABASE_URL` into a Kubernetes Secret,
  not a ConfigMap, and supports `postgres.existingSecret` for externally managed credentials.
- **Network exposure** - only the Ingress is reachable from outside; PostgreSQL has a headless
  ClusterIP Service and no Ingress rule. `cluster_endpoint_public_access_cidrs` lets you lock the
  EKS API endpoint to your own IP.
