# Evaluation Strategy: Trivy

This document describes the evaluation methodology for the Trivy vulnerability scanner integration.

## Philosophy & Approach

### Why Hybrid Evaluation?

The evaluation combines **programmatic checks** with **LLM-as-a-Judge** evaluation:

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 60% | Objective, reproducible, fast |
| LLM Judges | 40% | Semantic understanding, actionability |

This hybrid approach validates both technical accuracy and practical usefulness.

### Rationale for 60/40 Split

**Programmatic checks (60%)** ensure:
- Deterministic, reproducible results across runs
- Fast feedback during development
- Clear pass/fail criteria for CI/CD gates
- Objective measurement against ground truth

**LLM judges (40%)** provide:
- Semantic understanding of vulnerability categorization
- Assessment of actionability for security teams
- Nuanced evaluation of prioritization quality
- Detection of subtle issues missed by numeric checks

### Evaluation Principles

1. **Ground truth anchored**: All evaluations reference synthetic test projects with known vulnerabilities
2. **Multi-dimensional**: Accuracy, coverage, and completeness all matter
3. **Transparent scoring**: Every score has traceable evidence
4. **Severity aware**: Evaluation weights critical vulnerabilities higher

---

## Decision Thresholds

### Combined Score Calculation

```python
# Normalize programmatic score to 1-5 scale
programmatic_normalized = 1 + (programmatic_score * 4)  # 0-1 -> 1-5

# Weighted combination
combined_score = (0.60 * programmatic_normalized) + (0.40 * llm_score)
```

### Thresholds

| Decision | Combined Score | Interpretation |
|----------|----------------|----------------|
| STRONG_PASS | >= 4.0 | Excellent, production-ready |
| PASS | >= 3.5 | Good, minor improvements needed |
| WEAK_PASS | >= 3.0 | Acceptable with caveats |
| FAIL | < 3.0 | Significant issues |

---

## Dimension Summary

All evaluation dimensions with their check counts and weights:

| Category | Dimension | Checks | Weight | Focus Area |
|----------|-----------|--------|--------|------------|
| Programmatic | Accuracy | TR-AC-1 to TR-AC-5 | 40% | Vulnerability counts, severity |
| Programmatic | Coverage | TR-CV-1 to TR-CV-3 | 30% | Target and package coverage |
| Programmatic | Completeness | TR-CM-1 to TR-CM-4 | 30% | Data structure integrity |
| LLM | Vulnerability Accuracy | 1 judge | 35% | CVE classification |
| LLM | Coverage Completeness | 1 judge | 25% | Data extraction quality |
| LLM | Actionability | 1 judge | 20% | Report usefulness |

**Total**: 12 programmatic checks + 3 LLM judges

---

## Complete Check Catalog

### Programmatic Checks (12 Total)

#### Accuracy Checks (TR-AC-1 to TR-AC-5)

| ID | Name | Severity | Pass Criteria |
|----|------|----------|---------------|
| TR-AC-1 | Vulnerability count accuracy | Critical | Total vulns within +/-10% of expected |
| TR-AC-2 | Critical count accuracy | Critical | Critical count matches expected |
| TR-AC-3 | High count accuracy | High | High count within expected range |
| TR-AC-4 | CVE ID presence | High | All expected CVEs detected |
| TR-AC-5 | Severity classification | Medium | Severities match CVE database |

#### Coverage Checks (TR-CV-1 to TR-CV-3)

| ID | Name | Severity | Pass Criteria |
|----|------|----------|---------------|
| TR-CV-1 | Target coverage | High | All lockfiles detected as targets |
| TR-CV-2 | Package coverage | Medium | All vulnerable packages identified |
| TR-CV-3 | IaC file coverage | Medium | All IaC files scanned |

#### Completeness Checks (TR-CM-1 to TR-CM-4)

| ID | Name | Severity | Pass Criteria |
|----|------|----------|---------------|
| TR-CM-1 | Fix availability | High | Fixed versions present where available |
| TR-CM-2 | CVSS scores | Medium | CVSS scores present for major CVEs |
| TR-CM-3 | Target metadata | Medium | All targets have type and path |
| TR-CM-4 | Vulnerability fields | High | Required fields present (id, package, severity) |

---

## LLM Judge Dimensions (3 Judges)

### Judge Weights

| Judge | Weight | Focus |
|-------|--------|-------|
| Vulnerability Accuracy | 35% | Are CVEs correctly identified and classified? |
| Coverage Completeness | 25% | Are all vulnerable dependencies detected? |
| Actionability | 20% | Can security teams act on this report? |

### Vulnerability Accuracy Judge (35%)

**Sub-dimensions**:
- CVE identification (40%): Known CVEs are correctly identified
- Severity assignment (30%): Severity matches NVD classification
- Package attribution (30%): Vulnerabilities linked to correct packages

**Scoring Rubric**:

| Score | Criteria |
|-------|----------|
| 5 | All CVEs correctly identified and classified |
| 4 | 95%+ correctly identified, minor severity mismatches |
| 3 | 85%+ correctly identified |
| 2 | Significant identification errors |
| 1 | CVE identification unreliable |

