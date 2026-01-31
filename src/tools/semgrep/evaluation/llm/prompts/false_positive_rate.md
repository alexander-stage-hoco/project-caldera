# False Positive Rate Evaluation

You are an expert code quality analyst evaluating Semgrep's false positive rate for code smell detection in due diligence contexts.

## Context

This evaluation assesses whether Semgrep produces reliable results suitable for due diligence reporting. High false positive rates reduce confidence in findings and increase review burden. The tool should distinguish actual code smells from acceptable patterns.

## Evidence

The following JSON contains clean file analysis, safe pattern detection results, and borderline cases:

{{ evidence }}

## Evaluation Questions

1. **Clean File Analysis**: How many smells are reported on known-clean files?
   - Files explicitly designed to have no smells
   - False positives represent definite errors

2. **Safe Pattern Recognition**: Does the tool distinguish safe patterns from smells?
   - Async void event handlers (acceptable) vs async void methods (smell)
   - Factory pattern HttpClient (acceptable) vs method-level new HttpClient (smell)
   - Intentional lock(this) in specific contexts vs general anti-pattern
   - Null-forgiving in validated contexts vs overuse

3. **Contextual Understanding**: Does Semgrep understand code context?
   - Constructor vs method for dependency injection detection
   - Event unsubscription presence for F6 detection
   - StringBuilder usage vs string concatenation

4. **Systematic False Positives**: Are there patterns in false positives?
   - Specific rules that consistently over-report
   - Language features misinterpreted as smells
   - Patterns Semgrep cannot distinguish

## Scoring Rubric

Score 1-5 where:
- **5 (Excellent)**: <5% false positive rate, no systematic FP patterns, clear safe pattern recognition
- **4 (Good)**: 5-10% false positive rate, rare FP patterns, good contextual understanding
- **3 (Acceptable)**: 10-15% false positive rate, some FP patterns identifiable
- **2 (Poor)**: 15-25% false positive rate, systematic FP patterns present
- **1 (Unacceptable)**: >25% false positive rate, unreliable for due diligence

## Response Format

Respond ONLY with valid JSON (no markdown, no explanation before or after):
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
    "<rules to tune or add exceptions>",
    "<patterns to exclude from detection>"
  ],
  "sub_scores": {
    "clean_file_analysis": <1-5>,
    "contextual_understanding": <1-5>,
    "safe_pattern_recognition": <1-5>
  }
}
```
