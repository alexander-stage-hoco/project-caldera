# Smell Detection Accuracy Evaluation

You are an expert code quality analyst evaluating Semgrep as a code smell detection tool for due diligence technical assessments.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Low smell counts are NOT automatically failures
- Judge output quality: schema compliance, rule ID completeness, category mapping
- Judge detection quality: Are the smells that WERE detected accurate and well-categorized?
- Consider: A tool that finds 0 smells in a clean repo with proper output format deserves a high score

## Context

This evaluation measures precision and recall for code smell detection. The tool should accurately identify smells across multiple categories: async/concurrency issues, resource management problems, nullability concerns, API design flaws, and refactoring indicators.

## Evidence

The following JSON contains analysis results including detected smells, ground truth comparisons, and per-category breakdowns:

{{ evidence }}

## Evaluation Questions

1. **Async/Concurrency Accuracy**: Does the tool correctly identify async issues?
   - E1: Sync over async (.Result, .Wait())
   - E2: Async void methods
   - E4: Missing CancellationToken
   - E5: Unsafe lock patterns (lock(this), lock(typeof))
   - E7: Async without await

2. **Resource Management Accuracy**: Are resource issues accurately detected?
   - F3: HttpClient instantiation in methods
   - F5: Disposable fields without proper disposal
   - F6: Event handler leak patterns

3. **Nullability Accuracy**: Are nullability smells identified?
   - G1: Nullable reference types disabled (#nullable disable)
   - G2: Null-forgiving operator overuse (!)
   - G3: Inconsistent nullable annotations

4. **Line Number Accuracy**: How accurate are the line number references?

5. **Systematic Gaps**: Are there smell categories with systematically low detection rates?

## Scoring Rubric

### For Synthetic Repos (with ground truth):
Score 1-5 where:
- **5 (Excellent)**: >90% recall on expected smells, <5% false positive rate, accurate line numbers
- **4 (Good)**: 80-90% recall, 5-10% false positive rate, mostly accurate locations
- **3 (Acceptable)**: 65-80% recall, 10-15% false positive rate, some location inaccuracies
- **2 (Poor)**: 50-65% recall, 15-25% false positive rate, frequent location errors
- **1 (Unacceptable)**: <50% recall OR >25% false positive rate

### For Real-World Repos (when synthetic_baseline shows validated tool):
- **5 (Excellent)**: Output schema compliant, any smells are accurately categorized, metadata complete
- **4 (Good)**: Minor schema issues but smells accurate, good categorization
- **3 (Acceptable)**: Schema issues OR questionable smell categorization
- **2 (Poor)**: Multiple schema issues AND questionable categorization
- **1 (Failing)**: Broken output, missing required fields, obvious false positives

**Key principle**: Do NOT penalize for low smell counts on real-world repos when the tool is validated (synthetic_score >= 0.9). A clean codebase with well-formed output deserves a high score.

## Response Format

Respond ONLY with valid JSON (no markdown, no explanation before or after):
```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<your detailed analysis of smell detection accuracy>",
  "evidence_cited": [
    "<specific evidence from the tool output>",
    "<comparison with ground truth>"
  ],
  "recommendations": [
    "<how to improve detection accuracy>",
    "<rules to add or modify>"
  ],
  "sub_scores": {
    "async_concurrency_accuracy": <1-5>,
    "resource_management_accuracy": <1-5>,
    "nullability_accuracy": <1-5>,
    "api_design_accuracy": <1-5>,
    "refactoring_accuracy": <1-5>
  }
}
```
