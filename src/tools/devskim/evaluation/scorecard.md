# DevSkim Evaluation Scorecard

**Generated:** 2026-02-06T09:05:49.221856+00:00
**Decision:** STRONG_PASS
**Score:** 92.57%

## Summary

| Metric | Value |
|--------|-------|
| Total Checks | 30 |
| Passed | 30 |
| Failed | 0 |
| Raw Score | 0.926 |
| Normalized Score | 4.63/5.0 |

## Dimensions

| Dimension | Checks | Passed | Score |
|-----------|--------|--------|-------|
| Accuracy | 8 | 8/8 | 98.4% |
| Coverage | 8 | 8/8 | 100.0% |
| Edge Cases | 8 | 8/8 | 86.2% |
| Integration Fit | 1 | 1/1 | 100.0% |
| Output Quality | 1 | 1/1 | 100.0% |
| Performance | 4 | 4/4 | 75.0% |

## Detailed Results

### Accuracy

| Check | Status | Message |
|-------|--------|---------|
| AC-1 | PASS | Skipped: No SQL injection expectations in ground t... |
| AC-2 | PASS | Skipped: No hardcoded secret expectations in groun... |
| AC-3 | PASS | Found 10 insecure crypto issues (expected >= 10) |
| AC-4 | PASS | Skipped: No path traversal expectations in ground ... |
| AC-5 | PASS | Skipped: No XSS expectations in ground truth |
| AC-6 | PASS | Found 2 deserialization issues |
| AC-7 | PASS | Found 0 potential false positives out of 13 total |
| AC-8 | PASS | Precision: 1.00, Recall: 0.77, F1: 0.87 |

### Coverage

| Check | Status | Message |
|-------|--------|---------|
| CV-1 | PASS | 10 files, 13 issues, 3 categories |
| CV-2 | PASS | Skipped: python not present in ground truth |
| CV-3 | PASS | Skipped: javascript not present in ground truth |
| CV-4 | PASS | Skipped: java not present in ground truth |
| CV-5 | PASS | Skipped: go not present in ground truth |
| CV-6 | PASS | Skipped: cpp not present in ground truth |
| CV-7 | PASS | Analyzed 1 of 1 expected languages |
| CV-8 | PASS | Covered 3/3 security categories |

### Edge Cases

| Check | Status | Message |
|-------|--------|---------|
| EC-1 | PASS | Found 7 empty files, handled correctly |
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
| IF-1 | PASS | 10/10 files have relative paths |

### Output Quality

| Check | Status | Message |
|-------|--------|---------|
| OQ-1 | PASS | Schema validation passed |

### Performance

| Check | Status | Message |
|-------|--------|---------|
| PF-1 | PASS | Completed in 1.0s (target: <30s) |
| PF-2 | PASS | Throughput: 9.7 files/second |
| PF-3 | PASS | Throughput: 256 lines/second (waived) |
| PF-4 | PASS | Output completeness: 100% |

## Decision Thresholds

| Decision | Criteria |
|----------|----------|
| STRONG_PASS | >= 4.0 (80%+) |
| PASS | >= 3.5 (70%+) |
| WEAK_PASS | >= 3.0 (60%+) |
| FAIL | < 3.0 (below 60%) |

---

*Analysis: `/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/outputs/68806B0D-7043-43F7-B8D6-1209BB941741/output.json`*
*Ground Truth: `/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/evaluation/ground-truth`*