# Code Quality Judge

You are evaluating the **output richness and expressiveness** of scc (Sloc Cloc and Code) for use in technical due diligence.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

## Evaluation Dimension

**Output Richness (10% weight)**: How comprehensive and expressive is the data produced by scc?

## Scoring Rubric

### For Synthetic Repos (strict ground truth evaluation):

| Score | Criteria |
|-------|----------|
| 5 | Exceeds expectations: All metrics present, additional useful fields, excellent structure |
| 4 | Meets requirements: Core metrics (LOC, complexity, comments) with good detail |
| 3 | Minimum acceptable: Basic counts present, limited detail |
| 2 | Significant gaps: Missing important metrics, sparse output |
| 1 | Fails requirements: Insufficient data for due diligence |

### For Real-World Repos (when synthetic_baseline shows validated tool):

| Score | Criteria |
|-------|----------|
| 5 | Output schema compliant, metrics present and reasonable for repo size |
| 4 | Minor schema issues but metrics are internally consistent |
| 3 | Schema issues OR questionable metric values |
| 2 | Multiple schema issues AND inconsistent metrics |
| 1 | Broken output, missing required fields |

## Evidence to Evaluate

### Raw scc JSON Output
```json
{{ raw_output }}
```

### Per-File Output Sample
```json
{{ per_file_sample }}
```

## Evaluation Questions

1. Does the output include all expected metrics (LOC, SLOC, comments, blanks, complexity)?
2. Are numeric types appropriate (integers for counts, floats where needed)?
3. Is the JSON structure well-organized for programmatic consumption?
4. Are there any bonus fields that add value (ULOC, bytes, language detection)?
5. Is the complexity calculation useful for identifying problematic code?

## Required Output Format

Respond with a JSON object:

```json
{
  "dimension": "code_quality",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific fields or values from the evidence>"],
  "recommendations": ["<improvement suggestions>"]
}
```
