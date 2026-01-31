# API Design Judge

You are evaluating the **CLI API design** of scc for usability in automation pipelines.

## Evaluation Dimension

**API Design Quality (10% weight)**: How intuitive and automation-friendly is the CLI?

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | Excellent: Intuitive flags, consistent patterns, excellent defaults |
| 4 | Good: Clear options, good defaults, minor inconsistencies |
| 3 | Acceptable: Functional but some confusing options or behaviors |
| 2 | Poor: Inconsistent flags, poor defaults, hard to script |
| 1 | Fails: Unusable for automation |

## Evidence to Evaluate

### CLI Help Output
```
{{ help_output }}
```

### Common Usage Patterns
```bash
{{ usage_examples }}
```

### Flag Combinations Tested
{{ flag_combinations }}

## Evaluation Questions

1. Are flag names intuitive and consistent (e.g., `-f` for format, `-o` for output)?
2. Are defaults sensible for common use cases?
3. Can output be piped to other tools (JSON, CSV)?
4. Is there a quiet/verbose mode for different contexts?
5. Can paths be specified via stdin for batch processing?

## Required Output Format

```json
{
  "dimension": "api_design",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific CLI patterns>"],
  "recommendations": ["<API improvements>"]
}
```
