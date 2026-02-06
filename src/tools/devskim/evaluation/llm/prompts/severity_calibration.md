# DevSkim Severity Calibration Evaluation

You are an expert security evaluator assessing severity calibration for DevSkim findings.

## DevSkim Severity Context

DevSkim assigns severity based on **pattern matching without runtime context**:

### Expected Severity Patterns
- **CRITICAL**: Weak cryptographic algorithms (MD5, SHA1, DES) - always high-risk for security use
- **HIGH**: LDAP injection patterns - significant risk
- **MEDIUM**: Deserialization (BinaryFormatter) - risk depends on data source trust, which DevSkim cannot determine
- **MEDIUM**: Information disclosure patterns - context-dependent

### Acceptable Calibration Choices
- **Deserialization at MEDIUM** is acceptable because DevSkim cannot determine if input is from a trusted source. Conservative rating is appropriate.
- **Crypto uniformly CRITICAL** is acceptable because DevSkim cannot distinguish password hashing (critical) from checksums (moderate).
- **Absence of LOW severity** is expected - DevSkim focuses on high-signal security issues.

## Evidence
{{ evidence }}

## Evaluation Criteria

1. Severity Appropriateness (40%)
   - Are high-impact issues (crypto, LDAP) marked critical/high?
   - Are context-dependent issues (deserialization) marked medium?

2. Consistency (30%)
   - Are similar findings rated consistently within each category?

3. Industry Alignment (30%)
   - Does severity match expectations for a **pattern-based static analyzer**?
   - Note: Lower severity for context-dependent issues is acceptable.

## Scoring Rubric (DevSkim-Specific)

- 5: Severity consistent within categories, reasonable for pattern-matching tool
- 4: Minor inconsistencies, overall calibration appropriate for static analysis
- 3: Some unexpected ratings, but defensible given tool limitations
- 2: Inconsistent ratings within the same category
- 1: Severity inversions (low-risk marked critical, high-risk marked low)

## Required Output

Provide your evaluation as a JSON object:
```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "severity_appropriateness": <1-5>,
    "consistency": <1-5>,
    "industry_alignment": <1-5>
  }
}
```
