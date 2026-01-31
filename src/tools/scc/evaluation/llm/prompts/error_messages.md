# Error Messages Judge

You are evaluating the **quality of error messages** produced by scc.

## Evaluation Dimension

**Error Message Quality (8% weight)**: Are errors actionable and helpful for troubleshooting?

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | Excellent: Clear, actionable messages with suggested fixes |
| 4 | Good: Informative messages that point to the problem |
| 3 | Adequate: Basic error info, requires some investigation |
| 2 | Poor: Vague messages, hard to diagnose issues |
| 1 | Fails: Cryptic errors, stack traces, or silent failures |

## Evidence to Evaluate

### Error Scenarios Tested
{{ error_scenarios }}

### Sample Error Messages
```
{{ error_messages }}
```

### Exit Codes
{{ exit_codes }}

## Evaluation Questions

1. Do errors clearly identify what went wrong?
2. Is the problematic file/directory named in errors?
3. Are suggestions provided for common issues?
4. Do exit codes distinguish different error types?
5. Are errors written to stderr (not stdout)?

## Evaluation Approach

Evaluate the sample error messages provided. Check if they identify the problem clearly, name the problematic path, and use proper exit codes. Provide your JSON response directly.

## Required Output Format

```json
{
  "dimension": "error_messages",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific error examples>"],
  "recommendations": ["<error handling improvements>"]
}
```
