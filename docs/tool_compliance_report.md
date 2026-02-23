# Tool Compliance Report

Generated: `2026-02-23T06:59:54.915683+00:00`

Summary: 17 passed, 1 failed, 18 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| coverage-ingest | pass | 40 | 0 | - |
| dependensee | pass | 41 | 0 | - |
| devskim | pass | 40 | 0 | - |
| dotcover | pass | 41 | 0 | - |
| git-blame-scanner | pass | 41 | 0 | - |
| git-fame | pass | 40 | 0 | - |
| git-sizer | pass | 52 | 0 | - |
| gitleaks | pass | 41 | 0 | - |
| layout-scanner | pass | 51 | 0 | - |
| lizard | pass | 52 | 0 | - |
| pmd-cpd | pass | 41 | 0 | - |
| roslyn-analyzers | fail | 39 | 2 | evaluation.quality, evaluation.programmatic_quality |
| scancode | pass | 40 | 0 | - |
| scc | pass | 51 | 0 | - |
| semgrep | pass | 52 | 0 | - |
| sonarqube | pass | 52 | 0 | - |
| symbol-scanner | pass | 52 | 0 | - |
| trivy | pass | 40 | 0 | - |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| coverage-ingest | `adapter.compliance` | 283.63 |
| trivy | `adapter.integration` | 270.19 |
| sonarqube | `adapter.integration` | 248.84 |
| pmd-cpd | `adapter.integration` | 236.25 |
| lizard | `output.schema_validate` | 227.36 |
| layout-scanner | `adapter.integration` | 215.21 |
| scc | `adapter.integration` | 180.36 |
| scc | `output.schema_validate` | 178.00 |
| semgrep | `output.schema_validate` | 174.45 |
| lizard | `adapter.integration` | 167.40 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| lizard | 0.49 |
| sonarqube | 0.47 |
| coverage-ingest | 0.47 |
| layout-scanner | 0.46 |
| scc | 0.44 |
| semgrep | 0.41 |
| symbol-scanner | 0.36 |
| trivy | 0.34 |
| git-sizer | 0.31 |
| pmd-cpd | 0.29 |
| roslyn-analyzers | 0.21 |
| scancode | 0.21 |
| git-blame-scanner | 0.17 |
| gitleaks | 0.16 |
| dotcover | 0.15 |
| git-fame | 0.14 |
| devskim | 0.13 |
| dependensee | 0.12 |

