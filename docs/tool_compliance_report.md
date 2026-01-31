# Tool Compliance Report

Generated: `2026-01-30T21:03:01.702417+00:00`

Summary: 0 passed, 8 failed, 8 total

| Tool | Status | Failed Checks |
| --- | --- | --- |
| git-sizer | fail | run.analyze, run.evaluate_llm, output.load, evaluation.ground_truth, evaluation.rollup_validation, dbt.model_coverage, entity.repository_alignment |
| layout-scanner | fail | output.schema_validate, entity.repository_alignment |
| lizard | fail | output.schema_validate, entity.repository_alignment |
| roslyn-analyzers | fail | output.schema_validate, entity.repository_alignment |
| scc | fail | output.schema_validate, entity.repository_alignment |
| semgrep | fail | output.schema_validate, entity.repository_alignment |
| sonarqube | fail | output.schema_validate, entity.repository_alignment |
| trivy | fail | output.schema_validate, entity.repository_alignment |

## git-sizer failures
- `run.analyze` (critical): No analysis output found - run with --run-analysis or execute 'make analyze' [-]
- `run.evaluate_llm` (medium): No LLM evaluation output found - run with --run-llm or execute 'make evaluate-llm' [-]
- `output.load` (high): No output.json available [No output.json found]
- `evaluation.ground_truth` (high): Missing per-language ground truth [bloated.json, healthy.json]
- `evaluation.rollup_validation` (high): Rollup Validation section incomplete [Missing test paths: *Note**: git-sizer provides **repository-level** metrics, not file-level metrics. Therefore:, No directory rollup validation is applicable, Metrics are single values per repository run, No distribution analysis needed]
- `dbt.model_coverage` (high): Missing dbt model coverage [No staging models matching stg_*git-sizer*.sql, Missing rollup model for repo_level_metrics (no directory rollups - git-sizer is repository-level only)]
- `entity.repository_alignment` (high): Failed to import persistence modules: No module named 'duckdb' [No module named 'duckdb']

## layout-scanner failures
- `output.schema_validate` (critical): jsonschema not installed for validation [-]
- `entity.repository_alignment` (high): Failed to import persistence modules: No module named 'duckdb' [No module named 'duckdb']

## lizard failures
- `output.schema_validate` (critical): jsonschema not installed for validation [-]
- `entity.repository_alignment` (high): Failed to import persistence modules: No module named 'duckdb' [No module named 'duckdb']

## roslyn-analyzers failures
- `output.schema_validate` (critical): jsonschema not installed for validation [-]
- `entity.repository_alignment` (high): Failed to import persistence modules: No module named 'duckdb' [No module named 'duckdb']

## scc failures
- `output.schema_validate` (critical): jsonschema not installed for validation [-]
- `entity.repository_alignment` (high): Failed to import persistence modules: No module named 'duckdb' [No module named 'duckdb']

## semgrep failures
- `output.schema_validate` (critical): jsonschema not installed for validation [-]
- `entity.repository_alignment` (high): Failed to import persistence modules: No module named 'duckdb' [No module named 'duckdb']

## sonarqube failures
- `output.schema_validate` (critical): jsonschema not installed for validation [-]
- `entity.repository_alignment` (high): Failed to import persistence modules: No module named 'duckdb' [No module named 'duckdb']

## trivy failures
- `output.schema_validate` (critical): jsonschema not installed for validation [-]
- `entity.repository_alignment` (high): Failed to import persistence modules: No module named 'duckdb' [No module named 'duckdb']
