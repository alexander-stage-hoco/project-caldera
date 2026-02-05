# False Positive Evaluation

You are evaluating the false positive rate in dotCover's coverage detection.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Focus**: Are "uncovered" lines truly uncovered? Are "covered" lines truly covered?

## Evidence to Review

### Coverage Summary
{{ coverage_summary }}

### Known Covered Code (Ground Truth)
{{ known_covered_code }}

### Reported Coverage Status
{{ reported_coverage }}

### Edge Cases
{{ edge_cases }}

### Anomalies Detected
{{ anomalies }}

## Evaluation Criteria

### Score 5 (Excellent)
- No false positives on verified covered code
- Accurate coverage attribution for all scenarios
- Handles edge cases correctly (generics, async, lambdas)
- Consistent instrumentation results

### Score 4 (Good)
- Rare false positives (< 2% error rate)
- Minor edge case handling issues
- Overall reliable coverage data

### Score 3 (Acceptable)
- Some false positives present (2-5% error rate)
- Known edge case limitations
- Usable but requires verification

### Score 2 (Poor)
- Significant false positives (5-10% error rate)
- Multiple edge case failures
- Coverage data requires manual verification

### Score 1 (Unacceptable)
- Unreliable coverage detection (> 10% error rate)
- Systematic false positives
- Coverage data cannot be trusted

## Response Format

Respond with JSON:
```json
{
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "evidence_cited": ["<specific findings>"],
    "recommendations": ["<improvements>"],
    "sub_scores": {
        "uncovered_line_accuracy": <1-5>,
        "coverage_attribution": <1-5>,
        "edge_case_handling": <1-5>,
        "instrumentation_reliability": <1-5>
    }
}
```
