# Overall Quality Evaluation

You are evaluating the overall quality and reliability of the Roslyn Analyzers evaluation framework.

## Context

This evaluation assesses the holistic quality of the analysis:
- False positive rate on clean code
- Line-level precision of detections
- Category coverage completeness
- Performance characteristics
- Edge case handling

## Evidence

### Programmatic Evaluation Summary
{{ evaluation_summary }}

### Category Scores
{{ category_scores }}

### Edge Case Results
{{ edge_case_results }}

### Performance Metrics
{{ performance_metrics }}

## Evaluation Criteria

Score each sub-dimension from 1-5:

1. **False Positive Control** (weight: 30%)
   - What is the false positive rate on clean files?
   - Are clean patterns correctly recognized?

2. **Detection Precision** (weight: 25%)
   - Do violations have accurate line numbers?
   - Are rule IDs correctly mapped?

3. **Coverage Completeness** (weight: 25%)
   - Are all DD categories covered?
   - What percentage of expected rules trigger?

4. **Robustness** (weight: 20%)
   - Does analysis handle edge cases?
   - Is performance acceptable?

## Response Format

Respond with a JSON object:

```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "sub_scores": {
    "false_positive_control": <1-5>,
    "detection_precision": <1-5>,
    "coverage_completeness": <1-5>,
    "robustness": <1-5>
  },
  "evidence_cited": ["<specific findings from the data>"],
  "recommendations": ["<actionable improvements>"]
}
```

## Scoring Guide

- **5**: Excellent - 100% precision, full coverage, fast performance
- **4**: Good - >95% precision, good coverage, acceptable performance
- **3**: Adequate - >90% precision, most categories covered
- **2**: Poor - Significant precision or coverage gaps
- **1**: Failing - Unreliable analysis results
