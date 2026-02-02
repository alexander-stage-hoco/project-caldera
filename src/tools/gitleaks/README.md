# poc-gitleaks

PoC #9: Secret Detection using gitleaks

## Overview

This PoC evaluates **gitleaks** for detecting secrets (API keys, credentials, tokens) in git repositories, including historical secrets that have been removed but remain in git history.

**Lens Coverage**: L7 Security (critical gap)

## Quick Start

```bash
# Install gitleaks and dependencies
make setup

# Create synthetic test repositories
make build-repos

# Run secret analysis
make analyze

# Run evaluation
make evaluate
```

## Results

| Repository | Secrets | In HEAD | In History | Pass Rate |
|------------|---------|---------|------------|-----------|
| no-secrets | 0 | 0 | 0 | 100% |
| api-keys | 2 | 2 | 0 | 100% |
| aws-credentials | 2 | 2 | 0 | 100% |
| mixed-secrets | 2 | 2 | 0 | 100% |
| historical-secrets | 1 | 0 | 1 | 100% |
| **Total** | **7** | **6** | **1** | **100%** |

**Evaluation**: 140/140 checks passed (100%)

## Secret Types Detected

| Rule ID | Description | Example |
|---------|-------------|---------|
| `aws-access-token` | AWS Access Key IDs | `AKIAIOSFODNN7EXAMPLE` |
| `github-pat` | GitHub Personal Access Tokens | `ghp_xxxx...` |
| `stripe-access-token` | Stripe API Keys | `sk_live_xxxx...` |
| `generic-api-key` | Generic API keys and secrets | Various patterns |

## Architecture

```
Layer 1: gitleaks Tool (Go binary)
  ├── Scan git history
  ├── Pattern matching (regex rules)
  ├── Entropy analysis
  └── Output: JSON findings

Layer 2: Python Analyzer
  ├── Parse gitleaks JSON
  ├── Determine HEAD vs historical
  ├── Compute aggregates
  └── Directory rollups

Layer 3: Evaluation Framework
  ├── 28 checks per repository
  ├── 4 categories (Accuracy, Coverage, Detection, Performance)
  └── Zero tolerance ground truth
```

## Evaluation Checks (28 per repo)

### Accuracy (SA-1 to SA-10)
- Secret counts match expected
- Rule IDs detected correctly
- File locations accurate
- Line numbers correct

### Coverage (SC-1 to SC-8)
- Schema fields present
- Findings have required fields
- Directory metrics computed

### Detection (SD-1 to SD-6)
- No false negatives
- No unexpected rule types
- Historical secrets detected
- Clean repos pass clean

### Performance (SP-1 to SP-4)
- Scan time within threshold
- Reasonable time per finding

## Key Findings

1. **Gitleaks detects historical secrets** - Secrets removed from HEAD but still in git history are found
2. **Pattern-based detection** - Uses regex patterns, not just entropy
3. **Fast scanning** - Typically <50ms for small repos
4. **Specific rule IDs** - Each secret type has a specific rule (aws-access-token, github-pat, etc.)

## Files

| File | Lines | Description |
|------|-------|-------------|
| `scripts/secret_analyzer.py` | ~280 | Main analyzer wrapping gitleaks |
| `scripts/create_synthetic_repos.py` | ~170 | Synthetic repo generator |
| `scripts/evaluate.py` | ~120 | Evaluation orchestrator |
| `scripts/checks/__init__.py` | ~140 | Check framework |
| `scripts/checks/accuracy.py` | ~130 | Accuracy checks |
| `scripts/checks/coverage.py` | ~100 | Coverage checks |
| `scripts/checks/detection.py` | ~100 | Detection checks |
| `scripts/checks/performance.py` | ~70 | Performance checks |

## Synthetic Test Repositories

| Repository | Description | Secrets |
|------------|-------------|---------|
| `no-secrets` | Clean baseline | 0 |
| `api-keys` | API keys in config | 2 (GitHub PAT, Stripe) |
| `aws-credentials` | AWS access keys | 2 (both AWS access tokens) |
| `mixed-secrets` | Multiple types | 2 (JWT, Stripe) |
| `historical-secrets` | Removed secrets | 1 (AWS in history) |

## Makefile Variables

```bash
# Run analysis with custom output directory
make analyze REPO_PATH=/path/to/repo OUTPUT_DIR=/custom/output

# Available variables:
# REPO_PATH   - Repository to analyze (default: eval-repos/synthetic)
# REPO_NAME   - Name for output files (default: synthetic)
# OUTPUT_DIR  - Output directory (default: output/runs)
```

## Single Repository Analysis

To analyze a specific repository:

```bash
make analyze-repo REPO=/path/to/repository OUTPUT_DIR=/path/to/output
```

The output will be written to `OUTPUT_DIR/<repo-name>.json`.
