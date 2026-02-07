# Tool Compliance Report

Generated: `2026-02-06T16:08:35.601969+00:00`

Summary: 1 passed, 0 failed, 1 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| devskim | pass | 52 | 0 | - |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| devskim | `output.schema_validate` | 89.81 |
| devskim | `adapter.compliance` | 71.68 |
| devskim | `adapter.integration` | 35.35 |
| devskim | `sql.cross_tool_join_patterns` | 13.37 |
| devskim | `entity.repository_alignment` | 6.71 |
| devskim | `evaluation.synthetic_context` | 4.97 |
| devskim | `adapter.schema_alignment` | 1.74 |
| devskim | `output.paths` | 1.52 |
| devskim | `test.coverage_threshold` | 0.59 |
| devskim | `dbt.model_coverage` | 0.46 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| devskim | 0.23 |

## devskim

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/outputs/302BD23E-0445-4F82-99E2-F90732B4803B/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.11 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/evaluation/llm/results/llm-eval-20260206-155938.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.06 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 0.16 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/outputs/302BD23E-0445-4F82-99E2-F90732B4803B/output.json | - | - |
| `output.paths` | pass | high | 1.52 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.01 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.04 | Path consistency validated | Checked 31 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.00 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.00 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.00 | Tool name matches data.tool | devskim, devskim | - | - |
| `output.metadata_consistency` | pass | medium | 0.03 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.17 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 89.81 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.22 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.13 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.17 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.12 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target output pattern acceptable | - | - | - |
| `schema.draft` | pass | medium | 0.12 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.20 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.17 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.02 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.13 | LLM judge count meets minimum (4 >= 4) | rule_coverage.py, severity_calibration.py, security_focus.py, detection_accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 4.97 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: detection_accuracy.py, prompt: detection_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.05 | Ground truth files present | api-security.json, deserialization.json, xxe.json, csharp.json, clean.json | - | - |
| `evaluation.scorecard` | pass | low | 0.01 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.09 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.07 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.05 | LLM evaluation schema valid | run_id, timestamp, model, score, decision, dimensions, total_score, average_confidence, combined_score, programmatic_input | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.05 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.04 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.18 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_devskim_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 71.68 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.74 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 35.35 | Adapter successfully persisted fixture data | Fixture: devskim_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.36 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.15 | Adapter DevskimAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.20 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.10 | Tool 'devskim' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.18 | dbt staging model(s) found | stg_lz_devskim_findings.sql, stg_devskim_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.46 | dbt models present for tool | stg_lz_devskim_findings.sql, stg_devskim_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 6.71 | All entities have aligned repositories | DevskimFinding | - | - |
| `test.structure_naming` | pass | medium | 0.36 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 13.37 | Cross-tool SQL joins use correct patterns (170 files checked) | - | - | - |
| `test.coverage_threshold` | pass | high | 0.59 | Test coverage 80.7% >= 80% threshold | coverage=80.7%, threshold=80% | - | - |