### Coverage Completeness Judge (25%)

**Sub-dimensions**:
- Lockfile detection (40%): All package manifests found
- Dependency scanning (30%): Direct and transitive deps covered
- IaC scanning (30%): Infrastructure files scanned

**Scoring Rubric**:

| Score | Criteria |
|-------|----------|
| 5 | Complete coverage with no gaps |
| 4 | Minor gaps in edge case files |
| 3 | Some lockfiles or IaC files missed |
| 2 | Significant coverage gaps |
| 1 | Critical files not scanned |

### Actionability Judge (20%)

**Sub-dimensions**:
- Fix guidance (40%): Fixed versions clearly indicated
- Prioritization (30%): Critical issues highlighted
- Remediation path (30%): Clear next steps provided

**Scoring Rubric**:

| Score | Criteria |
|-------|----------|
| 5 | Immediately actionable with clear fix paths |
| 4 | Clear with minor presentation improvements |
| 3 | Usable but requires interpretation |
| 2 | Difficult to prioritize remediation |
| 1 | Output is not actionable |

---

## Scoring Methodology

### Aggregate Score Calculation

The overall score combines programmatic and LLM evaluations:

```
total_score = (
    accuracy_score * 0.40 +
    coverage_score * 0.30 +
    completeness_score * 0.30
) * 0.60 + llm_score * 0.40
```

### Programmatic Check Scoring

Each programmatic check returns:
- `pass`: 100 points
- `warn`: 50 points
- `fail`: 0 points

Dimension score = (sum of check scores) / (max possible) * 5

### LLM Judge Scoring

Each LLM judge returns a score 1-5:
- 5: Excellent - all criteria met
- 4: Good - minor issues
- 3: Acceptable - some gaps
- 2: Poor - significant issues
- 1: Unacceptable - unreliable

### Score Aggregation

```python
# Normalize programmatic score to 1-5 scale
programmatic_normalized = 1 + (programmatic_score * 4)  # 0-1 -> 1-5

# Weighted combination (60/40 split)
combined_score = (0.60 * programmatic_normalized) + (0.40 * llm_score)
```

---

## Test Scenarios

### Synthetic Repositories

| Repo | Type | Purpose | Expected |
|------|------|---------|----------|
| vulnerable-npm | npm | Known CVEs in dependencies | 5-10 vulns, 1+ critical |
| iac-terraform | Terraform | IaC misconfigurations | 3-8 misconfigs |

### Vulnerability Types Tested

1. Package vulnerabilities (CVEs)
2. IaC misconfigurations (CIS benchmarks)
3. Severity levels (CRITICAL, HIGH, MEDIUM, LOW)

---

## Running Evaluation

### Programmatic Evaluation

```bash
# Evaluate single file
make evaluate-single REPO_NAME=vulnerable-npm

# Evaluate all output files
make evaluate

# Verbose output
make evaluate VERBOSE=1
```

### LLM Evaluation

```bash
# Full LLM evaluation (3 judges)
make evaluate-llm

# Specific model
make evaluate-llm MODEL=opus-4.5
```

---

## Ground Truth Specifications

### Source Data

Ground truth files in `evaluation/ground-truth/` contain expected values:

```json
{
  "id": "vulnerable-npm",
  "description": "npm project with known vulnerable dependencies",
  "package_manager": "npm",
  "expected_targets": ["package-lock.json"],
  "expected_vulnerabilities": { "min": 5, "max": 15 },
  "expected_critical": { "min": 1, "max": 3 },
  "expected_high": { "min": 2, "max": 5 },
  "known_cves": ["CVE-2021-23337", "CVE-2021-44228"],
  "notes": "Uses lodash 4.17.15 with prototype pollution vulnerability"
}
```

### Tolerance Ranges

| Metric | Tolerance | Rationale |
|--------|-----------|-----------|
| Vulnerability count | +/-10% | Database updates may add/remove CVEs |
| Critical count | +/-1 | Classification may change |
| High count | +/-2 | Classification may change |
| Package count | Exact | Lockfile is deterministic |

---

## Evidence Collection

Each check collects evidence for transparency:

```python
evidence = {
    "expected_range": {"min": 5, "max": 15},
    "actual_value": 8,
    "within_range": True,
    "source": "vulnerabilities.count"
}
```

---

## Rollup Validation

Rollups:
- directory_counts_direct
- directory_counts_recursive

Tests:
- src/sot-engine/dbt/tests/test_rollup_trivy_direct_vs_recursive.sql

## Extending Evaluation

### Adding New Checks

1. Create check function in `scripts/checks/`
2. Add `@check` decorator with ID and metadata
3. Update ground truth if needed
4. Run `make evaluate` to verify

### Adding New Test Scenarios

1. Create test repo in `eval-repos/synthetic/`
2. Create ground truth file in `evaluation/ground-truth/`
3. Run analysis and verify results
4. Update evaluation expectations

---

## References

- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [NVD CVE Database](https://nvd.nist.gov/)
- [CVSS Scoring](https://www.first.org/cvss/)
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685)
