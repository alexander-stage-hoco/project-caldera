# scc PoC Evaluation Strategy

This document describes the evaluation framework for the scc (Sloc, Cloc, and Code) tool PoC, including the complete check catalog, scoring methodology, weight allocation, and decision thresholds.

## Overview

The evaluation framework assesses scc's fitness for integration into the DD Platform MVP across 10 dimensions with 63 individual checks.

### Version History

| Version | Dimensions | Checks | Core Weight | Extended Weight |
|---------|------------|--------|-------------|-----------------|
| v1.0 (Original) | 7 | 42 | 100% | - |
| v2.0 (Extended) | 10 | 63 | 70% | 30% |

### Key Changes in v2.0

1. **New Dimensions Added:**
   - Per-File Analysis (PF-1 to PF-6) - 10% weight
   - Directory Analysis (DA-1 to DA-12) - 10% weight
   - COCOMO Estimation (CO-1 to CO-3) - 10% weight

2. **Weight Rebalancing:**
   - Core dimensions reduced from 100% to 70%
   - Extended dimensions added at 30%
   - Maintains same relative proportions within core dimensions

---

## Dimension Summary

| Dimension | Code | Checks | Weight | Category |
|-----------|------|--------|--------|----------|
| Output Quality | OQ | 8 | 20% | Core |
| Integration Fit | IF | 6 | 15% | Core |
| Reliability | RL | 8 | 10% | Core |
| Performance | PF | 4 | 10% | Core |
| Installation | IN | 4 | 5% | Core |
| Coverage | CV | 9 | 5% | Core |
| License | CL | 3 | 5% | Core |
| Per-File | PF | 6 | 10% | Extended |
| Directory Analysis | DA | 12 | 10% | Extended |
| COCOMO | CO | 3 | 10% | Extended |
| **Total** | | **63** | **100%** | |

---

## Complete Check Catalog

### 1. Output Quality (OQ) - 20% Weight

Validates the structure and completeness of scc's JSON output.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| OQ-1 | JSON Valid | Raw output parses as valid JSON | `json.loads()` succeeds |
| OQ-2 | Array Structure | Root element is JSON array | `isinstance(data, list)` |
| OQ-3 | Required Fields | All required fields present per language entry | Fields: `Name`, `Count`, `Lines`, `Code`, `Comment`, `Blank` |
| OQ-4 | Numeric Types | Numeric fields are integers >= 0 | `Count`, `Lines`, `Code`, `Comment`, `Blank` are non-negative integers |
| OQ-5 | Non-Empty Output | Output array has >= 1 entry | `len(data) >= 1` |
| OQ-6 | Bytes Present | All entries have `Bytes` field | Field present in all entries |
| OQ-7 | Complexity Present | All entries have `Complexity` field | Field present in all entries |
| OQ-8 | No Parse Errors | Exit code 0, no errors in stderr | `exit_code == 0` and no "error"/"panic" in stderr |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 8 | 5 |
| 7 | 4 |
| 5-6 | 3 |
| 3-4 | 2 |
| 0-2 | 1 |

---

### 2. Integration Fit (IF) - 15% Weight

Validates transformation pipeline and schema compliance.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| IF-1 | Transform Success | transform.py runs without error | Exit code 0 |
| IF-2 | Schema Valid | Output validates against JSON schema | jsonschema validation passes |
| IF-3 | All Fields Mapped | All scc fields present in transformed output | Fields: `language`, `files`, `lines_total`, `lines_code`, `lines_comment`, `lines_blank`, `bytes`, `complexity` |
| IF-4 | No Data Loss | Totals in transformed output match raw totals | `files` and `loc` counts match |
| IF-5 | Provenance Complete | Provenance has required fields | Fields: `tool`, `timestamp` |
| IF-6 | Evidence IDs Unique | All evidence_id values are unique | No duplicate IDs |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 6 | 5 |
| 5 | 4 |
| 4 | 3 |
| 2-3 | 2 |
| 0-1 | 1 |

---

### 3. Reliability (RL) - 10% Weight

