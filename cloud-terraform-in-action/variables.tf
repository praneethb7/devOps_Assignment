variable "aws_region" {
  description = "Region everything is created in."
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment tag applied to every resource via default_tags."
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Name prefix for every resource."
  type        = string
  default     = "yatri"
}

variable "vpc_cidr" {
  description = "Address space for the VPC. Cannot be changed after creation."
  type        = string
  default     = "10.20.0.0/16"

  validation {
    condition     = can(cidrnetmask(var.vpc_cidr))
    error_message = "vpc_cidr must be a valid IPv4 CIDR block."
  }
}

variable "public_subnet_cidr" {
  description = "Public subnet, must sit inside vpc_cidr."
  type        = string
  default     = "10.20.1.0/24"
}

variable "private_subnet_cidr" {
  description = "Private subnet, no route to the internet gateway."
  type        = string
  default     = "10.20.11.0/24"
}

variable "instance_type" {
  description = "EC2 instance type for the web server."
  type        = string
  default     = "t3.micro"
}

variable "allowed_ssh_cidr" {
  description = <<-EOT
    CIDR allowed to reach port 22. Defaults to the VPC itself rather than
    0.0.0.0/0 - an SSH port open to the internet is the single most common
    avoidable finding in a security review.
  EOT
  type        = string
  default     = "10.20.0.0/16"
}

variable "bucket_name" {
  description = "Bucket for the application's static assets."
  type        = string
  default     = "yatri-assets-24bcs10081"
}
