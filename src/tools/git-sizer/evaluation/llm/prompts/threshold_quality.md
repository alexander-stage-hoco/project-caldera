# Threshold Quality Judge

You are evaluating the **threshold quality** of git-sizer's violation detection.

## Evaluation Dimension
**Threshold Quality (25% weight)**: Do threshold levels accurately identify problematic repositories?

## Background
git-sizer uses threshold levels to indicate severity:
- `*` - Acceptable (minor concern)
- `**` - Somewhat concerning
- `***` - Very concerning
- `!!!!` - Alarm bells

Good thresholds should:
- Not trigger on healthy repositories (low false positives)
- Correctly flag problematic repositories (high true positives)
- Use appropriate severity levels (not over/under-alarming)
- Result in meaningful health grades (A-F)

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | Perfect threshold accuracy, no false positives/negatives |
| 4 | Excellent thresholds, rare edge case misses |
| 3 | Good thresholds, some calibration issues |
| 2 | Thresholds too aggressive or too lenient |
| 1 | Thresholds unreliable, many misclassifications |

## Sub-Dimensions
1. **True Positive Rate (40%)**: Problematic repos correctly flagged
2. **False Positive Rate (30%)**: Healthy repos not incorrectly flagged
3. **Severity Calibration (30%)**: Levels match actual severity

## Evidence to Evaluate

{{ evidence }}

### Violation Summary
```json
{{ violation_summary }}
```

### Grade Distribution
```json
{{ grade_distribution }}
```

### Expected Outcomes
```json
{{ expected_outcomes }}
```

### Quality Test Results
```json
{{ quality_results }}
```

### Summary
- Tests passed: {{ passed_tests }}/{{ total_tests }}
- Pass rate: {{ pass_rate }}%
- Total violations: {{ total_violations }}

### Violation Level Distribution
```json
{{ level_distribution }}
```

## Evaluation Questions
1. Do healthy repositories correctly have no (or minimal) violations?
2. Are problematic repositories correctly flagged with violations?
3. Are severity levels appropriate for the issues detected?
4. Do health grades accurately reflect repository health?

## Required Output Format
Respond with ONLY a JSON object (no markdown code fences, no explanation):
```json
{
  "dimension": "threshold_quality",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of threshold quality assessment",
  "evidence_cited": ["specific threshold behaviors examined"],
  "recommendations": ["threshold calibration improvements"],
  "sub_scores": {
    "true_positive_rate": <1-5>,
    "false_positive_rate": <1-5>,
    "severity_calibration": <1-5>
  }
}
```
