output "cluster_name" { value = aws_eks_cluster.main.name }
output "vpc_id" { value = aws_vpc.main.id }
output "configure_kubectl" { value = "aws eks update-kubeconfig --region ${var.region} --name ${aws_eks_cluster.main.name}" }
