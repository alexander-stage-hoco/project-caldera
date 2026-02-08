# Tool Compliance Report

Generated: `2026-02-08T09:58:41.128978+00:00`

Summary: 4 passed, 12 failed, 16 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| dependensee | fail | 50 | 1 | run.evaluate |
| devskim | fail | 51 | 3 | evaluation.results, evaluation.quality, evaluation.llm_quality |
| dotcover | pass | 53 | 0 | - |
| git-fame | fail | 50 | 3 | evaluation.results, evaluation.quality, evaluation.llm_quality |
| git-sizer | fail | 52 | 1 | output.data_completeness |
| gitleaks | fail | 51 | 2 | evaluation.quality, evaluation.llm_quality |
| layout-scanner | pass | 53 | 0 | - |
| lizard | fail | 49 | 2 | run.analyze, run.evaluate |
| pmd-cpd | fail | 49 | 2 | evaluation.results, run.evaluate_llm |
| roslyn-analyzers | pass | 53 | 0 | - |
| scancode | fail | 52 | 1 | evaluation.quality |
| scc | fail | 50 | 1 | run.evaluate |
| semgrep | pass | 53 | 0 | - |
| sonarqube | fail | 46 | 3 | run.analyze, run.evaluate, run.evaluate_llm |
| symbol-scanner | fail | 50 | 1 | run.evaluate_llm |
| trivy | fail | 46 | 3 | run.analyze, run.evaluate, run.evaluate_llm |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| scc | `run.evaluate_llm` | 216803.16 |
| layout-scanner | `run.evaluate_llm` | 201345.91 |
| dotcover | `run.analyze` | 151199.11 |
| git-fame | `run.evaluate_llm` | 128181.08 |
| semgrep | `run.evaluate_llm` | 127442.07 |
| roslyn-analyzers | `run.evaluate_llm` | 99690.45 |
| dependensee | `run.evaluate_llm` | 82575.01 |
| devskim | `run.evaluate_llm` | 80959.22 |
| git-sizer | `run.evaluate_llm` | 76899.03 |
| gitleaks | `run.evaluate_llm` | 64768.72 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| scc | 217.69 |
| layout-scanner | 202.97 |
| dotcover | 152.55 |
| git-fame | 140.90 |
| semgrep | 136.53 |
| roslyn-analyzers | 133.89 |
| gitleaks | 97.19 |
| dependensee | 84.53 |
| devskim | 84.26 |
| git-sizer | 80.07 |
| lizard | 56.14 |
| pmd-cpd | 17.25 |
| scancode | 15.36 |
| symbol-scanner | 4.62 |
| sonarqube | 1.08 |
| trivy | 0.81 |

## dependensee

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 1162.16 | make analyze succeeded | - | Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/eval-repos/synthetic as project 'synthetic' /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/eval-repos/synthetic \ 		--repo-name synthetic \ 		--output-dir /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-pod_83yo \ 		--run-id compliance \ 		--repo-id compliance \ 		--branch main \ 		--commit 2f5bef575d66bab89d7bcb1221ac9bf0ab6b89d2 Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/eval-repos/synthetic Projects found: 4 Package dependencies: 9 Project references: 6 Circular dependencies: 0 Output: /var… | - |
| `run.evaluate` | fail | high | 129.34 | make evaluate failed | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate \
		--results-dir outputs/f23f9a48-fb85-4c81-8e04-da14641d23b3/ \
		--ground-truth-dir evaluation/ground-truth \
		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-12muqsb2/evaluation_report.json
