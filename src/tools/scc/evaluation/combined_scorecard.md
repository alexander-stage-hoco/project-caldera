# scc Evaluation Scorecard (Combined)

**Generated:** 2026-01-25T11:02:37.388186+00:00

---

## Summary

| Evaluation Type | Score | Weight | Weighted |
|-----------------|-------|--------|----------|
| Programmatic | 5.00/5.0 | 60% | 3.00 |
| LLM-as-Judge | 4.32/5.0 | 40% | 1.73 |
| **Combined** | **4.73/5.0** | 100% | **4.73** |

## Decision: **STRONG_PASS**

---

## Programmatic Evaluation

**Run ID:** eval-20260125-101837
**Checks:** 61/63
**Score:** 5.00/5.0

| Dimension | Passed | Total | Score |
|-----------|--------|-------|-------|
| output_quality | 8 | 8 | 5/5 |
| integration_fit | 6 | 6 | 5/5 |
| reliability | 8 | 8 | 5/5 |
| performance | 4 | 4 | 5/5 |
| installation | 4 | 4 | 5/5 |
| coverage | 9 | 9 | 5/5 |
| license | 3 | 3 | 5/5 |
| per_file | 6 | 6 | 5/5 |
| directory_analysis | 10 | 12 | 5/5 |
| cocomo | 3 | 3 | 5/5 |

---

## LLM-as-Judge Evaluation

**Run ID:** llm-eval-20260125-104034
**Average Confidence:** 0.88
**Score:** 4.32/5.0

| Dimension | Score | Weight | Confidence |
|-----------|-------|--------|------------|
| code_quality | 4/5 | 10% | 0.85 |
| integration_fit | 4/5 | 10% | 0.90 |
| documentation | 4/5 | 8% | 0.85 |
| edge_cases | 5/5 | 10% | 0.90 |
| error_messages | 4/5 | 8% | 0.85 |
| api_design | 4/5 | 10% | 0.85 |
| comparative | 4/5 | 8% | 0.85 |
| risk | 5/5 | 8% | 0.90 |
| directory_analysis | 5/5 | 14% | 0.95 |
| statistics | 4/5 | 14% | 0.85 |

---

## Decision Thresholds

| Decision | Threshold |
|----------|-----------|
| STRONG_PASS | >= 4.0 |
| PASS | >= 3.5 |
| WEAK_PASS | >= 3.0 |
| FAIL | < 3.0 |

---

*Combined score calculated as: (Programmatic × 60%) + (LLM × 40%)*