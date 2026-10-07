terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# This project runs against LocalStack, an AWS-compatible API served from a
# container on localhost. Everything below is what makes the real AWS provider
# talk to it instead of to Amazon:
#
#   - static dummy credentials, because LocalStack does not check them
#   - the three skip_* flags, which disable the calls that only real AWS answers
#   - s3_use_path_style, because bucket-as-subdomain needs real DNS
#   - endpoints, which points every service at the container
#
# Deleting this block is all it takes to target a real AWS account.
provider "aws" {
  region                      = var.aws_region
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    s3  = "http://localhost:4566"
    sts = "http://localhost:4566"
    iam = "http://localhost:4566"
  }
}
