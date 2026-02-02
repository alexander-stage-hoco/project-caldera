# Evaluation Strategy: SonarQube

This document describes the evaluation methodology for the SonarQube static analysis integration.

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
- Semantic understanding of issue categorization
- Assessment of actionability for developers
- Nuanced evaluation of report quality
- Detection of subtle issues missed by numeric checks

### Evaluation Principles

1. **Ground truth anchored**: All evaluations reference synthetic test projects
2. **Multi-dimensional**: Accuracy, coverage, and completeness all matter
3. **Transparent scoring**: Every score has traceable evidence
4. **Quality gate aware**: Evaluation respects SonarQube's QG decisions

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
| Programmatic | Accuracy | SQ-AC-1 to SQ-AC-5 | 40% | Issue counts, quality gate |
| Programmatic | Coverage | SQ-CV-1 to SQ-CV-4 | 30% | Metric and rule coverage |
| Programmatic | Completeness | SQ-CM-1 to SQ-CM-6 | 30% | Data structure integrity |
| LLM | Issue Accuracy | 1 judge | 35% | Issue categorization |
| LLM | Coverage Completeness | 1 judge | 25% | Data extraction quality |
| LLM | Actionability | 1 judge | 20% | Report usefulness |

**Total**: 15 programmatic checks + 3 LLM judges

---

## Programmatic Checks (16 Total)

### Overview by Dimension

| Dimension | Checks | Weight | Purpose |
|-----------|--------|--------|---------|
| Accuracy | SQ-AC-1 to SQ-AC-5 | 40% | Issue counts and quality gate |
| Coverage | SQ-CV-1 to SQ-CV-4 | 30% | Metric and rule coverage |
| Completeness | SQ-CM-1 to SQ-CM-6 | 30% | Data structure completeness |

### Accuracy Checks (SQ-AC-1 to SQ-AC-5)

| ID | Name | Severity | Pass Criteria |
|----|------|----------|---------------|
| SQ-AC-1 | Issue count accuracy | Critical | Total issues within ±20% of expected |
| SQ-AC-2 | Bug count accuracy | High | Bug count within expected range |
| SQ-AC-3 | Vulnerability count accuracy | High | Vulnerability count within expected range |
| SQ-AC-4 | Code smell count accuracy | Medium | Code smell count within ±30% of expected |
| SQ-AC-5 | Quality gate match | Critical | QG status (OK/ERROR) matches expected |

#### Scoring Formula

```python
def compute_accuracy_score(actual, expected, tolerance_pct):
    if expected == 0:
        return 1.0 if actual == 0 else 0.0
    deviation = abs(actual - expected) / expected
    return max(0, 1.0 - (deviation / tolerance_pct))
```

### Coverage Checks (SQ-CV-1 to SQ-CV-4)

| ID | Name | Severity | Pass Criteria |
|----|------|----------|---------------|
| SQ-CV-1 | Metric presence | High | All expected metrics present in catalog |
| SQ-CV-2 | Rule coverage | Medium | >= 80% of triggered rules have metadata |
| SQ-CV-3 | File coverage | High | >= 95% of files have measures |
| SQ-CV-4 | Language coverage | High | Expected languages detected |

### Completeness Checks (SQ-CM-1 to SQ-CM-6)

| ID | Name | Severity | Pass Criteria |
|----|------|----------|---------------|
| SQ-CM-1 | Component tree complete | Critical | TRK, DIR, FIL qualifiers present |
| SQ-CM-2 | Issue locations | High | >= 90% of issues have file+line |
| SQ-CM-3 | Rules hydrated | High | All triggered rules have metadata |
| SQ-CM-4 | Duplications present | Medium | Duplication data extracted |
| SQ-CM-5 | Quality gate conditions | Medium | QG has condition details |
| SQ-CM-6 | Derived insights present | Medium | Hotspots and rollups computed |

---

## Check Catalog

Complete reference of all programmatic checks with pass criteria and evidence types:

