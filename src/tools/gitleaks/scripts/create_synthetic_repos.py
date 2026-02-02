#!/usr/bin/env python3
"""Create synthetic repositories with planted secrets for gitleaks evaluation."""

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SecretSpec:
    """Specification for a planted secret."""
    file_path: str
    secret_type: str
    secret_value: str
    rule_id: str
    line_number: int = 1
    commit_message: str = "Add configuration"
    deleted_in_later_commit: bool = False


@dataclass
class RepoSpec:
    """Specification for a synthetic repository."""
    name: str
    description: str
    secrets: list[SecretSpec] = field(default_factory=list)
    files: dict[str, str] = field(default_factory=dict)


SYNTHETIC_REPOS = [
    RepoSpec(
        name="no-secrets",
        description="Clean repository with no secrets (baseline)",
        secrets=[],
        files={
            "README.md": "# No Secrets\n\nThis is a clean repository.\n",
            "src/main.py": '''"""Main module."""


def main():
    """Entry point."""
    print("Hello, World!")


if __name__ == "__main__":
    main()
''',
            "config/settings.py": '''"""Settings module."""

DATABASE_URL = "postgresql://localhost/mydb"
DEBUG = False
LOG_LEVEL = "INFO"
''',
        },
    ),
    RepoSpec(
        name="api-keys",
        description="Repository with API keys",
        secrets=[
            SecretSpec(
                file_path="config/api.py",
                secret_type="generic-api-key",
                secret_value="api_key = 'sk_live_abcdef123456789012345678901234567890'",
                rule_id="generic-api-key",
                line_number=5,
            ),
            SecretSpec(
                file_path=".env",
                secret_type="generic-api-key",
                secret_value="API_KEY=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                rule_id="github-pat",
                line_number=3,
            ),
        ],
        files={
            "README.md": "# API Keys Test\n\nRepository for testing API key detection.\n",
            "src/main.py": '''"""Main module."""


def main():
    """Entry point."""
    from config.api import API_KEY
    print(f"Using API key: {API_KEY[:8]}...")


if __name__ == "__main__":
    main()
''',
            "config/__init__.py": "",
            "config/api.py": '''"""API configuration."""

# API Configuration
# TODO: Move to environment variables
api_key = 'sk_live_abcdef123456789012345678901234567890'

def get_api_key():
    return api_key
''',
            ".env": '''# Environment variables
DEBUG=true
API_KEY=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LOG_LEVEL=debug
''',
        },
    ),
    RepoSpec(
        name="aws-credentials",
        description="Repository with AWS credentials",
        secrets=[
            SecretSpec(
                file_path="config/aws.py",
                secret_type="aws-access-key-id",
                secret_value="AWS_ACCESS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE'",
                rule_id="aws-access-key-id",
                line_number=4,
            ),
            SecretSpec(
                file_path="config/aws.py",
                secret_type="aws-secret-access-key",
                secret_value="AWS_SECRET_ACCESS_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'",
                rule_id="aws-secret-access-key",
                line_number=5,
            ),
            SecretSpec(
                file_path=".aws/credentials",
                secret_type="aws-access-key-id",
                secret_value="aws_access_key_id = AKIAIOSFODNN7EXAMPLE",
                rule_id="aws-access-key-id",
                line_number=2,
            ),
        ],
        files={
            "README.md": "# AWS Credentials Test\n\nRepository for testing AWS credential detection.\n",
            "src/s3_client.py": '''"""S3 client module."""

import boto3
from config.aws import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY


def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
''',
            "config/__init__.py": "",
            "config/aws.py": '''"""AWS configuration."""

# AWS Credentials - DO NOT COMMIT TO VERSION CONTROL
AWS_ACCESS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE'
AWS_SECRET_ACCESS_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
AWS_REGION = 'us-east-1'
''',
            ".aws/credentials": '''[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
''',
        },
    ),
    RepoSpec(
        name="mixed-secrets",
        description="Repository with multiple secret types",
        secrets=[
            SecretSpec(
                file_path="config/database.py",
                secret_type="generic-api-key",
                secret_value="DATABASE_PASSWORD = 'super_secret_password_123!'",
                rule_id="generic-api-key",
                line_number=3,
            ),
            SecretSpec(
                file_path="config/stripe.py",
                secret_type="stripe-api-key",
                secret_value="STRIPE_KEY = 'sk_live_4eC39HqLyjWDarjtT1zdp7dc'",
                rule_id="stripe-api-key",
                line_number=2,
            ),
            SecretSpec(
                file_path=".env.production",
                secret_type="jwt-secret",
                secret_value="JWT_SECRET=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
                rule_id="jwt",
                line_number=4,
            ),
            SecretSpec(
                file_path="scripts/deploy.sh",
                secret_type="private-key",
                secret_value="DEPLOY_KEY='-----BEGIN RSA PRIVATE KEY-----'",
                rule_id="private-key",
                line_number=6,
            ),
        ],
        files={
            "README.md": "# Mixed Secrets Test\n\nRepository with various secret types.\n",
            "src/main.py": '''"""Main module."""


def main():
    """Entry point."""
    print("Application starting...")


if __name__ == "__main__":
    main()
''',
            "config/__init__.py": "",
            "config/database.py": '''"""Database configuration."""

DATABASE_PASSWORD = 'super_secret_password_123!'
DATABASE_HOST = 'localhost'
DATABASE_PORT = 5432
''',
            "config/stripe.py": '''"""Stripe payment configuration."""
STRIPE_KEY = 'sk_live_4eC39HqLyjWDarjtT1zdp7dc'
STRIPE_WEBHOOK_SECRET = 'whsec_test123'
''',
            ".env.production": '''# Production environment
DEBUG=false
LOG_LEVEL=error
JWT_SECRET=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
REDIS_URL=redis://localhost:6379
''',
            "scripts/deploy.sh": '''#!/bin/bash
# Deployment script
set -e

# DO NOT COMMIT REAL KEYS
DEPLOY_KEY='-----BEGIN RSA PRIVATE KEY-----'
echo "Deploying..."
''',
        },
    ),
    RepoSpec(
        name="historical-secrets",
        description="Repository with secrets in git history (deleted but findable)",
        secrets=[
            SecretSpec(
                file_path="config/secrets.py",
                secret_type="aws-access-key-id",
                secret_value="AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'",
                rule_id="aws-access-key-id",
                line_number=2,
                deleted_in_later_commit=True,
            ),
            SecretSpec(
                file_path=".env",
                secret_type="generic-api-key",
                secret_value="DATABASE_URL=postgres://admin:password123@prod.example.com/db",
                rule_id="generic-api-key",
                line_number=2,
                deleted_in_later_commit=True,
            ),
        ],
        files={
            "README.md": "# Historical Secrets Test\n\nSecrets were removed but exist in git history.\n",
            "src/main.py": '''"""Main module."""
import os


def main():
    """Entry point."""
    db_url = os.environ.get("DATABASE_URL", "sqlite:///local.db")
    print(f"Connecting to database...")


if __name__ == "__main__":
    main()
''',
            "config/__init__.py": "",
            "config/secrets.py": '''"""Secrets configuration - use environment variables!"""
# All secrets should be in environment variables
# See .env.example for required variables
''',
            ".env.example": '''# Copy to .env and fill in values
DATABASE_URL=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
''',
        },
    ),
]