## coverage-ingest

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/coverage-ingest/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.36 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/coverage-ingest/evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.39 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | skip | high | 0.11 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.19 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.41 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.10 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.15 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.14 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.23 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.42 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.58 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.31 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.04 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.30 | LLM judge count meets minimum (4 >= 4) | cross_format_consistency.py, gap_actionability.py, parser_accuracy.py, risk_tier_quality.py | - | - |
| `evaluation.synthetic_context` | pass | high | 13.02 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: gap_actionability.py, prompt: gap_actionability.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.03 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.08 | Programmatic evaluation schema valid | timestamp, score, decision, summary, passed, total, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.07 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.14 | LLM evaluation schema valid | timestamp, output_dir, model, trace_id, judges, summary, programmatic_input, decision, score, dimensions | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.12 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.12 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.33 | Rollup Validation declared with valid tests | src/tools/coverage-ingest/tests/unit/test_lcov_parser.py, src/tools/coverage-ingest/tests/unit/test_jacoco_parser.py, src/tools/coverage-ingest/tests/integration/test_e2e.py | - | - |
| `adapter.compliance` | pass | info | 283.63 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.29 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 74.20 | Adapter successfully persisted fixture data | Fixture: coverage_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.86 | All 4 quality rules have implementation coverage | paths, ranges, coverage_invariants, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.48 | Adapter CoverageAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.34 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.55 | Tool 'coverage-ingest' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.27 | dbt staging model(s) found | stg_lz_coverage_summary.sql, stg_lz_dotcover_type_coverage.sql, stg_lz_dotcover_method_coverage.sql, stg_lz_dotcover_assembly_coverage.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.26 | dbt models present for tool | stg_lz_coverage_summary.sql, stg_lz_dotcover_type_coverage.sql, stg_lz_dotcover_method_coverage.sql, stg_lz_dotcover_assembly_coverage.sql | - | - |
| `entity.repository_alignment` | pass | high | 12.27 | All entities have aligned repositories | CoverageSummary | - | - |
| `test.structure_naming` | pass | medium | 1.04 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 77.33 | Cross-tool SQL joins use correct patterns (261 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.28 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## dependensee

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.26 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.23 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | skip | high | 0.12 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.19 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.23 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.05 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.07 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.05 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.13 | evaluate target input path is valid | input: $(LATEST_OUTPUT) | - | - |
| `schema.draft` | pass | medium | 0.36 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.10 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.51 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.48 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.09 | LLM judge count meets minimum (4 >= 4) | project_detection.py, circular_detection.py, graph_quality.py, dependency_accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 8.53 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: dependency_accuracy.py, prompt: dependency_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.04 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.07 | Programmatic evaluation schema valid | timestamp, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.06 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.09 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.08 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.08 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.21 | Rollup Validation declared with valid tests | src/tools/dependensee/tests/unit/test_analyze.py | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.75 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 58.60 | Adapter successfully persisted fixture data | Fixture: dependensee_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.65 | All 2 quality rules have implementation coverage | paths, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.26 | Adapter DependenseeAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.34 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.18 | Tool 'dependensee' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.25 | dbt staging model(s) found | stg_dependensee_package_refs.sql, stg_dependensee_projects.sql, stg_dependensee_project_refs.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.25 | dbt models present for tool | stg_dependensee_package_refs.sql, stg_dependensee_projects.sql, stg_dependensee_project_refs.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.26 | All entities have aligned repositories | DependenseeProject, DependenseeProjectReference, DependenseePackageReference | - | - |
| `test.structure_naming` | pass | medium | 0.79 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 28.01 | Cross-tool SQL joins use correct patterns (261 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.44 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## devskim

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.29 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/evaluation/llm/results/llm-eval-20260214-135849.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.36 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | skip | high | 0.15 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.19 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.37 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.05 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.08 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.43 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.13 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.40 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.49 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.08 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.03 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.31 | LLM judge count meets minimum (4 >= 4) | rule_coverage.py, severity_calibration.py, security_focus.py, detection_accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 8.15 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: detection_accuracy.py, prompt: detection_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.08 | Ground truth files present | api-security.json, deserialization.json, xxe.json, csharp.json, clean.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.01 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.13 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.12 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.34 | LLM evaluation schema valid | run_id, timestamp, model, score, decision, dimensions, total_score, average_confidence, combined_score, programmatic_input | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.08 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.08 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.25 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_devskim_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.68 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 73.47 | Adapter successfully persisted fixture data | Fixture: devskim_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.18 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.29 | Adapter DevskimAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.35 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.19 | Tool 'devskim' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.25 | dbt staging model(s) found | stg_lz_devskim_findings.sql, stg_devskim_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.81 | dbt models present for tool | stg_lz_devskim_findings.sql, stg_devskim_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 9.96 | All entities have aligned repositories | DevskimFinding | - | - |
| `test.structure_naming` | pass | medium | 1.20 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 30.35 | Cross-tool SQL joins use correct patterns (261 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.32 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## dotcover

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.27 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.35 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | skip | high | 0.12 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.19 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.42 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.04 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.08 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.05 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.07 | evaluate target input path is valid | input: $(SYNTHETIC_OUTPUT_DIR) | - | - |
| `schema.draft` | pass | medium | 0.42 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.31 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.37 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.05 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.08 | LLM judge count meets minimum (4 >= 4) | false_positive.py, actionability.py, integration.py, accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 9.66 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: accuracy.py, prompt: accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.04 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.07 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.06 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.06 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.05 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.05 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.20 | Rollup Validation declared with valid tests | src/tools/dotcover/tests/unit/test_analyze.py | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.79 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 90.19 | Adapter successfully persisted fixture data | Fixture: dotcover_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.43 | All 3 quality rules have implementation coverage | coverage_bounds, statement_invariants, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.25 | Adapter DotcoverAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.33 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.19 | Tool 'dotcover' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.24 | dbt staging model(s) found | stg_dotcover_file_metrics.sql, stg_lz_dotcover_type_coverage.sql, stg_lz_dotcover_method_coverage.sql, stg_lz_dotcover_assembly_coverage.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.23 | dbt models present for tool | stg_dotcover_file_metrics.sql, stg_lz_dotcover_type_coverage.sql, stg_lz_dotcover_method_coverage.sql, stg_lz_dotcover_assembly_coverage.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.04 | All entities have aligned repositories | DotcoverAssemblyCoverage, DotcoverTypeCoverage, DotcoverMethodCoverage | - | - |
| `test.structure_naming` | pass | medium | 0.58 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 28.07 | Cross-tool SQL joins use correct patterns (261 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.32 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## git-blame-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-blame-scanner/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.43 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-blame-scanner/evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.48 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | skip | high | 0.11 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.18 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.46 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.07 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.08 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.06 | evaluate target input path is valid | input: evaluation/results | - | - |
| `schema.draft` | pass | medium | 0.37 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.29 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.44 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.04 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.03 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.09 | LLM judge count meets minimum (5 >= 4) | ownership_accuracy.py, actionability.py, integration.py, churn_validity.py, utils.py | - | - |
| `evaluation.synthetic_context` | pass | high | 12.77 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: ownership_accuracy.py, prompt: ownership_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.05 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.07 | Programmatic evaluation schema valid | timestamp, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.06 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.15 | LLM evaluation schema valid | timestamp, output_dir, model, trace_id, judges, summary, programmatic_input, decision, score, dimensions | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.13 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-blame-scanner/evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.12 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.25 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_git_blame_direct_vs_recursive.sql, src/tools/git-blame-scanner/tests/unit/test_analyze.py | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.75 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 107.37 | Adapter successfully persisted fixture data | Fixture: git_blame_scanner_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.64 | All 4 quality rules have implementation coverage | paths, ownership_valid, churn_monotonic, authors_positive | - | - |
| `sot.adapter_registered` | pass | medium | 0.29 | Adapter GitBlameScannerAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.34 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.19 | Tool 'git-blame-scanner' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.24 | dbt staging model(s) found | stg_git_blame_author_stats.sql, stg_git_blame_summary.sql | - | - |
| `dbt.model_coverage` | pass | high | 1.19 | dbt models present for tool | stg_git_blame_author_stats.sql, stg_git_blame_summary.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.04 | All entities have aligned repositories | GitBlameFileSummary, GitBlameAuthorStats | - | - |
| `test.structure_naming` | pass | medium | 0.76 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 28.07 | Cross-tool SQL joins use correct patterns (261 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.30 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## git-fame

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.33 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.26 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | skip | high | 0.15 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.18 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.35 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.05 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.08 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.06 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.40 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.12 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.38 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.37 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.09 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.08 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.25 | LLM judge count meets minimum (7 >= 4) | integration_readiness.py, concentration_metrics.py, evidence_quality.py, authorship_quality.py, utils.py, bus_factor_accuracy.py, output_completeness.py | - | - |
| `evaluation.synthetic_context` | pass | high | 15.07 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: authorship_quality.py, prompt: authorship_quality.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.10 | Ground truth files present | synthetic.json, multi-author.json, bus-factor-1.json, balanced.json, multi-branch.json, single-author.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.01 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.08 | Programmatic evaluation schema valid | timestamp, tool, version, overall_score, classification, summary, dimensions | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.07 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.10 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.09 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.09 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.35 | Rollup Validation declared with valid tests | src/tools/git-fame/tests/scripts/test_analyze.py, src/tools/git-fame/tests/scripts/test_authorship_accuracy_checks.py, src/tools/git-fame/tests/scripts/test_output_quality_checks.py, src/tools/git-fame/tests/scripts/test_reliability_checks.py | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.73 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 72.65 | Adapter successfully persisted fixture data | Fixture: git_fame_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.20 | All 3 quality rules have implementation coverage | hhi_valid, ownership_sums_100, bus_factor_valid | - | - |
| `sot.adapter_registered` | pass | medium | 0.28 | Adapter GitFameAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.34 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.18 | Tool 'git-fame' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.25 | dbt staging model(s) found | stg_lz_git_fame_authors.sql, stg_lz_git_fame_summary.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.23 | dbt models present for tool | stg_lz_git_fame_authors.sql, stg_lz_git_fame_summary.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.07 | All entities have aligned repositories | GitFameAuthor, GitFameSummary | - | - |
| `test.structure_naming` | pass | medium | 0.90 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 28.29 | Cross-tool SQL joins use correct patterns (261 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.45 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## git-sizer

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/evaluation/results/output.json, WARNING: Output is 20 days old (threshold: 14 days) | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/evaluation/scorecard.md, WARNING: Output is 23 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 0.43 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/evaluation/llm/results/llm_evaluation.json, WARNING: Output is 20 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.30 | LLM evaluation decision meets threshold | WEAK_PASS | - | - |
| `output.load` | pass | high | 0.28 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/evaluation/results/output.json | - | - |
| `output.paths` | pass | high | 0.27 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.02 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | git-sizer, git-sizer | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.38 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 150.61 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.30 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.57 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.05 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.11 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.12 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.09 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.10 | evaluate target input path is valid | input: evaluation/results | - | - |
| `schema.draft` | pass | medium | 0.14 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.10 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.40 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.40 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.07 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.06 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.36 | LLM judge count meets minimum (4 >= 4) | integration_fit.py, size_accuracy.py, actionability.py, threshold_quality.py | - | - |
| `evaluation.synthetic_context` | pass | high | 11.35 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: size_accuracy.py, prompt: size_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.34 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.36 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.11 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.40 | LLM evaluation schema valid | timestamp, analysis_path, model, trace_id, judges, summary, programmatic_input, decision, score, dimensions | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.12 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.11 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.23 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_git_sizer_repo_level_only.sql | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.90 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 93.05 | Adapter successfully persisted fixture data | Fixture: git_sizer_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.71 | All 3 quality rules have implementation coverage | health_grade_valid, metrics_non_negative, violation_levels | - | - |
| `sot.adapter_registered` | pass | medium | 0.28 | Adapter GitSizerAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.35 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.19 | Tool 'git-sizer' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.27 | dbt staging model(s) found | stg_lz_git_sizer_metrics.sql, stg_lz_git_sizer_violations.sql, stg_lz_git_sizer_lfs_candidates.sql, stg_git_sizer_lfs_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.26 | dbt models present for tool | stg_lz_git_sizer_metrics.sql, stg_lz_git_sizer_violations.sql, stg_lz_git_sizer_lfs_candidates.sql, stg_git_sizer_lfs_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.51 | All entities have aligned repositories | GitSizerMetric, GitSizerViolation, GitSizerLfsCandidate | - | - |
| `test.structure_naming` | pass | medium | 0.96 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 28.03 | Cross-tool SQL joins use correct patterns (261 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.47 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## gitleaks

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/evaluation/scorecard.md, WARNING: Output is 16 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 0.45 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/evaluation/llm/results/llm-eval-20260214-140525.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.32 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | skip | high | 0.15 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.18 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.47 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.05 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.08 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.07 | evaluate target input path is valid | input: outputs/runs | - | - |
| `schema.draft` | pass | medium | 0.38 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.12 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.63 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.86 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.09 | LLM judge count meets minimum (4 >= 4) | false_positive.py, secret_coverage.py, detection_accuracy.py, severity_classification.py | - | - |
| `evaluation.synthetic_context` | pass | high | 4.08 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: detection_accuracy.py, prompt: detection_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.03 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.01 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.28 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary, categories | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.06 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.17 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.05 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.05 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.33 | Rollup Validation declared with valid tests | src/tools/gitleaks/tests/unit/test_rollup_invariants.py, src/sot-engine/dbt/tests/test_rollup_gitleaks_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.72 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 107.82 | Adapter successfully persisted fixture data | Fixture: gitleaks_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.75 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.29 | Adapter GitleaksAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.34 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.18 | Tool 'gitleaks' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.25 | dbt staging model(s) found | stg_gitleaks_secrets.sql, stg_lz_gitleaks_secrets.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.92 | dbt models present for tool | stg_gitleaks_secrets.sql, stg_lz_gitleaks_secrets.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.80 | All entities have aligned repositories | GitleaksSecret | - | - |
| `test.structure_naming` | pass | medium | 1.43 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 28.23 | Cross-tool SQL joins use correct patterns (261 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.43 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## layout-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner/outputs/70369b56-0250-4085-a006-331135ee4da8/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner/evaluation/scorecard.md, WARNING: Output is 16 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 2.73 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner/evaluation/llm/results/llm_evaluation.json, WARNING: Output is 20 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.32 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 0.43 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner/outputs/70369b56-0250-4085-a006-331135ee4da8/output.json | - | - |
| `output.paths` | pass | high | 0.66 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.02 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | layout-scanner, layout-scanner | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.47 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 165.70 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.27 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.63 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.10 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.10 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.08 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.19 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.15 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.77 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.82 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.11 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.06 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.13 | LLM judge count meets minimum (4 >= 4) | classification_reasoning.py, hierarchy_consistency.py, language_detection.py, directory_taxonomy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 8.21 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: classification_reasoning.py, prompt: classification_reasoning.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.11 | Ground truth files present | mixed-language.json, edge-cases.json, generated-code.json, config-heavy.json, vendor-heavy.json, small-clean.json, deep-nesting.json, mixed-types.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 2.31 | Programmatic evaluation schema valid | timestamp, evaluated_count, average_score, decision, score, summary, checks, repositories | - | - |
| `evaluation.programmatic_quality` | pass | high | 2.10 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.03 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.22 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.06 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.05 | LLM evaluation passed | WEAK_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.36 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_layout_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.77 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 215.21 | Adapter successfully persisted fixture data | Fixture: layout_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.61 | All 3 quality rules have implementation coverage | paths, ranges, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.28 | Adapter LayoutAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.34 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.00 | layout-scanner handled specially as prerequisite tool | Layout is ingested before TOOL_INGESTION_CONFIGS loop | - | - |
| `sot.dbt_staging_model` | pass | high | 0.28 | dbt staging model(s) found | stg_lz_layout_files.sql, stg_lz_layout_directories.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.95 | dbt models present for tool | stg_lz_layout_files.sql, stg_lz_layout_directories.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.95 | All entities have aligned repositories | LayoutFile, LayoutDirectory | - | - |
| `test.structure_naming` | pass | medium | 1.32 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 34.64 | Cross-tool SQL joins use correct patterns (261 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.56 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## lizard

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/lizard/evaluation/results/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/lizard/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.93 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/lizard/evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.28 | LLM evaluation decision meets threshold | WEAK_PASS | - | - |
| `output.load` | pass | high | 3.23 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/lizard/evaluation/results/output.json | - | - |
| `output.paths` | pass | high | 19.41 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.04 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.16 | Path consistency validated | Checked 85 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | lizard, lizard | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.77 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 227.36 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.27 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.16 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.09 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.12 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.09 | evaluate target input path is valid | input: $(EVAL_OUTPUT_DIR)/output.json | - | - |
| `schema.draft` | pass | medium | 0.18 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.15 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.93 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.52 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.06 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.13 | LLM judge count meets minimum (4 >= 4) | hotspot_ranking.py, ccn_accuracy.py, function_detection.py, statistics.py | - | - |
| `evaluation.synthetic_context` | pass | high | 16.20 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: ccn_accuracy.py, prompt: ccn_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.40 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.51 | Programmatic evaluation schema valid | decision, score, timestamp, analysis_path, ground_truth_path, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.43 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.10 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.08 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.07 | LLM evaluation passed | WEAK_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.36 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_lizard_direct_distribution_ranges.sql, src/sot-engine/dbt/tests/test_rollup_lizard_direct_vs_recursive.sql, src/sot-engine/dbt/tests/test_rollup_lizard_distribution_ranges.sql | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.80 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 167.40 | Adapter successfully persisted fixture data | Fixture: lizard_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.24 | All 3 quality rules have implementation coverage | paths, ranges, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.33 | Adapter LizardAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.35 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.19 | Tool 'lizard' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.27 | dbt staging model(s) found | stg_lz_lizard_file_metrics.sql, stg_lz_lizard_function_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.89 | dbt models present for tool | stg_lz_lizard_file_metrics.sql, stg_lz_lizard_function_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.65 | All entities have aligned repositories | LizardFileMetric, LizardFunctionMetric | - | - |
| `test.structure_naming` | pass | medium | 1.16 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 29.01 | Cross-tool SQL joins use correct patterns (261 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.32 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## pmd-cpd

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.52 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.25 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | skip | high | 0.09 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.18 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.37 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.05 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.12 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.09 | evaluate target input path is valid | input: $(SYNTHETIC_OUTPUT) | - | - |
| `schema.draft` | pass | medium | 0.47 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.09 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.50 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.75 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.06 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.32 | LLM judge count meets minimum (4 >= 4) | duplication_accuracy.py, actionability.py, semantic_detection.py, cross_file_detection.py | - | - |
| `evaluation.synthetic_context` | pass | high | 5.09 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: duplication_accuracy.py, prompt: duplication_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.32 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.01 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.22 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.20 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.09 | LLM evaluation schema valid | timestamp, analysis_path, model, summary, judges, score, decision, programmatic_input, combined | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.08 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.08 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.35 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_pmd_cpd_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.80 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 236.25 | Adapter successfully persisted fixture data | Fixture: pmd_cpd_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.74 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.28 | Adapter PmdCpdAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.34 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.18 | Tool 'pmd-cpd' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.24 | dbt staging model(s) found | stg_lz_pmd_cpd_duplications.sql, stg_lz_pmd_cpd_occurrences.sql, stg_lz_pmd_cpd_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.91 | dbt models present for tool | stg_lz_pmd_cpd_duplications.sql, stg_lz_pmd_cpd_occurrences.sql, stg_lz_pmd_cpd_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.14 | All entities have aligned repositories | PmdCpdFileMetric, PmdCpdDuplication, PmdCpdOccurrence | - | - |
| `test.structure_naming` | pass | medium | 1.19 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 28.11 | Cross-tool SQL joins use correct patterns (261 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.43 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## roslyn-analyzers

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/evaluation/scorecard.md, WARNING: Output is 16 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | fail | high | 0.33 | Evaluation decision below required threshold | FAIL | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/evaluation/llm/results/llm_evaluation.json, WARNING: Output is 20 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.31 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | skip | high | 0.16 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.20 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.30 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.05 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.12 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.15 | evaluate uses $(OUTPUT_DIR) but depends on analyze | prerequisites: $(VENV_READY) analyze | - | - |
| `schema.draft` | pass | medium | 0.41 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.11 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.42 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.68 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.06 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.09 | LLM judge count meets minimum (5 >= 4) | overall_quality.py, integration_fit.py, resource_management.py, security_detection.py, design_analysis.py | - | - |
| `evaluation.synthetic_context` | pass | high | 14.99 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: security_detection.py, prompt: security_detection.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.10 | Ground truth files present | clean-code.json, resource-management.json, dead-code.json, csharp.json, security-issues.json, design-violations.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.08 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary | - | - |
| `evaluation.programmatic_quality` | fail | high | 0.06 | Programmatic evaluation failed | FAIL | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.35 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.09 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.08 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.42 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_roslyn_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.72 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 146.89 | Adapter successfully persisted fixture data | Fixture: roslyn_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.71 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.27 | Adapter RoslynAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.34 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.19 | Tool 'roslyn-analyzers' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.24 | dbt staging model(s) found | stg_lz_roslyn_violations.sql, stg_roslyn_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 1.01 | dbt models present for tool | stg_lz_roslyn_violations.sql, stg_roslyn_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.56 | All entities have aligned repositories | RoslynViolation | - | - |
| `test.structure_naming` | pass | medium | 0.45 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 28.10 | Cross-tool SQL joins use correct patterns (261 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.31 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## scancode

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.77 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/evaluation/llm/results/llm-eval-20260214-134748.json | - | - |
| `evaluation.llm_quality` | pass | medium | 1.01 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | skip | high | 0.10 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.19 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.47 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.07 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.08 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.08 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.43 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.13 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.41 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.50 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.08 | LLM judge count meets minimum (4 >= 4) | coverage_judge.py, accuracy_judge.py, actionability_judge.py, risk_classification_judge.py | - | - |
| `evaluation.synthetic_context` | pass | high | 4.38 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: accuracy_judge.py, prompt: accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.22 | Ground truth files present | multi-license.json, mit-only.json, gpl-mixed.json, apache-bsd.json, public-domain.json, spdx-expression.json, no-license.json, dual-licensed.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.71 | Programmatic evaluation schema valid | timestamp, tool, version, decision, score, summary, checks, total_repositories, reports | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.55 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.90 | LLM evaluation schema valid | run_id, timestamp, model, dimensions, score, total_score, average_confidence, decision, programmatic_score, combined_score | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.57 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.55 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.19 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_scancode_repo_level_metrics.sql | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.74 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 150.50 | Adapter successfully persisted fixture data | Fixture: scancode_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.60 | All 3 quality rules have implementation coverage | paths, confidence, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.29 | Adapter ScancodeAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.34 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.18 | Tool 'scancode' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.24 | dbt staging model(s) found | stg_lz_scancode_summary.sql, stg_lz_scancode_file_licenses.sql, stg_scancode_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.22 | dbt models present for tool | stg_lz_scancode_summary.sql, stg_lz_scancode_file_licenses.sql, stg_scancode_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.41 | All entities have aligned repositories | ScancodeFileLicense, ScancodeSummary | - | - |
| `test.structure_naming` | pass | medium | 1.41 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 28.02 | Cross-tool SQL joins use correct patterns (261 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.35 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## scc

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/evaluation/results/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.69 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/evaluation/llm/results/llm-eval-20260125-104034.json, WARNING: Output is 28 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.45 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 1.09 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/evaluation/results/output.json | - | - |
| `output.paths` | pass | high | 7.47 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.03 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.14 | Path consistency validated | Checked 94 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | scc, scc | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.43 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 178.00 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.28 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.34 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.11 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.11 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.08 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.16 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.13 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.68 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.81 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.14 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.12 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.30 | LLM judge count meets minimum (10 >= 4) | error_messages.py, documentation.py, edge_cases.py, directory_analysis.py, integration_fit.py, code_quality.py, risk.py, statistics.py, comparative.py, api_design.py | - | - |
| `evaluation.synthetic_context` | pass | high | 14.55 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: directory_analysis.py, prompt: directory_analysis.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.05 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.32 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary, run_id, dimensions, total_score | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.26 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.52 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.13 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.13 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.39 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_scc_direct_distribution_ranges.sql, src/sot-engine/dbt/tests/test_rollup_scc_direct_vs_recursive.sql, src/sot-engine/dbt/tests/test_rollup_scc_distribution_ranges.sql | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.76 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 180.36 | Adapter successfully persisted fixture data | Fixture: scc_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.29 | All 4 quality rules have implementation coverage | paths, ranges, ratios, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.33 | Adapter SccAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.35 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.18 | Tool 'scc' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.25 | dbt staging model(s) found | stg_lz_scc_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.83 | dbt models present for tool | stg_lz_scc_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.48 | All entities have aligned repositories | SccFileMetric | - | - |
| `test.structure_naming` | pass | medium | 1.63 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 28.48 | Cross-tool SQL joins use correct patterns (261 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.36 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## semgrep

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/evaluation/results/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/evaluation/scorecard.md, WARNING: Output is 16 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 0.40 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/evaluation/llm/results/llm-eval-20260130-120000.json, WARNING: Output is 23 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.31 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 1.04 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/evaluation/results/output.json | - | - |
| `output.paths` | pass | high | 8.06 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.03 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.10 | Path consistency validated | Checked 65 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | semgrep, semgrep | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.32 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 174.45 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.28 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.39 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.10 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.14 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.11 | evaluate target input path is valid | input: evaluation/results/output.json | - | - |
| `schema.draft` | pass | medium | 0.15 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.11 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.82 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.74 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.10 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.06 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.50 | LLM judge count meets minimum (5 >= 4) | rule_coverage.py, actionability.py, security_detection.py, smell_accuracy.py, false_positive_rate.py | - | - |
| `evaluation.synthetic_context` | pass | high | 18.74 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: security_detection.py, prompt: security_detection.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.13 | Ground truth files present | java.json, go.json, csharp.json, rust.json, javascript.json, typescript.json, python.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.08 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.07 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.51 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, analysis_path, combined | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.12 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.11 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.37 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_semgrep_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.73 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 154.28 | Adapter successfully persisted fixture data | Fixture: semgrep_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 2.72 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.32 | Adapter SemgrepAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.34 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.19 | Tool 'semgrep' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.26 | dbt staging model(s) found | stg_semgrep_file_metrics.sql, stg_lz_semgrep_smells.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.95 | dbt models present for tool | stg_semgrep_file_metrics.sql, stg_lz_semgrep_smells.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.40 | All entities have aligned repositories | SemgrepSmell | - | - |
| `test.structure_naming` | pass | medium | 1.53 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 28.20 | Cross-tool SQL joins use correct patterns (261 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.49 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## sonarqube

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/evaluation/results/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/evaluation/scorecard.md, WARNING: Output is 23 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 0.37 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/evaluation/llm/results/llm-eval-20260130-120000.json, WARNING: Output is 23 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.28 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 0.69 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/evaluation/results/output.json | - | - |
| `output.paths` | pass | high | 6.54 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.02 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.2.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | sonarqube, sonarqube | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.41 | Output schema_version matches schema constraint | 1.2.0 | - | - |
| `output.schema_validate` | pass | critical | 154.24 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.27 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.00 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.09 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.15 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.11 | analyze target produces output.json | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.11 | evaluate target input path is valid | input: evaluation/results/output.json | - | - |
| `schema.draft` | pass | medium | 0.12 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.83 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.73 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.09 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.52 | LLM judge count meets minimum (4 >= 4) | issue_accuracy.py, integration_fit.py, actionability.py, coverage_completeness.py | - | - |
| `evaluation.synthetic_context` | pass | high | 10.27 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: issue_accuracy.py, prompt: issue_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.28 | Ground truth files present | java-security.json, typescript-duplication.json, csharp-baseline.json, python-mixed.json, csharp-complex.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.08 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.06 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.23 | LLM evaluation schema valid | timestamp, analysis_path, summary, dimensions, model, score, decision, programmatic_input, combined | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.06 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.05 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.45 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_sonarqube_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.05 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.82 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 248.84 | Adapter successfully persisted fixture data | Fixture: sonarqube_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.10 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.39 | Adapter SonarqubeAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.36 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.20 | Tool 'sonarqube' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.27 | dbt staging model(s) found | stg_sonarqube_issues.sql, stg_sonarqube_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.96 | dbt models present for tool | stg_sonarqube_issues.sql, stg_sonarqube_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.38 | All entities have aligned repositories | SonarqubeIssue, SonarqubeMetric | - | - |
| `test.structure_naming` | pass | medium | 1.15 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 28.08 | Cross-tool SQL joins use correct patterns (261 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.34 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## symbol-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/evaluation/results/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.99 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_quality` | pass | medium | 0.47 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 0.20 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/evaluation/results/output.json | - | - |
| `output.paths` | pass | high | 0.31 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.02 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | symbol-scanner, symbol-scanner | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.46 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 150.39 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.28 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.68 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.11 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.11 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.09 | evaluate target input path is valid | input: $(EVAL_OUTPUT_DIR)/output.json | - | - |
| `schema.draft` | pass | medium | 0.13 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.10 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.60 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.42 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.07 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.06 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.38 | LLM judge count meets minimum (4 >= 4) | call_relationship.py, import_completeness.py, integration.py, symbol_accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 7.28 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: call_relationship.py, prompt: call_relationship.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.18 | Ground truth files present | metaprogramming.json, csharp-tshock.json, cross-module-calls.json, deep-hierarchy.json, encoding-edge-cases.json, circular-imports.json, js-cross-module-calls.json, type-checking-imports.json, decorators-advanced.json, dynamic-code-generation.json, async-patterns.json, nested-structures.json, class-hierarchy.json, simple-functions.json, generators-comprehensions.json, dataclasses-protocols.json, ts-class-hierarchy.json, deep-nesting-stress.json, partial-syntax-errors.json, unresolved-externals.json, confusing-names.json, modern-syntax.json, large-file.json, js-simple-functions.json, web-framework-patterns.json, import-patterns.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.57 | Programmatic evaluation schema valid | timestamp, decision, score, checks, summary, aggregate, per_repo_results, metadata, regression | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.50 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.10 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.08 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.07 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.28 | Rollup Validation declared with valid tests | src/sot-engine/dbt/models/staging/stg_lz_code_symbols.sql | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.89 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 150.84 | Adapter successfully persisted fixture data | Fixture: symbol_scanner_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.77 | All 3 quality rules have implementation coverage | paths, ranges, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.33 | Adapter SymbolScannerAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.35 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.19 | Tool 'symbol-scanner' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.26 | dbt staging model(s) found | stg_symbol_calls_file_metrics.sql, stg_symbols_file_metrics.sql, stg_symbol_coupling_metrics.sql, stg_lz_symbol_calls.sql, stg_lz_code_symbols.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.28 | dbt models present for tool | stg_symbol_calls_file_metrics.sql, stg_symbols_file_metrics.sql, stg_symbol_coupling_metrics.sql, stg_lz_symbol_calls.sql, stg_lz_code_symbols.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.84 | All entities have aligned repositories | CodeSymbol, SymbolCall, FileImport | - | - |
| `test.structure_naming` | pass | medium | 1.26 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 28.11 | Cross-tool SQL joins use correct patterns (261 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.45 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## trivy

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/evaluation/scorecard.md, WARNING: Output is 24 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 0.45 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/evaluation/llm/results/synthetic-llm-eval.json, WARNING: Output is 23 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.31 | LLM evaluation score meets threshold | score=4.0 | - | - |
| `output.load` | skip | high | 0.22 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.19 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.27 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.05 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.06 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.40 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.11 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.52 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.39 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.09 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.11 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.09 | LLM judge count meets minimum (7 >= 4) | freshness_quality.py, vulnerability_detection.py, vulnerability_accuracy.py, severity_accuracy.py, iac_quality.py, sbom_completeness.py, false_positive_rate.py | - | - |
| `evaluation.synthetic_context` | pass | high | 13.62 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: vulnerability_accuracy.py, prompt: vulnerability_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.25 | Ground truth files present | dotnet-outdated.json, js-fullstack.json, vulnerable-npm.json, iac-terraform.json, no-vulnerabilities.json, iac-misconfigs.json, mixed-severity.json, java-outdated.json, critical-cves.json, outdated-deps.json, cfn-misconfigs.json, k8s-misconfigs.json | - | - |
| `evaluation.scorecard` | pass | low | 0.04 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.57 | Programmatic evaluation schema valid | timestamp, tool, version, decision, score, classification, overall_score, summary, checks, dimensions | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.25 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.39 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.11 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.10 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.23 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_trivy_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.85 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 270.19 | Adapter successfully persisted fixture data | Fixture: trivy_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.64 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.30 | Adapter TrivyAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.34 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.19 | Tool 'trivy' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.25 | dbt staging model(s) found | stg_trivy_file_metrics.sql, stg_trivy_iac_misconfigs.sql, stg_trivy_vulnerabilities.sql, stg_trivy_target_metrics.sql, stg_trivy_targets.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.80 | dbt models present for tool | stg_trivy_file_metrics.sql, stg_trivy_iac_misconfigs.sql, stg_trivy_vulnerabilities.sql, stg_trivy_target_metrics.sql, stg_trivy_targets.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.44 | All entities have aligned repositories | TrivyVulnerability, TrivyTarget, TrivyIacMisconfig | - | - |
| `test.structure_naming` | pass | medium | 1.39 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 28.15 | Cross-tool SQL joins use correct patterns (261 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.44 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |
