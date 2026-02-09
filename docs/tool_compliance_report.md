# Tool Compliance Report

Generated: `2026-02-09T14:35:05.910126+00:00`

Summary: 1 passed, 0 failed, 1 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| git-blame-scanner | pass | 51 | 0 | - |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| git-blame-scanner | `output.schema_validate` | 363.33 |
| git-blame-scanner | `adapter.compliance` | 189.38 |
| git-blame-scanner | `adapter.integration` | 114.22 |
| git-blame-scanner | `sql.cross_tool_join_patterns` | 92.40 |
| git-blame-scanner | `entity.repository_alignment` | 17.35 |
| git-blame-scanner | `evaluation.synthetic_context` | 11.61 |
| git-blame-scanner | `adapter.schema_alignment` | 2.66 |
| git-blame-scanner | `dbt.model_coverage` | 2.63 |
| git-blame-scanner | `output.paths` | 1.44 |
| git-blame-scanner | `adapter.quality_rules_coverage` | 1.26 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| git-blame-scanner | 0.81 |

## git-blame-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-blame-scanner/outputs/all-synthetic/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-blame-scanner/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.50 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-blame-scanner/evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.53 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 0.31 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-blame-scanner/outputs/all-synthetic/output.json | - | - |
| `output.paths` | pass | high | 1.44 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.05 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.05 | Path consistency validated | Checked 4 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | git-blame-scanner, git-blame-scanner | - | - |
| `output.metadata_consistency` | pass | medium | 0.05 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.90 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 363.33 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.36 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.43 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.35 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.15 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.13 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.34 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.25 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.05 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.03 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.23 | LLM judge count meets minimum (5 >= 4) | ownership_accuracy.py, actionability.py, integration.py, churn_validity.py, utils.py | - | - |
| `evaluation.synthetic_context` | pass | high | 11.61 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: ownership_accuracy.py, prompt: ownership_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.06 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.11 | Programmatic evaluation schema valid | timestamp, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.06 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.03 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.16 | LLM evaluation schema valid | timestamp, output_dir, model, trace_id, judges, summary, programmatic_input, decision, score, dimensions | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.11 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-blame-scanner/evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.10 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.26 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_git_blame_direct_vs_recursive.sql, src/tools/git-blame-scanner/tests/unit/test_analyze.py | - | - |
| `adapter.compliance` | pass | info | 189.38 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.66 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 114.22 | Adapter successfully persisted fixture data | Fixture: git_blame_scanner_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.26 | All 4 quality rules have implementation coverage | paths, ownership_valid, churn_monotonic, authors_positive | - | - |
| `sot.adapter_registered` | pass | medium | 0.45 | Adapter GitBlameScannerAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.84 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.81 | Tool 'git-blame-scanner' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.85 | dbt staging model(s) found | stg_git_blame_author_stats.sql, stg_git_blame_summary.sql | - | - |
| `dbt.model_coverage` | pass | high | 2.63 | dbt models present for tool | stg_git_blame_author_stats.sql, stg_git_blame_summary.sql | - | - |
| `entity.repository_alignment` | pass | high | 17.35 | All entities have aligned repositories | GitBlameFileSummary, GitBlameAuthorStats | - | - |
| `test.structure_naming` | pass | medium | 0.83 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 92.40 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.32 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |
