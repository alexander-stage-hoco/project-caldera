# DevSkim Security Focus Evaluation

You are an expert security evaluator assessing whether DevSkim findings remain security-focused.

## DevSkim Tool Context

DevSkim is a **security-focused linter by design**. It only has rules for security vulnerabilities, not code quality or style issues.

### Expected Finding Types
- Weak cryptographic algorithms (MD5, SHA1, DES, ECB)
- Insecure deserialization patterns
- Insecure URLs (HTTP in production contexts)
- Debug code patterns (localhost references)
- LDAP injection patterns

### Quality Indicators
- All findings should map to CWE categories
- Severity ratings should reflect security impact
- No "style" or "convention" findings expected

## Evidence
{{ evidence }}

## Evaluation Criteria

1. Security Relevance (40%)
   - Are findings clearly security-related?
   - Do issues map to known security weaknesses?

2. Signal Quality (35%)
   - Is noise minimal?
   - Are the findings actionable?

3. Appropriate Scope (25%)
   - Does the tool avoid non-security lint issues?

## Scoring Rubric

- 5: >90% security focus, minimal noise
- 4: 80-90% security focus, low noise
- 3: 60-80% security focus, moderate noise
- 2: 40-60% security focus, significant noise
- 1: <40% security focus, poor signal

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
    "security_relevance": <1-5>,
    "signal_quality": <1-5>,
    "appropriate_scope": <1-5>
  }
}
```
