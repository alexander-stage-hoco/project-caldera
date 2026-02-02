# Reports

This repo includes simple dbt analyses for the current marts. Each report expects
`run_pk` as the primary selector.

## Repo Health Snapshot

File: `src/sot-engine/dbt/analysis/report_repo_health_snapshot.sql`

Purpose: summarize repo-level totals and root-level distribution signals
(concentration, p95/p99) for LOC and complexity.

Key fields:
- totals: `total_files`, `total_loc`, `total_ccn`, `avg_ccn`
- concentration: `scc_loc_gini`, `ccn_gini`, `scc_loc_hoover`, `ccn_hoover`
- tail risk: `scc_loc_p95`, `scc_loc_p99`, `ccn_p95`, `ccn_p99`

## Hotspot Directories

File: `src/sot-engine/dbt/analysis/report_hotspot_directories.sql`

Purpose: list top directories by LOC and complexity using p95 and avg values.
Outputs two sections: `loc_hotspot` and `complexity_hotspot`.

Key fields:
- `directory_path`
- `p95_value`, `p99_value`, `avg_value`
- `gini_value`, `hoover_value`, `palma_value`, `top_20_pct_share`

## Collection Run Status

File: `src/sot-engine/dbt/analysis/report_collection_runs.sql`

Purpose: list collection runs with status, timestamps, and tool run counts.

Key fields:
- `collection_run_id`, `repo_id`, `run_id`
- `commit`, `branch`, `status`
- `started_at`, `completed_at`
- `tool_runs`

## Running Reports

1. Ensure marts are built:
   - `make dbt-run`
2. Run via the insights CLI (recommended). This repo does not ship a separate
   explorer CLI; the insights component is the supported reporting entrypoint:
   - `cd src/insights && .venv/bin/python -m insights generate 1 --db /tmp/caldera_sot.duckdb --format html -o output/report.html`
   - `cd src/insights && .venv/bin/python -m insights generate 1 --db /tmp/caldera_sot.duckdb --format md -o output/report.md`

Make targets are available in `src/insights/`:
- `make generate RUN_PK=1`
- `make generate-md RUN_PK=1`
- `make test-e2e` (seed test database, run dbt, generate report)

## Tests

Report analyses are covered by DuckDB-based unit-style tests under:
- `src/sot-engine/tests/test_report_*.py`
- `src/insights/tests/` (unit and E2E tests)

## Insights Component

The `src/insights/` component generates consolidated HTML/Markdown reports with multiple sections:
- Repository Health Overview
- File Hotspots
- Directory Analysis
- Vulnerabilities
- Cross-Tool Insights
- Language Coverage
- Distribution Insights
- Roslyn Violations
- IaC Misconfigurations

See `src/insights/README.md` for full documentation.
