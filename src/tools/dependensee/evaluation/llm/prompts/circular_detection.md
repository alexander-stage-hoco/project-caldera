# Circular Dependency Detection Evaluation

## Task

Evaluate DependenSee's ability to detect circular dependencies between projects.

## Evidence

- Total cycles detected: {total_cycles}
- Cycles: {cycles}

## Evaluation Criteria

Rate on a scale of 0.0-1.0:

1. **Detection** (50%): Are circular dependencies found?
   - 1.0: All circular dependencies in the project correctly identified
   - 0.5: Some cycles found but not all
   - 0.0: Circular dependencies missed

2. **Accuracy** (30%): Are detected cycles real?
   - 1.0: No false positives - all reported cycles are real
   - 0.5: Some false positives
   - 0.0: Many false positives

3. **Reporting** (20%): Are cycles clearly reported?
   - 1.0: Full cycle path provided (A -> B -> C -> A)
   - 0.5: Partial information
   - 0.0: Minimal information

## Output Format

Respond with:
```json
{
  "score": <0.0-1.0>,
  "verdict": "PASS" | "FAIL",
  "reasoning": "<explanation>"
}
```
