# Gitleaks PoC Evaluation Strategy

This document describes the evaluation framework for the Gitleaks secret detection tool PoC, including the complete check catalog, scoring methodology, weight allocation, and decision thresholds.

## Philosophy & Approach

The evaluation framework assesses Gitleaks' fitness for integration into the DD Platform across 8 dimensions with 38 individual checks.

### Version History

| Version | Dimensions | Checks | Description |
|---------|------------|--------|-------------|
| v1.0 (Original) | 4 | 28 | Initial evaluation framework |
| v2.0 (Extended) | 6 | 30 | Added Output Quality and Integration Fit |
| v3.0 (Caldera) | 8 | 38 | Added Edge Cases and Rollup Validation |

### Key Changes in v3.0

1. **New Dimensions Added:**
   - Edge Cases (EC-1 to EC-4) - Empty repos, unicode paths, large files, binary files
   - Rollup Validation (RV-1 to RV-4) - Directory rollup invariants

2. **Caldera Migration Updates:**
   - Output Quality validates Caldera envelope format (metadata + data)
   - BaseJudge inherits from shared module for observability
   - Prompt templates use standardized {{ evidence }} placeholder
   - LLM judges load all ground truth files for comprehensive evaluation

### Key Changes in v2.0

1. **New Dimensions Added:**
   - Output Quality (OQ-1) - Schema validation
   - Integration Fit (IF-1) - Path normalization

2. **Evaluation Principles:**
   - Ground truth anchored: All evaluations reference synthetic test repositories
   - Multi-dimensional: Accuracy, coverage, and detection quality all matter
   - Transparent scoring: Every score has traceable evidence
   - Security-focused: Prioritizes secret detection accuracy and zero false negatives

---

## Dimension Summary

| Dimension | Code | Checks | Weight | Description |
|-----------|------|--------|--------|-------------|
| Secret Accuracy | SA | 11 | 30% | Core detection accuracy |
| Coverage | SC | 8 | 12% | Output completeness |
| Detection Quality | SD | 6 | 20% | Detection characteristics |
| Performance | SP | 4 | 8% | Execution speed |
| Output Quality | OQ | 1 | 5% | Schema compliance |
| Integration Fit | IF | 1 | 5% | DD Platform compatibility |
| Edge Cases | EC | 4 | 10% | Edge case handling |
| Rollup Validation | RV | 4 | 10% | Directory rollup invariants |
| **Total** | | **39** | **100%** | |

---

## Complete Check Catalog

### 1. Secret Accuracy (SA) - 35% Weight

Validates that Gitleaks correctly detects all expected secrets with accurate metadata.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| SA-1 | Total Secret Count | Total secrets match expected | `total_secrets == expected.total_secrets` |
| SA-2 | Unique Secret Count | Unique secrets match expected | `unique_secrets == expected.unique_secrets` |
| SA-3 | Secrets in HEAD | HEAD secrets match expected | `secrets_in_head == expected.secrets_in_head` |
| SA-4 | Secrets in History | Historical secrets match expected | `secrets_in_history == expected.secrets_in_history` |
| SA-5 | Files with Secrets | File count matches expected | `files_with_secrets == expected.files_with_secrets` |
| SA-6 | Commits with Secrets | Commit count matches expected | `commits_with_secrets == expected.commits_with_secrets` |
| SA-7 | Rule IDs Detected | Expected rule IDs are found | All `expected.rule_ids` in `secrets_by_rule.keys()` |
| SA-8 | Files with Secrets List | Expected files are found | All `expected.files_with_secrets_list` in `files.keys()` |
| SA-9 | Rule Counts Match | Per-rule counts match expected | `secrets_by_rule[rule] == expected.secrets_by_rule[rule]` |
| SA-10 | Finding Line Numbers | Expected findings at exact locations | All `file:rule:line` fingerprints match |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 10 | 5 |
| 8-9 | 4 |
| 6-7 | 3 |
| 4-5 | 2 |
| 0-3 | 1 |

---

### 2. Coverage (SC) - 15% Weight

