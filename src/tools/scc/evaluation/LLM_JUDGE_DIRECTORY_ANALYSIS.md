# LLM-as-Judge Evaluation Strategy: Directory Analysis Feature

## Document Overview

This document defines a comprehensive LLM-as-a-judge evaluation strategy for the Directory Analysis feature of the scc PoC. The strategy supplements the existing programmatic checks (DA-1 through DA-5) with semantic evaluation capabilities that assess qualitative aspects beyond simple pass/fail assertions.

**Version:** 1.0
**Last Updated:** 2026-01-03
**Feature Under Evaluation:** `scripts/directory_analyzer.py`

---

## 1. Evaluation Dimensions

The LLM judge evaluates five complementary dimensions. Each dimension has a weight, detailed rubric, and specific evidence requirements.

### Dimension Summary

| Dimension | Weight | Focus Area | Evaluation Type |
|-----------|--------|------------|-----------------|
| Structural Integrity | 25% | Schema correctness, hierarchy validity | Programmatic + LLM |
| Statistical Validity | 25% | Distribution accuracy, mathematical correctness | Programmatic + LLM |
| Hotspot Detection Quality | 20% | Detection accuracy, ranking reasonableness | LLM-primary |
| Aggregation Correctness | 15% | Direct vs recursive consistency | Programmatic + LLM |
| Output Interpretability | 15% | Usability for due diligence analysis | LLM-primary |

---

### 1.1 Structural Integrity (25%)

**Purpose:** Evaluate whether the output structure correctly represents the directory hierarchy and contains all required fields.

**Rubric (1-5 Scale):**

| Score | Criteria |
|-------|----------|
| 5 | All directories represented; hierarchy perfectly mirrors filesystem; all required fields present with correct types; no orphaned entries |
| 4 | Complete representation with minor issues (e.g., 1-2 directories missing non-critical optional fields) |
| 3 | Mostly complete but with gaps: missing 1-2 directories or 3-5 missing optional fields across output |
| 2 | Significant structural issues: missing multiple directories, broken parent-child relationships, or type mismatches |
| 1 | Fundamental failures: invalid JSON, missing required sections, or hierarchy completely incorrect |

**Evidence to Examine:**
- `directories[]` array completeness
- `direct` and `recursive` object presence in each directory
- `files[]` array contents matching `direct.file_count`
- `subdirectories[]` consistency with actual child directories
- Presence of: `path`, `name`, `depth`, `hotspot_score`, `is_hotspot`, `hotspot_rank`

**Binary Assertions (pre-LLM):**
1. JSON parses successfully
2. `directories` is an array
3. Each directory has `direct` and `recursive` objects
4. Each directory has `path` (non-empty string)
5. Each directory has numeric `depth >= 0`

---

### 1.2 Statistical Validity (25%)

**Purpose:** Evaluate the mathematical correctness of distribution statistics and ensure they follow statistical invariants.

**Rubric (1-5 Scale):**

| Score | Criteria |
|-------|----------|
| 5 | All percentiles monotonic; mean/median relationships plausible given skewness; stddev consistent with data spread; skewness/kurtosis correctly indicate distribution shape |
| 4 | Statistics mathematically correct with minor interpretation concerns (e.g., unusual but valid distributions) |
| 3 | Mostly correct but with 1-2 statistical anomalies (e.g., p90 > p95 in edge cases, questionable skewness sign) |
| 2 | Multiple statistical errors: non-monotonic percentiles, impossible stddev values, or mean outside min-max range |
| 1 | Fundamental statistical failures: negative counts, mean < min or mean > max, or distributions not computed |

**Evidence to Examine:**
- `distribution.loc`, `distribution.complexity`, `distribution.comment_ratio`
- For each distribution: `min`, `max`, `mean`, `median`, `stddev`, `p25`, `p75`, `p90`, `p95`, `skewness`, `kurtosis`
- Cross-validate: `min <= p25 <= median <= p75 <= p90 <= p95 <= max`
- Cross-validate: `min <= mean <= max`
- Skewness sign consistency with mean vs median relationship

**Binary Assertions (pre-LLM):**
1. Percentiles are monotonically increasing: `p25 <= median <= p75 <= p90 <= p95`
2. `min <= mean <= max` for all distributions
3. `stddev >= 0` for all distributions
4. Distribution present when `file_count >= 3`
5. Distribution null/empty when `file_count < 3`

