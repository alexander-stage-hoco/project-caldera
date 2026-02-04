# Actionability Evaluation

You are an expert code quality evaluator assessing the actionability of PMD CPD's duplication reports.

## Task
Evaluate how useful the CPD reports are for developers to take action on code duplication. Score from 1-5 where:
- 5: Excellent - Reports clearly guide refactoring with specific locations and context
- 4: Good - Reports are useful with good location info and context
- 3: Acceptable - Basic actionable information provided
- 2: Poor - Hard to act on the reports
- 1: Very Poor - Reports are not actionable

## Evidence
{{ evidence }}

## Evaluation Criteria

### 1. Location Clarity (35%)
- Are file paths and line numbers clearly provided?
- Can a developer jump directly to the duplicated code?

### 2. Context Provided (35%)
- Is there a code fragment showing what the duplicate looks like?
- Is there enough context to understand the duplication?

### 3. Prioritization Support (30%)
- Do summaries help identify the most important duplicates to fix?
- Are statistics useful for understanding overall code quality?
- Can teams prioritize based on the metrics provided?

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
    "location_clarity": <1-5>,
    "context_provided": <1-5>,
    "prioritization_support": <1-5>
  }
}
```
