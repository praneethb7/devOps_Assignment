variable "aws_region" {
  description = "Region the bucket is created in."
  type        = string
  default     = "ap-south-1"
}

variable "bucket_name" {
  description = "Globally unique bucket name. Set in terraform.tfvars."
  type        = string
}

variable "environment" {
  description = "Environment tag applied to every resource."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of dev, staging or prod."
  }
}

variable "enable_versioning" {
  description = "Keep previous versions of every object."
  type        = bool
  default     = true
}

variable "enable_lifecycle_rules" {
  description = <<-EOT
    Create the noncurrent-version lifecycle rule.

    Defaults to false because LocalStack 3.8.1 does not satisfy the AWS
    provider's read-after-write consistency check on
    GetBucketLifecycleConfiguration: the apply hangs and then fails with
    "timeout while waiting for state to become 'true'". The resource is
    correct and works against real AWS - set this to true there.
  EOT
  type        = bool
  default     = false
}
