# Directory Analysis Judge (Schema v2.0)

You are evaluating the **directory tree analysis** capabilities of scc output.

## Evaluation Dimension

**Directory Tree Analysis (14% weight)**: How well does the directory analysis capture file organization and provide useful rollups?

## Critical Distinction

The directory analysis provides TWO types of statistics for each directory:

1. **Direct Stats** (`direct`): Files ONLY in that specific directory (not subdirectories)
2. **Recursive Stats** (`recursive`): ALL files in the directory tree starting at that directory

This distinction is critical for understanding codebase organization:
- **Direct**: "How much code is directly in src/utils?"
- **Recursive**: "How much total code is under src/utils including all subdirectories?"

## Schema v2.0 Features

### 22 Distribution Metrics
Each distribution object now includes:
- Basic: min, max, mean, median, stddev, p25, p75, p90, p95, **p99**
- Shape: skewness, kurtosis, cv, iqr
- **Inequality (NEW)**: gini, theil, hoover, palma, top_10_pct_share, top_20_pct_share, bottom_50_pct_share

### File Classifications
Files are classified into: test, config, docs, build, ci, source (null)
- `test_file_count + config_file_count + docs_file_count + build_file_count + ci_file_count + source_file_count == total_files`

### Per-Language Breakdown
`by_language` provides stats for each language:
- `sum(by_language.*.lines_code) == total_loc`

### Structural Metrics
Each directory has: `is_leaf`, `child_count`, `depth`
- `is_leaf == (child_count == 0)` must be consistent

### 8 COCOMO Presets
`summary.cocomo` contains all 8 presets:
- Effort ordering: early_startup < growth_startup < scale_up < sme < mid_market < large_enterprise < regulated
- `open_source.cost == 0`

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | All 22 distribution fields valid; inequality metrics in range; file classifications sum correctly; per-language breakdown consistent; COCOMO ordering correct; structural metrics valid |
| 4 | Stats mostly accurate; minor issues in edge cases; useful for directory-level analysis |
| 3 | Basic stats present but some v2.0 features missing or inconsistent |
| 2 | Significant aggregation errors; missing key v2.0 metrics |
| 1 | Unusable for directory analysis |

## Sub-Dimensions (5 total)

### 1. Structural Integrity (25%)
- JSON schema is correct
- All directories in hierarchy are present with `is_leaf`, `child_count`, `depth`
- `is_leaf == (child_count == 0)` for all directories
- All 7 summary sections present: structure, ratios, file_classifications, languages, distributions, by_language, cocomo

### 2. Statistical Validity (25%)
- All 22 distribution fields present (including p99 and 7 inequality metrics)
- Distribution percentiles are monotonic (p25 <= median <= p75 <= p90 <= p95 <= p99 <= max)
- Inequality metrics in valid ranges:
  - gini: [0, 1]
  - theil: >= 0
  - hoover: [0, 1]
  - palma: >= 0
  - shares: [0, 1]
- Mean is within [min, max] range
- Stddev is non-negative

### 3. Aggregation Correctness (20%)
- recursive.file_count >= direct.file_count for all directories
- sum(all direct.file_count) == total_files
- recursive.lines_code >= direct.lines_code
- **sum(by_language.*.lines_code) == total_loc**

### 4. Classification Accuracy (15%) - NEW
- File classifications sum: test + config + docs + build + ci + source == total_files
- test_loc matches sum of LOC in test-classified files
- Classification patterns correctly identify test files (test_*.py, *.spec.ts), config files (*.yaml), etc.

### 5. Output Interpretability (15%)
- Summary is clear and actionable
- COCOMO presets follow ordering (effort increases with org size)
- open_source.cost == 0
- All 8 COCOMO presets present
- Metrics are useful for downstream analysis

## Evidence to Evaluate

### Directory Analysis Output
```json
{{ directory_analysis }}
```

### Key Invariants to Check
1. Sum of direct file counts should equal total files: {{ sum_direct_files }} == {{ total_files }}
2. All recursive >= direct: {{ recursive_gte_direct }}
3. All computed ratios valid (non-negative): {{ computed_ratios_valid }}
4. Percentile monotonicity (including p99): {{ percentiles_monotonic }}
5. **Inequality metrics in range**: {{ inequality_metrics_valid }}
6. **Classification sum matches**: {{ classification_sum_matches }}
7. **Language LOC sum matches**: {{ lang_loc_sum_matches }}
8. **COCOMO ordering correct**: {{ cocomo_ordered }}

## Evaluation Questions

1. Are direct and recursive stats clearly separated for each directory?
2. Do the file counts roll up correctly (recursive >= direct)?
3. Are all 22 distribution fields present and valid (including inequality metrics)?
4. Are inequality metrics (gini, theil, hoover, palma, shares) in valid ranges?
5. Do file classification counts sum to total_files?
6. Does per-language LOC sum match total_loc?
7. Are COCOMO presets correctly ordered (startup < sme < enterprise)?
8. Are structural metrics consistent (is_leaf iff child_count == 0)?

## Evaluation Approach

Focus on the pre-computed invariants (lines 101-108) first - these provide quick pass/fail signals. If invariants pass, score based on the rubric. Provide your JSON response directly without extensive exploration.

## Required Output Format

```json
{
  "dimension": "directory_analysis",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific directories or stats>"],
  "recommendations": ["<improvements for directory analysis>"],
  "sub_scores": {
    "structural_integrity": <1-5>,
    "statistical_validity": <1-5>,
    "aggregation_correctness": <1-5>,
    "classification_accuracy": <1-5>,
    "output_interpretability": <1-5>
  }
}
```
