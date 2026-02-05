# Coverage Actionability Evaluation

You are evaluating how actionable the dotCover coverage output is for improving test coverage.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Focus**: Does the output help developers identify WHERE to add tests?

## Evidence to Review

### Coverage Summary
{{ coverage_summary }}

### Low Coverage Methods (< 50%)
{{ low_coverage_methods }}

### Uncovered Types
{{ uncovered_types }}

### Coverage Distribution
{{ coverage_distribution }}

### Ground Truth Expected Findings
{{ ground_truth_findings }}

## Evaluation Criteria

### Score 5 (Excellent)
- Clearly identifies all methods with < 50% coverage
- Provides specific type/method names for targeting
- Coverage data enables prioritization by impact
- Easy to identify "quick wins" for coverage improvement

### Score 4 (Good)
- Identifies most low-coverage areas
- Type/method granularity allows targeted testing
- Coverage percentages enable comparison

### Score 3 (Acceptable)
- Basic identification of uncovered areas
- Some granularity for test targeting
- Percentages present but limited context

### Score 2 (Poor)
- Limited identification of problem areas
- Too coarse-grained for actionable testing
- Missing key coverage gaps

### Score 1 (Unacceptable)
- No useful information for test improvement
- Cannot identify where tests are needed
- Data too aggregated or missing

## Response Format

Respond with JSON:
```json
{
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "evidence_cited": ["<specific findings>"],
    "recommendations": ["<improvements>"],
    "sub_scores": {
        "low_coverage_identification": <1-5>,
        "uncovered_detection": <1-5>,
        "priority_ranking": <1-5>,
        "improvement_guidance": <1-5>
    }
}
```
