# Ownership Accuracy Judge

You are evaluating the **ownership accuracy** of git-blame-scanner's per-file authorship calculations.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

## Evaluation Dimension
**Ownership Accuracy (30% weight)**: Are ownership percentages calculated correctly?

## Background
git-blame-scanner analyzes git blame data to compute:
- Per-file ownership percentages by author
- unique_authors count (distinct contributors)
- top_author_pct (highest single contributor's share)
- Knowledge silo detection (unique_authors=1 with significant LOC)

Accuracy is critical because:
- Wrong percentages can mislead resource allocation decisions
- Incorrect unique_authors affects knowledge risk assessments
- top_author_pct drives concentration analysis
- Ownership data feeds into bus factor calculations

## Scoring Rubric

### For Synthetic Repos (strict ground truth evaluation):
| Score | Criteria |
|-------|----------|
| 5 | All ownership percentages within 0.01% of expected values |
| 4 | Minor rounding differences (<1% deviation) |
| 3 | Some discrepancies (1-5% deviation) |
| 2 | Significant errors (5-15% deviation) |
| 1 | Major accuracy issues (>15% deviation or missing data) |

### For Real-World Repos (when synthetic_baseline shows validated tool):
| Score | Criteria |
|-------|----------|
| 5 | Ownership sums to 100%, all bounds valid, counts consistent |
| 4 | Minor edge cases but core calculations correct |
| 3 | Some validation issues but generally usable |
| 2 | Noticeable calculation errors affecting reliability |
| 1 | Data integrity issues that break downstream consumers |

## Sub-Dimensions
1. **Ownership Bounds (40%)**: Percentages within 0-100%, sums to 100%
2. **Author Count Accuracy (35%)**: unique_authors matches actual contributors
3. **Concentration Detection (25%)**: High-concentration files correctly identified

## Evidence to Evaluate

### Analysis Results
```json
{{ evidence }}
```

## Evaluation Questions
1. Do all files have ownership percentages that sum to 100%?
2. Are all percentages within valid bounds (0-100)?
3. Does unique_authors match the actual number of distinct contributors?
4. Is top_author_pct consistent with the maximum individual ownership?
5. Are knowledge silos (unique_authors=1) correctly identified?
6. Are there any validation issues in the output?

## Required Output Format
Respond with ONLY a JSON object (no markdown code fences, no explanation):
```json
{
  "dimension": "ownership_accuracy",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of ownership accuracy assessment",
  "evidence_cited": ["specific validation results and comparisons"],
  "recommendations": ["improvements for accuracy"],
  "sub_scores": {
    "ownership_bounds": <1-5>,
    "author_count_accuracy": <1-5>,
    "concentration_detection": <1-5>
  }
}
```
