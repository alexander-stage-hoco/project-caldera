# Hotspot Ranking Judge

You are evaluating the **hotspot identification quality** of Lizard function analysis.

## Evaluation Dimension
**Hotspot Ranking (20% weight)**: Are high-complexity functions correctly identified and ranked as refactoring candidates?

## Background

### What is a Hotspot?
A "hotspot" is a function that may need attention due to high complexity. Hotspots are potential refactoring targets.

### Complexity Thresholds
| CCN Range | Interpretation |
|-----------|---------------|
| 1-5 | Low complexity, easily testable |
| 6-10 | Moderate complexity, needs review |
| 11-20 | High complexity, consider refactoring |
| 21+ | Very high complexity, should be refactored |

### Multi-Dimensional Hotspots
Functions can be hotspots for multiple reasons:
- **High CCN**: Complex control flow
- **High NLOC**: Large function size (>50 lines concerning, >100 critical)
- **Many parameters**: >4 parameters is a code smell

### Directory-Level Hotspots
Complexity can concentrate in certain directories:
- High average CCN across a directory
- Many functions over threshold in one area
- Total CCN accumulation

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | Hotspots correctly ranked, thresholds accurate, directory-level patterns visible |
| 4 | Minor ranking issues, thresholds mostly correct |
| 3 | Major hotspots identified, some ranking/threshold inconsistencies |
| 2 | Hotspot identification is incomplete or significantly inconsistent |
| 1 | Hotspot identification is unreliable |

## Sub-Dimensions

1. **CCN Hotspots (40%)**
   - Functions ranked correctly by CCN
   - Highest CCN functions at top
   - Threshold counts match distribution data

2. **Multi-Metric Analysis (30%)**
   - NLOC hotspots identified
   - Parameter-heavy functions flagged
   - Correlation between metrics considered

3. **Directory-Level (30%)**
   - Directories ranked by complexity concentration
   - Over-threshold counts per directory
   - Recursive vs direct stats meaningful

## Evidence to Evaluate

### Top Functions by CCN (Primary Hotspots)
```json
{{ top_functions_by_ccn }}
```

### Top Functions by NLOC (Size Hotspots)
```json
{{ top_functions_by_nloc }}
```

### Top Functions by Parameters (API Hotspots)
```json
{{ top_functions_by_params }}
```

### Threshold Violations
- Functions with CCN > 10: {{ functions_over_10 }}
- Functions with CCN > 20: {{ functions_over_20 }}
- Total functions analyzed: {{ total_functions }}

### CCN Distribution Reference
- Maximum CCN in codebase: {{ max_ccn_overall }}
- 95th percentile CCN: {{ p95_ccn }}

Distribution details:
```json
{{ ccn_distribution }}
```

### Directory-Level Hotspots
```json
{{ directory_hotspots }}
```

## Evaluation Questions

1. **Ranking accuracy**: Are the highest-CCN functions actually at the top of the hotspot list?
   - Cross-check: max CCN in distribution should match top function's CCN

2. **Threshold consistency**: Do the threshold counts (over 10, over 20) match what you'd expect from the distribution?
   - If max is 26 and p95 is 8, there should be relatively few functions over 20

3. **Multi-metric correlation**: Is there overlap between CCN hotspots and NLOC hotspots?
   - High-CCN functions often (but not always) have high NLOC

4. **Directory patterns**: Do directory hotspots show meaningful concentration?
   - Some directories should have higher total CCN than others
   - Recursive stats should be >= direct stats

5. **Actionability**: Would this hotspot list help prioritize refactoring?
   - Clear ranking from most to least complex
   - Mix of metrics for comprehensive view

## Required Output Format

Respond with ONLY a valid JSON object (no markdown code blocks, no extra text):

```json
{
  "dimension": "hotspot_ranking",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "Detailed explanation of hotspot identification quality, citing specific examples",
  "evidence_cited": [
    "Example: Top function X with CCN=26 matches distribution max",
    "Threshold count of Y functions over 10 is consistent with p90",
    "Directory Z shows highest complexity concentration"
  ],
  "recommendations": [
    "Specific improvement suggestion 1",
    "Specific improvement suggestion 2"
  ],
  "sub_scores": {
    "ccn_hotspots": <1-5>,
    "multi_metric": <1-5>,
    "directory_level": <1-5>
  }
}
```
