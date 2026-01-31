#!/usr/bin/env python3
"""Build synthetic repositories for Trivy vulnerability scanning PoC."""

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPOS_DIR = SCRIPT_DIR.parent / "eval-repos" / "synthetic"


def create_no_vulnerabilities():
    """Create a repository with no known vulnerabilities."""
    repo_dir = REPOS_DIR / "no-vulnerabilities"
    repo_dir.mkdir(parents=True, exist_ok=True)

    # Clean package.json with latest safe versions
    package_json = {
        "name": "no-vulnerabilities",
        "version": "1.0.0",
        "description": "A project with no known vulnerable dependencies",
        "dependencies": {
            "express": "4.21.0",
            "lodash": "4.17.21",
            "axios": "1.7.7",
        },
    }

    (repo_dir / "package.json").write_text(json.dumps(package_json, indent=2))

    # Also create a simple Python requirements.txt with safe versions
    requirements = """# Safe Python dependencies
requests==2.32.3
flask==3.0.3
"""
    (repo_dir / "requirements.txt").write_text(requirements)

    print(f"Created: {repo_dir.name}")


def create_critical_cves():
    """Create a repository with critical CVEs."""
    repo_dir = REPOS_DIR / "critical-cves"
    repo_dir.mkdir(parents=True, exist_ok=True)

    # package.json with known critical vulnerabilities
    # lodash < 4.17.21 has CVE-2021-23337 (Command Injection, HIGH)
    # lodash < 4.17.12 has CVE-2019-10744 (Prototype Pollution, CRITICAL)
    # minimist < 1.2.6 has CVE-2021-44906 (Prototype Pollution, CRITICAL)
    package_json = {
        "name": "critical-cves",
        "version": "1.0.0",
        "description": "A project with critical CVE vulnerabilities",
        "dependencies": {
            "lodash": "4.17.4",  # Has multiple CVEs including CRITICAL
            "minimist": "1.2.0",  # CVE-2021-44906 (CRITICAL)
            "express": "4.17.1",  # Has some vulnerabilities
            "axios": "0.21.0",  # CVE-2021-3749 (HIGH)
        },
    }

    (repo_dir / "package.json").write_text(json.dumps(package_json, indent=2))

    # Python requirements with vulnerabilities
    requirements = """# Python dependencies with vulnerabilities
requests==2.25.0
urllib3==1.26.0
pyyaml==5.3
"""
    (repo_dir / "requirements.txt").write_text(requirements)

    print(f"Created: {repo_dir.name}")


def create_outdated_deps():
    """Create a repository with many outdated dependencies."""
    repo_dir = REPOS_DIR / "outdated-deps"
    repo_dir.mkdir(parents=True, exist_ok=True)

    # Outdated but not necessarily critically vulnerable
    package_json = {
        "name": "outdated-deps",
        "version": "1.0.0",
        "description": "A project with outdated dependencies",
        "dependencies": {
            "express": "4.16.0",
            "lodash": "4.17.15",
            "moment": "2.24.0",  # Deprecated, has vulnerabilities
            "async": "2.6.0",
            "bluebird": "3.5.0",
            "underscore": "1.8.0",
            "request": "2.88.0",  # Deprecated
            "uuid": "3.4.0",
        },
    }

    (repo_dir / "package.json").write_text(json.dumps(package_json, indent=2))

    print(f"Created: {repo_dir.name}")


def create_mixed_severity():
    """Create a repository with mixed severity vulnerabilities."""
    repo_dir = REPOS_DIR / "mixed-severity"
    repo_dir.mkdir(parents=True, exist_ok=True)

    # Mix of critical, high, medium vulnerabilities
    package_json = {
        "name": "mixed-severity",
        "version": "1.0.0",
        "description": "A project with mixed severity vulnerabilities",
        "dependencies": {
            "lodash": "4.17.10",  # CRITICAL + HIGH
            "express": "4.16.0",  # Various
            "qs": "6.5.1",  # Prototype pollution
            "helmet": "3.21.0",  # Medium issues
            "body-parser": "1.19.0",
            "cookie-parser": "1.4.4",
        },
    }

    (repo_dir / "package.json").write_text(json.dumps(package_json, indent=2))

    # requirements.txt with mixed issues
    requirements = """# Mixed severity Python dependencies
django==2.2.0
jinja2==2.10
pillow==7.0.0
cryptography==2.8
"""
    (repo_dir / "requirements.txt").write_text(requirements)

    print(f"Created: {repo_dir.name}")


def create_iac_misconfigs():
    """Create a repository with IaC misconfigurations."""
    repo_dir = REPOS_DIR / "iac-misconfigs"
    repo_dir.mkdir(parents=True, exist_ok=True)

    # Dockerfile with security issues
    dockerfile = """FROM python:3.8

# Running as root (security issue)
USER root

# Hardcoded credentials (security issue)
ENV DB_PASSWORD=mysecretpassword123

# Installing without version pinning
RUN pip install flask requests

# Exposing all ports
EXPOSE 22 80 443 8080

COPY . /app
WORKDIR /app

CMD ["python", "app.py"]
"""
    (repo_dir / "Dockerfile").write_text(dockerfile)

    # Terraform with misconfigurations
    terraform_main = """# Terraform with security misconfigurations

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
"""
    (repo_dir / "main.tf").write_text(terraform_main)

    # Also include package.json with some vulns
    package_json = {
        "name": "iac-misconfigs",
        "version": "1.0.0",
        "description": "A project with IaC misconfigurations",
        "dependencies": {
            "express": "4.17.1",
            "lodash": "4.17.19",
        },
    }
    (repo_dir / "package.json").write_text(json.dumps(package_json, indent=2))

    print(f"Created: {repo_dir.name}")


def main():
    """Create all synthetic repositories."""
    print("Building synthetic repositories for Trivy PoC...")
    print(f"Output directory: {REPOS_DIR}")
    print()

    create_no_vulnerabilities()
    create_critical_cves()
    create_outdated_deps()
    create_mixed_severity()
    create_iac_misconfigs()

    print()
    print("All synthetic repositories created successfully!")


if __name__ == "__main__":
    main()
