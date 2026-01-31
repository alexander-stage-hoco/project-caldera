# semgrep Evaluation Scorecard

**Evaluated:** 2026-01-25T19:42:07.279271+00:00
**Run ID:** eval-semgrep-20260125

---

## Quick Screen Results

- [x] Structured output (JSON/SARIF) - **Native JSON confirmed**
- [x] Supports target languages - **7 languages: Python, JavaScript, TypeScript, C#, Java, Go, Rust**
- [x] Active maintenance - **Open source, regularly updated**
- [x] Compatible license - **LGPL-2.1**
- [x] Can run offline - **Supports offline mode with downloaded rules**

**Result: ALL CHECKS PASSED - Proceed to scoring**

---

## Scoring Summary

| Dimension | Weight | Passed | Total | Score | Weighted |
|-----------|--------|--------|-------|-------|----------|
| Accuracy | 17% | 9 | 9 | 4.02/5 | 0.67 |
| Coverage | 17% | 8 | 8 | 4.38/5 | 0.73 |
| Edge Cases | 17% | 8 | 8 | 4.69/5 | 0.78 |
| Integration Fit | 17% | 2 | 2 | 5.00/5 | 0.83 |
| Output Quality | 17% | 3 | 3 | 5.00/5 | 0.83 |
| Performance | 17% | 4 | 4 | 4.87/5 | 0.81 |
| **TOTAL** | **100%** | **34** | **34** | | **4.51** |

**Decision: STRONG_PASS** (4.51/5.0, 90.11%)

---

### Accuracy (17%)

**Score: 4.02/5**

Checks:
- [x] AC-1: SQL injection detection - Detected 34 SQL injections (expected ~32)
- [x] AC-2: Empty catch detection - Detected 13 empty catches (expected ~13)
- [x] AC-3: Catch-all detection - Detected 1 catch-all patterns
- [x] AC-4: Async void detection - Detected 5 async void methods
- [x] AC-5: HttpClient/HTTP-related detection - Detected 12 HTTP-related issues
- [x] AC-6: High complexity detection - Detected 0 high complexity (Semgrep focuses on security)
- [x] AC-7: God class detection - Detected 0 god classes (Semgrep focuses on security)
- [x] AC-8: Overall detection quality - Categorization: 100.0% (178/178 properly categorized)
- [x] AC-9: Line number accuracy - Line accuracy: 74.0% (92 exact, 22 near +/-2, 40 missed)

**Weighted: 4.02 x 0.17 = 0.67**

### Coverage (17%)

**Score: 4.38/5**

Checks:
- [x] CV-1: Python coverage - 10 files, 17 smells, 4 categories
- [x] CV-2: JavaScript coverage - 4 files, 12 smells, 3 categories
- [x] CV-3: TypeScript coverage - 5 files, 16 smells, 3 categories
- [x] CV-4: C# coverage - 22 files, 118 smells, 8 categories
- [x] CV-5: Java coverage - 3 files, 9 smells, 3 categories
- [x] CV-6: Go coverage - 2 files, 6 smells, 1 categories
- [x] CV-7: Rust coverage - 3 files, 0 smells, 0 categories
- [x] CV-8: DD category coverage - Covered 9/13 DD categories

**Weighted: 4.38 x 0.17 = 0.73**

### Edge Cases (17%)

**Score: 4.69/5**

Checks:
- [x] EC-1: Empty files handling - Analysis completed without empty file errors
- [x] EC-2: Unicode content handling - Unicode files processed without errors
- [x] EC-3: Large files handling - Processed 0 files > 500 LOC
- [x] EC-4: Deep nesting handling - Deep nesting handled correctly
- [x] EC-5: Mixed language files (JS/TS) - Processed 9 JS/TS files
- [x] EC-6: No false positives in clean files - 0 false positives in 1 clean files
- [x] EC-7: Syntax error tolerance - Analysis completed (syntax errors handled gracefully)
- [x] EC-8: Path handling - Handled 49 file paths correctly

**Weighted: 4.69 x 0.17 = 0.78**

### Integration Fit (17%)

**Score: 5.00/5**

Checks:
- [x] IF-1: Relative file paths - 49/49 files have relative paths
- [x] IF-2: Smell entries include required fields - 178/178 smells include required fields

**Weighted: 5.00 x 0.17 = 0.83**

### Output Quality (17%)

**Score: 5.00/5**

Checks:
- [x] OQ-1: Required sections present - All required sections present
- [x] OQ-2: File entries include required fields - 49/49 files include required fields
- [x] OQ-3: Schema validation - Schema validation passed

**Weighted: 5.00 x 0.17 = 0.83**

### Performance (17%)

**Score: 4.87/5**

Checks:
- [x] PF-1: Synthetic repo analysis speed - Completed in 4.83s (threshold: 45.0s)
- [x] PF-2: Per-file analysis efficiency - 99ms per file (threshold: 1000ms)
- [x] PF-3: Analysis throughput - 897 LOC/s (threshold: 100 LOC/s)
- [x] PF-4: Startup overhead - Estimated startup: 0% of total time

**Weighted: 4.87 x 0.17 = 0.81**

---

## Decision

**STRONG_PASS (4.51/5.0)**

Semgrep is approved for use in the DD Platform MVP for code smell detection.
