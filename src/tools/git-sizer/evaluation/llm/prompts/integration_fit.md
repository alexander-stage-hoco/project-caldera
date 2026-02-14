# Integration Fit Judge

You are evaluating the **integration fit** of git-sizer for the DD Platform.

## Evaluation Dimension
**Integration Fit (20% weight)**: How well does git-sizer integrate with DD Platform?

## Background
The DD Platform is a Technical Due Diligence CLI tool with:
- 8-layer pipeline architecture
- DuckDB storage for Layers 1-5
- Existing collectors: scc (LOC), lizard (CCN), jscpd (duplication), semgrep (smells)
- File-level and function-level metrics already covered

git-sizer should:
- Fill gaps (not duplicate existing metrics)
- Use compatible output formats
- Meet performance requirements
- Add unique repository-level insights

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | Perfect fit - fills clear gap, compatible schema, fast performance |
| 4 | Good fit - minor schema adjustments needed, performs well |
| 3 | Acceptable fit - some gaps remain, moderate adjustments needed |
| 2 | Poor fit - significant overlap or incompatibilities |
| 1 | Does not fit - major conflicts with existing architecture |

## Sub-Dimensions
1. **Gap Coverage (40%)**: Fills gaps in existing DD capabilities
2. **Schema Compatibility (30%)**: Output maps to DD storage schema
3. **Performance (30%)**: Fast enough for pipeline integration

## Evidence to Evaluate

{{ evidence }}

### Schema Compatibility Check
```json
{{ schema_check }}
```

### DD Platform Mapping
```json
{{ dd_mapping }}
```

### Performance Assessment
```json
{{ performance }}
```

### Output Format
```json
{{ output_format }}
```

### Existing DD Tools
```json
{{ existing_dd_tools }}
```

### What git-sizer Adds
```json
{{ git_sizer_adds }}
```

## Evaluation Questions
1. Does git-sizer fill a clear gap in DD Platform capabilities?
2. Can the output schema map directly to DD storage tables?
3. Is performance acceptable for pipeline integration?
4. Is there minimal overlap with existing collectors?

## Required Output Format
Respond with ONLY a JSON object (no markdown code fences, no explanation):
```json
{
  "dimension": "integration_fit",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of integration fit assessment",
  "evidence_cited": ["specific compatibility factors examined"],
  "recommendations": ["integration improvements"],
  "sub_scores": {
    "gap_coverage": <1-5>,
    "schema_compatibility": <1-5>,
    "performance": <1-5>
  }
}
```
