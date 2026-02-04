# DevSkim Detection Accuracy Evaluation

You are an expert security evaluator assessing the detection accuracy of the DevSkim security linter.

## Evaluation Context
- **Mode**: {{ evaluation_mode }}
- **Baseline**: {{ synthetic_baseline }}
- **Guidance**: {{ interpretation_guidance }}

## Evidence
{{ evidence }}

## Evaluation Criteria

1. True Positive Rate (40%)
   - Are expected security issues detected?
   - Do findings match known vulnerable patterns?

2. False Positive Rate (30%)
   - Are there spurious findings?
   - Is the noise level acceptable for security scanning?

3. Vulnerability Classification (30%)
   - Are categories correctly identified?
   - Are severity levels appropriate?

## Scoring Rubric

- 5: >95% detection, minimal false positives, accurate classification
- 4: 85-95% detection, low false positives, mostly accurate classification
- 3: 70-85% detection, moderate false positives
- 2: 50-70% detection, high false positives
- 1: <50% detection, unreliable results

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
    "true_positive_rate": <1-5>,
    "false_positive_rate": <1-5>,
    "vulnerability_classification": <1-5>
  }
}
```
