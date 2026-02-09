# Tool Compliance Report

Generated: `2026-02-09T16:29:21.064527+00:00`

Summary: 1 passed, 0 failed, 1 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| trivy | pass | 51 | 0 | - |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| trivy | `output.schema_validate` | 178.40 |
| trivy | `adapter.compliance` | 110.37 |
| trivy | `adapter.integration` | 83.40 |
| trivy | `sql.cross_tool_join_patterns` | 29.37 |
| trivy | `evaluation.synthetic_context` | 23.61 |
| trivy | `entity.repository_alignment` | 10.21 |
| trivy | `make.targets` | 8.09 |
| trivy | `evaluation.quality` | 3.36 |
| trivy | `evaluation.llm_quality` | 3.11 |
| trivy | `schema.version_alignment` | 2.94 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| trivy | 0.47 |

## trivy

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/outputs/7a9c794e-4b86-4a18-820e-7b89459c9932/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 3.36 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/evaluation/llm/results/synthetic-llm-eval.json | - | - |
| `evaluation.llm_quality` | pass | medium | 3.11 | LLM evaluation score meets threshold | score=4.0 | - | - |
| `output.load` | pass | high | 1.55 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/outputs/7a9c794e-4b86-4a18-820e-7b89459c9932/output.json | - | - |
| `output.paths` | pass | high | 0.40 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.02 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.07 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.02 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.02 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.02 | Tool name matches data.tool | trivy, trivy | - | - |
| `output.metadata_consistency` | pass | medium | 0.13 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 2.94 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 178.40 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.25 | All required paths present | - | - | - |
| `make.targets` | pass | high | 8.09 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.08 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.36 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.15 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.11 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.12 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 2.70 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 1.42 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.11 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.10 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.22 | LLM judge count meets minimum (7 >= 4) | freshness_quality.py, vulnerability_detection.py, vulnerability_accuracy.py, severity_accuracy.py, iac_quality.py, sbom_completeness.py, false_positive_rate.py | - | - |
| `evaluation.synthetic_context` | pass | high | 23.61 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: vulnerability_accuracy.py, prompt: vulnerability_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.11 | Ground truth files present | dotnet-outdated.json, js-fullstack.json, vulnerable-npm.json, iac-terraform.json, no-vulnerabilities.json, iac-misconfigs.json, mixed-severity.json, java-outdated.json, critical-cves.json, outdated-deps.json, cfn-misconfigs.json, k8s-misconfigs.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.24 | Programmatic evaluation schema valid | timestamp, tool, version, decision, score, classification, overall_score, summary, checks, dimensions | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.17 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.37 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.10 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.07 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.21 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_trivy_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 110.37 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.43 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 83.40 | Adapter successfully persisted fixture data | Fixture: trivy_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.72 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.23 | Adapter TrivyAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.28 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.13 | Tool 'trivy' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.22 | dbt staging model(s) found | stg_trivy_file_metrics.sql, stg_trivy_iac_misconfigs.sql, stg_trivy_vulnerabilities.sql, stg_trivy_target_metrics.sql, stg_trivy_targets.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.66 | dbt models present for tool | stg_trivy_file_metrics.sql, stg_trivy_iac_misconfigs.sql, stg_trivy_vulnerabilities.sql, stg_trivy_target_metrics.sql, stg_trivy_targets.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.21 | All entities have aligned repositories | TrivyVulnerability, TrivyTarget, TrivyIacMisconfig | - | - |
| `test.structure_naming` | pass | medium | 0.40 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 29.37 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.64 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |
