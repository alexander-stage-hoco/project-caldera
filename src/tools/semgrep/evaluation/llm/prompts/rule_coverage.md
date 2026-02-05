# DD Smell Catalogue Coverage Evaluation

You are an expert code quality analyst evaluating Semgrep's rule coverage against the DD Platform's smell catalogue.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Low smell counts are NOT automatically failures
- Judge rule coverage by: Are the rules that ARE present correctly mapping to DD categories?
- Consider: A tool that covers 70% of categories on a clean codebase with proper output format deserves credit

## Context

The DD Platform defines a comprehensive smell catalogue with ~60 smell types across 9 categories. This evaluation measures what percentage of the catalogue has corresponding Semgrep rules.

## Evidence

The following JSON contains rule inventory, catalogue mapping, and uncovered smell analysis:

{{ evidence }}

## DD Smell Categories

| Category | ID Range | Example Smells |
|----------|----------|----------------|
| size_complexity (A) | A1-A7 | A1_LARGE_FILE, A2_LONG_METHOD, A3_DEEP_NESTING |
| refactoring (B) | B1-B16 | B6_MESSAGE_CHAINS, B8_SWITCH_STATEMENTS |
| dependency (C) | C1-C6 | C3_GOD_CLASS, C4_INAPPROPRIATE_INTIMACY |
| error_handling (D) | D1-D7 | D1_EMPTY_CATCH, D2_CATCH_ALL, D7_CATCH_RETURN_DEFAULT |
| async_concurrency (E) | E1-E8 | E1_SYNC_OVER_ASYNC, E2_ASYNC_VOID, E5_UNSAFE_LOCK |
| resource_management (F) | F1-F6 | F3_HTTPCLIENT_NEW, F5_DISPOSABLE_FIELD, F6_EVENT_HANDLER_LEAK |
| nullability (G) | G1-G3 | G1_NULLABLE_DISABLED, G2_NULL_FORGIVING |
| api_design (H) | H1-H8 | H3_BOOLEAN_BLINDNESS, H6_STATIC_MUTABLE_STATE |
| dead_code (I) | I1-I5 | I3_UNREACHABLE_CODE, I5_EMPTY_METHOD |

## Evaluation Questions

1. **Category Coverage**: Which DD smell categories have rules?
   - What percentage of each category is covered?
   - Are high-impact smells prioritized?

2. **Rule Quality**: Do rules have proper DD metadata?
   - dd_smell_id field present?
   - dd_category field present?
   - Accurate severity levels?

3. **Coverage Gaps**: What critical smells are missing rules?
   - Security-related smells
   - Performance-related smells
   - Maintainability smells

4. **Language Specificity**: Are language-specific patterns covered?
   - async/await patterns
   - IDisposable patterns
   - Nullable reference types

## Scoring Rubric

Score 1-5 where:
- **5 (Excellent)**: >80% catalogue coverage, all 9 categories represented, proper metadata
- **4 (Good)**: 60-80% coverage, 7-8 categories, mostly proper metadata
- **3 (Acceptable)**: 40-60% coverage, 5-6 categories, some metadata gaps
- **2 (Poor)**: 20-40% coverage, 3-4 categories, frequent metadata issues
- **1 (Unacceptable)**: <20% coverage, <3 categories, no DD metadata

## Response Format

Respond ONLY with valid JSON (no markdown, no explanation before or after):
```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<your detailed analysis of catalogue coverage>",
  "evidence_cited": [
    "<categories covered>",
    "<critical gaps identified>"
  ],
  "recommendations": [
    "<high-priority smells to add rules for>",
    "<metadata improvements needed>"
  ],
  "sub_scores": {
    "category_breadth": <1-5>,
    "smell_depth": <1-5>,
    "metadata_quality": <1-5>,
    "language_specificity": <1-5>
  }
}
```