Validates the structure and completeness of Gitleaks' JSON output.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| SC-1 | Schema Version | Schema version present | `schema_version is not None` |
| SC-2 | Tool Version | Tool version present | `tool_version` is non-empty string |
| SC-3 | Timestamp | Timestamp present | `timestamp is not None` |
| SC-4 | Summary Metrics | All summary fields present | Fields: `total_secrets`, `unique_secrets`, `secrets_in_head`, `secrets_in_history`, `files_with_secrets`, `commits_with_secrets` |
| SC-5 | Findings List | Findings list present | `"findings" in results` |
| SC-6 | Files Summary | Files summary present | `"files" in results` |
| SC-7 | Directory Metrics | Directory metrics present | `"directories" in results` |
| SC-8 | Finding Fields | All findings have required fields | Fields: `file_path`, `line_number`, `rule_id`, `secret_type`, `commit_hash`, `fingerprint` |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 8 | 5 |
| 7 | 4 |
| 5-6 | 3 |
| 3-4 | 2 |
| 0-2 | 1 |

---

### 3. Detection Quality (SD) - 25% Weight

Validates detection characteristics including false positive/negative rates.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| SD-1 | No False Negatives | All known secrets found | `actual_secrets >= expected_secrets` |
| SD-2 | No Unexpected Rules | No false positive rule types | No unexpected rule IDs when expected rules defined |
| SD-3 | Historical Detection | Historical secrets correctly identified | `historical_count == expected_historical` |
| SD-4 | Clean Repo Zero Secrets | Clean repos have no findings | When `expected.total_secrets == 0`, `actual.total_secrets == 0` |
| SD-5 | Entropy Values Valid | Entropy in reasonable range | All findings: `0 <= entropy <= 8` |
| SD-6 | Secrets Masked | All secrets have masked preview | All previews contain `*` or are <= 8 chars |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 6 | 5 |
| 5 | 4 |
| 4 | 3 |
| 2-3 | 2 |
| 0-1 | 1 |

---

### 4. Performance (SP) - 10% Weight

Validates execution speed and resource usage.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| SP-1 | Scan Time | Total scan time within threshold | `scan_time_ms <= thresholds.max_scan_time_ms` (default: 10000ms) |
| SP-2 | Time Per Commit | Scan time reasonable per commit | `time_per_commit <= thresholds.max_ms_per_commit` (default: 1000ms) |
| SP-3 | Time Per Finding | Scan time reasonable per finding | `time_per_finding <= thresholds.max_ms_per_finding` (default: 500ms) |
| SP-4 | Memory/Findings Size | Findings list reasonable size | `len(findings) <= thresholds.max_findings_for_test` (default: 100) |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 4 | 5 |
| 3 | 4 |
| 2 | 3 |
| 1 | 2 |
| 0 | 1 |

---

### 5. Output Quality (OQ) - 5% Weight

Validates schema compliance for Caldera envelope format.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| OQ-1 | Schema Validation | Root wrapper follows Caldera envelope | Required root fields: `metadata`, `data`. Required metadata fields: `tool_name`, `tool_version`, `run_id`, `repo_id`, `branch`, `commit`, `timestamp`, `schema_version`. Required data fields: `tool`, `tool_version`, `total_secrets`, `findings`. `metadata.tool_name == "gitleaks"` and `data.tool == "gitleaks"` |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 1 | 5 |
| 0 | 1 |

---

### 6. Integration Fit (IF) - 5% Weight

Validates compatibility with DD Platform requirements.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| IF-1 | Relative Paths | All file paths are relative | No findings have `os.path.isabs(file_path) == True` |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 1 | 5 |
| 0 | 1 |

---

### 7. Edge Cases (EC) - 10% Weight

Validates handling of edge cases in secret detection.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| EC-1 | Empty Repo | Empty repos produce valid output | Valid output with 0 secrets and findings list |
| EC-2 | Unicode Paths | File paths handle unicode correctly | All paths are valid UTF-8 strings |
| EC-3 | Large Files | Scan completes for repos with large files | Scan completes within timeout threshold |
| EC-4 | Binary Files | Binary files are skipped or handled gracefully | No findings in binary file extensions |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 4 | 5 |
| 3 | 4 |
| 2 | 3 |
| 1 | 2 |
| 0 | 1 |

---

### 8. Directory Aggregation (RV) - 10% Weight

