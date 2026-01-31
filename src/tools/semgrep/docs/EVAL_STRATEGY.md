# Evaluation Strategy: Semgrep PoC

This document describes the evaluation framework used to assess Semgrep as a code smell detection tool for the DD Platform.

## Overview

The evaluation uses a **dual-track approach**:
1. **Programmatic Checks (60%)**: Automated validation against ground truth
2. **LLM Judges (40%)**: AI-powered qualitative assessment

Combined scores determine the final decision:
- **STRONG PASS**: ≥4.0/5.0
- **PASS**: ≥3.5/5.0
- **WEAK PASS**: ≥3.0/5.0
- **FAIL**: <3.0/5.0

---

## Programmatic Evaluation (28 Checks)

### Accuracy Checks (AC-1 to AC-8)

| Check | Name | Target | Pass Criteria |
|-------|------|--------|---------------|
| AC-1 | SQL injection detection | sql_injection.* files | ≥1 finding per file |
| AC-2 | Empty catch detection | empty_catch.* files | ≥1 finding per file |
| AC-3 | Catch-all detection | catch_all.* files | ≥1 finding per file |
| AC-4 | Async void detection | async_void.* files | ≥1 finding per file |
| AC-5 | HTTP client issues | resource_leak.* files | ≥1 finding per file |
| AC-6 | High complexity | complexity.* files | ≥1 finding per file |
| AC-7 | God class detection | god_class.* files | ≥1 finding per file |
| AC-8 | Overall precision | All files | >50% true positive rate |

**Scoring**: Each check scores 0.0-1.0 based on detection rate.

### Coverage Checks (CV-1 to CV-8)

| Check | Name | Target | Pass Criteria |
|-------|------|--------|---------------|
| CV-1 | Python coverage | python/*.py | ≥1 smell detected |
| CV-2 | JavaScript coverage | javascript/*.js | ≥1 smell detected |
| CV-3 | TypeScript coverage | typescript/*.ts | ≥1 smell detected |
| CV-4 | C# coverage | csharp/*.cs | ≥1 smell detected |
| CV-5 | Java coverage | java/*.java | ≥1 smell detected |
| CV-6 | Go coverage | go/*.go | ≥1 smell detected |
| CV-7 | Rust coverage | rust/*.rs | ≥1 smell detected |
| CV-8 | DD category coverage | All categories | ≥5/9 categories covered |

**Scoring**: Language checks score based on files with findings / total files.

### Edge Case Checks (EC-1 to EC-8)

| Check | Name | Target | Pass Criteria |
|-------|------|--------|---------------|
| EC-1 | Empty files | empty.* files | No crashes |
| EC-2 | Unicode content | Files with Unicode | No encoding errors |
| EC-3 | Large files | Files >500 LOC | Analysis completes |
| EC-4 | Deep nesting | Deeply nested code | No stack overflow |
| EC-5 | Mixed language | JS/TS mixed files | Correct detection |
| EC-6 | False positives | no_smell.* files | 0 smells detected |
| EC-7 | Syntax errors | Malformed files | Graceful handling |
| EC-8 | Path handling | Special chars in paths | Correct processing |

**Scoring**: Pass/fail with 1.0 or 0.0.

### Performance Checks (PF-1 to PF-4)

| Check | Name | Target | Pass Criteria |
|-------|------|--------|---------------|
| PF-1 | Synthetic speed | 18 files | <15 seconds |
| PF-2 | Per-file efficiency | All files | <1000ms per file |
| PF-3 | Throughput | All files | ≥100 LOC/second |
| PF-4 | Startup overhead | N/A | <80% of total time |

**Scoring**: Ratio of threshold to actual (capped at 1.0).

---

## Ground Truth Files

Located in `evaluation/ground-truth/`:

```json
// python.json example
{
  "language": "python",
  "files": {
    "sql_injection.py": {
      "expected_smells": ["SQL_INJECTION"],
      "expected_count_min": 1,
      "expected_count_max": 10
    },
    "no_smells.py": {
      "expected_smells": [],
      "expected_count_min": 0,
      "expected_count_max": 0
    }
  }
}
```

### Ground Truth Principles

1. **Range-based expectations**: Allow min-max range, not exact counts
2. **Type-based validation**: Check smell types, not just counts
3. **Negative cases**: Include clean files to test false positive rate
4. **Language-specific**: Separate files per language

---

## LLM Evaluation (4 Judges)

### Judge 1: Smell Accuracy (35% weight)

**Focus**: Are detected smells genuine issues?

**Sub-dimensions**:
- True Positives (40%): Detected smells are actual issues
- Category Accuracy (30%): DD categories correctly assigned
- Location Accuracy (30%): Line numbers and file paths correct

**Evidence collected**:
- Sample of detected smells
- Comparison with ground truth
- Category breakdown

### Judge 2: Rule Coverage (25% weight)

**Focus**: Does Semgrep cover target languages and categories?

**Sub-dimensions**:
- Language Coverage (40%): All 7 target languages detected
- Category Coverage (35%): All 9 DD categories addressed
- Rule Variety (25%): Sufficient rule diversity

**Evidence collected**:
- Language statistics
- Category statistics
- Unique rule list

### Judge 3: False Positive Rate (20% weight)

**Focus**: Is the tool precise or noisy?

**Sub-dimensions**:
- Clean File Precision (40%): Files marked clean have no smells
- Contextual Appropriateness (35%): Detections are contextually valid
- Severity Calibration (25%): Severity levels not inflated

**Evidence collected**:
- Clean file results
- Potential false positives
- Severity distribution

### Judge 4: Actionability (20% weight)

**Focus**: Can developers act on findings?

**Sub-dimensions**:
- Message Clarity (40%): Messages explain the issue clearly
- Fix Suggestions (30%): Actionable remediation advice provided
- Location Precision (30%): Exact file, line, and range specified

**Evidence collected**:
- Sample messages
- Fix suggestion rate
- Location quality metrics

---

## Combined Scoring

```python
# Normalize programmatic score (0-1) to 1-5 scale
programmatic_normalized = programmatic_score * 4 + 1

# Calculate combined score
combined_score = (
    programmatic_normalized * 0.60 +  # 60% weight
    llm_score * 0.40                   # 40% weight
)

# Decision
if combined_score >= 4.0:
    decision = "STRONG_PASS"
elif combined_score >= 3.5:
    decision = "PASS"
elif combined_score >= 3.0:
    decision = "WEAK_PASS"
else:
    decision = "FAIL"
```

---

## Running Evaluations

### Programmatic Only

```bash
make evaluate
```

Output: Console report + `output/evaluation_report.json`

### LLM Only

```bash
make evaluate-llm
```

Output: Console report + `output/llm_evaluation.json`

### Combined

```bash
make evaluate-combined
```

Output: Console report + `output/combined_evaluation.json`

### Quick (Skip Performance)

```bash
make evaluate-quick
```

---

## Calibration Notes

### Why 69% Programmatic Score?

The 69% score reflects:
- **Strong security detection** (SQL injection 100%)
- **Limited DD category mapping** (0/9 categories)
- **Good edge case handling** (93.8%)
- **Missing code smell rules** (empty catch 0%, async void 0%)

This is expected for a security-focused tool. Semgrep excels at its purpose (security) but doesn't cover all DD smell categories.

### Recommended Threshold Adjustments

For production use, consider:
- Lowering AC-2, AC-3, AC-4 expectations (security tool, not code smell tool)
- Raising CV-8 threshold (category coverage less relevant)
- Adding custom rules for DD-specific smells

---

## References

- [Semgrep Custom Rules](https://semgrep.dev/docs/writing-rules/overview/)
- [DD Smell Catalogue](../../../src/dd_analyzer/collectors/smell_catalogue.json)
- [PoC Evaluation Pattern](../poc-jscpd/docs/EVAL_STRATEGY.md)
