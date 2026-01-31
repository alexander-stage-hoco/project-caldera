# Resource Management Evaluation

You are evaluating the resource management and disposal detection capabilities of Roslyn Analyzers.

## Context

This evaluation focuses on how well the analyzers detect resource management issues:
- Undisposed objects (CA2000)
- Missing IDisposable implementation (CA1001)
- Improper dispose pattern (CA1063)
- Missing cancellation token forwarding (CA2016)
- Async void methods (ASYNC0001)
- IDisposableAnalyzers rules (IDISP001, IDISP006)

## Evidence

### Programmatic Evaluation Results
{{ evaluation_results }}

### Resource-Related Checks
{{ resource_checks }}

### Ground Truth Resource Expectations
{{ ground_truth_resource }}

## Evaluation Criteria

Score each sub-dimension from 1-5:

1. **Disposal Detection** (weight: 35%)
   - Are undisposed IDisposable objects flagged?
   - Are using statements recognized as safe?

2. **IDisposable Implementation** (weight: 25%)
   - Are missing IDisposable implementations detected?
   - Is the dispose pattern correctly validated?

3. **Async Patterns** (weight: 20%)
   - Are async void methods flagged?
   - Is cancellation token forwarding checked?

4. **Resource Leak Prevention** (weight: 20%)
   - Are potential resource leaks identified?
   - Are safe disposal patterns recognized?

## Response Format

Respond with a JSON object:

```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "sub_scores": {
    "disposal_detection": <1-5>,
    "idisposable_impl": <1-5>,
    "async_patterns": <1-5>,
    "leak_prevention": <1-5>
  },
  "evidence_cited": ["<specific findings from the data>"],
  "recommendations": ["<actionable improvements>"]
}
```

## Scoring Guide

- **5**: Excellent - All resource issues detected, zero leaks missed
- **4**: Good - >90% detection, proper using/dispose recognition
- **3**: Adequate - >80% detection, some edge cases missed
- **2**: Poor - Significant resource issues missed
- **1**: Failing - Resource management analysis broken