---

### 1.3 Hotspot Detection Quality (20%)

**Purpose:** Evaluate whether hotspot scores and rankings reasonably identify problematic directories based on the defined criteria.

**Rubric (1-5 Scale):**

| Score | Criteria |
|-------|----------|
| 5 | Hotspot scores accurately reflect complexity/size/comment factors; rankings correctly order directories; no false positives on trivial directories; no false negatives on obviously complex directories |
| 4 | Scoring logic correctly applied with minor edge case issues; rankings sensible with 1-2 debatable placements |
| 3 | Scoring generally works but with notable gaps: some clearly complex directories underscored or simple directories overscored |
| 2 | Significant scoring issues: multiple directories with implausible scores given their metrics; ranking order questionable |
| 1 | Scoring fundamentally broken: scores outside [0,1], rankings inverted, or obvious hotspots missed entirely |

**Evidence to Examine:**
- `hotspot_score` for each directory
- `is_hotspot` flag (threshold: score > 0.7)
- `hotspot_rank` ordering (rank 1 = highest score)
- Correlation between score and: `complexity_total`, `file_count`, `lines_code`, comment ratio, LOC skewness
- Sample high-scoring directories: do they genuinely have concerning characteristics?
- Sample low-scoring directories: are they genuinely benign?

**Hotspot Factor Reference:**
| Factor | Threshold | Points |
|--------|-----------|--------|
| High avg complexity | >20 | 0.30 |
| High avg complexity | >10 | 0.15 |
| Large directory | >50 files | 0.20 |
| Large directory | >20 files | 0.10 |
| High LOC | >5000 | 0.20 |
| High LOC | >2000 | 0.10 |
| Low comment ratio | <0.05 | 0.15 |
| High LOC skewness | >2.0 | 0.15 |

**Binary Assertions (pre-LLM):**
1. All `hotspot_score` values in [0, 1]
2. `is_hotspot == (hotspot_score > 0.7)` for all directories
3. `hotspot_rank` values are 1 to N with no gaps
4. Directory with rank 1 has highest hotspot_score

---

### 1.4 Aggregation Correctness (15%)

**Purpose:** Evaluate whether direct and recursive statistics are correctly computed and their relationship is consistent.

**Rubric (1-5 Scale):**

| Score | Criteria |
|-------|----------|
| 5 | Perfect aggregation: recursive includes all descendants; direct counts only immediate files; sum of leaf direct counts equals total; no double-counting |
| 4 | Aggregation correct with minor discrepancies (e.g., off-by-one in edge cases) |
| 3 | Mostly correct but with isolated aggregation errors affecting 1-2 directories |
| 2 | Significant aggregation issues: multiple directories where recursive < direct or sum mismatches |
| 1 | Fundamental aggregation failures: recursive consistently wrong or direct/recursive reversed |

**Evidence to Examine:**
- For each directory: `recursive.file_count >= direct.file_count`
- For each directory: `recursive.lines_code >= direct.lines_code`
- Sum of `direct.file_count` for leaf directories == `summary.total_files`
- Parent recursive stats include child recursive stats
- Root directory recursive stats match summary totals

**Binary Assertions (pre-LLM):**
1. `recursive.file_count >= direct.file_count` for all directories
2. `recursive.lines_code >= direct.lines_code` for all directories
3. `sum(dir.direct.file_count for all dirs) == summary.total_files`
4. Root directory `recursive.file_count == summary.total_files`

---

### 1.5 Output Interpretability (15%)

**Purpose:** Evaluate whether the output is useful and interpretable for due diligence analysis purposes.

**Rubric (1-5 Scale):**

| Score | Criteria |
|-------|----------|
| 5 | Output provides clear, actionable insights; directory hierarchy easy to navigate; statistics meaningful for decision-making; COCOMO estimates reasonable; hotspots clearly identifiable |
| 4 | Good interpretability with minor gaps (e.g., some metrics need domain knowledge to interpret) |
| 3 | Usable but requires significant expertise; some fields unclear or poorly named; hotspot identification possible but not intuitive |
| 2 | Difficult to interpret: confusing structure, misleading field names, or statistics that don't support analysis goals |
| 1 | Not interpretable: output structure unclear, critical information missing, or actively misleading |

**Evidence to Examine:**
- Field naming clarity
- Presence of `summary` with aggregate metrics
- COCOMO estimates: `effort_person_months`, `schedule_months`, `cost`, `people`
- Language breakdown in `languages` field
- `dryness_pct` (ULOC ratio) meaningfulness
- Ability to identify "where to look" from output alone

**Qualitative Questions for LLM:**
1. Could a technical due diligence analyst use this output to identify problem areas?
2. Are the hotspot rankings actionable (i.e., would investigating top hotspots be valuable)?
3. Is the COCOMO cost estimate in a reasonable range given the codebase size?
4. Does the output support comparing directories to identify relative risk?

---

## 2. Prompt Template

### 2.1 Full Judge Prompt

```
You are an expert evaluator for a code analysis tool. You are assessing the Directory Analysis feature output for quality and correctness.

## Context

The Directory Analysis feature analyzes a codebase and produces:
1. Two-level statistics per directory (direct = files in this dir only; recursive = all files in subtree)
2. Distribution statistics (min, max, mean, median, stddev, percentiles, skewness, kurtosis)
3. Hotspot detection (score 0-1 based on complexity, size, LOC, comment ratio, skewness)

Hotspot scoring factors:
- High avg complexity (>20 = 0.30 points, >10 = 0.15 points)
- Large directory (>50 files = 0.20 points, >20 files = 0.10 points)
- High LOC (>5000 = 0.20 points, >2000 = 0.10 points)
- Low comment ratio (<0.05 = 0.15 points)
- High LOC skewness (>2.0 = 0.15 points)

## Evaluation Dimension: {dimension_name}

{dimension_description}

## Rubric

{rubric_text}

## Evidence

### Output Summary
{output_summary}

### Sample Directories
{sample_directories}

### Pre-Check Results
{precheck_results}

### Specific Evidence for This Dimension
{dimension_specific_evidence}

## Task

Evaluate this dimension and provide your assessment.

1. First, analyze the evidence systematically
2. Apply the rubric criteria
3. Identify specific issues or strengths
4. Assign a score (1-5)

Respond in this exact JSON format:
{
  "dimension": "{dimension_name}",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<2-4 sentences explaining the score>",
  "strengths": ["<specific positive finding>", ...],
  "issues": ["<specific problem found>", ...],
  "evidence_cited": ["<specific data point referenced>", ...]
}
```

### 2.2 Dimension-Specific Descriptions

**Structural Integrity:**
```
Evaluate whether the output structure correctly represents the directory hierarchy.

Key questions:
- Are all expected directories present?
- Does each directory have the required fields (path, name, depth, direct, recursive, files, subdirectories, hotspot_score, is_hotspot, hotspot_rank)?
- Are parent-child relationships correct?
- Are data types appropriate (strings, numbers, arrays, objects)?
```

**Statistical Validity:**
```
Evaluate the mathematical correctness of distribution statistics.

Key questions:
- Are percentiles monotonically increasing (p25 <= median <= p75 <= p90 <= p95)?
- Is the mean within [min, max]?
- Does skewness sign match the mean vs median relationship?
- Are distributions present only when file_count >= 3?
- Are impossible values absent (negative counts, stddev, etc.)?
```

**Hotspot Detection Quality:**
```
Evaluate whether hotspot scores accurately identify problematic directories.

Key questions:
- Do high-scoring directories genuinely have concerning characteristics (high complexity, large size, low comments)?
- Do low-scoring directories genuinely lack concerning characteristics?
- Are rankings consistent with scores?
- Is the 0.7 threshold for is_hotspot appropriate given the data?
```

**Aggregation Correctness:**
```
Evaluate whether direct and recursive statistics are correctly computed.

Key questions:
- Does recursive.file_count >= direct.file_count for every directory?
- Do parent recursive stats include all child files?
- Does the sum of direct file counts equal total files?
- Is there any double-counting or missing files?
```

**Output Interpretability:**
```
Evaluate whether the output is useful for due diligence analysis.

Key questions:
- Could an analyst quickly identify problem areas from this output?
- Are field names clear and self-explanatory?
- Are COCOMO estimates in reasonable ranges?
- Does the output support comparing directories to prioritize investigation?
```

