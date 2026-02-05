# Tool Compliance Report

Generated: `2026-02-05T23:23:53.442072+00:00`

Summary: 1 passed, 13 failed, 14 total

| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |
| --- | --- | --- | --- | --- |
| devskim | fail | 46 | 3 | run.analyze, run.evaluate, run.evaluate_llm |
| dotcover | fail | 52 | 1 | evaluation.results |
| git-sizer | fail | 52 | 1 | output.data_completeness |
| gitleaks | fail | 50 | 3 | evaluation.results, evaluation.quality, evaluation.llm_quality |
| layout-scanner | fail | 52 | 1 | evaluation.results |
| lizard | pass | 53 | 0 | - |
| pmd-cpd | fail | 47 | 2 | run.evaluate, run.evaluate_llm |
| roslyn-analyzers | fail | 52 | 1 | evaluation.results |
| scancode | fail | 51 | 2 | evaluation.results, evaluation.quality |
| scc | fail | 50 | 1 | run.evaluate |
| semgrep | fail | 50 | 3 | evaluation.results, evaluation.llm_quality, evaluation.llm_decision_quality |
| sonarqube | fail | 52 | 1 | evaluation.results |
| symbol-scanner | fail | 50 | 1 | run.evaluate_llm |
| trivy | fail | 49 | 2 | evaluation.quality, run.evaluate_llm |

## Performance Summary

### Slowest Checks

| Tool | Check ID | Duration (ms) |
| --- | --- | --- |
| layout-scanner | `run.evaluate_llm` | 274391.85 |
| scc | `run.evaluate_llm` | 208051.24 |
| sonarqube | `run.analyze` | 159902.65 |
| dotcover | `run.analyze` | 130773.23 |
| roslyn-analyzers | `run.evaluate_llm` | 91086.29 |
| semgrep | `run.evaluate_llm` | 83098.64 |
| git-sizer | `run.evaluate_llm` | 73336.54 |
| gitleaks | `run.evaluate_llm` | 63311.76 |
| lizard | `run.evaluate_llm` | 50401.13 |
| gitleaks | `run.analyze` | 14780.06 |

### Total Time Per Tool

| Tool | Total (s) |
| --- | --- |
| layout-scanner | 275.12 |
| scc | 208.64 |
| sonarqube | 160.77 |
| dotcover | 131.23 |
| roslyn-analyzers | 113.63 |
| semgrep | 89.40 |
| gitleaks | 78.39 |
| git-sizer | 74.75 |
| lizard | 53.66 |
| pmd-cpd | 18.17 |
| scancode | 9.90 |
| trivy | 3.69 |
| symbol-scanner | 2.90 |
| devskim | 0.46 |

