# Tool Compliance Report

Generated: `2026-02-08T08:53:48.217891+00:00`

Summary: 1 passed, 0 failed, 1 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| git-fame | pass | 51 | 0 | - |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| git-fame | `output.schema_validate` | 182.07 |
| git-fame | `adapter.compliance` | 146.30 |
| git-fame | `adapter.integration` | 76.58 |
| git-fame | `sql.cross_tool_join_patterns` | 36.71 |
| git-fame | `evaluation.synthetic_context` | 17.48 |
| git-fame | `entity.repository_alignment` | 14.52 |
| git-fame | `output.paths` | 4.50 |
| git-fame | `adapter.schema_alignment` | 3.19 |
| git-fame | `test.structure_naming` | 1.85 |
| git-fame | `docs.blueprint_structure` | 1.15 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| git-fame | 0.49 |

## git-fame

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/outputs/f23f9a48-fb85-4c81-8e04-da14641d23b3/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.14 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.16 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 0.33 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/outputs/f23f9a48-fb85-4c81-8e04-da14641d23b3/output.json | - | - |
| `output.paths` | pass | high | 4.50 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.05 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.02 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.02 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.02 | Tool name matches data.tool | git-fame, git-fame | - | - |
| `output.metadata_consistency` | pass | medium | 0.17 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.35 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 182.07 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.35 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.24 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.32 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.20 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.13 | analyze target produces output.json | - | - | - |
| `schema.draft` | pass | medium | 0.15 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.09 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 1.15 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.25 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.11 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.09 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.26 | LLM judge count meets minimum (7 >= 4) | integration_readiness.py, concentration_metrics.py, evidence_quality.py, authorship_quality.py, utils.py, bus_factor_accuracy.py, output_completeness.py | - | - |
| `evaluation.synthetic_context` | pass | high | 17.48 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: authorship_quality.py, prompt: authorship_quality.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.14 | Ground truth files present | synthetic.json, multi-author.json, bus-factor-1.json, balanced.json, multi-branch.json, single-author.json | - | - |
| `evaluation.scorecard` | pass | low | 0.03 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.03 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.11 | Programmatic evaluation schema valid | timestamp, tool, version, overall_score, classification, summary, dimensions | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.09 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.03 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.14 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.13 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/evaluation/results/evaluation_report.json, decision=MARGINAL_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.11 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.44 | Rollup Validation declared with valid tests | src/tools/git-fame/tests/scripts/test_analyze.py, src/tools/git-fame/tests/scripts/test_authorship_accuracy_checks.py, src/tools/git-fame/tests/scripts/test_output_quality_checks.py, src/tools/git-fame/tests/scripts/test_reliability_checks.py | - | - |
| `adapter.compliance` | pass | info | 146.30 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.19 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 76.58 | Adapter successfully persisted fixture data | Fixture: git_fame_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.98 | All 3 quality rules have implementation coverage | hhi_valid, ownership_sums_100, bus_factor_valid | - | - |
| `sot.adapter_registered` | pass | medium | 0.32 | Adapter GitFameAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.37 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.20 | Tool 'git-fame' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.30 | dbt staging model(s) found | stg_lz_git_fame_authors.sql, stg_lz_git_fame_summary.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.26 | dbt models present for tool | stg_lz_git_fame_authors.sql, stg_lz_git_fame_summary.sql | - | - |
| `entity.repository_alignment` | pass | high | 14.52 | All entities have aligned repositories | GitFameAuthor, GitFameSummary | - | - |
| `test.structure_naming` | pass | medium | 1.85 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 36.71 | Cross-tool SQL joins use correct patterns (200 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.46 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |
