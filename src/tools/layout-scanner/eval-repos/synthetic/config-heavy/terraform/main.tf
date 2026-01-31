provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "main" {
  bucket = var.bucket_name
}
