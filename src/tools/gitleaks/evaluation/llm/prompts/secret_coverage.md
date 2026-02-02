# Secret Type Coverage Evaluation

You are evaluating the coverage of secret types detected by Gitleaks.

## Evidence

{{ evidence }}

## Evaluation Criteria

Score the secret type coverage from 1-5 based on:

1. **Type Breadth** (40% of score)
   - Are common secret types detected? (API keys, tokens, passwords, private keys)
   - Are platform-specific secrets detected? (AWS, GCP, Azure, GitHub, Slack, etc.)
   - Are database credentials detected? (connection strings, passwords)

2. **Format Handling** (30% of score)
   - Are different encodings handled? (base64, hex, URL-encoded)
   - Are various file formats recognized? (JSON, YAML, .env, config files)
   - Are embedded secrets in code comments detected?

3. **Historical Coverage** (30% of score)
   - Are secrets in git history detected? (not just current HEAD)
   - Are deleted but previously committed secrets found?
   - Is the full commit history scanned appropriately?

## Secret Types to Check

Common types that should be detected:
- AWS access keys and secret keys
- GitHub/GitLab tokens
- Slack tokens and webhooks
- Private keys (RSA, DSA, EC)
- Database passwords
- API keys (generic and platform-specific)
- JWT tokens
- OAuth tokens

## Scoring Guide

- **5 (Excellent)**: Comprehensive coverage of all expected secret types
- **4 (Good)**: Good coverage with minor gaps in less common types
- **3 (Acceptable)**: Basic coverage of common types only
- **2 (Poor)**: Limited coverage, many important types missed
- **1 (Failing)**: Poor coverage, most secrets not detected

## Response Format

Respond with ONLY a JSON object:
{
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation of coverage gaps>",
    "evidence_cited": ["<secret types detected and missed>"],
    "recommendations": ["<types to add detection for>"],
    "sub_scores": {
        "type_breadth": <1-5>,
        "format_handling": <1-5>,
        "historical_coverage": <1-5>
    }
}
