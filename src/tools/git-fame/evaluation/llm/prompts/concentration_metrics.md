# Concentration Metrics Evaluation

You are evaluating git-fame's accuracy in calculating ownership concentration metrics.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Baseline Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Concentration metrics should be mathematically correct
- High concentration may be valid for small teams
- Focus on calculation accuracy, not expected concentration levels

## Background

### HHI (Herfindahl-Hirschman Index)
Sum of squared ownership fractions (0=equal distribution, 1=monopoly):
- **>0.50**: Highly concentrated (few dominant contributors)
- **0.25-0.50**: Moderately concentrated
- **0.15-0.25**: Unconcentrated (fairly distributed)
- **<0.15**: Highly distributed (many equal contributors)

### Top Author Metrics
- **Top Author %**: Ownership percentage of the highest contributor
- **Top Two %**: Combined ownership of top two contributors
- **Top N %**: Can indicate concentration at various levels

### Gini Coefficient
Inequality measure (0=perfect equality, 1=perfect inequality):
- Related to HHI but measures inequality differently
- Useful for understanding ownership distribution shape

## Task

Evaluate the accuracy of concentration metric calculations in the git-fame output.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

### 1. HHI Accuracy (40%)
Is HHI correctly calculated?
- **5**: All HHI values match recalculated values (within 1% tolerance)
- **4**: Minor discrepancies due to rounding only
- **3**: Some repos have incorrect values (>80% correct)
- **2**: Many repos have incorrect values (50-80% correct)
- **1**: Systematic calculation errors (<50% correct)

### 2. Top-N Accuracy (35%)
Are top author percentages correct?
- **5**: All top-N values match exactly (within rounding tolerance)
- **4**: Minor rounding differences only
- **3**: Some values off by >1 percentage point
- **2**: Many values incorrect
- **1**: Top-N calculations unreliable

### 3. Internal Consistency (25%)
Are metrics consistent with each other?
- **5**: All metrics are mutually consistent and non-contradictory
- **4**: Minor inconsistencies in edge cases
- **3**: Some inconsistencies that raise questions
- **2**: Significant inconsistencies between metrics
- **1**: Metrics clearly contradict each other

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation of concentration metrics assessment>",
  "evidence_cited": [
    "<specific HHI values compared>",
    "<top-N percentages examined>"
  ],
  "recommendations": [
    "<suggestions for improving metric calculations>",
    "<consistency improvements>"
  ],
  "sub_scores": {
    "hhi_accuracy": <1-5>,
    "top_n_accuracy": <1-5>,
    "internal_consistency": <1-5>
  }
}
