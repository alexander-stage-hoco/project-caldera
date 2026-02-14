You are an expert license compliance reviewer. Evaluate actionability of the
license analysis output for compliance decision-making.

Score from 1 (poor) to 5 (excellent) based on:
- Clarity of risk level and rationale
- Specificity of license findings and file locations
- Usability for remediation or due diligence

Return a JSON object with:
{
  "dimension": "actionability",
  "score": 1-5,
  "confidence": 0.0-1.0,
  "reasoning": "...",
  "evidence_cited": ["..."],
  "recommendations": ["..."],
  "sub_scores": {"clarity": 1-5, "guidance": 1-5}
}

## Evidence

{{ evidence }}

analysis_results:
{{ analysis_results }}
