# DevSkim Actionability Evaluation

You are an expert security evaluator assessing the actionability of DevSkim security findings.

## Evidence
{{ evidence }}

## Evaluation Criteria

1. Finding Clarity (35%)
   - Are findings clearly explained?
   - Is the security impact obvious?
   - Can developers understand what to fix?

2. Location Precision (30%)
   - Are file paths accurate?
   - Are line numbers precise?
   - Is the code snippet useful?

3. Fix Guidance (35%)
   - Does the finding suggest a remediation?
   - Is the severity appropriate for prioritization?
   - Are the DD categories meaningful?

## Scoring Rubric

- 5: Findings are immediately actionable with clear fix paths
- 4: Findings are actionable with minor clarification needed
- 3: Findings require investigation to determine fix
- 2: Findings are vague, remediation unclear
- 1: Findings are not actionable

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
    "finding_clarity": <1-5>,
    "location_precision": <1-5>,
    "fix_guidance": <1-5>
  }
}
```
