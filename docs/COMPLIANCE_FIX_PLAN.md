# Compliance Fix Plan

Goal: Make `make compliance` pass with **full runtime checks** (analysis + evaluate + LLM) and **no skips**.

## Phase 0 — Preflight
- Confirm Docker is running and CLI accessible.
- Confirm root `.venv` has shared deps (done).
- Confirm each tool venv exists (done via `make tools-setup`).

## Phase 1 — Standardize Evaluation Outputs (Cross-Tool)
Goal: Every tool honors `EVAL_OUTPUT_DIR` and writes required artifacts there.

1) **Normalize `evaluate` output paths**
- Update each tool’s `scripts/evaluate.py` or Makefile to:
  - read `EVAL_OUTPUT_DIR`
  - write `scorecard.md` + `checks.json` into that dir
  - keep current behavior if `EVAL_OUTPUT_DIR` is unset
- Apply to: `roslyn-analyzers`, `trivy`, `lizard`, `semgrep`, `layout-scanner`, `git-sizer`, `sonarqube`, `scc`
- Tests: one unit test per tool verifying `EVAL_OUTPUT_DIR` override

2) **Normalize `evaluate-llm` output path**
- Ensure each tool writes `evaluation/results/llm_evaluation.json` when run under compliance temp dir
- If tool writes to another path, add an override or copy
- Tests: one unit test per tool verifying LLM output path override

## Phase 2 — Tool-Specific Fixes

### A) git-sizer
- Initialize `eval-repos/synthetic` as a real git repo with a commit
- Fix `evaluate-llm` CLI: remove unsupported `--results-dir` or update orchestrator args
- Add minimal ground truth JSONs (or update TOOL_RULES to match actual GT format)
- Add Rollup Validation section to EVAL_STRATEGY.md (or explicitly state “no rollups”)
- dbt model coverage: add minimal staging model or declare tool non-dbt with documentation
- Tests: `test_git_sizer_evaluate_outputs`, `test_git_sizer_llm_output_path`

### B) layout-scanner
- `evaluate.py` should read analysis output from `EVAL_OUTPUT_DIR` or `OUTPUT_DIR`
- Fix only evaluate pathing (LLM runs but compliance fails because evaluate fails)
- Tests: `test_layout_scanner_evaluate_uses_eval_output_dir`

### C) lizard
- Fix permission error by invoking evaluator via `python -m scripts.evaluate` in Makefile
- Ensure evaluate writes to `EVAL_OUTPUT_DIR`
- Ensure LLM output path under compliance
- Tests: `test_lizard_evaluate_output_dir`

### D) roslyn-analyzers
- Ensure `evaluate` writes `scorecard.md` + `checks.json` to `EVAL_OUTPUT_DIR`
- Ensure LLM output path under compliance
- Tests: `test_roslyn_evaluate_outputs`

### E) trivy
- Ensure `evaluate` writes `scorecard.md` + `checks.json` to `EVAL_OUTPUT_DIR`
- Ensure LLM output path under compliance
- Tests: `test_trivy_evaluate_outputs`

### F) scc
- Fix LLM timeout: add env `LLM_TIMEOUT` and honor it in LLM runner
- Increase timeout for compliance
- Tests: `test_scc_llm_timeout_env`

### G) semgrep
- Programmatic eval fails due to schema mismatch + no findings
- Fixes:
  - Ensure analysis uses correct ruleset for synthetic repo
  - Ensure output schema version matches `schemas/output.schema.json`
  - Ensure analysis emits required sections (`tool`, `summary`, `files`, etc.)
  - Ensure synthetic repo or rules guarantee findings
- Tests:
  - `test_semgrep_output_schema_valid`
  - `test_semgrep_synthetic_generates_findings`
  - `test_semgrep_evaluate_outputs`

### H) sonarqube
- .NET scanner fails due to `sonar-project.properties` in repo
- Fix:
  - when using .NET scanner, remove/ignore `sonar-project.properties` in a temp copy
  - or use non-.NET scanner for C# repos where feasible
- Ensure evaluate + evaluate-llm write outputs into `EVAL_OUTPUT_DIR`
- Tests:
  - `test_sonarqube_dotnet_ignores_sonar_properties`
  - `test_sonarqube_evaluate_outputs`

## Phase 3 — Compliance Tool Enhancements
- Improve error reporting: include captured stdout/stderr in report for failed `make`
- If `--run-analysis` is set, enforce output from temp `EVAL_OUTPUT_DIR`
- Tests: `test_compliance_reports_error_details`

## Phase 4 — Verification
1) `make tools-setup`
2) `make compliance`
3) Expect 8/8 tools passing
