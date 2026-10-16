.PHONY: help up down logs test lint build scan helm-lint tf-validate smoke k8s-up k8s-down

help:            ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

up:              ## Start the full stack with Docker Compose
	docker compose up --build -d

down:            ## Stop the stack (keeps the database volume)
	docker compose down

logs:            ## Tail backend logs
	docker compose logs -f backend

test:            ## Run backend tests
	cd backend && pytest -v

lint:            ## Lint backend with ruff
	cd backend && ruff check . && ruff format --check .

build:           ## Build both images locally
	docker build -t resolvedesk-backend:local backend
	docker build -t resolvedesk-frontend:local frontend

scan: build      ## Trivy scan both local images (HIGH/CRITICAL)
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.58.1 image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 resolvedesk-backend:local
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.58.1 image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 resolvedesk-frontend:local

helm-lint:       ## Lint and render the Helm chart
	helm lint helm/resolvedesk -f helm/resolvedesk/values-dev.yaml
	helm template resolvedesk helm/resolvedesk -f helm/resolvedesk/values-prod.yaml > /dev/null

tf-validate:     ## terraform fmt + validate (no backend)
	cd terraform && terraform fmt -check -recursive && terraform init -backend=false -input=false && terraform validate

smoke:           ## Smoke test a running stack (BASE_URL=http://localhost:3000)
	scripts/smoke-test.sh

k8s-up:          ## Deploy to minikube
	scripts/minikube-up.sh

k8s-down:        ## Remove the release from the cluster
	helm uninstall resolvedesk -n resolvedesk || true
