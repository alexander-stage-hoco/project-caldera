# Trivy Evaluation Strategy

This document defines the evaluation methodology for the Trivy vulnerability and SBOM analysis tool.

## Overview

The Trivy PoC scans repositories for CVE vulnerabilities, generates SBOM inventories, and detects IaC misconfigurations. Evaluation focuses on:
1. Detection accuracy for known vulnerabilities
2. Severity classification correctness
3. SBOM completeness
4. IaC misconfiguration detection quality

## Decision Thresholds

| Decision | Score Threshold |
|----------|-----------------|
| STRONG_PASS | >= 4.5 |
| PASS | >= 3.5 |
| MARGINAL | >= 2.5 |
| FAIL | < 2.5 |

---

## Programmatic Checks

### Output Quality Checks (OQ-*)

| Check ID | Description | Weight |
|----------|-------------|--------|
| OQ-1 | json_validity | 1.0 |
| OQ-2 | schema_version | 1.0 |
| OQ-3 | required_summary_fields | 1.0 |
| OQ-4 | required_vuln_fields | 1.0 |
| OQ-5 | provenance | 1.0 |
| OQ-6 | timestamp_format | 1.0 |
| OQ-7 | numeric_types | 1.0 |

### Detection Accuracy Checks (DA-*)

| Check ID | Description | Weight |
|----------|-------------|--------|
| DA-1 | critical_detected | 1.0 |
| DA-2 | severity_distribution | 1.0 |
| DA-3 | target_identification | 1.0 |
| DA-4 | fix_availability | 1.0 |

### Count Accuracy Checks (CA-*)

| Check ID | Description | Weight |
|----------|-------------|--------|
| CA-1 | count_accuracy | 1.0 |
| CA-2 | severity_accuracy | 1.0 |
| CA-3 | false_positive_rate | 1.0 |
| CA-4 | package_accuracy | 1.0 |

### Integration Fit Checks (IF-*)

| Check ID | Description | Weight |
|----------|-------------|--------|
| IF-1 | cve_counts_for_security | 1.0 |
| IF-2 | age_for_patch_currency | 1.0 |
| IF-3 | iac_for_infrastructure | 1.0 |
| IF-4 | directory_rollups | 1.0 |
| IF-5 | evidence_transformability | 1.0 |
| IF-6 | sbom_for_inventory | 1.0 |

### Performance Checks (PF-*)

| Check ID | Description | Weight |
|----------|-------------|--------|
| PF-1 | small_repo_speed | 1.0 |
| PF-2 | memory_not_excessive | 1.0 |

---

## Dimension Weights

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Output Quality | 15% | JSON structure, schema compliance, field presence |
| Detection Accuracy | 25% | CVE detection, severity distribution, fix availability |
| Count Accuracy | 20% | Vulnerability counts, severity counts, false positives |
| Integration Fit | 25% | DD schema compatibility, SBOM, IaC, directory rollups |
| Performance | 15% | Scan speed, memory usage |

---

## LLM Judges

### Vulnerability Detection Judge

| Property | Value |
|----------|-------|
| Dimension | vulnerability_detection |
| Weight | 30% |
| Prompt File | prompts/vulnerability_detection.md |

**Evaluation Criteria:**
- True positive rate for known CVEs
- Detection of required packages
- Severity distribution alignment
- Fix availability tracking

### Severity Accuracy Judge

| Property | Value |
|----------|-------|
| Dimension | severity_accuracy |
| Weight | 25% |
| Prompt File | prompts/severity_accuracy.md |

**Evaluation Criteria:**
- CVSS score alignment with severity
- GHSA vs NVD severity consistency
- Critical/High classification accuracy

### SBOM Completeness Judge

| Property | Value |
|----------|-------|
| Dimension | sbom_completeness |
| Weight | 20% |
| Prompt File | prompts/sbom_completeness.md |

**Evaluation Criteria:**
- Package count coverage
- Transitive dependency detection
- Package manager support (npm, pip, Maven, etc.)
- Format compliance (CycloneDX/SPDX)

### IaC Quality Judge

| Property | Value |
|----------|-------|
| Dimension | iac_quality |
| Weight | 25% |
| Prompt File | prompts/iac_quality.md |

**Evaluation Criteria:**
- Terraform misconfiguration detection
- CloudFormation scanning accuracy
- Severity classification of IaC issues
- Actionability of recommendations

---

## LLM Dimension Weights Summary

| Dimension | Weight | Source |
|-----------|--------|--------|
| Vulnerability Detection | 30% | LLM |
| Severity Accuracy | 25% | LLM |
| SBOM Completeness | 20% | LLM |
| IaC Quality | 25% | LLM |

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
| no-vulnerabilities | Clean dependencies | Should produce zero CVEs |
| critical-cves | Critical detection | Known critical CVEs must be flagged |
| outdated-deps | Age tracking | Old dependencies with CVE age calculation |
| mixed-severity | Multi-severity | All severity levels present |
| iac-misconfigs | IaC scanning | Terraform/CloudFormation issues |

### Ground Truth Files

Located in `evaluation/ground-truth/`:
- `no-vulnerabilities.json`
- `critical-cves.json`
- `outdated-deps.json`
- `mixed-severity.json`
- `iac-misconfigs.json`

---

## Ground Truth Schema

```json
{
  "scenario": "critical-cves",
  "description": "Test repo with known critical vulnerabilities",
  "expected_vulnerabilities": {
    "min": 3,
    "max": 10
  },
  "expected_critical": {
    "min": 1,
    "max": 3
  },
  "expected_high": {
    "min": 1,
    "max": 5
  },
  "required_packages": ["log4j-core", "spring-core"],
  "required_cves": ["CVE-2021-44228"],
  "expected_targets": {
    "min": 1,
    "max": 5
  },
  "expected_fix_available_pct": {
    "min": 50,
    "max": 100
  }
}
```

---

## Running Evaluation

```bash
# Programmatic evaluation
make evaluate

# LLM evaluation
make evaluate-llm

# View scorecard
cat evaluation/scorecard.md
```

---

## Evaluation Results Summary

### Latest Programmatic Results

| Metric | Value |
|--------|-------|
| Total Checks | 115 |
| Passed | 115 |
| Failed | 0 |
| Pass Rate | 100% |
| Overall Score | 5.0/5.0 |
| Classification | STRONG_PASS |

### Latest LLM Results

| Judge | Score | Confidence |
|-------|-------|------------|
| vulnerability_detection | 5/5 | 95% |
| severity_accuracy | 4/5 | 85% |
| sbom_completeness | 3/5 | 85% |
| iac_quality | 5/5 | 95% |
| **Overall** | **4.35/5.0** | **90%** |

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-14 | Initial version |