| ID | Name | Category | Severity | Pass Criteria | Evidence Type |
|----|------|----------|----------|---------------|---------------|
| SQ-AC-1 | Issue count accuracy | Accuracy | Critical | Total issues within ±20% of expected | Count comparison |
| SQ-AC-2 | Bug count accuracy | Accuracy | High | Bug count within expected range | Count comparison |
| SQ-AC-3 | Vulnerability count accuracy | Accuracy | High | Vuln count within expected range | Count comparison |
| SQ-AC-4 | Code smell count accuracy | Accuracy | Medium | Smell count within ±30% of expected | Count comparison |
| SQ-AC-5 | Quality gate match | Accuracy | Critical | QG status matches expected | Status comparison |
| SQ-CV-1 | Metric presence | Coverage | High | All expected metrics in catalog | Metric list |
| SQ-CV-2 | Rule coverage | Coverage | Medium | >= 80% rules have metadata | Coverage % |
| SQ-CV-3 | File coverage | Coverage | High | >= 95% files have measures | Coverage % |
| SQ-CV-4 | Language coverage | Coverage | High | Expected languages detected | Language list |
| SQ-CM-1 | Component tree complete | Completeness | Critical | TRK, DIR, FIL qualifiers present | Qualifier breakdown |
| SQ-CM-2 | Issue locations | Completeness | High | >= 90% issues have file+line | Location % |
| SQ-CM-3 | Rules hydrated | Completeness | High | All triggered rules have metadata | Hydration % |
| SQ-CM-4 | Duplications present | Completeness | Medium | Duplication data extracted | Has data |
| SQ-CM-5 | Quality gate conditions | Completeness | Medium | QG has condition details | Condition list |
| SQ-CM-6 | Derived insights present | Completeness | Medium | Hotspots and rollups computed | Has insights |

---

## LLM Judge Dimensions (3 Judges)

### Judge Weights

| Judge | Weight | Focus |
|-------|--------|-------|
| Issue Accuracy | 35% | Are issues correctly categorized? |
| Coverage Completeness | 25% | Is all data extracted? |
| Actionability | 20% | Are reports useful? |

### Issue Accuracy Judge (35%)

The IssueAccuracyJudge evaluates whether SonarQube issues are correctly categorized by type. It operates in **dual-mode**: a fast heuristic mode (default) and an optional LLM mode for deeper semantic analysis.

#### Evaluation Modes

| Mode | Method | Speed | Use Case |
|------|--------|-------|----------|
| Heuristic (default) | Keyword validation in issue messages/rules | Fast (~ms) | CI/CD pipelines, batch evaluation |
| LLM | Semantic analysis via LLM prompt | Slow (~seconds) | Deep analysis, edge cases |

#### Heuristic Mode Implementation

The default heuristic mode validates issue classification by checking for expected keywords in issue messages and rule names. This approach provides fast, deterministic results suitable for automated pipelines.

**Sub-dimensions and Weights**:

| Sub-dimension | Weight | Validation Target |
|---------------|--------|-------------------|
| Bug classification | 33% | BUG type issues contain bug-related keywords |
| Vulnerability classification | 33% | VULNERABILITY issues contain security keywords |
| Code smell classification | 34% | CODE_SMELL issues contain maintainability keywords |

**Keyword Validation Sets**:

| Category | Keywords |
|----------|----------|
| Bug | `null`, `error`, `exception`, `fail`, `crash`, `overflow`, `leak`, `undefined` |
| Vulnerability | `sql`, `inject`, `xss`, `csrf`, `auth`, `password`, `credential`, `secret`, `hardcoded`, `sensitive`, `exposure`, `leak` |
| Code Smell | `complexity`, `duplicate`, `unused`, `dead`, `naming`, `long`, `parameter`, `cognitive`, `method`, `class`, `refactor` |

**Sub-Score Calculation**:

For each issue category:

```python
def calculate_sub_score(issues: list, keywords: list) -> int:
    if not issues:
        return 3  # Neutral score when no issues of this type exist

    # Count issues with at least one matching keyword in message or rule
    valid_count = sum(
        1 for issue in issues
        if any(keyword in issue["message"].lower() or
               keyword in issue["rule"].lower()
               for keyword in keywords)
    )

    # Convert ratio to 1-5 scale
    ratio = valid_count / len(issues)
    return max(1, min(5, round(1 + ratio * 4)))
```

**Final Score Calculation**:

```python
# Weighted average of sub-scores
total_score = round(
    bug_score * 0.33 +
    vuln_score * 0.33 +
    smell_score * 0.34
)

# Clamp to valid range
final_score = max(1, min(5, total_score))
```

**Sample Size**: Up to 10 issues per category are sampled for evaluation.

#### LLM Mode

When LLM mode is enabled, the judge uses a prompt template to perform semantic analysis of issue categorization. The LLM evaluates:

1. Whether issue types match their actual nature
2. Whether severity levels are appropriate
3. Whether messages accurately describe the problems

The LLM returns structured JSON with the same sub-scores (bug_classification, vulnerability_classification, code_smell_classification) plus detailed reasoning.

