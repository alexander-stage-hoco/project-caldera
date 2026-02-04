# DevSkim - Evaluation Strategy

> How we measure the quality and accuracy of DevSkim's security vulnerability detection.

## Philosophy & Approach

DevSkim is a security scanning tool that detects potential security vulnerabilities in source code. Our evaluation philosophy prioritizes:

1. **Detection accuracy over coverage breadth**: False negatives (missed vulnerabilities) are worse than false positives for security tools
2. **Severity calibration is critical**: Correct severity assignment determines remediation priority
3. **Binary decisions preferred**: Issues are either detected or missed, severities are correct or incorrect
4. **Ground truth validation**: All assessments validated against known vulnerable code patterns

### What does "correct" mean for DevSkim?
- A security finding is correctly identified at the right file and line
- The severity accurately reflects the real-world risk
- The rule category matches the actual vulnerability type

### How do we balance precision vs recall?
For security tools, recall (finding all vulnerabilities) is prioritized over precision (avoiding false alarms), but excessive false positives reduce signal quality.

---

## Dimension Summary

| Dimension | Weight | Target | Method | Rationale |
|-----------|--------|--------|--------|-----------|
| Detection Accuracy | 25% | F1 >= 0.85 | Programmatic + LLM | Core purpose - finding vulnerabilities |
| Severity Calibration | 20% | >= 80% correct | LLM | Remediation priority depends on correct severity |
| Category Coverage | 15% | >= 70% categories | Programmatic | Breadth of vulnerability detection |
| False Positive Rate | 15% | <= 20% FP rate | Programmatic | Minimize noise for developers |
| Edge Case Handling | 10% | All pass | Programmatic | Robustness across file types |
| Performance | 10% | < 30s small repos | Programmatic | CI/CD pipeline compatibility |
| Output Quality | 5% | Schema valid | Programmatic | Integration requirements |

---

## Check Catalog

### Programmatic Checks (30 checks)

Located in `scripts/checks/`:

#### Accuracy Checks (AC-1 to AC-8)

| Check | Name | Target | Pass Criteria |
|-------|------|--------|---------------|
| AC-1 | SQL injection detection | SqlInjection.* files | >= 1 finding per file |
| AC-2 | Hardcoded secrets detection | HardcodedSecrets.* files | >= 1 finding per file |
| AC-3 | Insecure crypto detection | InsecureCrypto.* files | >= 1 finding per file |
| AC-4 | Path traversal detection | PathTraversal.* files | >= 1 finding per file |
| AC-5 | XSS detection | XssVulnerability.* files | >= 1 finding per file |
| AC-6 | Deserialization detection | Deserialization.* files | >= 1 finding per file |
| AC-7 | False negative rate | All vulnerable files | <= 20% missed |
| AC-8 | Overall precision | All files | > 50% true positive rate |

**Scoring**: Each check scores 0.0-1.0 based on detection rate.

#### Coverage Checks (CV-1 to CV-8)

