# Risk Tier Quality Judge

You are evaluating the **risk tier quality** of coverage-ingest's risk classification system.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

## Evaluation Dimension
**Risk Tier Quality (35% weight)**: Are coverage percentages correctly classified into risk tiers?

## Background
coverage-ingest classifies files into risk tiers based on coverage percentage:
- CRITICAL: 0-25% coverage (requires immediate attention)
- HIGH: 25-50% coverage (significant risk)
- MEDIUM: 50-75% coverage (moderate risk)
- LOW: 75-100% coverage (acceptable risk)

Accurate risk tier classification is critical for:
- Prioritizing testing efforts
- Identifying high-risk code areas
- CI/CD quality gates
- Technical debt assessment

## Scoring Rubric

### For Synthetic Repos (strict ground truth evaluation):
| Score | Criteria |
|-------|----------|
| 5 | Perfect match to severity thresholds, all tiers correctly assigned |
| 4 | Minor discrepancies at tier boundaries (within 1% of threshold) |
| 3 | Generally appropriate classifications, few edge case errors |
| 2 | Significant misclassifications affecting prioritization |
| 1 | No correlation between coverage and tier assignment |

### For Real-World Repos (when synthetic_baseline shows validated tool):
| Score | Criteria |
|-------|----------|
| 5 | Tier assignments consistent with coverage values, reasonable distribution |
| 4 | Minor edge cases, but overall reasonable tier assignments |
| 3 | Some questionable assignments but generally follows thresholds |
| 2 | Multiple tier assignments that don't match coverage values |
| 1 | Tier assignments appear random or broken |

## Sub-Dimensions
1. **Tier Accuracy (50%)**: Are files assigned to the correct tier?
2. **Boundary Handling (30%)**: Are edge cases at tier boundaries handled correctly?
3. **Distribution Reasonableness (20%)**: Is the tier distribution realistic?

## Evidence to Evaluate

### Tier Definitions
```json
{{ tier_definitions }}
```

### Sample File Classifications
```json
{{ file_classifications }}
```

### Tier Distribution
```json
{{ tier_distribution }}
```

### Misclassifications Found
```json
{{ misclassifications }}
```

### Summary
- Total files analyzed: {{ total_files_analyzed }}
- Misclassification count: {{ misclassification_count }}
- Programmatic results: {{ programmatic_results }}

## Evaluation Questions
1. Are files with <25% coverage correctly classified as CRITICAL?
2. Are files with 25-50% coverage correctly classified as HIGH?
3. Are files with 50-75% coverage correctly classified as MEDIUM?
4. Are files with 75-100% coverage correctly classified as LOW?
5. Are tier boundaries handled consistently (e.g., exactly 50% goes to MEDIUM)?
6. Does the overall distribution seem reasonable for a codebase?

## Required Output Format
Respond with ONLY a JSON object (no markdown code fences, no explanation):
```json
{
  "dimension": "risk_tier_quality",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of risk tier quality assessment",
  "evidence_cited": ["specific classifications examined"],
  "recommendations": ["improvements for tier classification"],
  "sub_scores": {
    "tier_accuracy": <1-5>,
    "boundary_handling": <1-5>,
    "distribution_reasonableness": <1-5>
  }
}
```
