# Actionability Evaluation

You are an expert software engineer evaluating Semgrep's output actionability for developers and due diligence teams.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Low or zero smell counts are NOT automatically failures
- Judge actionability based on: Are the messages that ARE present clear, actionable, and well-formatted?
- Consider: A tool that produces 0 smells on a clean codebase but has good message format deserves credit

## Context

This evaluation assesses whether Semgrep's smell detection output is useful for remediation planning. Results should be clear, prioritizable, and include guidance for fixing issues identified during technical due diligence.

## Evidence

The following JSON contains sample smell messages, fix suggestions availability, and severity/priority information:

{{ evidence }}

## Evaluation Questions

1. **Message Clarity**: Are smell messages clear enough for developers?
   - Do they explain what the smell is?
   - Do they indicate why it matters (impact)?
   - Do they reference the specific code pattern?

2. **Fix Suggestions**: Do messages include actionable fix suggestions?
   - Direct guidance on how to refactor
   - Links to documentation or best practices
   - Code examples showing correct patterns

3. **Prioritization Support**: Can smells be prioritized for due diligence reporting?
   - Severity levels (ERROR, WARNING, INFO)
   - DD smell categories for grouping
   - Risk-based ordering capability

4. **Integration Fit**: Is output suitable for DD Platform integration?
   - JSON output with DD smell IDs
   - Line numbers for code mapping
   - Category metadata for aggregation

## Example Quality Assessment

**Good Message Example:**
```
"async void should only be used for event handlers. Convert to async Task for better error handling and testability."
```

**Poor Message Example:**
```
"async void detected"
```

## Scoring Rubric

Score 1-5 where:
- **5 (Excellent)**: Clear messages explaining impact, fix suggestions, DD metadata, documentation links
- **4 (Good)**: Clear messages, some fix suggestions, severity levels, DD smell IDs present
- **3 (Acceptable)**: Understandable messages, limited fix guidance, basic severity
- **2 (Poor)**: Confusing messages, no fix suggestions, weak categorization
- **1 (Unacceptable)**: Unclear messages, not actionable, no prioritization

## Response Format

Respond ONLY with valid JSON (no markdown, no explanation before or after):
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
    "<how to improve message clarity>",
    "<metadata to add for better integration>"
  ],
  "sub_scores": {
    "message_clarity": <1-5>,
    "fix_suggestions": <1-5>,
    "prioritization_support": <1-5>,
    "integration_fit": <1-5>
  }
}
```
