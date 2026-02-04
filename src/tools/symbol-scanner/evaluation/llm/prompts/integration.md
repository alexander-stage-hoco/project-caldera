# Integration Quality Judge

You are evaluating the **integration quality** of symbol-scanner for code analysis.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

## Evaluation Dimension

**Integration Quality (20% weight)**: How well does the symbol-scanner output integrate across files and maintain data coherence?

## Scoring Rubric

### For Synthetic Repos (strict ground truth evaluation):

| Score | Criteria |
|-------|----------|
| 5 | Exceeds expectations: Perfect coherence, all cross-references valid, metadata complete |
| 4 | Meets requirements: Coherent data with minor issues |
| 3 | Minimum acceptable: Mostly coherent, some inconsistencies |
| 2 | Significant gaps: Multiple coherence or consistency issues |
| 1 | Fails requirements: Broken output structure |

### For Real-World Repos (when synthetic_baseline shows validated tool):

| Score | Criteria |
|-------|----------|
| 5 | Output schema compliant, summary stats accurate, paths normalized |
| 4 | Minor issues but data is internally consistent |
| 3 | Schema issues OR summary/data mismatches |
| 2 | Multiple issues AND inconsistent data |
| 1 | Broken output, missing required fields |

## Evidence to Evaluate

### Metadata
```json
{{ metadata }}
```

### Summary Statistics
```json
{{ summary }}
```

### Summary Validation
```json
{{ summary_validation }}
```

### Metadata Completeness
```json
{{ metadata_completeness }}
```

### Path Issues Found
```json
{{ path_issues }}
```

### Data Counts
- Symbols: {{ symbols_count }}
- Calls: {{ calls_count }}
- Imports: {{ imports_count }}

## Evaluation Questions

1. Are summary statistics accurate (do counts match actual data)?
2. Is the metadata complete with all required fields?
3. Are all paths repo-relative (no absolute paths)?
4. Is the JSON structure valid and well-organized?
5. Are there any orphaned references?
6. Is cross-file consistency maintained?

## Required Output Format

Respond with a JSON object with a numeric score and supporting details:

```json
{
  "dimension": "integration",
  "score": 4,
  "confidence": 0.90,
  "reasoning": "<detailed explanation of score>",
  "evidence_cited": ["<key evidence points supporting the score>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "summary_accuracy": 5,
    "metadata_completeness": 4,
    "path_normalization": 5
  }
}
```

### Score Guidelines
- **5**: Perfect coherence, accurate summaries, complete metadata, all paths normalized
- **4**: Coherent data with minor issues (slight count discrepancies, optional metadata missing)
- **3**: Mostly coherent, some inconsistencies or minor path issues
- **2**: Multiple coherence or consistency issues
- **1**: Broken output structure, major mismatches, or absolute paths present
