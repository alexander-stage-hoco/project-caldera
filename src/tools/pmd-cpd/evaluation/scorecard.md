# PMD CPD Evaluation Scorecard

**Generated:** 2026-02-13T12:51:33.788368
**Decision:** STRONG_PASS
**Score:** 89.03%

## Summary

| Metric | Value |
|--------|-------|
| Total Checks | 28 |
| Passed | 27 |
| Failed | 1 |
| Raw Score | 0.890 |
| Normalized Score | 4.45/5.0 |

## Dimensions

| Dimension | Checks | Passed | Score |
|-----------|--------|--------|-------|
| Accuracy | 8 | 8/8 | 77.0% |
| Coverage | 8 | 8/8 | 100.0% |
| Edge Cases | 8 | 8/8 | 97.2% |
| Performance | 4 | 3/4 | 75.0% |

## Detailed Results

### Accuracy

| Check | Status | Message |
|-------|--------|---------|
| AC-1 | PASS | Detected 6/7 heavy duplication files |
| AC-2 | PASS | 26/35 files have clone counts in expected range |
| AC-3 | PASS | 14/20 files have duplication % in expected range |
| AC-4 | PASS | 5/5 clean files correctly identified (no false pos... |
| AC-5 | PASS | Detected 6/7 cross-file duplication pairs |
| AC-6 | PASS | Semantic mode not enabled (--ignore-identifiers no... |
| AC-7 | PASS | Semantic mode not enabled (--ignore-literals not u... |
| AC-8 | PASS | 39/39 clones have valid line counts |

### Coverage

| Check | Status | Message |
|-------|--------|---------|
| CV-1 | PASS | Analyzed 7/7 python files from ground truth |
| CV-2 | PASS | Analyzed 7/7 javascript files from ground truth |
| CV-3 | PASS | Analyzed 7/7 typescript files from ground truth |
| CV-4 | PASS | Analyzed 7/7 csharp files from ground truth |
| CV-5 | PASS | Analyzed 7/7 java files from ground truth |
| CV-6 | PASS | Analyzed 7/7 go files from ground truth |
| CV-7 | PASS | Analyzed 7/7 rust files from ground truth |
| CV-8 | PASS | Detected 7/7 expected languages |

### Edge Cases

| Check | Status | Message |
|-------|--------|---------|
| EC-1 | PASS | Empty files handled gracefully |
| EC-2 | PASS | Single-line files handled correctly |
| EC-3 | PASS | Analysis completed in 0.0s, 0 large files processe... |
| EC-4 | PASS | Unicode content handled correctly |
| EC-5 | PASS | Line endings handled correctly |
| EC-6 | PASS | Nested code structures analyzed (39 clones found) |
| EC-7 | PASS | File paths handled correctly (49 files processed) |
| EC-8 | PASS | Overall duplication: 23.0% (39 clones) |

### Performance

| Check | Status | Message |
|-------|--------|---------|
| PF-1 | PASS | Excellent: Analysis completed in 0.0s |
| PF-2 | PASS | No files to measure throughput |
| PF-3 | PASS | Efficient clone representation |
| PF-4 | FAIL | Missing metadata for incremental: repo_path, times... |

## Decision Thresholds

| Decision | Criteria |
|----------|----------|
| STRONG_PASS | >= 4.0 (80%+) |
| PASS | >= 3.5 (70%+) |
| WEAK_PASS | >= 3.0 (60%+) |
| FAIL | < 3.0 (below 60%) |

---

*Analysis: `outputs/cpd-test-run/output.json`*
*Ground Truth: `evaluation/ground-truth`*