output "bucket_name" {
  description = "Name of the bucket that was created."
  value       = aws_s3_bucket.receipts.id
}

output "bucket_arn" {
  description = "ARN, which is what an IAM policy would reference."
  value       = aws_s3_bucket.receipts.arn
}

output "bucket_region" {
  description = "Region the bucket lives in."
  value       = aws_s3_bucket.receipts.region
}

output "versioning_status" {
  description = "Whether object versioning ended up enabled."
  value       = aws_s3_bucket_versioning.receipts.versioning_configuration[0].status
}

output "object_key" {
  description = "Key of the seeded object."
  value       = aws_s3_object.readme.key
}
