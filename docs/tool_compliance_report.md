# Tool Compliance Report

Generated: `2026-02-09T20:17:41.093510+00:00`

Summary: 1 passed, 0 failed, 1 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| devskim | pass | 11 | 0 | - |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| devskim | `make.targets` | 1.37 |
| devskim | `test.structure_naming` | 0.74 |
| devskim | `docs.blueprint_structure` | 0.69 |
| devskim | `schema.draft` | 0.66 |
| devskim | `docs.eval_strategy_structure` | 0.41 |
| devskim | `structure.paths` | 0.12 |
| devskim | `make.uses_common` | 0.12 |
| devskim | `make.output_dir_convention` | 0.11 |
| devskim | `make.output_filename` | 0.10 |
| devskim | `schema.contract` | 0.09 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| devskim | 0.00 |

## devskim

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.12 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.37 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.12 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.11 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target output pattern acceptable | - | - | - |
| `schema.draft` | pass | medium | 0.66 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.09 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.69 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.41 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 0.74 | Test structure and naming conventions followed | - | - | - |
