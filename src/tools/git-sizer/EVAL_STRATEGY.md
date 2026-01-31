# Evaluation Strategy: git-sizer

This document describes the evaluation methodology for the git-sizer repository health analysis tool in Caldera.

## Philosophy & Approach

### Tool Purpose

git-sizer analyzes Git repositories to detect scaling issues and provide health assessments. It measures:
- **Blob sizes**: Identifies large files that should use Git LFS
- **Tree structures**: Detects wide directories that slow Git operations
- **History depth**: Analyzes commit counts and ancestry
- **Path characteristics**: Identifies deeply nested structures

### Why Hybrid Evaluation?

The evaluation combines **programmatic checks** with **LLM-as-a-Judge** evaluation:

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 80% | Objective size/structure validation |
| LLM Judges | 20% | Threshold quality and actionability assessment |

The 80/20 split reflects git-sizer's focus on quantitative metrics where ground truth can be precisely defined.

### Evaluation Goals

1. **Size Accuracy**: Validate blob/tree/commit measurements match expected values
2. **Coverage**: Ensure all relevant metrics are captured
3. **Edge Cases**: Verify handling of extreme repository structures
4. **Performance**: Confirm analysis completes within time bounds
5. **Threshold Quality**: Assess appropriateness of violation detection
6. **Actionability**: Evaluate usefulness of LFS recommendations and health grades

---

## Dimension Summary

All evaluation dimensions with their check counts and weights:

| Category | Dimension | Code Prefix | Checks | Weight | Focus Area |
|----------|-----------|-------------|--------|--------|------------|
| Programmatic | Size Accuracy | AC | AC-1 to AC-8 | 35% | Blob, tree, commit size validation |
| Programmatic | Coverage | CV | CV-1 to CV-8 | 20% | Metric presence and completeness |
| Programmatic | Edge Cases | EC | EC-1 to EC-8 | 15% | Extreme structure handling |
| Programmatic | Performance | PF | PF-1 to PF-4 | 10% | Analysis speed and efficiency |
| LLM | Threshold Quality | - | 1 judge | 10% | Violation detection accuracy |
| LLM | Actionability | - | 1 judge | 10% | Report usefulness |

**Total**: 28 programmatic checks + 4 LLM judges

---

## Complete Check Catalog

### Size Accuracy Checks (AC-1 to AC-8)

| ID | Name | Pass Criteria |
|----|------|---------------|
| AC-1 | Large blob detection | `max_blob_size >= 5 MB` for bloated repo |
| AC-2 | Total blob size accuracy | `blob_total_size >= 15 MB` for bloated repo |
| AC-3 | Commit count accuracy | `commit_count` within 490-510 for deep-history repo |
| AC-4 | Tree entries detection | `max_tree_entries >= 900` for wide-tree repo |
| AC-5 | Path depth detection | `max_path_depth >= 15` for deep-nesting repo |
| AC-6 | Health grade accuracy | Healthy repos get A/A+, problematic get C-F |
| AC-7 | LFS candidate identification | Bloated repo has `lfs_candidates.length > 0` |
| AC-8 | Threshold violation detection | Bloated: 1+, Wide-tree: 2+, Healthy: 0 |

### Coverage Checks (CV-1 to CV-8)

| ID | Name | Pass Criteria |
|----|------|---------------|
| CV-1 | Blob metrics coverage | `blob_count`, `blob_total_size`, `max_blob_size` present |
| CV-2 | Tree metrics coverage | `tree_count`, `tree_total_entries`, `max_tree_entries` present |
| CV-3 | Commit metrics coverage | `commit_count`, `commit_total_size`, `max_commit_size` present |
| CV-4 | Reference metrics coverage | `reference_count`, `branch_count`, `tag_count` present |
| CV-5 | Path metrics coverage | `max_path_depth`, `max_path_length` present |
| CV-6 | Expanded checkout metrics | `expanded_tree_count`, `expanded_blob_count` present |
| CV-7 | Health grade coverage | All repos have `health_grade` |
| CV-8 | Violation detail coverage | All violations have `metric`, `level` fields |

### Edge Case Checks (EC-1 to EC-8)

| ID | Name | Pass Criteria |
|----|------|---------------|
| EC-1 | Minimal repo handling | Healthy repo analyzed with `commit_count > 0` |
| EC-2 | Large history handling | Deep-history repo analyzed with `commit_count > 400` |
| EC-3 | Wide tree handling | Wide-tree repo analyzed with `max_tree_entries > 500` |
| EC-4 | Deep path handling | `max_path_depth > 10` detected |
| EC-5 | No violations case | Healthy repo has `violations.length == 0` |
| EC-6 | Multiple violations case | Wide-tree repo has `violations.length >= 2` |
| EC-7 | JSON output validity | `timestamp`, `repositories`, `summary` present |
| EC-8 | Raw output preservation | All repos have `raw_output` with content |

### Performance Checks (PF-1 to PF-4)

| ID | Name | Pass Criteria |
|----|------|---------------|
| PF-1 | Total analysis speed | `total_duration_ms < 5000` (5 seconds) |
| PF-2 | Per-repo analysis speed | `duration_ms < 2000` for 75%+ of repos |
| PF-3 | Large repo handling | `duration_ms < 30000` (30 seconds) |
| PF-4 | Output size efficiency | Total raw output `< 100 KB` |

---

## Decision Thresholds

| Decision | Combined Score | Interpretation |
|----------|----------------|----------------|
| STRONG_PASS | >= 4.0 | Production-ready, all dimensions excellent |
| PASS | >= 3.5 | Good quality, minor improvements possible |
| WEAK_PASS | >= 3.0 | Acceptable with documented limitations |
| FAIL | < 3.0 | Significant issues, not recommended for use |

---

## Ground Truth Specifications

### Synthetic Repository Overview

| Repository | Purpose | Expected Health Grade | Expected Violations |
|------------|---------|----------------------|---------------------|
| healthy-repo | Baseline clean repository | A or A+ | 0 |
| bloated-repo | Large binary files (LFS candidates) | C, C+, D, or D+ | 1-4 |
| deep-history | 500+ commits | B, B+, C, or C+ | 0-2 |
| wide-tree | 1000+ files in single directory | C, C+, D, or D+ | 1-3 |
| multi-branch | Multiple branches/tags | A, B, or B+ | 0-1 |

### Ground Truth Schema

```json
{
  "schema_version": "1.0",
  "scenario": "repo-name",
  "description": "Human-readable description",
  "repo_path": "eval-repos/synthetic/repo-name",
  "expected": {
    "health_grade": {
      "acceptable": ["A", "A+"],
      "description": "Why these grades are expected"
    },
    "metrics": {
      "metric_name": {
        "min": 0,
        "max": 100,
        "description": "What this metric measures"
      }
    }
  }
}
```

---

## LLM Judge Dimensions

### Judge Summary

| Judge | Weight | Focus | Sub-Dimensions |
|-------|--------|-------|----------------|
| Size Accuracy | 35% | Blob/tree/commit sizing | Blob (40%), Tree (30%), Commit (30%) |
| Threshold Quality | 25% | Violation detection | True Positive (40%), False Positive (30%), Severity (30%) |
| Actionability | 20% | Report usefulness | LFS Recommendations (40%), Violation Clarity (30%), Prioritization (30%) |
| Integration Fit | 20% | Caldera compatibility | Gap Coverage (40%), Schema (30%), Performance (30%) |

### Size Accuracy Judge (35%)

**Purpose**: Validates that blob, tree, and commit size measurements are correct.

**Scoring Rubric**:

| Score | Criteria |
|-------|----------|
| 5 | All measurements within 5% of expected values |
| 4 | Most measurements accurate, minor variations |
| 3 | Generally accurate, some significant variations |
| 2 | Several measurements significantly off |
| 1 | Measurements unreliable or missing |

### Threshold Quality Judge (25%)

**Purpose**: Evaluates appropriateness of threshold-based violation detection.

**Violation Levels**:
- Level 1: Acceptable concern
- Level 2: Somewhat concerning
- Level 3: Very concerning
- Level 4: Alarm bells

### Actionability Judge (20%)

**Purpose**: Assesses whether reports enable developers to take action.

### Integration Fit Judge (20%)

**Purpose**: Evaluates compatibility with Caldera Platform integration.

---

## Running Evaluation

### Programmatic Evaluation

```bash
# Navigate to tool directory
cd src/tools/git-sizer

# Run analysis on synthetic repos
make analyze-all

# Run programmatic evaluation
make evaluate

# Output to JSON
make evaluate OUTPUT=evaluation/results/report.json
```

### LLM Evaluation

```bash
# Run all LLM judges
make evaluate-llm

# Specific model
make evaluate-llm MODEL=sonnet

# Individual judge
make evaluate-llm JUDGE=size_accuracy
```

### Output Locations

| Output Type | Location |
|-------------|----------|
| Analysis results | `output/<run-id>/output.json` |
| Evaluation results | `evaluation/results/<repo>_eval.json` |
| LLM judge results | `evaluation/llm/results/<judge>.json` |
| Scorecard | `evaluation/scorecard.json` |

---

## Rollup Validation

Rollups:

Tests:
- src/sot-engine/dbt/tests/test_rollup_git_sizer_repo_level_only.sql

**Note**: git-sizer provides **repository-level** metrics, not file-level metrics. Therefore:
- No directory rollup validation is applicable
- Metrics are single values per repository run
- No distribution analysis (min/max/avg) needed

This differs from file-level tools like scc, lizard, and semgrep where rollup validation ensures directory aggregates match file sums.

---

## References

- [git-sizer GitHub Repository](https://github.com/github/git-sizer)
- [Git LFS Documentation](https://git-lfs.github.com/)
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685)
