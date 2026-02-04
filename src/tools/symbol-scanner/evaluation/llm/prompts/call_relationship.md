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

Respond with a JSON object with a numeric score and supporting details:

```json
{
  "dimension": "call_relationship",
  "score": 4,
  "confidence": 0.88,
  "reasoning": "<detailed explanation of score>",
  "evidence_cited": ["<key evidence points supporting the score>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "direct_calls": 5,
    "cross_file_calls": 4,
    "line_accuracy": 4
  }
}
```

### Score Guidelines
- **5**: All calls captured with correct caller/callee pairs and accurate line numbers
- **4**: Core calls captured with minor issues (missing some dynamic calls, slight line deviations)
- **3**: Most calls captured, some incorrect pairings or moderate line errors
- **2**: Missing important calls or incorrect caller/callee relationships
- **1**: Incomplete extraction, systematic errors, or broken output
