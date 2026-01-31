# Integration Fit Judge

You are evaluating how well scc output **integrates with the DD Platform architecture**.

## Evaluation Dimension

**Integration Architecture Fit (10% weight)**: How well does scc output map to DD Platform's evidence schema?

## DD Platform Evidence Schema (Envelope)

The DD Platform expects evidence in this format:
```json
{
  "metadata": {
    "tool_name": "scc",
    "tool_version": "3.x",
    "run_id": "uuid",
    "repo_id": "uuid",
    "branch": "main",
    "commit": "40-hex",
    "timestamp": "ISO-8601",
    "schema_version": "1.0.0"
  },
  "data": {
    "tool": "scc",
    "tool_version": "3.x",
    "summary": {
      "total_files": 10,
      "total_loc": 1200,
      "total_code": 1000,
      "total_comment": 200,
      "total_blank": 100
    },
    "languages": [
      {"name": "Python", "files": 5, "lines": 600, "code": 500, "comment": 80, "blank": 20}
    ]
  }
}
```

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | Perfect fit: All DD fields map directly, no transformation loss |
| 4 | Good fit: Minor transformations needed, all data preserved |
| 3 | Acceptable: Some manual mapping required, most data usable |
| 2 | Poor fit: Significant transformation needed, data loss likely |
| 1 | Incompatible: Cannot map to DD schema meaningfully |

## Evidence to Evaluate

### scc Output Structure
```json
{{ scc_output }}
```

### Envelope Output
```json
{{ tool_output_summary }}
```

## Evaluation Questions

1. Do all scc fields have a natural mapping to DD Platform fields?
2. Is any information lost in the transformation?
3. Can the transformation be fully automated?
4. Does metadata capture sufficient context?
5. Are identifiers present and stable across runs?

## Required Output Format

```json
{
  "dimension": "integration_fit",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific mapping examples>"],
  "recommendations": ["<integration improvements>"]
}
```
