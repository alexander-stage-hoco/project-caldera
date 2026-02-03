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

Respond with a JSON object with a **BINARY PASS/FAIL decision**:

```json
{
  "dimension": "import_completeness",
  "decision": "PASS",
  "confidence": 0.95,
  "reasoning": "<detailed explanation of why this passes or fails>",
  "issues": [
    {"severity": "LOW", "type": "missing_symbol", "import": "typing", "description": "Imported symbol 'Optional' not listed"}
  ],
  "recommendations": ["<improvement suggestions>"]
}
```

### Decision Rules
- **PASS**: All import statements captured with correct paths. Minor issues with imported symbols list are acceptable.
- **FAIL**: Missing import statements, incorrect paths, or systematic errors.

### Issue Severities
- **HIGH**: Missing import statement entirely, wrong import path
- **MEDIUM**: Wrong import type classification, missing TYPE_CHECKING import
- **LOW**: Incomplete imported_symbols list, minor line number deviation
