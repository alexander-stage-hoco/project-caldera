# Tool Compliance Report

Generated: `2026-02-05T12:56:51.427566+00:00`

Summary: 1 passed, 0 failed, 1 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| roslyn-analyzers | pass | 51 | 0 | - |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| roslyn-analyzers | `output.schema_validate` | 130.35 |
| roslyn-analyzers | `adapter.compliance` | 77.80 |
| roslyn-analyzers | `adapter.integration` | 38.74 |
| roslyn-analyzers | `output.paths` | 16.11 |
| roslyn-analyzers | `sql.cross_tool_join_patterns` | 14.01 |
| roslyn-analyzers | `evaluation.synthetic_context` | 11.10 |
| roslyn-analyzers | `entity.repository_alignment` | 6.51 |
| roslyn-analyzers | `output.load` | 1.65 |
| roslyn-analyzers | `adapter.schema_alignment` | 1.62 |
| roslyn-analyzers | `make.targets` | 1.29 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| roslyn-analyzers | 0.31 |

## roslyn-analyzers

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/outputs/5EC5FFED-5E1E-4A75-A9ED-D2A197775B4B/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.42 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/evaluation/llm/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.39 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 1.65 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/outputs/5EC5FFED-5E1E-4A75-A9ED-D2A197775B4B/output.json | - | - |
| `output.paths` | pass | high | 16.11 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.02 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.07 | Path consistency validated | Checked 71 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | roslyn-analyzers, roslyn-analyzers | - | - |
| `output.metadata_consistency` | pass | medium | 0.04 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.34 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 130.35 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.23 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.29 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.19 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.14 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.08 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.06 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.69 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.80 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.05 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.04 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.14 | LLM judge count meets minimum (5 >= 4) | overall_quality.py, integration_fit.py, resource_management.py, security_detection.py, design_analysis.py | - | - |
| `evaluation.synthetic_context` | pass | high | 11.10 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: security_detection.py, prompt: security_detection.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.09 | Ground truth files present | clean-code.json, resource-management.json, dead-code.json, csharp.json, security-issues.json, design-violations.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.09 | Programmatic evaluation schema valid | evaluation_id, timestamp, analysis_file, decision, score, summary, category_scores, checks, decision_reason | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.08 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.29 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.06 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.05 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.33 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_roslyn_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 77.80 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.62 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 38.74 | Adapter successfully persisted fixture data | Fixture: roslyn_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.57 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.16 | Adapter RoslynAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.23 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.17 | Tool 'roslyn-analyzers' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.18 | dbt staging model(s) found | stg_lz_roslyn_violations.sql, stg_roslyn_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.65 | dbt models present for tool | stg_lz_roslyn_violations.sql, stg_roslyn_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 6.51 | All entities have aligned repositories | RoslynViolation | - | - |
| `test.structure_naming` | pass | medium | 0.46 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 14.01 | Cross-tool SQL joins use correct patterns (145 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.25 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |
