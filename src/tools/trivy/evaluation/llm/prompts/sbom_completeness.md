# SBOM Completeness Evaluation

You are evaluating the completeness of Trivy's Software Bill of Materials (SBOM) generation for a due diligence code analysis tool.

## Context

SBOM (Software Bill of Materials) provides a complete inventory of all software components in a codebase. For due diligence purposes, SBOM completeness is critical for:
- Understanding dependency sprawl and supply chain exposure
- Identifying total attack surface (not just known vulnerabilities)
- Assessing technical debt from outdated dependencies

## Evidence

The following evidence shows SBOM/package inventory results:

{{ evidence }}

## Evaluation Criteria

Score 1-5 on SBOM completeness:

1. **Inventory Coverage** (40%): Are all dependency files scanned? Are package counts reasonable?
2. **Data Completeness** (30%): Are SBOM fields populated (total, vulnerable, clean)?
3. **Consistency** (30%): Do counts add up? Are target types properly identified?

### Scoring Rubric

- **5 (Excellent)**: Complete package inventory, all repos have SBOM data, consistent counts
- **4 (Good)**: Most repos have SBOM data, minor gaps in coverage
- **3 (Acceptable)**: SBOM present but incomplete, some consistency issues
- **2 (Poor)**: Missing SBOM for many repos, significant data gaps
- **1 (Failing)**: No useful SBOM data, unable to assess dependency landscape

## Response Format

Respond with ONLY a JSON object (no markdown code fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<2-3 sentences explaining the score>",
  "evidence_cited": ["<specific evidence points that informed your score>"],
  "recommendations": ["<actionable improvements if score < 5>"],
  "sub_scores": {
    "inventory_coverage": <1-5>,
    "data_completeness": <1-5>,
    "consistency": <1-5>
  }
}
