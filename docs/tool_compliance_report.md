# Tool Compliance Report

Generated: `2026-02-04T12:59:39.078369+00:00`

Summary: 0 passed, 1 failed, 1 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| pmd-cpd | fail | 33 | 18 | run.evaluate, evaluation.quality, run.evaluate_llm, evaluation.llm_quality, structure.paths, evaluation.synthetic_context, evaluation.scorecard, evaluation.programmatic_exists, evaluation.programmatic_schema, evaluation.programmatic_quality, evaluation.llm_exists, evaluation.llm_schema, evaluation.llm_includes_programmatic, evaluation.llm_decision_quality, evaluation.rollup_validation, adapter.integration, sot.dbt_staging_model, dbt.model_coverage |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| pmd-cpd | `output.schema_validate` | 104.28 |
| pmd-cpd | `adapter.compliance` | 77.89 |
| pmd-cpd | `sql.cross_tool_join_patterns` | 12.73 |
| pmd-cpd | `entity.repository_alignment` | 5.40 |
| pmd-cpd | `evaluation.synthetic_context` | 2.39 |
| pmd-cpd | `adapter.schema_alignment` | 1.51 |
| pmd-cpd | `output.paths` | 1.34 |
| pmd-cpd | `dbt.model_coverage` | 0.77 |
| pmd-cpd | `docs.eval_strategy_structure` | 0.30 |
| pmd-cpd | `evaluation.rollup_validation` | 0.29 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| pmd-cpd | 0.21 |

## pmd-cpd

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/outputs/E435CB8A-BEE1-45B5-B12F-929ED68B35E9/output.json | - | - |
| `run.evaluate` | fail | high | 0.00 | No evaluation output found - run with --run-evaluate or execute 'make evaluate' | - | - | - |
| `evaluation.quality` | fail | high | 0.00 | Evaluation quality check skipped (no outputs) | - | - | - |
| `run.evaluate_llm` | fail | medium | 0.00 | No LLM evaluation output found - run with --run-llm or execute 'make evaluate-llm' | - | - | - |
| `evaluation.llm_quality` | fail | medium | 0.00 | LLM evaluation quality check skipped (no outputs) | - | - | - |
| `output.load` | pass | high | 0.23 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/outputs/E435CB8A-BEE1-45B5-B12F-929ED68B35E9/output.json | - | - |
| `output.paths` | pass | high | 1.34 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.02 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.05 | Path consistency validated | Checked 49 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.00 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.00 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.00 | Tool name matches data.tool | pmd-cpd, pmd-cpd | - | - |
| `output.metadata_consistency` | pass | medium | 0.03 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.08 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 104.28 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | fail | high | 0.23 | Missing required paths | eval-repos/real, evaluation/scorecard.md | - | - |
| `make.targets` | pass | high | 0.13 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.01 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.18 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.13 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.09 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.06 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.28 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.30 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.04 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.04 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.14 | LLM judge count meets minimum (4 >= 4) | duplication_accuracy.py, actionability.py, semantic_detection.py, cross_file_detection.py | - | - |
| `evaluation.synthetic_context` | fail | high | 2.39 | Primary judge (duplication_accuracy.py) missing synthetic context injection in collect_evidence() | missing keys: synthetic_baseline, interpretation_guidance, evaluation_mode | - | - |
| `evaluation.ground_truth` | pass | high | 0.15 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | fail | medium | 0.01 | Scorecard missing | evaluation/scorecard.md | - | - |
| `evaluation.programmatic_exists` | fail | high | 0.02 | Missing evaluation_report.json at uniform path | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | fail | high | 0.01 | Cannot validate schema - file missing | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_quality` | fail | high | 0.01 | Cannot check quality - file missing | evaluation/results/evaluation_report.json | - | - |
| `evaluation.llm_exists` | fail | medium | 0.01 | Missing llm_evaluation.json at uniform path | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | fail | medium | 0.01 | Cannot validate schema - file missing | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_includes_programmatic` | fail | medium | 0.01 | Cannot check - file missing | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_decision_quality` | fail | medium | 0.01 | Cannot check quality - file missing | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.rollup_validation` | fail | high | 0.29 | Rollup Validation section incomplete | Missing test paths: src/sot-engine/dbt/tests/test_rollup_pmd_cpd_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 77.89 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.51 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | fail | high | 0.07 | No fixture file found for integration test | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/sot-engine/persistence/fixtures/pmd_cpd_output.json, /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/sot-engine/persistence/fixtures/pmd-cpd_output.json, /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/sot-engine/persistence/fixtures/pmd-cpd_output.json, /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/evaluation/ground-truth/synthetic.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.24 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.13 | Adapter PmdCpdAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.19 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.10 | Tool 'pmd-cpd' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | fail | high | 0.21 | No dbt staging models found for tool | Expected: stg_*pmd_cpd*.sql in /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/sot-engine/dbt/models/staging | - | - |
| `dbt.model_coverage` | fail | high | 0.77 | Missing dbt model coverage | No staging models matching stg_*pmd_cpd*.sql, Missing rollup model for directory_direct_counts (duplicate metrics for files directly in directory), Missing rollup model for directory_recursive_counts (duplicate metrics for all files in subtree) | - | - |
| `entity.repository_alignment` | pass | high | 5.40 | All entities have aligned repositories | PmdCpdFileMetric, PmdCpdDuplication, PmdCpdOccurrence | - | - |
| `test.structure_naming` | pass | medium | 0.29 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 12.73 | Cross-tool SQL joins use correct patterns (130 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.07 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |
