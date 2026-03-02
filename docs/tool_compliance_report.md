# Tool Compliance Report

Generated: `2026-03-01T18:51:39.569515+00:00`

Summary: 18 passed, 0 failed, 18 total

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
| roslyn-analyzers | pass | 48 | 0 | - |
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
| trivy | `adapter.integration` | 299.47 |
| sonarqube | `adapter.integration` | 251.82 |
| coverage-ingest | `adapter.compliance` | 246.51 |
| pmd-cpd | `adapter.integration` | 223.18 |
| layout-scanner | `adapter.integration` | 218.92 |
| lizard | `output.schema_validate` | 218.02 |
| roslyn-analyzers | `output.schema_validate` | 212.51 |
| scc | `adapter.integration` | 183.33 |
| semgrep | `output.schema_validate` | 176.60 |
| scc | `output.schema_validate` | 173.86 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| sonarqube | 0.51 |
| lizard | 0.50 |
| layout-scanner | 0.48 |
| roslyn-analyzers | 0.48 |
| scc | 0.46 |
| coverage-ingest | 0.45 |
| semgrep | 0.44 |
| symbol-scanner | 0.40 |
| trivy | 0.39 |
| git-sizer | 0.34 |
| pmd-cpd | 0.30 |
| scancode | 0.23 |
| dotcover | 0.20 |
| git-blame-scanner | 0.20 |
| gitleaks | 0.19 |
| devskim | 0.17 |
| git-fame | 0.17 |
| dependensee | 0.14 |

