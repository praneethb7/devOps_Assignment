mock_provider "aws" {
  mock_data "aws_iam_policy_document" {
    defaults = { json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}" }
  }
  mock_resource "aws_iam_openid_connect_provider" {
    defaults = { arn = "arn:aws:iam::123456789012:oidc-provider/oidc.eks.ap-south-1.amazonaws.com/id/CAMPUSCRATE" }
  }
  mock_data "aws_availability_zones" {
    defaults = { names = ["ap-south-1a", "ap-south-1b"] }
  }
  mock_resource "aws_eks_cluster" {
    defaults = {
      identity = [{ oidc = [{ issuer = "https://oidc.eks.ap-south-1.amazonaws.com/id/CAMPUSCRATE" }] }]
    }
  }
  mock_resource "aws_iam_role" {
    defaults = { arn = "arn:aws:iam::123456789012:role/campuscrate-test" }
  }
}
mock_provider "tls" {
  mock_data "tls_certificate" {
    defaults = { certificates = [{ sha1_fingerprint = "0123456789012345678901234567890123456789" }] }
  }
}
variables {
  admin_principal_arn    = "arn:aws:iam::123456789012:role/CapstoneAdmin"
  endpoint_allowed_cidrs = ["203.0.113.10/32"]
}
run "network_and_cluster_plan" {
  command = plan
  assert {
    condition     = length(aws_subnet.public) == 2 && length(aws_subnet.private) == 2
    error_message = "The cluster must have two public and two private subnets."
  }
  assert {
    condition     = aws_eks_node_group.main.scaling_config[0].desired_size == 2
    error_message = "The managed node group must start with two nodes."
  }
  assert {
    condition     = aws_eks_cluster.main.vpc_config[0].endpoint_private_access
    error_message = "Private API access must be enabled."
  }
}
