# Test Terraform configuration with intentional misconfigurations

provider "aws" {
  region = "us-east-1"
}

# S3 bucket without encryption
resource "aws_s3_bucket" "vulnerable_bucket" {
  bucket = "vulnerable-test-bucket"
  acl    = "public-read"

  tags = {
    Name = "Test Bucket"
  }
}

# Security group with overly permissive ingress
resource "aws_security_group" "allow_all" {
  name        = "allow_all"
  description = "Allow all inbound traffic"

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
