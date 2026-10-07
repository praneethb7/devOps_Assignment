# The bucket itself.
resource "aws_s3_bucket" "receipts" {
  bucket = var.bucket_name

  tags = {
    Name        = var.bucket_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Project     = "yatri"
  }
}

# Versioning is a separate resource in AWS provider v4+, not a block on the
# bucket. Older tutorials showing `versioning { }` inline no longer apply.
resource "aws_s3_bucket_versioning" "receipts" {
  bucket = aws_s3_bucket.receipts.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

# Block all four forms of public access. Deliberately explicit: the default
# on a new bucket is secure, but saying so in code means a later change
# cannot quietly open it.
resource "aws_s3_bucket_public_access_block" "receipts" {
  bucket = aws_s3_bucket.receipts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Encrypt objects at rest with S3-managed keys.
resource "aws_s3_bucket_server_side_encryption_configuration" "receipts" {
  bucket = aws_s3_bucket.receipts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Expire old receipt versions so the bucket does not grow without limit.
resource "aws_s3_bucket_lifecycle_configuration" "receipts" {
  count  = var.enable_lifecycle_rules ? 1 : 0
  bucket = aws_s3_bucket.receipts.id

  # Depends on versioning: a noncurrent-version rule is meaningless without it.
  depends_on = [aws_s3_bucket_versioning.receipts]

  rule {
    id     = "expire-noncurrent-receipts"
    status = "Enabled"

    filter {
      prefix = "receipts/"
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# An object, so the bucket is not empty and `terraform show` has something
# to display beyond configuration.
resource "aws_s3_object" "readme" {
  bucket  = aws_s3_bucket.receipts.id
  key     = "receipts/README.txt"
  content = "Receipt archive for the yatri booking service. Managed by Terraform.\n"

  tags = {
    ManagedBy = "terraform"
  }
}
