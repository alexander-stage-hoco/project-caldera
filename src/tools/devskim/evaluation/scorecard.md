# devskim Evaluation Scorecard

- Status: STRONG_PASS
- Last updated: 2026-01-22T12:45:00Z
- Source: `evaluation/results/evaluation_report.json`

## Summary
- Overall score: 94.3% (29/30 checks passed)
- Accuracy: 100% (8/8)
- Coverage: 100% (8/8)
- Edge cases: 86.2% (8/8)
- Performance: 85.0% (3/4)

## Notable Findings
- PF-3 (lines per second throughput) failed at 887 lines/second vs 1000 target.

## Next Steps
- Revisit PF-3 threshold or add caching/parallelism to improve throughput.
- Run LLM judge evaluation and capture findings.
