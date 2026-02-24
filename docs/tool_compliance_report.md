# Tool Compliance Report

Generated: `2026-02-24T07:03:49.784887+00:00`

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
| sonarqube | `test.structure_naming` | 1.57 |
| scc | `test.structure_naming` | 1.50 |
| semgrep | `test.structure_naming` | 1.37 |
| roslyn-analyzers | `test.structure_naming` | 1.29 |
| gitleaks | `test.structure_naming` | 1.24 |
| pmd-cpd | `test.structure_naming` | 1.24 |
| trivy | `test.structure_naming` | 1.24 |
| devskim | `test.structure_naming` | 1.22 |
| lizard | `test.structure_naming` | 1.21 |
| dependensee | `test.structure_naming` | 1.08 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| sonarqube | 0.00 |
| scc | 0.00 |
| lizard | 0.00 |
| semgrep | 0.00 |
| layout-scanner | 0.00 |
| pmd-cpd | 0.00 |
| gitleaks | 0.00 |
| roslyn-analyzers | 0.00 |
| coverage-ingest | 0.00 |
| devskim | 0.00 |
| trivy | 0.00 |
| dependensee | 0.00 |
| git-blame-scanner | 0.00 |
| symbol-scanner | 0.00 |
| git-sizer | 0.00 |
| git-fame | 0.00 |
| dotcover | 0.00 |
| scancode | 0.00 |

## coverage-ingest

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.21 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.47 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.12 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.16 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.15 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.23 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.36 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.09 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.47 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.29 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.07 | Test structure and naming conventions followed | - | - | - |

## dependensee

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.19 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.36 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.04 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.07 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.05 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.10 | evaluate target input path is valid | input: $(LATEST_OUTPUT) | - | - |
| `schema.draft` | pass | medium | 0.34 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.52 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.32 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.08 | Test structure and naming conventions followed | - | - | - |

## devskim

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.18 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.33 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.04 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.07 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.39 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.12 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.37 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.49 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.22 | Test structure and naming conventions followed | - | - | - |

## dotcover

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.18 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.39 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.01 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.04 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.08 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.05 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.07 | evaluate target input path is valid | input: $(SYNTHETIC_OUTPUT_DIR) | - | - |
| `schema.draft` | pass | medium | 0.41 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.07 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.30 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.45 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 0.77 | Test structure and naming conventions followed | - | - | - |

## git-blame-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.17 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.45 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.05 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.07 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.05 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.07 | evaluate target input path is valid | input: evaluation/results | - | - |
| `schema.draft` | pass | medium | 0.40 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.53 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.41 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 0.83 | Test structure and naming conventions followed | - | - | - |

## git-fame

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.18 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.33 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.04 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.08 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.05 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.06 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.40 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.07 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.45 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.44 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 0.94 | Test structure and naming conventions followed | - | - | - |

## git-sizer

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.18 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.41 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.01 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.04 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.10 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.09 | evaluate target input path is valid | input: evaluation/results | - | - |
| `schema.draft` | pass | medium | 0.39 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.32 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.50 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 0.91 | Test structure and naming conventions followed | - | - | - |

## gitleaks

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.17 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.39 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.01 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.04 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.08 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.06 | evaluate target input path is valid | input: outputs/runs | - | - |
| `schema.draft` | pass | medium | 0.34 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.07 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.54 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.83 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.24 | Test structure and naming conventions followed | - | - | - |

## layout-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.18 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.39 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.04 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.08 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.07 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.52 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.16 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.64 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.80 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 0.97 | Test structure and naming conventions followed | - | - | - |

## lizard

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.19 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.43 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.05 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.11 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.08 | evaluate target input path is valid | input: $(EVAL_OUTPUT_DIR)/output.json | - | - |
| `schema.draft` | pass | medium | 0.53 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.15 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.88 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.56 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.21 | Test structure and naming conventions followed | - | - | - |

## pmd-cpd

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.19 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.36 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.05 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.12 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.09 | evaluate target input path is valid | input: $(SYNTHETIC_OUTPUT) | - | - |
| `schema.draft` | pass | medium | 0.45 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.09 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.46 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.71 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.24 | Test structure and naming conventions followed | - | - | - |

## roslyn-analyzers

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.18 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.25 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.04 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.11 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.14 | evaluate uses $(OUTPUT_DIR) but depends on analyze | prerequisites: $(VENV_READY) analyze | - | - |
| `schema.draft` | pass | medium | 0.43 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.10 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.46 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.71 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.29 | Test structure and naming conventions followed | - | - | - |

## scancode

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.18 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.31 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.01 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.04 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.08 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.06 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.34 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.33 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.37 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 0.95 | Test structure and naming conventions followed | - | - | - |

## scc

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.24 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.39 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.06 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.07 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.51 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.14 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.63 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.68 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.50 | Test structure and naming conventions followed | - | - | - |

## semgrep

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.20 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.39 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.05 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.12 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.10 | evaluate target input path is valid | input: evaluation/results/output.json | - | - |
| `schema.draft` | pass | medium | 0.37 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.10 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.66 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.64 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.37 | Test structure and naming conventions followed | - | - | - |

## sonarqube

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.18 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.39 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.18 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.16 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.34 | analyze target produces output.json | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.17 | evaluate target input path is valid | input: evaluation/results/output.json | - | - |
| `schema.draft` | pass | medium | 0.54 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.10 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.65 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.68 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.57 | Test structure and naming conventions followed | - | - | - |

## symbol-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.20 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.34 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.05 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.08 | evaluate target input path is valid | input: $(EVAL_OUTPUT_DIR)/output.json | - | - |
| `schema.draft` | pass | medium | 0.41 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.09 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.32 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.43 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.02 | Test structure and naming conventions followed | - | - | - |

## trivy

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `structure.paths` | pass | high | 0.18 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.22 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.01 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.04 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.08 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.05 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.06 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.36 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.10 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.51 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.38 | EVAL_STRATEGY.md has required sections | - | - | - |
| `test.structure_naming` | pass | medium | 1.24 | Test structure and naming conventions followed | - | - | - |
