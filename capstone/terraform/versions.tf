terraform {
  required_version = ">= 1.6, < 2.0"
  required_providers {
    tls = { source = "hashicorp/tls", version = "~> 4.0" }
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}
provider "aws" {
  region = var.region
  default_tags {
    tags = { Project = var.name, Owner = "praneethb7", ManagedBy = "Terraform" }
  }
}
