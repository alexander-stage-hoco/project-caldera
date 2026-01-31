# roslyn-analyzers Evaluation Scorecard

- Status: STRONG_PASS
- Last updated: 2026-01-22T13:05:00Z
- Source: `output/runs/evaluation_report.json`

## Summary
- Overall score: 96.3% (29/30 checks passed)
- Accuracy: 100% (10/10)
- Coverage: 100% (8/8)
- Edge cases: 100% (8/8)
- Performance: 75.0% (3/4)

## Notable Findings
- PF-1 (Synthetic analysis speed) failed at ~32s vs 30s threshold.

## Next Steps
- Consider raising the PF-1 threshold or optimizing analysis duration.
- Run LLM judge evaluation and capture findings.
