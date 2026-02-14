# Tool Compliance Report

Generated: `2026-02-14T18:43:57.371614+00:00`

Summary: 18 passed, 0 failed, 18 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| coverage-ingest | pass | 11 | 0 | - |
| dependensee | pass | 12 | 0 | - |
| devskim | pass | 11 | 0 | - |
| dotcover | pass | 12 | 0 | - |
| git-blame-scanner | pass | 12 | 0 | - |
| git-fame | pass | 11 | 0 | - |
| git-sizer | pass | 12 | 0 | - |
| gitleaks | pass | 12 | 0 | - |
| layout-scanner | pass | 11 | 0 | - |
| lizard | pass | 12 | 0 | - |
| pmd-cpd | pass | 12 | 0 | - |
| roslyn-analyzers | pass | 12 | 0 | - |
| scancode | pass | 11 | 0 | - |
| scc | pass | 11 | 0 | - |
| semgrep | pass | 12 | 0 | - |
| sonarqube | pass | 12 | 0 | - |
| symbol-scanner | pass | 12 | 0 | - |
| trivy | pass | 11 | 0 | - |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| coverage-ingest | `test.structure_naming` | 6.01 |
| git-blame-scanner | `test.structure_naming` | 3.54 |
| scancode | `schema.contract` | 3.28 |
| symbol-scanner | `make.targets` | 2.81 |
| semgrep | `docs.eval_strategy_structure` | 2.73 |
| semgrep | `docs.blueprint_structure` | 2.52 |
| gitleaks | `docs.eval_strategy_structure` | 2.47 |
| semgrep | `test.structure_naming` | 2.43 |
| pmd-cpd | `test.structure_naming` | 2.34 |
| trivy | `test.structure_naming` | 2.33 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| coverage-ingest | 0.01 |
| semgrep | 0.01 |
| roslyn-analyzers | 0.01 |
| lizard | 0.01 |
| scancode | 0.01 |
| gitleaks | 0.01 |
| symbol-scanner | 0.01 |
| devskim | 0.01 |
| git-blame-scanner | 0.01 |
| layout-scanner | 0.01 |
| pmd-cpd | 0.01 |
| sonarqube | 0.01 |
| trivy | 0.01 |
| scc | 0.01 |
| dotcover | 0.01 |
| git-fame | 0.01 |
| dependensee | 0.01 |
| git-sizer | 0.00 |

## coverage-ingest

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.34 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.78 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.06 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.24 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.26 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.24 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | skip | high | 1.21 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 1.17 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.25 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 1.53 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.64 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 6.01 | Test structure and naming conventions followed | - | - | - |

## dependensee

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.46 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.59 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.07 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.12 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.13 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.09 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.28 | evaluate target input path is valid | input: $(LATEST_OUTPUT) | - | - |
| `schema.draft` | pass | medium | 0.41 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.17 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.68 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.54 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.46 | Test structure and naming conventions followed | - | - | - |

## devskim

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.63 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.85 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.09 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.16 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.30 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.40 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.25 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.89 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.48 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 1.97 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 1.58 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.63 | Test structure and naming conventions followed | - | - | - |

## dotcover

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.28 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.51 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.05 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.10 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.14 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.09 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.12 | evaluate target input path is valid | input: $(SYNTHETIC_OUTPUT_DIR) | - | - |
| `schema.draft` | pass | medium | 0.61 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.29 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.72 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 1.00 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.83 | Test structure and naming conventions followed | - | - | - |

## git-blame-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.63 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.19 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.08 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.15 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.26 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.29 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.12 | evaluate target input path is valid | input: evaluation/results | - | - |
| `schema.draft` | pass | medium | 0.94 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.42 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.72 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.61 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 3.54 | Test structure and naming conventions followed | - | - | - |

## git-fame

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.83 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.86 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.06 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.11 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.12 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.09 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.60 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.19 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.94 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.51 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.15 | Test structure and naming conventions followed | - | - | - |

## git-sizer

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.28 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.45 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.08 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.15 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.11 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.12 | evaluate target input path is valid | input: evaluation/results | - | - |
| `schema.draft` | pass | medium | 0.35 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.12 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.45 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.70 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.48 | Test structure and naming conventions followed | - | - | - |

## gitleaks

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.55 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.00 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.08 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.17 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.22 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.13 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.17 | evaluate target input path is valid | input: outputs/runs | - | - |
| `schema.draft` | pass | medium | 0.73 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.27 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 2.07 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 2.47 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.89 | Test structure and naming conventions followed | - | - | - |

## layout-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 1.01 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.54 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.14 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.16 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.37 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.26 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.97 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.50 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 2.25 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 1.29 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.30 | Test structure and naming conventions followed | - | - | - |

## lizard

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 1.08 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.03 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.10 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.32 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.72 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.78 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.53 | evaluate target input path is valid | input: $(EVAL_OUTPUT_DIR)/output.json | - | - |
| `schema.draft` | pass | medium | 1.47 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.48 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 1.28 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.94 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.34 | Test structure and naming conventions followed | - | - | - |

## pmd-cpd

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.60 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.79 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.07 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.13 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.31 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.41 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.34 | evaluate target input path is valid | input: $(SYNTHETIC_OUTPUT) | - | - |
| `schema.draft` | pass | medium | 0.82 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.65 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.92 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 1.10 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 2.34 | Test structure and naming conventions followed | - | - | - |

## roslyn-analyzers

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 1.54 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.07 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.13 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.58 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 1.22 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.38 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.57 | evaluate uses $(OUTPUT_DIR) but depends on analyze | prerequisites: $(VENV_READY) analyze | - | - |
| `schema.draft` | pass | medium | 0.72 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.29 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.98 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 1.69 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.50 | Test structure and naming conventions followed | - | - | - |

## scancode

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.60 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.71 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.05 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.13 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.12 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.51 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.15 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.77 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 3.28 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 2.04 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.90 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 0.81 | Test structure and naming conventions followed | - | - | - |

## scc

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.28 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.53 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.09 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.15 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.12 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.56 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.24 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 1.01 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 1.52 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.90 | Test structure and naming conventions followed | - | - | - |

## semgrep

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.44 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.75 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.11 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.17 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.29 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.18 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.20 | evaluate target input path is valid | input: evaluation/results/output.json | - | - |
| `schema.draft` | pass | medium | 0.66 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.24 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 2.52 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 2.73 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 2.43 | Test structure and naming conventions followed | - | - | - |

## sonarqube

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.79 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.93 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.06 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.19 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.40 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.18 | analyze target produces output.json | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.22 | evaluate target input path is valid | input: evaluation/results/output.json | - | - |
| `schema.draft` | pass | medium | 0.57 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.22 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.92 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 1.40 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 2.01 | Test structure and naming conventions followed | - | - | - |

## symbol-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.68 | All required paths present | - | - | - |
| `make.targets` | pass | high | 2.81 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.24 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 1.22 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.45 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.16 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.15 | evaluate target input path is valid | input: $(EVAL_OUTPUT_DIR)/output.json | - | - |
| `schema.draft` | pass | medium | 0.87 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.23 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 1.01 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.71 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.06 | Test structure and naming conventions followed | - | - | - |

## trivy

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.72 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.64 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.05 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.15 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.32 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.20 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.98 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.26 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 1.01 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.93 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 2.33 | Test structure and naming conventions followed | - | - | - |
