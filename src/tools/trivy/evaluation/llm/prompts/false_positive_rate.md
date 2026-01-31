# False Positive Rate Evaluation

You are evaluating the false positive rate of Trivy's vulnerability detection for a due diligence code analysis tool.

## Context

False positive rate is critical for security scanner adoption. A tool that floods developers with noise becomes shelfware:
- Teams stop reviewing alerts
- Real vulnerabilities get buried
- Trust in the tool erodes

For production readiness, false positive rate should be under 5%.

## Evidence

The following evidence shows false positive analysis results:

{{ evidence }}

## Evaluation Criteria

Score 1-5 based on three sub-dimensions:

1. **Clean Repository Precision (50%)**: Do clean repos stay clean?
   - Check `clean_repo_results` to see if repos expected to have 0 vulnerabilities actually show 0
   - `clean_repos_with_findings` should be 0
   - Any findings in clean repos are definite false positives

2. **Development Dependency Classification (25%)**: Are test/dev deps properly classified?
   - Check `dev_dependency_issues` for vulnerabilities in non-production dependencies
   - Production scans should not flag test-only packages
   - Dev dependency vulnerabilities should be clearly marked or excluded

3. **Overall Precision (25%)**: What is the overall false positive rate?
   - Check `false_positive_rate` - should be <5% for excellent
   - Check `precision` - should be >95% for excellent
   - Lower FP rates indicate better targeting

### Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | Zero false positives on clean repos, FP rate <1%, precision >99% |
| 4 | Zero clean repo issues, FP rate 1-3%, precision 97-99% |
| 3 | Minor clean repo issues, FP rate 3-5%, precision 95-97% |
| 2 | Clean repo failures, FP rate 5-10%, precision 90-95% |
| 1 | Multiple clean repo failures, FP rate >10%, precision <90% |

### Ground Truth Assertions

If `ground_truth_assertions.passed` is `false`, the score should be capped at 2 regardless of other factors. The failures explain why assertions failed.

## Response Format

Respond with ONLY a JSON object (no markdown code fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<2-3 sentences explaining the score based on evidence>",
  "evidence_cited": ["<specific evidence points from the data above>"],
  "recommendations": ["<actionable improvements if score < 5>"],
  "sub_scores": {
    "clean_repo_precision": <1-5>,
    "dev_dependency_classification": <1-5>,
    "overall_precision": <1-5>
  }
}
