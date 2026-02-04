# DevSkim Severity Calibration Evaluation

You are an expert security evaluator assessing severity calibration for DevSkim findings.

## Evidence
{{ evidence }}

## Evaluation Criteria

1. Severity Appropriateness (40%)
   - Are high-impact issues marked critical/high?
   - Are low-impact issues marked low?

2. Consistency (30%)
   - Are similar findings rated consistently?

3. Industry Alignment (30%)
   - Does severity match common security conventions?

## Scoring Rubric

- 5: Severities consistently accurate and aligned
- 4: Minor calibration issues
- 3: Some misclassification, acceptable distribution
- 2: Frequent misclassification
- 1: Unreliable severity ratings

## Required Output

Provide your evaluation as a JSON object:
```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "severity_appropriateness": <1-5>,
    "consistency": <1-5>,
    "industry_alignment": <1-5>
  }
}
```
