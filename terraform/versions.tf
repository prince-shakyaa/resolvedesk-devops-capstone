terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.68"
    }
  }

  # Remote state (recommended for teams). Create the bucket/table first, then
  # run: terraform init -migrate-state
  # backend "s3" {
  #   bucket         = "resolvedesk-tfstate-<account-id>"
  #   key            = "eks/terraform.tfstate"
  #   region         = "ap-south-1"
  #   dynamodb_table = "resolvedesk-tf-lock"
  #   encrypt        = true
  # }
}
