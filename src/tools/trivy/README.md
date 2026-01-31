# Trivy Vulnerability Scanner

Trivy is a comprehensive vulnerability scanner for containers, file systems, and IaC configurations. This tool integration wraps the trivy CLI to produce standardized output for the DD Platform.

## Overview

| Aspect | Details |
|--------|---------|
| **Tool** | [trivy](https://github.com/aquasecurity/trivy) by Aqua Security |
| **Purpose** | Vulnerability scanning for packages, containers, and IaC |
| **Languages** | All (dependency-based scanning) |
| **Output Types** | Package vulnerabilities, IaC misconfigurations |

## Features

- **Package Vulnerability Scanning**: Detects CVEs in npm, pip, Maven, NuGet, Go modules, and more
- **IaC Misconfiguration Detection**: Scans Terraform, CloudFormation, Kubernetes manifests
- **SBOM Generation**: Software Bill of Materials support
- **Severity Classification**: CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN

## Quick Start

```bash
# Setup
make setup

# Analyze a repository
make analyze REPO_PATH=/path/to/repo REPO_NAME=my-repo

# Run evaluation
make evaluate
```

## Output Structure

Trivy produces a unified JSON envelope containing:

```json
{
  "metadata": {
    "tool_name": "trivy",
    "tool_version": "0.58.0",
    "run_id": "<uuid>",
    "repo_id": "<uuid>",
    "branch": "main",
    "commit": "<40-hex-sha>",
    "timestamp": "<ISO8601>",
    "schema_version": "1.0.0"
  },
  "data": {
    "tool": "trivy",
    "targets": [...],
    "vulnerabilities": [...],
    "iac_misconfigurations": {...}
  }
}
```

## Scan Types

### Package Vulnerabilities

Trivy scans lockfiles and manifests for known vulnerabilities:

- `package-lock.json`, `yarn.lock` (npm)
- `requirements.txt`, `Pipfile.lock`, `poetry.lock` (Python)
- `pom.xml`, `build.gradle` (Java)
- `packages.config`, `*.csproj` (NuGet)
- `go.sum`, `go.mod` (Go)
- `Gemfile.lock` (Ruby)

### IaC Misconfigurations

Trivy detects security issues in infrastructure code:

- Terraform (`.tf`, `.tfvars`)
- CloudFormation (`.yaml`, `.json`)
- Kubernetes manifests
- Dockerfiles
- Helm charts

## Evaluation

The tool includes programmatic evaluation against ground truth:

```bash
# Run programmatic evaluation
make evaluate

# Run LLM-based evaluation
make evaluate-llm
```

See [EVAL_STRATEGY.md](./EVAL_STRATEGY.md) for evaluation methodology.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REPO_PATH` | `eval-repos/synthetic/vulnerable-npm` | Repository to analyze |
| `REPO_NAME` | `vulnerable-npm` | Project name |
| `OUTPUT_DIR` | `output/runs` | Output directory |
| `TRIVY_TIMEOUT` | `600` | Scan timeout in seconds |

## Requirements

- Python 3.10+
- trivy CLI (installed via `make setup`)
- Docker (optional, for container scanning)

## References

- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Trivy GitHub](https://github.com/aquasecurity/trivy)
- [Trivy Vulnerability Database](https://github.com/aquasecurity/trivy-db)