---

## 3. Calibration Examples

### 3.1 Example: Perfect Structural Integrity (Score 5)

**Evidence:**
```json
{
  "total_directories": 23,
  "all_have_direct_recursive": true,
  "all_have_required_fields": true,
  "parent_child_consistent": true,
  "depth_values_correct": true,
  "sample_directory": {
    "path": "eval-repos/synthetic/python",
    "name": "python",
    "depth": 2,
    "direct": {"file_count": 9, "lines_code": 765},
    "recursive": {"file_count": 9, "lines_code": 765},
    "files": [9 file objects],
    "subdirectories": [],
    "hotspot_score": 0.15,
    "is_hotspot": false,
    "hotspot_rank": 15
  }
}
```

**Expected Response:**
```json
{
  "dimension": "Structural Integrity",
  "score": 5,
  "confidence": 0.95,
  "reasoning": "All 23 directories are present with complete field sets. Parent-child relationships are consistent with the filesystem structure. Depth values correctly reflect directory nesting. No orphaned entries or structural anomalies detected.",
  "strengths": ["Complete directory coverage", "Consistent parent-child relationships", "All required fields present"],
  "issues": [],
  "evidence_cited": ["23/23 directories have direct/recursive", "depth values match path nesting", "files array length matches direct.file_count"]
}
```

---

### 3.2 Example: Questionable Hotspot Detection (Score 3)

**Evidence:**
```json
{
  "hotspot_rankings": [
    {"path": "src/utils", "score": 0.85, "complexity": 5, "file_count": 3, "loc": 150},
    {"path": "src/core", "score": 0.35, "complexity": 45, "file_count": 12, "loc": 3500}
  ],
  "anomalies": [
    "src/utils has high score (0.85) despite low complexity (5) and small size (3 files)",
    "src/core has low score (0.35) despite high complexity (45) and significant LOC (3500)"
  ]
}
```

**Expected Response:**
```json
{
  "dimension": "Hotspot Detection Quality",
  "score": 3,
  "confidence": 0.80,
  "reasoning": "The scoring logic appears to be applied but with unexpected results. The src/utils directory scores 0.85 despite having low complexity (5) and only 3 files, while src/core scores only 0.35 despite having complexity of 45 and 3500 LOC. This suggests the scoring factors may not be weighting complexity appropriately for this codebase.",
  "strengths": ["Scores are within valid range [0,1]", "Rankings are consistent with scores"],
  "issues": ["Apparent under-weighting of complexity factor", "Small directory with artificially high score", "Complex directory potentially under-flagged"],
  "evidence_cited": ["src/utils: score=0.85, complexity=5, files=3", "src/core: score=0.35, complexity=45, files=12, loc=3500"]
}
```

---

### 3.3 Example: Statistical Error (Score 2)

**Evidence:**
```json
{
  "directory": "src/components",
  "distribution": {
    "loc": {
      "min": 50,
      "max": 500,
      "mean": 35,
      "median": 150,
      "p25": 100,
      "p75": 200,
      "p90": 180,
      "p95": 450
    }
  },
  "violations": [
    "mean (35) < min (50)",
    "p90 (180) < p75 (200) - non-monotonic"
  ]
}
```

**Expected Response:**
```json
{
  "dimension": "Statistical Validity",
  "score": 2,
  "confidence": 0.95,
  "reasoning": "Multiple fundamental statistical errors detected. The mean (35) is below the minimum value (50), which is mathematically impossible. Additionally, percentiles are non-monotonic: p90 (180) is less than p75 (200). These errors indicate a bug in the statistics computation.",
  "strengths": ["Percentile fields are present", "Most values are positive"],
  "issues": ["Mean below minimum - impossible", "Non-monotonic percentiles (p90 < p75)", "Statistics unreliable for analysis"],
  "evidence_cited": ["min=50, mean=35 (mean < min)", "p75=200, p90=180 (p90 < p75)"]
}
```

---

### 3.4 Example: Excellent Interpretability (Score 5)