Validates directory rollup invariants for aggregated metrics.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| RV-1 | Recursive >= Direct Secrets | Recursive counts include direct | `recursive_secret_count >= direct_secret_count` |
| RV-2 | Recursive >= Direct Files | Recursive file counts include direct | `recursive_file_count >= direct_file_count` |
| RV-3 | Non-negative Counts | All rollup counts are non-negative | All counts >= 0 |
| RV-4 | Root Equals Total | Root recursive equals total secrets | `root.recursive_secret_count == total_secrets` |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 4 | 5 |
| 3 | 4 |
| 2 | 3 |
| 1 | 2 |
| 0 | 1 |

---

## Rollup Validation Details

Rollups:
- directory_counts_direct
- directory_counts_recursive

Tests:
- src/tools/gitleaks/tests/unit/test_rollup_invariants.py
- src/sot-engine/dbt/tests/test_rollup_gitleaks_direct_vs_recursive.sql

### Directory Rollup Invariants

| Invariant | Description | Formula |
|-----------|-------------|---------|
| RV-1 | Recursive >= Direct | `recursive_secret_count >= direct_secret_count` |
| RV-2 | Recursive files >= Direct files | `recursive_file_count >= direct_file_count` |
| RV-3 | Non-negative counts | All counts >= 0 |
| RV-4 | Root recursive equals total | Root `recursive_secret_count == total_secrets` |

### Validation Rules

1. **Direct counts** include only secrets in files directly within a directory (not subdirectories)
2. **Recursive counts** include secrets in the directory plus all nested subdirectories
3. For leaf directories (no subdirectories): `direct_count == recursive_count`
4. For parent directories: `recursive_count = direct_count + sum(child.recursive_count)`

### Example Validation

```
directories/
├── src/           # direct: 1, recursive: 3
│   ├── api/       # direct: 1, recursive: 2
│   │   └── keys.py  # 1 secret
│   │   └── auth/    # direct: 1, recursive: 1
│   │       └── token.py  # 1 secret
│   └── config.py  # 1 secret
└── .env           # 1 secret (in root)

root: direct: 1, recursive: 4 (total_secrets = 4) ✓
```

### Rollup Check Implementation

```python
def validate_rollups(directories: dict, total_secrets: int) -> list[CheckResult]:
    results = []
    for path, metrics in directories.items():
        direct = metrics.get("direct_secret_count", 0)
        recursive = metrics.get("recursive_secret_count", 0)

        # RV-1: Recursive >= Direct
        if recursive < direct:
            results.append(CheckResult(
                check_id="RV-1",
                passed=False,
                message=f"{path}: recursive ({recursive}) < direct ({direct})"
            ))

    # RV-4: Root recursive equals total
    root_recursive = directories.get(".", {}).get("recursive_secret_count", 0)
    if root_recursive != total_secrets:
        results.append(CheckResult(
            check_id="RV-4",
            passed=False,
            message=f"Root recursive ({root_recursive}) != total_secrets ({total_secrets})"
        ))

    return results
```

---

## Scoring Methodology

### Per-Dimension Score Calculation

1. Run all checks for the dimension
2. Count passed checks
3. Map to 1-5 score using dimension-specific scoring table
4. Multiply by dimension weight to get weighted score

```python
dimension_score = scoring_table[passed_count]
weighted_score = dimension_score * dimension_weight
```

### Total Score Calculation

```python
total_score = sum(d.weighted_score for d in dimensions)
```

The maximum possible score is 5.0 (all dimensions score 5/5).

### Combined Scoring Formula

```python
# Programmatic component (per-dimension weighted)
prog_accuracy = accuracy_passed / 10 * 0.35
prog_coverage = coverage_passed / 8 * 0.15
prog_detection = detection_passed / 6 * 0.25
prog_performance = performance_passed / 4 * 0.10
prog_output = output_quality_passed / 1 * 0.05
prog_integration = integration_fit_passed / 1 * 0.10
programmatic_score = sum([prog_*])

# Normalize to 1-5 scale
programmatic_normalized = 1 + (programmatic_score * 4)

# LLM component (already 1-5 scale)
llm_score = (
    detection_accuracy * 0.35 +
    false_positive_rate * 0.25 +
    secret_coverage * 0.20 +
    severity_classification * 0.20
)

# Combined (60/40 split)
combined_score = (0.60 * programmatic_normalized) + (0.40 * llm_score)
```