Validates handling of edge cases and output consistency.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| RL-1 | Empty File Handled | Empty files counted with LOC=0 | 7 empty files found, all with `Code=0` |
| RL-2 | Comments Only Handled | Comments-only files: Code=0, Comment>0 | 7 files with `Code=0` and `Comment>0` |
| RL-3 | Single Line Handled | Single-line files: Code=1 | 7 files with `Code=1` |
| RL-4 | Unicode Handled | Unicode files parse successfully | 7 files with `Lines>0` |
| RL-5 | Deep Nesting Handled | Deep nesting files report complexity | 7 files with `Complexity>0` |
| RL-6 | Deterministic Output | 3 consecutive runs produce identical output | All MD5 hashes match |
| RL-7 | All Files Detected | All 63 files are detected | `file_count >= 63` |
| RL-8 | No Crashes | scc exits with code 0 | Exit code 0 |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 8 | 5 |
| 7 | 4 |
| 5-6 | 3 |
| 3-4 | 2 |
| 0-2 | 1 |

---

### 4. Performance (PF) - 10% Weight

Validates execution speed and resource usage.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| PF-1 | Fast Execution | Execution time < 5 seconds | `elapsed_ms < 5000` |
| PF-2 | Very Fast Execution | Execution time < 1 second | `elapsed_ms < 1000` |
| PF-3 | Sub-Second | Execution time < 500ms | `elapsed_ms < 500` |
| PF-4 | Memory Reasonable | Peak memory < 100MB | `memory_mb < 100` |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 4 | 5 |
| 3 | 4 |
| 2 | 3 |
| 1 | 2 |
| 0 | 1 |

---

### 5. Installation (IN) - 5% Weight

Validates binary availability and standalone operation.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| IN-1 | Binary Exists | scc binary exists and is executable | File exists and has execute permission |
| IN-2 | Version Check | `--version` returns version string | Exit code 0 and output contains version info |
| IN-3 | Help Available | `--help` returns help text | Exit code 0 and output contains "usage" or "options" |
| IN-4 | No Dependencies | Runs without external runtime dependencies | No "library not found" errors |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 4 | 5 |
| 3 | 4 |
| 2 | 3 |
| 1 | 2 |
| 0 | 1 |

---

### 6. Coverage (CV) - 5% Weight

Validates language detection and file counting.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| CV-1 | Python Detected | Python language detected | "Python" in output |
| CV-2 | C# Detected | C# language detected | "C#" in output |
| CV-3 | JavaScript Detected | JavaScript language detected | "JavaScript" in output |
| CV-4 | TypeScript Detected | TypeScript language detected | "TypeScript" in output |
| CV-5 | Go Detected | Go language detected | "Go" in output |
| CV-6 | Rust Detected | Rust language detected | "Rust" in output |
| CV-7 | Java Detected | Java language detected | "Java" in output |
| CV-8 | File Counts Match | Each language shows 9 files | 9 files per language |
| CV-9 | LOC Within Range | Total LOC between 4500-10000 | `4500 <= total_loc <= 10000` |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 9 | 5 |
| 8 | 4 |
| 6-7 | 3 |
| 4-5 | 2 |
| 0-3 | 1 |

---

### 7. License (CL) - 5% Weight

Validates licensing compatibility.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| CL-1 | MIT License | Licensed under MIT or Unlicense | Dual-licensed MIT/Unlicense |
| CL-2 | Open Source | Source available on GitHub | GitHub repository exists |
| CL-3 | No Usage Fees | Free for commercial use | No payment required |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 3 | 5 |
| 2 | 4 |
| 1 | 3 |
| 0 | 2 |

---

### 8. Per-File Analysis (PF) - 10% Weight [NEW]

Validates per-file output mode with extended fields.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| PF-1 | Per-File JSON Valid | `--by-file` output is valid JSON | `json.loads()` succeeds |
| PF-2 | Files Have Location | All files have `Location` field | Field present and non-empty for all files |
| PF-3 | Files Have Complexity | All files have `Complexity >= 0` | Non-negative integer for all files |
| PF-4 | Files Have ULOC | All files have `Uloc` field with `--uloc` | Field present for all files |
| PF-5 | Minified Detection | `Minified` field present with `--min` | Field present for all files |
| PF-6 | Generated Detection | `Generated` field present with `--gen` | Field present for all files |

**Command Used:**
```bash
scc <path> --by-file --uloc --min --gen -f json
```

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 6 | 5 |
| 5 | 4 |
| 4 | 3 |
| 2-3 | 2 |
| 0-1 | 1 |

---

### 9. Directory Analysis (DA) - 10% Weight [NEW]

