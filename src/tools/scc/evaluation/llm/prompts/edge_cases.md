# Edge Cases Judge

You are evaluating how well scc **handles edge cases** encountered in real-world codebases.

## Evaluation Dimension

**Edge Case Handling (10% weight)**: Are unusual files and edge cases handled gracefully?

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | Excellent: All edge cases handled gracefully with appropriate output |
| 4 | Good: Most edge cases work, minor issues with exotic cases |
| 3 | Acceptable: Common edge cases work, some failures on unusual files |
| 2 | Poor: Frequent failures or crashes on edge cases |
| 1 | Fails: Cannot process many valid files |

## Edge Cases to Test

1. **Empty files** - Should report 0 lines, not error
2. **Comment-only files** - Should show 0 code lines, >0 comment lines
3. **Single-line files** - Should count correctly
4. **Unicode files** (UTF-8, UTF-16, emoji) - Should parse without crash
5. **Deep nesting** - Should report complexity
6. **Minified files** - Should detect or flag
7. **Generated files** - Should detect or flag
8. **Binary files** - Should skip or ignore
9. **Symlinks** - Should handle without infinite loops

## Evidence to Evaluate

{{ evidence }}

### Edge Case Test Results
```json
{{ edge_case_results }}
```

### Error Messages (if any)
{{ error_output }}

## Evaluation Questions

1. Do empty files produce valid (0-count) output?
2. Are comment-only files counted correctly?
3. Does Unicode cause crashes or incorrect counts?
4. Are minified/generated files flagged appropriately?
5. Is the tool deterministic across multiple runs?

## Required Output Format

```json
{
  "dimension": "edge_cases",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific test results>"],
  "recommendations": ["<edge case handling improvements>"]
}
```
