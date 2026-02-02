# Severity Classification Evaluation

You are evaluating the severity classification of secrets detected by Gitleaks.

## Evidence

{{ evidence }}

## Evaluation Criteria

Score the severity classification from 1-5 based on:

1. **Classification Accuracy** (40% of score)
   - Are critical secrets (production API keys, root credentials) marked as critical?
   - Are test/example/placeholder secrets correctly de-prioritized?
   - Do severity levels match the ground truth expectations?

2. **Risk Assessment** (30% of score)
   - Does classification consider the secret type's inherent risk?
   - Are high-value targets (AWS root keys, admin passwords) properly prioritized?
   - Are less sensitive secrets (test tokens, example keys) appropriately rated?

3. **Context Awareness** (30% of score)
   - Does severity consider file location? (production config vs test files)
   - Is commit recency considered? (recent vs historical)
   - Are environment indicators used? (prod, staging, dev, test)

## Severity Levels

Expected severity classifications:
- **CRITICAL**: Production credentials, root/admin keys, active database passwords
- **HIGH**: Service account keys, CI/CD tokens, encryption keys
- **MEDIUM**: Development keys, staging credentials, internal tokens
- **LOW**: Test data, example keys, clearly marked placeholders

## Scoring Guide

- **5 (Excellent)**: Perfect severity classification matching risk profile
- **4 (Good)**: Minor severity misclassifications (within one level)
- **3 (Acceptable)**: Some important misclassifications affecting triage order
- **2 (Poor)**: Significant misclassifications, critical items not prioritized
- **1 (Failing)**: Severity classification is unreliable, cannot be used for triage

## Response Format

Respond with ONLY a JSON object:
{
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation of classification accuracy>",
    "evidence_cited": ["<specific severity assignments and issues>"],
    "recommendations": ["<classification improvements>"],
    "sub_scores": {
        "classification_accuracy": <1-5>,
        "risk_assessment": <1-5>,
        "context_awareness": <1-5>
    }
}
