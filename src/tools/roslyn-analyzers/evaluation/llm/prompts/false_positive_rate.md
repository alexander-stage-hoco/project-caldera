# False Positive Rate Evaluation

You are an expert code quality analyst evaluating a code analysis tool (Roslyn Analyzers) for its false positive rate and signal-to-noise ratio.

## Context

This evaluation assesses whether the tool produces reliable results suitable for due diligence reporting. High false positive rates reduce confidence in findings and increase review burden.

## Evidence to Evaluate

### Clean File Results
{{ clean_file_violations }}

### Safe Pattern Detection
{{ safe_pattern_results }}

### Confidence Distribution
{{ confidence_scores }}

## Evaluation Questions

1. **Clean File Analysis**: How many violations are reported on known-clean files? These represent definite false positives.

2. **Safe Pattern Recognition**: Does the tool distinguish safe patterns from vulnerabilities?
   - Parameterized SQL queries vs string concatenation
   - Encoded output vs raw output
   - Properly disposed resources vs leaks

3. **Systematic False Positives**: Are there systematic patterns in false positives?
   - Specific rules that consistently over-report
   - Context-insensitive detection

4. **Signal-to-Noise Ratio**: What is the noise level for due diligence reporting?
   - Can results be trusted without extensive manual review?

## Scoring Rubric

Score 1-5 where:
- **5 (Excellent)**: <2% false positive rate, no systematic FP patterns, clear safe pattern recognition
- **4 (Good)**: 2-5% false positive rate, rare FP patterns, good contextual understanding
- **3 (Acceptable)**: 5-10% false positive rate, some FP patterns identifiable
- **2 (Poor)**: 10-20% false positive rate, systematic FP patterns present
- **1 (Unacceptable)**: >20% false positive rate, unreliable for due diligence

## Response Format

Provide your evaluation as JSON:
```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<your detailed analysis of false positive rate>",
  "evidence_cited": [
    "<violations on clean files>",
    "<safe patterns incorrectly flagged>"
  ],
  "recommendations": [
    "<rules to tune or suppress>",
    "<configuration to reduce FP rate>"
  ],
  "sub_scores": {
    "clean_file_analysis": <1-5>,
    "contextual_understanding": <1-5>,
    "safe_pattern_recognition": <1-5>
  }
}
```
