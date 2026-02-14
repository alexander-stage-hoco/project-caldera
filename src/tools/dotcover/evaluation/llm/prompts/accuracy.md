# Coverage Accuracy Evaluation

You are evaluating the accuracy of dotCover code coverage measurements.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Judge output quality: schema compliance, coverage calculations
- Verify that covered_statements <= total_statements invariant holds
- Check that percentages are correctly calculated (covered/total * 100)

## Evidence to Review

{{ evidence }}

### Coverage Summary
{{ coverage_summary }}

### Assembly Coverage
{{ assembly_coverage }}

### Type Coverage Sample
{{ type_coverage_sample }}

### Method Coverage Sample
{{ method_coverage_sample }}

### Ground Truth Comparison
{{ ground_truth_comparison }}

## Evaluation Criteria

### For Synthetic Repos (with ground truth):

#### Score 5 (Excellent)
- All coverage percentages match ground truth within 1%
- Statement counts are exact matches
- No invariant violations (covered <= total)
- Hierarchy totals sum correctly

#### Score 4 (Good)
- Coverage percentages within 5% of ground truth
- Minor statement count discrepancies
- No invariant violations

#### Score 3 (Acceptable)
- Coverage percentages within 10% of ground truth
- Some count discrepancies
- No critical invariant violations

#### Score 2 (Poor)
- Large percentage deviations (>10%)
- Multiple count discrepancies
- Some invariant violations

#### Score 1 (Unacceptable)
- Completely incorrect coverage data
- Major invariant violations
- Data appears corrupted or unusable

### For Real-World Repos:

#### Score 5 (Excellent)
- All invariants hold (covered <= total, 0 <= pct <= 100)
- Percentages correctly calculated
- Complete schema compliance

#### Score 4 (Good)
- Minor calculation rounding issues
- All data structurally correct

#### Score 3 (Acceptable)
- Some schema issues but data usable

#### Score 2 (Poor)
- Multiple schema or calculation issues

#### Score 1 (Failing)
- Broken output, invalid data

## Response Format

Respond with JSON:
```json
{
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "evidence_cited": ["<specific findings>"],
    "recommendations": ["<improvements>"],
    "sub_scores": {
        "statement_counts": <1-5>,
        "percentage_accuracy": <1-5>,
        "hierarchy_consistency": <1-5>,
        "ground_truth_match": <1-5>
    }
}
```
