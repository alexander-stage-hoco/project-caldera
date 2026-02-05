# Tool Compliance Report

Generated: `2026-02-05T18:57:37.887130+00:00`

Summary: 0 passed, 1 failed, 1 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| gitleaks | fail | 50 | 1 | evaluation.llm_quality |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| gitleaks | `adapter.compliance` | 130.40 |
| gitleaks | `output.schema_validate` | 125.79 |
| gitleaks | `adapter.integration` | 43.38 |
| gitleaks | `sql.cross_tool_join_patterns` | 30.57 |
| gitleaks | `entity.repository_alignment` | 6.00 |
| gitleaks | `evaluation.synthetic_context` | 3.07 |
| gitleaks | `output.paths` | 2.06 |
| gitleaks | `adapter.schema_alignment` | 1.80 |
| gitleaks | `docs.blueprint_structure` | 0.51 |
| gitleaks | `dbt.model_coverage` | 0.49 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| gitleaks | 0.35 |

## gitleaks

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/outputs/A67997A1-295A-4551-B86C-BE5CEBC1CBAF/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.19 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/evaluation/llm/results/llm-eval-20260205-182557.json | - | - |
| `evaluation.llm_quality` | fail | medium | 0.20 | LLM evaluation decision below required threshold | FAIL | - | - |
| `output.load` | pass | high | 0.37 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/outputs/A67997A1-295A-4551-B86C-BE5CEBC1CBAF/output.json | - | - |
| `output.paths` | pass | high | 2.06 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.02 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.05 | Path consistency validated | Checked 49 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.00 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.00 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.00 | Tool name matches data.tool | gitleaks, gitleaks | - | - |
| `output.metadata_consistency` | pass | medium | 0.03 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.24 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 125.79 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.23 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.32 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.20 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.11 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.09 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.06 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.51 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.48 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.04 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.04 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.13 | LLM judge count meets minimum (4 >= 4) | false_positive.py, secret_coverage.py, detection_accuracy.py, severity_classification.py | - | - |
| `evaluation.synthetic_context` | pass | high | 3.07 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: detection_accuracy.py, prompt: detection_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.03 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.01 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.18 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary, categories | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.04 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.15 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.04 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.04 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.26 | Rollup Validation declared with valid tests | src/tools/gitleaks/tests/unit/test_rollup_invariants.py, src/sot-engine/dbt/tests/test_rollup_gitleaks_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 130.40 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.80 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 43.38 | Adapter successfully persisted fixture data | Fixture: gitleaks_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.48 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.31 | Adapter GitleaksAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.20 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.31 | Tool 'gitleaks' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.16 | dbt staging model(s) found | stg_gitleaks_secrets.sql, stg_lz_gitleaks_secrets.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.49 | dbt models present for tool | stg_gitleaks_secrets.sql, stg_lz_gitleaks_secrets.sql | - | - |
| `entity.repository_alignment` | pass | high | 6.00 | All entities have aligned repositories | GitleaksSecret | - | - |
| `test.structure_naming` | pass | medium | 0.36 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 30.57 | Cross-tool SQL joins use correct patterns (155 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.33 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |
