# Evaluation Strategy: Lizard PoC

This document describes the evaluation methodology for PoC #2 (Lizard function-level complexity analysis).

## Evaluation Philosophy

The evaluation combines **programmatic checks** with **LLM-as-a-Judge** evaluation:

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 60% | Objective, reproducible, fast |
| LLM Judges | 40% | Semantic understanding, edge cases |

This hybrid approach provides both precision and nuance.

---

## Scoring System

### Combined Score Calculation

```python
# Normalize programmatic score to 1-5 scale
programmatic_normalized = 1 + (programmatic_score * 4)  # 0-1 → 1-5

# Weighted combination
combined_score = (0.60 * programmatic_normalized) + (0.40 * llm_score)
```

### Decision Thresholds

| Decision | Combined Score | Interpretation |
|----------|----------------|----------------|
| STRONG_PASS | >= 4.0 | Excellent, production-ready |
| PASS | >= 3.5 | Good, minor improvements needed |
| WEAK_PASS | >= 3.0 | Acceptable with caveats |
| FAIL | < 3.0 | Significant issues |

---

## Programmatic Checks (76 Total)

### Overview by Category

| Category | Checks | Severity Mix | Purpose |
|----------|--------|--------------|---------|
| Accuracy | 56 | 7 critical, 14 high, 28 medium, 7 low | CCN correctness |
| Coverage | 8 | 1 critical, 7 high | Language detection |
| Edge Cases | 8 | 2 high, 4 medium, 2 low | Edge case handling |
| Performance | 4 | 1 high, 2 medium, 1 low | Speed/memory |

### Accuracy Checks (AC-1 to AC-8, per language)

Each accuracy check runs against all 7 languages, yielding 56 checks.

| ID | Name | Severity | Pass Criteria |
|----|------|----------|---------------|
| AC-1 | Simple functions CCN=1 | Critical | All functions with expected CCN=1 report CCN=1 |
| AC-2 | Complex functions CCN 10-20 | High | CCN within ±2 of expected |
| AC-3 | Massive functions CCN >= 20 | High | CCN within ±3 of expected |
| AC-4 | Function count matches | Critical | Detected count = expected count |
| AC-5 | NLOC accuracy within 10% | Medium | NLOC within 10% of expected |
| AC-6 | Parameter count accuracy | Medium | Exact match for parameter count |
| AC-7 | Line range accuracy | Low | start_line/end_line within tolerance |
| AC-8 | Nested function detection | Medium | Nested functions detected with qualified names |

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
| CV-1 | Python detected | High | Python files found with functions |
| CV-2 | C# detected | High | C# files found with functions |
| CV-3 | Java detected | High | Java files found with functions |
| CV-4 | JavaScript detected | High | JavaScript files found with functions |
| CV-5 | TypeScript detected | High | TypeScript files found with functions |
| CV-6 | Go detected | High | Go files found with functions |
| CV-7 | Rust detected | High | Rust files found with functions |
| CV-8 | All languages in summary | Critical | by_language contains all 7 |

### Edge Case Checks (EC-1 to EC-8)

| ID | Name | Severity | Pass Criteria |
|----|------|----------|---------------|
| EC-1 | Empty files | Medium | 0 functions reported |
| EC-2 | Comments-only files | Medium | 0 functions reported |
| EC-3 | Single-line files | Low | Handled without error |
| EC-4 | Unicode function names | Medium | Detected and named correctly |
| EC-5 | Deep nesting | High | CCN >= 8 for deeply nested functions |
| EC-6 | Lambda functions | Low | Detected (28 expected) |
| EC-7 | Class methods | High | Detected with qualified names |
| EC-8 | Anonymous functions | Low | Handled appropriately |

### Performance Checks (PF-1 to PF-4)

| ID | Name | Severity | Threshold | Actual |
|----|------|----------|-----------|--------|
| PF-1 | Synthetic repos | High | < 2s | 0.29s |
| PF-2 | Real repo: click | Medium | < 5s | 0.35s |
| PF-3 | Real repo: picocli | Medium | < 30s | 1.63s |
| PF-4 | Memory usage | Low | < 500MB | 45.1MB |

---

## Dimension Summary

| Dimension | Weight | Pass Criteria | Focus Area |
|-----------|--------|---------------|------------|
| Accuracy | 60% | 95%+ correct CCN values | CCN, NLOC, parameter accuracy |
| Coverage | 15% | All 7 languages detected | Language support breadth |
| Edge Cases | 15% | Handle unicode, nesting, lambdas | Robustness |
| Performance | 10% | Within time/memory thresholds | Scalability |

---

## Check Catalog

### Accuracy Checks (AC-1 to AC-8)

| Check ID | Name | Severity | Pass Criteria |
|----------|------|----------|---------------|
| AC-1 | Simple functions CCN=1 | Critical | All functions with expected CCN=1 report CCN=1 |
| AC-2 | Complex functions CCN 10-20 | High | CCN within ±2 of expected |
| AC-3 | Massive functions CCN >= 20 | High | CCN within ±3 of expected |
| AC-4 | Function count matches | Critical | Detected count = expected count |
| AC-5 | NLOC accuracy within 10% | Medium | NLOC within 10% of expected |
| AC-6 | Parameter count accuracy | Medium | Exact match for parameter count |
| AC-7 | Line range accuracy | Low | start_line/end_line within tolerance |
| AC-8 | Nested function detection | Medium | Nested functions detected with qualified names |

### Coverage Checks (CV-1 to CV-8)

| Check ID | Name | Severity | Pass Criteria |
|----------|------|----------|---------------|
| CV-1 | Python detected | High | Python files found with functions |
| CV-2 | C# detected | High | C# files found with functions |
| CV-3 | Java detected | High | Java files found with functions |
| CV-4 | JavaScript detected | High | JavaScript files found with functions |
| CV-5 | TypeScript detected | High | TypeScript files found with functions |
| CV-6 | Go detected | High | Go files found with functions |
| CV-7 | Rust detected | High | Rust files found with functions |
| CV-8 | All languages in summary | Critical | by_language contains all 7 |

### Edge Case Checks (EC-1 to EC-8)

| Check ID | Name | Severity | Pass Criteria |
|----------|------|----------|---------------|
| EC-1 | Empty files | Medium | 0 functions reported |
| EC-2 | Comments-only files | Medium | 0 functions reported |
| EC-3 | Single-line files | Low | Handled without error |
| EC-4 | Unicode function names | Medium | Detected and named correctly |
| EC-5 | Deep nesting | High | CCN >= 8 for deeply nested functions |
| EC-6 | Lambda functions | Low | Detected (28 expected) |
| EC-7 | Class methods | High | Detected with qualified names |
| EC-8 | Anonymous functions | Low | Handled appropriately |

### Performance Checks (PF-1 to PF-4)

| Check ID | Name | Severity | Threshold |
|----------|------|----------|-----------|
| PF-1 | Synthetic repos | High | < 2s |
| PF-2 | Real repo: click | Medium | < 5s |
| PF-3 | Real repo: picocli | Medium | < 30s |
| PF-4 | Memory usage | Low | < 500MB |

---

## LLM Judge Dimensions (4 Judges)

### Judge Weights

| Judge | Weight | Focus |
|-------|--------|-------|
| CCN Accuracy | 35% | CCN calculation correctness |
| Function Detection | 25% | Nested/lambda/method detection |
| Statistics | 20% | Distribution validity |
| Hotspot Ranking | 20% | Prioritization accuracy |

---

## Rollup Validation

Rollups:
- directory_direct_distributions
- directory_recursive_distributions

Tests:
- src/sot-engine/dbt/tests/test_rollup_lizard_direct_distribution_ranges.sql
- src/sot-engine/dbt/tests/test_rollup_lizard_direct_vs_recursive.sql
- src/sot-engine/dbt/tests/test_rollup_lizard_distribution_ranges.sql
| Statistics | 20% | Distribution validity |
| Hotspot Ranking | 20% | Prioritization accuracy |

### CCN Accuracy Judge (35%)

**Sub-dimensions**:
- Simple functions (33%): CCN=1 correctly identified
- Complex functions (33%): CCN 10-20 accuracy
- Edge cases (34%): Lambdas, nested, class methods

**Scoring Rubric**:

| Score | Criteria |
|-------|----------|
| 5 | All sampled CCN values match ground truth exactly |
| 4 | 90%+ exact matches, minor deviations (±1) for rest |
| 3 | 70%+ within ±1 of expected, some outliers |
| 2 | Significant errors (>30% off by ±2 or more) |
| 1 | CCN values are systematically wrong |

### Function Detection Judge (25%)

**Sub-dimensions**:
- Regular functions (33%): Top-level functions found
- Class methods (33%): Methods with qualified names
- Edge cases (34%): Nested, anonymous, lambdas

**Scoring Rubric**:

| Score | Criteria |
|-------|----------|
| 5 | All function types detected with correct naming |
| 4 | 95%+ detected, minor naming issues |
| 3 | 80%+ detected, some missed nested/anonymous |
| 2 | Significant detection gaps |
| 1 | Major function types missed |

### Statistics Judge (20%)

**Sub-dimensions**:
- Basic statistics (33%): count, min, max, mean valid
- Percentiles (33%): Monotonicity preserved
- Advanced metrics (34%): Gini, skewness, kurtosis valid

**Scoring Rubric**:

| Score | Criteria |
|-------|----------|
| 5 | All statistics mathematically valid and consistent |
| 4 | Minor inconsistencies, all ranges valid |
| 3 | Some invalid values, percentiles correct |
| 2 | Multiple invalid statistics |
| 1 | Statistics are unreliable |

### Hotspot Ranking Judge (20%)

**Sub-dimensions**:
- CCN hotspots (33%): Top functions by CCN correct
- Multi-metric (33%): CCN-NLOC correlation valid
- Directory-level (34%): Directory aggregations correct

**Scoring Rubric**:

| Score | Criteria |
|-------|----------|
| 5 | Hotspots correctly prioritized, thresholds accurate |
| 4 | Minor ranking issues, thresholds correct |
| 3 | Some misranked functions, thresholds approximate |
| 2 | Significant ranking errors |
| 1 | Hotspot identification unreliable |

---

## Ground Truth Methodology

### Source Data

Ground truth files (`evaluation/ground-truth/*.json`) contain expected values for all 524 functions across 7 languages.

### Generation Process

1. **Run Lizard**: Initial analysis to get baseline values
2. **Manual Verification**: Spot-check CCN by counting decision points
3. **Cross-Reference**: Compare with IDE static analysis
4. **Edge Case Review**: Verify complex constructs (nested, anonymous)

### CCN Calculation Rules

Lizard counts these decision points:

```
if, else if, else        +1 each
for, while, do-while     +1 each
case (in switch)         +1 each
catch                    +1 each
&&, ||                   +1 each
? (ternary)              +1 each
```

**Base CCN**: Every function starts at CCN=1 (one path through).

### Example Verification

```python
def is_valid(user):           # CCN starts at 1
    if user.age >= 18:        # +1 (if)
        if user.email:        # +1 (if)
            if "@" in email:  # +1 (if)
                return True
    return False
# Expected CCN = 1 + 3 = 4
```

---

## Evaluation Workflow

### Running Programmatic Evaluation

```bash
# Full evaluation with verbose output
make evaluate

# Quick evaluation (skip performance checks)
make evaluate-quick

# JSON-only output
make evaluate-json
```

### Running LLM Evaluation

```bash
# Full LLM evaluation (4 judges, opus model)
make evaluate-llm

# Focused evaluation (single judge)
make evaluate-llm-focused

# Combined evaluation (programmatic + LLM)
make evaluate-combined
```

### Evaluation Outputs

Evaluation artifacts are written to a fixed location and overwrite the previous run:

```
evaluation/results/
├── output.json               # Envelope output for evaluation runs
├── evaluation_report.json    # Programmatic evaluation report
├── scorecard.md              # Programmatic scorecard
└── llm_evaluation.json       # LLM judge results (if run)
```

### Evaluation Output

```json
{
  "timestamp": "2026-01-05T09:34:55Z",
  "summary": {
    "total_checks": 76,
    "passed": 76,
    "failed": 0,
    "score": 0.988
  },
  "checks": [
    {
      "check_id": "AC-1",
      "name": "Simple functions CCN=1",
      "category": "accuracy",
      "severity": "critical",
      "passed": true,
      "score": 1.0,
      "message": "79/79 simple functions correctly identified",
      "evidence": {...}
    }
  ]
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

### Ground Truth Confidence

Assertions can cap LLM scores if ground truth checks fail:

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
    "correct": 79,
    "total": 79,
    "incorrect_functions": [],
    "language": "java"
}
```

### Evidence Types by Check

| Check Type | Evidence Collected |
|------------|-------------------|
| Accuracy | Function names, expected vs actual CCN |
| Coverage | File paths, function counts per language |
| Edge Cases | Edge case files, handling results |
| Performance | Elapsed time, threshold, path |

---

## Continuous Improvement

### Adding New Checks

1. Create check function in appropriate module
2. Add to `run_*_checks()` in that module
3. Update ground truth if needed
4. Run `make evaluate` to verify

### Updating Thresholds

Thresholds are defined in check functions:

```python
# In performance.py
threshold_seconds = 2.0  # PF-1 threshold

# In accuracy.py
tolerance = 2  # AC-2 CCN tolerance
```

### Calibrating LLM Judges

Use the calibration dataset to validate judge consistency:

```
evaluation/llm/calibration/calibration_dataset.json
```

---

## References

- [Lizard GitHub](https://github.com/terryyin/lizard)
- [McCabe Cyclomatic Complexity](https://en.wikipedia.org/wiki/Cyclomatic_complexity)
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685)