Validates directory-level aggregation and statistics.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| DA-1 | Directory Stats Complete | All directories have `direct`/`recursive` stats | Both objects present for all directories |
| DA-2 | Distribution Stats Valid | Distributions have all 22 required fields | All 22 distribution fields present |
| DA-3 | Structural Metrics Valid | Structural metrics consistent (is_leaf, child_count, depth) | Consistency rules pass |
| DA-4 | File Count Matches | Sum of direct files equals total files | `sum(direct_files) == total_files` |
| DA-5 | Recursive Includes Direct | `recursive.file_count >= direct.file_count` | Recursive >= direct for all directories |
| DA-6 | Inequality Metrics Valid | All inequality metrics present and in valid ranges | Gini, Theil, Hoover, Palma in expected ranges |
| DA-7 | File Classification Counts | File classification counts sum to total files | `sum(classifications) == total_files` |
| DA-8 | Per-Language Consistency | Per-language LOC sums match aggregate | Language LOC totals match |
| DA-9 | COCOMO Preset Ordering | COCOMO effort increases with org complexity | Monotonic ordering validated |
| DA-10 | P99 Monotonicity | p95 <= p99 <= max for all distributions | Percentile ordering maintained |
| DA-11 | Summary Structure | All 7 summary subsections present | Required subsections exist |
| DA-12 | File Entry Fields | All file entries have required fields | Location, Lines, Code, Complexity present |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 11-12 | 5 |
| 9-10 | 4 |
| 6-8 | 3 |
| 3-5 | 2 |
| 0-2 | 1 |

---

### 10. COCOMO Estimation (CO) - 10% Weight [NEW]

Validates COCOMO cost estimation output.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| CO-1 | COCOMO Output Present | COCOMO fields in json2 format | Fields: `estimatedCost`, `estimatedScheduleMonths`, `estimatedPeople` |
| CO-2 | Custom Params Applied | Different params produce different estimates | `embedded_cost > organic_cost` |
| CO-3 | Preset Values Match | SME preset produces expected ranges | Cost: $300K-$800K, Schedule: 5-15mo, People: 1-5 |

**Command Used:**
```bash
scc <path> -f json2 --cocomo-project-type <type>
```

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 3 | 5 |
| 2 | 4 |
| 1 | 3 |
| 0 | 2 |

---

## Scoring Methodology

### Per-Dimension Score Calculation

1. Run all checks for the dimension
2. Count passed checks
3. Map to 1-5 score using dimension-specific scoring table
4. Multiply by dimension weight to get weighted score

```python
dimension_score = scoring_table[passed_count]
weighted_score = dimension_score * dimension_weight
```

### Total Score Calculation

```python
total_score = sum(d.weighted_score for d in dimensions)
```

The maximum possible score is 5.0 (all dimensions score 5/5).

---

## Decision Thresholds

| Decision | Threshold | Description |
|----------|-----------|-------------|
| **STRONG_PASS** | >= 4.0 | Excellent fit, approved for immediate use |
| **PASS** | >= 3.5 | Good fit, approved with minor reservations |
| **WEAK_PASS** | >= 3.0 | Marginal fit, review failing checks before proceeding |
| **FAIL** | < 3.0 | Does not meet requirements |

### Decision Logic

```python
if total_score >= 4.0:
    return "STRONG_PASS"
elif total_score >= 3.5:
    return "PASS"
elif total_score >= 3.0:
    return "WEAK_PASS"
else:
    return "FAIL"
```

---

## Weight Allocation Rationale

### Core Dimensions (70%)

| Dimension | Weight | Rationale |
|-----------|--------|-----------|
| Output Quality | 20% | Highest priority - unusable if output is malformed |
| Integration Fit | 15% | Critical for pipeline integration |
| Reliability | 10% | Edge case handling affects production stability |
| Performance | 10% | Must meet latency requirements |
| Installation | 5% | Binary deployment is straightforward |
| Coverage | 5% | Language support is well-documented |
| License | 5% | MIT/Unlicense is pre-verified |

### Extended Dimensions (30%)

| Dimension | Weight | Rationale |
|-----------|--------|-----------|
| Per-File | 10% | Required for file-level analytics |
| Directory Analysis | 10% | Enables hotspot detection by directory |
| COCOMO | 10% | Cost estimation for due diligence reports |

---

## Ground Truth Specifications

### Synthetic Repository Structure

```
eval-repos/synthetic/
  python/           # 9 files
  csharp/           # 9 files
  javascript/       # 9 files
  typescript/       # 9 files
  go/               # 9 files
  rust/             # 9 files
  java/             # 9 files
```

**Total: 63 files across 7 languages**

### Expected Values

| Metric | Value | Tolerance |
|--------|-------|-----------|
| Total Files | 63 | Exact |
| Files per Language | 9 | Exact |
| Total LOC | 4500-10000 | Range |
| Languages Detected | 7 | Exact |