def run_git(repo_path: Path, *args: str) -> None:
    """Run a git command in the repository."""
    subprocess.run(
        ["git", "-C", str(repo_path)] + list(args),
        check=True,
        capture_output=True,
    )


def create_repo(base_path: Path, spec: RepoSpec) -> None:
    """Create a synthetic repository from specification."""
    repo_path = base_path / spec.name

    # Clean up existing repo
    if repo_path.exists():
        shutil.rmtree(repo_path)

    repo_path.mkdir(parents=True)

    # Initialize git repo
    run_git(repo_path, "init")
    run_git(repo_path, "config", "user.email", "test@example.com")
    run_git(repo_path, "config", "user.name", "Test User")

    # Track files that will have secrets deleted later
    files_to_clean: list[tuple[str, str]] = []

    # Create all files
    for file_path, content in spec.files.items():
        full_path = repo_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

    # Check if any secrets need to be in initial commit then deleted
    for secret in spec.secrets:
        if secret.deleted_in_later_commit:
            # Create file with secret for initial commit
            full_path = repo_path / secret.file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # For historical secrets, create the secret file
            if secret.file_path == "config/secrets.py":
                full_path.write_text(f'''"""Secrets configuration."""
AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'
AWS_SECRET = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
''')
                files_to_clean.append((secret.file_path, spec.files.get(secret.file_path, "")))
            elif secret.file_path == ".env":
                full_path.write_text('''# Environment variables
DATABASE_URL=postgres://admin:password123@prod.example.com/db
SECRET_KEY=supersecretkey123
''')
                files_to_clean.append((secret.file_path, ""))  # Delete .env entirely

    # Initial commit
    run_git(repo_path, "add", "-A")
    run_git(repo_path, "commit", "-m", "Initial commit with project setup")

    # For historical-secrets repo: clean up secrets in second commit
    if files_to_clean:
        for file_path, new_content in files_to_clean:
            full_path = repo_path / file_path
            if new_content:
                full_path.write_text(new_content)
            else:
                # Delete the file
                if full_path.exists():
                    full_path.unlink()

        run_git(repo_path, "add", "-A")
        run_git(repo_path, "commit", "-m", "Remove secrets and add .env.example")

    print(f"Created: {spec.name} - {spec.description}")


def main() -> None:
    """Create all synthetic repositories."""
    script_dir = Path(__file__).parent
    base_path = script_dir.parent / "eval-repos" / "synthetic"

    print("Creating synthetic repositories for gitleaks evaluation...")
    print(f"Output directory: {base_path}")
    print()

    for spec in SYNTHETIC_REPOS:
        create_repo(base_path, spec)

    print()
    print(f"Created {len(SYNTHETIC_REPOS)} synthetic repositories")

    # Summary
    total_secrets = sum(len(spec.secrets) for spec in SYNTHETIC_REPOS)
    historical = sum(1 for spec in SYNTHETIC_REPOS for s in spec.secrets if s.deleted_in_later_commit)
    print(f"Total planted secrets: {total_secrets}")
    print(f"  - Current (in HEAD): {total_secrets - historical}")
    print(f"  - Historical (in git history): {historical}")


if __name__ == "__main__":
    main()