| Check | Name | Target | Pass Criteria |
|-------|------|--------|---------------|
| CV-1 | C# coverage | csharp/*.cs | >= 1 finding detected |
| CV-2 | Python coverage | python/*.py | >= 1 finding detected |
| CV-3 | JavaScript coverage | javascript/*.js | >= 1 finding detected |
| CV-4 | Java coverage | java/*.java | >= 1 finding detected |
| CV-5 | Go coverage | go/*.go | >= 1 finding detected |
| CV-6 | C/C++ coverage | c/*.c, cpp/*.cpp | >= 1 finding detected |
| CV-7 | Multi-language repo | mixed/* | All languages analyzed |
| CV-8 | Category coverage | All categories | >= 5/8 categories covered |

**Scoring**: Language checks score based on files with findings / total files.

#### Edge Case Checks (EC-1 to EC-8)

| Check | Name | Target | Pass Criteria |
|-------|------|--------|---------------|
| EC-1 | Empty files | empty.* files | No crashes |
| EC-2 | Large files | Files > 10K LOC | Analysis completes |
| EC-3 | Comments only | comment_only.* files | No false positives |
| EC-4 | Minified code | minified.* files | Graceful handling |
| EC-5 | Unicode content | Files with Unicode | No encoding errors |
| EC-6 | Clean files | SafeCode.* files | 0 findings (true negatives) |
| EC-7 | Syntax errors | Malformed files | Graceful handling |
| EC-8 | Path handling | Special chars in paths | Correct processing |

**Scoring**: Pass/fail with 1.0 or 0.0.

#### Performance Checks (PF-1 to PF-4)

| Check | Name | Target | Pass Criteria |
|-------|------|--------|---------------|
| PF-1 | Small repo speed | eval-repos/synthetic | < 30 seconds |
| PF-2 | Per-file efficiency | All files | < 500ms per file |
| PF-3 | Throughput | All files | >= 50 LOC/second |
| PF-4 | Analysis completeness | All files | 100% files processed |

**Scoring**: Ratio of threshold to actual (capped at 1.0).

#### Output Quality Checks (OQ-1)

| Check | Name | Target | Pass Criteria |
|-------|------|--------|---------------|
| OQ-1 | Schema validation | output.json | Validates against output.schema.json |

#### Integration Fit Checks (IF-1)

| Check | Name | Target | Pass Criteria |
|-------|------|--------|---------------|
| IF-1 | Relative paths | All file_path fields | No absolute paths |

### LLM Judges (4 judges, 40% weight)

Located in `evaluation/llm/judges/`:

#### Judge 1: Detection Accuracy (35% weight)

**Focus**: Are detected findings genuine security issues?

**Sub-dimensions**:
- True Positive Rate (40%): Detected findings are actual vulnerabilities
- Classification Accuracy (30%): Vulnerability type correctly identified
- Location Accuracy (30%): File and line numbers are correct

**Evidence collected**:
- Sample of detected findings
- Comparison with ground truth
- Category breakdown

#### Judge 2: Rule Coverage (25% weight)

**Focus**: Does DevSkim cover target vulnerability categories?

**Sub-dimensions**:
- Category Coverage (40%): All target categories addressed
- Language Coverage (35%): All target languages supported
- Rule Variety (25%): Sufficient rule diversity

**Evidence collected**:
- Category statistics
- Language statistics
- Unique rule list

#### Judge 3: Severity Calibration (20% weight)

**Focus**: Are severity levels appropriate?

**Sub-dimensions**:
- Severity Appropriateness (50%): CRITICAL/HIGH/MEDIUM/LOW match real risk
- Consistency (30%): Similar vulnerabilities get similar severities
- Remediation Priority (20%): Severity guides correct fix order

**Evidence collected**:
- Severity distribution
- Sample severity assignments
- Cross-file consistency

#### Judge 4: Security Focus (20% weight)

**Focus**: Is the tool providing security value?

**Sub-dimensions**:
- Relevance (40%): Findings are security-relevant
- Signal Quality (35%): Low noise, high signal
- Actionability (25%): Developers can act on findings

**Evidence collected**:
- Sample finding messages
- False positive examples
- Remediation guidance quality

---

## Scoring Methodology

### Aggregate Score Calculation

```python
# Normalize programmatic score (0-1) to 1-5 scale
programmatic_normalized = programmatic_score * 4 + 1

# Calculate combined score
combined_score = (
    programmatic_normalized * 0.60 +  # 60% weight
    llm_score * 0.40                   # 40% weight
)
```

### Per-Check Scoring

Each programmatic check returns:
- `pass`: 100 points
- `warn`: 50 points
- `fail`: 0 points

Final dimension score = (sum of check scores) / (max possible)

---

## Decision Thresholds

### Pass/Fail Criteria

| Dimension | Pass | Warn | Fail |
|-----------|------|------|------|
| Detection Accuracy | >= 85% F1 | 70-85% F1 | < 70% F1 |
| Severity Calibration | >= 80% | 60-80% | < 60% |
| Category Coverage | >= 70% | 50-70% | < 50% |
| False Positive Rate | <= 20% | 20-35% | > 35% |
| Edge Cases | All pass | 1-2 fail | > 2 fail |
| Performance | < 30s | 30-60s | > 60s |
| Output Quality | Valid | - | Invalid |

### Overall Decision

| Decision | Score | Description |
|----------|-------|-------------|
| STRONG_PASS | >= 4.0 (80%+) | Production ready, no issues |
| PASS | >= 3.5 (70%+) | Acceptable for use |
| WEAK_PASS | >= 3.0 (60%+) | Needs improvement before production |
| FAIL | < 3.0 | Not ready for use |

### Critical Failures (Auto-FAIL)

Any of these conditions result in immediate FAIL:
- F1 score < 0.5 (accuracy too low)
- CRITICAL severity issue missed in ground truth
- False positive rate > 50%
- Schema validation fails
- Absolute paths in output

---

## Ground Truth Specifications

### Synthetic Repositories

Located in `eval-repos/synthetic/`:

| Repo | Purpose | Language | Key Scenarios |
|------|---------|----------|---------------|
| `csharp/` | Core security patterns | C# | SQL injection, crypto, deserialization |
| `api-security/` | API vulnerabilities | C# | Auth headers, CORS, input validation |

### Ground Truth Format

Located in `evaluation/ground-truth/`:

```json
{
  "schema_version": "1.0",
  "scenario": "csharp",
  "description": "Ground truth for DevSkim C# security detection",
  "repo_path": "eval-repos/synthetic/csharp",
  "expected": {
    "language": "csharp",
    "aggregate_expectations": {
      "min_total_issues": 13,
      "max_false_positives": 2,
      "required_categories": ["insecure_crypto", "deserialization"]
    }
  },
  "files": {
    "InsecureCrypto.cs": {
      "expected_issues": [
        {"category": "insecure_crypto", "count": 10}
      ],
      "total_expected": 10,
      "false_positives_allowed": 1
    },
    "SafeCode.cs": {
      "expected_issues": [],
      "total_expected": 0,
      "false_positives_allowed": 0,
      "notes": "Clean file - no security issues"
    }
  }
}
```

### Ground Truth Files

| File | Scenario | Files | Issues | Clean Files |
|------|----------|-------|--------|-------------|
| `csharp.json` | C# security | 7 | 13+ | 1 (SafeCode.cs) |
| `api-security.json` | API security | 5 | 2+ | 1 (SafeApiCode.cs) |

### Ground Truth Principles

1. **Range-based expectations**: Allow min-max range, not exact counts
2. **Type-based validation**: Check vulnerability categories, not just counts
3. **Negative cases**: Include clean files to test false positive rate
4. **Language-specific**: Separate ground truth per scenario

---

## Running Evaluations

### Programmatic Only

```bash
make evaluate
```

Output: Console report + `evaluation/results/evaluation_report.json`

### LLM Only

```bash
make evaluate-llm
```

Output: Console report + `evaluation/results/llm_evaluation.json`

### Combined

```bash
make evaluate-combined
```

Output: Console report + `evaluation/scorecard.json`

### Quick (Skip Performance)

```bash
make evaluate-quick
```

---

## Extending Evaluation

### Adding a Programmatic Check

1. Create check function in `scripts/checks/<dimension>.py`
2. Implement `check_*` function returning `CheckResult`
3. Register in `scripts/evaluate.py`
4. Update this document

### Adding an LLM Judge

1. Create `evaluation/llm/judges/<dimension>.py`
2. Create prompt in `evaluation/llm/prompts/<dimension>.md`
3. Register in `evaluation/llm/orchestrator.py`
4. Update this document

### Adding Ground Truth

1. Create synthetic repo in `eval-repos/synthetic/`
2. Run tool and manually verify output
3. Save ground truth in `evaluation/ground-truth/<scenario>.json`
4. Update this document

---

## Rollup Validation

DevSkim produces directory-level rollups via dbt for aggregating security findings.

Rollups:
- directory_counts_direct
- directory_counts_recursive

Tests:
- src/sot-engine/dbt/tests/test_rollup_devskim_direct_vs_recursive.sql

### Invariants Tested

| Invariant | Description |
|-----------|-------------|
| recursive >= direct | Recursive counts include all descendants |
| count >= 0 | All counts are non-negative |
| severity_counts sum | Sum of severity counts equals total |

---

## Calibration Notes

### Why Security-Focused Evaluation?

DevSkim is designed for security vulnerability detection, not general code quality. The evaluation reflects this:
- **High weight on detection accuracy (25%)**: Missing security issues is critical
- **Severity calibration matters (20%)**: Determines remediation priority
- **Performance is secondary (10%)**: Security is worth compute time

### Known Limitations

1. DevSkim focuses on pattern matching, not semantic analysis
2. Some vulnerability types (e.g., business logic) are out of scope
3. Detection rates vary by language (C# best supported)

### Recommended Improvements

For production use, consider:
- Adding custom rules for organization-specific patterns
- Combining with other security tools for defense in depth
- Adjusting severity mappings based on deployment context

---

## References

- [DevSkim Rules Documentation](https://github.com/microsoft/DevSkim/wiki)
- [DD Security Standards](../../../docs/SECURITY_STANDARDS.md)
- [Evaluation Template](../../../docs/templates/EVAL_STRATEGY.md.template)
