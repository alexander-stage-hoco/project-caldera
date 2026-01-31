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
2. Run via the report runner (recommended):
   - `.venv/bin/python src/explorer/report_runner.py repo-health --run-pk 1`
   - `.venv/bin/python src/explorer/report_runner.py hotspots --run-pk 1 --limit 10`

You can also resolve the latest run by repo id:
- `.venv/bin/python src/explorer/report_runner.py repo-health --repo-id demo-repo`
- `.venv/bin/python src/explorer/report_runner.py hotspots --repo-id demo-repo --run-id run-2026-01-24 --limit 10`

Make targets are available:
- `make report-health RUN_PK=1`
- `make report-hotspots RUN_PK=1 REPORT_LIMIT=10`
- `make report-health-latest REPO_ID=demo-repo`
- `make report-hotspots-latest REPO_ID=demo-repo REPORT_LIMIT=10`
- `make report-runs`
- `make dbt-test-reports`

## Tests

Report analyses are covered by DuckDB-based unit-style tests under
`src/sot-engine/tests/test_report_*.py`.

Latest run resolution uses `lz_tool_runs.created_at` (fallback to `lz_tool_runs.timestamp`) and
then selects the run with the most files when multiple tool runs share the same repo/run.

Markdown output:
- `.venv/bin/python src/explorer/report_runner.py repo-health --run-pk 1 --format md`
- `make report-health RUN_PK=1 REPORT_FORMAT=md`

Repeat for `report_hotspot_directories.sql` (add `--vars '{"run_pk": 1, "limit": 10}'` if needed).
