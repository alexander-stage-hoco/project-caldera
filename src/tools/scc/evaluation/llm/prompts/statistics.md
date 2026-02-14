# Statistics Quality Judge

You are evaluating the **distribution statistics and hotspot detection** quality.

## Evaluation Dimension

**Distribution Statistics Quality (14% weight)**: How useful are the distribution statistics for spotting outliers and hotspots?

## Required Distribution Fields

For each metric, the distribution should include:
- `min`, `max` - Range bounds
- `mean`, `median` - Central tendency
- `stddev` - Spread measure
- `p25`, `p75` - Interquartile range
- `p90`, `p95` - Tail percentiles
- `skewness` - Distribution shape (positive = right-skewed, heavy tail)
- `kurtosis` - Tail weight (high = more outliers)

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | Full distribution stats for each metric; hotspot scores well-calibrated (0-1); distribution shapes identify outliers via skewness/kurtosis |
| 4 | Most distribution fields present; hotspot detection works for obvious cases; percentiles useful |
| 3 | Basic stats (min, max, mean) present; hotspot detection has false positives/negatives |
| 2 | Incomplete stats; hotspot scores unreliable |
| 1 | No meaningful distribution analysis |

## Sub-Dimensions

### 1. Completeness (30%)
- All 11 distribution fields present (min, max, mean, median, stddev, p25, p75, p90, p95, skewness, kurtosis)
- Multiple metrics have distributions (LOC, complexity, comments)
- Distributions computed for directories with sufficient files (>= 3)

### 2. Accuracy (25%)
- Percentiles are monotonic: p25 <= median <= p75 <= p90 <= p95
- Mean is within [min, max]
- Stddev is non-negative
- Skewness and kurtosis are mathematically valid

### 3. Hotspot Calibration (25%)
- Scores are in [0, 1] range
- High-complexity directories have higher scores
- Low-complexity directories have lower scores
- The threshold (0.7) correctly separates hotspots from non-hotspots

### 4. Interpretability (20%)
- Distribution shapes (via skewness) identify heavy-tailed distributions
- High kurtosis flags outlier-prone directories
- Statistics are useful for due diligence decisions

## Evidence to Evaluate

{{ evidence }}

### Distribution Statistics Sample
```json
{{ distribution_sample }}
```

### Hotspot Scores
```json
{{ hotspot_scores }}
```

### Statistical Validation Results
- All percentiles monotonic: {{ percentiles_valid }}
- All means in range: {{ means_valid }}
- All stddevs non-negative: {{ stddevs_valid }}
- All hotspot scores in [0,1]: {{ hotspots_valid }}

## Evaluation Questions

1. Are all 11 distribution fields present for metrics with sufficient data?
2. Are percentiles monotonic (p25 <= p50 <= p75 <= p90 <= p95)?
3. Do skewness values correctly identify right-skewed (heavy-tailed) distributions?
4. Are hotspot scores calibrated (high complexity = high score)?
5. Would these statistics be useful for identifying outlier files and directories?

## Evaluation Approach

Use the pre-computed validation results (lines 67-70) as quick pass/fail signals. Focus on the sample data provided rather than exploring files. Provide your JSON response directly.

## Required Output Format

```json
{
  "dimension": "statistics",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific stats or directories>"],
  "recommendations": ["<improvements for statistics>"],
  "sub_scores": {
    "completeness": <1-5>,
    "accuracy": <1-5>,
    "hotspot_calibration": <1-5>,
    "interpretability": <1-5>
  }
}
```
