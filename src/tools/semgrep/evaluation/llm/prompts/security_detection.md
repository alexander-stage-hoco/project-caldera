# Security Detection Evaluation

You are evaluating **security vulnerability detection** by Semgrep, focusing on OWASP Top 10 categories.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Low security finding counts are NOT automatically failures
- Judge output quality: schema compliance, CWE mapping accuracy, OWASP categorization
- Judge detection quality: Are the security issues that WERE detected accurate and properly classified?
- Consider: A tool that finds 0 security issues in a secure codebase deserves a high score

## Evaluation Dimension

**Security Detection (40% weight)**: How effectively does Semgrep detect security vulnerabilities?

## OWASP Top 10 2021 Categories

- A01: Broken Access Control
- A02: Cryptographic Failures
- A03: Injection (SQL, XSS, Command, etc.)
- A04: Insecure Design
- A05: Security Misconfiguration
- A06: Vulnerable Components
- A07: Authentication Failures
- A08: Software and Data Integrity (Deserialization)
- A09: Security Logging Failures
- A10: Server-Side Request Forgery (SSRF)

## Evidence to Evaluate

{{ evidence }}

## Scoring Rubric

### For Synthetic Repos (with ground truth):

| Score | Criteria |
|-------|----------|
| 5 | >90% security detection, all OWASP categories covered, injection rate >95% |
| 4 | 80-90% detection, most OWASP categories, injection rate >85% |
| 3 | 70-80% detection, several OWASP categories, injection rate >70% |
| 2 | 50-70% detection, limited OWASP coverage, injection rate 50-70% |
| 1 | <50% detection, poor OWASP coverage, unreliable injection detection |

### For Real-World Repos (when synthetic_baseline shows validated tool):

| Score | Criteria |
|-------|----------|
| 5 | Output schema compliant, any findings accurately classified, complete CWE/OWASP mapping |
| 4 | Minor schema issues but findings accurate, good categorization |
| 3 | Schema issues OR questionable security classification |
| 2 | Multiple schema issues AND questionable classifications |
| 1 | Broken output, missing required fields, obvious false positives |

**Key principle**: Do NOT penalize for low finding counts on real-world repos when the tool is validated (synthetic_score >= 0.9). A secure codebase with well-formed output deserves a high score.

## Sub-Dimensions

1. **Injection Detection (40%)**: SQL, XSS, command, code injection accuracy
2. **OWASP Coverage (30%)**: Breadth of OWASP Top 10 categories detected
3. **CWE Mapping (30%)**: Proper CWE IDs assigned to findings

## Required Output Format

Respond with ONLY a JSON object:
```json
{
  "dimension": "security_detection",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of security detection assessment",
  "evidence_cited": ["specific security findings examined"],
  "recommendations": ["improvements for security detection"],
  "sub_scores": {
    "injection_detection": <1-5>,
    "owasp_coverage": <1-5>,
    "cwe_mapping": <1-5>
  }
}
```
