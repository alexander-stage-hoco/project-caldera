# Issue Accuracy Evaluation

You are an expert code quality analyst evaluating SonarQube's issue categorization accuracy for due diligence technical assessments.

## Context

This evaluation measures how accurately SonarQube classifies issues into the correct types (BUG, VULNERABILITY, CODE_SMELL) and assigns appropriate severity levels. Accurate classification is critical for prioritizing remediation efforts during technical due diligence.

## Evidence

The following JSON contains sampled issues by type, including their messages, rules, and severity:

{{ evidence }}

## Evaluation Questions

1. **Bug Classification (33%)**: Are BUG type issues genuine bugs?
   - Do they represent actual defects that could cause runtime failures?
   - Are null pointer, resource leak, and exception issues correctly tagged?
   - Is the severity (BLOCKER, CRITICAL, MAJOR, MINOR) appropriate for bugs?

2. **Vulnerability Classification (33%)**: Are VULNERABILITY issues real security risks?
   - Do they identify genuine security concerns (SQL injection, XSS, hardcoded credentials)?
   - Are false positives minimized for security-sensitive classifications?
   - Is severity aligned with actual security impact?

3. **Code Smell Classification (34%)**: Are CODE_SMELL issues maintainability concerns?
   - Do they identify refactoring opportunities, not actual defects?
   - Are complexity, duplication, and naming issues correctly categorized?
   - Is severity proportional to maintainability impact?

4. **Message Accuracy**: Do issue messages accurately describe the problems?
   - Are messages clear and specific about what's wrong?
   - Do they reference the problematic code pattern?

## Example Quality Assessment

**Correct Classification:**
```json
{
  "type": "VULNERABILITY",
  "rule": "java:S2076",
  "message": "Make sure this OS command argument is sanitized",
  "severity": "CRITICAL"
}
```
This is correctly classified as a vulnerability with appropriate severity.

**Incorrect Classification:**
```json
{
  "type": "BUG",
  "rule": "java:S1192",
  "message": "Define a constant instead of duplicating this literal",
  "severity": "MAJOR"
}
```
This should be CODE_SMELL, not BUG - it's a maintainability concern.

## Scoring Rubric

Score 1-5 where:
- **5 (Excellent)**: >95% of sampled issues correctly typed, severity always appropriate, clear messages
- **4 (Good)**: 85-95% correct typing, severity mostly appropriate, understandable messages
- **3 (Acceptable)**: 70-85% correct typing, some severity mismatches, adequate messages
- **2 (Poor)**: 50-70% correct typing, frequent severity mismatches, unclear messages
- **1 (Unacceptable)**: <50% correct typing OR systematic misclassification

## Response Format

Respond ONLY with valid JSON (no markdown, no explanation before or after):
```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<your detailed analysis of issue classification accuracy>",
  "evidence_cited": [
    "<example of correctly classified issue>",
    "<example of misclassified issue if found>"
  ],
  "recommendations": [
    "<how to improve classification accuracy>",
    "<rules to review or reconfigure>"
  ],
  "sub_scores": {
    "bug_classification": <1-5>,
    "vulnerability_classification": <1-5>,
    "code_smell_classification": <1-5>
  }
}
```
