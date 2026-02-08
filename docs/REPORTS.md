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

## File Hotspots

File: `src/sot-engine/dbt/analysis/report_file_hotspots.sql`

Purpose: identify top files by LOC, complexity, and other metrics.

## Cross-Tool Insights

File: `src/sot-engine/dbt/analysis/report_cross_tool_insights.sql`

Purpose: correlate findings across multiple tools for the same files.

## Category Breakdowns

Files:
- `src/sot-engine/dbt/analysis/report_semgrep_category_breakdown.sql` - Semgrep findings by category
- `src/sot-engine/dbt/analysis/report_roslyn_category_breakdown.sql` - Roslyn violations by category
- `src/sot-engine/dbt/analysis/report_category_severity.sql` - Findings by severity level

## Language Coverage

File: `src/sot-engine/dbt/analysis/report_language_coverage.sql`

Purpose: show file counts and LOC by programming language.

## Inequality Analyses

Files:
- `src/sot-engine/dbt/analysis/inequality_by_gini.sql` - Gini coefficient analysis
- `src/sot-engine/dbt/analysis/inequality_by_palma.sql` - Palma ratio analysis
- `src/sot-engine/dbt/analysis/inequality_concentration.sql` - Concentration metrics
- `src/sot-engine/dbt/analysis/inequality_cross_tool.sql` - Cross-tool inequality comparison
- `src/sot-engine/dbt/analysis/inequality_cross_tool_correlation.sql` - Tool correlation analysis

## Distribution Analyses

Files:
- `src/sot-engine/dbt/analysis/distribution_scope_comparison.sql` - Compare direct vs recursive distributions
- `src/sot-engine/dbt/analysis/distribution_shape_patterns.sql` - Distribution shape classification
- `src/sot-engine/dbt/analysis/distribution_tail_risk.sql` - Tail risk metrics (p95, p99)

## Module Health

Files:
- `src/sot-engine/dbt/analysis/module_health_scores.sql` - Directory-level health scoring
- `src/sot-engine/dbt/analysis/module_health_summary.sql` - Aggregated health summary
- `src/sot-engine/dbt/analysis/module_risk_factors.sql` - Risk factor identification

## Extended Directory Analysis

File: `src/sot-engine/dbt/analysis/report_directory_hotspots_full.sql`

Purpose: comprehensive directory analysis with all metrics.

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

## Tool Readiness Report

The tool readiness report scans all tools in `src/tools/` and summarizes their
evaluation status. Unlike other reports, this does not require a database.

```bash
# Generate markdown (default)
cd src/insights && .venv/bin/python -m insights tool-readiness

# Generate HTML
cd src/insights && .venv/bin/python -m insights tool-readiness --format html -o output/readiness.html
```

The report categorizes tools into:
- **Ready for Reports**: STRONG_PASS or PASS decision
- **Needs Investigation**: Missing scorecard.json but has evaluation infrastructure
- **Not Ready**: WEAK_PASS or FAIL decision
- **No Evaluation**: No evaluation infrastructure set up

Data sources (in order of precedence):
1. `evaluation/scorecard.json` - primary scorecard format
2. `evaluation/results/evaluation_report.json` - fallback format

## Insights Component

The `src/insights/` component generates consolidated HTML/Markdown reports with multiple sections:
- Tool Readiness (meta-report, no database required)
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
