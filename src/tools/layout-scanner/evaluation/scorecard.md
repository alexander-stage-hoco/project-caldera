# Layout Scanner Scorecard

## Summary

- Status: draft
- Last updated: 2026-01-26

## Gates

| Gate | Result | Notes |
| --- | --- | --- |
| A: Structure | Pending | Validate required files and schema presence |
| B: Output | Pending | Envelope schema validation + path rules |
| C: Evaluation | Pending | Programmatic checks + LLM summary |
| D: Testing | Pending | Unit + integration tests |
| E: Rollups | Pending | Rollup validation tests in EVAL_STRATEGY |

## Evidence

- EVAL_STRATEGY: `EVAL_STRATEGY.md`
- Schemas: `schemas/output.schema.json`, `schemas/layout.json`
- Tests: `tests/unit/test_hierarchy_builder.py`
