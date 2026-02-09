# Tool Compliance Report

Generated: `2026-02-08T20:54:40.391360+00:00`

Summary: 1 passed, 0 failed, 1 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| git-blame-scanner | pass | 11 | 0 | - |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| git-blame-scanner | `test.structure_naming` | 0.79 |
| git-blame-scanner | `docs.blueprint_structure` | 0.54 |
| git-blame-scanner | `schema.draft` | 0.36 |
| git-blame-scanner | `make.targets` | 0.28 |
| git-blame-scanner | `docs.eval_strategy_structure` | 0.25 |
| git-blame-scanner | `schema.contract` | 0.24 |
| git-blame-scanner | `structure.paths` | 0.19 |
| git-blame-scanner | `make.output_filename` | 0.17 |
| git-blame-scanner | `make.output_dir_convention` | 0.16 |
| git-blame-scanner | `make.uses_common` | 0.12 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| git-blame-scanner | 0.00 |

## git-blame-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.19 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.28 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.12 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.16 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.17 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.36 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.24 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.54 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.25 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 0.79 | Test structure and naming conventions followed | - | - | - |
