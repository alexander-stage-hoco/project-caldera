# DevSkim Evaluation Scorecard

**Generated:** 2026-02-13T06:07:10.285623+00:00
**Decision:** STRONG_PASS
**Score:** 94.47%

## Summary

| Metric | Value |
|--------|-------|
| Total Checks | 30 |
| Passed | 29 |
| Failed | 1 |
| Raw Score | 0.945 |
| Normalized Score | 4.72/5.0 |

## Dimensions

| Dimension | Checks | Passed | Score |
|-----------|--------|--------|-------|
| Accuracy | 8 | 8/8 | 100.0% |
| Coverage | 8 | 8/8 | 93.0% |
| Edge Cases | 8 | 7/8 | 86.2% |
| Integration Fit | 1 | 1/1 | 100.0% |
| Output Quality | 1 | 1/1 | 100.0% |
| Performance | 4 | 4/4 | 100.0% |

## Detailed Results

### Accuracy

| Check | Status | Message |
|-------|--------|---------|
| AC-1 | PASS | Skipped: No SQL injection expectations in ground t... |
| AC-2 | PASS | Skipped: No hardcoded secret expectations in groun... |
| AC-3 | PASS | Skipped: No insecure crypto expectations in ground... |
| AC-4 | PASS | Skipped: No path traversal expectations in ground ... |
| AC-5 | PASS | Skipped: No XSS expectations in ground truth |
| AC-6 | PASS | Skipped: No deserialization expectations in ground... |
| AC-7 | PASS | Found 0 potential false positives out of 22917 tot... |
| AC-8 | PASS | Precision: 1.00, Recall: 1.00, F1: 1.00 |

### Coverage

| Check | Status | Message |
|-------|--------|---------|
| CV-1 | PASS | 2595 files, 411 issues, 8 categories |
| CV-2 | PASS | Skipped: python not present in ground truth |
| CV-3 | PASS | Skipped: javascript not present in ground truth |
| CV-4 | PASS | Skipped: java not present in ground truth |
| CV-5 | PASS | Skipped: go not present in ground truth |
| CV-6 | PASS | Skipped: cpp not present in ground truth |
| CV-7 | PASS | Analyzed 3 of 1 expected languages |
| CV-8 | PASS | Covered 7/15 security categories |

### Edge Cases

| Check | Status | Message |
|-------|--------|---------|
| EC-1 | PASS | Found 0 empty files, handled correctly |
| EC-2 | PASS | Analyzed 548 large files (>1000 lines) |
| EC-3 | PASS | Found 291 files with multiple issue types |
| EC-4 | PASS | Nested code structures handled |
| EC-5 | PASS | Comments handled correctly |
| EC-6 | FAIL | Found 189 potential false positives in string lite... |
| EC-7 | PASS | Minified code handled |
| EC-8 | PASS | Encoding variations handled gracefully |

### Integration Fit

| Check | Status | Message |
|-------|--------|---------|
| IF-1 | PASS | 3407/3407 files have relative paths |

### Output Quality

| Check | Status | Message |
|-------|--------|---------|
| OQ-1 | PASS | Schema validation passed |

### Performance

| Check | Status | Message |
|-------|--------|---------|
| PF-1 | PASS | Completed in 57.9s (target: <300s) |
| PF-2 | PASS | Throughput: 58.9 files/second |
| PF-3 | PASS | Throughput: 154640 lines/second (waived) |
| PF-4 | PASS | Output completeness: 100% |

## Decision Thresholds

| Decision | Criteria |
|----------|----------|
| STRONG_PASS | >= 4.0 (80%+) |
| PASS | >= 3.5 (70%+) |
| WEAK_PASS | >= 3.0 (60%+) |
| FAIL | < 3.0 (below 60%) |

---

*Analysis: `/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/outputs/a03e871f-19b8-4728-aba8-eec58e9e0fb9/output.json`*
*Ground Truth: `/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/evaluation/ground-truth`*