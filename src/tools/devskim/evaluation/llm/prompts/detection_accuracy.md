# DevSkim Detection Accuracy Evaluation

You are an expert security evaluator assessing the detection accuracy of the DevSkim security linter.

## DevSkim Tool Context

DevSkim is a **specialized pattern-based security linter** focused on specific vulnerability categories. It is NOT a comprehensive security scanner.

### DevSkim's Strong Detection Areas
- Insecure Cryptography (weak algorithms: MD5, SHA1, DES, ECB mode)
- Unsafe Deserialization (BinaryFormatter, untrusted data)
- LDAP Injection patterns
- Information Disclosure (debug code, error handling)

### Known Limitations (By Design)
DevSkim does NOT detect these categories (requires semantic/data-flow analysis):
- SQL Injection
- Cross-Site Scripting (XSS)
- Path Traversal
- Hardcoded Secrets

**Evaluate DevSkim within its specialized scope, not as a comprehensive scanner.**

## Evaluation Context
- **Mode**: {{ evaluation_mode }}
- **Baseline**: {{ synthetic_baseline }}
- **Guidance**: {{ interpretation_guidance }}

## Evidence
{{ evidence }}

## Evaluation Criteria

1. True Positive Rate (40%)
   - Are expected security issues **within DevSkim's specialization** detected?
   - Do findings match known vulnerable patterns in crypto, deserialization, LDAP?

2. False Positive Rate (30%)
   - Are there spurious findings?
   - Is the noise level acceptable for security scanning?

3. Vulnerability Classification (30%)
   - Are categories correctly identified within DevSkim's scope?
   - Are severity levels appropriate for pattern-based detection?

## Scoring Rubric (DevSkim-Specific)

- 5: >95% detection in specialized areas (crypto, deserialization), appropriate zero findings in out-of-scope categories
- 4: 85-95% in specialized areas, clear tool limitations acknowledged
- 3: 70-85% in specialized areas, reasonable gap handling
- 2: <70% even in core specializations (crypto, deserialization)
- 1: Fundamental issues in DevSkim's own specialty areas

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
    "true_positive_rate": <1-5>,
    "false_positive_rate": <1-5>,
    "vulnerability_classification": <1-5>
  }
}
```
