# Duplication Accuracy Evaluation

You are an expert code quality evaluator assessing the accuracy of PMD CPD's code duplication detection.

## Context

{{ interpretation_guidance }}

### Synthetic Baseline
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

## Task
Evaluate the accuracy of code clone detection results. Score from 1-5 where:
- 5: Excellent - All detected clones are genuine, no false positives, accurate line counts
- 4: Good - Most clones are genuine with minor inaccuracies
- 3: Acceptable - Some false positives or missed duplicates
- 2: Poor - Significant accuracy issues
- 1: Very Poor - Mostly incorrect results

## Evidence
{{ evidence }}

## Evaluation Criteria

### 1. Genuine Clones (40%)
- Do the detected code fragments represent actual duplicated logic?
- Are the clones meaningful (not trivial patterns like imports)?

### 2. False Positive Rate (30%)
- Are there clones detected that shouldn't be?
- Are clean files (no_duplication) showing unexpected clones?

### 3. Location Accuracy (30%)
- Do the line numbers and file paths look correct?
- Are the token counts proportional to the line counts?

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
    "genuine_clones": <1-5>,
    "false_positive_rate": <1-5>,
    "location_accuracy": <1-5>
  }
}
```
