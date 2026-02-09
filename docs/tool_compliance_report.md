# Tool Compliance Report

Generated: `2026-02-09T15:01:18.352258+00:00`

Summary: 7 passed, 11 failed, 18 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| coverage-ingest | fail | 49 | 2 | run.analyze, run.evaluate |
| dependensee | fail | 50 | 1 | run.evaluate |
| devskim | fail | 52 | 2 | evaluation.results, evaluation.llm_quality |
| dotcover | pass | 53 | 0 | - |
| git-blame-scanner | pass | 53 | 0 | - |
| git-fame | fail | 50 | 3 | evaluation.results, evaluation.quality, evaluation.llm_quality |
| git-sizer | fail | 52 | 1 | output.data_completeness |
| gitleaks | fail | 51 | 2 | evaluation.quality, evaluation.llm_quality |
| layout-scanner | pass | 53 | 0 | - |
| lizard | pass | 53 | 0 | - |
| pmd-cpd | fail | 49 | 2 | evaluation.results, run.evaluate_llm |
| roslyn-analyzers | pass | 53 | 0 | - |
| scancode | fail | 52 | 1 | evaluation.quality |
| scc | fail | 50 | 1 | run.evaluate |
| semgrep | pass | 53 | 0 | - |
| sonarqube | pass | 53 | 0 | - |
| symbol-scanner | fail | 50 | 1 | run.evaluate_llm |
| trivy | fail | 49 | 2 | evaluation.quality, run.evaluate_llm |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| sonarqube | `run.analyze` | 533123.49 |
| git-fame | `run.evaluate_llm` | 229562.60 |
| layout-scanner | `run.evaluate_llm` | 225801.66 |
| scc | `run.evaluate_llm` | 220045.30 |
| dotcover | `run.analyze` | 141757.07 |
| semgrep | `run.evaluate_llm` | 134740.24 |
| roslyn-analyzers | `run.evaluate_llm` | 128968.29 |
| dependensee | `run.evaluate_llm` | 88693.08 |
| devskim | `run.evaluate_llm` | 79656.03 |
| git-blame-scanner | `run.evaluate_llm` | 77168.85 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| sonarqube | 536.80 |
| git-fame | 231.31 |
| roslyn-analyzers | 229.96 |
| layout-scanner | 227.90 |
| scc | 222.41 |
| semgrep | 147.60 |
| dotcover | 142.74 |
| gitleaks | 131.48 |
| dependensee | 91.16 |
| devskim | 83.28 |
| git-sizer | 79.21 |
| git-blame-scanner | 78.21 |
| coverage-ingest | 71.88 |
| lizard | 62.77 |
| pmd-cpd | 35.91 |
| trivy | 35.33 |
| scancode | 24.98 |
| symbol-scanner | 11.47 |

