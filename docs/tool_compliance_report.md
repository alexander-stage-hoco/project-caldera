# Tool Compliance Report

Generated: `2026-03-01T09:47:48.112289+00:00`

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
| pmd-cpd | `test.structure_naming` | 2.74 |
| coverage-ingest | `test.structure_naming` | 2.67 |
| devskim | `test.structure_naming` | 2.02 |
| gitleaks | `test.structure_naming` | 1.81 |
| sonarqube | `test.structure_naming` | 1.80 |
| scc | `test.structure_naming` | 1.69 |
| symbol-scanner | `test.structure_naming` | 1.63 |
| dependensee | `test.structure_naming` | 1.58 |
| roslyn-analyzers | `test.structure_naming` | 1.58 |
| semgrep | `test.structure_naming` | 1.51 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| pmd-cpd | 0.01 |
| coverage-ingest | 0.01 |
| git-fame | 0.01 |
| devskim | 0.01 |
| dotcover | 0.01 |
| git-sizer | 0.01 |
| sonarqube | 0.01 |
| scc | 0.01 |
| semgrep | 0.01 |
| roslyn-analyzers | 0.00 |
| gitleaks | 0.00 |
| git-blame-scanner | 0.00 |
| dependensee | 0.00 |
| layout-scanner | 0.00 |
| trivy | 0.00 |
| lizard | 0.00 |
| symbol-scanner | 0.00 |
| scancode | 0.00 |

## coverage-ingest

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.23 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.48 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.15 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.18 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.17 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.27 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.30 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.10 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.75 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 1.10 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 2.67 | Test structure and naming conventions followed | - | - | - |

## dependensee

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.23 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.61 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.09 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.18 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.19 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.15 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.31 | evaluate target input path is valid | input: $(LATEST_OUTPUT) | - | - |
| `schema.draft` | pass | medium | 0.36 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.13 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.58 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.37 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.58 | Test structure and naming conventions followed | - | - | - |

## devskim

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.23 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.41 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.07 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.11 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.10 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.86 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.35 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.75 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 1.12 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 2.02 | Test structure and naming conventions followed | - | - | - |

## dotcover

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.60 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.47 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.06 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.13 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.12 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.23 | evaluate target input path is valid | input: $(SYNTHETIC_OUTPUT_DIR) | - | - |
| `schema.draft` | pass | medium | 0.63 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.11 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.42 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.65 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.22 | Test structure and naming conventions followed | - | - | - |

## git-blame-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.21 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.56 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.08 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.23 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.28 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.11 | evaluate target input path is valid | input: evaluation/results | - | - |
| `schema.draft` | pass | medium | 0.38 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.10 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.64 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.81 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.41 | Test structure and naming conventions followed | - | - | - |

## git-fame

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.23 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.59 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.09 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.12 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.13 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.29 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.19 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.58 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.28 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 1.14 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 1.01 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.50 | Test structure and naming conventions followed | - | - | - |

## git-sizer

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.68 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.93 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.09 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.13 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.30 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.21 | evaluate target input path is valid | input: evaluation/results | - | - |
| `schema.draft` | pass | medium | 0.40 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.12 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.42 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.70 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.25 | Test structure and naming conventions followed | - | - | - |

## gitleaks

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.23 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.31 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.07 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.10 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.09 | evaluate target input path is valid | input: outputs/runs | - | - |
| `schema.draft` | pass | medium | 0.28 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.13 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.83 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.94 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.81 | Test structure and naming conventions followed | - | - | - |

## layout-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.26 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.38 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.08 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.12 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.09 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.46 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.25 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.73 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 1.03 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.18 | Test structure and naming conventions followed | - | - | - |

## lizard

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.25 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.31 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.06 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.14 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.09 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.11 | evaluate target input path is valid | input: $(EVAL_OUTPUT_DIR)/output.json | - | - |
| `schema.draft` | pass | medium | 0.39 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.19 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.80 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.67 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.14 | Test structure and naming conventions followed | - | - | - |

## pmd-cpd

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.26 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.59 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.12 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.24 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.33 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.15 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.32 | evaluate target input path is valid | input: $(SYNTHETIC_OUTPUT) | - | - |
| `schema.draft` | pass | medium | 0.48 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.23 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.95 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 1.38 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 2.74 | Test structure and naming conventions followed | - | - | - |

## roslyn-analyzers

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.28 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.48 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.07 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.15 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.19 | evaluate uses $(OUTPUT_DIR) but depends on analyze | prerequisites: $(VENV_READY) analyze | - | - |
| `schema.draft` | pass | medium | 0.55 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.13 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.47 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.91 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.58 | Test structure and naming conventions followed | - | - | - |

## scancode

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.25 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.53 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.06 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.10 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.08 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.42 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.12 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.47 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.59 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.12 | Test structure and naming conventions followed | - | - | - |

## scc

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.25 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.37 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.08 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.14 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.11 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.48 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.18 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.78 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.89 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.69 | Test structure and naming conventions followed | - | - | - |

## semgrep

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.25 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.45 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.07 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.17 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.11 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.13 | evaluate target input path is valid | input: evaluation/results/output.json | - | - |
| `schema.draft` | pass | medium | 0.43 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.14 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.88 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.89 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.51 | Test structure and naming conventions followed | - | - | - |

## sonarqube

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.26 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.48 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.05 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.09 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.19 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.12 | analyze target produces output.json | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.14 | evaluate target input path is valid | input: evaluation/results/output.json | - | - |
| `schema.draft` | pass | medium | 0.14 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.11 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.84 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.92 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.80 | Test structure and naming conventions followed | - | - | - |

## symbol-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.26 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.40 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.07 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.12 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.11 | evaluate target input path is valid | input: $(EVAL_OUTPUT_DIR)/output.json | - | - |
| `schema.draft` | pass | medium | 0.16 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.12 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.45 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.58 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.63 | Test structure and naming conventions followed | - | - | - |

## trivy

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.54 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.53 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.08 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.11 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.14 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.10 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.19 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.15 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.78 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.54 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.38 | Test structure and naming conventions followed | - | - | - |
