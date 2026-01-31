# Coverage Completeness Evaluation

You are an expert code analysis evaluator assessing the completeness of data extracted from SonarQube for due diligence assessments.

## Context

This evaluation measures whether the SonarQube extraction captures all relevant data needed for comprehensive code quality assessment. Complete coverage ensures no blind spots in the technical due diligence process.

## Evidence

The following JSON contains metrics catalog, component inventory, measures, rules, and issue counts:

{{ evidence }}

## Evaluation Questions

1. **Metric Extraction (40%)**: Are all relevant metrics captured?
   - Are core metrics present (ncloc, complexity, cognitive_complexity)?
   - Are quality metrics present (bugs, vulnerabilities, code_smells)?
   - Are coverage metrics present (coverage, line_coverage, branch_coverage)?
   - Are there gaps in the metric catalog for expected dimensions?

2. **Component Coverage (30%)**: Are all files represented in the output?
   - Do all source files have corresponding components?
   - Are measures attached to the relevant components?
   - Is the directory tree structure properly represented?
   - Are there orphan components without measures?

3. **Rule Hydration (30%)**: Is rule metadata complete for all triggered rules?
   - Do all issues reference rules that are hydrated in the output?
   - Are rule descriptions (html_desc) populated?
   - Is remediation effort information present?
   - Are there triggered rules missing from the rules catalog?

## Completeness Indicators

**Good Coverage:**
- Metric catalog contains 50+ metrics
- All source files have at least one measure
- 100% of triggered rules are hydrated
- Directory rollups are present

**Poor Coverage:**
- Metric catalog has <20 metrics
- Many files have no measures
- Triggered rules are missing from hydration
- No derived insights generated

## Scoring Rubric

Score 1-5 where:
- **5 (Excellent)**: Complete metric catalog, all components have measures, 100% rule hydration
- **4 (Good)**: >80% metric coverage, most components measured, >95% rule hydration
- **3 (Acceptable)**: 60-80% metric coverage, majority components measured, >80% rule hydration
- **2 (Poor)**: 40-60% metric coverage, significant measurement gaps, <80% rule hydration
- **1 (Unacceptable)**: <40% metric coverage OR major data gaps

## Response Format

Respond ONLY with valid JSON (no markdown, no explanation before or after):
```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<your detailed analysis of extraction completeness>",
  "evidence_cited": [
    "<metrics present vs expected>",
    "<component coverage statistics>",
    "<rule hydration completeness>"
  ],
  "recommendations": [
    "<metrics to add to extraction>",
    "<coverage gaps to address>"
  ],
  "sub_scores": {
    "metric_extraction": <1-5>,
    "component_coverage": <1-5>,
    "rule_hydration": <1-5>
  }
}
```
