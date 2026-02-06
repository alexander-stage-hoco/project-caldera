# DevSkim Evaluation Scorecard

**Generated:** 2026-02-06T07:11:54.468494+00:00
**Decision:** WEAK_PASS
**Score:** 67.33%

## Summary

| Metric | Value |
|--------|-------|
| Total Checks | 30 |
| Passed | 21 |
| Failed | 9 |
| Raw Score | 0.673 |
| Normalized Score | 3.37/5.0 |

## Dimensions

| Dimension | Checks | Passed | Score |
|-----------|--------|--------|-------|
| Accuracy | 8 | 5/8 | 62.4% |
| Coverage | 8 | 5/8 | 62.4% |
| Edge Cases | 8 | 8/8 | 92.4% |
| Integration Fit | 1 | 1/1 | 100.0% |
| Output Quality | 1 | 0/1 | 0.0% |
| Performance | 4 | 2/4 | 45.0% |

## Detailed Results

### Accuracy

| Check | Status | Message |
|-------|--------|---------|
| AC-1 | PASS | Skipped: No SQL injection expectations in ground t... |
| AC-2 | PASS | Skipped: No hardcoded secret expectations in groun... |
| AC-3 | FAIL | Found 0 insecure crypto issues (expected >= 10) |
| AC-4 | PASS | Skipped: No path traversal expectations in ground ... |
| AC-5 | PASS | Skipped: No XSS expectations in ground truth |
| AC-6 | FAIL | Found 0 deserialization issues |
| AC-7 | PASS | No findings to check for false positives |
| AC-8 | FAIL | Precision: 1.00, Recall: 0.00, F1: 0.00 |

### Coverage

| Check | Status | Message |
|-------|--------|---------|
| CV-1 | FAIL | 0 files, 0 issues, 0 categories |
| CV-2 | PASS | Skipped: python not present in ground truth |
| CV-3 | PASS | Skipped: javascript not present in ground truth |
| CV-4 | PASS | Skipped: java not present in ground truth |
| CV-5 | PASS | Skipped: go not present in ground truth |
| CV-6 | PASS | Skipped: cpp not present in ground truth |
| CV-7 | FAIL | Analyzed 0 of 1 expected languages |
| CV-8 | FAIL | Covered 0/3 security categories |

### Edge Cases

| Check | Status | Message |
|-------|--------|---------|
| EC-1 | PASS | Found 0 empty files, handled correctly |
| EC-2 | PASS | Analyzed 0 large files (>1000 lines) |
| EC-3 | PASS | Found 0 files with multiple issue types |
| EC-4 | PASS | Nested code structures handled |
| EC-5 | PASS | Comments handled correctly |
| EC-6 | PASS | String literals handled correctly |
| EC-7 | PASS | Minified code handled |
| EC-8 | PASS | Encoding variations handled gracefully |

### Integration Fit

| Check | Status | Message |
|-------|--------|---------|
| IF-1 | PASS | 0/0 files have relative paths |

### Output Quality

| Check | Status | Message |
|-------|--------|---------|
| OQ-1 | FAIL | Missing root wrapper for schema validation |

### Performance

| Check | Status | Message |
|-------|--------|---------|
| PF-1 | PASS | Completed in 0.0s (target: <30s) |
| PF-2 | FAIL | Throughput: 0.0 files/second |
| PF-3 | PASS | Throughput: 0 lines/second (waived) |
| PF-4 | FAIL | Output completeness: 20% |

## Decision Thresholds

| Decision | Criteria |
|----------|----------|
| STRONG_PASS | >= 4.0 (80%+) |
| PASS | >= 3.5 (70%+) |
| WEAK_PASS | >= 3.0 (60%+) |
| FAIL | < 3.0 (below 60%) |

---

*Analysis: `/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/outputs/233da6a1-8d93-4dfc-90b8-6886fb622001/output.json`*
*Ground Truth: `/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/evaluation/ground-truth`*