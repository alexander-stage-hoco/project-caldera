# Tool Compliance Report

Generated: `2026-02-06T10:40:24.232478+00:00`

Summary: 1 passed, 0 failed, 1 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| dependensee | pass | 51 | 0 | - |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| dependensee | `adapter.compliance` | 151.07 |
| dependensee | `output.schema_validate` | 145.46 |
| dependensee | `adapter.integration` | 53.93 |
| dependensee | `sql.cross_tool_join_patterns` | 43.90 |
| dependensee | `entity.repository_alignment` | 8.01 |
| dependensee | `evaluation.synthetic_context` | 7.52 |
| dependensee | `adapter.schema_alignment` | 2.24 |
| dependensee | `output.paths` | 0.57 |
| dependensee | `adapter.quality_rules_coverage` | 0.56 |
| dependensee | `make.targets` | 0.47 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| dependensee | 0.42 |

## dependensee

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/outputs/9AB15700-6108-4BB7-A101-31B4A1A7908E/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.24 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.22 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 0.25 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/outputs/9AB15700-6108-4BB7-A101-31B4A1A7908E/output.json | - | - |
| `output.paths` | pass | high | 0.57 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.01 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.00 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | dependensee, dependensee | - | - |
| `output.metadata_consistency` | pass | medium | 0.04 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.24 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 145.46 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.36 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.47 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.24 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.14 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.11 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.07 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.38 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.15 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.18 | LLM judge count meets minimum (4 >= 4) | project_detection.py, circular_detection.py, graph_quality.py, dependency_accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 7.52 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: dependency_accuracy.py, prompt: dependency_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.03 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.06 | Programmatic evaluation schema valid | timestamp, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.05 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.04 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.04 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.03 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.19 | Rollup Validation declared with valid tests | src/tools/dependensee/tests/unit/test_analyze.py | - | - |
| `adapter.compliance` | pass | info | 151.07 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.24 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 53.93 | Adapter successfully persisted fixture data | Fixture: dependensee_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.56 | All 2 quality rules have implementation coverage | paths, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.31 | Adapter DependenseeAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.24 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.28 | Tool 'dependensee' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.19 | dbt staging model(s) found | stg_dependensee_package_refs.sql, stg_dependensee_projects.sql, stg_dependensee_project_refs.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.18 | dbt models present for tool | stg_dependensee_package_refs.sql, stg_dependensee_projects.sql, stg_dependensee_project_refs.sql | - | - |
| `entity.repository_alignment` | pass | high | 8.01 | All entities have aligned repositories | DependenseeProject, DependenseeProjectReference, DependenseePackageReference | - | - |
| `test.structure_naming` | pass | medium | 0.25 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 43.90 | Cross-tool SQL joins use correct patterns (161 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.25 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |
