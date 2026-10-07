# ---------------------------------------------------------------- network ----
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true # needed for private DNS names inside the VPC

  tags = { Name = "${var.project_name}-vpc" }
}

# Without this, nothing in the VPC can reach the internet at all.
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = { Name = "${var.project_name}-igw" }
}

# Public only because of the route table below - there is no "public" flag.
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = { Name = "${var.project_name}-public-a", Tier = "public" }
}

# Same VPC, no 0.0.0.0/0 route. This is what makes it private.
resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidr
  availability_zone = "${var.aws_region}a"

  tags = { Name = "${var.project_name}-private-a", Tier = "private" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  # The `local` route for 10.20.0.0/16 is implicit and cannot be removed.
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = { Name = "${var.project_name}-public-rt" }
}

# A subnet with no explicit association silently falls back to the VPC's main
# route table, which is an easy way to make a subnet accidentally public.
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  tags = { Name = "${var.project_name}-private-rt" }
}

resource "aws_route_table_association" "private" {
  subnet_id      = aws_subnet.private.id
  route_table_id = aws_route_table.private.id
}

# --------------------------------------------------------- security groups ----
resource "aws_security_group" "web" {
  name        = "${var.project_name}-web-sg"
  description = "HTTP from anywhere, SSH from inside the VPC only"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH, restricted"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-web-sg" }
}

# The group-as-source pattern: the database accepts traffic from anything in
# the web security group and nothing else. No CIDR to maintain as instances
# come and go.
resource "aws_security_group" "db" {
  name        = "${var.project_name}-db-sg"
  description = "PostgreSQL from the web tier only"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL from web tier"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.web.id]
  }

  tags = { Name = "${var.project_name}-db-sg" }
}

# ---------------------------------------------------------------- compute ----
# Looked up, not hardcoded: an AMI ID is region-specific, so a literal breaks
# the moment someone changes var.aws_region.
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = <<-EOT
    #!/bin/bash
    dnf install -y nginx
    echo "<h1>yatri booking service</h1><p>provisioned by Terraform</p>" \
      > /usr/share/nginx/html/index.html
    systemctl enable --now nginx
  EOT

  root_block_device {
    volume_size = 8
    volume_type = "gp3"
    encrypted   = true
  }

  tags = { Name = "${var.project_name}-web" }
}

# ---------------------------------------------------------------- storage ----
resource "aws_s3_bucket" "assets" {
  bucket = var.bucket_name

  tags = { Name = var.bucket_name }
}

resource "aws_s3_bucket_public_access_block" "assets" {
  bucket = aws_s3_bucket.assets.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "assets" {
  bucket = aws_s3_bucket.assets.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Demonstrates an implicit dependency on the instance: the object's content
# interpolates an attribute that does not exist until the instance is created.
resource "aws_s3_object" "inventory" {
  bucket  = aws_s3_bucket.assets.id
  key     = "inventory/web.txt"
  content = <<-EOT
    instance_id   = ${aws_instance.web.id}
    private_ip    = ${aws_instance.web.private_ip}
    subnet        = ${aws_subnet.public.id}
    vpc           = ${aws_vpc.main.id}
  EOT
}
