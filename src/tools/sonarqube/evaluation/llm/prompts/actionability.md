# Actionability Evaluation

You are an expert software engineer evaluating SonarQube's output actionability for developers and due diligence teams.

## Context

This evaluation assesses whether SonarQube's analysis output is useful for remediation planning. Results should be clear, prioritizable, and include guidance for fixing issues identified during technical due diligence.

## Evidence

The following JSON contains quality gate status, issue samples, rule metadata, and derived insights:

{{ evidence }}

## Evaluation Questions

1. **Report Clarity (40%)**: Is the output understandable and well-organized?
   - Is schema version and structure clear?
   - Are derived insights (hotspots, rollups) present?
   - Is quality gate status with conditions provided?
   - Can developers quickly navigate to problem areas?

2. **Prioritization (30%)**: Are issues properly ranked for remediation ordering?
   - Do all issues have severity ratings (BLOCKER, CRITICAL, MAJOR, MINOR, INFO)?
   - Are severity levels consistent and meaningful?
   - Can issues be filtered and sorted by priority?
   - Are hotspots identified for focus areas?

3. **Remediation Guidance (30%)**: Are fix suggestions provided?
   - Do rules include description (html_desc)?
   - Is remediation effort information present?
   - Are file and line locations precise?
   - Can developers understand what to fix and how?

## Example Quality Assessment

**Good Actionability:**
```json
{
  "quality_gate_status": "ERROR",
  "issues_with_line": 142,
  "issues_total": 150,
  "rules_with_description": 45,
  "hotspots_count": 8
}
```
Clear quality gate, precise locations, rule descriptions, and identified hotspots.

**Poor Actionability:**
```json
{
  "quality_gate_status": null,
  "issues_with_line": 20,
  "issues_total": 150,
  "rules_with_description": 10,
  "hotspots_count": 0
}
```
Missing quality gate, imprecise locations, few descriptions, no hotspot analysis.

## Scoring Rubric

Score 1-5 where:
- **5 (Excellent)**: Clear structure, all issues prioritized, comprehensive remediation guidance
- **4 (Good)**: Well-organized, >90% issues with severity, most rules documented
- **3 (Acceptable)**: Understandable structure, basic prioritization, some guidance
- **2 (Poor)**: Confusing output, inconsistent severity, limited guidance
- **1 (Unacceptable)**: Unusable output, no prioritization, no remediation info

## Response Format

Respond ONLY with valid JSON (no markdown, no explanation before or after):
```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<your detailed analysis of actionability>",
  "evidence_cited": [
    "<quality gate and derived insights presence>",
    "<issue location and severity coverage>"
  ],
  "recommendations": [
    "<how to improve output clarity>",
    "<metadata to add for better prioritization>"
  ],
  "sub_scores": {
    "report_clarity": <1-5>,
    "prioritization": <1-5>,
    "remediation_guidance": <1-5>
  }
}
```