---

## Decision Thresholds

| Decision | Threshold | Description |
|----------|-----------|-------------|
| **STRONG_PASS** | >= 4.0 | Excellent fit, approved for immediate use |
| **PASS** | >= 3.5 | Good fit, approved with minor reservations |
| **WEAK_PASS** | >= 3.0 | Marginal fit, review failing checks before proceeding |
| **FAIL** | < 3.0 | Does not meet requirements |

### Decision Logic

```python
if total_score >= 4.0:
    return "STRONG_PASS"
elif total_score >= 3.5:
    return "PASS"
elif total_score >= 3.0:
    return "WEAK_PASS"
else:
    return "FAIL"
```

---

## Weight Allocation Rationale

| Dimension | Weight | Rationale |
|-----------|--------|-----------|
| Secret Accuracy | 35% | Highest priority - secret detection must be accurate |
| Detection Quality | 25% | Zero false negatives is critical for security |
| Coverage | 15% | Output must be complete and usable |
| Integration Fit | 10% | Required for DD Platform integration |
| Performance | 10% | Fast scanning enables CI/CD integration |
| Output Quality | 5% | Schema compliance is binary (works or doesn't) |

---

## Ground Truth Specifications

### Synthetic Repository Structure

```
eval-repos/synthetic/
├── no-secrets/          # Clean baseline (0 secrets)
├── api-keys/            # API keys (GitHub PAT, Stripe)
├── aws-credentials/     # AWS access key IDs
├── mixed-secrets/       # Multiple secret types
└── historical-secrets/  # Secrets in git history only
```

**Total: 5 scenarios covering different secret patterns**

### Expected Values by Scenario

| Scenario | Total | HEAD | History | Files | Rule Types |
|----------|-------|------|---------|-------|------------|
| no-secrets | 0 | 0 | 0 | 0 | none |
| api-keys | 2 | 2 | 0 | 2 | github-pat, stripe-access-token |
| aws-credentials | 2 | 2 | 0 | 2 | aws-access-token |
| mixed-secrets | 4+ | varies | varies | varies | multiple |
| historical-secrets | 2+ | 0 | 2+ | varies | varies |

### Ground Truth Schema

```json
{
  "schema_version": "1.0",
  "scenario": "scenario-name",
  "description": "Human-readable description",
  "generated_at": "2026-01-21T18:48:53Z",
  "repo_path": "eval-repos/synthetic/scenario-name",
  "expected": {
    "total_secrets": 2,
    "unique_secrets": 2,
    "secrets_in_head": 2,
    "secrets_in_history": 0,
    "files_with_secrets": 2,
    "commits_with_secrets": 1,
    "rule_ids": ["github-pat", "stripe-access-token"],
    "files_with_secrets_list": [".env", "config/api.py"],
    "secrets_by_rule": {
      "github-pat": 1,
      "stripe-access-token": 1
    },
    "findings": [
      {
        "file_path": ".env",
        "rule_id": "github-pat",
        "line_number": 3
      }
    ],
    "thresholds": {
      "max_scan_time_ms": 5000,
      "max_ms_per_commit": 1000,
      "max_ms_per_finding": 500,
      "max_findings_for_test": 100
    }
  }
}
```

### Tolerance Policy

| Metric | Tolerance | Rationale |
|--------|-----------|-----------|
| Secret counts | Exact (0) | Detection must be precise |
| Rule IDs | Exact | Specific patterns must match |
| Line numbers | Exact | Finding locations must be accurate |
| File paths | Exact | Files must be correctly identified |
| Scan time | Threshold | Performance varies by hardware |
| Entropy | Range (0-8) | Reasonable mathematical bounds |

---

## LLM Judge Dimensions (4 Judges)

### Judge Weights

| Judge | Weight | Focus |
|-------|--------|-------|
| Detection Accuracy | 35% | Are planted secrets found? |
| False Positive Rate | 25% | Are clean repos flagged clean? |
| Secret Coverage | 20% | Are different secret types identified? |
| Severity Classification | 20% | Are severity levels reasonable? |

### Detection Accuracy Judge (35%)

**Sub-dimensions:**
- Secret identification (40%): Known secrets are found
- Location accuracy (30%): Correct file and line numbers
- Historical detection (30%): Removed-but-committed secrets found

**Scoring Rubric:**
| Score | Criteria |
|-------|----------|
| 5 | All planted secrets detected with exact locations |
| 4 | 95%+ secrets detected, minor location discrepancies |
| 3 | 85%+ secrets detected |
| 2 | Significant detection gaps |
| 1 | Major secrets missed |

### False Positive Rate Judge (25%)

**Sub-dimensions:**
- Clean repo precision (50%): No false alarms on clean repos
- Legitimate value filtering (30%): Config values not flagged
- Rule specificity (20%): Patterns match actual secrets only

**Scoring Rubric:**
| Score | Criteria |
|-------|----------|
| 5 | Zero false positives on clean repos |
| 4 | < 1% false positive rate |
| 3 | 1-5% false positive rate |
| 2 | 5-10% false positive rate |
| 1 | > 10% false positive rate |

### Secret Coverage Judge (20%)

**Sub-dimensions:**
- Rule variety (50%): Multiple secret types detected
- Ecosystem coverage (30%): AWS, GitHub, Stripe, etc.
- Pattern completeness (20%): Variations of same secret type

**Scoring Rubric:**
| Score | Criteria |
|-------|----------|
| 5 | All expected secret types detected with correct classification |
| 4 | Most types detected, minor classification issues |
| 3 | Common types detected |
| 2 | Limited type coverage |
| 1 | Only generic detection |

### Severity Classification Judge (20%)

**Sub-dimensions:**
- Type-based severity (50%): AWS keys vs test tokens
- Context awareness (30%): Production vs test files
- Actionability (20%): Severity helps triage

**Scoring Rubric:**
| Score | Criteria |
|-------|----------|
| 5 | Severity reflects actual risk accurately |
| 4 | Reasonable severity, minor discrepancies |
| 3 | Basic severity classification |
| 2 | Inconsistent severity |
| 1 | No useful severity information |

---

## Running Evaluation

### Prerequisites

1. Gitleaks binary installed (v8.18.0+)
2. Python virtual environment in `.venv/`
3. Synthetic test repositories in `eval-repos/synthetic/`
4. Ground truth files in `evaluation/ground-truth/`

### Commands

```bash
# Setup environment
make setup

# Run full evaluation
make evaluate

# Evaluate specific scenario
make evaluate-single REPO_NAME=api-keys

# Run LLM evaluation
make evaluate-llm

# Combined evaluation
make evaluate-all

# Verbose output
make evaluate VERBOSE=1
```

### Output Artifacts

| File | Description |
|------|-------------|
| `evaluation/scorecard.md` | Human-readable evaluation report |
| `evaluation/results/<scenario>_checks.json` | Detailed check results with evidence |
| `evaluation/results/<run_id>_scorecard.json` | Timestamped scorecard |

---

## Extending Evaluation

### Adding a New Dimension

1. Create check module in `scripts/checks/<dimension>.py`
2. Implement check functions returning `CheckResult`
3. Add `run_<dimension>_checks()` function
4. Add weight in dimension configuration
5. Import and call in `scripts/evaluate.py`

### Adding a New Check

1. Add check function to appropriate module
2. Update scoring table thresholds if needed
3. Add check to the `run_*_checks()` generator
4. Update documentation

### Adding a New Scenario

1. Create test repo in `eval-repos/synthetic/<scenario>/`
2. Create ground truth file `evaluation/ground-truth/<scenario>.json`
3. Run analysis: `make analyze REPO_NAME=<scenario>`
4. Verify results match ground truth: `make evaluate`

---

## Appendix: Data Structures

### CheckResult

```python
@dataclass
class CheckResult:
    check_id: str      # e.g., "SA-1"
    category: str      # e.g., "Accuracy"
    passed: bool       # True/False
    message: str       # Human-readable result
    expected: Any = None      # Expected value
    actual: Any = None        # Actual value
```

### EvaluationReport

```python
@dataclass
class EvaluationReport:
    repository: str          # e.g., "api-keys"
    results: list[CheckResult] = field(default_factory=list)

    @property
    def total_checks(self) -> int:
        return len(self.results)

    @property
    def passed_checks(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def pass_rate(self) -> float:
        if self.total_checks == 0:
            return 0.0
        return self.passed_checks / self.total_checks
```

### Analysis Output Schema (Caldera Envelope Format)

```json
{
  "metadata": {
    "tool_name": "gitleaks",
    "tool_version": "8.18.4",
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "repo_id": "660e8400-e29b-41d4-a716-446655440001",
    "branch": "main",
    "commit": "abc123def456abc123def456abc123def456abc1",
    "timestamp": "2026-01-21T18:48:53Z",
    "schema_version": "1.0.0"
  },
  "data": {
    "tool": "gitleaks",
    "tool_version": "8.18.4",
    "total_secrets": 2,
    "unique_secrets": 2,
    "secrets_in_head": 2,
    "secrets_in_history": 0,
    "files_with_secrets": 2,
    "commits_with_secrets": 1,
    "secrets_by_rule": {
      "github-pat": 1,
      "stripe-access-token": 1
    },
    "secrets_by_severity": {
      "CRITICAL": 0,
      "HIGH": 2,
      "MEDIUM": 0,
      "LOW": 0
    },
    "findings": [
      {
        "file_path": ".env",
        "line_number": 3,
        "rule_id": "github-pat",
        "secret_type": "GitHub Personal Access Token",
        "commit_hash": "abc123",
        "fingerprint": "abc123:.env:github-pat:3",
        "entropy": 4.5,
        "secret_preview": "ghp_abcd****",
        "in_current_head": true,
        "severity": "HIGH"
      }
    ],
    "files": {
      ".env": {
        "file_path": ".env",
        "secret_count": 1,
        "rule_ids": ["github-pat"],
        "earliest_commit": "abc123",
        "latest_commit": "abc123"
      }
    },
    "directories": {
      ".": {
        "direct_secret_count": 1,
        "recursive_secret_count": 2,
        "direct_file_count": 1,
        "recursive_file_count": 2,
        "rule_id_counts": { "github-pat": 1 }
      }
    },
    "scan_time_ms": 45
  }
}
```

---

## Confidence Requirements

### LLM Judge Confidence

Each judge reports a confidence level (0.0-1.0):

| Confidence | Interpretation |
|------------|----------------|
| >= 0.9 | High confidence, reliable score |
| 0.7-0.9 | Moderate confidence, some uncertainty |
| < 0.7 | Low confidence, manual review needed |

### Ground Truth Assertions

If ground truth assertions fail, LLM scores are capped:

```python
def evaluate(self):
    gt_passed, gt_failures = self.run_ground_truth_assertions()

    # Cap score if assertions failed
    if not gt_passed:
        score = min(llm_score, 2)  # Max score of 2 if GT fails
```

---

## Current Evaluation Results

### Summary (as of PoC completion)

| Metric | Value |
|--------|-------|
| Total Checks | 140 (28 per repo x 5 repos) |
| Pass Rate | 100% |
| Decision | STRONG_PASS |
| Recommendation | ADOPT for L7 Security lens |

### Per-Scenario Results

| Scenario | Checks | Pass Rate |
|----------|--------|-----------|
| no-secrets | 28 | 100% |
| api-keys | 28 | 100% |
| aws-credentials | 28 | 100% |
| mixed-secrets | 28 | 100% |
| historical-secrets | 28 | 100% |

### Key Findings

1. **Strengths:**
   - Fast scanning (30ms-5s for test repos)
   - Accurate detection of specific secret types
   - Historical secret detection works correctly
   - Zero false positives on clean repos

2. **Limitations:**
   - Limited to known patterns (regex-based)
   - No severity classification built-in
   - No remediation status tracking

3. **Recommendation:** ADOPT for secret detection; augment with entropy analysis for unknown patterns

---

## Rollup Validation

Rollups:
- directory_counts_direct
- directory_counts_recursive

Tests:
- src/tools/gitleaks/tests/unit/test_rollup_invariants.py
- src/sot-engine/dbt/tests/test_rollup_gitleaks_direct_vs_recursive.sql

---

## References

- [Gitleaks GitHub](https://github.com/gitleaks/gitleaks)
- [Gitleaks Rules](https://github.com/gitleaks/gitleaks/blob/master/config/gitleaks.toml)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685)
