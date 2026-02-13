# Symbol Scanner Evaluation Scorecard

**Decision:** PASS
**Score:** 97.3%

## Summary

| Metric | Value |
|--------|-------|
| Total Repos | 25 |
| Passed | 22 |
| Warned | 0 |
| Failed | 3 |
| Average F1 | 87.58% |

## Aggregate Metrics

| Category | Precision | Recall | F1 |
|----------|-----------|--------|-----|
| Symbols | 97.90% | 94.24% | 96.03% |
| Calls | 100.00% | 98.09% | 99.03% |
| Imports | 100.00% | 86.30% | 92.65% |
| **Overall** | - | - | **97.27%** |

## Per-Repository Results

| Repository | Symbols F1 | Calls F1 | Imports F1 | Overall F1 | Status |
|------------|------------|----------|------------|------------|--------|
| async-patterns | 100.00% | 100.00% | 100.00% | 100.00% | Pass |
| circular-imports | 100.00% | 100.00% | 100.00% | 100.00% | Pass |
| class-hierarchy | 100.00% | 100.00% | 100.00% | 100.00% | Pass |
| confusing-names | 100.00% | 100.00% | 100.00% | 100.00% | Pass |
| cross-module-calls | 100.00% | 100.00% | 100.00% | 100.00% | Pass |
| dataclasses-protocols | 100.00% | 100.00% | 100.00% | 100.00% | Pass |
| decorators-advanced | 97.87% | 100.00% | 100.00% | 99.03% | Pass |
| deep-hierarchy | 100.00% | 100.00% | 100.00% | 100.00% | Pass |
| deep-nesting-stress | 100.00% | 100.00% | 100.00% | 100.00% | Pass |
| dynamic-code-generation | 100.00% | 100.00% | 100.00% | 100.00% | Pass |
| encoding-edge-cases | 100.00% | 100.00% | 100.00% | 100.00% | Pass |
| generators-comprehensions | 100.00% | 100.00% | 100.00% | 100.00% | Pass |
| import-patterns | 100.00% | 100.00% | 100.00% | 100.00% | Pass |
| js-cross-module-calls | 0.00% | 0.00% | 0.00% | 0.00% | Fail |
| js-simple-functions | 0.00% | 0.00% | 0.00% | 0.00% | Fail |
| large-file | 98.48% | 100.00% | 100.00% | 99.34% | Pass |
| metaprogramming | 99.07% | 100.00% | 100.00% | 99.53% | Pass |
| modern-syntax | 100.00% | 100.00% | 100.00% | 100.00% | Pass |
| nested-structures | 93.67% | 100.00% | 100.00% | 95.05% | Pass |
| partial-syntax-errors | 100.00% | 100.00% | 100.00% | 100.00% | Pass |
| simple-functions | 100.00% | 100.00% | 100.00% | 100.00% | Pass |
| ts-class-hierarchy | 0.00% | 0.00% | 0.00% | 0.00% | Fail |
| type-checking-imports | 92.86% | 100.00% | 100.00% | 97.14% | Pass |
| unresolved-externals | 100.00% | 100.00% | 100.00% | 100.00% | Pass |
| web-framework-patterns | 98.90% | 100.00% | 100.00% | 99.53% | Pass |

## Thresholds

- **PASS:** >= 95%
- **WARN:** 85% - 95%
- **FAIL:** < 85%

## Notes

3 JS/TS ground-truth repos (js-simple-functions, js-cross-module-calls, ts-class-hierarchy) scored 0% F1 — the evaluate pipeline does not yet run JS/TS analysis on these repos. Python repos: 22/22 pass with 99.5%+ average F1.