**Evidence:**
```json
{
  "summary": {
    "total_directories": 23,
    "total_files": 63,
    "total_loc": 5885,
    "total_complexity": 1027,
    "hotspot_directories": 2,
    "dryness_pct": 0.8153,
    "cocomo": {
      "effort_person_months": 8.5,
      "schedule_months": 6.2,
      "people": 1.4,
      "cost": 204000
    }
  },
  "language_breakdown": {
    "Python": 9, "C#": 9, "JavaScript": 9, "TypeScript": 9,
    "Go": 9, "Rust": 9, "Java": 9
  },
  "top_hotspots": [
    {"path": "src/legacy", "score": 0.75, "why": "high complexity, low comments"},
    {"path": "src/core/engine", "score": 0.72, "why": "large file count, high LOC"}
  ]
}
```

**Expected Response:**
```json
{
  "dimension": "Output Interpretability",
  "score": 5,
  "confidence": 0.90,
  "reasoning": "The output provides excellent support for due diligence analysis. The summary gives a clear overview with total files, LOC, complexity, and hotspot count. COCOMO estimates ($204K, 8.5 person-months) are reasonable for a 6K LOC codebase. The language breakdown and top hotspots allow immediate prioritization of investigation areas.",
  "strengths": ["Clear summary section", "Actionable hotspot identification", "Reasonable COCOMO estimates", "Language breakdown for technology assessment"],
  "issues": [],
  "evidence_cited": ["summary.cocomo.cost=$204K for 5885 LOC", "2 hotspots identified", "7 languages detected with even distribution"]
}
```

---

### 3.5 Example: Aggregation Error (Score 2)

**Evidence:**
```json
{
  "violations": [
    {
      "directory": "src/api",
      "direct_file_count": 15,
      "recursive_file_count": 12,
      "issue": "recursive < direct"
    }
  ],
  "sum_check": {
    "sum_of_direct": 58,
    "total_files": 63,
    "match": false
  }
}
```

**Expected Response:**
```json
{
  "dimension": "Aggregation Correctness",
  "score": 2,
  "confidence": 0.95,
  "reasoning": "Critical aggregation errors found. The src/api directory has direct.file_count=15 but recursive.file_count=12, which is impossible (recursive must always be >= direct). Additionally, the sum of direct file counts (58) does not match total_files (63), indicating 5 files are either missing or double-counted.",
  "strengths": ["Most directories appear correctly aggregated"],
  "issues": ["recursive < direct for src/api - impossible", "Sum mismatch: 58 direct vs 63 total", "5 files unaccounted for"],
  "evidence_cited": ["src/api: direct=15, recursive=12", "sum(direct)=58, total=63"]
}
```

---

## 4. Edge Cases to Test

The LLM judge should specifically examine these edge cases:

### 4.1 Empty Directories

| Case | Expected Behavior | Evidence to Check |
|------|-------------------|-------------------|
| Directory with no files | `direct.file_count = 0`, `distribution = null` | Verify null distribution, not empty object |
| Directory with only subdirectories | `direct.file_count = 0`, `recursive.file_count > 0` | Verify recursive includes children |
| Root directory | May have `direct.file_count = 0` | Verify recursive covers entire tree |

### 4.2 Single-File Directories

| Case | Expected Behavior | Evidence to Check |
|------|-------------------|-------------------|
| Directory with 1 file | `file_count = 1`, `distribution = null` or minimal | Distribution requires >= 3 files |
| Directory with 2 files | `file_count = 2`, `distribution = null` or minimal | stddev computation requires n >= 2 |

### 4.3 Deep Nesting

| Case | Expected Behavior | Evidence to Check |
|------|-------------------|-------------------|
| Directory at depth 5+ | `depth` field correct, parent-child intact | Verify path parsing handles deep nesting |
| Long directory names | Path correctly parsed | Unicode and special characters |

### 4.4 Distribution Edge Cases

| Case | Expected Behavior | Evidence to Check |
|------|-------------------|-------------------|
| All files same size | `stddev = 0`, `skewness = 0`, `min = max = mean = median` | Degenerate distributions handled |
| Extreme outlier | High skewness, high kurtosis, p95 >> p75 | Heavy-tailed detection works |
| All zeros | `min = max = mean = median = 0`, `stddev = 0` | Zero files (empty) handled |

### 4.5 Hotspot Edge Cases

