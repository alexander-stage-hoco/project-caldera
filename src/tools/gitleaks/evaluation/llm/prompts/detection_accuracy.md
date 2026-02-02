# Detection Accuracy Evaluation

You are evaluating the detection accuracy of Gitleaks secret detection output.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Low finding counts are NOT automatically failures
- Judge output quality: schema compliance, metadata completeness, directory rollups
- Judge detection capability: Are the findings that WERE detected accurate and well-formed?
- Consider: A tool that finds 0 secrets in a clean repo with proper output format deserves a high score

## Evidence

{{ evidence }}

## Evaluation Criteria

Score the detection accuracy from 1-5 based on:

1. **True Positive Rate** (40% of score)
   - Were all expected secrets detected? (For synthetic repos with ground truth)
   - For real-world repos: Are detected secrets plausible and correctly identified?
   - Were secret types correctly identified?

2. **Location Accuracy** (30% of score)
   - Are file paths correct and normalized?
   - Are line numbers accurate?
   - Is the match position within the line correct?

3. **Rule Matching** (30% of score)
   - Were appropriate detection rules triggered?
   - Is the match quality good (full secrets, not partial)?
   - Are rule IDs meaningful and consistent?

## Scoring Guide

### For Synthetic Repos (with ground truth):
- **5 (Excellent)**: All secrets detected with correct types and locations
- **4 (Good)**: >90% secrets detected, minor location inaccuracies
- **3 (Acceptable)**: 70-90% secrets detected, some misidentifications
- **2 (Poor)**: 50-70% secrets detected, significant issues
- **1 (Failing)**: <50% secrets detected, unreliable detection

### For Real-World Repos (when synthetic_baseline shows validated tool):
- **5 (Excellent)**: Output schema compliant, any findings are accurate, metadata complete
- **4 (Good)**: Minor schema issues but findings accurate, good metadata
- **3 (Acceptable)**: Schema issues OR questionable finding accuracy
- **2 (Poor)**: Multiple schema issues AND questionable findings
- **1 (Failing)**: Broken output, missing required fields, obvious false positives

**Key principle**: Do NOT penalize for low finding counts on real-world repos when the tool is validated (synthetic_score >= 0.9). A clean codebase with well-formed output deserves a high score.

## Response Format

Respond with ONLY a JSON object:
{
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation of scoring>",
    "evidence_cited": ["<specific findings from the output>"],
    "recommendations": ["<specific improvements>"],
    "sub_scores": {
        "true_positive_rate": <1-5>,
        "location_accuracy": <1-5>,
        "rule_matching": <1-5>
    }
}
