# terraform/ - AWS VPC + EKS

Provisions the production-style infrastructure for ResolveDesk:

```text
AWS (ap-southeast-2)
└── VPC 10.20.0.0/16
    ├── public subnets  10.20.101.0/24 (1a), 10.20.102.0/24 (1b)   <- NAT gateway, load balancers
    ├── private subnets 10.20.1.0/24   (1a), 10.20.2.0/24   (1b)   <- EKS worker nodes
    └── EKS 1.31 "resolvedesk-dev-eks"
        ├── managed node group "general": 2-4 x t3.medium
        └── add-ons: coredns, kube-proxy, vpc-cni, aws-ebs-csi-driver (IRSA)
```

> **New AWS accounts ("Projects" experience).** Accounts created through the new AWS sign-up flow are pinned
> to one region chosen from the contact address (India -> `ap-southeast-2` Sydney) and carry an AWS-managed
> service control policy that denies every other region, so `aws_region`/`availability_zones` default to
> Sydney. The same policy denies `iam:CreateOpenIDConnectProvider`; set `enable_ebs_csi_irsa = false` on
> such accounts. Classic accounts can use any region.

> **Cost warning.** An EKS control plane (~$0.10/h), a NAT gateway (~$0.05/h + data) and two
> t3.medium nodes cost real money every hour they exist. Run `terraform destroy` as soon as the
> demo is over.

## Usage

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # optional overrides
aws sts get-caller-identity                     # confirm credentials (never commit them)

terraform init
terraform fmt -recursive
terraform validate
terraform plan -out=tfplan
terraform apply tfplan                          # ~15 minutes

aws eks update-kubeconfig --region ap-southeast-2 --name resolvedesk-dev-eks
kubectl get nodes
```

Then install the cluster prerequisites and the application:

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl apply -f ../k8s/namespace.yaml
helm upgrade --install resolvedesk ../helm/resolvedesk -n resolvedesk -f ../helm/resolvedesk/values-prod.yaml \
  --set image.tag=<git-sha> --set ingress.host=<your-host>
```

Tear everything down:

```bash
helm uninstall resolvedesk -n resolvedesk      # removes the LoadBalancer first
helm uninstall ingress-nginx -n ingress-nginx
terraform destroy
```

## Files

| File | Purpose |
|------|---------|
| `versions.tf` | Terraform/provider constraints, optional S3 remote state |
| `providers.tf` | AWS provider with default tags |
| `variables.tf` | All tunables with sane defaults |
| `vpc.tf` | VPC module: 2 public + 2 private subnets, NAT |
| `eks.tf` | EKS module, managed node group, add-ons, EBS CSI IRSA role |
| `outputs.tf` | Cluster name/endpoint and the `update-kubeconfig` command |
| `terraform.tfvars.example` | Example variable file (no secrets) |

The CI workflow `validate-infra` runs `terraform fmt -check` and `terraform validate` on every push;
`.github/workflows/terraform.yml` can run plan/apply/destroy on demand with AWS credentials stored as
GitHub secrets.