## devskim

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | fail | critical | 28.22 | make analyze failed | Checking DevSkim CLI installation... | Checking DevSkim CLI installation... | You must install or update .NET to run this application.  App: /Users/alexander.stage/.dotnet/tools/devskim Architecture: arm64 Framework: 'Microsoft.NETCore.App', version '9.0.0' (arm64) .NET location: /usr/local/share/dotnet  The following frameworks were found:   10.0.1 at [/usr/local/share/dotnet/shared/Microsoft.NETCore.App]  Learn more: https://aka.ms/dotnet/app-launch-failed  To install missing framework, download: https://aka.ms/dotnet-core-applaunch?framework=Microsoft.NETCore.App&framework_version=9.0.0&arch=arm64&rid=osx-arm64&os=osx.15 make[1]: *** [_check-devskim] Error 150 |
| `run.evaluate` | fail | high | 24.10 | make evaluate failed | Checking DevSkim CLI installation... | Checking DevSkim CLI installation... | You must install or update .NET to run this application.  App: /Users/alexander.stage/.dotnet/tools/devskim Architecture: arm64 Framework: 'Microsoft.NETCore.App', version '9.0.0' (arm64) .NET location: /usr/local/share/dotnet  The following frameworks were found:   10.0.1 at [/usr/local/share/dotnet/shared/Microsoft.NETCore.App]  Learn more: https://aka.ms/dotnet/app-launch-failed  To install missing framework, download: https://aka.ms/dotnet-core-applaunch?framework=Microsoft.NETCore.App&framework_version=9.0.0&arch=arm64&rid=osx-arm64&os=osx.15 make[1]: *** [_check-devskim] Error 150 |
| `run.evaluate_llm` | fail | medium | 23.43 | make evaluate-llm failed | Checking DevSkim CLI installation... | Checking DevSkim CLI installation... | You must install or update .NET to run this application.  App: /Users/alexander.stage/.dotnet/tools/devskim Architecture: arm64 Framework: 'Microsoft.NETCore.App', version '9.0.0' (arm64) .NET location: /usr/local/share/dotnet  The following frameworks were found:   10.0.1 at [/usr/local/share/dotnet/shared/Microsoft.NETCore.App]  Learn more: https://aka.ms/dotnet/app-launch-failed  To install missing framework, download: https://aka.ms/dotnet-core-applaunch?framework=Microsoft.NETCore.App&framework_version=9.0.0&arch=arm64&rid=osx-arm64&os=osx.15 make[1]: *** [_check-devskim] Error 150 |
| `output.load` | pass | high | 1.22 | Output JSON loaded | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/devskim/outputs/6e1a36b0-040d-4943-848f-767b01c548ba/output.json | - | - |
| `output.paths` | pass | high | 3.18 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.04 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.17 | Path consistency validated | Checked 161 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | devskim, devskim | - | - |
| `output.metadata_consistency` | pass | medium | 0.07 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.62 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 143.04 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.24 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.15 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.01 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.19 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.13 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.11 | analyze target output pattern acceptable | - | - | - |
| `schema.draft` | pass | medium | 0.11 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.53 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.37 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.02 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.15 | LLM judge count meets minimum (4 >= 4) | rule_coverage.py, severity_calibration.py, security_focus.py, detection_accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 6.27 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: detection_accuracy.py, prompt: detection_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.16 | Ground truth files present | api-security.json, csharp.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.25 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.11 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.02 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.38 | LLM evaluation schema valid | run_id, timestamp, model, score, decision, dimensions, total_score, average_confidence, combined_score, programmatic_input | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.05 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.04 | LLM evaluation passed | WEAK_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.20 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_devskim_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 130.92 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.80 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 48.30 | Adapter successfully persisted fixture data | Fixture: devskim_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.63 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.30 | Adapter DevskimAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.21 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.40 | Tool 'devskim' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.17 | dbt staging model(s) found | stg_lz_devskim_findings.sql, stg_devskim_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.47 | dbt models present for tool | stg_lz_devskim_findings.sql, stg_devskim_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 7.33 | All entities have aligned repositories | DevskimFinding | - | - |
| `test.structure_naming` | pass | medium | 0.40 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 38.85 | Cross-tool SQL joins use correct patterns (158 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.26 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## dotcover

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 130773.23 | make analyze succeeded | - | Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/eval-repos/synthetic as project 'synthetic' /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/eval-repos/synthetic \ 		--repo-name synthetic \ 		--output-dir /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-a5aecnrt \ 		--run-id compliance \ 		--repo-id compliance \ 		--branch main \ 		--commit de062fd7e937bf79f0c0a9b45366d91ef014c7f7 Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/eval-repos/synthetic Found test project: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/dotcover/eval-repos/s… | - |
| `run.evaluate` | pass | high | 80.91 | make evaluate succeeded | - | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate \ 		--results-dir /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-a5aecnrt \ 		--ground-truth-dir evaluation/ground-truth \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-f_k5ji3r/evaluation_report.json Evaluation complete. Decision: PASS Score: 66.7% (2/3 passed) Results saved to /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-f_k5ji3r/evaluation_report.json | - |
| `evaluation.results` | fail | high | - | Missing evaluation outputs | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-f_k5ji3r/scorecard.md | - | - |
| `evaluation.quality` | pass | high | 0.19 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | pass | medium | 53.54 | make evaluate-llm succeeded | - | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator \ 		/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-a5aecnrt \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-ttl32d6t/llm_evaluation.json \ 		--model opus-4.5 \ 		--programmatic-results evaluation/results/evaluation_report.json LLM evaluation complete. Verdict: PASS Results saved to /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-ttl32d6t/llm_evaluation.json | - |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.12 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 0.07 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-a5aecnrt/output.json | - | - |
| `output.paths` | pass | high | 0.14 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.05 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | dotcover, dotcover | - | - |
| `output.metadata_consistency` | pass | medium | 0.02 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.50 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 143.28 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.23 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.16 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.10 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.07 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.05 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.10 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.06 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.67 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.28 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.05 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.15 | LLM judge count meets minimum (4 >= 4) | false_positive.py, actionability.py, integration.py, accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 7.39 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: accuracy.py, prompt: accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.04 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.01 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.07 | Programmatic evaluation schema valid | run_id, timestamp, tool, version, decision, score, summary, dimensions, total_score | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.05 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.04 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.04 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.04 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.18 | Rollup Validation declared with valid tests | src/tools/dotcover/tests/unit/test_analyze.py | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.71 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 115.91 | Adapter successfully persisted fixture data | Fixture: dotcover_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.50 | All 3 quality rules have implementation coverage | coverage_bounds, statement_invariants, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.44 | Adapter DotcoverAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.24 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.40 | Tool 'dotcover' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.20 | dbt staging model(s) found | stg_dotcover_file_metrics.sql, stg_lz_dotcover_type_coverage.sql, stg_lz_dotcover_method_coverage.sql, stg_lz_dotcover_assembly_coverage.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.16 | dbt models present for tool | stg_dotcover_file_metrics.sql, stg_lz_dotcover_type_coverage.sql, stg_lz_dotcover_method_coverage.sql, stg_lz_dotcover_assembly_coverage.sql | - | - |
| `entity.repository_alignment` | pass | high | 6.85 | All entities have aligned repositories | DotcoverAssemblyCoverage, DotcoverTypeCoverage, DotcoverMethodCoverage | - | - |
| `test.structure_naming` | pass | medium | 0.50 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 40.79 | Cross-tool SQL joins use correct patterns (158 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.23 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## git-sizer

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 1112.25 | make analyze succeeded | - | Running repository analysis...   REPO_PATH: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/eval-repos/synthetic   RUN_ID:    compliance   REPO_ID:   compliance   BRANCH:    main   COMMIT:    988008cd161b132ca2aa596b4f0eae76c565ab8c Found 5 git repositories under /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/eval-repos/synthetic Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/eval-repos/synthetic/bloated Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-u7tzb791/bloated/output.json Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/git-sizer/eval-repos/synthetic/deep-history Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/too… | - |
| `run.evaluate` | pass | high | 69.19 | make evaluate succeeded | - | Running programmatic evaluation...  ====================================================================== GIT-SIZER EVALUATION REPORT ======================================================================  Timestamp: 2026-02-06T00:05:45.551581 Analysis:  /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-u7tzb791  ---------------------------------------------------------------------- OVERALL SUMMARY ----------------------------------------------------------------------   Total Checks: 28   Passed:       28 (100.0%)   Failed:       0 (0.0%)   Overall Score: 1.00/1.00   Decision:      STRONG_PASS  ---------------------------------------------------------------------- CATEGORY BREAKDOWN ----------------------------------------------------------------------   ACCURACY         8/… | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | pass | high | 0.16 | Evaluation score meets threshold (computed) | score=1.0, failed=0, total=28 | - | - |
| `run.evaluate_llm` | pass | medium | 73336.54 | make evaluate-llm succeeded | - | Running LLM evaluation...  ====================================================================== GIT-SIZER LLM EVALUATION REPORT ======================================================================  Timestamp: 2026-02-05T23:05:45.671841+00:00 Analysis:  /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-u7tzb791 Model:     opus-4.5  ---------------------------------------------------------------------- SUMMARY ----------------------------------------------------------------------   Weighted Score: 4.55/5.0   Grade:          A   Verdict:        STRONG_PASS  ---------------------------------------------------------------------- JUDGE RESULTS ----------------------------------------------------------------------    SIZE_ACCURACY (weight: 35%)     Score:      5/5 (weighted: 1.… | Running size_accuracy judge...   Score: 5/5 (weight: 35%) Running threshold_quality judge...   Score: 4/5 (weight: 25%) Running actionability judge...   Score: 4/5 (weight: 20%) Running integration_fit judge...   Score: 5/5 (weight: 20%) |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.25 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 0.21 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-u7tzb791/output.json | - | - |
| `output.paths` | pass | high | 0.19 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | fail | high | 0.04 | Data completeness issues detected | violations[0] missing required field: file_path, violations[0] missing required field: rule_id | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | git-sizer, git-sizer | - | - |
| `output.metadata_consistency` | pass | medium | 0.01 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.40 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 129.48 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.20 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.40 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.03 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.10 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.08 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.09 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.06 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.42 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.31 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.05 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.06 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.10 | LLM judge count meets minimum (4 >= 4) | integration_fit.py, size_accuracy.py, actionability.py, threshold_quality.py | - | - |
| `evaluation.synthetic_context` | pass | high | 8.33 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: size_accuracy.py, prompt: size_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.15 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | pass | low | 0.01 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.01 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.23 | Programmatic evaluation schema valid | timestamp, decision, score, analysis_path, ground_truth_dir, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.07 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.09 | LLM evaluation schema valid | timestamp, analysis_path, model, trace_id, judges, summary, programmatic_input, decision, score, dimensions | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.08 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.07 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.17 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_git_sizer_repo_level_only.sql | - | - |
| `adapter.compliance` | pass | info | 0.04 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.76 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 46.50 | Adapter successfully persisted fixture data | Fixture: git_sizer_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.59 | All 3 quality rules have implementation coverage | health_grade_valid, metrics_non_negative, violation_levels | - | - |
| `sot.adapter_registered` | pass | medium | 0.34 | Adapter GitSizerAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.20 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.30 | Tool 'git-sizer' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.17 | dbt staging model(s) found | stg_lz_git_sizer_metrics.sql, stg_lz_git_sizer_violations.sql, stg_lz_git_sizer_lfs_candidates.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.17 | dbt models present for tool | stg_lz_git_sizer_metrics.sql, stg_lz_git_sizer_violations.sql, stg_lz_git_sizer_lfs_candidates.sql | - | - |
| `entity.repository_alignment` | pass | high | 6.44 | All entities have aligned repositories | GitSizerMetric, GitSizerViolation, GitSizerLfsCandidate | - | - |
| `test.structure_naming` | pass | medium | 0.28 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 30.27 | Cross-tool SQL joins use correct patterns (158 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.21 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## gitleaks

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 14780.06 | make analyze succeeded | - | Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/eval-repos/synthetic as project 'synthetic' /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/eval-repos/synthetic \ 		--repo-name synthetic \ 		--output-dir /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-e5iof6s4 \ 		--run-id compliance \ 		--repo-id compliance \ 		--branch main \ 		--commit 988008cd161b132ca2aa596b4f0eae76c565ab8c Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/eval-repos/synthetic Using gitleaks: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/gitleaks/bin/gitleaks Git… | - |
| `run.evaluate` | pass | high | 71.41 | make evaluate succeeded | - | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate \ 		--analysis-dir outputs/runs \ 		--ground-truth-dir evaluation/ground-truth \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-g5b2ed69 Gitleaks PoC Evaluation ============================================================ No analysis files found in outputs/runs Results saved to /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-g5b2ed69/evaluation_report.json | - |
| `evaluation.results` | fail | high | - | Missing evaluation outputs | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-g5b2ed69/scorecard.md | - | - |
| `evaluation.quality` | fail | high | 0.00 | Evaluation results JSON missing | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-g5b2ed69/checks.json, /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-g5b2ed69/evaluation_report.json, /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-g5b2ed69/llm_evaluation.json | - | - |
| `run.evaluate_llm` | pass | medium | 63311.76 | make evaluate-llm succeeded | - | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator \ 		--working-dir . \ 		--programmatic-results evaluation/results/evaluation_report.json \ 		--model opus-4.5 \ 		--evaluation-mode synthetic LLM Evaluation for poc-gitleaks Model: opus-4.5 Working directory: . Evaluation mode: synthetic ============================================================  Running 4 judges...  Running detection_accuracy evaluation...   Score: 1/5 (confidence: 0.99) Running false_positive evaluation...   Score: 3/5 (confidence: 0.50) Running secret_coverage evaluation...   Score: 1/5 (confidence: 0.95) Running severity_classification evaluation...   Score: 1/5 (confidence: 0.95)  ============================================================ RESULTS ============… | <frozen runpy>:128: RuntimeWarning: 'evaluation.llm.orchestrator' found in sys.modules after import of package 'evaluation.llm', but prior to execution of 'evaluation.llm.orchestrator'; this may result in unpredictable behaviour |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | fail | medium | 0.00 | LLM evaluation JSON missing | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-756egg84/llm_evaluation.json | - | - |
| `output.load` | pass | high | 0.63 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-e5iof6s4/output.json | - | - |
| `output.paths` | pass | high | 2.08 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.07 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.07 | Path consistency validated | Checked 49 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | gitleaks, gitleaks | - | - |
| `output.metadata_consistency` | pass | medium | 0.02 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.40 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 128.93 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.19 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.26 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.01 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.08 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.06 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.04 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.09 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.06 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.47 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.51 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.05 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.04 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.09 | LLM judge count meets minimum (4 >= 4) | false_positive.py, secret_coverage.py, detection_accuracy.py, severity_classification.py | - | - |
| `evaluation.synthetic_context` | pass | high | 3.25 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: detection_accuracy.py, prompt: detection_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.03 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.01 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.06 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary, categories | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.04 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.19 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.08 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.05 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.33 | Rollup Validation declared with valid tests | src/tools/gitleaks/tests/unit/test_rollup_invariants.py, src/sot-engine/dbt/tests/test_rollup_gitleaks_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.07 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.63 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 51.08 | Adapter successfully persisted fixture data | Fixture: gitleaks_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.41 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.39 | Adapter GitleaksAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.21 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.31 | Tool 'gitleaks' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.18 | dbt staging model(s) found | stg_gitleaks_secrets.sql, stg_lz_gitleaks_secrets.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.48 | dbt models present for tool | stg_gitleaks_secrets.sql, stg_lz_gitleaks_secrets.sql | - | - |
| `entity.repository_alignment` | pass | high | 6.18 | All entities have aligned repositories | GitleaksSecret | - | - |
| `test.structure_naming` | pass | medium | 0.33 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 31.38 | Cross-tool SQL joins use correct patterns (158 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.41 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## layout-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 164.77 | make analyze succeeded | - | Setup complete! Scanning synthetic... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner/eval-repos/synthetic" \ 		--repo-name "synthetic" \ 		--output-dir "/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-kdr_ws5e" \ 		--run-id "compliance" \ 		--repo-id "compliance" \ 		--branch "main" \ 		 \ 		--commit "988008cd161b132ca2aa596b4f0eae76c565ab8c" Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner/eval-repos/synthetic Files found: 143 Directories: 79 Scan duration: 16ms Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-kdr_ws5e/output.json | - |
| `run.evaluate` | pass | high | 199.68 | make evaluate succeeded | - | Setup complete! EVAL_OUTPUT_DIR=/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-4vh1c8kg /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate Evaluating output.json...   Score: 4.75/5.0 - STRONG_PASS   Checks: 33/36 passed  Results saved to /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-4vh1c8kg/evaluation_report.json  Aggregate: 4.75/5.0 - STRONG_PASS | - |
| `evaluation.results` | fail | high | - | Missing evaluation outputs | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-4vh1c8kg/checks.json | - | - |
| `evaluation.quality` | pass | high | 0.24 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 274391.85 | make evaluate-llm succeeded | - | Setup complete! /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator \ 		--working-dir /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/layout-scanner \ 		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-kdr_ws5e/output.json \ 		--model opus-4.5 \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-f2s559lm/llm_evaluation.json \ 		--programmatic-results evaluation/results/evaluation_report.json Running full evaluation (4 judges)... Running classification_reasoning evaluation...   Score: 4/5 (confidence: 0.82) Running directory_taxonomy evaluation...   Score: 3/5 (confidence: 0.88) Running hierarchy_consistency evaluation...   Score: 3/5 (confidence: 0.50) Runnin… | <frozen runpy>:128: RuntimeWarning: 'evaluation.llm.orchestrator' found in sys.modules after import of package 'evaluation.llm', but prior to execution of 'evaluation.llm.orchestrator'; this may result in unpredictable behaviour |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.30 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 1.25 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-kdr_ws5e/output.json | - | - |
| `output.paths` | pass | high | 9.44 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.10 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.02 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.02 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.02 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.02 | Tool name matches data.tool | layout-scanner, layout-scanner | - | - |
| `output.metadata_consistency` | pass | medium | 0.02 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.68 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 232.96 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.32 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.06 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.11 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.10 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.05 | analyze target output pattern acceptable | - | - | - |
| `schema.draft` | pass | medium | 0.14 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.10 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.57 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.75 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.10 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.12 | LLM judge count meets minimum (4 >= 4) | classification_reasoning.py, hierarchy_consistency.py, language_detection.py, directory_taxonomy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 6.24 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: classification_reasoning.py, prompt: classification_reasoning.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.08 | Ground truth files present | mixed-language.json, edge-cases.json, generated-code.json, config-heavy.json, vendor-heavy.json, small-clean.json, deep-nesting.json, mixed-types.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.66 | Programmatic evaluation schema valid | timestamp, decision, score, evaluated_count, average_score, summary, checks, repositories | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.48 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.08 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.06 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.05 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.33 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_layout_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.08 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.90 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 58.37 | Adapter successfully persisted fixture data | Fixture: layout_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.73 | All 3 quality rules have implementation coverage | paths, ranges, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.48 | Adapter LayoutAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.22 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.00 | layout-scanner handled specially as prerequisite tool | Layout is ingested before TOOL_INGESTION_CONFIGS loop | - | - |
| `sot.dbt_staging_model` | pass | high | 0.20 | dbt staging model(s) found | stg_lz_layout_files.sql, stg_lz_layout_directories.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.51 | dbt models present for tool | stg_lz_layout_files.sql, stg_lz_layout_directories.sql | - | - |
| `entity.repository_alignment` | pass | high | 6.66 | All entities have aligned repositories | LayoutFile, LayoutDirectory | - | - |
| `test.structure_naming` | pass | medium | 0.79 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 38.74 | Cross-tool SQL joins use correct patterns (158 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.40 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## lizard

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 444.28 | make analyze succeeded | - | Running function analysis on synthetic... Lizard version: lizard 1.20.0  Analyzing synthetic...   Analyzing 63 files with 8 threads...  Files analyzed: 63 Functions found: 529 Total CCN: 1358 Avg CCN: 2.57 Max CCN: 26 Functions over threshold: 20 Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-tak03mro/output.json | - |
| `run.evaluate` | pass | high | 2464.77 | make evaluate succeeded | - | Running programmatic evaluation (76 checks)... Lizard version: lizard 1.20.0  Analyzing synthetic...   Analyzing 63 files with 8 threads...  Files analyzed: 63 Functions found: 529 Total CCN: 1358 Avg CCN: 2.57 Max CCN: 26 Functions over threshold: 20 Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-w7324k8a/output.json  ================================================================================   LIZARD EVALUATION REPORT ================================================================================    Timestamp: 2026-02-05T23:12:55.543123+00:00   Analysis:  /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-w7324k8a/output.json   Ground Truth: evaluation/ground-truth  -------------------------------------------------------------------… | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | pass | high | 0.43 | Evaluation score meets threshold (computed) | score=0.986, failed=0, total=None | - | - |
| `run.evaluate_llm` | pass | medium | 50401.13 | make evaluate-llm succeeded | - | Running LLM evaluation (4 judges)...  ============================================================ LLM Evaluation - Lizard Function Complexity Analysis ============================================================  Running ccn_accuracy evaluation...   Ground truth assertions failed: 1 failures   Score: 2/5 (confidence: 0.45) Running function_detection evaluation...   Ground truth assertions failed: 1 failures   Score: 1/5 (confidence: 0.95) Running statistics evaluation...   Ground truth assertions failed: 1 failures   Score: 1/5 (confidence: 0.95) Running hotspot_ranking evaluation...   Ground truth assertions failed: 1 failures   Score: 1/5 (confidence: 0.95)  ============================================================ EVALUATION SUMMARY ==================================================… | <frozen runpy>:128: RuntimeWarning: 'evaluation.llm.orchestrator' found in sys.modules after import of package 'evaluation.llm', but prior to execution of 'evaluation.llm.orchestrator'; this may result in unpredictable behaviour |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.32 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 2.06 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-w7324k8a/output.json | - | - |
| `output.paths` | pass | high | 11.11 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.07 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.10 | Path consistency validated | Checked 85 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | lizard, lizard | - | - |
| `output.metadata_consistency` | pass | medium | 0.03 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.66 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 179.85 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.96 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.59 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.08 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.09 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.05 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.14 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.09 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.58 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.60 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.07 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.12 | LLM judge count meets minimum (4 >= 4) | hotspot_ranking.py, ccn_accuracy.py, function_detection.py, statistics.py | - | - |
| `evaluation.synthetic_context` | pass | high | 7.75 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: ccn_accuracy.py, prompt: ccn_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.18 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | pass | low | 0.01 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.60 | Programmatic evaluation schema valid | timestamp, decision, score, analysis_path, ground_truth_path, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.26 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.07 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.06 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.05 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.28 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_lizard_direct_distribution_ranges.sql, src/sot-engine/dbt/tests/test_rollup_lizard_direct_vs_recursive.sql, src/sot-engine/dbt/tests/test_rollup_lizard_distribution_ranges.sql | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.88 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 86.68 | Adapter successfully persisted fixture data | Fixture: lizard_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.63 | All 3 quality rules have implementation coverage | paths, ranges, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.53 | Adapter LizardAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.23 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.41 | Tool 'lizard' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.20 | dbt staging model(s) found | stg_lz_lizard_file_metrics.sql, stg_lz_lizard_function_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.49 | dbt models present for tool | stg_lz_lizard_file_metrics.sql, stg_lz_lizard_function_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 7.04 | All entities have aligned repositories | LizardFileMetric, LizardFunctionMetric | - | - |
| `test.structure_naming` | pass | medium | 0.66 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 42.42 | Cross-tool SQL joins use correct patterns (158 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.42 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## pmd-cpd

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 5859.05 | make analyze succeeded | - | Java found: /opt/homebrew/opt/openjdk@17/bin/java Running CPD analysis on synthetic... Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/eval-repos/synthetic... Analysis complete: 39 clones found Output written to: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-u7pgusvs/output.json Warnings: 1   - CPD error for rust: Invalid value for option '--language': Unknown language: rust Usage: pmd cpd [-Dh] [--ignore-annotations] [--ignore-identifiers]                [--ignore-literal-sequences] [--ignore-literals] | - |
| `run.evaluate` | fail | high | 6006.03 | make evaluate failed | Java found: /opt/homebrew/opt/openjdk@17/bin/java
Running CPD analysis on synthetic...
Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/eval-repos/synthetic...
Analysis complete: 39 clones found
Output written to: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-u7pgusvs/output.json
Warnings: 1
  - CPD error for rust: Invalid value for option '--language': Unknown language: rust
Usage: pmd cpd [-Dh] [--ignore-annotations] [--ignore-identifiers]
               [--ignore-literal-sequences] [--ignore-literals]
       
Running programmatic evaluation (~28 checks)...
======================================================================
PMD CPD EVALUATION REPORT
======================================================================

Analysis… | Java found: /opt/homebrew/opt/openjdk@17/bin/java Running CPD analysis on synthetic... Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/eval-repos/synthetic... Analysis complete: 39 clones found Output written to: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-u7pgusvs/output.json Warnings: 1   - CPD error for rust: Invalid value for option '--language': Unknown language: rust Usage: pmd cpd [-Dh] [--ignore-annotations] [--ignore-identifiers]                [--ignore-literal-sequences] [--ignore-literals]         Running programmatic evaluation (~28 checks)... ====================================================================== PMD CPD EVALUATION REPORT ======================================================================  Analysis… | make[1]: *** [evaluate] Error 1 |
| `run.evaluate_llm` | fail | medium | 5871.44 | make evaluate-llm failed | Java found: /opt/homebrew/opt/openjdk@17/bin/java
Running CPD analysis on synthetic...
Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/eval-repos/synthetic...
Analysis complete: 39 clones found
Output written to: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-u7pgusvs/output.json
Warnings: 1
  - CPD error for rust: Invalid value for option '--language': Unknown language: rust
Usage: pmd cpd [-Dh] [--ignore-annotations] [--ignore-identifiers]
               [--ignore-literal-sequences] [--ignore-literals]
       
Running LLM evaluation (4 judges)... | Java found: /opt/homebrew/opt/openjdk@17/bin/java Running CPD analysis on synthetic... Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/eval-repos/synthetic... Analysis complete: 39 clones found Output written to: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-u7pgusvs/output.json Warnings: 1   - CPD error for rust: Invalid value for option '--language': Unknown language: rust Usage: pmd cpd [-Dh] [--ignore-annotations] [--ignore-identifiers]                [--ignore-literal-sequences] [--ignore-literals]         Running LLM evaluation (4 judges)... | Traceback (most recent call last):   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/scripts/llm_evaluate.py", line 348, in <module>     main()   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/scripts/llm_evaluate.py", line 271, in main     report = run_llm_evaluation(              ^^^^^^^^^^^^^^^^^^^   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/pmd-cpd/scripts/llm_evaluate.py", line 93, in run_llm_evaluation     DuplicationAccuracyJudge( TypeError: BaseJudge.__init__() got an unexpected keyword argument 'analysis_path' make[1]: *** [evaluate-llm] Error 1 |
| `output.load` | pass | high | 0.55 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-u7pgusvs/output.json | - | - |
| `output.paths` | pass | high | 1.92 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.04 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.09 | Path consistency validated | Checked 49 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | pmd-cpd, pmd-cpd | - | - |
| `output.metadata_consistency` | pass | medium | 0.03 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.55 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 215.13 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.29 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.29 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.10 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.30 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.39 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.18 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.21 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.18 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.60 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.77 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.08 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.07 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.13 | LLM judge count meets minimum (4 >= 4) | duplication_accuracy.py, actionability.py, semantic_detection.py, cross_file_detection.py | - | - |
| `evaluation.synthetic_context` | pass | high | 5.16 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: duplication_accuracy.py, prompt: duplication_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.21 | Ground truth covers synthetic repos | - | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.17 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.37 | Programmatic evaluation schema valid | timestamp, analysis_path, ground_truth_dir, decision, score, summary, checks | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.19 | Programmatic evaluation passed | WEAK_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.03 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.20 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, combined_score, notes | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.06 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=WEAK_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.05 | LLM evaluation passed | WEAK_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.38 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_pmd_cpd_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.38 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 155.70 | Adapter successfully persisted fixture data | Fixture: pmd_cpd_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.28 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.44 | Adapter PmdCpdAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.29 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.41 | Tool 'pmd-cpd' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.27 | dbt staging model(s) found | stg_lz_pmd_cpd_duplications.sql, stg_lz_pmd_cpd_occurrences.sql, stg_lz_pmd_cpd_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.76 | dbt models present for tool | stg_lz_pmd_cpd_duplications.sql, stg_lz_pmd_cpd_occurrences.sql, stg_lz_pmd_cpd_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 8.62 | All entities have aligned repositories | PmdCpdFileMetric, PmdCpdDuplication, PmdCpdOccurrence | - | - |
| `test.structure_naming` | pass | medium | 0.72 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 38.24 | Cross-tool SQL joins use correct patterns (158 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.29 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## roslyn-analyzers

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 14016.30 | make analyze succeeded | - | Building external repo: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/eval-repos/synthetic... MSBUILD : error MSB1003: Specify a project or solution file. The current working directory does not contain a project or solution file. MSBUILD : error MSB1003: Specify a project or solution file. The current working directory does not contain a project or solution file. Build completed (some errors may be expected) Running Roslyn analysis... Building AsyncPatterns.csproj...   Found 150 violations Building NullSafety.csproj...   Found 83 violations Building ApiConventions.csproj...   Found 1 violations Building SyntheticSmells.csproj...   Found 1051 violations Building ResourceManagement.csproj...   Found 6 violations  =======================================… | - |
| `run.evaluate` | pass | high | 8061.05 | make evaluate succeeded | - | Building external repo: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/eval-repos/synthetic... MSBUILD : error MSB1003: Specify a project or solution file. The current working directory does not contain a project or solution file. MSBUILD : error MSB1003: Specify a project or solution file. The current working directory does not contain a project or solution file. Build completed (some errors may be expected) Running Roslyn analysis... Building AsyncPatterns.csproj...   Found 150 violations Building NullSafety.csproj...   Found 83 violations Building ApiConventions.csproj...   Found 1 violations Building SyntheticSmells.csproj...   Found 1051 violations Building ResourceManagement.csproj...   Found 6 violations  =======================================… | - |
| `evaluation.results` | fail | high | - | Missing evaluation outputs | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-2yx809vt/checks.json | - | - |
| `evaluation.quality` | pass | high | 0.31 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 91086.29 | make evaluate-llm succeeded | - | Building external repo: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/roslyn-analyzers/eval-repos/synthetic... MSBUILD : error MSB1003: Specify a project or solution file. The current working directory does not contain a project or solution file. MSBUILD : error MSB1003: Specify a project or solution file. The current working directory does not contain a project or solution file. Build completed (some errors may be expected) Running Roslyn analysis... Building AsyncPatterns.csproj...   Found 150 violations Building NullSafety.csproj...   Found 83 violations Building ApiConventions.csproj...   Found 1 violations Building SyntheticSmells.csproj...   Found 1051 violations Building ResourceManagement.csproj...   Found 6 violations  =======================================… | - |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.29 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 2.34 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-hs5fgawi/output.json | - | - |
| `output.paths` | pass | high | 19.85 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.08 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.09 | Path consistency validated | Checked 62 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | roslyn-analyzers, roslyn-analyzers | - | - |
| `output.metadata_consistency` | pass | medium | 0.03 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.42 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 231.00 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.27 | All required paths present | - | - | - |
| `make.targets` | pass | high | 1.45 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.04 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.13 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.12 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.08 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.12 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.40 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.77 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.07 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.13 | LLM judge count meets minimum (5 >= 4) | overall_quality.py, integration_fit.py, resource_management.py, security_detection.py, design_analysis.py | - | - |
| `evaluation.synthetic_context` | pass | high | 12.82 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: security_detection.py, prompt: security_detection.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.09 | Ground truth files present | clean-code.json, resource-management.json, dead-code.json, csharp.json, security-issues.json, design-violations.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.24 | Programmatic evaluation schema valid | evaluation_id, timestamp, analysis_file, decision, score, summary, category_scores, checks, decision_reason | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.09 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.08 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.08 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.07 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.38 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_roslyn_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.07 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.03 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 140.09 | Adapter successfully persisted fixture data | Fixture: roslyn_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.61 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.55 | Adapter RoslynAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.25 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.45 | Tool 'roslyn-analyzers' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.22 | dbt staging model(s) found | stg_lz_roslyn_violations.sql, stg_roslyn_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.72 | dbt models present for tool | stg_lz_roslyn_violations.sql, stg_roslyn_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 8.06 | All entities have aligned repositories | RoslynViolation | - | - |
| `test.structure_naming` | pass | medium | 0.56 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 40.25 | Cross-tool SQL joins use correct patterns (158 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.35 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## scancode

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 227.19 | make analyze succeeded | - | Running license analysis on synthetic... Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/eval-repos/synthetic Licenses found: ['Apache-2.0', 'BSD-3-Clause', 'GPL-2.0-only WITH Classpath-exception-2.0', 'GPL-3.0-only', 'LGPL-2.1-only', 'MIT', 'Unlicense'] Overall risk: critical Files with licenses: 23 Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-mmnji1m5/output.json | - |
| `run.evaluate` | pass | high | 120.50 | make evaluate succeeded | - | Running programmatic evaluation... License Analysis Evaluation ============================================================  no-license: 32/32 (PASS) apache-bsd: 32/32 (PASS) mit-only: 32/32 (PASS) apache-bsd: 32/32 (PASS) gpl-mixed: 32/32 (PASS) multi-license: 32/32 (PASS)  ============================================================ Summary ============================================================ Repositories evaluated: 6 Total checks: 192 Passed: 192 Failed: 0 Overall pass rate: 100.0%  Scorecard saved to: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/evaluation/scorecard.json Markdown scorecard saved to: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/evaluation/scorecard.md  Results saved to: evaluation/results/evaluati… | - |
| `evaluation.results` | fail | high | - | Missing evaluation outputs | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-0b3x818v/scorecard.md | - | - |
| `evaluation.quality` | fail | high | 0.00 | Evaluation results JSON missing | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-0b3x818v/checks.json, /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-0b3x818v/evaluation_report.json, /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-0b3x818v/llm_evaluation.json | - | - |
| `run.evaluate_llm` | pass | medium | 9284.88 | make evaluate-llm succeeded | - | Running LLM-as-a-Judge evaluation... LLM Evaluation for scancode Model: opus-4.5 Working directory: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode ============================================================  Running 4 judges...  Running accuracy evaluation...   Score: 3/5 (confidence: 0.50) Running coverage evaluation...   Score: 3/5 (confidence: 0.50) Running actionability evaluation...   Score: 3/5 (confidence: 0.50) Running risk_classification evaluation...   Score: 3/5 (confidence: 0.50)  ============================================================ RESULTS ============================================================ Total Score: 3.00 Decision: WEAK_PASS  Results saved to: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scancode/evalu… | - |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.65 | LLM evaluation decision meets threshold | WEAK_PASS | - | - |
| `output.load` | pass | high | 0.33 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-mmnji1m5/output.json | - | - |
| `output.paths` | pass | high | 1.18 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.08 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.04 | Path consistency validated | Checked 23 paths across 1 sections | - | - |
| `output.required_fields` | pass | high | 0.02 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.02 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.02 | Tool name matches data.tool | scancode, scancode | - | - |
| `output.metadata_consistency` | pass | medium | 0.02 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.42 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 119.22 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.23 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.14 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.01 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.08 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.07 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.09 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.07 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.51 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.35 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.06 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.06 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.12 | LLM judge count meets minimum (4 >= 4) | coverage_judge.py, accuracy_judge.py, actionability_judge.py, risk_classification_judge.py | - | - |
| `evaluation.synthetic_context` | pass | high | 3.53 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: accuracy_judge.py, prompt: accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.07 | Ground truth files present | multi-license.json, mit-only.json, gpl-mixed.json, apache-bsd.json, public-domain.json, spdx-expression.json, no-license.json, dual-licensed.json | - | - |
| `evaluation.scorecard` | pass | low | 0.01 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.41 | Programmatic evaluation schema valid | timestamp, tool, version, decision, score, summary, checks, total_repositories, reports | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.33 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.03 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.85 | LLM evaluation schema valid | run_id, timestamp, model, dimensions, score, total_score, average_confidence, decision, programmatic_score, combined_score | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.58 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.54 | LLM evaluation passed | WEAK_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.16 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_scancode_repo_level_metrics.sql | - | - |
| `adapter.compliance` | pass | info | 0.09 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.66 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 85.97 | Adapter successfully persisted fixture data | Fixture: scancode_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.58 | All 3 quality rules have implementation coverage | paths, confidence, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.42 | Adapter ScancodeAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.24 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.36 | Tool 'scancode' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.27 | dbt staging model(s) found | stg_lz_scancode_summary.sql, stg_lz_scancode_file_licenses.sql, stg_scancode_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.18 | dbt models present for tool | stg_lz_scancode_summary.sql, stg_lz_scancode_file_licenses.sql, stg_scancode_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 7.75 | All entities have aligned repositories | ScancodeFileLicense, ScancodeSummary | - | - |
| `test.structure_naming` | pass | medium | 0.32 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 33.87 | Cross-tool SQL joins use correct patterns (158 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.36 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## scc

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 168.13 | make analyze succeeded | - | Running directory analysis on synthetic... Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/eval-repos/synthetic Using scc: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/bin/scc Files found: 63 Total files: 63 Total lines: 7,666 Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-20fpxmxi/output.json | - |
| `run.evaluate` | fail | high | 109.44 | make evaluate failed | Running programmatic evaluation... | Running programmatic evaluation... | Traceback (most recent call last):   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/scripts/evaluate.py", line 17, in <module>     from scripts.analyze import _resolve_commit ImportError: cannot import name '_resolve_commit' from 'scripts.analyze' (/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc/scripts/analyze.py) make[1]: *** [evaluate] Error 1 |
| `run.evaluate_llm` | pass | medium | 208051.24 | make evaluate-llm succeeded | - | Running LLM-as-a-Judge evaluation... ============================================================ LLM-as-a-Judge Evaluation ============================================================ Mode: full Model: opus-4.5 Working Directory: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/scc ============================================================  Registering all judges (10 dimensions)...  Running code_quality evaluation...   Score: 4/5 (confidence: 0.85) Running integration_fit evaluation...   Score: 4/5 (confidence: 0.92) Running documentation evaluation...   Score: 4/5 (confidence: 0.82) Running edge_cases evaluation...   Score: 4/5 (confidence: 0.82) Running error_messages evaluation...   Score: 4/5 (confidence: 0.85) Running api_design evaluation...   Score: 4/5 (confi… | - |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.44 | LLM evaluation decision meets threshold | STRONG_PASS | - | - |
| `output.load` | pass | high | 1.05 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-20fpxmxi/output.json | - | - |
| `output.paths` | pass | high | 4.94 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.08 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.11 | Path consistency validated | Checked 94 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | scc, scc | - | - |
| `output.metadata_consistency` | pass | medium | 0.02 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.55 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 148.59 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.80 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.49 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.08 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.07 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.11 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.75 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.56 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.12 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.10 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.11 | LLM judge count meets minimum (10 >= 4) | error_messages.py, documentation.py, edge_cases.py, directory_analysis.py, integration_fit.py, code_quality.py, risk.py, statistics.py, comparative.py, api_design.py | - | - |
| `evaluation.synthetic_context` | pass | high | 9.81 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: directory_analysis.py, prompt: directory_analysis.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.03 | synthetic.json ground truth present | - | - | - |
| `evaluation.scorecard` | pass | low | 0.01 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.17 | Programmatic evaluation schema valid | run_id, timestamp, dimensions, total_score, decision | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.14 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.12 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.09 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.09 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.28 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_scc_direct_distribution_ranges.sql, src/sot-engine/dbt/tests/test_rollup_scc_direct_vs_recursive.sql, src/sot-engine/dbt/tests/test_rollup_scc_distribution_ranges.sql | - | - |
| `adapter.compliance` | pass | info | 0.07 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.78 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 90.52 | Adapter successfully persisted fixture data | Fixture: scc_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 1.31 | All 4 quality rules have implementation coverage | paths, ranges, ratios, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.57 | Adapter SccAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.20 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.45 | Tool 'scc' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.20 | dbt staging model(s) found | stg_lz_scc_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.50 | dbt models present for tool | stg_lz_scc_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 6.55 | All entities have aligned repositories | SccFileMetric | - | - |
| `test.structure_naming` | pass | medium | 0.39 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 38.46 | Cross-tool SQL joins use correct patterns (158 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.36 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## semgrep

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 5664.80 | make analyze succeeded | - | SKIP_SETUP=1: skipping semgrep install Initializing real repositories... Initializing Elttam audit rules...   Elttam rules already present Setup complete! Analyzing synthetic... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/eval-repos/synthetic" \ 		--repo-name "synthetic" \ 		--output-dir "/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-tbo8fkk4" \ 		--run-id "compliance" \ 		--repo-id "compliance" \ 		--branch "main" \ 		--commit "988008cd161b132ca2aa596b4f0eae76c565ab8c" Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/eval-repos/synthetic Files analyzed: 58 Smells found: 193 Duration: 4304m… | - |
| `run.evaluate` | pass | high | 247.66 | make evaluate succeeded | - | SKIP_SETUP=1: skipping semgrep install Initializing real repositories... Initializing Elttam audit rules...   Elttam rules already present Setup complete! Running programmatic evaluation (~28 checks)... EVAL_OUTPUT_DIR=/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-llj54zpn /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate \ 		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-tbo8fkk4/output.json \ 		--ground-truth evaluation/ground-truth \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-llj54zpn/evaluation_report.json  [36m======================================================================[0m [36m[1m  SEMGREP EVALUATION REPORT[0m [36m====================… | - |
| `evaluation.results` | fail | high | - | Missing evaluation outputs | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-llj54zpn/checks.json | - | - |
| `evaluation.quality` | pass | high | 0.13 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 83098.64 | make evaluate-llm succeeded | - | SKIP_SETUP=1: skipping semgrep install Initializing real repositories... Initializing Elttam audit rules...   Elttam rules already present Setup complete! Analyzing synthetic... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/eval-repos/synthetic" \ 		--repo-name "synthetic" \ 		--output-dir "/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-tbo8fkk4" \ 		--run-id "compliance" \ 		--repo-id "compliance" \ 		--branch "main" \ 		--commit "988008cd161b132ca2aa596b4f0eae76c565ab8c" Analyzing: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/eval-repos/synthetic Files analyzed: 58 Smells found: 193 Duration: 3466m… | [DEBUG] Looking for analysis files in: outputs   [DEBUG] Found 12 JSON files   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Looking for analysis files in: outputs   [DEBUG] Found 12 JSON files   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Loaded: output.json   [DEBUG] Load… |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | fail | medium | 0.39 | LLM evaluation decision below required threshold | FAIL | - | - |
| `output.load` | pass | high | 0.98 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-tbo8fkk4/output.json | - | - |
| `output.paths` | pass | high | 5.42 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.09 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.09 | Path consistency validated | Checked 65 paths across 2 sections | - | - |
| `output.required_fields` | pass | high | 0.02 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.02 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.02 | Tool name matches data.tool | semgrep, semgrep | - | - |
| `output.metadata_consistency` | pass | medium | 0.02 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.67 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 181.79 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.24 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.39 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.09 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.10 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target output pattern acceptable | - | - | - |
| `schema.draft` | pass | medium | 0.12 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.65 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.78 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.09 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.07 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.13 | LLM judge count meets minimum (5 >= 4) | rule_coverage.py, actionability.py, security_detection.py, smell_accuracy.py, false_positive_rate.py | - | - |
| `evaluation.synthetic_context` | pass | high | 20.18 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: security_detection.py, prompt: security_detection.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.10 | Ground truth files present | java.json, go.json, csharp.json, rust.json, javascript.json, typescript.json, python.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.19 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.05 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.09 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, analysis_path, combined | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.08 | LLM evaluation includes programmatic input | file=/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/semgrep/evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | fail | medium | 0.07 | LLM evaluation failed | FAIL | - | - |
| `evaluation.rollup_validation` | pass | high | 0.27 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_semgrep_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.03 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.59 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 127.30 | Adapter successfully persisted fixture data | Fixture: semgrep_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.53 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.48 | Adapter SemgrepAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.24 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.50 | Tool 'semgrep' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.20 | dbt staging model(s) found | stg_semgrep_file_metrics.sql, stg_lz_semgrep_smells.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.55 | dbt models present for tool | stg_semgrep_file_metrics.sql, stg_lz_semgrep_smells.sql | - | - |
| `entity.repository_alignment` | pass | high | 6.39 | All entities have aligned repositories | SemgrepSmell | - | - |
| `test.structure_naming` | pass | medium | 0.70 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 36.87 | Cross-tool SQL joins use correct patterns (158 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.37 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## sonarqube

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 159902.65 | make analyze succeeded | - | Analyzing synthetic... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/eval-repos/synthetic \ 		--project-key synthetic \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-ndg8e3cy/output.json \ 		--sonarqube-url http://localhost:9000 \ 		--run-id "compliance" \ 		--repo-id "compliance" \ 		--branch "main" \ 		--commit "988008cd161b132ca2aa596b4f0eae76c565ab8c" \ 		 \ 		 \ 		 [2m2026-02-05T23:21:08.296614Z[0m [[32m[1minfo     [0m] [1mStarting SonarQube container  [0m [36mcompose_file[0m=[35m/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/sonarqube/docker-compose.yml[0m [2m2026-02-05T23:21:08.826699Z[0m [[3… | - |
| `run.evaluate` | pass | high | 210.75 | make evaluate succeeded | - | Running programmatic evaluation... EVAL_OUTPUT_DIR=/var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-ie3vfbp4 /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.evaluate \ 		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-ndg8e3cy/output.json \ 		--ground-truth evaluation/ground-truth \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-ie3vfbp4/evaluation_report.json [36m[1m Running programmatic evaluation...[0m  [35m======================================================================[0m [35m[1m  SONARQUBE EVALUATION REPORT[0m [35m======================================================================[0m  [34m[1mSUMMARY[0m [34m-----------------------------------… | - |
| `evaluation.results` | fail | high | - | Missing evaluation outputs | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-ie3vfbp4/checks.json | - | - |
| `evaluation.quality` | pass | high | 0.38 | Evaluation decision meets threshold | STRONG_PASS | - | - |
| `run.evaluate_llm` | pass | medium | 212.53 | make evaluate-llm succeeded | - | Running LLM evaluation (3 judges)... /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.llm_evaluate \ 		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-ndg8e3cy/output.json \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-540dqx79/llm_evaluation.json \ 		--model opus-4.5 \ 		--programmatic-results evaluation/results/evaluation_report.json [36m[1m Running LLM evaluation...[0m   Running issue_accuracy judge... [31m2/5[0m (conf: 80%)   Running coverage_completeness judge... [32m5/5[0m (conf: 85%)   Running actionability judge... [32m5/5[0m (conf: 75%)  [35m======================================================================[0m [35m[1m  SONARQUBE LLM EVALUATION REPORT[0m [35m====… | - |
| `evaluation.llm_results` | pass | medium | - | LLM evaluation output present | - | - | - |
| `evaluation.llm_quality` | pass | medium | 0.17 | LLM evaluation decision meets threshold | PASS | - | - |
| `output.load` | pass | high | 1.75 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-ndg8e3cy/output.json | - | - |
| `output.paths` | pass | high | 10.32 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.07 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.01 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.2.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | sonarqube, sonarqube | - | - |
| `output.metadata_consistency` | pass | medium | 0.02 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.48 | Output schema_version matches schema constraint | 1.2.0 | - | - |
| `output.schema_validate` | pass | critical | 156.98 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.24 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.19 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.11 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.12 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.07 | analyze target produces output.json | - | - | - |
| `schema.draft` | pass | medium | 0.10 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.06 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 0.66 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.85 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.10 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.14 | LLM judge count meets minimum (4 >= 4) | issue_accuracy.py, integration_fit.py, actionability.py, coverage_completeness.py | - | - |
| `evaluation.synthetic_context` | pass | high | 9.40 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: issue_accuracy.py, prompt: issue_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.11 | Ground truth files present | java-security.json, typescript-duplication.json, csharp-baseline.json, python-mixed.json, csharp-complex.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.02 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.07 | Programmatic evaluation schema valid | timestamp, tool, decision, score, checks, summary | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.05 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.01 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.06 | LLM evaluation schema valid | timestamp, analysis_path, summary, dimensions, model, score, decision, programmatic_input, combined | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.06 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.04 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.72 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_sonarqube_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.09 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 2.07 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 209.76 | Adapter successfully persisted fixture data | Fixture: sonarqube_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.53 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.57 | Adapter SonarqubeAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.25 | Schema tables found for tool | Found 2 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.51 | Tool 'sonarqube' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.26 | dbt staging model(s) found | stg_sonarqube_issues.sql, stg_sonarqube_file_metrics.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.65 | dbt models present for tool | stg_sonarqube_issues.sql, stg_sonarqube_file_metrics.sql | - | - |
| `entity.repository_alignment` | pass | high | 8.26 | All entities have aligned repositories | SonarqubeIssue, SonarqubeMetric | - | - |
| `test.structure_naming` | pass | medium | 0.42 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 39.87 | Cross-tool SQL joins use correct patterns (158 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.37 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## symbol-scanner

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 850.53 | make analyze succeeded | - | Running symbol extraction on synthetic... Symbol Scanner v0.1.0  Analyzing synthetic... Repository: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/eval-repos/synthetic  Files analyzed: 25 Symbols found: 609   - Functions: 200   - Classes: 110   - Methods: 286   - Variables: 13 Calls found: 615   - Direct: 306   - Dynamic: 284   - Async: 25   - Resolved: 137     - Same file: 137     - Cross file: 0   - Unresolved: 478 Imports found: 63   - Static: 58   - Dynamic: 0 Errors: 1  Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-m6z4zn_b/output.json | - |
| `run.evaluate` | pass | high | 1602.90 | make evaluate succeeded | - | Running programmatic evaluation... Symbol Scanner v0.1.0  Analyzing synthetic... Repository: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/eval-repos/synthetic  Files analyzed: 25 Symbols found: 609   - Functions: 200   - Classes: 110   - Methods: 286   - Variables: 13 Calls found: 615   - Direct: 306   - Dynamic: 284   - Async: 25   - Resolved: 137     - Same file: 137     - Cross file: 0   - Unresolved: 478 Imports found: 63   - Static: 58   - Dynamic: 0 Errors: 1  Output: /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-gd2n3n5b/output.json Running evaluation in analysis mode... Ground truth: evaluation/ground-truth Repos dir: /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/eval-repos/syntheti… | Warning: Repository csharp-tshock not found at /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/symbol-scanner/eval-repos/synthetic/csharp-tshock   Minor regression: 99.77% -> 99.07% (within threshold) |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | pass | high | 0.51 | Evaluation decision meets threshold | PASS | - | - |
| `run.evaluate_llm` | fail | medium | 131.63 | make evaluate-llm failed | Running LLM evaluation (4 judges)... | Running LLM evaluation (4 judges)... | usage: orchestrator.py [-h] [--analysis ANALYSIS] [--output OUTPUT]                        [--model MODEL]                        [--programmatic-results PROGRAMMATIC_RESULTS]                        [--focused] orchestrator.py: error: unrecognized arguments: --working-dir . make[1]: *** [evaluate-llm] Error 2 |
| `output.load` | pass | high | 1.57 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-gd2n3n5b/output.json | - | - |
| `output.paths` | pass | high | 18.06 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.12 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.06 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | symbol-scanner, symbol-scanner | - | - |
| `output.metadata_consistency` | pass | medium | 0.02 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.55 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 164.86 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.23 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.18 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.02 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.10 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.07 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.06 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.11 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.07 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 1.71 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.52 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.24 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.05 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.09 | LLM judge count meets minimum (4 >= 4) | call_relationship.py, import_completeness.py, integration.py, symbol_accuracy.py | - | - |
| `evaluation.synthetic_context` | pass | high | 5.63 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: call_relationship.py, prompt: call_relationship.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.12 | Ground truth files present | metaprogramming.json, csharp-tshock.json, cross-module-calls.json, deep-hierarchy.json, encoding-edge-cases.json, circular-imports.json, type-checking-imports.json, decorators-advanced.json, dynamic-code-generation.json, async-patterns.json, nested-structures.json, class-hierarchy.json, simple-functions.json, generators-comprehensions.json, dataclasses-protocols.json, deep-nesting-stress.json, partial-syntax-errors.json, unresolved-externals.json, confusing-names.json, modern-syntax.json, large-file.json, web-framework-patterns.json, import-patterns.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.23 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.48 | Programmatic evaluation schema valid | timestamp, decision, score, checks, summary, aggregate, per_repo_results, metadata, regression | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.28 | Programmatic evaluation passed | PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.18 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.17 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.06 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.05 | LLM evaluation passed | STRONG_PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.21 | Rollup Validation declared with valid tests | src/sot-engine/dbt/models/staging/stg_lz_code_symbols.sql | - | - |
| `adapter.compliance` | pass | info | 0.06 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.71 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 88.72 | Adapter successfully persisted fixture data | Fixture: symbol_scanner_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.68 | All 3 quality rules have implementation coverage | paths, ranges, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.26 | Adapter SymbolScannerAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.22 | Schema tables found for tool | Found 1 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.13 | Tool 'symbol-scanner' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.19 | dbt staging model(s) found | stg_symbol_calls_file_metrics.sql, stg_symbols_file_metrics.sql, stg_symbol_coupling_metrics.sql, stg_lz_symbol_calls.sql, stg_lz_code_symbols.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.19 | dbt models present for tool | stg_symbol_calls_file_metrics.sql, stg_symbols_file_metrics.sql, stg_symbol_coupling_metrics.sql, stg_lz_symbol_calls.sql, stg_lz_code_symbols.sql | - | - |
| `entity.repository_alignment` | pass | high | 6.57 | All entities have aligned repositories | CodeSymbol, SymbolCall, FileImport | - | - |
| `test.structure_naming` | pass | medium | 1.17 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 15.42 | Cross-tool SQL joins use correct patterns (158 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.53 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |

## trivy

| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run.analyze` | pass | critical | 3073.02 | make analyze succeeded | - | Analyzing /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/eval-repos/synthetic as project 'synthetic' /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m scripts.analyze \ 		--repo-path /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/eval-repos/synthetic \ 		--repo-name synthetic \ 		--output-dir /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-6b66p6a_ \ 		--run-id compliance \ 		--repo-id compliance \ 		--branch main \ 		--commit 988008cd161b132ca2aa596b4f0eae76c565ab8c \ 		--timeout 600 [2m2026-02-05T23:23:49.878488Z[0m [[32m[1minfo     [0m] [1mStarting trivy analysis       [0m [36mrepo_name[0m=[35msynthetic[0m [36mrepo_path[0m=[35m/Users/alexander.stage/Projects/2026-01-24-Pro… | - |
| `run.evaluate` | pass | high | 108.13 | make evaluate succeeded | - | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python scripts/evaluate.py --output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-xclj9dps/ Evaluated 0 files | - |
| `evaluation.results` | pass | high | - | Evaluation outputs present | - | - | - |
| `evaluation.quality` | fail | high | 0.15 | Evaluation decision missing | missing decision and summary score | - | - |
| `run.evaluate_llm` | fail | medium | 119.15 | make evaluate-llm failed | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator \
		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-6b66p6a_/output.json \
		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-94mqf4q5/llm_evaluation.json
Running vulnerability_accuracy evaluation...
  Ground truth assertions failed: 1 failures | /Users/alexander.stage/Projects/2026-01-24-Project-Caldera/.venv/bin/python -m evaluation.llm.orchestrator \ 		--analysis /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-6b66p6a_/output.json \ 		--output /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-eval-94mqf4q5/llm_evaluation.json Running vulnerability_accuracy evaluation...   Ground truth assertions failed: 1 failures | Traceback (most recent call last):   File "<frozen runpy>", line 198, in _run_module_as_main   File "<frozen runpy>", line 88, in _run_code   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/evaluation/llm/orchestrator.py", line 198, in <module>     main()   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/evaluation/llm/orchestrator.py", line 171, in main     result = evaluator.evaluate()              ^^^^^^^^^^^^^^^^^^^^   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/shared/evaluation/orchestrator.py", line 189, in evaluate     result = judge.evaluate()              ^^^^^^^^^^^^^^^^   File "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/tools/trivy/evaluation/llm/judges/vulnerability_a… |
| `output.load` | pass | high | 2.72 | Output JSON loaded | /var/folders/zr/c7zp4x316wvg0rsvdnq_dcm40000gn/T/tool-compliance-6b66p6a_/output.json | - | - |
| `output.paths` | pass | high | 13.76 | Path values are repo-relative | - | - | - |
| `output.data_completeness` | pass | high | 0.10 | Data completeness validated | - | - | - |
| `output.path_consistency` | pass | medium | 0.05 | No path fields found to validate | - | - | - |
| `output.required_fields` | pass | high | 0.01 | Required metadata fields present | - | - | - |
| `output.schema_version` | pass | medium | 0.01 | Schema version is semver | 1.0.0 | - | - |
| `output.tool_name_match` | pass | low | 0.01 | Tool name matches data.tool | trivy, trivy | - | - |
| `output.metadata_consistency` | pass | medium | 0.02 | Metadata formats are consistent | - | - | - |
| `schema.version_alignment` | pass | medium | 0.79 | Output schema_version matches schema constraint | 1.0.0 | - | - |
| `output.schema_validate` | pass | critical | 159.25 | Output validates against schema (venv) | - | - | - |
| `structure.paths` | pass | high | 0.24 | All required paths present | - | - | - |
| `make.targets` | pass | high | 0.18 | Makefile targets present | - | - | - |
| `make.permissions` | pass | low | 0.01 | Makefile has correct permissions | - | - | - |
| `make.uses_common` | pass | medium | 0.11 | Makefile includes ../Makefile.common | - | - | - |
| `make.output_dir_convention` | pass | low | 0.07 | OUTPUT_DIR inherited from Makefile.common | outputs/$(RUN_ID) | - | - |
| `make.output_filename` | pass | medium | 0.05 | analyze target uses output directory argument | - | - | - |
| `schema.draft` | pass | medium | 0.10 | Schema draft is 2020-12 | - | - | - |
| `schema.contract` | pass | high | 0.08 | Schema requires metadata and data fields | - | - | - |
| `docs.blueprint_structure` | pass | medium | 1.56 | BLUEPRINT.md has required sections | - | - | - |
| `docs.eval_strategy_structure` | pass | high | 0.38 | EVAL_STRATEGY.md has required sections | - | - | - |
| `evaluation.check_modules` | pass | medium | 0.09 | Check modules present | - | - | - |
| `evaluation.llm_prompts` | pass | medium | 0.09 | LLM prompts present | - | - | - |
| `evaluation.llm_judge_count` | pass | medium | 0.09 | LLM judge count meets minimum (7 >= 4) | freshness_quality.py, vulnerability_detection.py, vulnerability_accuracy.py, severity_accuracy.py, iac_quality.py, sbom_completeness.py, false_positive_rate.py | - | - |
| `evaluation.synthetic_context` | pass | high | 10.67 | Synthetic evaluation context pattern implemented correctly | base.py: evaluation_mode parameter present, primary judge: vulnerability_accuracy.py, prompt: vulnerability_accuracy.md has all placeholders | - | - |
| `evaluation.ground_truth` | pass | high | 0.11 | Ground truth files present | dotnet-outdated.json, js-fullstack.json, vulnerable-npm.json, iac-terraform.json, no-vulnerabilities.json, iac-misconfigs.json, mixed-severity.json, java-outdated.json, critical-cves.json, outdated-deps.json, cfn-misconfigs.json, k8s-misconfigs.json | - | - |
| `evaluation.scorecard` | pass | low | 0.02 | Scorecard present | - | - | - |
| `evaluation.programmatic_exists` | pass | high | 0.27 | Programmatic evaluation file exists | evaluation/results/evaluation_report.json | - | - |
| `evaluation.programmatic_schema` | pass | high | 0.40 | Programmatic evaluation schema valid | timestamp, tool, version, decision, score, classification, overall_score, summary, checks, dimensions | - | - |
| `evaluation.programmatic_quality` | pass | high | 0.17 | Programmatic evaluation passed | STRONG_PASS | - | - |
| `evaluation.llm_exists` | pass | medium | 0.26 | LLM evaluation file exists | evaluation/results/llm_evaluation.json | - | - |
| `evaluation.llm_schema` | pass | medium | 0.21 | LLM evaluation schema valid | timestamp, model, decision, score, programmatic_input, dimensions, summary, run_id, total_score, average_confidence | - | - |
| `evaluation.llm_includes_programmatic` | pass | medium | 0.07 | LLM evaluation includes programmatic input | file=evaluation/results/evaluation_report.json, decision=STRONG_PASS | - | - |
| `evaluation.llm_decision_quality` | pass | medium | 0.06 | LLM evaluation passed | PASS | - | - |
| `evaluation.rollup_validation` | pass | high | 0.19 | Rollup Validation declared with valid tests | src/sot-engine/dbt/tests/test_rollup_trivy_direct_vs_recursive.sql | - | - |
| `adapter.compliance` | pass | info | 0.05 | Adapter exposes schema, LZ contract, and validation hooks | - | - | - |
| `adapter.schema_alignment` | pass | high | 1.70 | TABLE_DDL matches schema.sql | - | - | - |
| `adapter.integration` | pass | high | 167.54 | Adapter successfully persisted fixture data | Fixture: trivy_output.json | - | - |
| `adapter.quality_rules_coverage` | pass | info | 0.65 | All 3 quality rules have implementation coverage | paths, line_numbers, required_fields | - | - |
| `sot.adapter_registered` | pass | medium | 0.28 | Adapter TrivyAdapter properly registered in adapters/__init__.py | - | - | - |
| `sot.schema_table` | pass | high | 0.23 | Schema tables found for tool | Found 3 table(s) | - | - |
| `sot.orchestrator_wired` | pass | high | 0.13 | Tool 'trivy' wired in TOOL_INGESTION_CONFIGS | - | - | - |
| `sot.dbt_staging_model` | pass | high | 0.20 | dbt staging model(s) found | stg_trivy_iac_misconfigs.sql, stg_trivy_vulnerabilities.sql, stg_trivy_target_metrics.sql, stg_trivy_targets.sql | - | - |
| `dbt.model_coverage` | pass | high | 0.49 | dbt models present for tool | stg_trivy_iac_misconfigs.sql, stg_trivy_vulnerabilities.sql, stg_trivy_target_metrics.sql, stg_trivy_targets.sql | - | - |
| `entity.repository_alignment` | pass | high | 6.16 | All entities have aligned repositories | TrivyVulnerability, TrivyTarget, TrivyIacMisconfig | - | - |
| `test.structure_naming` | pass | medium | 1.16 | Test structure and naming conventions followed | - | - | - |
| `sql.cross_tool_join_patterns` | pass | high | 15.86 | Cross-tool SQL joins use correct patterns (158 files checked) | - | - | - |
| `test.coverage_threshold` | skip | high | 0.31 | No coverage report found - run with --run-coverage | coverage.json not found | - | - |
