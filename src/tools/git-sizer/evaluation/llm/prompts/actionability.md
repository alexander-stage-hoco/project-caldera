# Actionability Judge

You are evaluating the **actionability** of git-sizer's repository health reports.

## Evaluation Dimension
**Actionability (20% weight)**: Can developers easily understand and act on the findings?

## Background
Actionable reports should:
- Clearly identify files that should use Git LFS
- Explain what threshold violations mean
- Provide health grades for quick prioritization
- Enable teams to make informed decisions

Good actionability examples:
- "5 files over 1 MiB identified as LFS candidates"
- "max_blob_size: 10.2 MiB exceeds threshold of 1 MiB (level: ***)"
- "Health Grade: C+ - Large binary files detected"

Poor actionability:
- "Repository has issues"
- "Size: large"

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | Clear LFS recommendations, detailed violations, actionable grades |
| 4 | Good recommendations, clear messages, useful grades |
| 3 | Adequate information, some gaps in clarity |
| 2 | Vague messages, limited actionable information |
| 1 | Unclear findings, no actionable recommendations |

## Sub-Dimensions
1. **LFS Recommendations (40%)**: Clear identification of LFS candidates
2. **Violation Clarity (30%)**: Messages explain issues clearly
3. **Prioritization Support (30%)**: Grades enable quick assessment

## Evidence to Evaluate

### LFS Candidates Summary
```json
{{ lfs_candidates_summary }}
```
- Total LFS candidates identified: {{ total_lfs_candidates }}

### Violation Messages
```json
{{ violation_messages }}
```

### Message Quality Metrics
```json
{{ message_quality }}
```

### Grade Coverage
```json
{{ grade_coverage }}
```
- Repositories with grades: {{ grade_coverage_pct }}%

### Actionable Information
```json
{{ actionable_info }}
```

## Evaluation Questions
1. Are LFS candidates clearly identified with file names/paths?
2. Do violation messages explain what the metric means?
3. Are threshold values and current values both shown?
4. Do health grades help quickly identify problematic repos?

## Required Output Format
Respond with ONLY a JSON object (no markdown code fences, no explanation):
```json
{
  "dimension": "actionability",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of actionability assessment",
  "evidence_cited": ["specific actionable elements examined"],
  "recommendations": ["improvements for actionability"],
  "sub_scores": {
    "lfs_recommendations": <1-5>,
    "violation_clarity": <1-5>,
    "prioritization_support": <1-5>
  }
}
```