## coverage-ingest

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/coverage-ingest/evaluation/scorecard.md, WARNING: Output is 16 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 0.39 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/coverage-ingest/evaluation/results/llm_evaluation.json, WARNING: Output is 16 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.37 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | skip | high | 0.11 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.19 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.32 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.11 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.15 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.14 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.23 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.42 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.09 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.60 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.27 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.04 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.06 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.27 | LLM judge count meets minimum (4 >= 4) | cross_format_consistency.py, gap_actionability.py, parser_accuracy.py, risk_tier_quality.py | - | - |
| `evaluation.synthetic_context` | pass | high | 13.49 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: gap_actionability.py, prompt: gap_actionability.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.03 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.08 | Programmatic evaluation schema valid | timestamp, score, decision, summary, passed, total, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.07 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.13 | LLM evaluation schema valid | timestamp, output_dir, model, trace_id, judges, summary, programmatic_input, decision, score, dimensions | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.14 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.12 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.51 | Rollup Validation declared with valid tests | src/tools/coverage-ingest/tests/unit/test_lcov_parser.py, src/tools/coverage-ingest/tests/unit/test_jacoco_parser.py, src/tools/coverage-ingest/tests/integration/test_e2e.py | - | - |
| `adapter.compliance` | pass | info | 246.51 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.46 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 76.83 | Adapter successfully persisted fixture data | Fixture: coverage_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.81 | All 4 quality rules have implementation coverage | paths, ranges, coverage_invariants, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.40 | Adapter CoverageIngestAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.38 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.37 | Tool 'coverage-ingest' registered with adapter in TOOL_REGISTRY | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.28 | dbt staging model(s) found | stg_lz_coverage_summary.sql, stg_lz_dotcover_type_coverage.sql, stg_lz_dotcover_method_coverage.sql, stg_lz_dotcover_assembly_coverage.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.28 | dbt models present for tool | stg_lz_coverage_summary.sql, stg_lz_dotcover_type_coverage.sql, stg_lz_dotcover_method_coverage.sql, stg_lz_dotcover_assembly_coverage.sql | - | - |
| `entity.repository_alignment` | pass | high | 12.92 | All entities have aligned repositories | CoverageSummary | - | - |
| `test.structure_naming` | pass | medium | 0.56 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 86.39 | Cross-tool SQL joins use correct patterns (293 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.26 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## dependensee

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/evaluation/scorecard.md, WARNING: Output is 16 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 0.21 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/evaluation/results/llm_evaluation.json, WARNING: Output is 15 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.23 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | skip | high | 0.12 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.19 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.21 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.05 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.07 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.05 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.13 | evaluate target input path is valid | input: $(LATEST_OUTPUT) | - | - |
| `schema.draft` | pass | medium | 0.25 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.36 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.29 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.05 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.08 | LLM judge count meets minimum (4 >= 4) | project_detection.py, circular_detection.py, graph_quality.py, dependency_accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 8.36 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: dependency_accuracy.py, prompt: dependency_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.03 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.01 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.06 | Programmatic evaluation schema valid | timestamp, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.06 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.09 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.08 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.08 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.18 | Rollup Validation declared with valid tests | src/tools/dependensee/tests/unit/test_analyze.py | - | - |
| `adapter.compliance` | pass | info | 0.05 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.18 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 61.10 | Adapter successfully persisted fixture data | Fixture: dependensee_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.93 | All 2 quality rules have implementation coverage | paths, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.26 | Adapter DependenseeAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.39 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.22 | Tool 'dependensee' registered with adapter in TOOL_REGISTRY | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.27 | dbt staging model(s) found | stg_dependensee_package_refs.sql, stg_dependensee_projects.sql, stg_dependensee_project_refs.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.25 | dbt models present for tool | stg_dependensee_package_refs.sql, stg_dependensee_projects.sql, stg_dependensee_project_refs.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.33 | All entities have aligned repositories | DependenseeProject, DependenseeProjectReference, DependenseePackageReference | - | - |
| `test.structure_naming` | pass | medium | 0.45 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 52.30 | Cross-tool SQL joins use correct patterns (293 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 1.01 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## devskim

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.37 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/evaluation/llm/results/llm-eval-20260214-135849.json, WARNING: Output is 15 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.29 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | skip | high | 0.10 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.20 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.28 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.04 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.08 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.32 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.13 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.41 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.40 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.08 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.03 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.08 | LLM judge count meets minimum (4 >= 4) | rule_coverage.py, severity_calibration.py, security_focus.py, detection_accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 7.81 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: detection_accuracy.py, prompt: detection_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.08 | Ground truth files present | api-security.json, deserialization.json, xxe.json, csharp.json, clean.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.01 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.13 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.12 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.25 | LLM evaluation schema valid | run_id, timestamp, model, score, decision, dimensions, total_score, average_confidence, combined_score, programmatic_input | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.08 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.08 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.23 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_devskim_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.59 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 76.53 | Adapter successfully persisted fixture data | Fixture: devskim_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.49 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.27 | Adapter DevskimAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.38 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.20 | Tool 'devskim' registered with adapter in TOOL_REGISTRY | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.26 | dbt staging model(s) found | stg_lz_devskim_findings.sql, stg_devskim_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.84 | dbt models present for tool | stg_lz_devskim_findings.sql, stg_devskim_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 14.87 | All entities have aligned repositories | DevskimFinding | - | - |
| `test.structure_naming` | pass | medium | 0.64 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 60.85 | Cross-tool SQL joins use correct patterns (293 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.92 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## dotcover

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.24 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/evaluation/results/llm_evaluation.json, WARNING: Output is 15 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.23 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | skip | high | 0.20 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.24 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.31 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.06 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.11 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.09 | evaluate target input path is valid | input: $(SYNTHETIC_OUTPUT_DIR) | - | - |
| `schema.draft` | pass | medium | 0.29 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.11 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.43 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.32 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.07 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.11 | LLM judge count meets minimum (4 >= 4) | false_positive.py, actionability.py, integration.py, accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 12.06 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: accuracy.py, prompt: accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.05 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.10 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.10 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.08 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.07 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.08 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.22 | Rollup Validation declared with valid tests | src/tools/dotcover/tests/unit/test_analyze.py | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 6.07 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 110.84 | Adapter successfully persisted fixture data | Fixture: dotcover_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.57 | All 3 quality rules have implementation coverage | coverage_bounds, statement_invariants, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.33 | Adapter DotcoverAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.43 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.23 | Tool 'dotcover' registered with adapter in TOOL_REGISTRY | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.31 | dbt staging model(s) found | stg_dotcover_file_metrics.sql, stg_lz_dotcover_type_coverage.sql, stg_lz_dotcover_method_coverage.sql, stg_lz_dotcover_assembly_coverage.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.30 | dbt models present for tool | stg_dotcover_file_metrics.sql, stg_lz_dotcover_type_coverage.sql, stg_lz_dotcover_method_coverage.sql, stg_lz_dotcover_assembly_coverage.sql | - | - |
| `entity.repository_alignment` | pass | high | 11.75 | All entities have aligned repositories | DotcoverAssemblyCoverage, DotcoverTypeCoverage, DotcoverMethodCoverage | - | - |
| `test.structure_naming` | pass | medium | 0.49 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 54.95 | Cross-tool SQL joins use correct patterns (293 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.33 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## git-blame-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-blame-scanner/evaluation/scorecard.md, WARNING: Output is 21 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 0.24 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-blame-scanner/evaluation/results/llm_evaluation.json, WARNING: Output is 16 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.34 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | skip | high | 0.11 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.19 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.24 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.05 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.07 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.05 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.06 | evaluate target input path is valid | input: evaluation/results | - | - |
| `schema.draft` | pass | medium | 0.24 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.30 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.26 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.04 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.03 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.08 | LLM judge count meets minimum (5 >= 4) | ownership_accuracy.py, actionability.py, integration.py, churn_validity.py, utils.py | - | - |
| `evaluation.synthetic_context` | pass | high | 12.30 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: ownership_accuracy.py, prompt: ownership_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.04 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.08 | Programmatic evaluation schema valid | timestamp, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.06 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.16 | LLM evaluation schema valid | timestamp, output_dir, model, trace_id, judges, summary, programmatic_input, decision, score, dimensions | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.14 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-blame-scanner/evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.13 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.26 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_git_blame_direct_vs_recursive.sql, src/tools/git-blame-scanner/tests/unit/test_analyze.py | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.19 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 110.16 | Adapter successfully persisted fixture data | Fixture: git_blame_scanner_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.65 | All 4 quality rules have implementation coverage | paths, ownership_valid, churn_monotonic, authors_positive | - | - |
| `sot.adapter_registered` | pass | medium | 0.27 | Adapter GitBlameScannerAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.38 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.23 | Tool 'git-blame-scanner' registered with adapter in TOOL_REGISTRY | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.25 | dbt staging model(s) found | stg_git_blame_author_stats.sql, stg_git_blame_summary.sql | - | - |
| `dbt.model_coverage` | pass | high | 1.26 | dbt models present for tool | stg_git_blame_author_stats.sql, stg_git_blame_summary.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.13 | All entities have aligned repositories | GitBlameFileSummary, GitBlameAuthorStats | - | - |
| `test.structure_naming` | pass | medium | 0.36 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 52.62 | Cross-tool SQL joins use correct patterns (293 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.40 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## git-fame

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/evaluation/scorecard.md, WARNING: Output is 15 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 0.28 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/evaluation/results/llm_evaluation.json, WARNING: Output is 15 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.34 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | skip | high | 0.13 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.18 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.25 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.05 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.08 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.06 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.26 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.35 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.36 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.10 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.08 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.10 | LLM judge count meets minimum (7 >= 4) | integration_readiness.py, concentration_metrics.py, evidence_quality.py, authorship_quality.py, utils.py, bus_factor_accuracy.py, output_completeness.py | - | - |
| `evaluation.synthetic_context` | pass | high | 14.52 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: authorship_quality.py, prompt: authorship_quality.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.12 | Ground truth files present | synthetic.json, multi-author.json, bus-factor-1.json, balanced.json, multi-branch.json, single-author.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.10 | Programmatic evaluation schema valid | timestamp, tool, version, overall_score, classification, summary, dimensions | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.08 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.11 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.10 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.09 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.34 | Rollup Validation declared with valid tests | src/tools/git-fame/tests/scripts/test_analyze.py, src/tools/git-fame/tests/scripts/test_authorship_accuracy_checks.py, src/tools/git-fame/tests/scripts/test_output_quality_checks.py, src/tools/git-fame/tests/scripts/test_reliability_checks.py | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.18 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 78.95 | Adapter successfully persisted fixture data | Fixture: git_fame_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.56 | All 3 quality rules have implementation coverage | hhi_valid, ownership_sums_100, bus_factor_valid | - | - |
| `sot.adapter_registered` | pass | medium | 0.28 | Adapter GitFameAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.39 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.20 | Tool 'git-fame' registered with adapter in TOOL_REGISTRY | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.26 | dbt staging model(s) found | stg_lz_git_fame_authors.sql, stg_lz_git_fame_summary.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.23 | dbt models present for tool | stg_lz_git_fame_authors.sql, stg_lz_git_fame_summary.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.51 | All entities have aligned repositories | GitFameAuthor, GitFameSummary | - | - |
| `test.structure_naming` | pass | medium | 0.41 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 50.84 | Cross-tool SQL joins use correct patterns (293 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.92 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## git-sizer

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/evaluation/results/output.json, WARNING: Output is 27 days old (threshold: 14 days) | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/evaluation/scorecard.md, WARNING: Output is 29 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 0.40 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/evaluation/llm/results/llm_evaluation.json, WARNING: Output is 27 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.25 | LLM evaluation decision meets threshold | WEAK_PASS | - | - |
| `output.load` | pass | high | 0.22 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/evaluation/results/output.json | - | - |
| `output.paths` | pass | high | 0.29 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.02 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | git-sizer, git-sizer | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.31 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 154.07 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.31 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.42 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.11 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.12 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.09 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.10 | evaluate target input path is valid | input: evaluation/results | - | - |
| `schema.draft` | pass | medium | 0.13 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.10 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.41 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.39 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.07 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.07 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.14 | LLM judge count meets minimum (4 >= 4) | integration_fit.py, size_accuracy.py, actionability.py, threshold_quality.py | - | - |
| `evaluation.synthetic_context` | pass | high | 10.76 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: size_accuracy.py, prompt: size_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.22 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.30 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.11 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.31 | LLM evaluation schema valid | timestamp, analysis_path, model, trace_id, judges, summary, programmatic_input, decision, score, dimensions | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.12 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.11 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.26 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_git_sizer_repo_level_only.sql | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.37 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 95.31 | Adapter successfully persisted fixture data | Fixture: git_sizer_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.49 | All 3 quality rules have implementation coverage | health_grade_valid, metrics_non_negative, violation_levels | - | - |
| `sot.adapter_registered` | pass | medium | 0.29 | Adapter GitSizerAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.39 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.22 | Tool 'git-sizer' registered with adapter in TOOL_REGISTRY | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.29 | dbt staging model(s) found | stg_lz_git_sizer_metrics.sql, stg_lz_git_sizer_violations.sql, stg_lz_git_sizer_lfs_candidates.sql, stg_git_sizer_lfs_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.27 | dbt models present for tool | stg_lz_git_sizer_metrics.sql, stg_lz_git_sizer_violations.sql, stg_lz_git_sizer_lfs_candidates.sql, stg_git_sizer_lfs_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.73 | All entities have aligned repositories | GitSizerMetric, GitSizerViolation, GitSizerLfsCandidate | - | - |
| `test.structure_naming` | pass | medium | 0.46 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 53.62 | Cross-tool SQL joins use correct patterns (293 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.27 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## gitleaks

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/evaluation/scorecard.md, WARNING: Output is 23 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 0.23 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/evaluation/llm/results/llm-eval-20260214-140525.json, WARNING: Output is 15 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.22 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | skip | high | 0.14 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.19 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.26 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.05 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.08 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.07 | evaluate target input path is valid | input: outputs/runs | - | - |
| `schema.draft` | pass | medium | 0.26 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.57 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.66 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.05 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.06 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.08 | LLM judge count meets minimum (4 >= 4) | false_positive.py, secret_coverage.py, detection_accuracy.py, severity_classification.py | - | - |
| `evaluation.synthetic_context` | pass | high | 5.95 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: detection_accuracy.py, prompt: detection_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.04 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.01 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.22 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary, categories | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.07 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.19 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.06 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.05 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.39 | Rollup Validation declared with valid tests | src/tools/gitleaks/tests/unit/test_rollup_invariants.py, src/sot-engine/dbt/tests/test_rollup_gitleaks_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.05 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.15 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 108.96 | Adapter successfully persisted fixture data | Fixture: gitleaks_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.01 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.28 | Adapter GitleaksAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.38 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.19 | Tool 'gitleaks' registered with adapter in TOOL_REGISTRY | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.25 | dbt staging model(s) found | stg_gitleaks_secrets.sql, stg_lz_gitleaks_secrets.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.89 | dbt models present for tool | stg_gitleaks_secrets.sql, stg_lz_gitleaks_secrets.sql | - | - |
| `entity.repository_alignment` | pass | high | 11.05 | All entities have aligned repositories | GitleaksSecret | - | - |
| `test.structure_naming` | pass | medium | 0.53 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 49.01 | Cross-tool SQL joins use correct patterns (293 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.85 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## layout-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner/outputs/70369b56-0250-4085-a006-331135ee4da8/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner/evaluation/scorecard.md, WARNING: Output is 23 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 2.57 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner/evaluation/llm/results/llm_evaluation.json, WARNING: Output is 27 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.26 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 0.25 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner/outputs/70369b56-0250-4085-a006-331135ee4da8/output.json | - | - |
| `output.paths` | pass | high | 0.66 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.02 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | layout-scanner, layout-scanner | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.36 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 170.69 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.32 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.09 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.09 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.12 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.08 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.19 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.15 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.65 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.75 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.13 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.06 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.14 | LLM judge count meets minimum (4 >= 4) | classification_reasoning.py, hierarchy_consistency.py, language_detection.py, directory_taxonomy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 7.96 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: classification_reasoning.py, prompt: classification_reasoning.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.10 | Ground truth files present | mixed-language.json, edge-cases.json, generated-code.json, config-heavy.json, vendor-heavy.json, small-clean.json, deep-nesting.json, mixed-types.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 2.30 | Programmatic evaluation schema valid | timestamp, evaluated_count, average_score, decision, score, summary, checks, repositories | - | - |
| `evaluation.programmatic_quality` | pass | high | 2.10 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.22 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.07 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.05 | LLM evaluation passed | WEAK_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.40 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_layout_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.28 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 218.92 | Adapter successfully persisted fixture data | Fixture: layout_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.11 | All 3 quality rules have implementation coverage | paths, ranges, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.31 | Adapter LayoutScannerAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.39 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.00 | layout-scanner handled specially as prerequisite tool | Layout is ingested before TOOL_INGESTION_CONFIGS loop | - | - |
| `sot.dbt_staging_model` | pass | high | 0.27 | dbt staging model(s) found | stg_lz_layout_files.sql, stg_lz_layout_directories.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.92 | dbt models present for tool | stg_lz_layout_files.sql, stg_lz_layout_directories.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.63 | All entities have aligned repositories | LayoutFile, LayoutDirectory | - | - |
| `test.structure_naming` | pass | medium | 0.59 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 51.08 | Cross-tool SQL joins use correct patterns (293 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 1.08 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## lizard

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/lizard/evaluation/results/output.json, WARNING: Output is 16 days old (threshold: 14 days) | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/lizard/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.77 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/lizard/evaluation/results/llm_evaluation.json, WARNING: Output is 15 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.31 | LLM evaluation decision meets threshold | WEAK_PASS | - | - |
| `output.load` | pass | high | 2.73 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/lizard/evaluation/results/output.json | - | - |
| `output.paths` | pass | high | 17.43 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.04 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.16 | Path consistency validated | Checked 85 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | lizard, lizard | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.52 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 218.02 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.30 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.08 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.10 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.12 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.09 | evaluate target input path is valid | input: $(EVAL_OUTPUT_DIR)/output.json | - | - |
| `schema.draft` | pass | medium | 0.20 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.16 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.74 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.55 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.09 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.07 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.13 | LLM judge count meets minimum (4 >= 4) | hotspot_ranking.py, ccn_accuracy.py, function_detection.py, statistics.py | - | - |
| `evaluation.synthetic_context` | pass | high | 16.67 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: ccn_accuracy.py, prompt: ccn_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.30 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.49 | Programmatic evaluation schema valid | decision, score, timestamp, analysis_path, ground_truth_path, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.42 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.10 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.10 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.09 | LLM evaluation passed | WEAK_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.40 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_lizard_direct_distribution_ranges.sql, src/sot-engine/dbt/tests/test_rollup_lizard_direct_vs_recursive.sql, src/sot-engine/dbt/tests/test_rollup_lizard_distribution_ranges.sql | - | - |
| `adapter.compliance` | pass | info | 0.05 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.29 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 168.22 | Adapter successfully persisted fixture data | Fixture: lizard_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.10 | All 3 quality rules have implementation coverage | paths, ranges, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.32 | Adapter LizardAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.38 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.19 | Tool 'lizard' registered with adapter in TOOL_REGISTRY | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.26 | dbt staging model(s) found | stg_lz_lizard_file_metrics.sql, stg_lz_lizard_function_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.82 | dbt models present for tool | stg_lz_lizard_file_metrics.sql, stg_lz_lizard_function_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.69 | All entities have aligned repositories | LizardFileMetric, LizardFunctionMetric | - | - |
| `test.structure_naming` | pass | medium | 0.46 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 51.82 | Cross-tool SQL joins use correct patterns (293 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.92 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## pmd-cpd

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/evaluation/scorecard.md, WARNING: Output is 15 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 0.46 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/evaluation/results/llm_evaluation.json, WARNING: Output is 16 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.30 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | skip | high | 0.10 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.19 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.30 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.05 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.11 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.09 | evaluate target input path is valid | input: $(SYNTHETIC_OUTPUT) | - | - |
| `schema.draft` | pass | medium | 0.29 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.10 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.52 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.63 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.09 | LLM judge count meets minimum (4 >= 4) | duplication_accuracy.py, actionability.py, semantic_detection.py, cross_file_detection.py | - | - |
| `evaluation.synthetic_context` | pass | high | 4.78 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: duplication_accuracy.py, prompt: duplication_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.25 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.23 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.21 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.09 | LLM evaluation schema valid | timestamp, analysis_path, model, summary, judges, score, decision, programmatic_input, combined | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.08 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.08 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.35 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_pmd_cpd_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.05 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.19 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 223.18 | Adapter successfully persisted fixture data | Fixture: pmd_cpd_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.04 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.26 | Adapter PmdCpdAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.37 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.20 | Tool 'pmd-cpd' registered with adapter in TOOL_REGISTRY | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.26 | dbt staging model(s) found | stg_lz_pmd_cpd_duplications.sql, stg_lz_pmd_cpd_occurrences.sql, stg_lz_pmd_cpd_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.94 | dbt models present for tool | stg_lz_pmd_cpd_duplications.sql, stg_lz_pmd_cpd_occurrences.sql, stg_lz_pmd_cpd_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.14 | All entities have aligned repositories | PmdCpdFileMetric, PmdCpdDuplication, PmdCpdOccurrence | - | - |
| `test.structure_naming` | pass | medium | 0.40 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 50.50 | Cross-tool SQL joins use correct patterns (293 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 1.03 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## roslyn-analyzers

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/outputs/B668E4F3-8995-4C65-BEA3-C404D182A0D7/output.json | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.08 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/evaluation/llm/results/llm_evaluation.json, WARNING: Output is 27 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.33 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 2.36 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/outputs/B668E4F3-8995-4C65-BEA3-C404D182A0D7/output.json | - | - |
| `output.paths` | pass | high | 25.15 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.03 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.13 | Path consistency validated | Checked 71 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | roslyn-analyzers, roslyn-analyzers | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.52 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 212.51 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.30 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.15 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.11 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.14 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.20 | evaluate uses $(OUTPUT_DIR) but depends on analyze | prerequisites: $(VENV_READY) analyze | - | - |
| `schema.draft` | pass | medium | 0.13 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.10 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.50 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.78 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.07 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.06 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.14 | LLM judge count meets minimum (5 >= 4) | overall_quality.py, integration_fit.py, resource_management.py, security_detection.py, design_analysis.py | - | - |
| `evaluation.synthetic_context` | pass | high | 14.86 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: security_detection.py, prompt: security_detection.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.11 | Ground truth files present | clean-code.json, resource-management.json, dead-code.json, csharp.json, security-issues.json, design-violations.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.08 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.07 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | skip | medium | 0.02 | Missing llm_evaluation.json at uniform path | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | skip | medium | 0.01 | Cannot validate schema - file missing | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_includes_programmatic` | skip | medium | 0.01 | Cannot check - file missing | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_decision_quality` | skip | medium | 0.01 | Cannot check quality - file missing | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.rollup_validation` | pass | high | 0.45 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_roslyn_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.18 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 149.29 | Adapter successfully persisted fixture data | Fixture: roslyn_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.48 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.28 | Adapter RoslynAnalyzersAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.38 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.21 | Tool 'roslyn-analyzers' registered with adapter in TOOL_REGISTRY | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.26 | dbt staging model(s) found | stg_lz_roslyn_violations.sql, stg_roslyn_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.99 | dbt models present for tool | stg_lz_roslyn_violations.sql, stg_roslyn_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.49 | All entities have aligned repositories | RoslynViolation | - | - |
| `test.structure_naming` | pass | medium | 0.40 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 50.73 | Cross-tool SQL joins use correct patterns (293 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.91 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## scancode

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/evaluation/scorecard.md, WARNING: Output is 15 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 0.89 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/evaluation/llm/results/llm-eval-20260214-134748.json, WARNING: Output is 15 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.86 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | skip | high | 0.11 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.20 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.28 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.06 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.07 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.31 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.09 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.39 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.32 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.07 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.08 | LLM judge count meets minimum (4 >= 4) | coverage_judge.py, accuracy_judge.py, actionability_judge.py, risk_classification_judge.py | - | - |
| `evaluation.synthetic_context` | pass | high | 3.54 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: accuracy_judge.py, prompt: accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.08 | Ground truth files present | multi-license.json, mit-only.json, gpl-mixed.json, apache-bsd.json, public-domain.json, spdx-expression.json, no-license.json, dual-licensed.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.01 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.53 | Programmatic evaluation schema valid | timestamp, tool, version, decision, score, summary, checks, total_repositories, reports | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.53 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.78 | LLM evaluation schema valid | run_id, timestamp, model, dimensions, score, total_score, average_confidence, decision, programmatic_score, combined_score | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.56 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.55 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.17 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_scancode_repo_level_metrics.sql | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.16 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 152.17 | Adapter successfully persisted fixture data | Fixture: scancode_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.47 | All 3 quality rules have implementation coverage | paths, confidence, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.29 | Adapter ScancodeAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.37 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.20 | Tool 'scancode' registered with adapter in TOOL_REGISTRY | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.26 | dbt staging model(s) found | stg_lz_scancode_summary.sql, stg_lz_scancode_file_licenses.sql, stg_scancode_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.23 | dbt models present for tool | stg_lz_scancode_summary.sql, stg_lz_scancode_file_licenses.sql, stg_scancode_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.42 | All entities have aligned repositories | ScancodeFileLicense, ScancodeSummary | - | - |
| `test.structure_naming` | pass | medium | 0.91 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 49.60 | Cross-tool SQL joins use correct patterns (293 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.36 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## scc

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/evaluation/results/output.json, WARNING: Output is 16 days old (threshold: 14 days) | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/evaluation/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.75 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/evaluation/llm/results/llm-eval-20260125-104034.json, WARNING: Output is 35 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.50 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 1.25 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/evaluation/results/output.json | - | - |
| `output.paths` | pass | high | 7.48 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.03 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.14 | Path consistency validated | Checked 94 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | scc, scc | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.57 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 173.86 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.30 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.06 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.12 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.11 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.09 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.09 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.17 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.14 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.78 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.78 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.14 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.13 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.33 | LLM judge count meets minimum (10 >= 4) | error_messages.py, documentation.py, edge_cases.py, directory_analysis.py, integration_fit.py, code_quality.py, risk.py, statistics.py, comparative.py, api_design.py | - | - |
| `evaluation.synthetic_context` | pass | high | 13.97 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: directory_analysis.py, prompt: directory_analysis.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.04 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.32 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary, run_id, dimensions, total_score | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.26 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.31 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.13 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.12 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.44 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_scc_direct_distribution_ranges.sql, src/sot-engine/dbt/tests/test_rollup_scc_direct_vs_recursive.sql, src/sot-engine/dbt/tests/test_rollup_scc_distribution_ranges.sql | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.15 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 183.33 | Adapter successfully persisted fixture data | Fixture: scc_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.24 | All 4 quality rules have implementation coverage | paths, ranges, ratios, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.34 | Adapter SccAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.39 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.19 | Tool 'scc' registered with adapter in TOOL_REGISTRY | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.27 | dbt staging model(s) found | stg_lz_scc_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.86 | dbt models present for tool | stg_lz_scc_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 11.05 | All entities have aligned repositories | SccFileMetric | - | - |
| `test.structure_naming` | pass | medium | 0.58 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 50.38 | Cross-tool SQL joins use correct patterns (293 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.92 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## semgrep

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/evaluation/results/output.json, WARNING: Output is 16 days old (threshold: 14 days) | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/evaluation/scorecard.md, WARNING: Output is 23 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 0.30 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/evaluation/llm/results/llm-eval-20260130-120000.json, WARNING: Output is 30 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.23 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 0.99 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/evaluation/results/output.json | - | - |
| `output.paths` | pass | high | 8.05 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.03 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.11 | Path consistency validated | Checked 65 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | semgrep, semgrep | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.43 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 176.60 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.30 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.14 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.09 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.14 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target output pattern acceptable | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.12 | evaluate target input path is valid | input: evaluation/results/output.json | - | - |
| `schema.draft` | pass | medium | 0.15 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.12 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.75 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.65 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.11 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.06 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.14 | LLM judge count meets minimum (5 >= 4) | rule_coverage.py, actionability.py, security_detection.py, smell_accuracy.py, false_positive_rate.py | - | - |
| `evaluation.synthetic_context` | pass | high | 18.53 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: security_detection.py, prompt: security_detection.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.11 | Ground truth files present | java.json, go.json, csharp.json, rust.json, javascript.json, typescript.json, python.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.09 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.06 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.30 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, analysis_path, combined | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.12 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.11 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.42 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_semgrep_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.28 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 161.55 | Adapter successfully persisted fixture data | Fixture: semgrep_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.60 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.34 | Adapter SemgrepAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.39 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.20 | Tool 'semgrep' registered with adapter in TOOL_REGISTRY | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.28 | dbt staging model(s) found | stg_semgrep_file_metrics.sql, stg_lz_semgrep_smells.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.95 | dbt models present for tool | stg_semgrep_file_metrics.sql, stg_lz_semgrep_smells.sql | - | - |
| `entity.repository_alignment` | pass | high | 11.49 | All entities have aligned repositories | SemgrepSmell | - | - |
| `test.structure_naming` | pass | medium | 0.56 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 50.14 | Cross-tool SQL joins use correct patterns (293 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 1.26 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## sonarqube

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/evaluation/results/output.json, WARNING: Output is 16 days old (threshold: 14 days) | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/evaluation/scorecard.md, WARNING: Output is 30 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 0.10 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/evaluation/llm/results/llm-eval-20260130-120000.json, WARNING: Output is 30 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.26 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 0.52 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/evaluation/results/output.json | - | - |
| `output.paths` | pass | high | 6.82 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.02 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.2.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | sonarqube, sonarqube | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.19 | Output schema_version matches schema constraint | 1.2.0 | - | - |
| `output.schema_validate` | pass | critical | 162.92 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.32 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.55 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.05 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.13 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.16 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target produces output.json | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.13 | evaluate target input path is valid | input: evaluation/results/output.json | - | - |
| `schema.draft` | pass | medium | 0.13 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.09 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.63 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.78 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.09 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.13 | LLM judge count meets minimum (4 >= 4) | issue_accuracy.py, integration_fit.py, actionability.py, coverage_completeness.py | - | - |
| `evaluation.synthetic_context` | pass | high | 10.28 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: issue_accuracy.py, prompt: issue_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.24 | Ground truth files present | java-security.json, typescript-duplication.json, csharp-baseline.json, python-mixed.json, csharp-complex.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.09 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.06 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.08 | LLM evaluation schema valid | timestamp, analysis_path, summary, dimensions, model, score, decision, programmatic_input, combined | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.07 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.06 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.45 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_sonarqube_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.23 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 251.82 | Adapter successfully persisted fixture data | Fixture: sonarqube_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.59 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.38 | Adapter SonarqubeAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.42 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.21 | Tool 'sonarqube' registered with adapter in TOOL_REGISTRY | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.27 | dbt staging model(s) found | stg_sonarqube_issues.sql, stg_sonarqube_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 1.00 | dbt models present for tool | stg_sonarqube_issues.sql, stg_sonarqube_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 11.04 | All entities have aligned repositories | SonarqubeIssue, SonarqubeMetric | - | - |
| `test.structure_naming` | pass | medium | 0.56 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 50.13 | Cross-tool SQL joins use correct patterns (293 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.94 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## symbol-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 0.00 | Pre-existing analysis output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/evaluation/results/output.json, WARNING: Output is 16 days old (threshold: 14 days) | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/evaluation/scorecard.md, WARNING: Output is 15 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 0.58 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/evaluation/results/llm_evaluation.json, WARNING: Output is 16 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.10 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 0.07 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/evaluation/results/output.json | - | - |
| `output.paths` | pass | high | 0.33 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.02 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | symbol-scanner, symbol-scanner | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.13 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 157.45 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.32 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.21 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.08 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.11 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | pass | high | 0.10 | evaluate target input path is valid | input: $(EVAL_OUTPUT_DIR)/output.json | - | - |
| `schema.draft` | pass | medium | 0.13 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.11 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.65 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.24 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.07 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.06 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.13 | LLM judge count meets minimum (4 >= 4) | call_relationship.py, import_completeness.py, integration.py, symbol_accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 6.74 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: call_relationship.py, prompt: call_relationship.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.18 | Ground truth files present | metaprogramming.json, csharp-tshock.json, cross-module-calls.json, deep-hierarchy.json, encoding-edge-cases.json, circular-imports.json, js-cross-module-calls.json, type-checking-imports.json, decorators-advanced.json, dynamic-code-generation.json, async-patterns.json, nested-structures.json, class-hierarchy.json, simple-functions.json, generators-comprehensions.json, dataclasses-protocols.json, ts-class-hierarchy.json, deep-nesting-stress.json, partial-syntax-errors.json, unresolved-externals.json, confusing-names.json, modern-syntax.json, large-file.json, js-simple-functions.json, web-framework-patterns.json, import-patterns.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.57 | Programmatic evaluation schema valid | timestamp, decision, score, checks, summary, aggregate, per_repo_results, metadata, regression | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.50 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.09 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.08 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.08 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.27 | Rollup Validation declared with valid tests | src/sot-engine/dbt/models/staging/stg_lz_code_symbols.sql | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.33 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 157.19 | Adapter successfully persisted fixture data | Fixture: symbol_scanner_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.65 | All 3 quality rules have implementation coverage | paths, ranges, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.40 | Adapter SymbolScannerAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.50 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.41 | Tool 'symbol-scanner' registered with adapter in TOOL_REGISTRY | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.32 | dbt staging model(s) found | stg_symbol_calls_file_metrics.sql, stg_symbols_file_metrics.sql, stg_symbol_coupling_metrics.sql, stg_lz_symbol_calls.sql, stg_lz_code_symbols.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.37 | dbt models present for tool | stg_symbol_calls_file_metrics.sql, stg_symbols_file_metrics.sql, stg_symbol_coupling_metrics.sql, stg_lz_symbol_calls.sql, stg_lz_code_symbols.sql | - | - |
| `entity.repository_alignment` | pass | high | 11.24 | All entities have aligned repositories | CodeSymbol, SymbolCall, FileImport | - | - |
| `test.structure_naming` | pass | medium | 0.52 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 50.84 | Cross-tool SQL joins use correct patterns (293 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.97 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## trivy

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | skip | critical | 0.00 | No analysis output found - run with --run-analysis or execute 'make analyze' | - | - | - |
| `run.evaluate` | pass | high | 0.00 | Pre-existing evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/evaluation/scorecard.md, WARNING: Output is 31 days old (threshold: 14 days) | - | - |
| `evaluation.quality` | pass | high | 0.27 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 0.00 | Pre-existing LLM evaluation output found (stale) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/evaluation/llm/results/synthetic-llm-eval.json, WARNING: Output is 29 days old (threshold: 14 days) | - | - |
| `evaluation.llm_quality` | pass | medium | 0.24 | LLM evaluation score meets threshold | score=4.0 | - | - |
| `output.load` | skip | high | 0.17 | No output.json available | No output.json found | - | - |
| `structure.paths` | pass | high | 0.19 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.27 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.05 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `make.evaluate_input_valid` | skip | high | 0.07 | No --results-dir/--analysis-dir/--analysis argument found in evaluate target | - | - | - |
| `schema.draft` | pass | medium | 0.12 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.10 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.46 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.24 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.09 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.12 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.09 | LLM judge count meets minimum (7 >= 4) | freshness_quality.py, vulnerability_detection.py, vulnerability_accuracy.py, severity_accuracy.py, iac_quality.py, sbom_completeness.py, false_positive_rate.py | - | - |
| `evaluation.synthetic_context` | pass | high | 13.24 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: vulnerability_accuracy.py, prompt: vulnerability_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.10 | Ground truth files present | dotnet-outdated.json, js-fullstack.json, vulnerable-npm.json, iac-terraform.json, no-vulnerabilities.json, iac-misconfigs.json, mixed-severity.json, java-outdated.json, critical-cves.json, outdated-deps.json, cfn-misconfigs.json, k8s-misconfigs.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.01 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.25 | Programmatic evaluation schema valid | timestamp, tool, version, decision, score, classification, overall_score, summary, checks, dimensions | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.22 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.13 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.11 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.09 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.22 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_trivy_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.25 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 299.47 | Adapter successfully persisted fixture data | Fixture: trivy_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.57 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.29 | Adapter TrivyAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.37 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.19 | Tool 'trivy' registered with adapter in TOOL_REGISTRY | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.27 | dbt staging model(s) found | stg_trivy_file_metrics.sql, stg_trivy_iac_misconfigs.sql, stg_trivy_vulnerabilities.sql, stg_trivy_target_metrics.sql, stg_trivy_targets.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.81 | dbt models present for tool | stg_trivy_file_metrics.sql, stg_trivy_iac_misconfigs.sql, stg_trivy_vulnerabilities.sql, stg_trivy_target_metrics.sql, stg_trivy_targets.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.36 | All entities have aligned repositories | TrivyVulnerability, TrivyTarget, TrivyIacMisconfig | - | - |
| `test.structure_naming` | pass | medium | 1.38 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 50.23 | Cross-tool SQL joins use correct patterns (293 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.71 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |
