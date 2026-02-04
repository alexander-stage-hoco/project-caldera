# Import Completeness Judge

You are evaluating the **import extraction accuracy** of symbol-scanner for code analysis.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

## Evaluation Dimension

**Import Completeness (20% weight)**: How accurately does symbol-scanner extract import statements?

## Scoring Rubric

### For Synthetic Repos (strict ground truth evaluation):

| Score | Criteria |
|-------|----------|
| 5 | Exceeds expectations: All imports captured, paths correct, symbols listed |
| 4 | Meets requirements: Core imports captured with minor omissions |
| 3 | Minimum acceptable: Most imports captured, some path issues |
| 2 | Significant gaps: Missing important imports or incorrect paths |
| 1 | Fails requirements: Incomplete or incorrect extraction |

### For Real-World Repos (when synthetic_baseline shows validated tool):

| Score | Criteria |
|-------|----------|
| 5 | Output schema compliant, imports consistent with source |
| 4 | Minor gaps but imports match visible import statements |
| 3 | Schema issues OR questionable import paths |
| 2 | Multiple issues AND inconsistent data |
| 1 | Broken output, missing required fields |

## Evidence to Evaluate

### Extracted Imports
```json
{{ imports }}
```

### Import Counts by Type
```json
{{ imports_by_type }}
```

### Source Code Samples
```json
{{ source_samples }}
```

### Total Imports Count
{{ imports_count }}

## Evaluation Questions

1. Are all `import x` statements captured?
2. Are all `from x import y` statements captured?
3. Are import paths correct?
4. Are imported symbols correctly listed?
5. Are line numbers accurate?
6. Are import types classified correctly (static vs dynamic)?

## Required Output Format

Respond with a JSON object with a numeric score and supporting details:

```json
{
  "dimension": "import_completeness",
  "score": 4,
  "confidence": 0.95,
  "reasoning": "<detailed explanation of score>",
  "evidence_cited": ["<key evidence points supporting the score>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "import_capture": 5,
    "path_accuracy": 4,
    "symbol_listing": 4
  }
}
```

### Score Guidelines
- **5**: All imports captured with correct paths, symbols, and line numbers
- **4**: Core imports captured with minor issues (incomplete symbol lists, slight line deviations)
- **3**: Most imports captured, some path issues or type misclassifications
- **2**: Missing important imports or incorrect paths
- **1**: Incomplete extraction, systematic errors, or broken output
