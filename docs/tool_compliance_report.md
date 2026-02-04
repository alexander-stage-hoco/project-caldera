# Tool Compliance Report

Generated: `2026-02-04T14:13:07.745448+00:00`

Summary: 2 passed, 10 failed, 12 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| git-sizer | fail | 50 | 1 | evaluation.llm_includes_programmatic |
| gitleaks | fail | 51 | 1 | test.coverage_threshold |
| layout-scanner | fail | 50 | 1 | evaluation.llm_includes_programmatic |
| lizard | fail | 48 | 4 | evaluation.llm_quality, evaluation.llm_includes_programmatic, evaluation.llm_decision_quality, test.coverage_threshold |
| pmd-cpd | pass | 51 | 0 | - |
| roslyn-analyzers | fail | 49 | 3 | evaluation.llm_includes_programmatic, evaluation.llm_decision_quality, test.coverage_threshold |
| scancode | fail | 41 | 11 | run.evaluate_llm, evaluation.llm_quality, output.paths, output.data_completeness, evaluation.synthetic_context, evaluation.llm_exists, evaluation.llm_schema, evaluation.llm_includes_programmatic, evaluation.llm_decision_quality, evaluation.rollup_validation, test.coverage_threshold |
| scc | fail | 50 | 2 | evaluation.llm_includes_programmatic, test.coverage_threshold |
| semgrep | fail | 48 | 3 | evaluation.llm_schema, evaluation.llm_includes_programmatic, evaluation.llm_decision_quality |
| sonarqube | fail | 50 | 2 | output.paths, test.coverage_threshold |
| symbol-scanner | pass | 51 | 0 | - |
| trivy | fail | 50 | 1 | output.data_completeness |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| semgrep | `output.schema_validate` | 310.50 |
| roslyn-analyzers | `output.schema_validate` | 218.57 |
| sonarqube | `adapter.integration` | 202.90 |
| sonarqube | `output.schema_validate` | 176.63 |
| symbol-scanner | `output.schema_validate` | 174.98 |
| lizard | `output.schema_validate` | 159.63 |
| trivy | `adapter.integration` | 142.45 |
| layout-scanner | `output.schema_validate` | 140.91 |
| pmd-cpd | `output.schema_validate` | 134.24 |
| symbol-scanner | `adapter.integration` | 130.50 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| semgrep | 0.46 |
| sonarqube | 0.44 |
| roslyn-analyzers | 0.37 |
| git-sizer | 0.36 |
| symbol-scanner | 0.36 |
| trivy | 0.30 |
| lizard | 0.29 |
| pmd-cpd | 0.29 |
| scc | 0.26 |
| layout-scanner | 0.23 |
| scancode | 0.22 |
| gitleaks | 0.18 |

## git-sizer

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/evaluation/results/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.42 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/evaluation/llm/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.27 | LLM evaluation decision meets threshold | WEAK_PASS | - | - |
| `output.load` | pass | high | 0.24 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/evaluation/results/output.json | - | - |
| `output.paths` | pass | high | 0.17 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.01 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.00 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | git-sizer, git-sizer | - | - |
| `output.metadata_consistency` | pass | medium | 0.04 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.39 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 128.63 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.21 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.58 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.25 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.14 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.09 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.09 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.07 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.35 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.30 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.05 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.04 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.47 | LLM judge count meets minimum (4 >= 4) | integration_fit.py, size_accuracy.py, actionability.py, threshold_quality.py | - | - |
| `evaluation.synthetic_context` | pass | high | 8.29 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: size_accuracy.py, prompt: size_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.26 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | pass | low | 0.01 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.09 | Programmatic evaluation schema valid | timestamp, decision, score, analysis_path, ground_truth_dir, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.07 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.34 | LLM evaluation schema valid | timestamp, analysis_path, model, trace_id, judges, summary, programmatic_input, decision, score, dimensions | - | - |
| `evaluation.llm_includes_programmatic` | fail | medium | 0.08 | Missing programmatic_input field in llm_evaluation.json | LLM evaluation must include programmatic results | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.06 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.20 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_git_sizer_repo_level_only.sql | - | - |
| `adapter.compliance` | pass | info | 126.80 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.79 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 45.32 | Adapter successfully persisted fixture data | Fixture: git_sizer_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.70 | All 3 quality rules have implementation coverage | health_grade_valid, metrics_non_negative, violation_levels | - | - |
| `sot.adapter_registered` | pass | medium | 0.39 | Adapter GitSizerAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.21 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.38 | Tool 'git-sizer' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.16 | dbt staging model(s) found | stg_lz_git_sizer_metrics.sql, stg_lz_git_sizer_violations.sql, stg_lz_git_sizer_lfs_candidates.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.16 | dbt models present for tool | stg_lz_git_sizer_metrics.sql, stg_lz_git_sizer_violations.sql, stg_lz_git_sizer_lfs_candidates.sql | - | - |
| `entity.repository_alignment` | pass | high | 5.82 | All entities have aligned repositories | GitSizerMetric, GitSizerViolation, GitSizerLfsCandidate | - | - |
| `test.structure_naming` | pass | medium | 1.01 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 36.37 | Cross-tool SQL joins use correct patterns (137 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.31 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## gitleaks

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/outputs/9ad8b91b-0618-4351-9ed3-9a07fc72bb19/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.27 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/evaluation/llm/results/llm-eval-20260204-135934.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.25 | LLM evaluation decision meets threshold | WEAK_PASS | - | - |
| `output.load` | pass | high | 0.29 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/outputs/9ad8b91b-0618-4351-9ed3-9a07fc72bb19/output.json | - | - |
| `output.paths` | pass | high | 0.06 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.01 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.00 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | gitleaks, gitleaks | - | - |
| `output.metadata_consistency` | pass | medium | 0.00 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.27 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 103.71 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.20 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.05 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.11 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.06 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.09 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.07 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.76 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.83 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.09 | LLM judge count meets minimum (4 >= 4) | false_positive.py, secret_coverage.py, detection_accuracy.py, severity_classification.py | - | - |
| `evaluation.synthetic_context` | pass | high | 3.77 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: detection_accuracy.py, prompt: detection_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.03 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.01 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.33 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary, categories | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.04 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.23 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.04 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.04 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.27 | Rollup Validation declared with valid tests | src/tools/gitleaks/tests/unit/test_rollup_invariants.py, src/sot-engine/dbt/tests/test_rollup_gitleaks_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.38 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 40.02 | Adapter successfully persisted fixture data | Fixture: gitleaks_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.45 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.22 | Adapter GitleaksAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.19 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.11 | Tool 'gitleaks' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.16 | dbt staging model(s) found | stg_gitleaks_secrets.sql, stg_lz_gitleaks_secrets.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.43 | dbt models present for tool | stg_gitleaks_secrets.sql, stg_lz_gitleaks_secrets.sql | - | - |
| `entity.repository_alignment` | pass | high | 5.66 | All entities have aligned repositories | GitleaksSecret | - | - |
| `test.structure_naming` | pass | medium | 0.95 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 12.38 | Cross-tool SQL joins use correct patterns (137 files checked) | - | - | - |
| `test.coverage_threshold` | fail | high | 0.26 | pytest-cov not in requirements.txt | Add pytest-cov>=4.0.0 to requirements.txt | - | - |

## layout-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner/outputs/9ad8b91b-0618-4351-9ed3-9a07fc72bb19/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.81 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner/evaluation/llm/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.24 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 0.56 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner/outputs/9ad8b91b-0618-4351-9ed3-9a07fc72bb19/output.json | - | - |
| `output.paths` | pass | high | 3.37 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.02 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | layout-scanner, layout-scanner | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.50 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 140.91 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.22 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.19 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.10 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.07 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.13 | analyze target output pattern acceptable | - | - | - |
| `schema.draft` | pass | medium | 0.13 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.10 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.73 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.68 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.08 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.04 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.08 | LLM judge count meets minimum (4 >= 4) | classification_reasoning.py, hierarchy_consistency.py, language_detection.py, directory_taxonomy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 5.96 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: classification_reasoning.py, prompt: classification_reasoning.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.08 | Ground truth files present | mixed-language.json, edge-cases.json, generated-code.json, config-heavy.json, vendor-heavy.json, small-clean.json, deep-nesting.json, mixed-types.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.01 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.53 | Programmatic evaluation schema valid | timestamp, decision, score, evaluated_count, average_score, summary, checks, repositories | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.47 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.31 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | fail | medium | 0.05 | Missing programmatic_input field in llm_evaluation.json | LLM evaluation must include programmatic results | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.04 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.25 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_layout_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.27 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 48.19 | Adapter successfully persisted fixture data | Fixture: layout_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.75 | All 3 quality rules have implementation coverage | paths, ranges, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.19 | Adapter LayoutAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.19 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.00 | layout-scanner handled specially as prerequisite tool | Layout is ingested before TOOL_INGESTION_CONFIGS loop | - | - |
| `sot.dbt_staging_model` | pass | high | 0.16 | dbt staging model(s) found | stg_lz_layout_files.sql, stg_lz_layout_directories.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.49 | dbt models present for tool | stg_lz_layout_files.sql, stg_lz_layout_directories.sql | - | - |
| `entity.repository_alignment` | pass | high | 5.10 | All entities have aligned repositories | LayoutFile, LayoutDirectory | - | - |
| `test.structure_naming` | pass | medium | 1.05 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 13.16 | Cross-tool SQL joins use correct patterns (137 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.43 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## lizard

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/lizard/evaluation/results/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/lizard/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.66 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/lizard/evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | fail | medium | 0.14 | LLM evaluation decision below required threshold | FAIL | - | - |
| `output.load` | pass | high | 2.06 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/lizard/evaluation/results/output.json | - | - |
| `output.paths` | pass | high | 10.64 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.03 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.09 | Path consistency validated | Checked 85 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.00 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.00 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.00 | Tool name matches data.tool | lizard, lizard | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.42 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 159.63 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.94 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.84 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.01 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.10 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.08 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.13 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.09 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.44 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.61 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.05 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.08 | LLM judge count meets minimum (4 >= 4) | hotspot_ranking.py, ccn_accuracy.py, function_detection.py, statistics.py | - | - |
| `evaluation.synthetic_context` | pass | high | 7.76 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: ccn_accuracy.py, prompt: ccn_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.34 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.33 | Programmatic evaluation schema valid | timestamp, decision, score, analysis_path, ground_truth_path, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.30 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.08 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | fail | medium | 0.06 | Missing programmatic_input field in llm_evaluation.json | LLM evaluation must include programmatic results | - | - |
| `evaluation.llm_decision_quality` | fail | medium | 0.05 | LLM evaluation failed | FAIL | - | - |
| `evaluation.rollup_validation` | pass | high | 0.32 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_lizard_direct_distribution_ranges.sql, src/sot-engine/dbt/tests/test_rollup_lizard_direct_vs_recursive.sql, src/sot-engine/dbt/tests/test_rollup_lizard_distribution_ranges.sql | - | - |
| `adapter.compliance` | pass | info | 0.05 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.37 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 74.80 | Adapter successfully persisted fixture data | Fixture: lizard_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.66 | All 3 quality rules have implementation coverage | paths, ranges, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.18 | Adapter LizardAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.19 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.10 | Tool 'lizard' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.16 | dbt staging model(s) found | stg_lz_lizard_file_metrics.sql, stg_lz_lizard_function_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.43 | dbt models present for tool | stg_lz_lizard_file_metrics.sql, stg_lz_lizard_function_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 6.62 | All entities have aligned repositories | LizardFileMetric, LizardFunctionMetric | - | - |
| `test.structure_naming` | pass | medium | 0.86 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 14.10 | Cross-tool SQL joins use correct patterns (137 files checked) | - | - | - |
| `test.coverage_threshold` | fail | high | 0.29 | pytest-cov not in requirements.txt | Add pytest-cov>=4.0.0 to requirements.txt | - | - |

## pmd-cpd

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/outputs/cpd-test-run/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.64 | Evaluation decision meets threshold | WEAK_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.26 | LLM evaluation decision meets threshold | WEAK_PASS | - | - |
| `output.load` | pass | high | 0.72 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/outputs/cpd-test-run/output.json | - | - |
| `output.paths` | pass | high | 1.93 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.03 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.17 | Path consistency validated | Checked 49 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | pmd-cpd, pmd-cpd | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.34 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 134.24 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.23 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.60 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.10 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.13 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.09 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.54 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.78 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.05 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.04 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.85 | LLM judge count meets minimum (4 >= 4) | duplication_accuracy.py, actionability.py, semantic_detection.py, cross_file_detection.py | - | - |
| `evaluation.synthetic_context` | pass | high | 4.19 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: duplication_accuracy.py, prompt: duplication_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.29 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | pass | low | 0.01 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.01 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.29 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.22 | Programmatic evaluation passed | WEAK_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.15 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, combined_score, notes | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.04 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=WEAK_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.04 | LLM evaluation passed | WEAK_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.32 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_pmd_cpd_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.05 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.89 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 112.96 | Adapter successfully persisted fixture data | Fixture: pmd_cpd_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.66 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.25 | Adapter PmdCpdAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.21 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.12 | Tool 'pmd-cpd' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.18 | dbt staging model(s) found | stg_lz_pmd_cpd_duplications.sql, stg_lz_pmd_cpd_occurrences.sql, stg_lz_pmd_cpd_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.58 | dbt models present for tool | stg_lz_pmd_cpd_duplications.sql, stg_lz_pmd_cpd_occurrences.sql, stg_lz_pmd_cpd_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 5.27 | All entities have aligned repositories | PmdCpdFileMetric, PmdCpdDuplication, PmdCpdOccurrence | - | - |
| `test.structure_naming` | pass | medium | 0.86 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 14.12 | Cross-tool SQL joins use correct patterns (137 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.62 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## roslyn-analyzers

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/outputs/bdaa107a-6afd-4b4e-ade4-1c76601d2a9f/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.32 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/evaluation/llm/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.29 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 4.41 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/outputs/bdaa107a-6afd-4b4e-ade4-1c76601d2a9f/output.json | - | - |
| `output.paths` | pass | high | 41.83 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.20 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 1.68 | Path consistency validated | Checked 1900 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | roslyn-analyzers, roslyn-analyzers | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.39 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 218.57 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.23 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.47 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.10 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.09 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.07 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.48 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.71 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.09 | LLM judge count meets minimum (5 >= 4) | overall_quality.py, integration_fit.py, resource_management.py, security_detection.py, design_analysis.py | - | - |
| `evaluation.synthetic_context` | pass | high | 10.28 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: security_detection.py, prompt: security_detection.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.28 | Ground truth files present | clean-code.json, resource-management.json, dead-code.json, csharp.json, security-issues.json, design-violations.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.20 | Programmatic evaluation schema valid | evaluation_id, timestamp, analysis_file, decision, score, summary, category_scores, checks, decision_reason | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.10 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.18 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | fail | medium | 0.06 | Missing programmatic_input field in llm_evaluation.json | LLM evaluation must include programmatic results | - | - |
| `evaluation.llm_decision_quality` | fail | medium | 0.05 | LLM evaluation failed | FAIL | - | - |
| `evaluation.rollup_validation` | pass | high | 0.31 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_roslyn_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.05 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.38 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 67.70 | Adapter successfully persisted fixture data | Fixture: roslyn_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.56 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.24 | Adapter RoslynAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.19 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.12 | Tool 'roslyn-analyzers' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.17 | dbt staging model(s) found | stg_roslyn_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.68 | dbt models present for tool | stg_roslyn_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 4.84 | All entities have aligned repositories | RoslynViolation | - | - |
| `test.structure_naming` | pass | medium | 0.79 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 13.27 | Cross-tool SQL joins use correct patterns (137 files checked) | - | - | - |
| `test.coverage_threshold` | fail | high | 0.19 | pytest-cov not in requirements.txt | Add pytest-cov>=4.0.0 to requirements.txt | - | - |

## scancode

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/outputs/9BA0669F-E59F-4BC8-9314-D4BF3B24F279/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 1.16 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | fail | medium | 0.00 | No LLM evaluation output found - run with --run-llm or execute 'make evaluate-llm' | - | - | - |
| `evaluation.llm_quality` | fail | medium | 0.00 | LLM evaluation quality check skipped (no outputs) | - | - | - |
| `output.load` | pass | high | 0.34 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/outputs/9BA0669F-E59F-4BC8-9314-D4BF3B24F279/output.json | - | - |
| `output.paths` | fail | high | 1.07 | Invalid path values detected | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/eval-repos/synthetic | - | - |
| `output.data_completeness` | fail | high | 0.03 | Data completeness issues detected | findings[0] missing required field: message, findings[1] missing required field: message, findings[2] missing required field: message, findings[3] missing required field: message, findings[4] missing required field: message, ... 18 more issues in findings | - | - |
| `output.path_consistency` | pass | medium | 0.03 | Path consistency validated | Checked 23 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | scancode, scancode | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.37 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 116.48 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.21 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.35 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.01 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.08 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.06 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.05 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.09 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.07 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.42 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.18 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.04 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.04 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.08 | LLM judge count meets minimum (4 >= 4) | coverage_judge.py, accuracy_judge.py, actionability_judge.py, risk_classification_judge.py | - | - |
| `evaluation.synthetic_context` | fail | high | 1.87 | base.py missing evaluation_mode parameter | base.py __init__ missing evaluation_mode parameter | - | - |
| `evaluation.ground_truth` | pass | high | 0.07 | Ground truth files present | multi-license.json, mit-only.json, gpl-mixed.json, apache-bsd.json, public-domain.json, spdx-expression.json, no-license.json, dual-licensed.json | - | - |
| `evaluation.scorecard` | pass | low | 0.01 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.01 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.59 | Programmatic evaluation schema valid | timestamp, tool, version, decision, score, summary, checks, total_repositories, reports | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.52 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | fail | medium | 0.02 | Missing llm_evaluation.json at uniform path | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | fail | medium | 0.01 | Cannot validate schema - file missing | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_includes_programmatic` | fail | medium | 0.01 | Cannot check - file missing | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_decision_quality` | fail | medium | 0.01 | Cannot check quality - file missing | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.rollup_validation` | fail | high | 0.06 | Rollup Validation section not declared | - | - | - |
| `adapter.compliance` | pass | info | 0.05 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.33 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 73.59 | Adapter successfully persisted fixture data | Fixture: scancode_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.51 | All 3 quality rules have implementation coverage | paths, confidence, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.31 | Adapter ScancodeAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.22 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.12 | Tool 'scancode' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.22 | dbt staging model(s) found | stg_lz_scancode_summary.sql, stg_lz_scancode_file_licenses.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.13 | dbt models present for tool | stg_lz_scancode_summary.sql, stg_lz_scancode_file_licenses.sql | - | - |
| `entity.repository_alignment` | pass | high | 5.46 | All entities have aligned repositories | ScancodeFileLicense, ScancodeSummary | - | - |
| `test.structure_naming` | pass | medium | 0.71 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 12.77 | Cross-tool SQL joins use correct patterns (137 files checked) | - | - | - |
| `test.coverage_threshold` | fail | high | 0.22 | pytest-cov not in requirements.txt | Add pytest-cov>=4.0.0 to requirements.txt | - | - |

## scc

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/evaluation/results/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.50 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/evaluation/llm/results/llm-eval-20260125-104034.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.40 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 0.81 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/evaluation/results/output.json | - | - |
| `output.paths` | pass | high | 4.65 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.02 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.10 | Path consistency validated | Checked 94 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.00 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.00 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.00 | Tool name matches data.tool | scc, scc | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.44 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 124.48 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.21 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.37 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.09 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.07 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.11 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.65 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.50 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.10 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.09 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.37 | LLM judge count meets minimum (10 >= 4) | error_messages.py, documentation.py, edge_cases.py, directory_analysis.py, integration_fit.py, code_quality.py, risk.py, statistics.py, comparative.py, api_design.py | - | - |
| `evaluation.synthetic_context` | pass | high | 9.93 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: directory_analysis.py, prompt: directory_analysis.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.04 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.01 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.24 | Programmatic evaluation schema valid | run_id, timestamp, dimensions, total_score, decision | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.17 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.25 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | fail | medium | 0.07 | Missing programmatic_input field in llm_evaluation.json | LLM evaluation must include programmatic results | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.07 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.29 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_scc_direct_distribution_ranges.sql, src/sot-engine/dbt/tests/test_rollup_scc_direct_vs_recursive.sql, src/sot-engine/dbt/tests/test_rollup_scc_distribution_ranges.sql | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.38 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 84.51 | Adapter successfully persisted fixture data | Fixture: scc_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.70 | All 4 quality rules have implementation coverage | paths, ranges, ratios, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.23 | Adapter SccAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.27 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.12 | Tool 'scc' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.17 | dbt staging model(s) found | stg_lz_scc_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.51 | dbt models present for tool | stg_lz_scc_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 6.55 | All entities have aligned repositories | SccFileMetric | - | - |
| `test.structure_naming` | pass | medium | 3.29 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 14.43 | Cross-tool SQL joins use correct patterns (137 files checked) | - | - | - |
| `test.coverage_threshold` | fail | high | 0.29 | pytest-cov not in requirements.txt | Add pytest-cov>=4.0.0 to requirements.txt | - | - |

## semgrep

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/outputs/9ad8b91b-0618-4351-9ed3-9a07fc72bb19/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.30 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/evaluation/llm/results/llm-eval-20260130-120000.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.24 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 0.60 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/outputs/9ad8b91b-0618-4351-9ed3-9a07fc72bb19/output.json | - | - |
| `output.paths` | pass | high | 3.27 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.02 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.07 | Path consistency validated | Checked 65 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | semgrep, semgrep | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.40 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 310.50 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.25 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.42 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.14 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target output pattern acceptable | - | - | - |
| `schema.draft` | pass | medium | 0.14 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.10 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.50 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.89 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.10 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.39 | LLM judge count meets minimum (5 >= 4) | rule_coverage.py, actionability.py, security_detection.py, smell_accuracy.py, false_positive_rate.py | - | - |
| `evaluation.synthetic_context` | pass | high | 13.76 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: security_detection.py, prompt: security_detection.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.28 | Ground truth files present | java.json, go.json, csharp.json, rust.json, javascript.json, typescript.json, python.json | - | - |
| `evaluation.scorecard` | pass | low | 0.03 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.07 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.05 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | fail | medium | 0.31 | Missing required fields in llm_evaluation.json | model, decision, score, programmatic_input | - | - |
| `evaluation.llm_includes_programmatic` | fail | medium | 0.08 | Missing programmatic_input field in llm_evaluation.json | LLM evaluation must include programmatic results | - | - |
| `evaluation.llm_decision_quality` | fail | medium | 0.07 | LLM score below threshold | score=1.75 | - | - |
| `evaluation.rollup_validation` | pass | high | 0.33 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_semgrep_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.05 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.51 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 95.69 | Adapter successfully persisted fixture data | Fixture: semgrep_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.37 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.24 | Adapter SemgrepAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.19 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.11 | Tool 'semgrep' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.17 | dbt staging model(s) found | stg_semgrep_file_metrics.sql, stg_lz_semgrep_smells.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.51 | dbt models present for tool | stg_semgrep_file_metrics.sql, stg_lz_semgrep_smells.sql | - | - |
| `entity.repository_alignment` | pass | high | 5.08 | All entities have aligned repositories | SemgrepSmell | - | - |
| `test.structure_naming` | pass | medium | 1.56 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 18.71 | Cross-tool SQL joins use correct patterns (137 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.81 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## sonarqube

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/outputs/B16129A2-F8A9-4C9A-A347-365A8569418B/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.39 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/evaluation/llm/results/llm-eval-20260130-120000.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.45 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 1.56 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/outputs/B16129A2-F8A9-4C9A-A347-365A8569418B/output.json | - | - |
| `output.paths` | fail | high | 3.04 | Invalid path values detected | / | - | - |
| `output.data_completeness` | pass | high | 0.02 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.2.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | sonarqube, sonarqube | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.56 | Output schema_version matches schema constraint | 1.2.0 | - | - |
| `output.schema_validate` | pass | critical | 176.63 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.54 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.41 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.09 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.25 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.29 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.23 | analyze target produces output.json | - | - | - |
| `schema.draft` | pass | medium | 0.20 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 1.34 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.69 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.08 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.04 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.11 | LLM judge count meets minimum (4 >= 4) | issue_accuracy.py, integration_fit.py, actionability.py, coverage_completeness.py | - | - |
| `evaluation.synthetic_context` | pass | high | 12.16 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: issue_accuracy.py, prompt: issue_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.33 | Ground truth files present | java-security.json, typescript-duplication.json, csharp-baseline.json, python-mixed.json, csharp-complex.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.03 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.08 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.05 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.54 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, analysis_path, summary, dimensions | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.29 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.09 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.43 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_sonarqube_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.48 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 202.90 | Adapter successfully persisted fixture data | Fixture: sonarqube_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.60 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.25 | Adapter SonarqubeAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.20 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.12 | Tool 'sonarqube' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.18 | dbt staging model(s) found | stg_sonarqube_issues.sql, stg_sonarqube_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.58 | dbt models present for tool | stg_sonarqube_issues.sql, stg_sonarqube_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 7.56 | All entities have aligned repositories | SonarqubeIssue, SonarqubeMetric | - | - |
| `test.structure_naming` | pass | medium | 3.58 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 16.75 | Cross-tool SQL joins use correct patterns (137 files checked) | - | - | - |
| `test.coverage_threshold` | fail | high | 0.20 | pytest-cov not in requirements.txt | Add pytest-cov>=4.0.0 to requirements.txt | - | - |

## symbol-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/evaluation/results/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.98 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.47 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 0.19 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/evaluation/results/output.json | - | - |
| `output.paths` | pass | high | 0.21 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.04 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.00 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.00 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.00 | Tool name matches data.tool | symbol-scanner, symbol-scanner | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.40 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 174.98 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.27 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.48 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.18 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.11 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.07 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.30 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.42 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.07 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.48 | LLM judge count meets minimum (4 >= 4) | call_relationship.py, import_completeness.py, integration.py, symbol_accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 15.72 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: call_relationship.py, prompt: call_relationship.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.12 | Ground truth files present | metaprogramming.json, csharp-tshock.json, cross-module-calls.json, deep-hierarchy.json, encoding-edge-cases.json, circular-imports.json, type-checking-imports.json, decorators-advanced.json, dynamic-code-generation.json, async-patterns.json, nested-structures.json, class-hierarchy.json, simple-functions.json, generators-comprehensions.json, dataclasses-protocols.json, deep-nesting-stress.json, partial-syntax-errors.json, unresolved-externals.json, confusing-names.json, modern-syntax.json, large-file.json, web-framework-patterns.json, import-patterns.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.01 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.37 | Programmatic evaluation schema valid | timestamp, decision, score, checks, summary, aggregate, per_repo_results, metadata, regression | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.35 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.07 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.05 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.05 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.19 | Rollup Validation declared with valid tests | src/sot-engine/dbt/models/staging/stg_lz_code_symbols.sql | - | - |
| `adapter.compliance` | pass | info | 0.03 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.45 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 130.50 | Adapter successfully persisted fixture data | Fixture: symbol_scanner_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.81 | All 3 quality rules have implementation coverage | paths, ranges, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.26 | Adapter SymbolScannerAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.20 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.12 | Tool 'symbol-scanner' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.17 | dbt staging model(s) found | stg_symbol_calls_file_metrics.sql, stg_symbols_file_metrics.sql, stg_lz_symbol_calls.sql, stg_lz_code_symbols.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.18 | dbt models present for tool | stg_symbol_calls_file_metrics.sql, stg_symbols_file_metrics.sql, stg_lz_symbol_calls.sql, stg_lz_code_symbols.sql | - | - |
| `entity.repository_alignment` | pass | high | 9.12 | All entities have aligned repositories | CodeSymbol, SymbolCall, FileImport | - | - |
| `test.structure_naming` | pass | medium | 1.49 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 17.12 | Cross-tool SQL joins use correct patterns (137 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.46 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## trivy

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/outputs/9ad8b91b-0618-4351-9ed3-9a07fc72bb19/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.56 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/evaluation/llm/results/synthetic-llm-eval.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.33 | LLM evaluation score meets threshold | score=4.0 | - | - |
| `output.load` | pass | high | 0.38 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/outputs/9ad8b91b-0618-4351-9ed3-9a07fc72bb19/output.json | - | - |
| `output.paths` | pass | high | 1.30 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | fail | high | 0.03 | Data completeness issues detected | vulnerabilities[0] missing required field: vulnerability_id, vulnerabilities[1] missing required field: vulnerability_id, vulnerabilities[2] missing required field: vulnerability_id, vulnerabilities[3] missing required field: vulnerability_id, vulnerabilities[4] missing required field: vulnerability_id, ... 32 more issues in vulnerabilities | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | trivy, trivy | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.40 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 119.80 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.20 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.58 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.11 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.07 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.05 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.11 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.59 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.36 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.08 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.08 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.11 | LLM judge count meets minimum (7 >= 4) | freshness_quality.py, vulnerability_detection.py, vulnerability_accuracy.py, severity_accuracy.py, iac_quality.py, sbom_completeness.py, false_positive_rate.py | - | - |
| `evaluation.synthetic_context` | pass | high | 11.40 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: vulnerability_accuracy.py, prompt: vulnerability_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.23 | Ground truth files present | dotnet-outdated.json, js-fullstack.json, vulnerable-npm.json, iac-terraform.json, no-vulnerabilities.json, iac-misconfigs.json, mixed-severity.json, java-outdated.json, critical-cves.json, outdated-deps.json, cfn-misconfigs.json, k8s-misconfigs.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.19 | Programmatic evaluation schema valid | timestamp, tool, version, decision, score, classification, overall_score, summary, checks, dimensions | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.16 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.29 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.07 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.06 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.19 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_trivy_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.50 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 142.45 | Adapter successfully persisted fixture data | Fixture: trivy_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.54 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.24 | Adapter TrivyAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.22 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.15 | Tool 'trivy' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.18 | dbt staging model(s) found | stg_trivy_iac_misconfigs.sql, stg_trivy_vulnerabilities.sql, stg_trivy_target_metrics.sql, stg_trivy_targets.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.49 | dbt models present for tool | stg_trivy_iac_misconfigs.sql, stg_trivy_vulnerabilities.sql, stg_trivy_target_metrics.sql, stg_trivy_targets.sql | - | - |
| `entity.repository_alignment` | pass | high | 5.72 | All entities have aligned repositories | TrivyVulnerability, TrivyTarget, TrivyIacMisconfig | - | - |
| `test.structure_naming` | pass | medium | 0.93 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 13.62 | Cross-tool SQL joins use correct patterns (137 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.22 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |
