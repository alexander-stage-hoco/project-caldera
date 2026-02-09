# Cross-Format Consistency Judge

You are evaluating the **cross-format consistency** of coverage-ingest's parsers.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

## Evaluation Dimension
**Cross-Format Consistency (30% weight)**: Do all 4 format parsers produce consistent output?

## Background
coverage-ingest supports 4 coverage formats:
- **LCOV**: Line-based text format (gcov, Python coverage, genhtml)
- **Cobertura**: XML format (Java, Python pytest-cov, coverage.py)
- **JaCoCo**: XML format (Java/JVM, Gradle, Maven)
- **Istanbul**: JSON format (JavaScript/TypeScript, nyc, c8)

Consistency is critical because:
- Same coverage data should produce identical normalized metrics
- Path normalization must be uniform (repo-relative, POSIX separators)
- Branch coverage handling should be equivalent across formats
- Aggregations should match regardless of source format
- Consumers of the data shouldn't need to know the source format

## Scoring Rubric

### For Synthetic Repos (strict ground truth evaluation):
| Score | Criteria |
|-------|----------|
| 5 | Perfect consistency across all formats and test cases |
| 4 | Minor format-specific variations that don't affect usability |
| 3 | Mostly consistent with some explainable differences |
| 2 | Significant inconsistencies that affect data reliability |
| 1 | Inconsistent output that cannot be trusted across formats |

### For Real-World Repos (when synthetic_baseline shows validated tool):
| Score | Criteria |
|-------|----------|
| 5 | Output format is consistent, paths normalized correctly |
| 4 | Minor format artifacts but core metrics are consistent |
| 3 | Some format-specific quirks but generally usable |
| 2 | Noticeable format-specific differences in output |
| 1 | Format-specific output that breaks downstream consumers |

## Sub-Dimensions
1. **Metric Consistency (40%)**: Same coverage data produces same metrics
2. **Path Normalization (30%)**: Paths normalized consistently (no /, POSIX only)
3. **Branch Handling (30%)**: Branch coverage treated uniformly

## Evidence to Evaluate

### Cross-Format Test Results
```json
{{ consistency_results }}
```

### Validation Rules
```json
{{ validation_rules }}
```

### Path Normalization Issues
```json
{{ path_normalization_issues }}
```

### Summary
- Formats evaluated: {{ formats_evaluated }}
- Total tests: {{ total_tests }}
- Consistent tests: {{ consistent_tests }}
- Consistency rate: {{ consistency_rate }}%
- Programmatic results: {{ programmatic_results }}

## Evaluation Questions
1. Do equivalent coverage files produce identical normalized metrics?
2. Are file paths normalized consistently (no leading /, no backslashes)?
3. Is branch coverage handled uniformly across all 4 formats?
4. Are there format-specific edge cases causing inconsistencies?
5. Would a consumer be surprised by format-specific differences?
6. Are null/missing values handled consistently across formats?

## Path Normalization Rules
All paths should:
- Be repo-relative (no leading `/`)
- Use POSIX separators (`/` not `\`)
- Not contain `./` or `..`
- Not contain drive letters (e.g., `C:`)

## Required Output Format
Respond with ONLY a JSON object (no markdown code fences, no explanation):
```json
{
  "dimension": "cross_format_consistency",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of cross-format consistency assessment",
  "evidence_cited": ["specific test results and comparisons"],
  "recommendations": ["improvements for format consistency"],
  "sub_scores": {
    "metric_consistency": <1-5>,
    "path_normalization": <1-5>,
    "branch_handling": <1-5>
  }
}
```
