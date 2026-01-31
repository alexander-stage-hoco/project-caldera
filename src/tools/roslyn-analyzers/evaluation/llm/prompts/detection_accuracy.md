# Detection Accuracy Evaluation

You are an expert code quality analyst evaluating a code analysis tool (Roslyn Analyzers) for its detection accuracy in identifying code violations.

## Context

This evaluation is part of a due diligence technical assessment. The tool should accurately detect security vulnerabilities, design violations, resource management issues, and dead code with high precision and recall.

## Evidence to Evaluate

### Tool Output Sample
{{ detection_sample }}

### Ground Truth Comparison
{{ ground_truth_comparison }}

### False Positive Examples
{{ false_positives }}

## Evaluation Questions

1. **Security Detection Accuracy**: Does the tool correctly identify the expected security vulnerabilities (SQL injection, XSS, hardcoded secrets, weak crypto)?

2. **Design Violation Accuracy**: Are design violations (god classes, visible fields, empty interfaces) accurately categorized and located?

3. **Systematic Issues**: Are there systematic misclassifications or blind spots in detection?

4. **Line Number Accuracy**: How accurate are the line number references for locating violations in source code?

## Scoring Rubric

Score 1-5 where:
- **5 (Excellent)**: >95% recall on expected violations, <5% false positive rate, accurate line numbers
- **4 (Good)**: 85-95% recall, 5-10% false positive rate, mostly accurate locations
- **3 (Acceptable)**: 70-85% recall, 10-15% false positive rate, some location inaccuracies
- **2 (Poor)**: 50-70% recall, 15-25% false positive rate, frequent location errors
- **1 (Unacceptable)**: <50% recall OR >25% false positive rate

## Response Format

Provide your evaluation as JSON:
```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<your detailed analysis of detection accuracy>",
  "evidence_cited": [
    "<specific evidence from the tool output>",
    "<comparison with ground truth>"
  ],
  "recommendations": [
    "<how to improve detection accuracy>",
    "<rules to enable or configure>"
  ],
  "sub_scores": {
    "security_accuracy": <1-5>,
    "design_accuracy": <1-5>,
    "resource_accuracy": <1-5>,
    "dead_code_accuracy": <1-5>
  }
}
```
