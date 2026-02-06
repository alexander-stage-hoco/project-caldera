# Bus Factor Accuracy Evaluation

You are evaluating git-fame's accuracy in calculating the bus factor metric.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Baseline Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Bus factor should accurately reflect code ownership concentration
- Low bus factors (1-2) indicate genuine key-person risk
- Validate that bus factor aligns with cumulative ownership distribution

## Background

**Bus Factor** = minimum number of authors whose combined ownership reaches 50% of the codebase.

Interpretation:
- Bus factor = 1: Single point of failure (critical risk)
- Bus factor = 2: High key-person risk
- Bus factor = 3-4: Moderate risk
- Bus factor >= 5: Well-distributed knowledge

## Task

Evaluate the accuracy of bus factor calculation in the git-fame output.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

### 1. Calculation Accuracy (50%)
Is bus factor correctly calculated?
- **5**: All bus factors match recalculated values exactly
- **4**: Minor discrepancies in edge cases only (rounding)
- **3**: Some repos have incorrect values (>80% correct)
- **2**: Many repos have incorrect values (50-80% correct)
- **1**: Systematic calculation errors (<50% correct)

### 2. Consistency with Distribution (30%)
Does bus factor align with ownership distribution?
- **5**: Bus factor perfectly reflects cumulative ownership pattern
- **4**: Minor inconsistencies in edge cases
- **3**: Some inconsistencies where bus factor seems off
- **2**: Significant inconsistencies
- **1**: Bus factor contradicts visible ownership data

### 3. Risk Assessment Validity (20%)
Is the implied risk classification appropriate?
- **5**: Risk levels accurately reflect bus factor implications
- **4**: Minor misclassifications for borderline cases
- **3**: Some questionable risk assessments
- **2**: Many misclassifications
- **1**: Risk assessment is unreliable

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation of bus factor accuracy assessment>",
  "evidence_cited": [
    "<specific bus factor calculations examined>",
    "<cumulative ownership patterns observed>"
  ],
  "recommendations": [
    "<suggestions for improving bus factor calculation>",
    "<risk assessment improvements>"
  ],
  "sub_scores": {
    "calculation_accuracy": <1-5>,
    "distribution_consistency": <1-5>,
    "risk_assessment": <1-5>
  }
}
