# Parser Accuracy Judge

You are evaluating the **parser accuracy** of coverage-ingest's format parsers.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

## Evaluation Dimension
**Parser Accuracy (35% weight)**: Are coverage metrics parsed correctly from each format?

## Background
coverage-ingest parses coverage data from 4 formats:
- LCOV: Line-oriented text format (SF:, LF:, LH:, BRF:, BRH:)
- Cobertura: XML format with line-rate/branch-rate attributes
- JaCoCo: XML format with LINE/BRANCH counters
- Istanbul: JSON format with statement/branch maps

Accurate parsing is critical for:
- Correct coverage percentage calculations
- Reliable risk tier classification
- Cross-format consistency
- CI/CD quality gates

## Scoring Rubric

### For Synthetic Repos (strict ground truth evaluation):
| Score | Criteria |
|-------|----------|
| 5 | >= 99% accuracy across all 4 formats, all metrics correct |
| 4 | >= 95% accuracy, minor discrepancies in edge cases |
| 3 | >= 85% accuracy, some systematic errors in one format |
| 2 | >= 70% accuracy, significant parsing issues |
| 1 | < 70% accuracy, fundamental parsing problems |

### For Real-World Repos (when synthetic_baseline shows validated tool):
| Score | Criteria |
|-------|----------|
| 5 | Metrics consistent and reasonable, all formats parse without error |
| 4 | Minor inconsistencies, but overall reasonable values |
| 3 | Some questionable values but formats parse correctly |
| 2 | Multiple parsing issues or inconsistent metrics |
| 1 | Parsing appears broken or produces invalid data |

## Sub-Dimensions
1. **Line Metric Accuracy (40%)**: Are line counts extracted correctly?
2. **Branch Metric Accuracy (30%)**: Are branch counts extracted correctly?
3. **Percentage Calculation (30%)**: Are percentages computed accurately?

## Evidence to Evaluate

{{ evidence }}

### Format Accuracy Breakdown
```json
{{ format_accuracy }}
```

### Sample File Data
```json
{{ sample_files }}
```

### Summary
- Total checks: {{ total_checks }}
- Passed checks: {{ passed_checks }}
- Overall accuracy: {{ overall_accuracy }}%
- Programmatic results: {{ programmatic_results }}

## Evaluation Questions
1. Are line counts (total/covered) extracted correctly from each format?
2. Are branch counts (when present) extracted correctly?
3. Are coverage percentages calculated accurately (within 0.01%)?
4. Is there consistency across formats for equivalent data?
5. Do all 4 formats (LCOV, Cobertura, JaCoCo, Istanbul) parse correctly?

## Required Output Format
Respond with ONLY a JSON object (no markdown code fences, no explanation):
```json
{
  "dimension": "parser_accuracy",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of parser accuracy assessment",
  "evidence_cited": ["specific metrics examined"],
  "recommendations": ["improvements for parsing accuracy"],
  "sub_scores": {
    "line_metric_accuracy": <1-5>,
    "branch_metric_accuracy": <1-5>,
    "percentage_calculation": <1-5>
  }
}
```
