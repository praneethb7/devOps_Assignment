output "vpc_id" {
  description = "ID of the VPC."
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "Address space actually allocated."
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_id" {
  value = aws_subnet.public.id
}

output "private_subnet_id" {
  value = aws_subnet.private.id
}

output "internet_gateway_id" {
  value = aws_internet_gateway.main.id
}

output "web_security_group_id" {
  value = aws_security_group.web.id
}

output "db_security_group_id" {
  value = aws_security_group.db.id
}

output "instance_id" {
  value = aws_instance.web.id
}

output "instance_private_ip" {
  description = "Always present, assigned from the subnet CIDR."
  value       = aws_instance.web.private_ip
}

output "instance_public_ip" {
  description = "Present because the subnet sets map_public_ip_on_launch."
  value       = aws_instance.web.public_ip
}

output "ami_id" {
  description = "Resolved by the data source rather than hardcoded."
  value       = data.aws_ami.al2023.id
}

output "assets_bucket" {
  value = aws_s3_bucket.assets.id
}
