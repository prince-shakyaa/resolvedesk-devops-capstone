# EKS control plane + one managed node group in the private subnets.
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "20.31.6"

  cluster_name    = "${local.name}-eks"
  cluster_version = var.cluster_version

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access       = true
  cluster_endpoint_public_access_cidrs = var.cluster_endpoint_public_access_cidrs

  # Gives the identity running `terraform apply` cluster-admin via EKS access entries.
  enable_cluster_creator_admin_permissions = true

  # The EKS module creates the IAM OIDC provider when enable_irsa is true.
  enable_irsa = var.enable_ebs_csi_irsa

  cluster_addons = merge(
    {
      coredns    = {}
      kube-proxy = {}
      vpc-cni    = {}
    },
    var.enable_ebs_csi_irsa ? {
      # PostgreSQL's PersistentVolumeClaim needs the EBS CSI driver on EKS >= 1.23.
      aws-ebs-csi-driver = {
        service_account_role_arn = module.ebs_csi_irsa[0].iam_role_arn
      }
    } : {}
  )

  eks_managed_node_group_defaults = {
    ami_type       = "AL2023_x86_64_STANDARD"
    disk_size      = 30
    instance_types = var.node_instance_types
  }

  eks_managed_node_groups = {
    general = {
      name           = "${local.name}-general"
      iam_role_name  = "${local.name}-node" # keep the IAM role name_prefix under AWS's 38-char limit
      min_size       = var.node_min_size
      max_size       = var.node_max_size
      desired_size   = var.node_desired_size
      capacity_type  = "ON_DEMAND"
      instance_types = var.node_instance_types

      labels = {
        workload = "general"
      }
    }
  }

  tags = local.tags
}

# IAM role for the EBS CSI driver service account (IRSA).
module "ebs_csi_irsa" {
  count = var.enable_ebs_csi_irsa ? 1 : 0

  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "5.48.0"

  role_name             = "${local.name}-ebs-csi"
  attach_ebs_csi_policy = true

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }

  tags = local.tags
}
