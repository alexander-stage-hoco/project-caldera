# Tool Compliance Report

Generated: `2026-02-05T22:43:58.494394+00:00`

Summary: 1 passed, 0 failed, 1 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| scancode | pass | 51 | 0 | - |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| scancode | `output.schema_validate` | 104.60 |
| scancode | `adapter.compliance` | 79.62 |
| scancode | `adapter.integration` | 34.96 |
| scancode | `sql.cross_tool_join_patterns` | 13.42 |
| scancode | `entity.repository_alignment` | 5.93 |
| scancode | `evaluation.synthetic_context` | 2.27 |
| scancode | `output.paths` | 2.19 |
| scancode | `adapter.schema_alignment` | 1.57 |
| scancode | `evaluation.llm_schema` | 0.54 |
| scancode | `evaluation.llm_includes_programmatic` | 0.51 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| scancode | 0.25 |

## scancode

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/outputs/191da4b5-931d-42d5-8fca-b0f3b37eadcc/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.47 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/evaluation/llm/results/llm-eval-20260205-223841.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.37 | LLM evaluation decision meets threshold | WEAK_PASS | - | - |
| `output.load` | pass | high | 0.20 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/outputs/191da4b5-931d-42d5-8fca-b0f3b37eadcc/output.json | - | - |
| `output.paths` | pass | high | 2.19 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.03 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.07 | Path consistency validated | Checked 84 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.00 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.00 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.00 | Tool name matches data.tool | scancode, scancode | - | - |
| `output.metadata_consistency` | pass | medium | 0.03 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.08 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 104.60 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.22 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.13 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.01 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.16 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.11 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.08 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.06 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.18 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.08 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.04 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.04 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.15 | LLM judge count meets minimum (4 >= 4) | coverage_judge.py, accuracy_judge.py, actionability_judge.py, risk_classification_judge.py | - | - |
| `evaluation.synthetic_context` | pass | high | 2.27 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: accuracy_judge.py, prompt: accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.07 | Ground truth files present | multi-license.json, mit-only.json, gpl-mixed.json, apache-bsd.json, public-domain.json, spdx-expression.json, no-license.json, dual-licensed.json | - | - |
| `evaluation.scorecard` | pass | low | 0.01 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.40 | Programmatic evaluation schema valid | timestamp, tool, version, decision, score, summary, checks, total_repositories, reports | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.35 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.54 | LLM evaluation schema valid | run_id, timestamp, model, dimensions, score, total_score, average_confidence, decision, programmatic_score, combined_score | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.51 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.51 | LLM evaluation passed | WEAK_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.16 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_scancode_repo_level_metrics.sql | - | - |
| `adapter.compliance` | pass | info | 79.62 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.57 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 34.96 | Adapter successfully persisted fixture data | Fixture: scancode_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.36 | All 3 quality rules have implementation coverage | paths, confidence, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.15 | Adapter ScancodeAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.20 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.11 | Tool 'scancode' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.17 | dbt staging model(s) found | stg_lz_scancode_summary.sql, stg_lz_scancode_file_licenses.sql, stg_scancode_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.15 | dbt models present for tool | stg_lz_scancode_summary.sql, stg_lz_scancode_file_licenses.sql, stg_scancode_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 5.93 | All entities have aligned repositories | ScancodeFileLicense, ScancodeSummary | - | - |
| `test.structure_naming` | pass | medium | 0.31 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 13.42 | Cross-tool SQL joins use correct patterns (158 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.08 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |
