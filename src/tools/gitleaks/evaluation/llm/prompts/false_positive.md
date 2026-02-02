# False Positive Rate Evaluation

You are evaluating the false positive rate of Gitleaks secret detection output.

## Evidence

{{ evidence }}

## Evaluation Criteria

Score the false positive rate from 1-5 based on:

1. **False Positive Count** (40% of score)
   - How many false positives were reported?
   - What percentage of total findings are false positives?
   - Compare detected vs expected secrets

2. **Pattern Quality** (30% of score)
   - Are false positives from overly broad regex patterns?
   - Are test/example secrets correctly identified as such?
   - Are placeholder values (e.g., "YOUR_API_KEY") flagged incorrectly?

3. **Noise Level** (30% of score)
   - Is the signal-to-noise ratio acceptable for practical use?
   - Are findings actionable or overwhelmed by noise?
   - Would a security team be able to triage efficiently?

## Scoring Guide

- **5 (Excellent)**: No false positives, all findings are true secrets
- **4 (Good)**: < 5% false positive rate, minimal noise
- **3 (Acceptable)**: 5-15% false positive rate, manageable noise
- **2 (Poor)**: 15-30% false positive rate, significant noise
- **1 (Failing)**: > 30% false positive rate, overwhelming noise

## Response Format

Respond with ONLY a JSON object:
{
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation of scoring>",
    "evidence_cited": ["<specific false positives identified>"],
    "recommendations": ["<pattern improvements to reduce FPs>"],
    "sub_scores": {
        "false_positive_count": <1-5>,
        "pattern_quality": <1-5>,
        "noise_level": <1-5>
    }
}
