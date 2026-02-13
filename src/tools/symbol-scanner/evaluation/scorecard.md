# Symbol Scanner Evaluation Scorecard

**Decision:** ✅ PASS
**Score:** 99.5%
**Timestamp:** 2026-02-13T18:16:49.295741+00:00

## Summary

| Metric | Value |
|--------|-------|
| Total Repos | 25 |
| Passed | 25 |
| Warned | 0 |
| Failed | 0 |
| Average F1 | 99.58% |

## Aggregate Metrics

| Category | Precision | Recall | F1 |
|----------|-----------|--------|-----|
| Symbols | 98.03% | 100.00% | 99.01% |
| Calls | 100.00% | 100.00% | 100.00% |
| Imports | 100.00% | 100.00% | 100.00% |
| **Overall** | - | - | **99.53%** |

## Per-Repository Results

| Repository | Symbols F1 | Calls F1 | Imports F1 | Overall F1 | Status |
|------------|------------|----------|------------|------------|--------|
| async-patterns | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| circular-imports | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| class-hierarchy | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| confusing-names | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| cross-module-calls | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| dataclasses-protocols | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| decorators-advanced | 97.87% | 100.00% | 100.00% | 99.03% | ✅ |
| deep-hierarchy | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| deep-nesting-stress | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| dynamic-code-generation | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| encoding-edge-cases | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| generators-comprehensions | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| import-patterns | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| js-cross-module-calls | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| js-simple-functions | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| large-file | 98.48% | 100.00% | 100.00% | 99.34% | ✅ |
| metaprogramming | 99.07% | 100.00% | 100.00% | 99.53% | ✅ |
| modern-syntax | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| nested-structures | 93.67% | 100.00% | 100.00% | 95.05% | ✅ |
| partial-syntax-errors | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| simple-functions | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| ts-class-hierarchy | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| type-checking-imports | 92.86% | 100.00% | 100.00% | 97.14% | ✅ |
| unresolved-externals | 100.00% | 100.00% | 100.00% | 100.00% | ✅ |
| web-framework-patterns | 98.90% | 100.00% | 100.00% | 99.53% | ✅ |

## Thresholds

- **PASS:** ≥ 95%
- **WARN:** 85% - 95%
- **FAIL:** < 85%
