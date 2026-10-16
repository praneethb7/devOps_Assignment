variable "region" {
  type    = string
  default = "ap-south-1"
}
variable "name" {
  type    = string
  default = "campuscrate"
}
variable "kubernetes_version" {
  type    = string
  default = "1.35"
}
variable "node_instance_type" {
  type    = string
  default = "t3.medium"
}
variable "admin_principal_arn" {
  description = "IAM role or user ARN granted EKS administrator access. Never use a session ARN."
  type        = string
}
variable "endpoint_allowed_cidrs" {
  description = "Public API endpoint CIDRs, e.g. your workstation public IPv4 /32."
  type        = list(string)
  validation {
    condition     = length(var.endpoint_allowed_cidrs) > 0 && !contains(var.endpoint_allowed_cidrs, "0.0.0.0/0")
    error_message = "Restrict EKS public access to trusted CIDRs."
  }
}
