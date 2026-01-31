# IaC Quality Evaluation

You are evaluating the quality of Trivy's Infrastructure-as-Code (IaC) misconfiguration detection for a due diligence code analysis tool.

## Context

Trivy scans Dockerfiles, Terraform files, and other IaC artifacts for security misconfigurations. For due diligence purposes, IaC scanning is critical for:
- Identifying infrastructure security gaps before deployment
- Assessing DevOps security maturity
- Finding compliance violations (encryption, access controls, etc.)

## Evidence

The following evidence shows IaC misconfiguration detection results:

{{ evidence }}

## Evaluation Criteria

Score 1-5 on IaC detection quality:

1. **Detection Accuracy** (40%): Are real misconfigurations being found? (Docker root user, open security groups, unencrypted storage)
2. **Coverage** (30%): Are both Dockerfile and Terraform issues detected? Are different issue types found?
3. **Actionability** (30%): Do findings include resolution guidance? Are line numbers provided?

### Scoring Rubric

- **5 (Excellent)**: Detects critical IaC issues, covers multiple file types, provides actionable resolutions
- **4 (Good)**: Good detection across file types, mostly actionable findings
- **3 (Acceptable)**: Basic detection working, some gaps in coverage or actionability
- **2 (Poor)**: Missing significant IaC issues, limited coverage
- **1 (Failing)**: IaC detection not working or producing unusable results

## Response Format

Respond with ONLY a JSON object (no markdown code fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<2-3 sentences explaining the score>",
  "evidence_cited": ["<specific evidence points that informed your score>"],
  "recommendations": ["<actionable improvements if score < 5>"],
  "sub_scores": {
    "detection_accuracy": <1-5>,
    "coverage": <1-5>,
    "actionability": <1-5>
  }
}
