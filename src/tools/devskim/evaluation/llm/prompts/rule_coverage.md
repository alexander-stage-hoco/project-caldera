# DevSkim Rule Coverage Evaluation

You are an expert security evaluator assessing rule coverage for DevSkim.

## Evidence
{{ evidence }}

## Evaluation Criteria

1. Rule Breadth (35%)
   - Are multiple rules triggered across scenarios?
   - Does coverage span core security categories?

2. Category Coverage (35%)
   - Are major security categories represented?
   - Is the distribution reasonable for the repo mix?

3. Ground Truth Alignment (30%)
   - Do triggered rules align with expected rules?
   - Are expected categories represented?

## Scoring Rubric

- 5: >10 rules, all major categories, >90% alignment
- 4: 7-10 rules, most categories, 70-90% alignment
- 3: 5-7 rules, key categories present, 50-70% alignment
- 2: 3-5 rules, missing important categories, 30-50% alignment
- 1: <3 rules or major gaps, <30% alignment

## Required Output

Provide your evaluation as a JSON object:
```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "rule_breadth": <1-5>,
    "category_coverage": <1-5>,
    "ground_truth_alignment": <1-5>
  }
}
```
