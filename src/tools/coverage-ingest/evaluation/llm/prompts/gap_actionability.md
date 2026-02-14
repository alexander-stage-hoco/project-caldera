# Gap Analysis Actionability Judge

You are evaluating the **actionability** of coverage-ingest's gap analysis output.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

## Evaluation Dimension
**Gap Actionability (35% weight)**: Do coverage gap findings enable immediate developer action?

## Background
Actionable coverage gap analysis should:
- Clearly identify files with lowest coverage
- Provide specific, locatable file paths
- Include precise line/branch counts
- Prioritize gaps by severity
- Enable developers to take immediate action

Good actionability means a developer can:
1. Open the exact file with a coverage gap
2. See exactly how many lines need tests
3. Prioritize which files to address first
4. Track progress as coverage improves

## Scoring Rubric

### For Synthetic Repos (strict ground truth evaluation):
| Score | Criteria |
|-------|----------|
| 5 | Highly actionable with clear priorities, specific paths, precise metrics |
| 4 | Actionable with minor gaps in detail or prioritization |
| 3 | Somewhat actionable but requires additional investigation |
| 2 | Limited actionability due to vague paths or missing metrics |
| 1 | Not actionable - cannot determine where to add tests |

### For Real-World Repos (when synthetic_baseline shows validated tool):
| Score | Criteria |
|-------|----------|
| 5 | Output clearly shows what files need tests, with precise metrics |
| 4 | Most files have actionable data, minor gaps in some areas |
| 3 | Generally actionable but some files lack detail |
| 2 | Significant gaps in actionability for many files |
| 1 | Cannot determine action items from output |

## Sub-Dimensions
1. **Gap Clarity (40%)**: Are coverage gaps clearly identified and ranked?
2. **Path Specificity (30%)**: Are file paths specific enough to locate?
3. **Metric Precision (30%)**: Are line/branch counts precise and accurate?

## Evidence to Evaluate

{{ evidence }}

### Top Coverage Gaps (Lowest Coverage Files)
```json
{{ top_coverage_gaps }}
```

### Actionability Metrics
```json
{{ actionability_metrics }}
```

### Gap Distribution
```json
{{ gap_distribution }}
```

### Branch Coverage Gaps
```json
{{ branch_gap_analysis }}
```

### Summary
- Total files analyzed: {{ total_files_analyzed }}
- Actionability score: {{ actionability_score }}%
- Programmatic results: {{ programmatic_results }}

## Evaluation Questions
1. Can a developer immediately locate the files with lowest coverage?
2. Are the line counts specific enough to know the scope of work?
3. Are files prioritized by coverage gap severity (CRITICAL first)?
4. Is branch coverage tracked where relevant for complex logic?
5. Can progress be measured as tests are added?
6. Are there any files with missing or incomplete metrics?

## Required Output Format
Respond with ONLY a JSON object (no markdown code fences, no explanation):
```json
{
  "dimension": "gap_actionability",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of gap actionability assessment",
  "evidence_cited": ["specific gaps and paths examined"],
  "recommendations": ["improvements for actionability"],
  "sub_scores": {
    "gap_clarity": <1-5>,
    "path_specificity": <1-5>,
    "metric_precision": <1-5>
  }
}
```
