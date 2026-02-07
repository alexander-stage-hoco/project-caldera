# Tool Compliance Report

Generated: `2026-02-07T10:28:42.787656+00:00`

Summary: 1 passed, 0 failed, 1 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| dotcover | pass | 51 | 0 | - |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| dotcover | `adapter.compliance` | 153.97 |
| dotcover | `output.schema_validate` | 145.38 |
| dotcover | `adapter.integration` | 95.58 |
| dotcover | `sql.cross_tool_join_patterns` | 39.87 |
| dotcover | `entity.repository_alignment` | 12.89 |
| dotcover | `evaluation.synthetic_context` | 8.76 |
| dotcover | `adapter.schema_alignment` | 3.02 |
| dotcover | `adapter.quality_rules_coverage` | 0.94 |
| dotcover | `output.paths` | 0.59 |
| dotcover | `output.metadata_consistency` | 0.46 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| dotcover | 0.47 |

## dotcover

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/outputs/dotcover-test-run/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.09 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.06 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 0.07 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/outputs/dotcover-test-run/output.json | - | - |
| `output.paths` | pass | high | 0.59 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.02 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | dotcover, dotcover | - | - |
| `output.metadata_consistency` | pass | medium | 0.46 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.42 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 145.38 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.29 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.20 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.23 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.14 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.11 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.06 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.20 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.13 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.04 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.20 | LLM judge count meets minimum (4 >= 4) | false_positive.py, actionability.py, integration.py, accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 8.76 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: accuracy.py, prompt: accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.04 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.06 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.04 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.05 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.05 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=WEAK_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.04 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.19 | Rollup Validation declared with valid tests | src/tools/dotcover/tests/unit/test_analyze.py | - | - |
| `adapter.compliance` | pass | info | 153.97 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.02 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 95.58 | Adapter successfully persisted fixture data | Fixture: dotcover_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.94 | All 3 quality rules have implementation coverage | coverage_bounds, statement_invariants, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.35 | Adapter DotcoverAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.39 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.38 | Tool 'dotcover' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.45 | dbt staging model(s) found | stg_dotcover_file_metrics.sql, stg_lz_dotcover_type_coverage.sql, stg_lz_dotcover_method_coverage.sql, stg_lz_dotcover_assembly_coverage.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.23 | dbt models present for tool | stg_dotcover_file_metrics.sql, stg_lz_dotcover_type_coverage.sql, stg_lz_dotcover_method_coverage.sql, stg_lz_dotcover_assembly_coverage.sql | - | - |
| `entity.repository_alignment` | pass | high | 12.89 | All entities have aligned repositories | DotcoverAssemblyCoverage, DotcoverTypeCoverage, DotcoverMethodCoverage | - | - |
| `test.structure_naming` | pass | medium | 0.45 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 39.87 | Cross-tool SQL joins use correct patterns (170 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.17 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |
