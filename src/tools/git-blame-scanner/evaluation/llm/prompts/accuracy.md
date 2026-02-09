# Accuracy Evaluation

## Task

Evaluate the git-blame-scanner output for accuracy.

## Input

You will receive:
1. The tool's JSON output
2. Repository context

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