| Case | Expected Behavior | Evidence to Check |
|------|-------------------|-------------------|
| Score exactly 0.7 | `is_hotspot = false` (> 0.7 required) | Threshold boundary |
| Score 0.0 | Valid for trivial directories | Not flagged as error |
| Score 1.0 | Maximum possible score | Multiple factors combined |
| All scores identical | Rankings still assigned 1 to N | Tie-breaking behavior |

### 4.6 Aggregation Edge Cases

| Case | Expected Behavior | Evidence to Check |
|------|-------------------|-------------------|
| Leaf directory | `direct == recursive` | No children to aggregate |
| Parent with single child | `parent.recursive = child.recursive` | Single-child case |
| Very wide directory | Many subdirectories | Horizontal aggregation correct |

---

## 5. Ground Truth Assertions (Programmatic)

These assertions run BEFORE the LLM judge to filter obvious failures:

### 5.1 Schema Assertions (Hard Failures)

```python
def assert_schema_valid(output: dict) -> List[str]:
    """Return list of schema violations (empty = pass)."""
    violations = []

    # Root structure
    if "directories" not in output:
        violations.append("Missing 'directories' array")
    if "summary" not in output:
        violations.append("Missing 'summary' object")

    # Directory structure
    for d in output.get("directories", []):
        if "path" not in d or not d["path"]:
            violations.append(f"Directory missing 'path'")
        if "direct" not in d:
            violations.append(f"Directory {d.get('path', '?')} missing 'direct'")
        if "recursive" not in d:
            violations.append(f"Directory {d.get('path', '?')} missing 'recursive'")
        if "hotspot_score" not in d:
            violations.append(f"Directory {d.get('path', '?')} missing 'hotspot_score'")

    return violations
```

### 5.2 Statistical Invariant Assertions

```python
def assert_statistics_valid(output: dict) -> List[str]:
    """Return list of statistical violations."""
    violations = []

    for d in output.get("directories", []):
        for stats_type in ["direct", "recursive"]:
            dist = d.get(stats_type, {}).get("distribution")
            if dist is None:
                continue

            for metric in ["loc", "complexity", "comment_ratio"]:
                m = dist.get(metric, {})
                if not m:
                    continue

                # Percentile monotonicity
                if m.get("p25", 0) > m.get("median", float("inf")):
                    violations.append(f"{d['path']}.{stats_type}.{metric}: p25 > median")
                if m.get("median", 0) > m.get("p75", float("inf")):
                    violations.append(f"{d['path']}.{stats_type}.{metric}: median > p75")
                if m.get("p75", 0) > m.get("p90", float("inf")):
                    violations.append(f"{d['path']}.{stats_type}.{metric}: p75 > p90")
                if m.get("p90", 0) > m.get("p95", float("inf")):
                    violations.append(f"{d['path']}.{stats_type}.{metric}: p90 > p95")

                # Mean within range
                if m.get("mean", 0) < m.get("min", 0):
                    violations.append(f"{d['path']}.{stats_type}.{metric}: mean < min")
                if m.get("mean", 0) > m.get("max", float("inf")):
                    violations.append(f"{d['path']}.{stats_type}.{metric}: mean > max")

                # Non-negative stddev
                if m.get("stddev", 0) < 0:
                    violations.append(f"{d['path']}.{stats_type}.{metric}: negative stddev")

    return violations
```

### 5.3 Aggregation Assertions

```python
def assert_aggregation_valid(output: dict) -> List[str]:
    """Return list of aggregation violations."""
    violations = []

    # Check recursive >= direct for each directory
    for d in output.get("directories", []):
        direct = d.get("direct", {})
        recursive = d.get("recursive", {})

        if recursive.get("file_count", 0) < direct.get("file_count", 0):
            violations.append(
                f"{d['path']}: recursive.file_count ({recursive.get('file_count')}) "
                f"< direct.file_count ({direct.get('file_count')})"
            )

        if recursive.get("lines_code", 0) < direct.get("lines_code", 0):
            violations.append(
                f"{d['path']}: recursive.lines_code < direct.lines_code"
            )

    # Check sum of direct files equals total
    total_direct = sum(
        len(d.get("files", []))
        for d in output.get("directories", [])
    )
    total_files = output.get("summary", {}).get("total_files", 0)

    if total_direct != total_files:
        violations.append(
            f"Sum of direct files ({total_direct}) != total_files ({total_files})"
        )

    return violations
```

