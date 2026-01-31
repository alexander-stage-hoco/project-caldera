# Semgrep PoC Evaluation Strategy

This document describes the evaluation framework for the Semgrep code smell and security analysis tool PoC, including the complete check catalog, scoring methodology, weight allocation, and decision thresholds.

## Philosophy & Approach

The evaluation framework assesses Semgrep's fitness for integration into the DD Platform across 6 dimensions with 34 individual checks.

### Version History

| Version | Dimensions | Checks | Description |
|---------|------------|--------|-------------|
| v1.0 (Original) | 4 | 28 | Initial evaluation framework |
| v2.0 (Extended) | 6 | 34 | Added Output Quality and Integration Fit |

### Key Changes in v2.0

1. **New Dimensions Added:**
   - Output Quality (OQ-1 to OQ-3) - Schema and structure validation
   - Integration Fit (IF-1 to IF-2) - DD Platform compatibility

2. **Evaluation Principles:**
   - Ground truth anchored: All evaluations reference synthetic test repositories
   - Multi-dimensional: Accuracy, coverage, and detection quality all matter
   - Transparent scoring: Every score has traceable evidence
   - Security-focused: Semgrep excels at security patterns over complexity metrics

---

## Dimension Summary

| Dimension | Code | Checks | Weight | Description |
|-----------|------|--------|--------|-------------|
| Accuracy | AC | 9 | 30% | Detection accuracy for smell types |
| Coverage | CV | 8 | 20% | Language and category coverage |
| Edge Cases | EC | 8 | 15% | Robustness and error handling |
| Performance | PF | 4 | 10% | Execution speed and efficiency |
| Output Quality | OQ | 3 | 10% | Schema and structure compliance |
| Integration Fit | IF | 2 | 15% | DD Platform compatibility |
| **Total** | | **34** | **100%** | |

---

## Complete Check Catalog

### 1. Accuracy (AC) - 30% Weight

