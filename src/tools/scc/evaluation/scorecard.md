# scc Evaluation Scorecard

## Summary

| Metric | Value |
|--------|-------|
| **Overall Score** | 5.00 / 5.0 |
| **Decision** | STRONG_PASS |
| **Total Checks** | 63 |
| **Passed** | 61 |
| **Failed** | 2 |
| **Raw Score** | 100.0% |

## Programmatic Evaluation Results

### D1 — Output Quality (weight: 0.20, 8 checks)

**Score:** 5 / 5 | **Weighted:** 1.00

| Check | Status | Notes |
|-------|--------|-------|
| OQ-1 | PASS | JSON Valid — Valid JSON with 7 entries |
| OQ-2 | PASS | Array Structure — Root is array |
| OQ-3 | PASS | Required Fields — All required fields present |
| OQ-4 | PASS | Numeric Types — All numeric fields valid |
| OQ-5 | PASS | Non-Empty Output — Output has 7 entries |
| OQ-6 | PASS | Bytes Present — All entries have Bytes |
| OQ-7 | PASS | Complexity Present — All entries have Complexity |
| OQ-8 | PASS | No Parse Errors — No errors |

### D2 — Integration Fit (weight: 0.15, 6 checks)

**Score:** 5 / 5 | **Weighted:** 0.75

| Check | Status | Notes |
|-------|--------|-------|
| IF-1 | PASS | Output Generated — output.json present |
| IF-2 | PASS | Schema Valid — Output validates against schema |
| IF-3 | PASS | Required Fields Present — All required fields present |
| IF-4 | PASS | No Data Loss — Totals match |
| IF-5 | PASS | Metadata Complete — Metadata complete |
| IF-6 | PASS | Relative Paths — All paths are repo-relative |

### D3 — Reliability (weight: 0.10, 8 checks)

**Score:** 5 / 5 | **Weighted:** 0.50

| Check | Status | Notes |
|-------|--------|-------|
| RL-1 | PASS | Empty File Handled |
| RL-2 | PASS | Comments Only Handled |
| RL-3 | PASS | Single Line Handled |
| RL-4 | PASS | Unicode Handled |
| RL-5 | PASS | Deep Nesting Handled |
| RL-6 | PASS | Deterministic Output — 3 runs identical |
| RL-7 | PASS | All Files Detected — Found 63/63 files |
| RL-8 | PASS | No Crashes — Exit code: 0 |

### D4 — Performance (weight: 0.10, 4 checks)

**Score:** 5 / 5 | **Weighted:** 0.50

| Check | Status | Notes |
|-------|--------|-------|
| PF-1 | PASS | Fast Execution — 6ms (threshold: 5000ms) |
| PF-2 | PASS | Very Fast Execution — 6ms (threshold: 1000ms) |
| PF-3 | PASS | Sub-Second — 5ms (threshold: 500ms) |
| PF-4 | PASS | Memory Reasonable — 21.5MB (threshold: 100MB) |

### D5 — Installation (weight: 0.05, 4 checks)

**Score:** 5 / 5 | **Weighted:** 0.25

| Check | Status | Notes |
|-------|--------|-------|
| IN-1 | PASS | Binary Exists — exists and executable |
| IN-2 | PASS | Version Check — scc version 3.6.0 |
| IN-3 | PASS | Help Available |
| IN-4 | PASS | No Dependencies — Runs without external dependencies |

### D6 — Coverage (weight: 0.05, 9 checks)

**Score:** 5 / 5 | **Weighted:** 0.25

| Check | Status | Notes |
|-------|--------|-------|
| CV-1 | PASS | Python Detected |
| CV-2 | PASS | C# Detected |
| CV-3 | PASS | JavaScript Detected |
| CV-4 | PASS | TypeScript Detected |
| CV-5 | PASS | Go Detected |
| CV-6 | PASS | Rust Detected |
| CV-7 | PASS | Java Detected |
| CV-8 | PASS | File Counts Match — All file counts match |
| CV-9 | PASS | LOC Within Range — Total LOC: 5885 |

### D7 — License (weight: 0.05, 3 checks)

**Score:** 5 / 5 | **Weighted:** 0.25

| Check | Status | Notes |
|-------|--------|-------|
| CL-1 | PASS | MIT License — dual-licensed MIT and Unlicense |
| CL-2 | PASS | Open Source — source available on GitHub |
| CL-3 | PASS | No Usage Fees — free for all use |

### D8 — Per File (weight: 0.10, 6 checks)

**Score:** 5 / 5 | **Weighted:** 0.50

| Check | Status | Notes |
|-------|--------|-------|
| PF-1 | PASS | Per-File JSON Valid — 7 language entries |
| PF-2 | PASS | Files Have Location — 63/63 files |
| PF-3 | PASS | Files Have Complexity — 63/63 files |
| PF-4 | PASS | Files Have ULOC — 63/63 files |
| PF-5 | PASS | Minified Detection — 63/63 files |
| PF-6 | PASS | Generated Detection — 63/63 files |

### D9 — Directory Analysis (weight: 0.10, 12 checks)

**Score:** 5 / 5 | **Weighted:** 0.50

| Check | Status | Notes |
|-------|--------|-------|
| DA-1 | PASS | Directory Stats Complete — 23/23 directories |
| DA-2 | PASS | Distribution Stats Valid — 16/16 distributions |
| DA-3 | PASS | Structural Metrics Valid — 23/23 directories |
| DA-4 | PASS | File Count Matches — 63 files |
| DA-5 | PASS | Recursive Includes Direct — 23/23 directories |
| DA-6 | PASS | Inequality Metrics Valid — 16/16 distributions |
| DA-7 | PASS | File Classification Counts — 63 files |
| DA-8 | FAIL | Per-Language Consistency — Language LOC sum (0) != total_loc (5885) |
| DA-9 | PASS | COCOMO Preset Ordering |
| DA-10 | PASS | P99 Monotonicity — 16/16 distributions |
| DA-11 | PASS | Summary Structure Complete — 7/7 sections |
| DA-12 | FAIL | File Entry Fields Complete — 0/63 files have all 22 fields |

### D10 — Cocomo (weight: 0.10, 3 checks)

**Score:** 5 / 5 | **Weighted:** 0.50

| Check | Status | Notes |
|-------|--------|-------|
| CO-1 | PASS | COCOMO Output Present — Cost, Schedule, People |
| CO-2 | PASS | Custom Params Applied — Default: $173,712, Embedded: $339,924 |
| CO-3 | PASS | Preset Values Match — Cost: $524,141, Schedule: 7.4mo, People: 3.0 |

## Decision Thresholds

| Decision | Combined Score | Interpretation |
|----------|----------------|----------------|
| STRONG_PASS | >= 4.0 | 80%+ |
| PASS | >= 3.5 | 70%+ |
| WEAK_PASS | >= 3.0 | 60%+ |
| FAIL | < 3.0 | below 60% |

---

*Generated from `scorecard.json`. Run `make evaluate` to refresh.*
