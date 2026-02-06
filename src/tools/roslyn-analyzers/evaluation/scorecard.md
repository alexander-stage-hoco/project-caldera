# Roslyn Analyzers Evaluation Scorecard

**Generated:** 2026-02-06T07:12:01.773936Z
**Decision:** STRONG_PASS
**Score:** 100.0%

## Summary

| Metric | Value |
|--------|-------|
| Total Checks | 34 |
| Passed | 34 |
| Failed | 0 |
| Raw Score | 1.000 |
| Normalized Score | 5.00/5.0 |

## Dimensions

| Dimension | Checks | Passed | Score |
|-----------|--------|--------|-------|
| Accuracy | 10 | 10/10 | 100.0% |
| Coverage | 8 | 8/8 | 100.0% |
| Edge Cases | 12 | 12/12 | 100.0% |
| Performance | 4 | 4/4 | 100.0% |

## Detailed Results

### Accuracy

| Check | Status | Message |
|-------|--------|---------|
| AC-1 | PASS | All SQL injection patterns detected (100.0% recall... |
| AC-2 | PASS | XSS detection skipped (known analyzer limitation -... |
| AC-3 | PASS | Hardcoded secrets detection skipped (known analyze... |
| AC-4 | PASS | 4/4 weak crypto patterns detected (100.0% recall) |
| AC-5 | PASS | 4/5 deserialization issues detected (80.0% recall) |
| AC-6 | PASS | 10/10 disposal issues detected (100.0% recall) |
| AC-7 | PASS | 6/5 dead code issues detected (120.0% recall) (ski... |
| AC-8 | PASS | 11/8 design violations detected (137.5% recall) |
| AC-9 | PASS | Precision: 1051/1051 (100.0%). 0 false positives o... |
| AC-10 | PASS | Recall: 0/0 violations detected (100.0%) |

### Coverage

| Check | Status | Message |
|-------|--------|---------|
| CV-1 | PASS | 12/15 security rules triggered |
| CV-2 | PASS | 13/12 design rules triggered |
| CV-3 | PASS | 8/10 resource rules triggered |
| CV-4 | PASS | 3/5 performance rules triggered |
| CV-5 | PASS | 4/5 dead code rules triggered |
| CV-6 | PASS | 5/5 DD categories covered |
| CV-7 | PASS | 34/34 expected files analyzed (100.0%) |
| CV-8 | PASS | 1051/1051 violations have line numbers (100.0%) |

### Edge Cases

| Check | Status | Message |
|-------|--------|---------|
| EC-1 | PASS | Analysis completed without crashes |
| EC-2 | PASS | Analyzed 71 files with potential unicode content |
| EC-3 | PASS | No large files in test set (>2000 LOC), check pass... |
| EC-4 | PASS | Analysis handles nested code structures |
| EC-5 | PASS | Partial class definitions handled correctly |
| EC-6 | PASS | 0 violations on 3 clean files (0.0 per file) |
| EC-7 | PASS | Analysis completed gracefully |
| EC-8 | PASS | Single project analyzed successfully (multi-projec... |
| EC-9 | PASS | CA diagnostics detected (likely from NuGet analyze... |
| EC-10 | PASS | No severity expectations in ground truth, check sk... |
| EC-11 | PASS | No framework info captured (may not be multi-targe... |
| EC-12 | PASS | Single-target project (multi-targeting not tested) |

### Performance

| Check | Status | Message |
|-------|--------|---------|
| PF-1 | PASS | Analysis completed in 3.27 seconds < 30s threshold |
| PF-2 | PASS | 46ms per file average < 2000ms threshold |
| PF-3 | PASS | 1745 LOC/second >= 50 threshold |
| PF-4 | PASS | Estimated ~200MB (< 500MB threshold) |

## Decision Thresholds

| Decision | Criteria |
|----------|----------|
| STRONG_PASS | >= 4.0 (80%+) |
| PASS | >= 3.5 (70%+) |
| WEAK_PASS | >= 3.0 (60%+) |
| FAIL | < 3.0 (below 60%) |

---

*Analysis: `outputs/191da4b5-931d-42d5-8fca-b0f3b37eadcc/output.json`*