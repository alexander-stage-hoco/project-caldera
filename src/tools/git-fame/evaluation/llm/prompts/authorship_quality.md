# Authorship Quality Evaluation

You are an expert in code analysis evaluating git-fame's accuracy in author attribution.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Baseline Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Judge output quality based on data consistency and completeness
- Low author counts may be valid for small or single-maintainer projects
- Focus on accuracy of what IS detected, not expected counts

## Task

Evaluate the quality and accuracy of author attribution in the git-fame output.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

### 1. Author Identification (40%)
Are authors correctly identified from git history?
- **5**: All authors captured with correct names, no duplicates
- **4**: Most authors correct (>95%), minimal duplication
- **3**: Majority correct (85-95%), some duplicates or missing
- **2**: Some issues (70-85%), notable gaps
- **1**: Many authors missing or incorrect (<70%)

### 2. Ownership Accuracy (35%)
Are ownership percentages accurate and valid?
- **5**: All percentages sum to 100%, values are reasonable
- **4**: Minor discrepancies (<1% total deviation)
- **3**: Some issues (1-5% deviation)
- **2**: Significant issues (5-10% deviation)
- **1**: Major data integrity issues (>10% deviation)

### 3. Metric Completeness (25%)
Are author metrics complete and valid?
- **5**: LOC, commits, files all present and valid for all authors
- **4**: Minor metrics missing (<5% of data)
- **3**: Some metrics missing (5-15%)
- **2**: Many metrics missing (15-30%)
- **1**: Critical data missing (>30%)

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation of your evaluation>",
  "evidence_cited": [
    "<specific evidence from author data>",
    "<validation results if available>"
  ],
  "recommendations": [
    "<suggestions for improving author attribution>",
    "<data quality improvements>"
  ],
  "sub_scores": {
    "author_identification": <1-5>,
    "ownership_accuracy": <1-5>,
    "metric_completeness": <1-5>
  }
}
