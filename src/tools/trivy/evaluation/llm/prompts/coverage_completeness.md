# Coverage Completeness Evaluation

Evaluate the completeness of the vulnerability scan coverage.

## Evaluation Criteria

1. **Lockfile Detection (40%)**: Were all package manifests found?
2. **Dependency Scanning (30%)**: Were direct and transitive dependencies covered?
3. **IaC Scanning (30%)**: Were infrastructure files scanned?

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | Complete coverage with no gaps |
| 4 | Minor gaps in edge case files |
| 3 | Some lockfiles or IaC files missed |
| 2 | Significant coverage gaps |
| 1 | Critical files not scanned |

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
