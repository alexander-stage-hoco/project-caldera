# Call Relationship Judge

You are evaluating the **call extraction accuracy** of symbol-scanner for code analysis.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

## Evaluation Dimension

**Call Relationships (30% weight)**: How accurately does symbol-scanner extract function and method call relationships?

## Scoring Rubric

### For Synthetic Repos (strict ground truth evaluation):

| Score | Criteria |
|-------|----------|
| 5 | Exceeds expectations: All calls captured, caller/callee pairs correct, line numbers exact |
| 4 | Meets requirements: Core calls captured with minor omissions |
| 3 | Minimum acceptable: Most calls captured, some incorrect pairings |
| 2 | Significant gaps: Missing important calls or incorrect relationships |
| 1 | Fails requirements: Incomplete or incorrect extraction |

### For Real-World Repos (when synthetic_baseline shows validated tool):

| Score | Criteria |
|-------|----------|
| 5 | Output schema compliant, calls consistent with source structure |
| 4 | Minor gaps but calls match visible code patterns |
| 3 | Schema issues OR questionable call relationships |
| 2 | Multiple issues AND inconsistent data |
| 1 | Broken output, missing required fields |

## Evidence to Evaluate

### Extracted Calls
```json
{{ calls }}
```

### Call Counts by Type
```json
{{ calls_by_type }}
```

### Source Code Samples
```json
{{ source_samples }}
```

### Symbol Names for Reference
```json
{{ symbol_names_sample }}
```

### Total Calls Count
{{ calls_count }}

### Total Symbols Count
{{ symbols_count }}

## Evaluation Questions

1. Are all direct function calls captured?
2. Are all method calls on objects captured?
3. Are caller/callee pairs correctly identified?
4. Are line numbers accurate?
5. Are call types classified correctly (direct vs dynamic vs async)?
6. Do callers reference valid symbols?

## Required Output Format

Respond with a JSON object with a **BINARY PASS/FAIL decision**:

```json
{
  "dimension": "call_relationship",
  "decision": "PASS",
  "confidence": 0.88,
  "reasoning": "<detailed explanation of why this passes or fails>",
  "issues": [
    {"severity": "MEDIUM", "type": "missing_call", "call": "main->helper", "description": "Cross-file call not captured"}
  ],
  "recommendations": ["<improvement suggestions>"]
}
```

### Decision Rules
- **PASS**: All critical calls extracted correctly with accurate caller/callee relationships.
- **FAIL**: Missing important calls, incorrect caller/callee pairs, or systematic errors.

### Issue Severities
- **HIGH**: Missing cross-file call, completely wrong caller/callee pair
- **MEDIUM**: Missing internal call, incorrect call type classification
- **LOW**: Minor line number deviation, missing dynamic call (expected limitation)
