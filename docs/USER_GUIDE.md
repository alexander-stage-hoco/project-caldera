# User Guide

This guide covers common workflows for analyzing repositories with Project Caldera.

## Prerequisites

- Python 3.12
- A virtual environment with dependencies installed

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
make tools-setup
```

## Quick Start

Analyze a repository in one command:

```bash
make orchestrate \
  ORCH_REPO_PATH=/path/to/your/repo \
  ORCH_REPO_ID=my-project \
  ORCH_RUN_ID=run-001 \
  ORCH_BRANCH=main \
  ORCH_COMMIT=abc1234
```

This runs all analysis tools, loads results into DuckDB, and builds the data marts.

To view results:

```bash
make report-health-latest REPO_ID=my-project
make report-hotspots-latest REPO_ID=my-project REPORT_LIMIT=10
```

## Core Workflows

### Running the Full Pipeline

The orchestrator coordinates the entire analysis pipeline:

```bash
# Analyze a repository (all required parameters)
make orchestrate \
  ORCH_REPO_PATH=/path/to/repo \
  ORCH_REPO_ID=project-name \
  ORCH_RUN_ID=run-2026-01-27 \
  ORCH_BRANCH=main \
  ORCH_COMMIT=$(git -C /path/to/repo rev-parse HEAD)
```

Or use the Python script directly:

```bash
.venv/bin/python src/sot-engine/orchestrator.py \
  --repo-path /path/to/repo \
  --repo-id project-name \
  --run-id run-001 \
  --branch main \
  --commit HEAD \
  --run-tools --run-dbt
```

### Running Individual Tools

Run all tools against their configured test repositories:

```bash
make tools-analyze
```

Run a specific tool:

```bash
make tools-analyze TOOL=scc
make tools-analyze TOOL=lizard
```

### Generating Reports

Reports require a completed pipeline run. Use either a run primary key or repo ID:

```bash
# By run primary key
make report-health RUN_PK=1
make report-hotspots RUN_PK=1 REPORT_LIMIT=10

# By repo ID (uses latest run)
make report-health-latest REPO_ID=my-project
make report-hotspots-latest REPO_ID=my-project

# List all collection runs
make report-runs
```

Output formats: `table` (default) or `md` (markdown):

```bash
make report-health RUN_PK=1 REPORT_FORMAT=md
```

### Exploring Data

List all tables in the database:

```bash
make explore
```

Run ad-hoc SQL queries:

```bash
make explore-query QUERY="SELECT * FROM lz_collection_runs LIMIT 5"
make explore-query QUERY="SELECT COUNT(*) FROM unified_file_metrics"
```

## Understanding Outputs

### Key Metrics

| Metric | Description |
|--------|-------------|
| LOC | Lines of code (excludes blanks and comments) |
| CCN | Cyclomatic complexity number (decision points + 1) |
| NLOC | Non-commenting lines of code per function |
| Gini | Concentration measure (0=equal, 1=concentrated) |
| p95/p99 | 95th/99th percentile values |

### Output Locations

- **DuckDB database**: `/tmp/caldera_sot.duckdb` (default)
- **Tool outputs**: `src/tools/<tool>/outputs/<run-id>/output.json`
- **Compliance reports**: `/tmp/tool_compliance_report.{json,md}`
- **Orchestrator logs**: `/tmp/caldera_orchestrator_<run-id>.log`

### Reading Report Summaries

**Repo Health Snapshot** shows repository-level totals and distribution signals:
- `total_files`, `total_loc`, `total_ccn`, `avg_ccn` for overall size
- `gini`, `hoover` values indicate code concentration
- `p95`, `p99` values flag tail-risk outliers

**Hotspot Directories** ranks directories by complexity and size, helping identify areas needing attention.

## Common Tasks

### Re-analyzing After Code Changes

Add `ORCH_REPLACE=1` to overwrite an existing run:

```bash
make orchestrate \
  ORCH_REPO_PATH=/path/to/repo \
  ORCH_REPO_ID=my-project \
  ORCH_RUN_ID=run-001 \
  ORCH_BRANCH=main \
  ORCH_COMMIT=newcommit \
  ORCH_REPLACE=1
```

### Checking Tool Compliance

Verify tools meet readiness requirements (full compliance run, no skips allowed):

```bash
make compliance
```

### Running Tests

```bash
make test          # All tests (pytest + tool tests + dbt tests)
make tools-test    # Tool-specific tests only
make dbt-test      # dbt model tests only
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Path validation errors | Ensure paths are repo-relative (no leading `/` or `./`) |
| "Collection run already exists" | Use `ORCH_REPLACE=1` or `--replace` flag |
| dbt test failures | Check rollup invariants: recursive count >= direct count |
| Missing tables | Run `make dbt-run` to build marts |
| Tool not found | Verify `src/tools/<name>/Makefile` exists |

For detailed architecture and adding new tools, see `docs/TOOL_REQUIREMENTS.md` and `docs/TOOL_MIGRATION_CHECKLIST.md`.
