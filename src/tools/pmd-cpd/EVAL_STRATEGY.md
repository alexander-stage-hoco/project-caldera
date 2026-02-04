# Evaluation Strategy: PMD CPD

This document describes the evaluation methodology for the PMD CPD (Copy/Paste Detector) tool integration.

## Philosophy & Approach

### Why Hybrid Evaluation?

The evaluation combines **programmatic checks** with **LLM-as-a-Judge** evaluation:

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 60% | Objective, reproducible, fast |
| LLM Judges | 40% | Semantic understanding, actionability |

This hybrid approach provides both precision and nuance in evaluating duplication detection quality.

### Rationale for 60/40 Split

**Programmatic checks (60%)** ensure:
- Deterministic, reproducible results across runs
- Fast feedback loop during development
- Clear pass/fail criteria for CI/CD gates
- Objective measurement against ground truth

**LLM judges (40%)** provide:
- Semantic understanding of clone quality
- Assessment of actionability for developers
- Nuanced evaluation that can't be reduced to numeric thresholds
- Detection of subtle issues missed by programmatic checks

### Evaluation Principles

1. **Ground truth anchored**: All evaluations reference known-good synthetic examples
2. **Multi-dimensional**: No single metric determines pass/fail
3. **Transparent scoring**: Every score has traceable evidence
4. **Fail-safe defaults**: Conservative scoring when confidence is low

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

All evaluation dimensions with their check counts and weights in a single reference table:

| Category | Dimension | Checks | Weight | Focus Area |
|----------|-----------|--------|--------|------------|
| Programmatic | Accuracy | AC-1 to AC-8 | 40% | Clone detection correctness |
| Programmatic | Coverage | CV-1 to CV-8 | 25% | Language and file coverage |
| Programmatic | Edge Cases | EC-1 to EC-8 | 20% | Boundary condition handling |
| Programmatic | Performance | PF-1 to PF-4 | 15% | Speed and resource usage |
| LLM | Duplication Accuracy | 1 judge | 35% | Clone genuineness |
| LLM | Semantic Detection | 1 judge | 25% | Type 2 clone detection |
| LLM | Cross-File Detection | 1 judge | 20% | Multi-file clone linking |
| LLM | Actionability | 1 judge | 20% | Report usefulness |

**Total**: 28 programmatic checks + 4 LLM judges

---

## Programmatic Checks (28 Total)

### Overview by Category

| Category | Checks | Weight | Purpose |
|----------|--------|--------|---------|
| Accuracy | AC-1 to AC-8 | 40% | Clone detection accuracy |
| Coverage | CV-1 to CV-8 | 25% | Language and file coverage |
| Edge Cases | EC-1 to EC-8 | 20% | Edge case handling |
| Performance | PF-1 to PF-4 | 15% | Speed and resource checks |

### Accuracy Checks (AC-1 to AC-8)

| ID | Name | Severity | Pass Criteria |
|----|------|----------|---------------|
| AC-1 | Clone count matches | Critical | Detected clones within expected range |
| AC-2 | Line range accuracy | High | start_line/end_line within ±2 tolerance |
| AC-3 | Token count validity | Medium | Token counts > min_tokens threshold |
| AC-4 | Cross-file detection | Critical | Cross-file clones correctly linked |
| AC-5 | Duplication percentage | High | Overall percentage within ±5% of expected |
| AC-6 | Per-file metrics | Medium | Individual file duplication % accurate |
| AC-7 | Semantic mode clones | High | Additional clones found in semantic mode |
| AC-8 | Clone ID uniqueness | Low | All clone IDs are unique |

#### Scoring Formula

```python
def compute_accuracy_score(correct, total):
    if total == 0:
        return 1.0  # No items to check
    return correct / total
```

### Coverage Checks (CV-1 to CV-8)

| ID | Name | Severity | Pass Criteria |
|----|------|----------|---------------|
| CV-1 | Python detected | High | Python files found with clones |
| CV-2 | C# detected | High | C# files found with clones |
| CV-3 | Java detected | High | Java files found with clones |
| CV-4 | JavaScript detected | High | JavaScript files found with clones |
| CV-5 | TypeScript detected | High | TypeScript files found with clones |
| CV-6 | Go detected | High | Go files found with clones |
| CV-7 | Rust detected | High | Rust files found with clones |
| CV-8 | Multi-language stats | Critical | by_language contains all 7 |

### Edge Case Checks (EC-1 to EC-8)

| ID | Name | Severity | Pass Criteria |
|----|------|----------|---------------|
| EC-1 | Empty files | Medium | 0 duplications reported |
| EC-2 | Single-line files | Low | Handled without error |
| EC-3 | Unicode identifiers | Medium | Files processed correctly |
| EC-4 | Large files | High | Processed within timeout |
| EC-5 | Deep nesting | Medium | Clones detected in nested code |
| EC-6 | Comments excluded | High | Comments not included in clones |
| EC-7 | No duplicates file | Critical | 0 clones for clean file |
| EC-8 | Heavy duplication | High | Multiple clones detected |

### Performance Checks (PF-1 to PF-4)

| ID | Name | Severity | Threshold | Description |
|----|------|----------|-----------|-------------|
| PF-1 | Synthetic repos | High | < 10s | All 7 language repos |
| PF-2 | Per-language speed | Medium | < 3s | Each language individually |
| PF-3 | Semantic mode overhead | Medium | < 2x | Semantic vs standard time |
| PF-4 | Memory usage | Low | < 500MB | Peak memory consumption |

---

## Check Catalog

Complete reference of all programmatic checks with pass criteria and evidence types:

| ID | Name | Category | Severity | Pass Criteria | Evidence Type |
|----|------|----------|----------|---------------|---------------|
| AC-1 | Clone count matches | Accuracy | Critical | Detected clones within expected range | Count comparison |
| AC-2 | Line range accuracy | Accuracy | High | start_line/end_line within ±2 | Line diff |
| AC-3 | Token count validity | Accuracy | Medium | Token counts > min_tokens | Token count |
| AC-4 | Cross-file detection | Accuracy | Critical | Cross-file clones linked | File pair list |
| AC-5 | Duplication percentage | Accuracy | High | Overall % within ±5% of expected | Percentage diff |
| AC-6 | Per-file metrics | Accuracy | Medium | Individual file % accurate | Per-file data |
| AC-7 | Semantic mode clones | Accuracy | High | Additional clones in semantic mode | Clone delta |
| AC-8 | Clone ID uniqueness | Accuracy | Low | All clone IDs unique | ID list |
| CV-1 | Python detected | Coverage | High | Python files with clones found | File list |
| CV-2 | C# detected | Coverage | High | C# files with clones found | File list |
| CV-3 | Java detected | Coverage | High | Java files with clones found | File list |
| CV-4 | JavaScript detected | Coverage | High | JS files with clones found | File list |
| CV-5 | TypeScript detected | Coverage | High | TS files with clones found | File list |
| CV-6 | Go detected | Coverage | High | Go files with clones found | File list |
| CV-7 | Rust detected | Coverage | High | Rust files with clones found | File list |
| CV-8 | Multi-language stats | Coverage | Critical | by_language contains all 7 | Language map |
| EC-1 | Empty files | Edge Cases | Medium | 0 duplications reported | Clone count |
| EC-2 | Single-line files | Edge Cases | Low | Handled without error | Status |
| EC-3 | Unicode identifiers | Edge Cases | Medium | Files processed correctly | Parse status |
| EC-4 | Large files | Edge Cases | High | Processed within timeout | Timing |
| EC-5 | Deep nesting | Edge Cases | Medium | Clones detected in nested code | Clone list |
| EC-6 | Comments excluded | Edge Cases | High | Comments not in clones | Clone content |
| EC-7 | No duplicates file | Edge Cases | Critical | 0 clones for clean file | Clone count |
| EC-8 | Heavy duplication | Edge Cases | High | Multiple clones detected | Clone count |
| PF-1 | Synthetic repos | Performance | High | All 7 langs < 10s | Timing |
| PF-2 | Per-language speed | Performance | Medium | Each language < 3s | Timing |
| PF-3 | Semantic overhead | Performance | Medium | Semantic < 2x standard | Timing ratio |
| PF-4 | Memory usage | Performance | Low | Peak < 500MB | Memory stats |

---

## LLM Judge Dimensions (4 Judges)

### Judge Weights

| Judge | Weight | Focus |
|-------|--------|-------|
| Duplication Accuracy | 35% | Are detected clones genuine? |
| Semantic Detection | 25% | Does semantic mode work correctly? |
| Cross-File Detection | 20% | Are cross-file clones linked? |
| Actionability | 20% | Are reports useful for refactoring? |

### Duplication Accuracy Judge (35%)

**Sub-dimensions**:
- Genuine clones (40%): No false positives in detected clones
- Line accuracy (30%): Line ranges match actual code
- Token validity (30%): Token counts are reasonable

**Scoring Rubric**:

| Score | Criteria |
|-------|----------|
| 5 | All detected clones are genuine with accurate line ranges |
| 4 | 95%+ genuine, minor line range discrepancies |
| 3 | 85%+ genuine, some false positives |
| 2 | Significant false positives (>20%) |
| 1 | Clone detection is unreliable |

### Semantic Detection Judge (25%)

**Sub-dimensions**:
- Identifier detection (50%): Renamed variable clones found
- Literal detection (50%): Different constant clones found

**Scoring Rubric**:

| Score | Criteria |
|-------|----------|
| 5 | All semantic duplicates detected with accurate matching |
| 4 | 90%+ semantic duplicates found |
| 3 | 75%+ found, some missed patterns |
| 2 | Limited semantic detection |
| 1 | Semantic mode not working |

### Cross-File Detection Judge (20%)

**Sub-dimensions**:
- Detection rate (50%): Cross-file clones found
- Linking accuracy (50%): Occurrences correctly associated

**Scoring Rubric**:

| Score | Criteria |
|-------|----------|
| 5 | All cross-file clones detected and linked correctly |
| 4 | 95%+ detected, minor linking issues |
| 3 | 80%+ detected, some orphaned occurrences |
| 2 | Significant cross-file detection gaps |
| 1 | Cross-file detection unreliable |

### Actionability Judge (20%)

**Sub-dimensions**:
- Report clarity (40%): Output is understandable
- Refactoring guidance (30%): Information supports refactoring
- Code fragments (30%): Sample code aids comprehension

**Scoring Rubric**:

| Score | Criteria |
|-------|----------|
| 5 | Immediately actionable for refactoring |
| 4 | Clear reports with minor improvements needed |
| 3 | Usable but requires interpretation |
| 2 | Reports are difficult to act on |
| 1 | Output is not actionable |

---

## Dimension Weights Summary

### Programmatic Weights (60% of combined)

| Dimension | Weight | Check Count |
|-----------|--------|-------------|
| Accuracy | 40% | 8 |
| Coverage | 25% | 8 |
| Edge Cases | 20% | 8 |
| Performance | 15% | 4 |

### LLM Weights (40% of combined)

| Dimension | Weight |
|-----------|--------|
| Duplication Accuracy | 35% |
| Semantic Detection | 25% |
| Cross-File Detection | 20% |
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
prog_coverage = coverage_passed / coverage_total * 0.25
prog_edge = edge_passed / edge_total * 0.20
prog_perf = perf_passed / perf_total * 0.15
programmatic_score = prog_accuracy + prog_coverage + prog_edge + prog_perf

# Normalize to 1-5 scale
programmatic_normalized = 1 + (programmatic_score * 4)

# LLM component (already 1-5 scale)
llm_score = (
    duplication_accuracy * 0.35 +
    semantic_detection * 0.25 +
    cross_file * 0.20 +
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

```python
def weighted_dimension_score(checks: list[Check]) -> float:
    """Calculate severity-weighted dimension score."""
    weights = {"critical": 2.0, "high": 1.5, "medium": 1.0, "low": 0.5}
    total_weight = sum(weights[c.severity] for c in checks)
    passed_weight = sum(weights[c.severity] for c in checks if c.passed)
    return passed_weight / total_weight if total_weight > 0 else 1.0
```

---

## Test Scenarios

### Synthetic Repositories (7 Languages)

Each language has identical test structure:

| File | Purpose | Expected Clones |
|------|---------|-----------------|
| `no_duplication.*` | Clean code | 0 |
| `light_duplication.*` | Small clones | 1-2 |
| `heavy_duplication.*` | Large blocks | 3-5 |
| `cross_file_a.*` + `_b.*` | Cross-file | 1 (linked) |
| `semantic_dup_identifiers.*` | Renamed vars | 0 std / 1 semantic |
| `semantic_dup_literals.*` | Different constants | 0 std / 1 semantic |

### Languages Covered

1. Python (`.py`)
2. C# (`.cs`)
3. Java (`.java`)
4. JavaScript (`.js`)
5. TypeScript (`.ts`)
6. Go (`.go`)
7. Rust (`.rs`)

---

## Running Evaluation

### Programmatic Evaluation

```bash
# Full evaluation with verbose output
make evaluate

# Quick evaluation (skip performance checks)
make evaluate QUICK=1

# JSON output only
make evaluate-json
```

### LLM Evaluation

```bash
# Full LLM evaluation (4 judges, opus model)
make evaluate-llm

# Specific model
make evaluate-llm MODEL=sonnet

# Skip specific judges
make evaluate-llm SKIP_JUDGES="actionability"
```

### Combined Evaluation

```bash
# Run both programmatic and LLM evaluation
make evaluate-all
```

### Evaluation Output

```json
{
  "timestamp": "2026-01-05T14:30:00Z",
  "summary": {
    "total_checks": 28,
    "passed": 27,
    "failed": 1,
    "score": 0.964
  },
  "checks": [
    {
      "check_id": "AC-1",
      "name": "Clone count matches",
      "category": "accuracy",
      "severity": "critical",
      "passed": true,
      "score": 1.0,
      "message": "15/15 expected clones detected",
      "evidence": {...}
    }
  ]
}
```

---

## Ground Truth Specifications

### Source Data

Ground truth files in `evaluation/ground-truth/` contain expected values per language:

```json
{
  "language": "python",
  "files": {
    "no_duplication.py": { "expected_clones": 0 },
    "light_duplication.py": { "expected_clones": {"min": 1, "max": 2} },
    "heavy_duplication.py": { "expected_clones": {"min": 3, "max": 5} }
  },
  "cross_file": {
    "expected_clones": 1,
    "files": ["cross_file_a.py", "cross_file_b.py"]
  },
  "semantic": {
    "identifiers": { "standard": 0, "semantic": 1 },
    "literals": { "standard": 0, "semantic": 1 }
  }
}
```

### Per-Scenario Expected Values

| Scenario | File Pattern | Standard Mode | Semantic Mode | Notes |
|----------|--------------|---------------|---------------|-------|
| No duplication | `no_duplication.*` | 0 clones | 0 clones | Clean baseline |
| Light duplication | `light_duplication.*` | 1-2 clones | 1-2 clones | ~15 line blocks |
| Heavy duplication | `heavy_duplication.*` | 3-5 clones | 3-5 clones | 30+ line blocks |
| Cross-file | `cross_file_a.*` + `_b.*` | 1 linked clone | 1 linked clone | Same code, 2 files |
| Semantic identifiers | `semantic_dup_identifiers.*` | 0 clones | 1 clone | Renamed variables |
| Semantic literals | `semantic_dup_literals.*` | 0 clones | 1 clone | Different constants |

### Tolerance Ranges

| Metric | Tolerance | Rationale |
|--------|-----------|-----------|
| Clone count | ±0 for exact, range for approx | CPD is deterministic |
| Line numbers | ±2 lines | Minor tokenization differences |
| Token count | ±5% | Language-specific tokenization |
| Duplication % | ±5% | Rounding differences |

### File-Level Ground Truth Schema

```json
{
  "$schema": "ground-truth.schema.json",
  "file": "heavy_duplication.py",
  "expected_clones": {
    "count": { "min": 3, "max": 5 },
    "total_lines": { "min": 90, "max": 150 },
    "duplication_pct": { "min": 15, "max": 25 }
  },
  "expected_locations": [
    { "start_line": 10, "end_line": 40, "tolerance": 2 },
    { "start_line": 50, "end_line": 80, "tolerance": 2 }
  ]
}
```

### Generation Process

1. **Create test files**: Write known duplicates with specific patterns
2. **Run CPD**: Initial analysis to validate detection
3. **Manual verification**: Confirm clone boundaries match code
4. **Document expected**: Record expected values in ground truth
5. **Version control**: Commit ground truth alongside test files

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

## Extending Evaluation

### Adding New Programmatic Checks

1. **Create check function** in the appropriate category file (`scripts/checks/accuracy.py`, etc.):

```python
from .base import check, CheckResult, Severity

@check("AC-9", "New check name", "accuracy", Severity.HIGH)
def check_new_feature(data: dict, ground_truth: dict | None) -> CheckResult:
    """Verify new feature works correctly."""
    # Extract data
    actual = data.get("new_metric", 0)
    expected = ground_truth.get("expected_new_metric", 0) if ground_truth else 0

    # Evaluate
    passed = actual >= expected

    return CheckResult(
        passed=passed,
        score=1.0 if passed else 0.0,
        message=f"New metric: {actual} (expected >= {expected})",
        evidence={"actual": actual, "expected": expected}
    )
```

2. **Register check** in the category's `__init__.py`:

```python
from .accuracy import check_new_feature
ACCURACY_CHECKS.append(check_new_feature)
```

3. **Update ground truth** if needed in `evaluation/ground-truth/`

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
        # Parse LLM response into score and reasoning
        return {"score": 4.0, "reasoning": "...", "confidence": 0.9}
```

2. **Create prompt template** in `evaluation/llm/prompts/new_dimension.md`

3. **Register judge** in `evaluation/llm/__init__.py`:

```python
from .judges.new_dimension import NewDimensionJudge
JUDGES = [..., NewDimensionJudge]
```

### Adding New Evaluation Dimensions

To add a completely new dimension (e.g., "Maintainability"):

1. Create new category file: `scripts/checks/maintainability.py`
2. Define checks with new category prefix (e.g., "MT-1", "MT-2")
3. Add weight allocation in `evaluate.py`:

```python
DIMENSION_WEIGHTS = {
    "accuracy": 0.35,
    "coverage": 0.20,
    "edge_cases": 0.20,
    "performance": 0.10,
    "maintainability": 0.15,  # New dimension
}
```

4. Update documentation in EVAL_STRATEGY.md

### Template for New Checks

```python
@check(
    check_id="XX-N",           # Category prefix + number
    name="Descriptive name",   # Human-readable name
    category="category_name",  # accuracy, coverage, edge_cases, performance
    severity=Severity.HIGH     # CRITICAL, HIGH, MEDIUM, LOW
)
def check_something(data: dict, ground_truth: dict | None) -> CheckResult:
    """
    One-line description of what this check validates.

    Args:
        data: Parsed tool output JSON
        ground_truth: Expected values (or None if no ground truth)

    Returns:
        CheckResult with passed, score, message, and evidence
    """
    # Implementation
    pass
```

---

## References

- [PMD CPD Documentation](https://pmd.github.io/latest/pmd_userdocs_cpd.html)
- [Clone Detection Types](https://en.wikipedia.org/wiki/Duplicate_code#Types_of_code_clones)
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685)

---

## Rollup Validation

Rollups:
- directory_counts_direct
- directory_counts_recursive

Tests:
- src/sot-engine/dbt/tests/test_rollup_pmd_cpd_direct_vs_recursive.sql

### Invariants Tested

| Invariant | Description |
|-----------|-------------|
| recursive >= direct | Recursive counts include all descendants |
| recursive_dup_lines >= direct_dup_lines | Duplication aggregates follow hierarchy |