Validates that Semgrep correctly detects expected smell patterns against ground truth.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| AC-1 | SQL Injection Detection | Detects SQL injection vulnerabilities | `detected >= expected * 0.5` |
| AC-2 | Empty Catch Detection | Detects empty catch blocks | `detected >= expected * 0.5` (requires custom rules) |
| AC-3 | Catch-All Detection | Detects broad exception catches | `detected >= expected * 0.5` |
| AC-4 | Async Void Detection | Detects async void methods (C#) | `detected >= expected * 0.5` (requires custom rules) |
| AC-5 | HTTP Client Detection | Detects HTTP-related security issues | `detected > 0` |
| AC-6 | High Complexity Detection | Detects high complexity patterns | Pass (neutral - use Lizard) |
| AC-7 | God Class Detection | Detects god class patterns | Pass (neutral - use Lizard) |
| AC-8 | Overall Detection Quality | Categorization rate | `categorized >= 80%` |
| AC-9 | Line Number Accuracy | Line numbers within ±2 tolerance | `accuracy >= 70%` |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 9 | 5 |
| 7-8 | 4 |
| 5-6 | 3 |
| 3-4 | 2 |
| 0-2 | 1 |

---

### 2. Coverage (CV) - 20% Weight

Validates language support and DD category coverage.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| CV-1 | Python Coverage | Python files analyzed | `files > 0` |
| CV-2 | JavaScript Coverage | JavaScript files analyzed | `files > 0` |
| CV-3 | TypeScript Coverage | TypeScript files analyzed | `files > 0` |
| CV-4 | C# Coverage | C# files analyzed | `files > 0` |
| CV-5 | Java Coverage | Java files analyzed | `files > 0` |
| CV-6 | Go Coverage | Go files analyzed | `files > 0` |
| CV-7 | Rust Coverage | Rust files analyzed | `files > 0` |
| CV-8 | DD Category Coverage | DD smell categories detected | `categories > 0` |

**Per-Language Scoring:**
- 0.4 points: Language files analyzed
- 0.3 points: At least one smell detected
- 0.3 points: Multiple categories covered (scaled)

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 8 | 5 |
| 7 | 4 |
| 5-6 | 3 |
| 3-4 | 2 |
| 0-2 | 1 |

---

### 3. Edge Cases (EC) - 15% Weight

Validates handling of edge cases and unusual inputs.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| EC-1 | Empty Files Handling | Analysis handles empty files | No crashes |
| EC-2 | Unicode Content Handling | Unicode files processed | No encoding errors |
| EC-3 | Large Files Handling | Files > 500 LOC processed | Analysis completes |
| EC-4 | Deep Nesting Handling | Deeply nested code analyzed | No stack overflow |
| EC-5 | Mixed Language Files | JS/TS files (JSX/TSX) handled | Proper parsing |
| EC-6 | No False Positives | Clean files have no detections | `false_positives == 0` |
| EC-7 | Syntax Error Tolerance | Files with syntax errors handled | Graceful degradation |
| EC-8 | Path Handling | Various path formats accepted | `paths_processed > 0` |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 8 | 5 |
| 7 | 4 |
| 5-6 | 3 |
| 3-4 | 2 |
| 0-2 | 1 |

---

### 4. Performance (PF) - 10% Weight

Validates execution speed and efficiency.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| PF-1 | Synthetic Repo Speed | Analysis completes in time | `duration < 45s` (includes rule download) |
| PF-2 | Per-File Efficiency | Per-file analysis time | `ms_per_file < 1000ms` |
| PF-3 | Analysis Throughput | Lines processed per second | `LOC/s >= 100` |
| PF-4 | Startup Overhead | Startup vs analysis ratio | `startup_ratio < 90%` |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 4 | 5 |
| 3 | 4 |
| 2 | 3 |
| 1 | 2 |
| 0 | 1 |

---

### 5. Output Quality (OQ) - 10% Weight

Validates schema compliance and output structure.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| OQ-1 | Required Sections Present | All top-level sections exist | Sections: `tool`, `tool_version`, `metadata`, `summary`, `directories`, `files`, `by_language`, `statistics` |
| OQ-2 | File Entry Fields | File entries have required fields | Fields: `path`, `language`, `lines`, `smell_count`, `smells` |
| OQ-3 | Schema Validation | Output validates against JSON schema | Zero validation errors |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 3 | 5 |
| 2 | 3 |
| 0-1 | 1 |

---

### 6. Integration Fit (IF) - 15% Weight

Validates compatibility with DD Platform requirements.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| IF-1 | Relative File Paths | All paths are relative | `absolute_paths == 0` and `embedded_root == 0` |
| IF-2 | Smell Entry Fields | Smell entries have required DD fields | Fields: `dd_smell_id`, `dd_category`, `line_start`, `line_end`, `severity` |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 2 | 5 |
| 1 | 3 |
| 0 | 1 |

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
prog_accuracy = accuracy_passed / 9 * 0.30
prog_coverage = coverage_passed / 8 * 0.20
prog_edge_cases = edge_case_passed / 8 * 0.15
prog_performance = performance_passed / 4 * 0.10
prog_output = output_quality_passed / 3 * 0.10
prog_integration = integration_fit_passed / 2 * 0.15
programmatic_score = sum([prog_*])

# Normalize to 1-5 scale
programmatic_normalized = 1 + (programmatic_score * 4)

# LLM component (already 1-5 scale)
llm_score = (
    smell_accuracy * 0.35 +
    rule_coverage * 0.25 +
    false_positive_rate * 0.20 +
    actionability * 0.20
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
| Accuracy | 30% | Core function - security detection must be accurate |
| Coverage | 20% | Multi-language support is essential |
| Integration Fit | 15% | Required for DD Platform integration |
| Edge Cases | 15% | Robustness matters for production use |
| Performance | 10% | Important but Semgrep is generally fast |
| Output Quality | 10% | Schema compliance is binary |

---

## Ground Truth Specifications

### Synthetic Repository Structure

```
eval-repos/synthetic/
├── csharp/              # C# smell patterns
├── go/                  # Go smell patterns
├── java/                # Java smell patterns
├── javascript/          # JavaScript smell patterns
├── python/              # Python smell patterns
├── rust/                # Rust smell patterns
└── typescript/          # TypeScript smell patterns
```

**Total: 7 language-specific scenarios**

### Expected Detection by Language

| Language | Security Patterns | Error Handling | Resource Mgmt |
|----------|-------------------|----------------|---------------|
| Python | SQL injection, subprocess | Empty catch, catch-all | N/A |
| JavaScript | XSS, DOM manipulation | Try-catch issues | N/A |
| TypeScript | Same as JavaScript | Same as JavaScript | N/A |
| C# | SSRF, MemoryMarshal | Empty catch | HttpClient |
| Java | SQL injection, serialization | Empty catch | N/A |
| Go | SQL injection, command injection | Error ignored | N/A |
| Rust | Basic security rules | N/A | N/A |

### Ground Truth Schema

```json
{
  "schema_version": "1.0",
  "language": "python",
  "description": "Python smell detection ground truth",
  "generated_at": "2026-01-21T00:00:00Z",
  "files": {
    "sql_injection.py": {
      "expected_smells": [
        {
          "smell_id": "SQL_INJECTION",
          "count": 2,
          "lines": [10, 25]
        }
      ]
    }
  },
  "totals": {
    "total_files": 5,
    "total_smells": 12,
    "by_category": {
      "security": 8,
      "error_handling": 4
    }
  }
}
```

### Tolerance Policy

| Metric | Tolerance | Rationale |
|--------|-----------|-----------|
| Detection count | >= 50% | Semgrep may not cover all DD patterns |
| Line numbers | ±2 lines | Minor variance acceptable |
| False positives | 0% | Clean files must stay clean |
| Performance | Threshold | Hardware variance expected |

---

## LLM Judge Dimensions (4 Judges)

### Judge Weights

| Judge | Weight | Focus |
|-------|--------|-------|
| Smell Accuracy | 35% | Correct smell type identification |
| Rule Coverage | 25% | Breadth of rules exercised |
| False Positive Rate | 20% | Precision of detection |
| Actionability | 20% | Message clarity and fix guidance |

### Smell Accuracy Judge (35%)

**Sub-dimensions:**
- Smell type identification (40%): Correct classification
- Severity assignment (30%): Appropriate severity levels
- Rule matching (30%): Correct rule ID attribution

**Scoring Rubric:**
| Score | Criteria |
|-------|----------|
| 5 | All security patterns detected with correct classification |
| 4 | 95%+ patterns detected, minor classification issues |
| 3 | 85%+ patterns detected |
| 2 | Significant detection gaps |
| 1 | Major patterns missed |

### Rule Coverage Judge (25%)

**Sub-dimensions:**
- Rule variety (40%): Multiple rule types exercised
- Language completeness (30%): All languages have detections
- Category diversity (30%): Multiple DD categories covered

**Scoring Rubric:**
| Score | Criteria |
|-------|----------|
| 5 | Comprehensive rule coverage across all languages |
| 4 | Good coverage, minor gaps |
| 3 | Moderate coverage |
| 2 | Limited rule types |
| 1 | Minimal coverage |

### False Positive Rate Judge (20%)

**Sub-dimensions:**
- Clean file precision (50%): No false alarms on clean files
- Pattern specificity (30%): Patterns match actual issues
- Context awareness (20%): Considers surrounding code

**Scoring Rubric:**
| Score | Criteria |
|-------|----------|
| 5 | Zero false positives |
| 4 | < 1% false positive rate |
| 3 | 1-5% false positive rate |
| 2 | 5-10% false positive rate |
| 1 | > 10% false positive rate |

### Actionability Judge (20%)

**Sub-dimensions:**
- Message clarity (40%): Clear problem description
- Fix suggestion quality (35%): Actionable remediation
- Priority guidance (25%): Helps with triage

**Scoring Rubric:**
| Score | Criteria |
|-------|----------|
| 5 | Clear messages with actionable fix suggestions |
| 4 | Good messages, some fix guidance |
| 3 | Basic messages, limited guidance |
| 2 | Unclear messages |
| 1 | Messages not helpful |

---

## Running Evaluation

### Prerequisites

1. Semgrep CLI installed (v1.146.0+)
2. Python virtual environment in `.venv/`
3. Synthetic test repositories in `eval-repos/synthetic/`
4. Ground truth files in `evaluation/ground-truth/`

### Commands

```bash
# Setup environment
make setup

# Run full evaluation
make evaluate

# Run LLM evaluation
make evaluate-llm

# Combined evaluation
make evaluate-combined

# Quick evaluation (subset)
make evaluate-quick

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

### Adding a New Language

1. Create synthetic test files in `eval-repos/synthetic/<lang>/`
2. Create ground truth file `evaluation/ground-truth/<lang>.json`
3. Add coverage check `CV-N` in `scripts/checks/coverage.py`
4. Run analysis and verify results

---

## Appendix: Data Structures

### CheckResult

```python
@dataclass
class CheckResult:
    check_id: str           # e.g., "AC-1"
    name: str               # e.g., "SQL injection detection"
    category: CheckCategory # Enum: ACCURACY, COVERAGE, etc.
    passed: bool            # True/False
    score: float            # 0.0 to 1.0
    message: str            # Human-readable result
    evidence: dict = field(default_factory=dict)
```

### CheckCategory Enum

```python
class CheckCategory(Enum):
    ACCURACY = "Accuracy"
    COVERAGE = "Coverage"
    EDGE_CASES = "Edge Cases"
    PERFORMANCE = "Performance"
    OUTPUT_QUALITY = "Output Quality"
    INTEGRATION_FIT = "Integration Fit"
```

### Analysis Output Schema

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-01-21T00:00:00Z",
  "repo_name": "synthetic-python",
  "repo_path": "/path/to/repo",
  "results": {
    "tool": "semgrep",
    "tool_version": "1.146.0",
    "metadata": {
      "analysis_duration_ms": 6500,
      "root_path": "/path/to/repo"
    },
    "summary": {
      "total_files": 18,
      "total_lines": 1500,
      "total_smells": 25,
      "smells_by_category": {
        "security": 15,
        "error_handling": 10
      },
      "smells_by_severity": {
        "ERROR": 5,
        "WARNING": 15,
        "INFO": 5
      }
    },
    "files": [
      {
        "path": "sql_injection.py",
        "language": "python",
        "lines": 50,
        "smell_count": 2,
        "smells": [
          {
            "dd_smell_id": "SQL_INJECTION",
            "dd_category": "security",
            "rule_id": "python.lang.security.audit.dangerous-subprocess-use",
            "line_start": 10,
            "line_end": 10,
            "severity": "ERROR",
            "message": "Detected string concatenation in SQL query"
          }
        ]
      }
    ],
    "directories": {},
    "by_language": {
      "python": {"files": 5, "smells": 12}
    },
    "statistics": {}
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
| Total Checks | 34 |
| Pass Rate | 96.4% (27/28 original) |
| Overall Score | 69.0% |
| Decision | PASS |
| Recommendation | ADOPT for security scanning |

### Per-Dimension Results

| Dimension | Score | Passed |
|-----------|-------|--------|
| Accuracy | 47.8% | 8/9 |
| Coverage | 67.5% | 7/8 |
| Edge Cases | 93.8% | 8/8 |
| Performance | 64.8% | 4/4 |
| Output Quality | TBD | TBD |
| Integration Fit | TBD | TBD |

### Key Findings

1. **Strengths:**
   - SQL injection detection: 100%
   - False positive rate: 0% on clean files
   - Performance: Within thresholds
   - Language support: 7 languages

2. **Limitations:**
   - Empty catch detection: 0% (requires custom rules)
   - Async void detection: 0% (requires custom rules)
   - DD category coverage: Limited (security-focused)
   - Complexity metrics: Use Lizard instead

3. **Recommendation:** ADOPT for security scanning; complement with Lizard for complexity and jscpd for duplication

---

## Rollup Validation

Rollups:
- directory_counts_direct
- directory_counts_recursive

Tests:
- src/sot-engine/dbt/tests/test_rollup_semgrep_direct_vs_recursive.sql

---

## References

- [Semgrep Documentation](https://semgrep.dev/docs/)
- [Semgrep Rules Registry](https://semgrep.dev/explore)
- [Custom Rules Guide](https://semgrep.dev/docs/writing-rules/overview/)
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685)