### Edge Case Files (per language)

| Type | Pattern | Expected Behavior |
|------|---------|-------------------|
| Empty | `empty.*` | Code=0, Lines=0 |
| Comments Only | `comments_only.*` | Code=0, Comment>0 |
| Single Line | `single_line.*` | Code=1 |
| Unicode | `unicode.*` | Lines>0, no parse errors |
| Deep Nesting | `deep_nesting.*` | Complexity>0 |

### Per-File Output Fields

| Field | Type | Description | Ground Truth |
|-------|------|-------------|--------------|
| Location | string | Relative file path | Non-empty for all files |
| Complexity | int | Cyclomatic complexity | >= 0 for all files |
| Uloc | int | Unique lines of code | >= 0 for all files |
| Minified | bool | File is minified | Present for all files |
| Generated | bool | File is generated | Present for all files |

### Directory Analysis Fields

| Field | Type | Description | Ground Truth |
|-------|------|-------------|--------------|
| path | string | Directory path | Non-empty |
| direct.file_count | int | Files directly in directory | >= 0 |
| direct.loc | int | LOC in direct files | >= 0 |
| recursive.file_count | int | Files in subtree | >= direct.file_count |
| recursive.loc | int | LOC in subtree | >= direct.loc |
| distribution.loc.* | float | LOC distribution stats | All 9 fields present |
| hotspot_score | float | Computed hotspot score | 0.0 - 1.0 |

### COCOMO Fields

| Field | Type | Description | Ground Truth (SME preset) |
|-------|------|-------------|---------------------------|
| estimatedCost | float | Estimated cost in USD | $300,000 - $800,000 |
| estimatedScheduleMonths | float | Estimated duration | 5.0 - 15.0 months |
| estimatedPeople | float | Estimated team size | 1.0 - 5.0 people |

---

## Running the Evaluation

### Prerequisites

1. scc binary installed in `bin/scc`
2. Python virtual environment in `.venv/`
3. Synthetic test repository in `eval-repos/synthetic/`

### Commands

```bash
# Run full evaluation
python scripts/evaluate.py

# Results saved to:
# - evaluation/results/scorecard.md
# - evaluation/results/evaluation_report.json
```

### Evaluation Outputs

Evaluation artifacts are written to a fixed location and overwrite the previous run:

```
evaluation/results/
├── output.json            # Envelope output for evaluation runs
├── raw_scc_output.json    # Raw scc output (evaluation)
├── evaluation_report.json            # Programmatic checks (JSON)
├── scorecard.md           # Programmatic scorecard
└── llm_evaluation.json    # LLM judge results (if run)
```

### Output Artifacts

| File | Description |
|------|-------------|
| `evaluation/results/scorecard.md` | Human-readable evaluation report |
| `evaluation/results/evaluation_report.json` | Detailed check results with evidence |
| `evaluation/results/output.json` | Envelope output used in evaluation |

---

## Extending the Evaluation

### Adding a New Dimension

1. Create check module in `scripts/checks/<dimension>.py`
2. Implement check functions returning `CheckResult`
3. Add `run_<dimension>_checks()` function
4. Add scoring table in `scripts/scoring.py`
5. Add weight in `DIMENSION_WEIGHTS`
6. Import and call in `scripts/evaluate.py`

### Adding a New Check

1. Add check function to appropriate module
2. Update scoring table thresholds if needed
3. Add check to the `run_*_checks()` function
4. Update documentation

---

## Appendix: Data Structures

### CheckResult

```python
@dataclass
class CheckResult:
    check_id: str      # e.g., "OQ-1"
    name: str          # e.g., "JSON Valid"
    passed: bool       # True/False
    message: str       # Human-readable result
    expected: Any      # Expected value (optional)
    actual: Any        # Actual value (optional)
    evidence: dict     # Supporting data (optional)
```

### DimensionResult

```python
@dataclass
class DimensionResult:
    dimension: str       # e.g., "output_quality"
    weight: float        # e.g., 0.20
    checks: List[CheckResult]
    score: int           # 1-5
    weighted_score: float  # score * weight
```

### EvaluationResult

```python
@dataclass
class EvaluationResult:
    run_id: str          # e.g., "eval-20260103-171124"
    timestamp: str       # ISO 8601 timestamp
    dimensions: List[DimensionResult]
    total_score: float   # 0.0 - 5.0
    decision: str        # STRONG_PASS, PASS, WEAK_PASS, FAIL
    summary: dict        # Aggregate statistics
```
