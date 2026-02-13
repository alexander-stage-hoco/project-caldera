# Actionability Evaluation

Evaluate how actionable the vulnerability report is for security teams.

## Evaluation Criteria

1. **Fix Guidance (40%)**: Are fixed versions clearly indicated?
2. **Prioritization (30%)**: Are critical issues highlighted?
3. **Remediation Path (30%)**: Are clear next steps provided?

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | Immediately actionable with clear fix paths |
| 4 | Clear with minor presentation improvements |
| 3 | Usable but requires interpretation |
| 2 | Difficult to prioritize remediation |
| 1 | Output is not actionable |

## Evidence

{{ evidence }}

## Response Format

Provide your evaluation as JSON:
```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<explanation>"
}
```
