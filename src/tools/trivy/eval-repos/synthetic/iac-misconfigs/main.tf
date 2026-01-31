# Terraform with security misconfigurations

resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket"

  # Missing encryption configuration (security issue)
  # Missing versioning (compliance issue)
  # Missing logging (audit issue)
}

resource "aws_security_group" "allow_all" {
  name = "allow_all"

  # Overly permissive ingress (security issue)
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Overly permissive egress
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "web" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"

  # Missing IMDSv2 (security issue)
  # Missing encryption at rest
}
