# Dependency Freshness Quality Evaluation

You are evaluating the accuracy of Trivy's dependency freshness (outdatedness) detection capabilities for a due diligence code analysis tool.

## Context

Dependency freshness analysis identifies packages that are behind the latest available versions. For due diligence purposes, accurate freshness detection is critical for:
- Assessing technical debt from outdated dependencies
- Identifying maintenance burden for acquisition targets
- Correlating outdatedness with security vulnerabilities
- Estimating upgrade effort and breaking change risk

## Evidence

The following evidence shows freshness detection results across multiple test repositories:

{{ evidence }}

## Evaluation Criteria

Score 1-5 on dependency freshness detection quality:

1. **Outdatedness Detection** (40%): Are outdated packages correctly identified? Is the outdated count within expected ranges?
2. **Version Delta Accuracy** (30%): Are major/minor/patch version calculations correct? Are days-behind metrics reasonable?
3. **Registry Coverage** (30%): Are all supported package ecosystems covered (npm, pip, nuget, maven, go)?

### Scoring Rubric

- **5 (Excellent)**: All repos have freshness data, accurate version deltas, all registry types covered, ground truth met
- **4 (Good)**: Most repos have freshness data, minor calculation issues, most registry types covered
- **3 (Acceptable)**: Partial freshness coverage, some inaccurate deltas, limited registry types
- **2 (Poor)**: Limited freshness data, significant calculation errors, poor registry coverage
- **1 (Failing)**: Freshness checking non-functional or unreliable

### Key Indicators

**Positive signals:**
- repos_with_freshness matches expected repos
- outdated_count within ground truth ranges
- Version delta samples show reasonable major/minor/patch calculations
- Multiple registry types covered (pip, npm, nuget, maven)
- days_since_latest values are reasonable (not negative, not impossibly large)

**Negative signals:**
- repos_without_freshness when freshness_expected is true in ground truth
- outdated_count outside expected ranges
- Zero registry coverage for expected package types
- Missing or null latest_version data
- Extreme or impossible days_since_latest values

## Response Format

Respond with ONLY a JSON object (no markdown code fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<2-3 sentences explaining the score>",
  "evidence_cited": ["<specific evidence points that informed your score>"],
  "recommendations": ["<actionable improvements if score < 5>"],
  "sub_scores": {
    "outdatedness_detection": <1-5>,
    "version_delta_accuracy": <1-5>,
    "registry_coverage": <1-5>
  }
}
