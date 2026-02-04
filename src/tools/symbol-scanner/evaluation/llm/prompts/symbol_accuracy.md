# Symbol Accuracy Judge

You are evaluating the **symbol extraction accuracy** of symbol-scanner for code analysis.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

## Evaluation Dimension

**Symbol Extraction (30% weight)**: How accurately does symbol-scanner extract function, class, and method definitions?

## Scoring Rubric

### For Synthetic Repos (strict ground truth evaluation):

| Score | Criteria |
|-------|----------|
| 5 | Exceeds expectations: All symbols captured, types correct, line numbers exact |
| 4 | Meets requirements: Core symbols captured with minor omissions |
| 3 | Minimum acceptable: Most symbols captured, some type misclassifications |
| 2 | Significant gaps: Missing important symbols or incorrect types |
| 1 | Fails requirements: Incomplete or incorrect extraction |

### For Real-World Repos (when synthetic_baseline shows validated tool):

| Score | Criteria |
|-------|----------|
| 5 | Output schema compliant, symbols consistent with source structure |
| 4 | Minor gaps but symbols match visible code structure |
| 3 | Schema issues OR questionable symbol classifications |
| 2 | Multiple issues AND inconsistent data |
| 1 | Broken output, missing required fields |

## Evidence to Evaluate

### Extracted Symbols
```json
{{ symbols }}
```

### Symbol Counts by Type
```json
{{ symbols_by_type }}
```

### Source Code Samples
```json
{{ source_samples }}
```

### Total Symbols Count
{{ symbols_count }}

## Evaluation Questions

1. Are all visible function definitions extracted?
2. Are all class definitions extracted?
3. Are all methods within classes extracted?
4. Are symbol types correctly classified (function vs class vs method)?
5. Are line numbers accurate (start and end)?
6. Is export status (public vs private) correct?

## Required Output Format

Respond with a JSON object with a numeric score and supporting details:

```json
{
  "dimension": "symbol_accuracy",
  "score": 4,
  "confidence": 0.92,
  "reasoning": "<detailed explanation of score>",
  "evidence_cited": ["<key evidence points supporting the score>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "function_extraction": 5,
    "class_extraction": 4,
    "line_accuracy": 4
  }
}
```

### Score Guidelines
- **5**: All symbols captured correctly with exact line numbers and proper type classification
- **4**: Core symbols captured with minor issues (off-by-one lines, optional fields missing)
- **3**: Most symbols captured, some type misclassifications or moderate line errors
- **2**: Missing important symbols or incorrect types
- **1**: Incomplete extraction, systematic errors, or broken output
