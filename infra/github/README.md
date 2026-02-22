# GitHub Repository Settings (Terraform)

Manages GitHub branch protection rules, environments, and long-lived branches as Infrastructure as Code.

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
- A GitHub personal access token with scopes: `repo` (full) + `admin:org` (read), or fine-grained: Administration (write), Environments (write), Contents (write)

## Setup

```bash
# From project root:
make github-setup

# Or manually:
cd infra/github
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
```

## Usage

```bash
# Preview changes
make github-plan

# Apply changes
make github-apply
```

## What It Manages

| Resource | Description |
|----------|-------------|
| `github_branch.develop` | Long-lived `develop` branch (from `main`) |
| `github_branch.release` | Long-lived `release` branch (from `main`) |
| `github_branch_protection.main` | PR required, Gates A+B, no force push, no deletion |
| `github_branch_protection.release` | PR required, Gates A+B+C+D, no force push |
| `github_branch_protection.develop` | PR required, Gate A, no force push |
| `github_repository_environment.llm_eval` | `llm-eval` environment with optional reviewers |
| `github_repository_environment.cloud` | `cloud` environment with optional reviewers |

## Auth

Set `GITHUB_TOKEN` as an environment variable. **Never** put tokens in `terraform.tfvars`.

```bash
export GITHUB_TOKEN=ghp_...
```

## Secrets

Environment secrets (`ANTHROPIC_API_KEY`, `HCLOUD_TOKEN`, `SSH_PRIVATE_KEY`) are **not** managed by Terraform. Add them manually in the GitHub UI under Settings > Environments.

## State

State is stored locally (`terraform.tfstate`) and gitignored. This is fine for single-maintainer repos. For team use, consider migrating to a remote backend.

## Relationship to Hetzner Terraform

The Hetzner config in `infra/` (parent directory) is ephemeral: `terraform apply` creates a VM, `terraform destroy` removes it. This GitHub config is persistent: apply once, update as needed. They use separate state files and different providers/tokens.
