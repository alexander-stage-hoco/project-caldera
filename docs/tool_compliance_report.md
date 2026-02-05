# Tool Compliance Report

Generated: `2026-02-05T09:33:03.084692+00:00`

Summary: 1 passed, 0 failed, 1 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| dotcover | pass | 11 | 0 | - |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| dotcover | `docs.eval_strategy_structure` | 0.43 |
| dotcover | `docs.blueprint_structure` | 0.35 |
| dotcover | `structure.paths` | 0.34 |
| dotcover | `test.structure_naming` | 0.31 |
| dotcover | `make.targets` | 0.20 |
| dotcover | `schema.draft` | 0.17 |
| dotcover | `schema.contract` | 0.14 |
| dotcover | `make.output_dir_convention` | 0.09 |
| dotcover | `make.uses_common` | 0.08 |
| dotcover | `make.output_filename` | 0.07 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| dotcover | 0.00 |

## dotcover

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.34 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.20 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.01 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.08 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.17 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.14 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.35 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.43 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 0.31 | Test structure and naming conventions followed | - | - | - |
