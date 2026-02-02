# Integration Fit Evaluation

You are an expert data integration architect evaluating SonarQube's output compatibility with the DD Platform schema for due diligence technical assessments.

## Context

This evaluation measures how well SonarQube's output structure maps to the DD Platform's evidence schema. Good integration fit means minimal transformation loss and seamless data flow through the analytics pipeline.

## Evidence

The following JSON shows the SonarQube output structure:

{{ evidence }}

## Evaluation Questions

1. **Envelope Format Compliance (25%)**: Does the output use the Caldera envelope format?
   - Is there a `metadata` section with tool_name, run_id, repo_id, timestamp?
   - Is there a `data` section with the analysis results?
   - Are schema_version and tool_version present?

2. **Issues Structure (25%)**: How well does the issues data map to DD Platform?
   - Are issues in an `items` array with consistent structure?
   - Does each issue have type, severity, rule, message, and location?
   - Are rollups provided for directory-level aggregation?

3. **Metrics Integration (25%)**: How well do metrics integrate?
   - Is there a metrics summary with key indicators?
   - Are per-file and per-directory metrics available?
   - Do distributions follow the 22-metric pattern?

4. **Cross-Tool Correlation (25%)**: Can this output correlate with other tools?
   - Are file paths normalized and repo-relative?
   - Can file IDs link to layout-scanner output?
   - Are severity levels compatible with other tools?

## Scoring Rubric

Score 1-5 where:
- **5 (Perfect Fit)**: Full envelope compliance, all required fields, rollups present, paths normalized
- **4 (Minor Transformations)**: Envelope format present, minor field mapping needed, paths mostly normalized
- **3 (Some Mapping Required)**: Partial envelope compliance, some manual mapping for fields/paths
- **2 (Significant Transformation)**: Non-envelope format, requires significant restructuring
- **1 (Incompatible)**: Cannot be reasonably transformed to DD Platform schema

## Response Format

Respond ONLY with valid JSON (no markdown, no explanation before or after):
```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<your detailed analysis of integration fit>",
  "evidence_cited": [
    "<example of good schema compliance>",
    "<example of integration issue if found>"
  ],
  "recommendations": [
    "<how to improve integration fit>",
    "<missing fields or transformations needed>"
  ],
  "sub_scores": {
    "envelope_compliance": <1-5>,
    "issues_structure": <1-5>,
    "metrics_integration": <1-5>,
    "cross_tool_correlation": <1-5>
  }
}
```
