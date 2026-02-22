# scc Evaluation Scorecard

**Evaluated:** 2026-01-25T10:18:37.196661+00:00
**Run ID:** eval-20260125-101837

**Related:** Combined scorecard at `evaluation/results/combined_scorecard.md` (LLM run: `llm-eval-20260125-104034`)

---

## Quick Screen Results

- [x] Structured output (JSON/SARIF/CSV) - **Native JSON confirmed**
- [x] Supports target languages - **All 7 languages detected**
- [x] Active maintenance - **6.4K+ GitHub stars, regular releases**
- [x] Compatible license - **MIT/Unlicense**
- [x] Can run offline - **Single binary, no network required**

**Result: ALL CHECKS PASSED - Proceed to scoring**

---

## Scoring Summary

| Dimension | Weight | Passed | Total | Score | Weighted |
|-----------|--------|--------|-------|-------|----------|
| Output Quality | 20% | 8 | 8 | 5/5 | 1.00 |
| Integration Fit | 15% | 6 | 6 | 5/5 | 0.75 |
| Reliability | 10% | 8 | 8 | 5/5 | 0.50 |
| Performance | 10% | 4 | 4 | 5/5 | 0.50 |
| Installation | 5% | 4 | 4 | 5/5 | 0.25 |
| Coverage | 5% | 9 | 9 | 5/5 | 0.25 |
| License | 5% | 3 | 3 | 5/5 | 0.25 |
| Per File | 10% | 6 | 6 | 5/5 | 0.50 |
| Directory Analysis | 10% | 10 | 12 | 5/5 | 0.50 |
| Cocomo | 10% | 3 | 3 | 5/5 | 0.50 |
| **TOTAL** | **100%** | | | | **5.00** |

**Decision: STRONG_PASS** (5.00/5.0)


---

### Output Quality (20%)

**Score: 5/5**

Checks:
- [x] JSON Valid: Valid JSON with 7 entries
- [x] Array Structure: Root is array
- [x] Required Fields: All required fields present
- [x] Numeric Types: All numeric fields valid
- [x] Non-Empty Output: Output has 7 entries
- [x] Bytes Present: All entries have Bytes
- [x] Complexity Present: All entries have Complexity
- [x] No Parse Errors: No errors

**Weighted: 5 x 0.20 = 1.00**

### Integration Fit (15%)

**Score: 5/5**

Checks:
- [x] Output Generated: output.json present
- [x] Schema Valid: Output validates against schema
- [x] Required Fields Present: All required fields present
- [x] No Data Loss: Totals match
- [x] Metadata Complete: Metadata complete
- [x] Relative Paths: All paths are repo-relative

**Weighted: 5 x 0.15 = 0.75**

### Reliability (10%)

**Score: 5/5**

Checks:
- [x] Empty File Handled: Found 7/7 empty files, all 0 LOC: True
- [x] Comments Only Handled: Found 7 files, Code=0: True, Comment>0: True
- [x] Single Line Handled: Found 7 files, Code=1: True
- [x] Unicode Handled: Found 7 unicode files, all parsed: True
- [x] Deep Nesting Handled: Found 7 files, complexity reported: True
- [x] Deterministic Output: 3 runs identical: True
- [x] All Files Detected: Found 63/63 files
- [x] No Crashes: Exit code: 0

**Weighted: 5 x 0.10 = 0.50**

### Performance (10%)

**Score: 5/5**

Checks:
- [x] Fast Execution: Execution time: 6ms (threshold: 5000ms)
- [x] Very Fast Execution: Execution time: 6ms (threshold: 1000ms)
- [x] Sub-Second: Execution time: 5ms (threshold: 500ms)
- [x] Memory Reasonable: Peak memory: 21.5MB (threshold: 100MB)

**Weighted: 5 x 0.10 = 0.50**

### Installation (5%)

**Score: 5/5**

Checks:
- [x] Binary Exists: Binary exists: True, executable: True
- [x] Version Check: Version output: scc version 3.6.0
- [x] Help Available: Help available: True
- [x] No Dependencies: Runs without external dependencies

**Weighted: 5 x 0.05 = 0.25**

### Coverage (5%)

**Score: 5/5**

Checks:
- [x] Python Detected: Python detected: True
- [x] C# Detected: C# detected: True
- [x] JavaScript Detected: JavaScript detected: True
- [x] TypeScript Detected: TypeScript detected: True
- [x] Go Detected: Go detected: True
- [x] Rust Detected: Rust detected: True
- [x] Java Detected: Java detected: True
- [x] File Counts Match: All file counts match
- [x] LOC Within Range: Total LOC: 5885 (expected 4500-10000)

**Weighted: 5 x 0.05 = 0.25**

### License (5%)

**Score: 5/5**

Checks:
- [x] MIT License: scc is dual-licensed under MIT and Unlicense
- [x] Open Source: scc source available on GitHub (6.4K+ stars)
- [x] No Usage Fees: scc is free for all use (MIT/Unlicense)

**Weighted: 5 x 0.05 = 0.25**

### Per File (10%)

**Score: 5/5**

Checks:
- [x] Per-File JSON Valid: Valid JSON with 7 language entries
- [x] Files Have Location: 63/63 files have Location field
- [x] Files Have Complexity: 63/63 files have valid Complexity
- [x] Files Have ULOC: 63/63 files have Uloc field
- [x] Minified Detection: Minified field present: 63/63, flagged: 0
- [x] Generated Detection: Generated field present: 63/63, flagged: 0

**Weighted: 5 x 0.10 = 0.50**

### Directory Analysis (10%)

**Score: 5/5**

Checks:
- [x] Directory Stats Complete: 23/23 directories have complete stats
- [x] Distribution Stats Valid (22 fields): 16/16 distributions have all 22 fields
- [x] Structural Metrics Valid: 23/23 directories have valid structural metrics
- [x] File Count Matches: Sum of direct.file_count (63), root files (63), total (63)
- [x] Recursive Includes Direct: 23/23 directories have recursive >= direct
- [x] Inequality Metrics Valid: 16/16 distributions have valid inequality metrics
- [x] File Classification Counts: Classification sum (63) == total_files (63)
- [ ] Per-Language Consistency: Language LOC sum (0) != total_loc (5885)
- [x] COCOMO Preset Ordering: COCOMO presets valid
- [x] P99 Monotonicity: 16/16 distributions have p95 <= p99 <= max
- [x] Summary Structure Complete: 7/7 summary sections present
- [ ] File Entry Fields Complete: 0/63 files have all 22 fields

**Weighted: 5 x 0.10 = 0.50**

### Cocomo (10%)

**Score: 5/5**

Checks:
- [x] COCOMO Output Present: Cost: True, Schedule: True, People: True
- [x] Custom Params Applied: Default: $173,712, Embedded: $339,924
- [x] Preset Values Match: Cost: $524,141 (OK), Schedule: 7.4mo (OK), People: 3.0 (OK)

**Weighted: 5 x 0.10 = 0.50**

---

## Decision

**STRONG_PASS (5.00/5.0)**

scc is approved for use in the DD Platform MVP.
