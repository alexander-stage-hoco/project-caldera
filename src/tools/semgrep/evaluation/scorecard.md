# Semgrep Evaluation Scorecard

**Generated:** 2026-02-06T09:28:46.245685+00:00
**Decision:** STRONG_PASS
**Score:** 90.0%

## Summary

| Metric | Value |
|--------|-------|
| Total Checks | 34 |
| Passed | 33 |
| Failed | 1 |
| Raw Score | 0.900 |
| Normalized Score | 4.50/5.0 |

## Dimensions

| Dimension | Checks | Passed | Score |
|-----------|--------|--------|-------|
| Accuracy | 9 | 8/9 | 78.8% |
| Coverage | 8 | 8/8 | 87.6% |
| Edge Cases | 8 | 8/8 | 93.8% |
| Integration Fit | 2 | 2/2 | 100.0% |
| Output Quality | 3 | 3/3 | 100.0% |
| Performance | 4 | 4/4 | 100.0% |

## Detailed Results

### Accuracy

| Check | Status | Message |
|-------|--------|---------|
| AC-1 | PASS | Detected 38 SQL injections (expected ~32) |
| AC-2 | PASS | Detected 13 empty catches (expected ~13) |
| AC-3 | PASS | Detected 1 catch-all patterns |
| AC-4 | PASS | Detected 5 async void methods |
| AC-5 | PASS | Detected 12 HTTP-related issues |
| AC-6 | PASS | Detected 0 high complexity (Semgrep focuses on sec... |
| AC-7 | PASS | Detected 0 god classes (Semgrep focuses on securit... |
| AC-8 | PASS | Categorization: 100.0% (193/193 properly categoriz... |
| AC-9 | FAIL | Line accuracy: 60.0% (110 exact, 10 near ±2, 80 mi... |

### Coverage

| Check | Status | Message |
|-------|--------|---------|
| CV-1 | PASS | 12 files, 17 smells, 4 categories |
| CV-2 | PASS | 6 files, 12 smells, 3 categories |
| CV-3 | PASS | 5 files, 16 smells, 3 categories |
| CV-4 | PASS | 23 files, 118 smells, 8 categories |
| CV-5 | PASS | 5 files, 22 smells, 3 categories |
| CV-6 | PASS | 4 files, 8 smells, 1 categories |
| CV-7 | PASS | 3 files, 0 smells, 0 categories |
| CV-8 | PASS | Covered 9/13 DD categories |

### Edge Cases

| Check | Status | Message |
|-------|--------|---------|
| EC-1 | PASS | Analysis completed without empty file errors |
| EC-2 | PASS | Unicode files processed without errors |
| EC-3 | PASS | Processed 0 files > 500 LOC |
| EC-4 | PASS | Deep nesting handled correctly |
| EC-5 | PASS | Processed 11 JS/TS files |
| EC-6 | PASS | 0 false positives in 1 clean files |
| EC-7 | PASS | Analysis completed (syntax errors handled graceful... |
| EC-8 | PASS | Handled 58 file paths correctly |

### Integration Fit

| Check | Status | Message |
|-------|--------|---------|
| IF-1 | PASS | 58/58 files have relative paths |
| IF-2 | PASS | 193/193 smells include required fields |

### Output Quality

| Check | Status | Message |
|-------|--------|---------|
| OQ-1 | PASS | All required sections present |
| OQ-2 | PASS | 58/58 files include required fields |
| OQ-3 | PASS | Schema validation passed |

### Performance

| Check | Status | Message |
|-------|--------|---------|
| PF-1 | PASS | Completed in 0.00s (threshold: 45.0s) |
| PF-2 | PASS | 0ms per file (threshold: 1000ms) |
| PF-3 | PASS | 5370000 LOC/s (threshold: 100 LOC/s) |
| PF-4 | PASS | Estimated startup: 0% of total time |

## Decision Thresholds

| Decision | Criteria |
|----------|----------|
| STRONG_PASS | >= 4.0 (80%+) |
| PASS | >= 3.5 (70%+) |
| WEAK_PASS | >= 3.0 (60%+) |
| FAIL | < 3.0 (below 60%) |

---

*Analysis: `outputs/04B80681-E8E3-4DC8-961B-4BAA2F09C001/output.json`*
*Ground Truth: `evaluation/ground-truth`*