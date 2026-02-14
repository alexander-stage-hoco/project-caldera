# Actionability Evaluation

## Task

Evaluate the dependensee output for actionability.

## Input

You will receive:
1. The tool's JSON output
2. Repository context

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:
- 5: Excellent
- 4: Good
- 3: Acceptable
- 2: Poor
- 1: Unacceptable

## Output Format

Respond with:
```json
{
  "score": <1-5>,
  "verdict": "PASS" | "FAIL",
  "reasoning": "<explanation>"
}
```
