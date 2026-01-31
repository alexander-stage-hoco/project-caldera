# Security Coverage Evaluation

You are an expert security analyst evaluating a code analysis tool (Roslyn Analyzers) for its coverage of security vulnerabilities relevant to .NET applications.

## Context

This evaluation assesses whether the tool provides adequate security coverage for technical due diligence on .NET codebases. The tool should detect OWASP Top 10 vulnerabilities and .NET-specific security patterns.

## Evidence to Evaluate

### Security Rules Triggered
{{ security_rules_triggered }}

### OWASP Mapping
{{ owasp_coverage_map }}

### Severity Distribution
{{ severity_breakdown }}

## Evaluation Questions

1. **OWASP Coverage**: Does the tool cover critical OWASP Top 10 vulnerabilities?
   - A03:2021 Injection (SQL, XSS)
   - A02:2021 Cryptographic Failures
   - A08:2021 Software and Data Integrity (deserialization)
   - A05:2021 Security Misconfiguration (TLS/SSL)

2. **.NET-Specific Patterns**: Are .NET-specific security patterns adequately covered?
   - CA3xxx rules for injection
   - CA5xxx rules for cryptography
   - CA2xxx rules for deserialization

3. **Severity Classification**: Is severity classification appropriate for prioritizing remediation?

4. **Coverage Gaps**: What critical security patterns are missing that would be important for due diligence?

## Scoring Rubric

Score 1-5 where:
- **5 (Excellent)**: Covers all OWASP Top 10 applicable to .NET, comprehensive CA rules
- **4 (Good)**: Covers 8+ OWASP categories, most security-related CA rules
- **3 (Acceptable)**: Covers 5-7 OWASP categories, core security rules present
- **2 (Poor)**: Covers 3-4 OWASP categories, limited security rule coverage
- **1 (Unacceptable)**: <3 OWASP categories covered, major security gaps

## Response Format

Provide your evaluation as JSON:
```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<your detailed analysis of security coverage>",
  "evidence_cited": [
    "<specific OWASP categories covered>",
    "<.NET security rules triggered>"
  ],
  "recommendations": [
    "<rules to enable for better coverage>",
    "<additional tools to consider>"
  ],
  "sub_scores": {
    "owasp_coverage": <1-5>,
    "dotnet_specific": <1-5>,
    "severity_classification": <1-5>
  }
}
```