#### Scoring Rubric

| Score | Heuristic Interpretation | LLM Interpretation |
|-------|-------------------------|-------------------|
| 5 | 100% of sampled issues contain expected keywords | All sampled issues correctly categorized |
| 4 | 75%+ issues contain expected keywords | 95%+ correctly categorized, minor misclassifications |
| 3 | 50% issues contain expected keywords (or no issues) | 85%+ correctly categorized |
| 2 | 25% issues contain expected keywords | Significant categorization errors |
| 1 | <25% issues contain expected keywords | Issue categorization unreliable |

#### Edge Cases

| Condition | Behavior |
|-----------|----------|
| No issues found | Returns score 3 with confidence 0.5, neutral evaluation |
| No issues of a specific type | Sub-score defaults to 3 (neutral) |
| Empty message/rule fields | Keywords will not match, lowering sub-score |

### Coverage Completeness Judge (25%)

**Sub-dimensions**:
- Metric extraction (40%): All relevant metrics captured
- Component coverage (30%): All files represented
- Rule hydration (30%): Rule metadata complete

**Scoring Rubric**:

| Score | Criteria |
|-------|----------|
| 5 | Complete data extraction with no gaps |
| 4 | Minor gaps in non-critical data |
| 3 | Some missing metrics or components |
| 2 | Significant data gaps |
| 1 | Critical data missing |

### Actionability Judge (20%)

**Sub-dimensions**:
- Report clarity (40%): Output is understandable
- Prioritization (30%): Issues ranked by severity
- Remediation guidance (30%): Fix suggestions present

**Scoring Rubric**:

| Score | Criteria |
|-------|----------|
| 5 | Immediately actionable for remediation |
| 4 | Clear with minor presentation improvements |
| 3 | Usable but requires interpretation |
| 2 | Difficult to prioritize work |
| 1 | Output is not actionable |

---

## Dimension Weights Summary

### Programmatic Weights (60% of combined)

| Dimension | Weight | Check Count |
|-----------|--------|-------------|
| Accuracy | 40% | 5 |
| Coverage | 30% | 4 |
| Completeness | 30% | 6 |

### LLM Weights (40% of combined)

| Dimension | Weight |
|-----------|--------|
| Issue Accuracy | 35% |
| Coverage Completeness | 25% |
| Actionability | 20% |

---

## Scoring Methodology

### Per-Dimension Score Calculation

Each programmatic dimension calculates a pass rate (0.0 to 1.0):

```python
def dimension_score(passed: int, total: int) -> float:
    """Calculate dimension score from check results."""
    if total == 0:
        return 1.0  # No checks = perfect score
    return passed / total
```

### Dimension Score to 1-5 Scale

Dimension pass rates map to the 1-5 scale used by LLM judges:

| Pass Rate | Score | Interpretation |
|-----------|-------|----------------|
| 1.00 | 5.0 | All checks passed |
| 0.90-0.99 | 4.6-4.9 | Excellent |
| 0.80-0.89 | 4.2-4.5 | Good |
| 0.70-0.79 | 3.8-4.1 | Acceptable |
| 0.60-0.69 | 3.4-3.7 | Marginal |
| < 0.60 | < 3.4 | Failing |

### Combined Scoring Formula

```python
# Programmatic component (per-dimension weighted)
prog_accuracy = accuracy_passed / accuracy_total * 0.40
prog_coverage = coverage_passed / coverage_total * 0.30
prog_completeness = completeness_passed / completeness_total * 0.30
programmatic_score = prog_accuracy + prog_coverage + prog_completeness

# Normalize to 1-5 scale
programmatic_normalized = 1 + (programmatic_score * 4)

# LLM component (already 1-5 scale)
llm_score = (
    issue_accuracy * 0.35 +
    coverage_completeness * 0.25 +
    actionability * 0.20
)

# Combined (60/40 split)
combined_score = (0.60 * programmatic_normalized) + (0.40 * llm_score)
```

### Severity Weighting (Optional)

For weighted scoring that prioritizes critical checks:

| Severity | Weight Multiplier |
|----------|-------------------|
| Critical | 2.0 |
| High | 1.5 |
| Medium | 1.0 |
| Low | 0.5 |

---

## Test Scenarios

### Synthetic Repositories (5 Scenarios)