### 5.4 Hotspot Assertions

```python
def assert_hotspots_valid(output: dict) -> List[str]:
    """Return list of hotspot violations."""
    violations = []

    scores = []
    for d in output.get("directories", []):
        score = d.get("hotspot_score")

        # Score in range
        if score is None:
            violations.append(f"{d['path']}: missing hotspot_score")
        elif not (0 <= score <= 1):
            violations.append(f"{d['path']}: hotspot_score {score} not in [0,1]")
        else:
            scores.append((score, d["path"]))

        # is_hotspot consistency
        if score is not None:
            expected_hotspot = score > 0.7
            actual_hotspot = d.get("is_hotspot", False)
            if expected_hotspot != actual_hotspot:
                violations.append(
                    f"{d['path']}: is_hotspot={actual_hotspot} but score={score}"
                )

    # Rank consistency
    scores_sorted = sorted(scores, key=lambda x: -x[0])
    for i, (score, path) in enumerate(scores_sorted):
        expected_rank = i + 1
        actual_rank = next(
            (d.get("hotspot_rank") for d in output.get("directories", [])
             if d["path"] == path),
            None
        )
        if actual_rank != expected_rank:
            violations.append(
                f"{path}: expected rank {expected_rank}, got {actual_rank}"
            )

    return violations
```

---

## 6. Integration with Existing Evaluation Framework

### 6.1 Execution Flow

```
1. Run programmatic checks (DA-1 to DA-5)
   |
   v
2. Run ground truth assertions (schema, statistics, aggregation, hotspots)
   |
   v
3. If assertions pass, invoke LLM judge for each dimension
   |
   v
4. Aggregate LLM scores with programmatic results
   |
   v
5. Generate combined scorecard
```

### 6.2 Score Integration

The final Directory Analysis dimension score combines:

| Component | Weight | Source |
|-----------|--------|--------|
| Programmatic checks (DA-1 to DA-5) | 50% | Existing `check_directory_analysis.py` |
| LLM Judge (5 dimensions) | 50% | New LLM evaluation |

**Combined Score Formula:**
```python
programmatic_score = (passed_checks / 5) * 5  # Scale to 1-5
llm_score = sum(dim.score * dim.weight for dim in llm_dimensions)
final_score = 0.5 * programmatic_score + 0.5 * llm_score
```

### 6.3 Output Format

```json
{
  "dimension": "directory_analysis",
  "check_results": {
    "DA-1": {"passed": true, "message": "..."},
    "DA-2": {"passed": true, "message": "..."},
    "DA-3": {"passed": true, "message": "..."},
    "DA-4": {"passed": true, "message": "..."},
    "DA-5": {"passed": true, "message": "..."}
  },
  "programmatic_score": 5,
  "assertion_violations": [],
  "llm_evaluations": {
    "structural_integrity": {"score": 5, "confidence": 0.95, "reasoning": "..."},
    "statistical_validity": {"score": 4, "confidence": 0.85, "reasoning": "..."},
    "hotspot_detection_quality": {"score": 4, "confidence": 0.80, "reasoning": "..."},
    "aggregation_correctness": {"score": 5, "confidence": 0.95, "reasoning": "..."},
    "output_interpretability": {"score": 5, "confidence": 0.90, "reasoning": "..."}
  },
  "llm_aggregate_score": 4.6,
  "final_score": 4.8,
  "decision": "PASS"
}
```

---

## 7. Implementation Checklist

### 7.1 New Files to Create

| File | Purpose |
|------|---------|
| `scripts/checks/directory_analysis_llm.py` | LLM judge implementation |
| `evaluation/prompts/directory_analysis.yaml` | Prompt templates |
| `evaluation/calibration/directory_analysis.json` | Calibration examples |

### 7.2 Files to Modify

| File | Changes |
|------|---------|
| `scripts/evaluate.py` | Add LLM judge invocation after DA checks |
| `scripts/scoring.py` | Add combined scoring logic |
| `scripts/llm_judge.py` | Add `judge_directory_analysis()` function |

### 7.3 Dependencies

- `anthropic` Python package (existing)
- `ANTHROPIC_API_KEY` environment variable (existing)

### 7.4 Testing

