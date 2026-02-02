# Tool Compliance Report

Generated: `2026-02-02T18:16:43.438971+00:00`

Summary: 1 passed, 0 failed, 1 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| gitleaks | pass | 11 | 0 | - |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| gitleaks | `test.structure_naming` | 1.05 |
| gitleaks | `docs.blueprint_structure` | 0.85 |
| gitleaks | `docs.eval_strategy_structure` | 0.78 |
| gitleaks | `make.targets` | 0.62 |
| gitleaks | `schema.draft` | 0.43 |
| gitleaks | `structure.paths` | 0.42 |
| gitleaks | `make.uses_common` | 0.19 |
| gitleaks | `make.output_dir_convention` | 0.14 |
| gitleaks | `make.output_filename` | 0.14 |
| gitleaks | `schema.contract` | 0.08 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| gitleaks | 0.00 |

## gitleaks

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.42 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.62 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.19 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.14 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.14 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.43 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.85 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.78 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.05 | Test structure and naming conventions followed | - | - | - |
