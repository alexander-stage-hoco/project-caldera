# Documentation Judge

You are evaluating the **documentation quality** of scc for integration into the DD Platform.

## Evaluation Dimension

**Documentation Completeness (8% weight)**: Is the documentation sufficient for integration and troubleshooting?

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | Excellent: Comprehensive docs, examples, API reference, troubleshooting |
| 4 | Good: Clear usage docs, common examples, some edge cases covered |
| 3 | Adequate: Basic usage documented, limited examples |
| 2 | Poor: Missing important documentation, confusing structure |
| 1 | Insufficient: Cannot understand usage without reading source |

## Evidence to Evaluate

{{ evidence }}

### README Content
{{ readme_content }}

### Help Output
```
{{ help_output }}
```

### Available Documentation Files
{{ doc_files }}

## Evaluation Questions

1. Is the installation process clearly documented?
2. Are all CLI flags and options explained?
3. Are output formats (JSON, CSV, etc.) documented with examples?
4. Are language-specific quirks or limitations noted?
5. Is there guidance for large repository analysis?

## Evaluation Approach

Evaluate based on the README content and help output provided. Check for installation instructions, CLI flag documentation, and output format examples. Provide your JSON response directly.

## Required Output Format

```json
{
  "dimension": "documentation",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific doc sections>"],
  "recommendations": ["<documentation improvements>"]
}
```
