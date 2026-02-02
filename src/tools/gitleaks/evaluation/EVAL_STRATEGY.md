# Gitleaks Evaluation Strategy

This document defines the evaluation methodology for the Gitleaks secret detection tool.

## Overview

The Gitleaks PoC detects secrets and credentials in git repositories. Evaluation focuses on:
1. Detection accuracy for known secrets
2. False positive rate
3. Secret type coverage
4. Severity classification quality

## Decision Thresholds

| Decision | Score Threshold |
|----------|-----------------|
| STRONG_PASS | ≥ 4.0 |
| PASS | ≥ 3.5 |
| WEAK_PASS | ≥ 3.0 |
| FAIL | < 3.0 |

---

## Programmatic Checks

### Secret Detection Checks (SD-*)

| Check ID | Description | Weight |
|----------|-------------|--------|
| SD-1 | Basic secret detection works | 1.0 |
| SD-2 | Expected secrets are detected | 1.0 |
| SD-3 | Secret count matches expected | 1.0 |
| SD-4 | Secret types correctly identified | 1.0 |
| SD-5 | Line numbers are accurate | 1.0 |
| SD-6 | File paths are correct | 1.0 |

### Secret Coverage Checks (SC-*)

| Check ID | Description | Weight |
|----------|-------------|--------|
| SC-1 | AWS credentials detected | 1.0 |
| SC-2 | API keys detected | 1.0 |
| SC-3 | Private keys detected | 1.0 |
| SC-4 | Database credentials detected | 1.0 |
| SC-5 | GitHub tokens detected | 1.0 |
| SC-6 | Slack tokens detected | 1.0 |
| SC-7 | Generic secrets detected | 1.0 |
| SC-8 | Historical secrets detected | 1.0 |

### Secret Accuracy Checks (SA-*)

| Check ID | Description | Weight |
|----------|-------------|--------|
| SA-8 | No false positives in clean files | 1.0 |
| SA-9 | Test secrets correctly handled | 1.0 |
| SA-10 | Severity classification correct | 1.0 |

### Secret Performance Checks (SP-*)

| Check ID | Description | Weight |
|----------|-------------|--------|
| SP-2 | Small repo scan time | 1.0 |
| SP-3 | Large repo scan time | 1.0 |
| SP-4 | Output size reasonable | 1.0 |

---

## LLM Judges

### Detection Accuracy Judge

| Property | Value |
|----------|-------|
| Dimension | detection_accuracy |
| Weight | 35% |
| Prompt File | prompts/detection_accuracy.md |

**Evaluation Criteria:**
- True positive rate
- Location accuracy (file paths, line numbers)
- Rule matching quality

### False Positive Judge

| Property | Value |
|----------|-------|
| Dimension | false_positive |
| Weight | 25% |
| Prompt File | prompts/false_positive.md |

**Evaluation Criteria:**
- False positive count and rate
- Pattern quality
- Signal-to-noise ratio

### Secret Coverage Judge

| Property | Value |
|----------|-------|
| Dimension | secret_coverage |
| Weight | 20% |
| Prompt File | prompts/secret_coverage.md |

**Evaluation Criteria:**
- Type breadth (API keys, tokens, passwords)
- Format handling (base64, JSON, etc.)
- Historical detection (git history)

### Severity Classification Judge

| Property | Value |
|----------|-------|
| Dimension | severity_classification |
| Weight | 20% |
| Prompt File | prompts/severity_classification.md |

**Evaluation Criteria:**
- Classification accuracy
- Risk assessment quality
- Context awareness

---

## Dimension Weights Summary

| Dimension | Weight | Source |
|-----------|--------|--------|
| Detection Accuracy | 35% | LLM |
| False Positive Rate | 25% | LLM |
| Secret Coverage | 20% | LLM |
| Severity Classification | 20% | LLM |

## Combined Scoring

The final score combines programmatic and LLM evaluations:

```
combined_score = (programmatic_score * 0.60) + (llm_score * 0.40)
```

---

## Test Scenarios

### Synthetic Repositories

| Scenario | Purpose | Description |
|----------|---------|-------------|
| api-keys | API key detection | Various API key formats |
| aws-credentials | AWS credential detection | Access keys, secrets |
| historical-secrets | Git history scanning | Deleted secrets in history |
| mixed-secrets | Multi-type detection | Mix of secret types |
| no-secrets | Clean codebase | Should produce no findings |

### Ground Truth Files

Located in `evaluation/ground-truth/`:
- `api-keys.json`
- `aws-credentials.json`
- `historical-secrets.json`
- `mixed-secrets.json`
- `no-secrets.json`

---

## Running Evaluation

```bash
# Programmatic evaluation
make evaluate

# LLM evaluation
make evaluate-llm

# Combined evaluation
make evaluate-combined

# Quick evaluation (subset of checks)
make evaluate-quick
```

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-14 | Initial version |