Evaluation complete. Decision: FAIL
Score: 93.8% (15/16 passed) | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate \ 		--results-dir outputs/f23f9a48-fb85-4c81-8e04-da14641d23b3/ \ 		--ground-truth-dir evaluation/ground-truth \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-12muqsb2/evaluation_report.json Evaluation complete. Decision: FAIL Score: 93.8% (15/16 passed) | make[1]: *** [evaluate] Error 1 |
| `run.evaluate_llm` | pass | medium | 82575.01 | make evaluate-llm succeeded | - | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator \ 		/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-pod_83yo \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-pn80fg8s/llm_evaluation.json \ 		--model opus-4.5 LLM Evaluation for dependensee Model: opus-4.5 Working directory: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee Output directory: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-pod_83yo ============================================================  Running full evaluation (4 judges)... Registered 4 judges  Running project_detection evaluation...   Score: 4/5 (confidence: 0.82) Running dependency_accuracy evaluation...   Score:… | [DEBUG] Looking for analysis files in: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-pod_83yo   [DEBUG] Found 1 JSON files   [DEBUG] Loaded: output.json   [DEBUG] Looking for analysis files in: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-pod_83yo   [DEBUG] Found 1 JSON files   [DEBUG] Loaded: output.json   [DEBUG] Looking for analysis files in: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-pod_83yo   [DEBUG] Found 1 JSON files   [DEBUG] Loaded: output.json   [DEBUG] Looking for analysis files in: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-pod_83yo   [DEBUG] Found 1 JSON files   [DEBUG] Loaded: output.json   [DEBUG] Looking for analysis files in: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-… |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.85 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 0.58 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-pod_83yo/output.json | - | - |
| `output.paths` | pass | high | 1.40 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.09 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.03 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.03 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.03 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.03 | Tool name matches data.tool | dependensee, dependensee | - | - |
| `output.metadata_consistency` | pass | medium | 0.14 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.56 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 218.46 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.40 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.67 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.05 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.38 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.25 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.16 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.17 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.12 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.62 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.52 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.14 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.08 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.41 | LLM judge count meets minimum (4 >= 4) | project_detection.py, circular_detection.py, graph_quality.py, dependency_accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 12.89 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: dependency_accuracy.py, prompt: dependency_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.06 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.03 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.12 | Programmatic evaluation schema valid | timestamp, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.09 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.03 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.16 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.12 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dependensee/evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.10 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.31 | Rollup Validation declared with valid tests | src/tools/dependensee/tests/unit/test_analyze.py | - | - |
| `adapter.compliance` | pass | info | 227.83 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 4.20 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 97.67 | Adapter successfully persisted fixture data | Fixture: dependensee_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.35 | All 2 quality rules have implementation coverage | paths, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.76 | Adapter DependenseeAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.47 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.56 | Tool 'dependensee' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.40 | dbt staging model(s) found | stg_dependensee_package_refs.sql, stg_dependensee_projects.sql, stg_dependensee_project_refs.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.35 | dbt models present for tool | stg_dependensee_package_refs.sql, stg_dependensee_projects.sql, stg_dependensee_project_refs.sql | - | - |
| `entity.repository_alignment` | pass | high | 13.56 | All entities have aligned repositories | DependenseeProject, DependenseeProjectReference, DependenseePackageReference | - | - |
| `test.structure_naming` | pass | medium | 1.06 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 76.28 | Cross-tool SQL joins use correct patterns (200 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.45 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## devskim

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 2514.38 | make analyze succeeded | - | Checking DevSkim CLI installation... Setup complete! Analyzing synthetic... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/eval-repos/synthetic" \ 		--repo-name "synthetic" \ 		--output-dir "/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-hpq2_s_o" \ 		--run-id "compliance" \ 		--repo-id "compliance" \ 		--branch "main" \ 		--commit "2f5bef575d66bab89d7bcb1221ac9bf0ab6b89d2" \ 		--custom-rules "rules/custom" Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/eval-repos/synthetic Files analyzed: 16 Issues found: 50 Duration: 1899ms Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compl… | devskim 1.0.70+d69541fde7 |
| `run.evaluate` | pass | high | 282.91 | make evaluate succeeded | - | Checking DevSkim CLI installation... Setup complete! Running programmatic evaluation...  [36m======================================================================[0m [36m[1m  DEVSKIM EVALUATION REPORT[0m [36m======================================================================[0m  [34m[1mSUMMARY[0m [34m----------------------------------------[0m   Total Checks:  30   Passed:        [32m29[0m   Failed:        [31m1[0m   Overall Score: [32m[1m91.1%[0m  [34m[1mSCORE BY CATEGORY[0m [34m----------------------------------------[0m   accuracy        [32m100.0%[0m  (8/8 passed)   coverage        [32m93.0%[0m  (8/8 passed)   edge_cases      [32m80.0%[0m  (7/8 passed)   integration_fit [32m100.0%[0m  (1/1 passed)   output_quality  [32m100.0%[0m  (1/1 passed)   per… | devskim 1.0.70+d69541fde7 |
| `evaluation.results` | fail | high | - | Missing evaluation outputs | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-ob92maxl/scorecard.md, /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-ob92maxl/checks.json | - | - |
| `evaluation.quality` | fail | high | 0.00 | Evaluation results JSON missing | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-ob92maxl/checks.json, /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-ob92maxl/evaluation_report.json, /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-ob92maxl/llm_evaluation.json | - | - |
| `run.evaluate_llm` | pass | medium | 80959.22 | make evaluate-llm succeeded | - | Checking DevSkim CLI installation... Setup complete! Analyzing synthetic... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/eval-repos/synthetic" \ 		--repo-name "synthetic" \ 		--output-dir "/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-hpq2_s_o" \ 		--run-id "compliance" \ 		--repo-id "compliance" \ 		--branch "main" \ 		--commit "2f5bef575d66bab89d7bcb1221ac9bf0ab6b89d2" \ 		--custom-rules "rules/custom" Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/eval-repos/synthetic Files analyzed: 16 Issues found: 50 Duration: 1654ms Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compl… | devskim 1.0.70+d69541fde7 <frozen runpy>:128: RuntimeWarning: 'evaluation.llm.orchestrator' found in sys.modules after import of package 'evaluation.llm', but prior to execution of 'evaluation.llm.orchestrator'; this may result in unpredictable behaviour |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | fail | medium | 0.00 | LLM evaluation JSON missing | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-c1fv_fk0/llm_evaluation.json | - | - |
| `output.load` | pass | high | 1.54 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-hpq2_s_o/output.json | - | - |
| `output.paths` | pass | high | 2.44 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.24 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.20 | Path consistency validated | Checked 18 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.04 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.04 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.04 | Tool name matches data.tool | devskim, devskim | - | - |
| `output.metadata_consistency` | pass | medium | 0.05 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 1.05 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 277.69 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.64 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.46 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.10 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.23 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.15 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.72 | analyze target output pattern acceptable | - | - | - |
| `schema.draft` | pass | medium | 0.56 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.39 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 1.06 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.71 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.13 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.06 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.22 | LLM judge count meets minimum (4 >= 4) | rule_coverage.py, severity_calibration.py, security_focus.py, detection_accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 12.64 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: detection_accuracy.py, prompt: detection_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.32 | Ground truth files present | api-security.json, deserialization.json, xxe.json, csharp.json, clean.json | - | - |
| `evaluation.scorecard` | pass | low | 0.03 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.04 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.37 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.19 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.03 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.11 | LLM evaluation schema valid | run_id, timestamp, model, score, decision, dimensions, total_score, average_confidence, combined_score, programmatic_input | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.09 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.09 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.38 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_devskim_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.14 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 3.52 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 121.01 | Adapter successfully persisted fixture data | Fixture: devskim_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.74 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.78 | Adapter DevskimAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.37 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.61 | Tool 'devskim' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.28 | dbt staging model(s) found | stg_lz_devskim_findings.sql, stg_devskim_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.79 | dbt models present for tool | stg_lz_devskim_findings.sql, stg_devskim_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 17.33 | All entities have aligned repositories | DevskimFinding | - | - |
| `test.structure_naming` | pass | medium | 1.11 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 55.88 | Cross-tool SQL joins use correct patterns (200 files checked) | - | - | - |
| `test.coverage_threshold` | pass | high | 1.49 | Test coverage 80.7% >= 80% threshold | coverage=80.7%, threshold=80% | - | - |

## dotcover

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 151199.11 | make analyze succeeded | - | Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/eval-repos/synthetic as project 'synthetic' /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/eval-repos/synthetic \ 		--repo-name synthetic \ 		--output-dir /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-guh5dlbx \ 		--run-id compliance \ 		--repo-id compliance \ 		--branch main \ 		--commit 2f5bef575d66bab89d7bcb1221ac9bf0ab6b89d2 Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/eval-repos/synthetic Found test project: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/eval-repos/s… | - |
| `run.evaluate` | pass | high | 224.70 | make evaluate succeeded | - | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate \ 		--results-dir outputs/dotcover-test-run \ 		--ground-truth-dir evaluation/ground-truth \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-zbxemixd/evaluation_report.json Scorecard JSON saved to: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/evaluation/scorecard.json Scorecard Markdown saved to: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/evaluation/scorecard.md Evaluation complete. Decision: PASS Score: 100.0% (19/19 passed) Results saved to /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-zbxemixd/evaluation_report.json | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | pass | high | 0.31 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 175.74 | make evaluate-llm succeeded | - | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator \ 		/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-guh5dlbx \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-o0u2aeza/llm_evaluation.json \ 		--model opus-4.5 \ 		--programmatic-results evaluation/results/evaluation_report.json LLM evaluation complete. Verdict: PASS Results saved to /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-o0u2aeza/llm_evaluation.json | - |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.40 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 0.18 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-guh5dlbx/output.json | - | - |
| `output.paths` | pass | high | 0.88 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.26 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.04 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.04 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.04 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.04 | Tool name matches data.tool | dotcover, dotcover | - | - |
| `output.metadata_consistency` | pass | medium | 0.05 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 1.13 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 283.10 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.36 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.28 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.15 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.16 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.26 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 1.13 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.34 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.10 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.21 | LLM judge count meets minimum (4 >= 4) | false_positive.py, actionability.py, integration.py, accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 21.62 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: accuracy.py, prompt: accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.05 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.08 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.06 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.05 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.05 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.04 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 1.03 | Rollup Validation declared with valid tests | src/tools/dotcover/tests/unit/test_analyze.py | - | - |
| `adapter.compliance` | pass | info | 0.36 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 7.37 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 470.00 | Adapter successfully persisted fixture data | Fixture: dotcover_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 2.40 | All 3 quality rules have implementation coverage | coverage_bounds, statement_invariants, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 2.18 | Adapter DotcoverAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.93 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.54 | Tool 'dotcover' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.83 | dbt staging model(s) found | stg_dotcover_file_metrics.sql, stg_lz_dotcover_type_coverage.sql, stg_lz_dotcover_method_coverage.sql, stg_lz_dotcover_assembly_coverage.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.27 | dbt models present for tool | stg_dotcover_file_metrics.sql, stg_lz_dotcover_type_coverage.sql, stg_lz_dotcover_method_coverage.sql, stg_lz_dotcover_assembly_coverage.sql | - | - |
| `entity.repository_alignment` | pass | high | 31.10 | All entities have aligned repositories | DotcoverAssemblyCoverage, DotcoverTypeCoverage, DotcoverMethodCoverage | - | - |
| `test.structure_naming` | pass | medium | 1.11 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 118.39 | Cross-tool SQL joins use correct patterns (203 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.82 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## git-fame

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 7388.17 | make analyze succeeded | - | Running authorship analysis on synthetic... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python scripts/analyze.py /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/eval-repos/synthetic --output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-bugzz6rh/output.json ============================================================ git-fame Authorship Analysis ============================================================ Found 5 repositories to analyze  Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/eval-repos/synthetic/balanced...   Results: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-bugzz6rh/output.json   Authors: 4   Total LOC: 994   Bus Factor: 2   HHI Index: 0.2500… | - |
| `run.evaluate` | pass | high | 4952.05 | make evaluate succeeded | - | Running programmatic evaluation... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python scripts/evaluate.py ============================================================ git-fame Programmatic Evaluation ============================================================  Using output directory: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/outputs/f23f9a48-fb85-4c81-8e04-da14641d23b3 Running evaluation checks...  1. Output Quality checks...    Score: 5.0/5.0 (6/6 passed) 2. Authorship Accuracy checks...    Score: 5.0/5.0 (8/8 passed) 3. Reliability checks...    Score: 5.0/5.0 (4/4 passed) 4. Performance checks...    Score: 5.0/5.0 (4/4 passed) 5. Integration Fit checks...    Score: 5.0/5.0 (4/4 passed) 6. Installation checks...    Score: 5.0/5… | - |
| `evaluation.results` | fail | high | - | Missing evaluation outputs | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-cifyw_j0/scorecard.md | - | - |
| `evaluation.quality` | fail | high | 0.00 | Evaluation results JSON missing | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-cifyw_j0/checks.json, /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-cifyw_j0/evaluation_report.json, /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-cifyw_j0/llm_evaluation.json | - | - |
| `run.evaluate_llm` | pass | medium | 128181.08 | make evaluate-llm succeeded | - | Running LLM-as-a-Judge evaluation... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator --model opus-4.5 --output evaluation/results/llm_evaluation.json LLM Evaluation for git-fame Model: opus-4.5 Working directory: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame Output directory: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/outputs ============================================================  Running full evaluation (6 judges)... Registered 6 judges  Running authorship_quality evaluation...   Score: 4/5 (confidence: 0.78) Running bus_factor_accuracy evaluation...   Score: 4/5 (confidence: 0.88) Running concentration_metrics evaluation...   Score: 5/5 (confidence: 0.95) Ru… | <frozen runpy>:128: RuntimeWarning: 'evaluation.llm.orchestrator' found in sys.modules after import of package 'evaluation.llm', but prior to execution of 'evaluation.llm.orchestrator'; this may result in unpredictable behaviour |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | fail | medium | 0.00 | LLM evaluation JSON missing | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-5pmt0f7l/llm_evaluation.json | - | - |
| `output.load` | pass | high | 0.74 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-bugzz6rh/output.json | - | - |
| `output.paths` | pass | high | 0.49 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.13 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.06 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.05 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.05 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.05 | Tool name matches data.tool | git-fame, git-fame | - | - |
| `output.metadata_consistency` | pass | medium | 0.07 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.84 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 170.99 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.29 | All required paths present | - | - | - |
| `make.targets` | pass | high | 2.61 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.08 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.18 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.10 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target produces output.json | - | - | - |
| `schema.draft` | pass | medium | 0.12 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.07 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.48 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.34 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.10 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.09 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.19 | LLM judge count meets minimum (7 >= 4) | integration_readiness.py, concentration_metrics.py, evidence_quality.py, authorship_quality.py, utils.py, bus_factor_accuracy.py, output_completeness.py | - | - |
| `evaluation.synthetic_context` | pass | high | 20.36 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: authorship_quality.py, prompt: authorship_quality.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.13 | Ground truth files present | synthetic.json, multi-author.json, bus-factor-1.json, balanced.json, multi-branch.json, single-author.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.09 | Programmatic evaluation schema valid | timestamp, tool, version, overall_score, classification, summary, dimensions | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.07 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.11 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.10 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-fame/evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.08 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.36 | Rollup Validation declared with valid tests | src/tools/git-fame/tests/scripts/test_analyze.py, src/tools/git-fame/tests/scripts/test_authorship_accuracy_checks.py, src/tools/git-fame/tests/scripts/test_output_quality_checks.py, src/tools/git-fame/tests/scripts/test_reliability_checks.py | - | - |
| `adapter.compliance` | pass | info | 0.36 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 4.14 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 121.83 | Adapter successfully persisted fixture data | Fixture: git_fame_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.72 | All 3 quality rules have implementation coverage | hhi_valid, ownership_sums_100, bus_factor_valid | - | - |
| `sot.adapter_registered` | pass | medium | 0.99 | Adapter GitFameAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.53 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.59 | Tool 'git-fame' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.69 | dbt staging model(s) found | stg_lz_git_fame_authors.sql, stg_lz_git_fame_summary.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.55 | dbt models present for tool | stg_lz_git_fame_authors.sql, stg_lz_git_fame_summary.sql | - | - |
| `entity.repository_alignment` | pass | high | 12.67 | All entities have aligned repositories | GitFameAuthor, GitFameSummary | - | - |
| `test.structure_naming` | pass | medium | 1.77 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 34.85 | Cross-tool SQL joins use correct patterns (203 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.42 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## git-sizer

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 2420.39 | make analyze succeeded | - | Running repository analysis...   REPO_PATH: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/eval-repos/synthetic   RUN_ID:    compliance   REPO_ID:   compliance   BRANCH:    main   COMMIT:    2f5bef575d66bab89d7bcb1221ac9bf0ab6b89d2 Found 5 git repositories under /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/eval-repos/synthetic Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/eval-repos/synthetic/bloated Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-iwmjts2u/bloated/output.json Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/eval-repos/synthetic/deep-history Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/too… | - |
| `run.evaluate` | pass | high | 172.78 | make evaluate succeeded | - | Running programmatic evaluation...  ====================================================================== GIT-SIZER EVALUATION REPORT ======================================================================  Timestamp: 2026-02-08T10:42:40.030830 Analysis:  /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-iwmjts2u  ---------------------------------------------------------------------- OVERALL SUMMARY ----------------------------------------------------------------------   Total Checks: 28   Passed:       28 (100.0%)   Failed:       0 (0.0%)   Overall Score: 1.00/1.00   Decision:      STRONG_PASS  ---------------------------------------------------------------------- CATEGORY BREAKDOWN ----------------------------------------------------------------------   ACCURACY         8/… | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | pass | high | 0.87 | Evaluation score meets threshold (computed) | score=1.0, failed=0, total=28 | - | - |
| `run.evaluate_llm` | pass | medium | 76899.03 | make evaluate-llm succeeded | - | Running LLM evaluation...  ====================================================================== GIT-SIZER LLM EVALUATION REPORT ======================================================================  Timestamp: 2026-02-08T09:42:40.232454+00:00 Analysis:  /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-iwmjts2u Model:     opus-4.5  ---------------------------------------------------------------------- SUMMARY ----------------------------------------------------------------------   Weighted Score: 4.8/5.0   Grade:          A   Verdict:        STRONG_PASS  ---------------------------------------------------------------------- JUDGE RESULTS ----------------------------------------------------------------------    SIZE_ACCURACY (weight: 35%)     Score:      5/5 (weighted: 1.7… | Running size_accuracy judge...   Score: 5/5 (weight: 35%) Running threshold_quality judge...   Score: 5/5 (weight: 25%) Running actionability judge...   Score: 4/5 (weight: 20%) Running integration_fit judge...   Score: 5/5 (weight: 20%) |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.70 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 0.51 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-iwmjts2u/output.json | - | - |
| `output.paths` | pass | high | 0.35 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | fail | high | 0.09 | Data completeness issues detected | violations[0] missing required field: file_path, violations[0] missing required field: rule_id | - | - |
| `output.path_consistency` | pass | medium | 0.03 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.02 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.02 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.02 | Tool name matches data.tool | git-sizer, git-sizer | - | - |
| `output.metadata_consistency` | pass | medium | 0.04 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.54 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 244.26 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.33 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.61 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.05 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.17 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.12 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.15 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.58 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.47 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.08 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.08 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.57 | LLM judge count meets minimum (4 >= 4) | integration_fit.py, size_accuracy.py, actionability.py, threshold_quality.py | - | - |
| `evaluation.synthetic_context` | pass | high | 13.75 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: size_accuracy.py, prompt: size_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.22 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.38 | Programmatic evaluation schema valid | timestamp, decision, score, analysis_path, ground_truth_dir, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.10 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.13 | LLM evaluation schema valid | timestamp, analysis_path, model, trace_id, judges, summary, programmatic_input, decision, score, dimensions | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.11 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.10 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.24 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_git_sizer_repo_level_only.sql | - | - |
| `adapter.compliance` | pass | info | 0.09 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 4.28 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 212.52 | Adapter successfully persisted fixture data | Fixture: git_sizer_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.73 | All 3 quality rules have implementation coverage | health_grade_valid, metrics_non_negative, violation_levels | - | - |
| `sot.adapter_registered` | pass | medium | 0.63 | Adapter GitSizerAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.32 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.53 | Tool 'git-sizer' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.55 | dbt staging model(s) found | stg_lz_git_sizer_metrics.sql, stg_lz_git_sizer_violations.sql, stg_lz_git_sizer_lfs_candidates.sql, stg_git_sizer_lfs_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.26 | dbt models present for tool | stg_lz_git_sizer_metrics.sql, stg_lz_git_sizer_violations.sql, stg_lz_git_sizer_lfs_candidates.sql, stg_git_sizer_lfs_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 12.97 | All entities have aligned repositories | GitSizerMetric, GitSizerViolation, GitSizerLfsCandidate | - | - |
| `test.structure_naming` | pass | medium | 1.03 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 76.68 | Cross-tool SQL joins use correct patterns (203 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.81 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## gitleaks

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 31893.75 | make analyze succeeded | - | Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/eval-repos/synthetic as project 'synthetic' /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/eval-repos/synthetic \ 		--repo-name synthetic \ 		--output-dir /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-i497279u \ 		--run-id compliance \ 		--repo-id compliance \ 		--branch main \ 		--commit 2f5bef575d66bab89d7bcb1221ac9bf0ab6b89d2 Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/eval-repos/synthetic Using gitleaks: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/bin/gitleaks Git… | - |
| `run.evaluate` | pass | high | 129.72 | make evaluate succeeded | - | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate \ 		--analysis-dir outputs/runs \ 		--ground-truth-dir evaluation/ground-truth \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-9v9grg5g Gitleaks PoC Evaluation ============================================================ No analysis files found in outputs/runs Results saved to /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-9v9grg5g/evaluation_report.json | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | fail | high | 0.00 | Evaluation results JSON missing | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-9v9grg5g/checks.json, /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-9v9grg5g/evaluation_report.json, /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-9v9grg5g/llm_evaluation.json | - | - |
| `run.evaluate_llm` | pass | medium | 64768.72 | make evaluate-llm succeeded | - | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator \ 		--working-dir . \ 		--programmatic-results evaluation/results/evaluation_report.json \ 		--model opus-4.5 \ 		--evaluation-mode synthetic LLM Evaluation for poc-gitleaks Model: opus-4.5 Working directory: . Evaluation mode: synthetic ============================================================  Running 4 judges...  Running detection_accuracy evaluation...   Score: 1/5 (confidence: 0.99) Running false_positive evaluation...   Score: 3/5 (confidence: 0.30) Running secret_coverage evaluation...   Score: 1/5 (confidence: 0.95) Running severity_classification evaluation...   Score: 1/5 (confidence: 0.95)  ============================================================ RESULTS ============… | <frozen runpy>:128: RuntimeWarning: 'evaluation.llm.orchestrator' found in sys.modules after import of package 'evaluation.llm', but prior to execution of 'evaluation.llm.orchestrator'; this may result in unpredictable behaviour |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | fail | medium | 0.00 | LLM evaluation JSON missing | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-f0g8_bjp/llm_evaluation.json | - | - |
| `output.load` | pass | high | 1.93 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-i497279u/output.json | - | - |
| `output.paths` | pass | high | 2.71 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.17 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.29 | Path consistency validated | Checked 49 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.04 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.04 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.04 | Tool name matches data.tool | gitleaks, gitleaks | - | - |
| `output.metadata_consistency` | pass | medium | 0.05 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.86 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 161.51 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.33 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.54 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.19 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.67 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.43 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.59 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.33 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.21 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 1.51 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.90 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.28 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.16 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.50 | LLM judge count meets minimum (4 >= 4) | false_positive.py, secret_coverage.py, detection_accuracy.py, severity_classification.py | - | - |
| `evaluation.synthetic_context` | pass | high | 5.13 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: detection_accuracy.py, prompt: detection_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.04 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.07 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary, categories | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.06 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.29 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.07 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.04 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.37 | Rollup Validation declared with valid tests | src/tools/gitleaks/tests/unit/test_rollup_invariants.py, src/sot-engine/dbt/tests/test_rollup_gitleaks_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.10 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.39 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 132.37 | Adapter successfully persisted fixture data | Fixture: gitleaks_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.56 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.66 | Adapter GitleaksAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.27 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.40 | Tool 'gitleaks' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.23 | dbt staging model(s) found | stg_gitleaks_secrets.sql, stg_lz_gitleaks_secrets.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.68 | dbt models present for tool | stg_gitleaks_secrets.sql, stg_lz_gitleaks_secrets.sql | - | - |
| `entity.repository_alignment` | pass | high | 9.49 | All entities have aligned repositories | GitleaksSecret | - | - |
| `test.structure_naming` | pass | medium | 0.90 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 63.89 | Cross-tool SQL joins use correct patterns (203 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.50 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## layout-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 301.35 | make analyze succeeded | - | Setup complete! Scanning synthetic... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner/eval-repos/synthetic" \ 		--repo-name "synthetic" \ 		--output-dir "/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-_ux3xyce" \ 		--run-id "compliance" \ 		--repo-id "compliance" \ 		--branch "main" \ 		 \ 		--commit "2f5bef575d66bab89d7bcb1221ac9bf0ab6b89d2" Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner/eval-repos/synthetic Files found: 143 Directories: 79 Scan duration: 26ms Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-_ux3xyce/output.json | - |
| `run.evaluate` | pass | high | 284.61 | make evaluate succeeded | - | Setup complete! EVAL_OUTPUT_DIR=/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-4ox47rag /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate Evaluating output.json...   Score: 4.75/5.0 - STRONG_PASS   Checks: 33/36 passed  Results saved to /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-4ox47rag/evaluation_report.json Scorecard saved to /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-4ox47rag/scorecard.md  Aggregate: 4.75/5.0 - STRONG_PASS | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | pass | high | 0.52 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 201345.91 | make evaluate-llm succeeded | - | Setup complete! /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator \ 		--working-dir /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner \ 		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-_ux3xyce/output.json \ 		--model opus-4.5 \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-ldi7t5yy/llm_evaluation.json \ 		--programmatic-results evaluation/results/evaluation_report.json Running full evaluation (4 judges)... Running classification_reasoning evaluation...   Score: 4/5 (confidence: 0.82) Running directory_taxonomy evaluation...   Score: 3/5 (confidence: 0.50) Running hierarchy_consistency evaluation...   Score: 5/5 (confidence: 0.88) Runnin… | <frozen runpy>:128: RuntimeWarning: 'evaluation.llm.orchestrator' found in sys.modules after import of package 'evaluation.llm', but prior to execution of 'evaluation.llm.orchestrator'; this may result in unpredictable behaviour |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.46 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 1.71 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-_ux3xyce/output.json | - | - |
| `output.paths` | pass | high | 15.20 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.08 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.03 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.02 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.02 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.02 | Tool name matches data.tool | layout-scanner, layout-scanner | - | - |
| `output.metadata_consistency` | pass | medium | 0.03 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.77 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 449.88 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.38 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.63 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.18 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.28 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.09 | analyze target output pattern acceptable | - | - | - |
| `schema.draft` | pass | medium | 0.25 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.14 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.59 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.96 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.16 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.07 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.21 | LLM judge count meets minimum (4 >= 4) | classification_reasoning.py, hierarchy_consistency.py, language_detection.py, directory_taxonomy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 17.87 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: classification_reasoning.py, prompt: classification_reasoning.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 7.11 | Ground truth files present | mixed-language.json, edge-cases.json, generated-code.json, config-heavy.json, vendor-heavy.json, small-clean.json, deep-nesting.json, mixed-types.json | - | - |
| `evaluation.scorecard` | pass | low | 0.03 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 3.61 | Programmatic evaluation schema valid | timestamp, decision, score, evaluated_count, average_score, summary, checks, repositories | - | - |
| `evaluation.programmatic_quality` | pass | high | 2.36 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.15 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.39 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.19 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.15 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.78 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_layout_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.22 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 6.53 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 377.07 | Adapter successfully persisted fixture data | Fixture: layout_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.03 | All 3 quality rules have implementation coverage | paths, ranges, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.73 | Adapter LayoutAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.37 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.00 | layout-scanner handled specially as prerequisite tool | Layout is ingested before TOOL_INGESTION_CONFIGS loop | - | - |
| `sot.dbt_staging_model` | pass | high | 1.45 | dbt staging model(s) found | stg_lz_layout_files.sql, stg_lz_layout_directories.sql | - | - |
| `dbt.model_coverage` | pass | high | 2.62 | dbt models present for tool | stg_lz_layout_files.sql, stg_lz_layout_directories.sql | - | - |
| `entity.repository_alignment` | pass | high | 29.03 | All entities have aligned repositories | LayoutFile, LayoutDirectory | - | - |
| `test.structure_naming` | pass | medium | 2.20 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 109.60 | Cross-tool SQL joins use correct patterns (203 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.64 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## lizard

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | fail | critical | 241.21 | make analyze failed | Running function analysis on synthetic... | Running function analysis on synthetic... | Traceback (most recent call last):   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/lizard/scripts/analyze.py", line 13, in <module>     from function_analyzer import (   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/lizard/scripts/function_analyzer.py", line 20, in <module>     import lizard ModuleNotFoundError: No module named 'lizard' make[1]: *** [analyze] Error 1 |
| `run.evaluate` | fail | high | 221.29 | make evaluate failed | Running programmatic evaluation (76 checks)... | Running programmatic evaluation (76 checks)... | Traceback (most recent call last):   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/lizard/scripts/analyze.py", line 13, in <module>     from function_analyzer import (   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/lizard/scripts/function_analyzer.py", line 20, in <module>     import lizard ModuleNotFoundError: No module named 'lizard' make[1]: *** [evaluate] Error 1 |
| `run.evaluate_llm` | pass | medium | 55166.11 | make evaluate-llm succeeded | - | Running LLM evaluation (4 judges)...  ============================================================ LLM Evaluation - Lizard Function Complexity Analysis ============================================================  Running ccn_accuracy evaluation...   Ground truth assertions failed: 1 failures   Score: 2/5 (confidence: 0.45) Running function_detection evaluation...   Ground truth assertions failed: 1 failures   Score: 1/5 (confidence: 0.95) Running statistics evaluation...   Ground truth assertions failed: 1 failures   Score: 1/5 (confidence: 0.95) Running hotspot_ranking evaluation...   Ground truth assertions failed: 1 failures   Score: 1/5 (confidence: 0.95)  ============================================================ EVALUATION SUMMARY ==================================================… | <frozen runpy>:128: RuntimeWarning: 'evaluation.llm.orchestrator' found in sys.modules after import of package 'evaluation.llm', but prior to execution of 'evaluation.llm.orchestrator'; this may result in unpredictable behaviour |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.38 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 4.25 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/lizard/evaluation/results/output.json | - | - |
| `output.paths` | pass | high | 16.85 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.13 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.14 | Path consistency validated | Checked 85 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.02 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.02 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.02 | Tool name matches data.tool | lizard, lizard | - | - |
| `output.metadata_consistency` | pass | medium | 0.05 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.91 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 238.90 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.26 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.54 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.14 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.11 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.17 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.12 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.63 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.50 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.10 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.07 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.17 | LLM judge count meets minimum (4 >= 4) | hotspot_ranking.py, ccn_accuracy.py, function_detection.py, statistics.py | - | - |
| `evaluation.synthetic_context` | pass | high | 11.67 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: ccn_accuracy.py, prompt: ccn_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.23 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | pass | low | 0.01 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.03 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.68 | Programmatic evaluation schema valid | timestamp, decision, score, analysis_path, ground_truth_path, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.36 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.08 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.07 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.06 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.32 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_lizard_direct_distribution_ranges.sql, src/sot-engine/dbt/tests/test_rollup_lizard_direct_vs_recursive.sql, src/sot-engine/dbt/tests/test_rollup_lizard_distribution_ranges.sql | - | - |
| `adapter.compliance` | pass | info | 0.10 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.56 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 148.80 | Adapter successfully persisted fixture data | Fixture: lizard_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.72 | All 3 quality rules have implementation coverage | paths, ranges, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.62 | Adapter LizardAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.30 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.53 | Tool 'lizard' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.26 | dbt staging model(s) found | stg_lz_lizard_file_metrics.sql, stg_lz_lizard_function_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.68 | dbt models present for tool | stg_lz_lizard_file_metrics.sql, stg_lz_lizard_function_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 9.09 | All entities have aligned repositories | LizardFileMetric, LizardFunctionMetric | - | - |
| `test.structure_naming` | pass | medium | 0.74 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 66.83 | Cross-tool SQL joins use correct patterns (203 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.50 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## pmd-cpd

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 7774.03 | make analyze succeeded | - | Java found: /opt/homebrew/opt/openjdk@17/bin/java Running CPD analysis on synthetic... Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/eval-repos/synthetic... Analysis complete: 39 clones found Output written to: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-t7q_tovz/output.json Warnings: 1   - CPD error for rust: Invalid value for option '--language': Unknown language: rust Usage: pmd cpd [-Dh] [--ignore-annotations] [--ignore-identifiers]                [--ignore-literal-sequences] [--ignore-literals] | - |
| `run.evaluate` | pass | high | 278.02 | make evaluate succeeded | - | Running programmatic evaluation (~28 checks)... ====================================================================== PMD CPD EVALUATION REPORT ======================================================================  Analysis: outputs/cpd-test-run/output.json Ground Truth: evaluation/ground-truth Timestamp: 2026-02-08T10:50:01.877531  ---------------------------------------------------------------------- SUMMARY ---------------------------------------------------------------------- Total Checks: 28 Passed: 27 Failed: 1 Overall Score: 89.03%  Score by Category:   ACCURACY: 76.96% (8/8 passed)   COVERAGE: 100.00% (8/8 passed)   EDGE_CASES: 97.13% (8/8 passed)   PERFORMANCE: 75.00% (3/4 passed)  ---------------------------------------------------------------------- CHECK RESULTS -------------… | - |
| `evaluation.results` | fail | high | - | Missing evaluation outputs | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-aifbhgi7/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 2.39 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | fail | medium | 8642.05 | make evaluate-llm failed | Java found: /opt/homebrew/opt/openjdk@17/bin/java
Running CPD analysis on synthetic...
Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/eval-repos/synthetic...
Analysis complete: 39 clones found
Output written to: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-t7q_tovz/output.json
Warnings: 1
  - CPD error for rust: Invalid value for option '--language': Unknown language: rust
Usage: pmd cpd [-Dh] [--ignore-annotations] [--ignore-identifiers]
               [--ignore-literal-sequences] [--ignore-literals]
       
Running LLM evaluation (4 judges)... | Java found: /opt/homebrew/opt/openjdk@17/bin/java Running CPD analysis on synthetic... Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/eval-repos/synthetic... Analysis complete: 39 clones found Output written to: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-t7q_tovz/output.json Warnings: 1   - CPD error for rust: Invalid value for option '--language': Unknown language: rust Usage: pmd cpd [-Dh] [--ignore-annotations] [--ignore-identifiers]                [--ignore-literal-sequences] [--ignore-literals]         Running LLM evaluation (4 judges)... | Traceback (most recent call last):   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/scripts/llm_evaluate.py", line 348, in <module>     main()   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/scripts/llm_evaluate.py", line 271, in main     report = run_llm_evaluation(              ^^^^^^^^^^^^^^^^^^^   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/scripts/llm_evaluate.py", line 93, in run_llm_evaluation     DuplicationAccuracyJudge( TypeError: BaseJudge.__init__() got an unexpected keyword argument 'analysis_path' make[1]: *** [evaluate-llm] Error 1 |
| `output.load` | pass | high | 0.96 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-t7q_tovz/output.json | - | - |
| `output.paths` | pass | high | 1.79 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.11 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.12 | Path consistency validated | Checked 49 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.02 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.02 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.02 | Tool name matches data.tool | pmd-cpd, pmd-cpd | - | - |
| `output.metadata_consistency` | pass | medium | 0.04 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.80 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 196.85 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.30 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.30 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.13 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.13 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.14 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.09 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.65 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.80 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.09 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.08 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.18 | LLM judge count meets minimum (4 >= 4) | duplication_accuracy.py, actionability.py, semantic_detection.py, cross_file_detection.py | - | - |
| `evaluation.synthetic_context` | pass | high | 6.42 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: duplication_accuracy.py, prompt: duplication_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.30 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.42 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.21 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.22 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, combined_score, notes | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.07 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=WEAK_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.05 | LLM evaluation passed | WEAK_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.41 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_pmd_cpd_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.10 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 4.73 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 253.95 | Adapter successfully persisted fixture data | Fixture: pmd_cpd_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.41 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.41 | Adapter PmdCpdAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.30 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.39 | Tool 'pmd-cpd' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.37 | dbt staging model(s) found | stg_lz_pmd_cpd_duplications.sql, stg_lz_pmd_cpd_occurrences.sql, stg_lz_pmd_cpd_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.78 | dbt models present for tool | stg_lz_pmd_cpd_duplications.sql, stg_lz_pmd_cpd_occurrences.sql, stg_lz_pmd_cpd_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 16.07 | All entities have aligned repositories | PmdCpdFileMetric, PmdCpdDuplication, PmdCpdOccurrence | - | - |
| `test.structure_naming` | pass | medium | 0.66 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 57.14 | Cross-tool SQL joins use correct patterns (203 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.96 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## roslyn-analyzers

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 20398.97 | make analyze succeeded | - | Building external repo: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/eval-repos/synthetic... MSBUILD : error MSB1003: Specify a project or solution file. The current working directory does not contain a project or solution file. MSBUILD : error MSB1003: Specify a project or solution file. The current working directory does not contain a project or solution file. Build completed (some errors may be expected) Running Roslyn analysis... Building AsyncPatterns.csproj...   Found 150 violations Building NullSafety.csproj...   Found 83 violations Building ApiConventions.csproj...   Found 1 violations Building SyntheticSmells.csproj...   Found 1051 violations Building ResourceManagement.csproj...   Found 6 violations  =======================================… | - |
| `run.evaluate` | pass | high | 12616.10 | make evaluate succeeded | - | Building external repo: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/eval-repos/synthetic... MSBUILD : error MSB1003: Specify a project or solution file. The current working directory does not contain a project or solution file. MSBUILD : error MSB1003: Specify a project or solution file. The current working directory does not contain a project or solution file. Build completed (some errors may be expected) Running Roslyn analysis... Building AsyncPatterns.csproj...   Found 150 violations Building NullSafety.csproj...   Found 83 violations Building ApiConventions.csproj...   Found 1 violations Building SyntheticSmells.csproj...   Found 1051 violations Building ResourceManagement.csproj...   Found 6 violations  =======================================… | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | pass | high | 3.34 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 99690.45 | make evaluate-llm succeeded | - | Building external repo: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/eval-repos/synthetic... MSBUILD : error MSB1003: Specify a project or solution file. The current working directory does not contain a project or solution file. MSBUILD : error MSB1003: Specify a project or solution file. The current working directory does not contain a project or solution file. Build completed (some errors may be expected) Running Roslyn analysis... Building AsyncPatterns.csproj...   Found 150 violations Building NullSafety.csproj...   Found 83 violations Building ApiConventions.csproj...   Found 1 violations Building SyntheticSmells.csproj...   Found 1051 violations Building ResourceManagement.csproj...   Found 6 violations  =======================================… | - |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.52 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 5.01 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-58u3f_u3/output.json | - | - |
| `output.paths` | pass | high | 35.13 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.11 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.11 | Path consistency validated | Checked 62 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.02 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.02 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.02 | Tool name matches data.tool | roslyn-analyzers, roslyn-analyzers | - | - |
| `output.metadata_consistency` | pass | medium | 0.03 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.50 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 388.78 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.40 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.45 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.17 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.13 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.56 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.37 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.10 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 10.29 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 1.15 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.08 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.08 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.19 | LLM judge count meets minimum (5 >= 4) | overall_quality.py, integration_fit.py, resource_management.py, security_detection.py, design_analysis.py | - | - |
| `evaluation.synthetic_context` | pass | high | 38.16 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: security_detection.py, prompt: security_detection.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.17 | Ground truth files present | clean-code.json, resource-management.json, dead-code.json, csharp.json, security-issues.json, design-violations.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.03 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.24 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary | - | - |
| `evaluation.programmatic_quality` | pass | high | 1.92 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.07 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.20 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.18 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.82 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 2.57 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_roslyn_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.83 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 6.82 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 441.38 | Adapter successfully persisted fixture data | Fixture: roslyn_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.16 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.93 | Adapter RoslynAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.37 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.58 | Tool 'roslyn-analyzers' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.33 | dbt staging model(s) found | stg_lz_roslyn_violations.sql, stg_roslyn_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 1.37 | dbt models present for tool | stg_lz_roslyn_violations.sql, stg_roslyn_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 13.09 | All entities have aligned repositories | RoslynViolation | - | - |
| `test.structure_naming` | pass | medium | 1.33 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 219.00 | Cross-tool SQL joins use correct patterns (203 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.72 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## scancode

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 535.31 | make analyze succeeded | - | Running license analysis on synthetic... Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/eval-repos/synthetic Licenses found: ['Apache-2.0', 'BSD-3-Clause', 'GPL-2.0-only WITH Classpath-exception-2.0', 'GPL-3.0-only', 'LGPL-2.1-only', 'MIT', 'Unlicense'] Overall risk: critical Files with licenses: 23 Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-c0fvgecw/output.json | - |
| `run.evaluate` | pass | high | 309.98 | make evaluate succeeded | - | Running programmatic evaluation... License Analysis Evaluation ============================================================  no-license: 32/32 (PASS) apache-bsd: 32/32 (PASS) mit-only: 32/32 (PASS) apache-bsd: 32/32 (PASS) gpl-mixed: 32/32 (PASS) multi-license: 32/32 (PASS)  ============================================================ Summary ============================================================ Repositories evaluated: 6 Total checks: 192 Passed: 192 Failed: 0 Overall pass rate: 100.0%  Scorecard saved to: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/evaluation/scorecard.json Markdown scorecard saved to: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/evaluation/scorecard.md  Results saved to: evaluation/results/evaluati… | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | fail | high | 0.00 | Evaluation results JSON missing | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-owig3o3k/checks.json, /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-owig3o3k/evaluation_report.json, /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-owig3o3k/llm_evaluation.json | - | - |
| `run.evaluate_llm` | pass | medium | 14130.87 | make evaluate-llm succeeded | - | Running LLM-as-a-Judge evaluation... LLM Evaluation for scancode Model: opus-4.5 Working directory: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode ============================================================  Running 4 judges...  Running accuracy evaluation...   Score: 3/5 (confidence: 0.50) Running coverage evaluation...   Score: 3/5 (confidence: 0.50) Running actionability evaluation...   Score: 3/5 (confidence: 0.50) Running risk_classification evaluation...   Score: 3/5 (confidence: 0.50)  ============================================================ RESULTS ============================================================ Total Score: 3.00 Decision: WEAK_PASS  Results saved to: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/evalu… | - |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.93 | LLM evaluation decision meets threshold | WEAK_PASS | - | - |
| `output.load` | pass | high | 0.51 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-c0fvgecw/output.json | - | - |
| `output.paths` | pass | high | 1.57 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.12 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.05 | Path consistency validated | Checked 23 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.02 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.02 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.02 | Tool name matches data.tool | scancode, scancode | - | - |
| `output.metadata_consistency` | pass | medium | 0.04 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.58 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 143.84 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.28 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.39 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.15 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.11 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.12 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.50 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.40 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.07 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.09 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.18 | LLM judge count meets minimum (4 >= 4) | coverage_judge.py, accuracy_judge.py, actionability_judge.py, risk_classification_judge.py | - | - |
| `evaluation.synthetic_context` | pass | high | 17.83 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: accuracy_judge.py, prompt: accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.11 | Ground truth files present | multi-license.json, mit-only.json, gpl-mixed.json, apache-bsd.json, public-domain.json, spdx-expression.json, no-license.json, dual-licensed.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.77 | Programmatic evaluation schema valid | timestamp, tool, version, decision, score, summary, checks, total_repositories, reports | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.53 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.05 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 1.03 | LLM evaluation schema valid | run_id, timestamp, model, dimensions, score, total_score, average_confidence, decision, programmatic_score, combined_score | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.73 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.67 | LLM evaluation passed | WEAK_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.21 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_scancode_repo_level_metrics.sql | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.30 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 149.51 | Adapter successfully persisted fixture data | Fixture: scancode_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.44 | All 3 quality rules have implementation coverage | paths, confidence, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.47 | Adapter ScancodeAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.30 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.38 | Tool 'scancode' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.25 | dbt staging model(s) found | stg_lz_scancode_summary.sql, stg_lz_scancode_file_licenses.sql, stg_scancode_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.20 | dbt models present for tool | stg_lz_scancode_summary.sql, stg_lz_scancode_file_licenses.sql, stg_scancode_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 9.75 | All entities have aligned repositories | ScancodeFileLicense, ScancodeSummary | - | - |
| `test.structure_naming` | pass | medium | 0.56 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 47.57 | Cross-tool SQL joins use correct patterns (203 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.43 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## scc

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 264.77 | make analyze succeeded | - | Running directory analysis on synthetic... Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/eval-repos/synthetic Using scc: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/bin/scc Files found: 63 Total files: 63 Total lines: 7,666 Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-8e53jh9m/output.json | - |
| `run.evaluate` | fail | high | 186.02 | make evaluate failed | Running programmatic evaluation... | Running programmatic evaluation... | Traceback (most recent call last):   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/scripts/evaluate.py", line 17, in <module>     from scripts.analyze import _resolve_commit ImportError: cannot import name '_resolve_commit' from 'scripts.analyze' (/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/scripts/analyze.py) make[1]: *** [evaluate] Error 1 |
| `run.evaluate_llm` | pass | medium | 216803.16 | make evaluate-llm succeeded | - | Running LLM-as-a-Judge evaluation... ============================================================ LLM-as-a-Judge Evaluation ============================================================ Mode: full Model: opus-4.5 Working Directory: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc ============================================================  Registering all judges (10 dimensions)...  Running code_quality evaluation...   Score: 4/5 (confidence: 0.88) Running integration_fit evaluation...   Score: 4/5 (confidence: 0.92) Running documentation evaluation...   Score: 4/5 (confidence: 0.82) Running edge_cases evaluation...   Score: 4/5 (confidence: 0.82) Running error_messages evaluation...   Score: 4/5 (confidence: 0.82) Running api_design evaluation...   Score: 4/5 (confi… | - |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.80 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 1.42 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-8e53jh9m/output.json | - | - |
| `output.paths` | pass | high | 5.88 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.10 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.15 | Path consistency validated | Checked 94 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.02 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.02 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.02 | Tool name matches data.tool | scc, scc | - | - |
| `output.metadata_consistency` | pass | medium | 0.03 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.74 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 173.06 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.27 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.65 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.13 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.10 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.15 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.11 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.84 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.67 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.17 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.13 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.19 | LLM judge count meets minimum (10 >= 4) | error_messages.py, documentation.py, edge_cases.py, directory_analysis.py, integration_fit.py, code_quality.py, risk.py, statistics.py, comparative.py, api_design.py | - | - |
| `evaluation.synthetic_context` | pass | high | 13.87 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: directory_analysis.py, prompt: directory_analysis.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.06 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.23 | Programmatic evaluation schema valid | run_id, timestamp, dimensions, total_score, decision | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.19 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.17 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.13 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.11 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.38 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_scc_direct_distribution_ranges.sql, src/sot-engine/dbt/tests/test_rollup_scc_direct_vs_recursive.sql, src/sot-engine/dbt/tests/test_rollup_scc_distribution_ranges.sql | - | - |
| `adapter.compliance` | pass | info | 0.07 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.43 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 154.74 | Adapter successfully persisted fixture data | Fixture: scc_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.49 | All 4 quality rules have implementation coverage | paths, ranges, ratios, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.79 | Adapter SccAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.29 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.48 | Tool 'scc' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.27 | dbt staging model(s) found | stg_lz_scc_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.73 | dbt models present for tool | stg_lz_scc_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 9.84 | All entities have aligned repositories | SccFileMetric | - | - |
| `test.structure_naming` | pass | medium | 0.72 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 61.88 | Cross-tool SQL joins use correct patterns (203 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.48 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## semgrep

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 8158.82 | make analyze succeeded | - | SKIP_SETUP=1: skipping semgrep install Initializing real repositories... Initializing Elttam audit rules...   Elttam rules already present Setup complete! Analyzing synthetic... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/eval-repos/synthetic" \ 		--repo-name "synthetic" \ 		--output-dir "/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-hcjan9wi" \ 		--run-id "compliance" \ 		--repo-id "compliance" \ 		--branch "main" \ 		--commit "2f5bef575d66bab89d7bcb1221ac9bf0ab6b89d2" Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/eval-repos/synthetic Files analyzed: 58 Smells found: 193 Duration: 6011m… | - |
| `run.evaluate` | pass | high | 410.18 | make evaluate succeeded | - | SKIP_SETUP=1: skipping semgrep install Initializing real repositories... Initializing Elttam audit rules...   Elttam rules already present Setup complete! Running programmatic evaluation (~28 checks)... EVAL_OUTPUT_DIR=/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-zfomcb32 /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate \ 		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-hcjan9wi/output.json \ 		--ground-truth evaluation/ground-truth \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-zfomcb32/evaluation_report.json  [36m======================================================================[0m [36m[1m  SEMGREP EVALUATION REPORT[0m [36m====================… | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | pass | high | 0.25 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 127442.07 | make evaluate-llm succeeded | - | SKIP_SETUP=1: skipping semgrep install Initializing real repositories... Initializing Elttam audit rules...   Elttam rules already present Setup complete! Analyzing synthetic... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/eval-repos/synthetic" \ 		--repo-name "synthetic" \ 		--output-dir "/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-hcjan9wi" \ 		--run-id "compliance" \ 		--repo-id "compliance" \ 		--branch "main" \ 		--commit "2f5bef575d66bab89d7bcb1221ac9bf0ab6b89d2" Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/eval-repos/synthetic Files analyzed: 58 Smells found: 193 Duration: 5704m… | [DEBUG] Looking for analysis files in: outputs   [DEBUG] Found 16 JSON files   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Looking for analysis files in: outputs   [DEBUG] Found 16 JSON files   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Load… |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.76 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 1.21 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-hcjan9wi/output.json | - | - |
| `output.paths` | pass | high | 7.14 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.11 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.12 | Path consistency validated | Checked 65 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.02 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.02 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.02 | Tool name matches data.tool | semgrep, semgrep | - | - |
| `output.metadata_consistency` | pass | medium | 0.03 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 2.88 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 222.90 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.30 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.02 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.06 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.15 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.15 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.09 | analyze target output pattern acceptable | - | - | - |
| `schema.draft` | pass | medium | 0.17 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.11 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.81 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.93 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.14 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.08 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.21 | LLM judge count meets minimum (5 >= 4) | rule_coverage.py, actionability.py, security_detection.py, smell_accuracy.py, false_positive_rate.py | - | - |
| `evaluation.synthetic_context` | pass | high | 20.40 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: security_detection.py, prompt: security_detection.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.14 | Ground truth files present | java.json, go.json, csharp.json, rust.json, javascript.json, typescript.json, python.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.25 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.08 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.17 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, analysis_path, combined | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.18 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.12 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.40 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_semgrep_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.07 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.67 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 175.15 | Adapter successfully persisted fixture data | Fixture: semgrep_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 2.21 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.91 | Adapter SemgrepAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.34 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.60 | Tool 'semgrep' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.28 | dbt staging model(s) found | stg_semgrep_file_metrics.sql, stg_lz_semgrep_smells.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.88 | dbt models present for tool | stg_semgrep_file_metrics.sql, stg_lz_semgrep_smells.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.44 | All entities have aligned repositories | SemgrepSmell | - | - |
| `test.structure_naming` | pass | medium | 1.15 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 65.16 | Cross-tool SQL joins use correct patterns (203 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.50 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## sonarqube

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | fail | critical | 214.78 | make analyze failed | Analyzing synthetic...
/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/eval-repos/synthetic \
		--project-key synthetic \
		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-fy9i5v94/output.json \
		--sonarqube-url http://localhost:9000 \
		--run-id "compliance" \
		--repo-id "compliance" \
		--branch "main" \
		--commit "2f5bef575d66bab89d7bcb1221ac9bf0ab6b89d2" \
		 \
		 \ | Analyzing synthetic... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/eval-repos/synthetic \ 		--project-key synthetic \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-fy9i5v94/output.json \ 		--sonarqube-url http://localhost:9000 \ 		--run-id "compliance" \ 		--repo-id "compliance" \ 		--branch "main" \ 		--commit "2f5bef575d66bab89d7bcb1221ac9bf0ab6b89d2" \ 		 \ 		 \ | Traceback (most recent call last):   File "<frozen runpy>", line 198, in _run_module_as_main   File "<frozen runpy>", line 88, in _run_code   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/scripts/analyze.py", line 18, in <module>     import structlog ModuleNotFoundError: No module named 'structlog' make[1]: *** [analyze] Error 1 |
| `run.evaluate` | fail | high | 116.58 | make evaluate failed | Running programmatic evaluation...
EVAL_OUTPUT_DIR=/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-mq8hb07h /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate \
		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-fy9i5v94/output.json \
		--ground-truth evaluation/ground-truth \
		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-mq8hb07h/evaluation_report.json | Running programmatic evaluation... EVAL_OUTPUT_DIR=/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-mq8hb07h /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate \ 		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-fy9i5v94/output.json \ 		--ground-truth evaluation/ground-truth \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-mq8hb07h/evaluation_report.json | Error: Analysis file not found: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-fy9i5v94/output.json make[1]: *** [evaluate] Error 1 |
| `run.evaluate_llm` | fail | medium | 168.03 | make evaluate-llm failed | Running LLM evaluation (3 judges)...
/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.llm_evaluate \
		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-fy9i5v94/output.json \
		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-n2cxpbme/llm_evaluation.json \
		--model opus-4.5 \
		--programmatic-results evaluation/results/evaluation_report.json | Running LLM evaluation (3 judges)... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.llm_evaluate \ 		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-fy9i5v94/output.json \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-n2cxpbme/llm_evaluation.json \ 		--model opus-4.5 \ 		--programmatic-results evaluation/results/evaluation_report.json | Error: Analysis file not found: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-fy9i5v94/output.json make[1]: *** [evaluate-llm] Error 1 |
| `output.load` | pass | high | 4.23 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/outputs/B6FAEEC8-1FC9-47A2-BD1D-9B3329C3E4C4/output.json | - | - |
| `output.paths` | pass | high | 7.03 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.04 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.2.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | sonarqube, sonarqube | - | - |
| `output.metadata_consistency` | pass | medium | 0.02 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.62 | Output schema_version matches schema constraint | 1.2.0 | - | - |
| `output.schema_validate` | pass | critical | 204.45 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.26 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.21 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.11 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.14 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.09 | analyze target produces output.json | - | - | - |
| `schema.draft` | pass | medium | 0.12 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.76 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.91 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.11 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.21 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.29 | LLM judge count meets minimum (4 >= 4) | issue_accuracy.py, integration_fit.py, actionability.py, coverage_completeness.py | - | - |
| `evaluation.synthetic_context` | pass | high | 11.76 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: issue_accuracy.py, prompt: issue_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.14 | Ground truth files present | java-security.json, typescript-duplication.json, csharp-baseline.json, python-mixed.json, csharp-complex.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.25 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.09 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.39 | LLM evaluation schema valid | timestamp, analysis_path, summary, dimensions, model, score, decision, programmatic_input, combined | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.09 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.06 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.42 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_sonarqube_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.39 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 304.46 | Adapter successfully persisted fixture data | Fixture: sonarqube_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.98 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.41 | Adapter SonarqubeAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.34 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.18 | Tool 'sonarqube' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.29 | dbt staging model(s) found | stg_sonarqube_issues.sql, stg_sonarqube_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.96 | dbt models present for tool | stg_sonarqube_issues.sql, stg_sonarqube_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 14.32 | All entities have aligned repositories | SonarqubeIssue, SonarqubeMetric | - | - |
| `test.structure_naming` | pass | medium | 0.62 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 26.69 | Cross-tool SQL joins use correct patterns (203 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.66 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## symbol-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 1562.98 | make analyze succeeded | - | Running symbol extraction on synthetic... Symbol Scanner v0.1.0  Analyzing synthetic... Repository: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/eval-repos/synthetic  Files analyzed: 25 Symbols found: 609   - Functions: 200   - Classes: 110   - Methods: 286   - Variables: 13 Calls found: 615   - Direct: 306   - Dynamic: 284   - Async: 25   - Resolved: 137     - Same file: 137     - Cross file: 0   - Unresolved: 478 Imports found: 63   - Static: 58   - Dynamic: 0 Errors: 1  Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-0awr5y9j/output.json | - |
| `run.evaluate` | pass | high | 2386.82 | make evaluate succeeded | - | Running programmatic evaluation... Symbol Scanner v0.1.0  Analyzing synthetic... Repository: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/eval-repos/synthetic  Files analyzed: 25 Symbols found: 609   - Functions: 200   - Classes: 110   - Methods: 286   - Variables: 13 Calls found: 615   - Direct: 306   - Dynamic: 284   - Async: 25   - Resolved: 137     - Same file: 137     - Cross file: 0   - Unresolved: 478 Imports found: 63   - Static: 58   - Dynamic: 0 Errors: 1  Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-x9f1tleh/output.json Running evaluation in analysis mode... Ground truth: evaluation/ground-truth Repos dir: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/eval-repos/syntheti… | Warning: Repository csharp-tshock not found at /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/eval-repos/synthetic/csharp-tshock   Minor regression: 99.77% -> 99.07% (within threshold) |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | pass | high | 0.76 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | fail | medium | 178.95 | make evaluate-llm failed | Running LLM evaluation (4 judges)... | Running LLM evaluation (4 judges)... | usage: orchestrator.py [-h] [--analysis ANALYSIS] [--output OUTPUT]                        [--model MODEL]                        [--programmatic-results PROGRAMMATIC_RESULTS]                        [--focused] orchestrator.py: error: unrecognized arguments: --working-dir . make[1]: *** [evaluate-llm] Error 2 |
| `output.load` | pass | high | 4.47 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-x9f1tleh/output.json | - | - |
| `output.paths` | pass | high | 27.64 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.23 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.09 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.02 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.02 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.02 | Tool name matches data.tool | symbol-scanner, symbol-scanner | - | - |
| `output.metadata_consistency` | pass | medium | 0.08 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.82 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 217.79 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.29 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.21 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.12 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.12 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 1.65 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.84 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.13 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.09 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.17 | LLM judge count meets minimum (4 >= 4) | call_relationship.py, import_completeness.py, integration.py, symbol_accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 7.60 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: call_relationship.py, prompt: call_relationship.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.16 | Ground truth files present | metaprogramming.json, csharp-tshock.json, cross-module-calls.json, deep-hierarchy.json, encoding-edge-cases.json, circular-imports.json, type-checking-imports.json, decorators-advanced.json, dynamic-code-generation.json, async-patterns.json, nested-structures.json, class-hierarchy.json, simple-functions.json, generators-comprehensions.json, dataclasses-protocols.json, deep-nesting-stress.json, partial-syntax-errors.json, unresolved-externals.json, confusing-names.json, modern-syntax.json, large-file.json, web-framework-patterns.json, import-patterns.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.80 | Programmatic evaluation schema valid | timestamp, decision, score, checks, summary, aggregate, per_repo_results, metadata, regression | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.44 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.23 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.27 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.10 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.07 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.29 | Rollup Validation declared with valid tests | src/sot-engine/dbt/models/staging/stg_lz_code_symbols.sql | - | - |
| `adapter.compliance` | pass | info | 0.10 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.27 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 182.19 | Adapter successfully persisted fixture data | Fixture: symbol_scanner_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.74 | All 3 quality rules have implementation coverage | paths, ranges, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.39 | Adapter SymbolScannerAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.30 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.17 | Tool 'symbol-scanner' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.28 | dbt staging model(s) found | stg_symbol_calls_file_metrics.sql, stg_symbols_file_metrics.sql, stg_symbol_coupling_metrics.sql, stg_lz_symbol_calls.sql, stg_lz_code_symbols.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.26 | dbt models present for tool | stg_symbol_calls_file_metrics.sql, stg_symbols_file_metrics.sql, stg_symbol_coupling_metrics.sql, stg_lz_symbol_calls.sql, stg_lz_code_symbols.sql | - | - |
| `entity.repository_alignment` | pass | high | 10.39 | All entities have aligned repositories | CodeSymbol, SymbolCall, FileImport | - | - |
| `test.structure_naming` | pass | medium | 2.04 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 25.03 | Cross-tool SQL joins use correct patterns (203 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.40 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## trivy

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | fail | critical | 147.09 | make analyze failed | Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/eval-repos/synthetic as project 'synthetic'
/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \
		--repo-path /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/eval-repos/synthetic \
		--repo-name synthetic \
		--output-dir /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-88dnw6w6 \
		--run-id compliance \
		--repo-id compliance \
		--branch main \
		--commit 2f5bef575d66bab89d7bcb1221ac9bf0ab6b89d2 \
		--timeout 600 | Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/eval-repos/synthetic as project 'synthetic' /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/eval-repos/synthetic \ 		--repo-name synthetic \ 		--output-dir /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-88dnw6w6 \ 		--run-id compliance \ 		--repo-id compliance \ 		--branch main \ 		--commit 2f5bef575d66bab89d7bcb1221ac9bf0ab6b89d2 \ 		--timeout 600 | Traceback (most recent call last):   File "<frozen runpy>", line 198, in _run_module_as_main   File "<frozen runpy>", line 88, in _run_code   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/scripts/analyze.py", line 15, in <module>     import structlog ModuleNotFoundError: No module named 'structlog' make[1]: *** [analyze] Error 1 |
| `run.evaluate` | fail | high | 94.39 | make evaluate failed | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python scripts/evaluate.py --output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-ti8fezea/ | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python scripts/evaluate.py --output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-ti8fezea/ | Traceback (most recent call last):   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/scripts/evaluate.py", line 14, in <module>     import structlog ModuleNotFoundError: No module named 'structlog' make[1]: *** [evaluate] Error 1 |
| `run.evaluate_llm` | fail | medium | 105.11 | make evaluate-llm failed | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator \
		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-88dnw6w6/output.json \
		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-6ez8gcu_/llm_evaluation.json | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator \ 		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-88dnw6w6/output.json \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-6ez8gcu_/llm_evaluation.json | Error: Analysis file does not exist: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-88dnw6w6/output.json make[1]: *** [evaluate-llm] Error 1 |
| `output.load` | pass | high | 2.55 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/outputs/f23f9a48-fb85-4c81-8e04-da14641d23b3/output.json | - | - |
| `output.paths` | pass | high | 0.31 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.04 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | trivy, trivy | - | - |
| `output.metadata_consistency` | pass | medium | 0.02 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.61 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 133.46 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.54 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.31 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.18 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.18 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.13 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.24 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.18 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 1.57 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.51 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.12 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.12 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.14 | LLM judge count meets minimum (7 >= 4) | freshness_quality.py, vulnerability_detection.py, vulnerability_accuracy.py, severity_accuracy.py, iac_quality.py, sbom_completeness.py, false_positive_rate.py | - | - |
| `evaluation.synthetic_context` | pass | high | 14.73 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: vulnerability_accuracy.py, prompt: vulnerability_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.13 | Ground truth files present | dotnet-outdated.json, js-fullstack.json, vulnerable-npm.json, iac-terraform.json, no-vulnerabilities.json, iac-misconfigs.json, mixed-severity.json, java-outdated.json, critical-cves.json, outdated-deps.json, cfn-misconfigs.json, k8s-misconfigs.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.67 | Programmatic evaluation schema valid | timestamp, tool, version, decision, score, classification, overall_score, summary, checks, dimensions | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.26 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.43 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.11 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.09 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.26 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_trivy_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.07 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.42 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 270.04 | Adapter successfully persisted fixture data | Fixture: trivy_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.53 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.41 | Adapter TrivyAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.31 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.17 | Tool 'trivy' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.27 | dbt staging model(s) found | stg_trivy_file_metrics.sql, stg_trivy_iac_misconfigs.sql, stg_trivy_vulnerabilities.sql, stg_trivy_target_metrics.sql, stg_trivy_targets.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.69 | dbt models present for tool | stg_trivy_file_metrics.sql, stg_trivy_iac_misconfigs.sql, stg_trivy_vulnerabilities.sql, stg_trivy_target_metrics.sql, stg_trivy_targets.sql | - | - |
| `entity.repository_alignment` | pass | high | 9.00 | All entities have aligned repositories | TrivyVulnerability, TrivyTarget, TrivyIacMisconfig | - | - |
| `test.structure_naming` | pass | medium | 1.03 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 22.97 | Cross-tool SQL joins use correct patterns (203 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.55 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |
