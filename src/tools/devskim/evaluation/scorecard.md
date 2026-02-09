# DevSkim Evaluation Scorecard

**Generated:** 2026-02-09T20:14:07.387618+00:00
**Decision:** STRONG_PASS
**Score:** 95.47%

## Summary

| Metric | Value |
|--------|-------|
| Total Checks | 30 |
| Passed | 30 |
| Failed | 0 |
| Raw Score | 0.955 |
| Normalized Score | 4.77/5.0 |

## Dimensions

| Dimension | Checks | Passed | Score |
|-----------|--------|--------|-------|
| Accuracy | 8 | 8/8 | 100.0% |
| Coverage | 8 | 8/8 | 90.6% |
| Edge Cases | 8 | 8/8 | 92.4% |
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
| AC-7 | PASS | Found 0 potential false positives out of 40 total |
| AC-8 | PASS | Precision: 1.00, Recall: 1.00, F1: 1.00 |

### Coverage

| Check | Status | Message |
|-------|--------|---------|
| CV-1 | PASS | 118 files, 22 issues, 3 categories |
| CV-2 | PASS | Skipped: python not present in ground truth |
| CV-3 | PASS | Skipped: javascript not present in ground truth |
| CV-4 | PASS | Skipped: java not present in ground truth |
| CV-5 | PASS | Skipped: go not present in ground truth |
| CV-6 | PASS | Skipped: cpp not present in ground truth |
| CV-7 | PASS | Analyzed 3 of 1 expected languages |
| CV-8 | PASS | Covered 4/15 security categories |

### Edge Cases

| Check | Status | Message |
|-------|--------|---------|
| EC-1 | PASS | Found 0 empty files, handled correctly |
| EC-2 | PASS | Analyzed 9 large files (>1000 lines) |
| EC-3 | PASS | Found 4 files with multiple issue types |
| EC-4 | PASS | Nested code structures handled |
| EC-5 | PASS | Comments handled correctly |
| EC-6 | PASS | String literals handled correctly |
| EC-7 | PASS | Minified code handled |
| EC-8 | PASS | Encoding variations handled gracefully |

### Integration Fit

| Check | Status | Message |
|-------|--------|---------|
| IF-1 | PASS | 124/124 files have relative paths |

### Output Quality

| Check | Status | Message |
|-------|--------|---------|
| OQ-1 | PASS | Schema validation passed |

### Performance

| Check | Status | Message |
|-------|--------|---------|
| PF-1 | PASS | Completed in 4.3s (target: <120s) |
| PF-2 | PASS | Throughput: 28.7 files/second |
| PF-3 | PASS | Throughput: 11170 lines/second (waived) |
| PF-4 | PASS | Output completeness: 100% |

## Decision Thresholds

| Decision | Criteria |
|----------|----------|
| STRONG_PASS | >= 4.0 (80%+) |
| PASS | >= 3.5 (70%+) |
| WEAK_PASS | >= 3.0 (60%+) |
| FAIL | < 3.0 (below 60%) |

---

*Analysis: `/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/outputs/7a9c794e-4b86-4a18-820e-7b89459c9932/output.json`*
*Ground Truth: `/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/evaluation/ground-truth`*