| Repo | Language | Purpose | Expected |
|------|----------|---------|----------|
| csharp-clean | C# | Baseline, minimal issues | < 10 issues, QG=OK |
| csharp-complex | C# | High complexity | > 50 smells, high CCN |
| java-security | Java | Security vulnerabilities | > 5 vulns, QG=ERROR |
| typescript-duplication | TypeScript | High duplication | > 20% duplication |
| python-mixed | Python | Mixed issue types | 10-100 issues |

### Languages Covered

1. C# (`.cs`)
2. Java (`.java`)
3. JavaScript (`.js`)
4. TypeScript (`.ts`)
5. Python (`.py`)

---

## Running Evaluation

### Programmatic Evaluation

```bash
# Evaluate single file
make evaluate-single REPO_NAME=csharp-clean

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

# Combined evaluation
make evaluate-all
```

### Evaluation Output

```json
{
  "input_file": "output/runs/csharp-clean.json",
  "evaluated_at": "2026-01-05T14:30:00Z",
  "dimensions": {
    "accuracy": {
      "score": 95.0,
      "passed": 5,
      "failed": 0,
      "checks": [...]
    },
    "coverage": {
      "score": 87.5,
      "passed": 3,
      "failed": 1,
      "checks": [...]
    },
    "completeness": {
      "score": 100.0,
      "passed": 6,
      "failed": 0,
      "checks": [...]
    }
  },
  "overall_score": 94.2,
  "errors": []
}
```

---

## Ground Truth Specifications

### Source Data

Ground truth files in `evaluation/ground-truth/` contain expected values:

```json
{
  "id": "csharp-clean",
  "description": "Clean C# codebase with minimal issues",
  "language": "csharp",
  "expected_languages": ["cs"],
  "expected_issues": { "min": 1, "max": 10 },
  "expected_bugs": { "min": 0, "max": 2 },
  "expected_vulnerabilities": { "min": 0, "max": 1 },
  "expected_smells": { "min": 1, "max": 7 },
  "expected_metrics": {
    "ncloc": { "min": 100, "max": 500 },
    "complexity": { "min": 5, "max": 50 }
  },
  "quality_gate_expected": "OK",
  "notes": "Baseline project with clean code practices"
}
```

### Per-Scenario Expected Values

| Scenario | Language | Issues | Bugs | Vulns | Smells | QG Status |
|----------|----------|--------|------|-------|--------|-----------|
| csharp-clean | C# | 10-20 | 0-2 | 0-1 | 10-20 | ERROR |
| csharp-complex | C# | 3000-3600 | 0-5 | 0-5 | 3000-3600 | ERROR |
| java-security | Java | 20-50 | 2-5 | 5-15 | 10-30 | ERROR |
| typescript-duplication | TypeScript | 15-40 | 1-3 | 0-2 | 10-35 | WARN/ERROR |
| python-mixed | Python | 10-100 | 2-20 | 1-10 | 5-50 | ERROR |

### Tolerance Ranges

| Metric | Tolerance | Rationale |
|--------|-----------|-----------|
| Issue count | ±20% | SonarQube rules may change between versions |
| Bug count | ±30% | Classification can vary |
| Vulnerability count | ±30% | Security rules are updated frequently |
| Code smell count | ±30% | Style rules vary by configuration |
| Quality gate | Exact match | Binary pass/fail decision |
| ncloc | ±5% | Minor counting differences |
| complexity | ±10% | Algorithm differences |

### Ground Truth Schema

```json
{
  "$schema": "ground-truth.schema.json",
  "id": "scenario-name",
  "description": "Human-readable description",
  "language": "primary-language",
  "expected_languages": ["lang1", "lang2"],
  "expected_issues": { "min": 0, "max": 100 },
  "expected_bugs": { "min": 0, "max": 10 },
  "expected_vulnerabilities": { "min": 0, "max": 10 },
  "expected_smells": { "min": 0, "max": 50 },
  "expected_metrics": {
    "ncloc": { "min": 100, "max": 1000 },
    "complexity": { "min": 10, "max": 100 },
    "cognitive_complexity": { "min": 5, "max": 50 },
    "duplicated_lines_density": { "min": 0, "max": 30 }
  },
  "quality_gate_expected": "OK|WARN|ERROR",
  "notes": "Additional context for this scenario"
}
```

### Generation Process

1. **Create test repo**: Write code with known characteristics
2. **Run SonarQube**: Analyze to get baseline values
3. **Manual verification**: Confirm issues are valid
4. **Document expected**: Record ranges in ground truth
5. **Version control**: Commit ground truth alongside test repos

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

## Evidence Collection

Each check collects evidence for transparency:

```python
evidence = {
    "expected_range": {"min": 10, "max": 50},
    "actual_value": 35,
    "within_range": True,
    "source": "issues.rollups.total"
}
```

### Evidence Types by Check

| Check Type | Evidence Collected |
|------------|-------------------|
| Accuracy | Expected range, actual value, deviation |
| Coverage | Metric list, missing metrics, coverage % |
| Completeness | Component counts, qualifier breakdown |

---

## Continuous Improvement

### Adding New Checks

1. Create check function in appropriate module (`accuracy.py`, `coverage.py`, `completeness.py`)
2. Add `@check` decorator with ID and metadata
3. Add to `*_CHECKS` list in module
4. Update ground truth if needed
5. Run `make evaluate` to verify

### Updating Thresholds

Thresholds are defined in check functions:

```python
@check("SQ-AC-1", "Issue count accuracy", Dimension.ACCURACY, Severity.CRITICAL)
def check_issue_count(data: dict, ground_truth: dict | None) -> CheckResult:
    tolerance = 0.20  # 20% tolerance
    ...
```

### Calibrating LLM Judges

Calibrate judges using diverse samples:
- Projects with known issue distributions
- Edge cases (zero issues, thousands of issues)
- Mixed severity distributions

---

## Extending Evaluation

### Adding New Programmatic Checks

1. **Create check function** in the appropriate module (`scripts/checks/accuracy.py`, etc.):

```python
from .base import check, CheckResult, Severity

@check("SQ-AC-6", "New accuracy check", "accuracy", Severity.HIGH)
def check_new_metric(data: dict, ground_truth: dict | None) -> CheckResult:
    """Verify new metric is within expected range."""
    actual = data.get("new_metric", 0)
    expected = ground_truth.get("expected_new_metric", {}) if ground_truth else {}

    min_val = expected.get("min", 0)
    max_val = expected.get("max", float("inf"))
    passed = min_val <= actual <= max_val

    return CheckResult(
        passed=passed,
        score=1.0 if passed else 0.0,
        message=f"New metric: {actual} (expected {min_val}-{max_val})",
        evidence={"actual": actual, "expected": expected}
    )
```

2. **Register check** in the category's check list

3. **Update ground truth** files with expected values

4. **Run evaluation** to verify: `make evaluate`

### Adding New LLM Judges

1. **Create judge class** in `evaluation/llm/judges/`:

```python
# evaluation/llm/judges/new_dimension.py
from .base import BaseJudge

class NewDimensionJudge(BaseJudge):
    """Judge for evaluating new dimension."""

    name = "new_dimension"
    weight = 0.15  # 15% of LLM score

    def get_prompt(self, data: dict) -> str:
        return self.load_prompt("new_dimension.md", data=data)

    def parse_response(self, response: str) -> dict:
        return {"score": 4.0, "reasoning": "...", "confidence": 0.9}
```

2. **Create prompt template** in `evaluation/llm/prompts/new_dimension.md`

3. **Register judge** in orchestrator

### Adding New Test Scenarios

To add a new synthetic test repository:

1. Create test repo in `eval-repos/synthetic/`:
   ```
   eval-repos/synthetic/new-scenario/
   ├── src/
   │   └── ... (code files with known characteristics)
   └── sonar-project.properties
   ```

2. Create ground truth file `evaluation/ground-truth/new-scenario.json`

3. Run analysis: `make analyze REPO_NAME=new-scenario`

4. Verify results match ground truth: `make evaluate`

### Template for New Checks

```python
@check(
    check_id="SQ-XX-N",        # Category prefix + number
    name="Descriptive name",   # Human-readable name
    category="category_name",  # accuracy, coverage, completeness
    severity=Severity.HIGH     # CRITICAL, HIGH, MEDIUM, LOW
)
def check_something(data: dict, ground_truth: dict | None) -> CheckResult:
    """
    One-line description of what this check validates.

    Args:
        data: Parsed SonarQube export JSON
        ground_truth: Expected values (or None if no ground truth)

    Returns:
        CheckResult with passed, score, message, and evidence
    """
    # Implementation
    pass
```

---

## Rollup Validation

Rollups:
- directory_counts_direct
- directory_counts_recursive

Tests:
- src/sot-engine/dbt/tests/test_rollup_sonarqube_direct_vs_recursive.sql

---

## References

- [SonarQube Quality Gates](https://docs.sonarqube.org/latest/user-guide/quality-gates/)
- [SonarQube Metrics](https://docs.sonarqube.org/latest/user-guide/metric-definitions/)
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685)