| Test Type | Coverage |
|-----------|----------|
| Unit tests | Assertion functions with known good/bad inputs |
| Integration tests | Full LLM judge flow with mock responses |
| Calibration tests | Verify LLM scores match expected for calibration examples |

---

## 8. Maintenance and Iteration

### 8.1 Calibration Schedule

- **Initial calibration:** Run LLM judge on 10 diverse outputs, manually score, compare
- **Monthly review:** Sample 5 random evaluations, verify LLM reasoning quality
- **Threshold adjustment:** If agreement drops below 85%, retrain calibration examples

### 8.2 Prompt Evolution

Track prompt versions in `evaluation/prompts/directory_analysis.yaml`:

```yaml
version: "1.0"
last_updated: "2026-01-03"
changes:
  - "Initial release"

model_requirements:
  recommended: "claude-3-5-sonnet-20241022"
  fallback: "claude-3-haiku-20240307"

calibration_agreement:
  target: 0.85
  current: null  # Fill after calibration
```

### 8.3 Known Limitations

1. **Hotspot scoring is deterministic:** LLM cannot override scoring logic, only evaluate if logic was applied correctly
2. **Statistical edge cases:** Very small files or degenerate distributions may produce unusual but valid statistics
3. **COCOMO sensitivity:** Cost estimates vary significantly with COCOMO preset choice

---

## Appendix A: Complete Evidence Schema

```json
{
  "output_summary": {
    "schema_version": "string",
    "run_id": "string",
    "total_directories": "int",
    "total_files": "int",
    "total_loc": "int",
    "hotspot_count": "int",
    "cocomo_cost": "float",
    "cocomo_months": "float"
  },
  "sample_directories": [
    {
      "path": "string",
      "depth": "int",
      "direct_file_count": "int",
      "direct_loc": "int",
      "recursive_file_count": "int",
      "recursive_loc": "int",
      "hotspot_score": "float",
      "is_hotspot": "bool",
      "has_distribution": "bool"
    }
  ],
  "precheck_results": {
    "schema_valid": "bool",
    "schema_violations": ["string"],
    "statistics_valid": "bool",
    "statistics_violations": ["string"],
    "aggregation_valid": "bool",
    "aggregation_violations": ["string"],
    "hotspots_valid": "bool",
    "hotspot_violations": ["string"]
  },
  "dimension_specific": {
    "structural_integrity": {
      "fields_present": {"path": true, "direct": true, "...": "..."},
      "type_checks": {"path": "string", "depth": "int", "...": "..."},
      "hierarchy_valid": "bool"
    },
    "statistical_validity": {
      "distributions_present": "int",
      "monotonic_violations": "int",
      "range_violations": "int",
      "sample_distribution": {"metric": "loc", "values": {"min": 0, "max": 591, "...": "..."}}
    },
    "hotspot_detection_quality": {
      "top_hotspots": [{"path": "...", "score": 0.75, "factors": {"complexity": true, "...": "..."}}],
      "bottom_directories": [{"path": "...", "score": 0.0, "file_count": 3}],
      "score_distribution": {"min": 0.0, "max": 0.85, "mean": 0.25}
    },
    "aggregation_correctness": {
      "recursive_gte_direct_all": "bool",
      "sum_matches_total": "bool",
      "violations": []
    },
    "output_interpretability": {
      "summary_present": "bool",
      "cocomo_present": "bool",
      "language_breakdown_present": "bool",
      "field_names_clear": ["path", "direct", "recursive", "hotspot_score"]
    }
  }
}
```

---

## Appendix B: Decision Matrix

| Programmatic Score | LLM Score | Final Score | Decision |
|--------------------|-----------|-------------|----------|
| 5 | 5.0 | 5.0 | STRONG_PASS |
| 5 | 4.0 | 4.5 | STRONG_PASS |
| 5 | 3.0 | 4.0 | STRONG_PASS |
| 4 | 4.0 | 4.0 | STRONG_PASS |
| 4 | 3.0 | 3.5 | PASS |
| 3 | 4.0 | 3.5 | PASS |
| 3 | 3.0 | 3.0 | WEAK_PASS |
| 2 | 4.0 | 3.0 | WEAK_PASS |
| 2 | 2.0 | 2.0 | FAIL |
| 1 | any | < 3.0 | FAIL |

---

*End of Document*
