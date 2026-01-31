# Severity Classification Evaluation

You are evaluating the accuracy of Trivy's CVE severity classification for a due diligence code analysis tool.

## Context

Trivy classifies vulnerabilities into severity levels (CRITICAL, HIGH, MEDIUM, LOW) based on CVSS scores. Accurate severity classification is essential for:
- Prioritizing remediation efforts
- Assessing immediate security risk
- Making informed investment decisions

CVSS 3.x severity ranges:
- CRITICAL: 9.0-10.0
- HIGH: 7.0-8.9
- MEDIUM: 4.0-6.9
- LOW: 0.1-3.9

## Evidence

The following evidence shows severity classification results:

{{ evidence }}

## Evaluation Criteria

Score 1-5 on severity classification accuracy:

1. **CVSS Alignment** (50%): Do severity labels match CVSS score ranges?
2. **Distribution Accuracy** (30%): Are severity counts within expected ground truth ranges?
3. **Critical/High Accuracy** (20%): Are the most severe vulnerabilities correctly identified?

### Scoring Rubric

- **5 (Excellent)**: >90% CVSS alignment, all severity counts in expected ranges
- **4 (Good)**: >80% CVSS alignment, most severity counts correct
- **3 (Acceptable)**: >70% CVSS alignment, minor discrepancies in counts
- **2 (Poor)**: Significant misclassifications, counts outside expected ranges
- **1 (Failing)**: Unreliable severity classification

## Response Format

Respond with ONLY a JSON object (no markdown code fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<2-3 sentences explaining the score>",
  "evidence_cited": ["<specific evidence points that informed your score>"],
  "recommendations": ["<actionable improvements if score < 5>"],
  "sub_scores": {
    "cvss_alignment": <1-5>,
    "distribution_accuracy": <1-5>,
    "critical_high_accuracy": <1-5>
  }
}
