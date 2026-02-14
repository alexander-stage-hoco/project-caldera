# Design Analysis Evaluation

You are evaluating the design pattern and code quality detection capabilities of Roslyn Analyzers.

## Context

This evaluation focuses on how well the analyzers detect design issues in C# code:
- Visible instance fields (CA1051)
- Empty interfaces (CA1040)
- Static members in generic types (CA1000)
- Improper inheritance (CA1061)
- Missing accessibility modifiers (IDE0040)
- God classes / high complexity (CA1502, CA1506)

## Evidence

{{ evidence }}

### Programmatic Evaluation Results
{{ evaluation_results }}

### Design-Related Checks
{{ design_checks }}

### Ground Truth Design Expectations
{{ ground_truth_design }}

## Evaluation Criteria

Score each sub-dimension from 1-5:

1. **Encapsulation Violations** (weight: 30%)
   - Are public fields correctly flagged?
   - Are proper accessors recognized?

2. **Interface Design** (weight: 25%)
   - Are empty interfaces detected?
   - Are marker interfaces distinguished?

3. **Inheritance Patterns** (weight: 25%)
   - Are base class conflicts identified?
   - Are virtual/override patterns correct?

4. **Complexity Detection** (weight: 20%)
   - Are god classes identified?
   - Is cyclomatic complexity measured?

## Response Format

Respond with a JSON object:

```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "sub_scores": {
    "encapsulation": <1-5>,
    "interface_design": <1-5>,
    "inheritance": <1-5>,
    "complexity": <1-5>
  },
  "evidence_cited": ["<specific findings from the data>"],
  "recommendations": ["<actionable improvements>"]
}
```

## Scoring Guide

- **5**: Excellent - All design issues detected accurately
- **4**: Good - >90% detection, good precision
- **3**: Adequate - >80% detection, some noise
- **2**: Poor - Missing significant design issues
- **1**: Failing - Design analysis not functional
