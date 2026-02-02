# Security Detection Evaluation

You are evaluating the security vulnerability detection capabilities of Roslyn Analyzers for .NET code analysis.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Low security finding counts are NOT automatically failures
- Judge output quality: schema compliance, rule categorization, severity mapping
- Judge detection quality: Are the security issues that WERE detected accurate and properly classified?
- Consider: A tool that finds 0 security issues in a secure codebase deserves a high score

## Context

This evaluation focuses on how well the analyzers detect security issues in C# code, including:
- SQL injection (CA3001, CA2100)
- XSS vulnerabilities (CA3002, SCS0029)
- Hardcoded secrets (CA5390, SCS0015)
- Weak cryptography (CA5350, CA5351)
- Insecure deserialization (CA2300-CA2315)
- Deprecated TLS (CA5364, CA5397)
- CSRF vulnerabilities (CA3147, SCS0016)

## Evidence

### Security Summary
{{ security_summary }}

### Detection by Rule Category
{{ detection_by_category }}

### Sample Violations
{{ violations_sample }}

### Ground Truth Comparison
{{ ground_truth_comparison }}

## Evaluation Criteria

Score each sub-dimension from 1-5:

1. **SQL Injection Detection** (weight: 25%)
   - Are all SQL injection patterns correctly identified?
   - Are parameterized queries recognized as safe?

2. **Cryptography Analysis** (weight: 25%)
   - Are weak algorithms (MD5, SHA1, DES) flagged?
   - Are modern algorithms (SHA256, AES) accepted?

3. **Deserialization Security** (weight: 25%)
   - Are unsafe deserializers detected?
   - Is type binder validation recognized?

4. **Overall Security Coverage** (weight: 25%)
   - Are all security categories covered?
   - What is the recall on expected violations?

## Scoring Guide

### For Synthetic Repos (with ground truth):

- **5**: Excellent - All security issues detected, zero false positives
- **4**: Good - >90% detection rate, minimal false positives
- **3**: Adequate - >80% detection rate, some gaps
- **2**: Poor - <80% detection rate, significant gaps
- **1**: Failing - Major security categories missed

### For Real-World Repos (when synthetic_baseline shows validated tool):

- **5**: Output schema compliant, any findings accurately classified, complete metadata
- **4**: Minor schema issues but findings accurate, good rule categorization
- **3**: Schema issues OR questionable security classification
- **2**: Multiple schema issues AND questionable classifications
- **1**: Broken output, missing required fields, obvious false positives

**Key principle**: Do NOT penalize for low finding counts on real-world repos when the tool is validated (synthetic_score >= 0.9). A secure codebase with well-formed output deserves a high score.

## Response Format

Respond with a JSON object:

```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "sub_scores": {
    "sql_injection": <1-5>,
    "cryptography": <1-5>,
    "deserialization": <1-5>,
    "overall_coverage": <1-5>
  },
  "evidence_cited": ["<specific findings from the data>"],
  "recommendations": ["<actionable improvements>"]
}
```
