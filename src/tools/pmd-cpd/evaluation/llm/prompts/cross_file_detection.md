# Cross-File Detection Evaluation

You are an expert code quality evaluator assessing PMD CPD's cross-file duplication detection.

## Task
Evaluate how well CPD detects and reports duplicates that span multiple files. Score from 1-5 where:
- 5: Excellent - All cross-file clones detected with clear file relationships
- 4: Good - Most cross-file clones detected with useful linking
- 3: Acceptable - Basic cross-file detection works
- 2: Poor - Misses many cross-file duplicates
- 1: Very Poor - Fails to detect cross-file clones

## Evidence
{{ evidence }}

## Evaluation Criteria

### 1. Detection Rate (40%)
- Are cross_file_a and cross_file_b test files showing expected clones?
- Is the cross_file_clone_count reasonable for the test data?

### 2. File Linking (30%)
- Are the files_involved lists accurate?
- Do occurrences properly identify both source files?

### 3. Reporting Clarity (30%)
- Is it clear which parts of each file are duplicated?
- Would a developer know exactly what to refactor?

## Response Format
Respond with a JSON object:
```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "Your detailed reasoning explaining the score",
  "evidence_cited": ["list of specific evidence points you referenced"],
  "recommendations": ["actionable recommendations for improvement"],
  "sub_scores": {
    "detection_rate": <1-5>,
    "file_linking": <1-5>,
    "reporting_clarity": <1-5>
  }
}
```