## coverage-ingest

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | fail | critical | 99.06 | make analyze failed | Error: COVERAGE_FILE is required.
Usage: make analyze COVERAGE_FILE=/path/to/coverage.xml | Error: COVERAGE_FILE is required. Usage: make analyze COVERAGE_FILE=/path/to/coverage.xml | make[1]: *** [analyze] Error 1 |
| `run.evaluate` | fail | high | 158.85 | make evaluate failed | Running programmatic evaluation... | Running programmatic evaluation... | Traceback (most recent call last):   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/coverage-ingest/scripts/evaluate.py", line 20, in <module>     from parsers import (   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/coverage-ingest/scripts/parsers/__init__.py", line 6, in <module>     from .cobertura import CoberturaParser   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/coverage-ingest/scripts/parsers/cobertura.py", line 27, in <module>     import defusedxml.ElementTree as ET ModuleNotFoundError: No module named 'defusedxml' make[1]: *** [evaluate] Error 1 |
| `run.evaluate_llm` | pass | medium | 70854.01 | make evaluate-llm succeeded | - | Running LLM evaluation...  ====================================================================== COVERAGE-INGEST LLM EVALUATION REPORT ======================================================================  Timestamp: 2026-02-09T14:20:34.390113+00:00 Output Dir: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-qss_vfi5 Model:      opus-4.5  ---------------------------------------------------------------------- SUMMARY ----------------------------------------------------------------------   Weighted Score: 5.0/5.0   Grade:          A   Verdict:        STRONG_PASS  ---------------------------------------------------------------------- JUDGE RESULTS ----------------------------------------------------------------------    RISK_TIER_QUALITY (weight: 25%)     Score:      5/5 (w… | <frozen runpy>:128: RuntimeWarning: 'evaluation.llm.orchestrator' found in sys.modules after import of package 'evaluation.llm', but prior to execution of 'evaluation.llm.orchestrator'; this may result in unpredictable behaviour Running risk_tier_quality judge...   Score: 5/5 (weight: 25%) Running gap_actionability judge...   Score: 5/5 (weight: 25%) Running cross_format_consistency judge...   Score: 5/5 (weight: 25%) Running parser_accuracy judge...   Score: 5/5 (weight: 25%) |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 3.27 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 2.57 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/coverage-ingest/outputs/77D267E0-83B0-41FB-B5B1-E15DAC907D5A/output.json | - | - |
| `output.paths` | pass | high | 0.86 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.07 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.02 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.02 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.02 | Tool name matches data.tool | coverage-ingest, coverage-ingest | - | - |
| `output.metadata_consistency` | pass | medium | 0.09 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.62 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 272.96 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.68 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.80 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.05 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.28 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.16 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.15 | analyze target output pattern acceptable | - | - | - |
| `schema.draft` | pass | medium | 0.12 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.21 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.15 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.05 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.21 | LLM judge count meets minimum (4 >= 4) | cross_format_consistency.py, gap_actionability.py, parser_accuracy.py, risk_tier_quality.py | - | - |
| `evaluation.synthetic_context` | pass | high | 16.91 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: gap_actionability.py, prompt: gap_actionability.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.06 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.03 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.43 | Programmatic evaluation schema valid | timestamp, score, decision, summary, passed, total, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.11 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.06 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.48 | LLM evaluation schema valid | timestamp, output_dir, model, trace_id, judges, summary, programmatic_input, decision, score, dimensions | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.32 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.24 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.88 | Rollup Validation declared with valid tests | src/tools/coverage-ingest/tests/unit/test_lcov_parser.py, src/tools/coverage-ingest/tests/unit/test_jacoco_parser.py, src/tools/coverage-ingest/tests/integration/test_e2e.py | - | - |
| `adapter.compliance` | pass | info | 282.31 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.41 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 98.34 | Adapter successfully persisted fixture data | Fixture: coverage_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.87 | All 4 quality rules have implementation coverage | paths, ranges, coverage_invariants, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.32 | Adapter CoverageAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.26 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.50 | Tool 'coverage-ingest' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.23 | dbt staging model(s) found | stg_lz_coverage_summary.sql, stg_lz_dotcover_type_coverage.sql, stg_lz_dotcover_method_coverage.sql, stg_lz_dotcover_assembly_coverage.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.22 | dbt models present for tool | stg_lz_coverage_summary.sql, stg_lz_dotcover_type_coverage.sql, stg_lz_dotcover_method_coverage.sql, stg_lz_dotcover_assembly_coverage.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.04 | All entities have aligned repositories | CoverageSummary | - | - |
| `test.structure_naming` | pass | medium | 1.03 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 71.24 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.11 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## dependensee

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 1306.08 | make analyze succeeded | - | Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/eval-repos/synthetic as project 'synthetic' /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/eval-repos/synthetic \ 		--repo-name synthetic \ 		--output-dir /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-a22o2ano \ 		--run-id compliance \ 		--repo-id compliance \ 		--branch main \ 		--commit 2af2aa283d775c337e2bbdbca7434af3f6b264ef Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/eval-repos/synthetic Projects found: 4 Package dependencies: 9 Project references: 6 Circular dependencies: 0 Output: /var… | - |
| `run.evaluate` | fail | high | 628.15 | make evaluate failed | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate \
		--results-dir outputs/7a9c794e-4b86-4a18-820e-7b89459c9932/ \
		--ground-truth-dir evaluation/ground-truth \
		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-b82mle4e/evaluation_report.json
Evaluation complete. Decision: FAIL
Score: 93.8% (15/16 passed) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate \ 		--results-dir outputs/7a9c794e-4b86-4a18-820e-7b89459c9932/ \ 		--ground-truth-dir evaluation/ground-truth \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-b82mle4e/evaluation_report.json Evaluation complete. Decision: FAIL Score: 93.8% (15/16 passed) | make[1]: *** [evaluate] Error 1 |
| `run.evaluate_llm` | pass | medium | 88693.08 | make evaluate-llm succeeded | - | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator \ 		/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-a22o2ano \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-xtwoy7ou/llm_evaluation.json \ 		--model opus-4.5 LLM Evaluation for dependensee Model: opus-4.5 Working directory: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee Output directory: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-a22o2ano ============================================================  Running full evaluation (4 judges)... Registered 4 judges  Running project_detection evaluation...   Score: 4/5 (confidence: 0.82) Running dependency_accuracy evaluation...   Score:… | [DEBUG] Looking for analysis files in: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-a22o2ano   [DEBUG] Found 1 JSON files   [DEBUG] Loaded: output.json   [DEBUG] Looking for analysis files in: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-a22o2ano   [DEBUG] Found 1 JSON files   [DEBUG] Loaded: output.json   [DEBUG] Looking for analysis files in: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-a22o2ano   [DEBUG] Found 1 JSON files   [DEBUG] Loaded: output.json   [DEBUG] Looking for analysis files in: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-a22o2ano   [DEBUG] Found 1 JSON files   [DEBUG] Loaded: output.json   [DEBUG] Looking for analysis files in: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-… |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.55 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 0.33 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-a22o2ano/output.json | - | - |
| `output.paths` | pass | high | 0.61 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.12 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.03 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.03 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.03 | Tool name matches data.tool | dependensee, dependensee | - | - |
| `output.metadata_consistency` | pass | medium | 0.03 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.33 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 237.73 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.28 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.37 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.17 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.08 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.11 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.44 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.39 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.09 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.07 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.14 | LLM judge count meets minimum (4 >= 4) | project_detection.py, circular_detection.py, graph_quality.py, dependency_accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 11.29 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: dependency_accuracy.py, prompt: dependency_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.08 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.06 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.03 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.37 | Programmatic evaluation schema valid | timestamp, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.22 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.05 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.34 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.38 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.18 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.49 | Rollup Validation declared with valid tests | src/tools/dependensee/tests/unit/test_analyze.py | - | - |
| `adapter.compliance` | pass | info | 0.53 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.77 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 172.22 | Adapter successfully persisted fixture data | Fixture: dependensee_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.75 | All 2 quality rules have implementation coverage | paths, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 1.18 | Adapter DependenseeAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.48 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.83 | Tool 'dependensee' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.32 | dbt staging model(s) found | stg_dependensee_package_refs.sql, stg_dependensee_projects.sql, stg_dependensee_project_refs.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.55 | dbt models present for tool | stg_dependensee_package_refs.sql, stg_dependensee_projects.sql, stg_dependensee_project_refs.sql | - | - |
| `entity.repository_alignment` | pass | high | 12.70 | All entities have aligned repositories | DependenseeProject, DependenseeProjectReference, DependenseePackageReference | - | - |
| `test.structure_naming` | pass | medium | 0.52 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 82.53 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.47 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## devskim

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 2547.46 | make analyze succeeded | - | Checking DevSkim CLI installation... Setup complete! Analyzing synthetic... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/eval-repos/synthetic" \ 		--repo-name "synthetic" \ 		--output-dir "/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-gg_reful" \ 		--run-id "compliance" \ 		--repo-id "compliance" \ 		--branch "main" \ 		--commit "2af2aa283d775c337e2bbdbca7434af3f6b264ef" \ 		--custom-rules "rules/custom" Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/eval-repos/synthetic Files analyzed: 16 Issues found: 50 Duration: 1969ms Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compl… | devskim 1.0.70+d69541fde7 |
| `run.evaluate` | pass | high | 324.44 | make evaluate succeeded | - | Checking DevSkim CLI installation... Setup complete! Running programmatic evaluation...  [36m======================================================================[0m [36m[1m  DEVSKIM EVALUATION REPORT[0m [36m======================================================================[0m  [34m[1mSUMMARY[0m [34m----------------------------------------[0m   Total Checks:  30   Passed:        [32m30[0m   Failed:        [32m0[0m   Overall Score: [32m[1m95.5%[0m  [34m[1mSCORE BY CATEGORY[0m [34m----------------------------------------[0m   accuracy        [32m100.0%[0m  (8/8 passed)   coverage        [32m90.5%[0m  (8/8 passed)   edge_cases      [32m92.5%[0m  (8/8 passed)   integration_fit [32m100.0%[0m  (1/1 passed)   output_quality  [32m100.0%[0m  (1/1 passed)   per… | devskim 1.0.70+d69541fde7 |
| `evaluation.results` | fail | high | - | Missing evaluation outputs | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-ia3x5cwz/scorecard.md, /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-ia3x5cwz/checks.json | - | - |
| `evaluation.quality` | pass | high | 1.42 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 79656.03 | make evaluate-llm succeeded | - | Checking DevSkim CLI installation... Setup complete! Analyzing synthetic... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/eval-repos/synthetic" \ 		--repo-name "synthetic" \ 		--output-dir "/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-gg_reful" \ 		--run-id "compliance" \ 		--repo-id "compliance" \ 		--branch "main" \ 		--commit "2af2aa283d775c337e2bbdbca7434af3f6b264ef" \ 		--custom-rules "rules/custom" Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/eval-repos/synthetic Files analyzed: 16 Issues found: 50 Duration: 1799ms Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compl… | devskim 1.0.70+d69541fde7 <frozen runpy>:128: RuntimeWarning: 'evaluation.llm.orchestrator' found in sys.modules after import of package 'evaluation.llm', but prior to execution of 'evaluation.llm.orchestrator'; this may result in unpredictable behaviour |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | fail | medium | 0.00 | LLM evaluation JSON missing | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-703tmd_i/llm_evaluation.json | - | - |
| `output.load` | pass | high | 0.99 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-gg_reful/output.json | - | - |
| `output.paths` | pass | high | 2.03 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.15 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.07 | Path consistency validated | Checked 18 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.04 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.04 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.04 | Tool name matches data.tool | devskim, devskim | - | - |
| `output.metadata_consistency` | pass | medium | 0.07 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.83 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 355.93 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 1.14 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.65 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.13 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target output pattern acceptable | - | - | - |
| `schema.draft` | pass | medium | 0.17 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.11 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.84 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.51 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.12 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.03 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.15 | LLM judge count meets minimum (4 >= 4) | rule_coverage.py, severity_calibration.py, security_focus.py, detection_accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 16.54 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: detection_accuracy.py, prompt: detection_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 1.00 | Ground truth files present | api-security.json, deserialization.json, xxe.json, csharp.json, clean.json | - | - |
| `evaluation.scorecard` | pass | low | 0.06 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.05 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.46 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.15 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.09 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.23 | LLM evaluation schema valid | run_id, timestamp, model, score, decision, dimensions, total_score, average_confidence, combined_score, programmatic_input | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.25 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.20 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.69 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_devskim_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.09 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 5.99 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 253.88 | Adapter successfully persisted fixture data | Fixture: devskim_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.46 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.69 | Adapter DevskimAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 1.28 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.97 | Tool 'devskim' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.79 | dbt staging model(s) found | stg_lz_devskim_findings.sql, stg_devskim_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.75 | dbt models present for tool | stg_lz_devskim_findings.sql, stg_devskim_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 13.45 | All entities have aligned repositories | DevskimFinding | - | - |
| `test.structure_naming` | pass | medium | 0.62 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 84.35 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | pass | high | 1.80 | Test coverage 80.7% >= 80% threshold | coverage=80.7%, threshold=80% | - | - |

## dotcover

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 141757.07 | make analyze succeeded | - | Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/eval-repos/synthetic as project 'synthetic' /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/eval-repos/synthetic \ 		--repo-name synthetic \ 		--output-dir /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-4lvo49ul \ 		--run-id compliance \ 		--repo-id compliance \ 		--branch main \ 		--commit 2af2aa283d775c337e2bbdbca7434af3f6b264ef Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/eval-repos/synthetic Found test project: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/eval-repos/s… | - |
| `run.evaluate` | pass | high | 152.62 | make evaluate succeeded | - | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate \ 		--results-dir outputs/dotcover-test-run \ 		--ground-truth-dir evaluation/ground-truth \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-g0638xhb/evaluation_report.json Scorecard JSON saved to: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/evaluation/scorecard.json Scorecard Markdown saved to: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/evaluation/scorecard.md Evaluation complete. Decision: PASS Score: 100.0% (19/19 passed) Results saved to /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-g0638xhb/evaluation_report.json | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | pass | high | 0.74 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 106.69 | make evaluate-llm succeeded | - | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator \ 		/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-4lvo49ul \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-kptek4re/llm_evaluation.json \ 		--model opus-4.5 \ 		--programmatic-results evaluation/results/evaluation_report.json LLM evaluation complete. Verdict: PASS Results saved to /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-kptek4re/llm_evaluation.json | - |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.22 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 0.09 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-4lvo49ul/output.json | - | - |
| `output.paths` | pass | high | 0.17 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.06 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.03 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.03 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.03 | Tool name matches data.tool | dotcover, dotcover | - | - |
| `output.metadata_consistency` | pass | medium | 0.03 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.50 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 260.95 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.61 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.62 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.06 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.15 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.13 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.82 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.31 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.07 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.08 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.17 | LLM judge count meets minimum (4 >= 4) | false_positive.py, actionability.py, integration.py, accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 14.39 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: accuracy.py, prompt: accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.07 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.09 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.06 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.06 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.05 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.04 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.42 | Rollup Validation declared with valid tests | src/tools/dotcover/tests/unit/test_analyze.py | - | - |
| `adapter.compliance` | pass | info | 0.08 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 4.20 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 294.82 | Adapter successfully persisted fixture data | Fixture: dotcover_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.82 | All 3 quality rules have implementation coverage | coverage_bounds, statement_invariants, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 3.63 | Adapter DotcoverAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.91 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.84 | Tool 'dotcover' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.31 | dbt staging model(s) found | stg_dotcover_file_metrics.sql, stg_lz_dotcover_type_coverage.sql, stg_lz_dotcover_method_coverage.sql, stg_lz_dotcover_assembly_coverage.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.24 | dbt models present for tool | stg_dotcover_file_metrics.sql, stg_lz_dotcover_type_coverage.sql, stg_lz_dotcover_method_coverage.sql, stg_lz_dotcover_assembly_coverage.sql | - | - |
| `entity.repository_alignment` | pass | high | 25.58 | All entities have aligned repositories | DotcoverAssemblyCoverage, DotcoverTypeCoverage, DotcoverMethodCoverage | - | - |
| `test.structure_naming` | pass | medium | 0.65 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 111.27 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.64 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## git-blame-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 399.09 | make analyze succeeded | - | Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-blame-scanner/eval-repos/synthetic as project 'synthetic' /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-blame-scanner/eval-repos/synthetic \ 		--repo-name synthetic \ 		--output-dir /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-vyb1k8q8 \ 		--run-id compliance \ 		--repo-id compliance \ 		--branch main \ 		--commit 9dacf07c0b319271c7f1860327c54917b1d55586 ============================================================ git-blame-scanner - Per-file Authorship Analysis ============================================================ Repository: /Users/alexander.st… | - |
| `run.evaluate` | pass | high | 87.16 | make evaluate succeeded | - | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate \ 		--results-dir /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-vyb1k8q8 \ 		--ground-truth-dir evaluation/ground-truth \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-4y1v2abt/evaluation_report.json Evaluation complete. Decision: PASS Score: 100.0% (17/17 passed) Results saved to /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-4y1v2abt/evaluation_report.json | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | pass | high | 0.17 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | pass | medium | 77168.85 | make evaluate-llm succeeded | - | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator \ 		/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-vyb1k8q8 \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-w74_xvm0/llm_evaluation.json \ 		--model opus-4.5  ====================================================================== GIT-BLAME-SCANNER LLM EVALUATION REPORT ======================================================================  Timestamp: 2026-02-09T14:27:03.485866+00:00 Output Dir: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-vyb1k8q8 Model:      opus-4.5  ---------------------------------------------------------------------- SUMMARY -------------------------------------------------------------------… | Running ownership_accuracy judge...   Score: 5/5 (weight: 30%) Running churn_validity judge...   Score: 5/5 (weight: 25%) Running actionability judge...   Score: 2/5 (weight: 25%) Running integration judge...   Score: 5/5 (weight: 20%) |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.80 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 0.46 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-vyb1k8q8/output.json | - | - |
| `output.paths` | pass | high | 0.29 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.08 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.05 | Path consistency validated | Checked 2 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.02 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.02 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.02 | Tool name matches data.tool | git-blame-scanner, git-blame-scanner | - | - |
| `output.metadata_consistency` | pass | medium | 0.03 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.37 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 220.16 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.34 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.39 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.25 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.19 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.25 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.11 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.38 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.28 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.03 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.16 | LLM judge count meets minimum (5 >= 4) | ownership_accuracy.py, actionability.py, integration.py, churn_validity.py, utils.py | - | - |
| `evaluation.synthetic_context` | pass | high | 20.09 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: ownership_accuracy.py, prompt: ownership_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.06 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.31 | Programmatic evaluation schema valid | timestamp, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.10 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.48 | LLM evaluation schema valid | timestamp, output_dir, model, trace_id, judges, summary, programmatic_input, decision, score, dimensions | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.12 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-blame-scanner/evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.10 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.31 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_git_blame_direct_vs_recursive.sql, src/tools/git-blame-scanner/tests/unit/test_analyze.py | - | - |
| `adapter.compliance` | pass | info | 0.08 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 4.40 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 195.04 | Adapter successfully persisted fixture data | Fixture: git_blame_scanner_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.54 | All 4 quality rules have implementation coverage | paths, ownership_valid, churn_monotonic, authors_positive | - | - |
| `sot.adapter_registered` | pass | medium | 1.99 | Adapter GitBlameScannerAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.34 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.62 | Tool 'git-blame-scanner' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.25 | dbt staging model(s) found | stg_git_blame_author_stats.sql, stg_git_blame_summary.sql | - | - |
| `dbt.model_coverage` | pass | high | 1.61 | dbt models present for tool | stg_git_blame_author_stats.sql, stg_git_blame_summary.sql | - | - |
| `entity.repository_alignment` | pass | high | 18.35 | All entities have aligned repositories | GitBlameFileSummary, GitBlameAuthorStats | - | - |
| `test.structure_naming` | pass | medium | 0.27 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 86.83 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.51 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## git-fame

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 487.35 | make analyze succeeded | - | Running authorship analysis on synthetic... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python scripts/analyze.py /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/eval-repos/synthetic --output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-n8pqgx1o/output.json ============================================================ git-fame Authorship Analysis ============================================================ Found 5 repositories to analyze  Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/eval-repos/synthetic/balanced... git-fame error: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python: No module named gitfame    No output from git-fame  Analyzing /Users/… | - |
| `run.evaluate` | pass | high | 576.17 | make evaluate succeeded | - | Running programmatic evaluation... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python scripts/evaluate.py --output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-50_pdz5b/evaluation_report.json ============================================================ git-fame Programmatic Evaluation ============================================================  Using output directory: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/outputs/943ade1f-b105-4154-9fab-f8afe3be7bbb Running evaluation checks...  1. Output Quality checks...    Score: 5.0/5.0 (6/6 passed) 2. Authorship Accuracy checks...    Score: 5.0/5.0 (8/8 passed) 3. Reliability checks...    Score: 2.5/5.0 (2/4 passed) 4. Performance checks...    Score: 3.75/5.0 (3… | - |
| `evaluation.results` | fail | high | - | Missing evaluation outputs | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-50_pdz5b/scorecard.md | - | - |
| `evaluation.quality` | fail | high | 0.33 | Evaluation decision below required threshold | MARGINAL_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 229562.60 | make evaluate-llm succeeded | - | Running LLM-as-a-Judge evaluation... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator --model opus-4.5 --output evaluation/results/llm_evaluation.json LLM Evaluation for git-fame Model: opus-4.5 Working directory: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame Output directory: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/outputs ============================================================  Running full evaluation (6 judges)... Registered 6 judges  Running authorship_quality evaluation...   Score: 3/5 (confidence: 0.72) Running bus_factor_accuracy evaluation...   Score: 4/5 (confidence: 0.92) Running concentration_metrics evaluation...   Score: 5/5 (confidence: 0.95) Ru… | <frozen runpy>:128: RuntimeWarning: 'evaluation.llm.orchestrator' found in sys.modules after import of package 'evaluation.llm', but prior to execution of 'evaluation.llm.orchestrator'; this may result in unpredictable behaviour |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | fail | medium | 0.00 | LLM evaluation JSON missing | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-76ffgj2b/llm_evaluation.json | - | - |
| `output.load` | pass | high | 0.78 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/outputs/943ade1f-b105-4154-9fab-f8afe3be7bbb/output.json | - | - |
| `output.paths` | pass | high | 0.48 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.24 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.02 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.06 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.06 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.06 | Tool name matches data.tool | git-fame, git-fame | - | - |
| `output.metadata_consistency` | pass | medium | 0.04 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.57 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 327.98 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.30 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.51 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.07 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.18 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.11 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target produces output.json | - | - | - |
| `schema.draft` | pass | medium | 0.15 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.86 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.49 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.13 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.11 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.61 | LLM judge count meets minimum (7 >= 4) | integration_readiness.py, concentration_metrics.py, evidence_quality.py, authorship_quality.py, utils.py, bus_factor_accuracy.py, output_completeness.py | - | - |
| `evaluation.synthetic_context` | pass | high | 17.16 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: authorship_quality.py, prompt: authorship_quality.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.24 | Ground truth files present | synthetic.json, multi-author.json, bus-factor-1.json, balanced.json, multi-branch.json, single-author.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.07 | Programmatic evaluation schema valid | timestamp, tool, version, overall_score, classification, summary, dimensions | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.06 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.10 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.08 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.07 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.35 | Rollup Validation declared with valid tests | src/tools/git-fame/tests/scripts/test_analyze.py, src/tools/git-fame/tests/scripts/test_authorship_accuracy_checks.py, src/tools/git-fame/tests/scripts/test_output_quality_checks.py, src/tools/git-fame/tests/scripts/test_reliability_checks.py | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.45 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 224.43 | Adapter successfully persisted fixture data | Fixture: git_fame_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.99 | All 3 quality rules have implementation coverage | hhi_valid, ownership_sums_100, bus_factor_valid | - | - |
| `sot.adapter_registered` | pass | medium | 0.82 | Adapter GitFameAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.34 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.53 | Tool 'git-fame' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.84 | dbt staging model(s) found | stg_lz_git_fame_authors.sql, stg_lz_git_fame_summary.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.22 | dbt models present for tool | stg_lz_git_fame_authors.sql, stg_lz_git_fame_summary.sql | - | - |
| `entity.repository_alignment` | pass | high | 16.50 | All entities have aligned repositories | GitFameAuthor, GitFameSummary | - | - |
| `test.structure_naming` | pass | medium | 0.52 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 83.15 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.54 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## git-sizer

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 2347.79 | make analyze succeeded | - | Running repository analysis...   REPO_PATH: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/eval-repos/synthetic   RUN_ID:    compliance   REPO_ID:   compliance   BRANCH:    main   COMMIT:    e73ab0a9b5506051281d1a7497abbf9743728566 Found 5 git repositories under /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/eval-repos/synthetic Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/eval-repos/synthetic/bloated Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-n_6yscy2/bloated/output.json Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/eval-repos/synthetic/deep-history Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/too… | - |
| `run.evaluate` | pass | high | 188.15 | make evaluate succeeded | - | Running programmatic evaluation...  ====================================================================== GIT-SIZER EVALUATION REPORT ======================================================================  Timestamp: 2026-02-09T15:32:14.760675 Analysis:  /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-n_6yscy2  ---------------------------------------------------------------------- OVERALL SUMMARY ----------------------------------------------------------------------   Total Checks: 28   Passed:       28 (100.0%)   Failed:       0 (0.0%)   Overall Score: 1.00/1.00   Decision:      STRONG_PASS  ---------------------------------------------------------------------- CATEGORY BREAKDOWN ----------------------------------------------------------------------   ACCURACY         8/… | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | pass | high | 0.89 | Evaluation score meets threshold (computed) | score=1.0, failed=0, total=28 | - | - |
| `run.evaluate_llm` | pass | medium | 75937.27 | make evaluate-llm succeeded | - | Running LLM evaluation...  ====================================================================== GIT-SIZER LLM EVALUATION REPORT ======================================================================  Timestamp: 2026-02-09T14:32:15.110301+00:00 Analysis:  /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-n_6yscy2 Model:     opus-4.5  ---------------------------------------------------------------------- SUMMARY ----------------------------------------------------------------------   Weighted Score: 4.55/5.0   Grade:          A   Verdict:        STRONG_PASS  ---------------------------------------------------------------------- JUDGE RESULTS ----------------------------------------------------------------------    SIZE_ACCURACY (weight: 35%)     Score:      5/5 (weighted: 1.… | Running size_accuracy judge...   Score: 5/5 (weight: 35%) Running threshold_quality judge...   Score: 4/5 (weight: 25%) Running actionability judge...   Score: 4/5 (weight: 20%) Running integration_fit judge...   Score: 5/5 (weight: 20%) |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.85 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 0.57 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-n_6yscy2/output.json | - | - |
| `output.paths` | pass | high | 0.42 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | fail | high | 0.11 | Data completeness issues detected | violations[0] missing required field: file_path, violations[0] missing required field: rule_id | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.03 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.03 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.03 | Tool name matches data.tool | git-sizer, git-sizer | - | - |
| `output.metadata_consistency` | pass | medium | 0.04 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.77 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 312.51 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.59 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.82 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.05 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.16 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.11 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.14 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.47 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.36 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.10 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.09 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.47 | LLM judge count meets minimum (4 >= 4) | integration_fit.py, size_accuracy.py, actionability.py, threshold_quality.py | - | - |
| `evaluation.synthetic_context` | pass | high | 13.31 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: size_accuracy.py, prompt: size_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.38 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.44 | Programmatic evaluation schema valid | timestamp, decision, score, analysis_path, ground_truth_dir, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.10 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.15 | LLM evaluation schema valid | timestamp, analysis_path, model, trace_id, judges, summary, programmatic_input, decision, score, dimensions | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.31 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.26 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.91 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_git_sizer_repo_level_only.sql | - | - |
| `adapter.compliance` | pass | info | 0.40 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 7.01 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 261.71 | Adapter successfully persisted fixture data | Fixture: git_sizer_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.95 | All 3 quality rules have implementation coverage | health_grade_valid, metrics_non_negative, violation_levels | - | - |
| `sot.adapter_registered` | pass | medium | 1.04 | Adapter GitSizerAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.93 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.88 | Tool 'git-sizer' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 1.03 | dbt staging model(s) found | stg_lz_git_sizer_metrics.sql, stg_lz_git_sizer_violations.sql, stg_lz_git_sizer_lfs_candidates.sql, stg_git_sizer_lfs_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.38 | dbt models present for tool | stg_lz_git_sizer_metrics.sql, stg_lz_git_sizer_violations.sql, stg_lz_git_sizer_lfs_candidates.sql, stg_git_sizer_lfs_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 13.99 | All entities have aligned repositories | GitSizerMetric, GitSizerViolation, GitSizerLfsCandidate | - | - |
| `test.structure_naming` | pass | medium | 0.98 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 109.95 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.54 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## gitleaks

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 58363.22 | make analyze succeeded | - | Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/eval-repos/synthetic as project 'synthetic' /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/eval-repos/synthetic \ 		--repo-name synthetic \ 		--output-dir /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-kbin699v \ 		--run-id compliance \ 		--repo-id compliance \ 		--branch main \ 		--commit e73ab0a9b5506051281d1a7497abbf9743728566 Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/eval-repos/synthetic Using gitleaks: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/bin/gitleaks Git… | - |
| `run.evaluate` | pass | high | 202.41 | make evaluate succeeded | - | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate \ 		--analysis-dir outputs/runs \ 		--ground-truth-dir evaluation/ground-truth \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-scugzg0s Gitleaks PoC Evaluation ============================================================ No analysis files found in outputs/runs Results saved to /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-scugzg0s/evaluation_report.json | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | fail | high | 0.00 | Evaluation results JSON missing | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-scugzg0s/checks.json, /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-scugzg0s/evaluation_report.json, /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-scugzg0s/llm_evaluation.json | - | - |
| `run.evaluate_llm` | pass | medium | 72167.08 | make evaluate-llm succeeded | - | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator \ 		--working-dir . \ 		--programmatic-results evaluation/results/evaluation_report.json \ 		--model opus-4.5 \ 		--evaluation-mode synthetic LLM Evaluation for poc-gitleaks Model: opus-4.5 Working directory: . Evaluation mode: synthetic ============================================================  Running 4 judges...  Running detection_accuracy evaluation...   Score: 3/5 (confidence: 0.50) Running false_positive evaluation...   Score: 3/5 (confidence: 0.50) Running secret_coverage evaluation...   Score: 1/5 (confidence: 0.95) Running severity_classification evaluation...   Score: 1/5 (confidence: 0.97)  ============================================================ RESULTS ============… | <frozen runpy>:128: RuntimeWarning: 'evaluation.llm.orchestrator' found in sys.modules after import of package 'evaluation.llm', but prior to execution of 'evaluation.llm.orchestrator'; this may result in unpredictable behaviour |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | fail | medium | 0.00 | LLM evaluation JSON missing | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-0l6mzsvm/llm_evaluation.json | - | - |
| `output.load` | pass | high | 1.39 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-kbin699v/output.json | - | - |
| `output.paths` | pass | high | 4.99 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.13 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.13 | Path consistency validated | Checked 98 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.04 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.04 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.04 | Tool name matches data.tool | gitleaks, gitleaks | - | - |
| `output.metadata_consistency` | pass | medium | 0.12 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.67 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 418.52 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.69 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.73 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.06 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.18 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.14 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.74 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.82 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.10 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.09 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.18 | LLM judge count meets minimum (4 >= 4) | false_positive.py, secret_coverage.py, detection_accuracy.py, severity_classification.py | - | - |
| `evaluation.synthetic_context` | pass | high | 9.06 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: detection_accuracy.py, prompt: detection_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.18 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.62 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.28 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary, categories | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.07 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.25 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.08 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.06 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 1.93 | Rollup Validation declared with valid tests | src/tools/gitleaks/tests/unit/test_rollup_invariants.py, src/sot-engine/dbt/tests/test_rollup_gitleaks_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.26 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.84 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 188.17 | Adapter successfully persisted fixture data | Fixture: gitleaks_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.76 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.80 | Adapter GitleaksAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.33 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.92 | Tool 'gitleaks' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.97 | dbt staging model(s) found | stg_gitleaks_secrets.sql, stg_lz_gitleaks_secrets.sql | - | - |
| `dbt.model_coverage` | pass | high | 1.66 | dbt models present for tool | stg_gitleaks_secrets.sql, stg_lz_gitleaks_secrets.sql | - | - |
| `entity.repository_alignment` | pass | high | 17.62 | All entities have aligned repositories | GitleaksSecret | - | - |
| `test.structure_naming` | pass | medium | 0.84 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 87.32 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 1.29 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## layout-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 434.66 | make analyze succeeded | - | Setup complete! Scanning synthetic... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner/eval-repos/synthetic" \ 		--repo-name "synthetic" \ 		--output-dir "/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-5o79_v5z" \ 		--run-id "compliance" \ 		--repo-id "compliance" \ 		--branch "main" \ 		 \ 		--commit "e73ab0a9b5506051281d1a7497abbf9743728566" Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner/eval-repos/synthetic Files found: 143 Directories: 79 Scan duration: 35ms Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-5o79_v5z/output.json | - |
| `run.evaluate` | pass | high | 549.99 | make evaluate succeeded | - | Setup complete! EVAL_OUTPUT_DIR=/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-wiy4ln95 /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate Evaluating output.json...   Score: 4.75/5.0 - STRONG_PASS   Checks: 33/36 passed  Results saved to /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-wiy4ln95/evaluation_report.json Scorecard saved to /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-wiy4ln95/scorecard.md  Aggregate: 4.75/5.0 - STRONG_PASS | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | pass | high | 1.67 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 225801.66 | make evaluate-llm succeeded | - | Setup complete! /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator \ 		--working-dir /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner \ 		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-5o79_v5z/output.json \ 		--model opus-4.5 \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-_47lb3ht/llm_evaluation.json \ 		--programmatic-results evaluation/results/evaluation_report.json Running full evaluation (4 judges)... Running classification_reasoning evaluation...   Score: 3/5 (confidence: 0.82) Running directory_taxonomy evaluation...   Score: 3/5 (confidence: 0.50) Running hierarchy_consistency evaluation...   Score: 5/5 (confidence: 0.91) Runnin… | <frozen runpy>:128: RuntimeWarning: 'evaluation.llm.orchestrator' found in sys.modules after import of package 'evaluation.llm', but prior to execution of 'evaluation.llm.orchestrator'; this may result in unpredictable behaviour |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.50 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 4.74 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-5o79_v5z/output.json | - | - |
| `output.paths` | pass | high | 22.97 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.23 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.04 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.06 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.06 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.06 | Tool name matches data.tool | layout-scanner, layout-scanner | - | - |
| `output.metadata_consistency` | pass | medium | 0.07 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.84 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 558.40 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.54 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.62 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.05 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.17 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.10 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target output pattern acceptable | - | - | - |
| `schema.draft` | pass | medium | 0.25 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.18 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.71 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.83 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.18 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.06 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.18 | LLM judge count meets minimum (4 >= 4) | classification_reasoning.py, hierarchy_consistency.py, language_detection.py, directory_taxonomy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 10.55 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: classification_reasoning.py, prompt: classification_reasoning.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.14 | Ground truth files present | mixed-language.json, edge-cases.json, generated-code.json, config-heavy.json, vendor-heavy.json, small-clean.json, deep-nesting.json, mixed-types.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.03 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.81 | Programmatic evaluation schema valid | timestamp, decision, score, evaluated_count, average_score, summary, checks, repositories | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.71 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.13 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.09 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.07 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.41 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_layout_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.15 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.22 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 395.68 | Adapter successfully persisted fixture data | Fixture: layout_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.94 | All 3 quality rules have implementation coverage | paths, ranges, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 1.14 | Adapter LayoutAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.32 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.00 | layout-scanner handled specially as prerequisite tool | Layout is ingested before TOOL_INGESTION_CONFIGS loop | - | - |
| `sot.dbt_staging_model` | pass | high | 0.25 | dbt staging model(s) found | stg_lz_layout_files.sql, stg_lz_layout_directories.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.84 | dbt models present for tool | stg_lz_layout_files.sql, stg_lz_layout_directories.sql | - | - |
| `entity.repository_alignment` | pass | high | 16.54 | All entities have aligned repositories | LayoutFile, LayoutDirectory | - | - |
| `test.structure_naming` | pass | medium | 0.32 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 90.99 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.41 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## lizard

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 905.15 | make analyze succeeded | - | Running function analysis on synthetic... Lizard version: lizard 1.20.0  Analyzing synthetic...   Analyzing 63 files with 8 threads...  Files analyzed: 63 Functions found: 529 Total CCN: 1358 Avg CCN: 2.57 Max CCN: 26 Functions over threshold: 20 Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-rf9dj01f/output.json | - |
| `run.evaluate` | pass | high | 4709.93 | make evaluate succeeded | - | Running programmatic evaluation (76 checks)... Lizard version: lizard 1.20.0  Analyzing synthetic...   Analyzing 63 files with 8 threads...  Files analyzed: 63 Functions found: 529 Total CCN: 1358 Avg CCN: 2.57 Max CCN: 26 Functions over threshold: 20 Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-ptuq5yxx/output.json  ================================================================================   LIZARD EVALUATION REPORT ================================================================================    Timestamp: 2026-02-09T14:39:36.444690+00:00   Analysis:  /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-ptuq5yxx/output.json   Ground Truth: evaluation/ground-truth  -------------------------------------------------------------------… | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | pass | high | 2.81 | Evaluation score meets threshold (computed) | score=0.986, failed=0, total=None | - | - |
| `run.evaluate_llm` | pass | medium | 55859.34 | make evaluate-llm succeeded | - | Running LLM evaluation (4 judges)...  ============================================================ LLM Evaluation - Lizard Function Complexity Analysis ============================================================  Running ccn_accuracy evaluation...   Ground truth assertions failed: 1 failures   Score: 2/5 (confidence: 0.45) Running function_detection evaluation...   Ground truth assertions failed: 1 failures   Score: 1/5 (confidence: 0.95) Running statistics evaluation...   Ground truth assertions failed: 1 failures   Score: 1/5 (confidence: 0.95) Running hotspot_ranking evaluation...   Ground truth assertions failed: 1 failures   Score: 1/5 (confidence: 0.95)  ============================================================ EVALUATION SUMMARY ==================================================… | <frozen runpy>:128: RuntimeWarning: 'evaluation.llm.orchestrator' found in sys.modules after import of package 'evaluation.llm', but prior to execution of 'evaluation.llm.orchestrator'; this may result in unpredictable behaviour |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.64 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 12.06 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-ptuq5yxx/output.json | - | - |
| `output.paths` | pass | high | 27.67 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.84 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.48 | Path consistency validated | Checked 85 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.08 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.08 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.08 | Tool name matches data.tool | lizard, lizard | - | - |
| `output.metadata_consistency` | pass | medium | 0.29 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.99 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 468.21 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 1.20 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.51 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.20 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.11 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 1.45 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 2.96 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 2.18 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.84 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.10 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.07 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.17 | LLM judge count meets minimum (4 >= 4) | hotspot_ranking.py, ccn_accuracy.py, function_detection.py, statistics.py | - | - |
| `evaluation.synthetic_context` | pass | high | 32.07 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: ccn_accuracy.py, prompt: ccn_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.28 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.03 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 1.46 | Programmatic evaluation schema valid | timestamp, decision, score, analysis_path, ground_truth_path, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 2.55 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.32 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 1.61 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.39 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.27 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.92 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_lizard_direct_distribution_ranges.sql, src/sot-engine/dbt/tests/test_rollup_lizard_direct_vs_recursive.sql, src/sot-engine/dbt/tests/test_rollup_lizard_distribution_ranges.sql | - | - |
| `adapter.compliance` | pass | info | 0.09 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.62 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 410.23 | Adapter successfully persisted fixture data | Fixture: lizard_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.05 | All 3 quality rules have implementation coverage | paths, ranges, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.92 | Adapter LizardAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.36 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.48 | Tool 'lizard' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.27 | dbt staging model(s) found | stg_lz_lizard_file_metrics.sql, stg_lz_lizard_function_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.75 | dbt models present for tool | stg_lz_lizard_file_metrics.sql, stg_lz_lizard_function_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 17.70 | All entities have aligned repositories | LizardFileMetric, LizardFunctionMetric | - | - |
| `test.structure_naming` | pass | medium | 0.33 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 299.77 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.51 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## pmd-cpd

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 17913.20 | make analyze succeeded | - | Java found: /opt/homebrew/opt/openjdk@17/bin/java Running CPD analysis on synthetic... Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/eval-repos/synthetic... Analysis complete: 39 clones found Output written to: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-6pajzy2r/output.json Warnings: 1   - CPD error for rust: Invalid value for option '--language': Unknown language: rust Usage: pmd cpd [-Dh] [--ignore-annotations] [--ignore-identifiers]                [--ignore-literal-sequences] [--ignore-literals] | - |
| `run.evaluate` | pass | high | 351.64 | make evaluate succeeded | - | Running programmatic evaluation (~28 checks)... ====================================================================== PMD CPD EVALUATION REPORT ======================================================================  Analysis: outputs/cpd-test-run/output.json Ground Truth: evaluation/ground-truth Timestamp: 2026-02-09T15:40:51.883197  ---------------------------------------------------------------------- SUMMARY ---------------------------------------------------------------------- Total Checks: 28 Passed: 27 Failed: 1 Overall Score: 89.03%  Score by Category:   ACCURACY: 76.96% (8/8 passed)   COVERAGE: 100.00% (8/8 passed)   EDGE_CASES: 97.13% (8/8 passed)   PERFORMANCE: 75.00% (3/4 passed)  ---------------------------------------------------------------------- CHECK RESULTS -------------… | - |
| `evaluation.results` | fail | high | - | Missing evaluation outputs | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-n1sjp7nd/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.50 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | fail | medium | 16182.96 | make evaluate-llm failed | Java found: /opt/homebrew/opt/openjdk@17/bin/java
Running CPD analysis on synthetic...
Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/eval-repos/synthetic...
Analysis complete: 39 clones found
Output written to: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-6pajzy2r/output.json
Warnings: 1
  - CPD error for rust: Invalid value for option '--language': Unknown language: rust
Usage: pmd cpd [-Dh] [--ignore-annotations] [--ignore-identifiers]
               [--ignore-literal-sequences] [--ignore-literals]
       
Running LLM evaluation (4 judges)... | Java found: /opt/homebrew/opt/openjdk@17/bin/java Running CPD analysis on synthetic... Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/eval-repos/synthetic... Analysis complete: 39 clones found Output written to: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-6pajzy2r/output.json Warnings: 1   - CPD error for rust: Invalid value for option '--language': Unknown language: rust Usage: pmd cpd [-Dh] [--ignore-annotations] [--ignore-identifiers]                [--ignore-literal-sequences] [--ignore-literals]         Running LLM evaluation (4 judges)... | Traceback (most recent call last):   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/scripts/llm_evaluate.py", line 348, in <module>     main()   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/scripts/llm_evaluate.py", line 271, in main     report = run_llm_evaluation(              ^^^^^^^^^^^^^^^^^^^   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/scripts/llm_evaluate.py", line 93, in run_llm_evaluation     DuplicationAccuracyJudge( TypeError: BaseJudge.__init__() got an unexpected keyword argument 'analysis_path' make[1]: *** [evaluate-llm] Error 1 |
| `output.load` | pass | high | 1.59 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-6pajzy2r/output.json | - | - |
| `output.paths` | pass | high | 2.10 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.29 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.26 | Path consistency validated | Checked 49 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.07 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.07 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.07 | Tool name matches data.tool | pmd-cpd, pmd-cpd | - | - |
| `output.metadata_consistency` | pass | medium | 0.04 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.72 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 555.70 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 1.02 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.82 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.09 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 2.22 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 3.18 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 1.16 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 1.16 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.29 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 3.35 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 1.42 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.22 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.08 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 1.14 | LLM judge count meets minimum (4 >= 4) | duplication_accuracy.py, actionability.py, semantic_detection.py, cross_file_detection.py | - | - |
| `evaluation.synthetic_context` | pass | high | 15.13 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: duplication_accuracy.py, prompt: duplication_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.27 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | pass | low | 0.01 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.22 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.39 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.19 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.03 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.22 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, combined_score, notes | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.08 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=WEAK_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.05 | LLM evaluation passed | WEAK_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.37 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_pmd_cpd_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.09 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 4.14 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 730.74 | Adapter successfully persisted fixture data | Fixture: pmd_cpd_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 5.20 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 1.47 | Adapter PmdCpdAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.62 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.57 | Tool 'pmd-cpd' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.42 | dbt staging model(s) found | stg_lz_pmd_cpd_duplications.sql, stg_lz_pmd_cpd_occurrences.sql, stg_lz_pmd_cpd_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 1.20 | dbt models present for tool | stg_lz_pmd_cpd_duplications.sql, stg_lz_pmd_cpd_occurrences.sql, stg_lz_pmd_cpd_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 31.85 | All entities have aligned repositories | PmdCpdFileMetric, PmdCpdDuplication, PmdCpdOccurrence | - | - |
| `test.structure_naming` | pass | medium | 1.23 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 91.31 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.79 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## roslyn-analyzers

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 57184.45 | make analyze succeeded | - | Building external repo: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/eval-repos/synthetic... MSBUILD : error MSB1003: Specify a project or solution file. The current working directory does not contain a project or solution file. MSBUILD : error MSB1003: Specify a project or solution file. The current working directory does not contain a project or solution file. Build completed (some errors may be expected) Running Roslyn analysis... Found 5 project(s) ⠴ Building AsyncPatterns.csproj...   Found 150 violations ⠏ Building NullSafety.csproj...   Found 83 violations ⠴ Building ApiConventions.csproj...   Found 1 violations ⠙ Building SyntheticSmells.csproj...   Found 1051 violations ⠹ Building ResourceManagement.csproj...   Found 6 violations  ╭─────────… | - |
| `run.evaluate` | pass | high | 42574.51 | make evaluate succeeded | - | Building external repo: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/eval-repos/synthetic... MSBUILD : error MSB1003: Specify a project or solution file. The current working directory does not contain a project or solution file. MSBUILD : error MSB1003: Specify a project or solution file. The current working directory does not contain a project or solution file. Build completed (some errors may be expected) Running Roslyn analysis... Found 5 project(s) ⠇ Building AsyncPatterns.csproj...   Found 150 violations ⠏ Building NullSafety.csproj...   Found 83 violations ⠇ Building ApiConventions.csproj...   Found 1 violations ⠸ Building SyntheticSmells.csproj...   Found 1051 violations ⠴ Building ResourceManagement.csproj...   Found 6 violations  ╭─────────… | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | pass | high | 1.82 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 128968.29 | make evaluate-llm succeeded | - | Building external repo: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/eval-repos/synthetic... MSBUILD : error MSB1003: Specify a project or solution file. The current working directory does not contain a project or solution file. MSBUILD : error MSB1003: Specify a project or solution file. The current working directory does not contain a project or solution file. Build completed (some errors may be expected) Running Roslyn analysis... Found 5 project(s) ⠦ Building AsyncPatterns.csproj...   Found 150 violations ⠼ Building NullSafety.csproj...   Found 83 violations ⠦ Building ApiConventions.csproj...   Found 1 violations ⠦ Building SyntheticSmells.csproj...   Found 1051 violations ⠏ Building ResourceManagement.csproj...   Found 6 violations  ╭─────────… | - |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 5.82 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 20.80 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-g7xpb20t/output.json | - | - |
| `output.paths` | pass | high | 111.24 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 1.15 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.19 | Path consistency validated | Checked 62 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.08 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.08 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.08 | Tool name matches data.tool | roslyn-analyzers, roslyn-analyzers | - | - |
| `output.metadata_consistency` | pass | medium | 0.52 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 1.21 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 515.16 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 1.38 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.82 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.25 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.40 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.18 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.61 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.18 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.67 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 1.59 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.30 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.41 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.74 | LLM judge count meets minimum (5 >= 4) | overall_quality.py, integration_fit.py, resource_management.py, security_detection.py, design_analysis.py | - | - |
| `evaluation.synthetic_context` | pass | high | 46.82 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: security_detection.py, prompt: security_detection.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.55 | Ground truth files present | clean-code.json, resource-management.json, dead-code.json, csharp.json, security-issues.json, design-violations.json | - | - |
| `evaluation.scorecard` | pass | low | 0.08 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.06 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.40 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.11 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.14 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.09 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.08 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 1.07 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_roslyn_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.72 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 4.23 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 342.14 | Adapter successfully persisted fixture data | Fixture: roslyn_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.83 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 3.22 | Adapter RoslynAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 1.51 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.86 | Tool 'roslyn-analyzers' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 2.29 | dbt staging model(s) found | stg_lz_roslyn_violations.sql, stg_roslyn_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 2.63 | dbt models present for tool | stg_lz_roslyn_violations.sql, stg_roslyn_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 33.33 | All entities have aligned repositories | RoslynViolation | - | - |
| `test.structure_naming` | pass | medium | 1.17 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 123.65 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 1.16 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## scancode

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 716.00 | make analyze succeeded | - | Running license analysis on synthetic... Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/eval-repos/synthetic Licenses found: ['Apache-2.0', 'BSD-3-Clause', 'GPL-2.0-only WITH Classpath-exception-2.0', 'GPL-3.0-only', 'LGPL-2.1-only', 'MIT', 'Unlicense'] Overall risk: critical Files with licenses: 23 Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-ci1nnk0d/output.json | - |
| `run.evaluate` | pass | high | 535.42 | make evaluate succeeded | - | Running programmatic evaluation... License Analysis Evaluation ============================================================  no-license: 32/32 (PASS) apache-bsd: 32/32 (PASS) mit-only: 32/32 (PASS) apache-bsd: 32/32 (PASS) gpl-mixed: 32/32 (PASS) multi-license: 32/32 (PASS)  ============================================================ Summary ============================================================ Repositories evaluated: 6 Total checks: 192 Passed: 192 Failed: 0 Overall pass rate: 100.0%  Scorecard saved to: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/evaluation/scorecard.json Markdown scorecard saved to: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/evaluation/scorecard.md  Results saved to: evaluation/results/evaluati… | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | fail | high | 0.00 | Evaluation results JSON missing | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-_ubgjw6s/checks.json, /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-_ubgjw6s/evaluation_report.json, /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-_ubgjw6s/llm_evaluation.json | - | - |
| `run.evaluate_llm` | pass | medium | 21999.47 | make evaluate-llm succeeded | - | Running LLM-as-a-Judge evaluation... LLM Evaluation for scancode Model: opus-4.5 Working directory: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode ============================================================  Running 4 judges...  Running accuracy evaluation...   Score: 3/5 (confidence: 0.50) Running coverage evaluation...   Score: 3/5 (confidence: 0.50) Running actionability evaluation...   Score: 3/5 (confidence: 0.50) Running risk_classification evaluation...   Score: 3/5 (confidence: 0.50)  ============================================================ RESULTS ============================================================ Total Score: 3.00 Decision: WEAK_PASS  Results saved to: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/evalu… | - |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 13.48 | LLM evaluation decision meets threshold | WEAK_PASS | - | - |
| `output.load` | pass | high | 2.02 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-ci1nnk0d/output.json | - | - |
| `output.paths` | pass | high | 4.04 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 2.96 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.43 | Path consistency validated | Checked 23 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.71 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.71 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.71 | Tool name matches data.tool | scancode, scancode | - | - |
| `output.metadata_consistency` | pass | medium | 0.37 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 1.86 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 510.48 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.47 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.45 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 1.40 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.21 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.09 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.46 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.11 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.81 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.55 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.11 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.07 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.71 | LLM judge count meets minimum (4 >= 4) | coverage_judge.py, accuracy_judge.py, actionability_judge.py, risk_classification_judge.py | - | - |
| `evaluation.synthetic_context` | pass | high | 9.64 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: accuracy_judge.py, prompt: accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 1.80 | Ground truth files present | multi-license.json, mit-only.json, gpl-mixed.json, apache-bsd.json, public-domain.json, spdx-expression.json, no-license.json, dual-licensed.json | - | - |
| `evaluation.scorecard` | pass | low | 0.05 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.05 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 3.83 | Programmatic evaluation schema valid | timestamp, tool, version, decision, score, summary, checks, total_repositories, reports | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.89 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.17 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 2.51 | LLM evaluation schema valid | run_id, timestamp, model, dimensions, score, total_score, average_confidence, decision, programmatic_score, combined_score | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 4.61 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 1.96 | LLM evaluation passed | WEAK_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.31 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_scancode_repo_level_metrics.sql | - | - |
| `adapter.compliance` | pass | info | 1.64 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 4.28 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 907.75 | Adapter successfully persisted fixture data | Fixture: scancode_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 4.81 | All 3 quality rules have implementation coverage | paths, confidence, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 2.72 | Adapter ScancodeAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 1.86 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 3.39 | Tool 'scancode' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 3.13 | dbt staging model(s) found | stg_lz_scancode_summary.sql, stg_lz_scancode_file_licenses.sql, stg_scancode_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.91 | dbt models present for tool | stg_lz_scancode_summary.sql, stg_lz_scancode_file_licenses.sql, stg_scancode_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 75.84 | All entities have aligned repositories | ScancodeFileLicense, ScancodeSummary | - | - |
| `test.structure_naming` | pass | medium | 0.68 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 156.46 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.98 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## scc

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 760.03 | make analyze succeeded | - | Running directory analysis on synthetic... Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/eval-repos/synthetic Using scc: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/bin/scc Files found: 63 Total files: 63 Total lines: 7,666 Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-l4vwconc/output.json | - |
| `run.evaluate` | fail | high | 620.16 | make evaluate failed | Running programmatic evaluation... | Running programmatic evaluation... | Traceback (most recent call last):   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/scripts/evaluate.py", line 17, in <module>     from scripts.analyze import _resolve_commit ImportError: cannot import name '_resolve_commit' from 'scripts.analyze' (/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/scripts/analyze.py) make[1]: *** [evaluate] Error 1 |
| `run.evaluate_llm` | pass | medium | 220045.30 | make evaluate-llm succeeded | - | Running LLM-as-a-Judge evaluation... ============================================================ LLM-as-a-Judge Evaluation ============================================================ Mode: full Model: opus-4.5 Working Directory: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc ============================================================  Registering all judges (10 dimensions)...  Running code_quality evaluation...   Score: 4/5 (confidence: 0.85) Running integration_fit evaluation...   Score: 4/5 (confidence: 0.92) Running documentation evaluation...   Score: 4/5 (confidence: 0.82) Running edge_cases evaluation...   Score: 4/5 (confidence: 0.82) Running error_messages evaluation...   Score: 4/5 (confidence: 0.85) Running api_design evaluation...   Score: 4/5 (confi… | - |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 4.80 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 3.97 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-l4vwconc/output.json | - | - |
| `output.paths` | pass | high | 7.89 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.39 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.15 | Path consistency validated | Checked 94 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.03 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.03 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.03 | Tool name matches data.tool | scc, scc | - | - |
| `output.metadata_consistency` | pass | medium | 0.03 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.76 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 348.01 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.75 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.45 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.35 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.33 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.10 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.18 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.12 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.71 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.68 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.17 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.37 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.20 | LLM judge count meets minimum (10 >= 4) | error_messages.py, documentation.py, edge_cases.py, directory_analysis.py, integration_fit.py, code_quality.py, risk.py, statistics.py, comparative.py, api_design.py | - | - |
| `evaluation.synthetic_context` | pass | high | 22.19 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: directory_analysis.py, prompt: directory_analysis.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.27 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.03 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.30 | Programmatic evaluation schema valid | run_id, timestamp, dimensions, total_score, decision | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.53 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.03 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.35 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.17 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.11 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.39 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_scc_direct_distribution_ranges.sql, src/sot-engine/dbt/tests/test_rollup_scc_direct_vs_recursive.sql, src/sot-engine/dbt/tests/test_rollup_scc_distribution_ranges.sql | - | - |
| `adapter.compliance` | pass | info | 0.09 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.83 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 477.91 | Adapter successfully persisted fixture data | Fixture: scc_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.05 | All 4 quality rules have implementation coverage | paths, ranges, ratios, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.78 | Adapter SccAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.58 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.37 | Tool 'scc' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 1.20 | dbt staging model(s) found | stg_lz_scc_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 2.74 | dbt models present for tool | stg_lz_scc_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 19.81 | All entities have aligned repositories | SccFileMetric | - | - |
| `test.structure_naming` | pass | medium | 0.74 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 82.49 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.58 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## semgrep

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 11672.40 | make analyze succeeded | - | SKIP_SETUP=1: skipping semgrep install Initializing real repositories... Initializing Elttam audit rules...   Elttam rules already present Setup complete! Analyzing synthetic... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/eval-repos/synthetic" \ 		--repo-name "synthetic" \ 		--output-dir "/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-pi2inm88" \ 		--run-id "compliance" \ 		--repo-id "compliance" \ 		--branch "main" \ 		--commit "6ab266ad81d0bf4252dd5d45f3dfcf41424170ad" Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/eval-repos/synthetic Files analyzed: 58 Smells found: 193 Duration: 8596m… | - |
| `run.evaluate` | pass | high | 359.92 | make evaluate succeeded | - | SKIP_SETUP=1: skipping semgrep install Initializing real repositories... Initializing Elttam audit rules...   Elttam rules already present Setup complete! Running programmatic evaluation (~28 checks)... EVAL_OUTPUT_DIR=/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-__vutx79 /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate \ 		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-pi2inm88/output.json \ 		--ground-truth evaluation/ground-truth \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-__vutx79/evaluation_report.json  [36m======================================================================[0m [36m[1m  SEMGREP EVALUATION REPORT[0m [36m====================… | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | pass | high | 0.20 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 134740.24 | make evaluate-llm succeeded | - | SKIP_SETUP=1: skipping semgrep install Initializing real repositories... Initializing Elttam audit rules...   Elttam rules already present Setup complete! Analyzing synthetic... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/eval-repos/synthetic" \ 		--repo-name "synthetic" \ 		--output-dir "/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-pi2inm88" \ 		--run-id "compliance" \ 		--repo-id "compliance" \ 		--branch "main" \ 		--commit "6ab266ad81d0bf4252dd5d45f3dfcf41424170ad" Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/eval-repos/synthetic Files analyzed: 58 Smells found: 193 Duration: 7669m… | [DEBUG] Looking for analysis files in: outputs   [DEBUG] Found 18 JSON files   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Looking for analysis files in: outputs   [DEBUG] Found 18 JSON files   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Load… |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 1.03 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 4.15 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-pi2inm88/output.json | - | - |
| `output.paths` | pass | high | 12.83 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.79 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.63 | Path consistency validated | Checked 65 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.14 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.14 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.14 | Tool name matches data.tool | semgrep, semgrep | - | - |
| `output.metadata_consistency` | pass | medium | 0.25 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.92 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 345.21 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.78 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.35 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.15 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.13 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target output pattern acceptable | - | - | - |
| `schema.draft` | pass | medium | 0.16 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.11 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.74 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.84 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.32 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.07 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.17 | LLM judge count meets minimum (5 >= 4) | rule_coverage.py, actionability.py, security_detection.py, smell_accuracy.py, false_positive_rate.py | - | - |
| `evaluation.synthetic_context` | pass | high | 24.40 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: security_detection.py, prompt: security_detection.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.50 | Ground truth files present | java.json, go.json, csharp.json, rust.json, javascript.json, typescript.json, python.json | - | - |
| `evaluation.scorecard` | pass | low | 0.08 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.03 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.39 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.17 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.31 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, analysis_path, combined | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.14 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.12 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.60 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_semgrep_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.10 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.72 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 319.88 | Adapter successfully persisted fixture data | Fixture: semgrep_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.80 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 1.02 | Adapter SemgrepAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.33 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.57 | Tool 'semgrep' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.29 | dbt staging model(s) found | stg_semgrep_file_metrics.sql, stg_lz_semgrep_smells.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.82 | dbt models present for tool | stg_semgrep_file_metrics.sql, stg_lz_semgrep_smells.sql | - | - |
| `entity.repository_alignment` | pass | high | 16.23 | All entities have aligned repositories | SemgrepSmell | - | - |
| `test.structure_naming` | pass | medium | 0.72 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 82.28 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.52 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## sonarqube

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 533123.49 | make analyze succeeded | - | Analyzing synthetic... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/eval-repos/synthetic \ 		--project-key synthetic \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-4y6ui8uj/output.json \ 		--sonarqube-url http://localhost:9000 \ 		--run-id "compliance" \ 		--repo-id "compliance" \ 		--branch "main" \ 		--commit "6ab266ad81d0bf4252dd5d45f3dfcf41424170ad" \ 		 \ 		 \ 		 [2m2026-02-09T14:51:39.787812Z[0m [[32m[1minfo     [0m] [1mStarting SonarQube container  [0m [36mcompose_file[0m=[35m/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/docker-compose.yml[0m [2m2026-02-09T14:51:41.182349Z[0m [[3… | - |
| `run.evaluate` | pass | high | 634.21 | make evaluate succeeded | - | Running programmatic evaluation... EVAL_OUTPUT_DIR=/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-jmn0wjqu /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate \ 		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-4y6ui8uj/output.json \ 		--ground-truth evaluation/ground-truth \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-jmn0wjqu/evaluation_report.json [36m[1m Running programmatic evaluation...[0m  [35m======================================================================[0m [35m[1m  SONARQUBE EVALUATION REPORT[0m [35m======================================================================[0m  [34m[1mSUMMARY[0m [34m-----------------------------------… | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | pass | high | 8.97 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 1367.30 | make evaluate-llm succeeded | - | Running LLM evaluation (3 judges)... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.llm_evaluate \ 		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-4y6ui8uj/output.json \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-_uuyg770/llm_evaluation.json \ 		--model opus-4.5 \ 		--programmatic-results evaluation/results/evaluation_report.json [36m[1m Running LLM evaluation...[0m   Running issue_accuracy judge... [31m2/5[0m (conf: 80%)   Running coverage_completeness judge... [32m5/5[0m (conf: 85%)   Running actionability judge... [32m5/5[0m (conf: 75%)  [35m======================================================================[0m [35m[1m  SONARQUBE LLM EVALUATION REPORT[0m [35m====… | - |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 2.88 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 9.98 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-4y6ui8uj/output.json | - | - |
| `output.paths` | pass | high | 29.30 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.53 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.02 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.54 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.54 | Schema version is semver | 1.2.0 | - | - |
| `output.tool_name_match` | pass | low | 0.54 | Tool name matches data.tool | sonarqube, sonarqube | - | - |
| `output.metadata_consistency` | pass | medium | 0.21 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 4.31 | Output schema_version matches schema constraint | 1.2.0 | - | - |
| `output.schema_validate` | pass | critical | 734.96 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.69 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.91 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.06 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.79 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.98 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.39 | analyze target produces output.json | - | - | - |
| `schema.draft` | pass | medium | 0.48 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.15 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 1.14 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 1.36 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 1.23 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.15 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 1.31 | LLM judge count meets minimum (4 >= 4) | issue_accuracy.py, integration_fit.py, actionability.py, coverage_completeness.py | - | - |
| `evaluation.synthetic_context` | pass | high | 31.31 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: issue_accuracy.py, prompt: issue_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 1.07 | Ground truth files present | java-security.json, typescript-duplication.json, csharp-baseline.json, python-mixed.json, csharp-complex.json | - | - |
| `evaluation.scorecard` | pass | low | 0.04 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.04 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.15 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.62 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.04 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.20 | LLM evaluation schema valid | timestamp, analysis_path, summary, dimensions, model, score, decision, programmatic_input, combined | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.10 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.08 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 2.96 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_sonarqube_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 1.72 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 8.24 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 672.19 | Adapter successfully persisted fixture data | Fixture: sonarqube_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 5.56 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 1.29 | Adapter SonarqubeAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.54 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.66 | Tool 'sonarqube' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.41 | dbt staging model(s) found | stg_sonarqube_issues.sql, stg_sonarqube_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 2.31 | dbt models present for tool | stg_sonarqube_issues.sql, stg_sonarqube_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 37.01 | All entities have aligned repositories | SonarqubeIssue, SonarqubeMetric | - | - |
| `test.structure_naming` | pass | medium | 0.43 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 103.48 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.74 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## symbol-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 3810.44 | make analyze succeeded | - | Running symbol extraction on synthetic... Symbol Scanner v0.1.0  Analyzing synthetic... Repository: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/eval-repos/synthetic  Files analyzed: 25 Symbols found: 609   - Functions: 200   - Classes: 110   - Methods: 286   - Variables: 13 Calls found: 615   - Direct: 306   - Dynamic: 284   - Async: 25   - Resolved: 137     - Same file: 137     - Cross file: 0   - Unresolved: 478 Imports found: 63   - Static: 58   - Dynamic: 0 Errors: 1  Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-5klst0l3/output.json | - |
| `run.evaluate` | pass | high | 3775.69 | make evaluate succeeded | - | Running programmatic evaluation... Symbol Scanner v0.1.0  Analyzing synthetic... Repository: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/eval-repos/synthetic  Files analyzed: 25 Symbols found: 609   - Functions: 200   - Classes: 110   - Methods: 286   - Variables: 13 Calls found: 615   - Direct: 306   - Dynamic: 284   - Async: 25   - Resolved: 137     - Same file: 137     - Cross file: 0   - Unresolved: 478 Imports found: 63   - Static: 58   - Dynamic: 0 Errors: 1  Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-uudo3_ii/output.json Running evaluation in analysis mode... Ground truth: evaluation/ground-truth Repos dir: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/eval-repos/syntheti… | Warning: Repository csharp-tshock not found at /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/eval-repos/synthetic/csharp-tshock   Minor regression: 99.77% -> 99.07% (within threshold) |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | pass | high | 5.02 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | fail | medium | 1269.50 | make evaluate-llm failed | Running LLM evaluation (4 judges)... | Running LLM evaluation (4 judges)... | usage: orchestrator.py [-h] [--analysis ANALYSIS] [--output OUTPUT]                        [--model MODEL]                        [--programmatic-results PROGRAMMATIC_RESULTS]                        [--focused] orchestrator.py: error: unrecognized arguments: --working-dir . make[1]: *** [evaluate-llm] Error 2 |
| `output.load` | pass | high | 15.22 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-uudo3_ii/output.json | - | - |
| `output.paths` | pass | high | 66.53 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 1.66 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.94 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.06 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.06 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.06 | Tool name matches data.tool | symbol-scanner, symbol-scanner | - | - |
| `output.metadata_consistency` | pass | medium | 0.05 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 5.29 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 1288.83 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 1.07 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.55 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.48 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.31 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.17 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 1.87 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.52 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 3.48 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 6.72 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 2.35 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.21 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.34 | LLM judge count meets minimum (4 >= 4) | call_relationship.py, import_completeness.py, integration.py, symbol_accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 36.19 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: call_relationship.py, prompt: call_relationship.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.53 | Ground truth files present | metaprogramming.json, csharp-tshock.json, cross-module-calls.json, deep-hierarchy.json, encoding-edge-cases.json, circular-imports.json, type-checking-imports.json, decorators-advanced.json, dynamic-code-generation.json, async-patterns.json, nested-structures.json, class-hierarchy.json, simple-functions.json, generators-comprehensions.json, dataclasses-protocols.json, deep-nesting-stress.json, partial-syntax-errors.json, unresolved-externals.json, confusing-names.json, modern-syntax.json, large-file.json, web-framework-patterns.json, import-patterns.json | - | - |
| `evaluation.scorecard` | pass | low | 0.13 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 1.59 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 2.12 | Programmatic evaluation schema valid | timestamp, decision, score, checks, summary, aggregate, per_repo_results, metadata, regression | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.92 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.11 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.96 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.47 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.21 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.69 | Rollup Validation declared with valid tests | src/sot-engine/dbt/models/staging/stg_lz_code_symbols.sql | - | - |
| `adapter.compliance` | pass | info | 0.21 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 9.33 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 915.06 | Adapter successfully persisted fixture data | Fixture: symbol_scanner_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 6.99 | All 3 quality rules have implementation coverage | paths, ranges, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 4.64 | Adapter SymbolScannerAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 1.44 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 2.12 | Tool 'symbol-scanner' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 3.12 | dbt staging model(s) found | stg_symbol_calls_file_metrics.sql, stg_symbols_file_metrics.sql, stg_symbol_coupling_metrics.sql, stg_lz_symbol_calls.sql, stg_lz_code_symbols.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.77 | dbt models present for tool | stg_symbol_calls_file_metrics.sql, stg_symbols_file_metrics.sql, stg_symbol_coupling_metrics.sql, stg_lz_symbol_calls.sql, stg_lz_code_symbols.sql | - | - |
| `entity.repository_alignment` | pass | high | 62.77 | All entities have aligned repositories | CodeSymbol, SymbolCall, FileImport | - | - |
| `test.structure_naming` | pass | medium | 0.95 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 162.36 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 1.85 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## trivy

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 30387.90 | make analyze succeeded | - | Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/eval-repos/synthetic as project 'synthetic' /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/eval-repos/synthetic \ 		--repo-name synthetic \ 		--output-dir /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-r4ydylsm \ 		--run-id compliance \ 		--repo-id compliance \ 		--branch main \ 		--commit 6ab266ad81d0bf4252dd5d45f3dfcf41424170ad \ 		--timeout 600 [2m2026-02-09T15:00:44.244414Z[0m [[32m[1minfo     [0m] [1mStarting trivy analysis       [0m [36mrepo_name[0m=[35msynthetic[0m [36mrepo_path[0m=[35m/Users/alexander.stage/Projects/2026-01-24-Pro… | - |
| `run.evaluate` | pass | high | 1310.26 | make evaluate succeeded | - | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python scripts/evaluate.py --output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-niwjxoph/ Evaluated 0 files | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | fail | high | 7.45 | Evaluation decision missing | missing decision and summary score | - | - |
| `run.evaluate_llm` | fail | medium | 1408.33 | make evaluate-llm failed | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator \
		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-r4ydylsm/output.json \
		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-h53hazwq/llm_evaluation.json
Running vulnerability_accuracy evaluation...
  Ground truth assertions failed: 1 failures | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator \ 		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-r4ydylsm/output.json \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-h53hazwq/llm_evaluation.json Running vulnerability_accuracy evaluation...   Ground truth assertions failed: 1 failures | Traceback (most recent call last):   File "<frozen runpy>", line 198, in _run_module_as_main   File "<frozen runpy>", line 88, in _run_code   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/evaluation/llm/orchestrator.py", line 198, in <module>     main()   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/evaluation/llm/orchestrator.py", line 171, in main     result = evaluator.evaluate()              ^^^^^^^^^^^^^^^^^^^^   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/shared/evaluation/orchestrator.py", line 189, in evaluate     result = judge.evaluate()              ^^^^^^^^^^^^^^^^   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/evaluation/llm/judges/vulnerability_a… |
| `output.load` | pass | high | 23.85 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-r4ydylsm/output.json | - | - |
| `output.paths` | pass | high | 38.57 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.76 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.27 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.25 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.25 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.25 | Tool name matches data.tool | trivy, trivy | - | - |
| `output.metadata_consistency` | pass | medium | 0.04 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 1.04 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 742.61 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 2.84 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.97 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.09 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.56 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.26 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.15 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.53 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.38 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 2.77 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 3.93 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.21 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 3.35 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.58 | LLM judge count meets minimum (7 >= 4) | freshness_quality.py, vulnerability_detection.py, vulnerability_accuracy.py, severity_accuracy.py, iac_quality.py, sbom_completeness.py, false_positive_rate.py | - | - |
| `evaluation.synthetic_context` | pass | high | 97.19 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: vulnerability_accuracy.py, prompt: vulnerability_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.52 | Ground truth files present | dotnet-outdated.json, js-fullstack.json, vulnerable-npm.json, iac-terraform.json, no-vulnerabilities.json, iac-misconfigs.json, mixed-severity.json, java-outdated.json, critical-cves.json, outdated-deps.json, cfn-misconfigs.json, k8s-misconfigs.json | - | - |
| `evaluation.scorecard` | pass | low | 0.04 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.06 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 5.19 | Programmatic evaluation schema valid | timestamp, tool, version, decision, score, classification, overall_score, summary, checks, dimensions | - | - |
| `evaluation.programmatic_quality` | pass | high | 1.03 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.14 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 2.81 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.25 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.11 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.78 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_trivy_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 3.46 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 7.91 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 1051.98 | Adapter successfully persisted fixture data | Fixture: trivy_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 3.14 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 3.50 | Adapter TrivyAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 1.85 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 2.71 | Tool 'trivy' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.94 | dbt staging model(s) found | stg_trivy_file_metrics.sql, stg_trivy_iac_misconfigs.sql, stg_trivy_vulnerabilities.sql, stg_trivy_target_metrics.sql, stg_trivy_targets.sql | - | - |
| `dbt.model_coverage` | pass | high | 2.24 | dbt models present for tool | stg_trivy_file_metrics.sql, stg_trivy_iac_misconfigs.sql, stg_trivy_vulnerabilities.sql, stg_trivy_target_metrics.sql, stg_trivy_targets.sql | - | - |
| `entity.repository_alignment` | pass | high | 26.35 | All entities have aligned repositories | TrivyVulnerability, TrivyTarget, TrivyIacMisconfig | - | - |
| `test.structure_naming` | pass | medium | 0.48 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 174.95 | Cross-tool SQL joins use correct patterns (244 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.55 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |
