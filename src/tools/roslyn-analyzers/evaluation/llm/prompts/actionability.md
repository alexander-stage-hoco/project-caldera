# Actionability Evaluation

You are an expert software engineer evaluating a code analysis tool (Roslyn Analyzers) for the actionability of its output for developers and due diligence teams.

## Context

This evaluation assesses whether the tool's output is useful for remediation planning. Results should be clear, prioritizable, and include guidance for fixing issues.

## Evidence to Evaluate

### Sample Violation Messages
{{ message_samples }}

### Fix Recommendations
{{ fix_suggestions }}

### Severity/Priority Info
{{ severity_priority_info }}

## Evaluation Questions

1. **Message Clarity**: Are violation messages clear enough for developers to understand?
   - Do they explain what the issue is?
   - Do they indicate why it matters?

2. **Fix Suggestions**: Do messages include actionable fix suggestions?
   - Direct guidance on how to fix
   - Links to documentation
   - Code examples where applicable

3. **Prioritization Support**: Can violations be prioritized for due diligence reporting?
   - Severity levels (critical, high, medium, low)
   - Category grouping
   - Risk-based ordering

4. **Remediation Context**: Is sufficient context provided for planning remediation?
   - File and line locations
   - Rule documentation
   - Effort estimation hints

## Scoring Rubric

Score 1-5 where:
- **5 (Excellent)**: Clear messages, fix suggestions, documentation links, good prioritization
- **4 (Good)**: Clear messages, some fix suggestions, basic prioritization available
- **3 (Acceptable)**: Understandable messages, limited fix guidance, severity levels present
- **2 (Poor)**: Confusing messages, no fix suggestions, weak prioritization
- **1 (Unacceptable)**: Unclear messages, not actionable, no prioritization

## Response Format

Provide your evaluation as JSON:
```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<your detailed analysis of actionability>",
  "evidence_cited": [
    "<example of clear/unclear messages>",
    "<availability of fix guidance>"
  ],
  "recommendations": [
    "<how to improve actionability>",
    "<integration suggestions for reporting>"
  ],
  "sub_scores": {
    "message_clarity": <1-5>,
    "fix_suggestions": <1-5>,
    "prioritization_support": <1-5>
  }
}
```
