# Caldera Pilot Plan (scc + lizard)

## Cut Line (Reuse vs Replace)
### Reuse
- Tool implementations: `src/tools/scc/`, `src/tools/lizard/`
- Tool schemas (update only if needed to match envelope + path rules)
- Layout scanner (source of file registry)
- Tool compliance evaluation - we have expectations towards tools. Adjust and add a make target to do the evaluation of all tools 
- Evaluation framework (programmatic + LLM)

### Replace / Add
- SoT adapters for scc + lizard (JSON -> landing zone tables)
- Landing zone schemas for scc + lizard (if missing)
- dbt models for unified marts (file_metrics + run_summary for scc/lizard)
- Orchestrator path to use JSON-only ingestion for scc/lizard

### Bypass (Pilot)
- Aggregator path for scc/lizard (keep for other tools)

## Phase 0 - Standards & Compliance (Complete)
- Confirm envelope + tool schemas
- Ensure outputs include `run_id`, `repo_id`, `commit`, `timestamp`
- Enforce repo-relative path rules
- Establish tool compliance scanner as the single readiness gate
- Add top-level Makefile targets for tool orchestration + compliance

Exit gate: Compliance scan passes for structure + schema checks.

## Phase 1 - Tool Hardening (scc + lizard) (Complete)
- Run compliance scanner with `--run-analysis` to validate output schema + path rules
- Validate evaluation artifacts are produced and current
- Align Makefile targets with standards (help/setup/analyze/evaluate/evaluate-llm/test/clean)

Exit gate: Compliance scan with `--run-analysis --run-evaluate` passes for both tools.

Status:
- scc + lizard pass compliance with `--run-analysis --run-evaluate --run-llm` (no skips allowed).

## Phase 2 - SoT Adapters + Landing Zone (Complete)
- Implement landing zone schema (`lz_*`) with raw per-file/per-function tables only
- Implement repositories + adapters for scc/lizard (JSON -> entities -> repositories)
- Add schema-compliant fixtures for scc/lizard
- Unit tests for JSON -> entity mapping
- Integration tests with DuckDB temp DB and layout lookup

Exit gate: specs map JSON -> landing zone via repositories.

## Phase 3 - dbt Marts (Complete)
- dbt staging models for `lz_*` tables
- dbt tests for nulls, ranges, uniqueness, run_id consistency
- dbt marts to merge scc + lizard into unified outputs
- Report analyses covered by DuckDB-based report tests
- Report-specific dbt tests for repo health snapshot metrics

Exit gate: dbt run + test pass on pilot run.

## Phase 4 - Orchestrator Hook (Complete)
- Orchestrator runs layout → scc/lizard adapters → dbt
- Validate run_id/repo_id alignment on ingestion
- Keep old path for other tools
- Enforce one collection run per repo+commit; `--replace` overwrites prior data

Exit gate: end-to-end run produces unified marts for scc + lizard.

## Phase 5 - Evaluation
- Programmatic precision/recall checks on synthetic repos
- LLM judges supplemental on real repos; propose improvements on synthetic

Exit gate: evaluation scorecard meets production threshold.

## Phase 6 - Rollup Coverage (Complete)
- Add direct rollup marts alongside recursive rollups
- Add dbt tests asserting recursive >= direct
- Expand rollup tests for distribution bounds (quantiles, concentration metrics)
- Add report-specific dbt tests (`make dbt-test-reports`)

## Immediate Next Steps
1. **Wire semgrep to orchestrator** - Add to TOOL_CONFIGS and test end-to-end pipeline
2. Add semgrep staging models and unified marts (currently smells go to lz_semgrep_smells only)
3. Expand rollup coverage for semgrep smell counts per directory
4. Decide next tool onboarding target after semgrep is fully integrated
