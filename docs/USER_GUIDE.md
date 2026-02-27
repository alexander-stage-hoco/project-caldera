# Project Caldera — User Guide

Project Caldera analyzes codebases by running 18 analysis tools, persisting results to a DuckDB warehouse, and generating an actionable insights report.

## Prerequisites

| Requirement | Check | Install |
|-------------|-------|---------|
| Python 3.12+ | `python3 --version` | [python.org](https://www.python.org/downloads/) |
| git | `git --version` | `brew install git` |
| make | `make --version` | Included with Xcode CLI tools |
| duckdb CLI (optional) | `duckdb --version` | `brew install duckdb` (optional, for ad-hoc inspection) |

Run `make status` to verify all prerequisites at once.

## Quick Start

### 1. Setup (one-time)

```bash
make setup
```

This creates the project virtual environment, installs dependencies, and sets up all 18 tool environments.

### 2. Configure secrets (one-time)

```bash
cp .env.example .env
```

Edit `.env` and fill in the API keys you need. At minimum, set `ANTHROPIC_API_KEY` for LLM evaluation. All secrets are documented in the file. The `.env` file is gitignored and never committed.

### 3. Analyze a repository

**Local repository:**

```bash
make analyze REPO=/path/to/your/repo
```

**Remote GitHub repository:**

```bash
make analyze REPO=https://github.com/user/project
```

Remote URLs are cloned (full history by default) to a temporary directory, analyzed, then cleaned up. Pass `CLONE_DEPTH=1` for a shallow clone if you don't need history-based tools (git-fame, git-blame-scanner, gitleaks).

### 4. View results

The pipeline produces three output files:

| File | Contents |
|------|----------|
| `src/insights/output/pipeline/report.html` | Full HTML analysis report |
| `src/insights/output/pipeline/evaluation.json` | LLM quality evaluation of the report |
| `src/insights/output/pipeline/top3_insights.json` | Top 3 actionable insights |

Open the HTML report in a browser to see the full analysis.

Each run is also archived under `src/insights/output/pipeline/runs/<repo_id>/<run_id>/` with:
- `orchestrator.log` (tool + dbt logs)
- `tool_run_summary.json` (written even on failure)
- `dbt_summary.json` (dbt run/test status + durations)
- `dbt_logs/` and `dbt_target/`
- `run_manifest.json` (machine-readable summary)

## What Happens During Analysis

The `make analyze` command runs four phases automatically:

### Phase 1 — Tool Execution (18 tools)

Each tool runs against the target repository and produces JSON output:

| Category | Tools |
|----------|-------|
| Size & structure | layout-scanner, scc, git-sizer |
| Complexity | lizard |
| Code quality | semgrep, roslyn-analyzers, sonarqube, devskim |
| Security | trivy, gitleaks |
| Dependencies | dependensee, scancode |
| Coverage | dotcover, coverage-ingest |
| Duplication | pmd-cpd |
| Symbols | symbol-scanner |
| Git history | git-fame, git-blame-scanner |

Tool outputs are written to `src/tools/<tool>/outputs/`.

### Phase 2 — Data Persistence

The orchestrator validates each tool's JSON output and loads it into the DuckDB landing zone. Adapters enforce schema validation, path normalization, and quality rules.

Database location: `~/.caldera/caldera_sot.duckdb` (override with `DB_PATH`).

### Phase 3 — Data Transformation (dbt)

dbt transforms raw landing zone data through staging models into marts:

```
Landing Zone (lz_*) → Staging (stg_*) → Marts (unified_file_metrics, unified_run_summary, rollups)
```

### Phase 4 — Report & Evaluation

1. Generates an HTML report from dbt marts
2. LLM evaluates report quality using InsightQualityJudge
3. Extracts the top 3 actionable insights with improvement proposals

## Common Workflows

### Re-analyze the same repository

If you've already analyzed a repo at the same commit, use `REPLACE=1`:

```bash
make analyze REPO=/path/to/repo REPLACE=1
```

### Regenerate report without re-running tools

```bash
make report                              # from the latest collection run
make report COLLECTION_RUN_ID=<uuid>     # from a specific collection run
```

### Check what runs exist

```bash
make list-runs
```

### Continue even if a tool fails (partial results)

By default, the orchestrator stops at the first tool failure. To continue running the remaining tools (and still ingest/dbt), use:

```bash
make analyze REPO=/path/to/repo CONTINUE_ON_TOOL_FAILURE=1
```

### Run a single tool manually

```bash
cd src/tools/scc && make analyze REPO_PATH=/path/to/repo
```

### Check project health

```bash
make status       # verify prerequisites
make doctor       # detailed system diagnostics (Python, tools, DB, dbt)
make compliance   # run tool compliance scanner
make test         # run all tests (pytest + tool tests + dbt)
```

### Artifact bundle workflow (optional)

Collect tool artifacts (JSON + logs) without DuckDB/dbt:

```bash
make collect REPO=/path/to/repo
```

Then ingest and generate a report on another machine:

```bash
make analyze-bundle REPO=/path/to/repo BUNDLE=artifacts/<repo_id>/<run_id>
```

### Cloud analysis (Hetzner)

Run the full pipeline on an ephemeral Hetzner Cloud VM. The server is created, runs the analysis, downloads results, and is destroyed automatically.

**Prerequisites:**

1. Install Terraform: `brew install terraform`
2. Configure credentials: `cp infra/terraform.tfvars.example infra/terraform.tfvars` and fill in your Hetzner API token and Caldera repo URL
3. One-time init: `make cloud-setup`

**Run a cloud analysis:**

```bash
make cloud-run REPO=https://github.com/pallets/flask
```

Options:

```bash
make cloud-run REPO=https://github.com/org/repo CLOUD_SERVER=cx43   # Larger server (8 vCPU / 16 GB)
make cloud-run REPO=https://github.com/org/repo SKIP_TOOLS=sonarqube,trivy
make cloud-run REPO=https://github.com/org/repo KEEP_SERVER=1       # Don't destroy (for debugging)
```

Results are downloaded to `infra/results/<repo-id>/<run-id>/` containing the DuckDB database, HTML report, and a `manifest.json`. Open the report:

```bash
open infra/results/<repo-id>/<run-id>/reports/report.html
```

Check cloud server status and download progress:

```bash
make cloud-status
```

If you used `KEEP_SERVER=1`, destroy the server when done:

```bash
make cloud-destroy
```

For large repositories and detailed cloud configuration, see [Cloud Analysis Guide](CLOUD_ANALYSIS_GUIDE.md).

See [infra/README.md](../infra/README.md) for the full infrastructure reference.

### Reset the database

```bash
make clean-db
```

Removes the DuckDB database. The next `make analyze` creates a fresh one.

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `REPO` | (required) | Path or URL to analyze |
| `REPLACE` | unset | Set to `1` to overwrite an existing run |
| `DB_PATH` | `~/.caldera/caldera_sot.duckdb` | DuckDB database location |
| `COLLECTION_RUN_ID` | latest | Specific collection run UUID for `make report` |
| `CLONE_DEPTH` | (full) | Set to `N` for `--depth N` shallow clone of remote URLs |
| `TOOL` | all | Limit `tools-*` targets to one tool |
| `SKIP_TOOLS` | unset | Comma-separated tool names to skip |
| `PIPELINE_LLM` | `1` | Set to `0` to skip LLM evaluation + top3 extraction |
| `BUNDLE_DIR` | `artifacts` | Bundle output directory for `make collect` |
| `BUNDLE_TAR` | `1` | Create `.tar.gz` from bundle |
| `CLOUD_SERVER` | `cx33` | Hetzner server type for `make cloud-run` |
| `CLOUD_RESULTS` | `infra/results` | Local directory for cloud run results |
| `KEEP_SERVER` | unset | Set to `1` to keep VM alive after cloud run |
| `CONTINUE_ON_TOOL_FAILURE` | unset | Set to `1` to continue past tool failures |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Python 3.12+ required` | Install Python 3.12+ and ensure `python3` points to it |
| `No module named 'duckdb'` | Use `.venv/bin/python`, not system `python` |
| Path validation errors | Ensure paths are repo-relative (no leading `/` or `./`) |
| `Collection run exists` | Use `REPLACE=1` flag: `make analyze REPO=... REPLACE=1` |
| dbt test failures | Check rollup invariant: `recursive >= direct` |
| Schema validation errors | Compare output against `schemas/output.schema.json` |
| Import errors for shared modules | Check PYTHONPATH includes `src/` |
| `No database found` | Run `make analyze` first to create the database |
| Clone fails for remote URL | Verify the URL is accessible and git is installed |

## Further Reading

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](../CLAUDE.md) | Full project reference for AI-assisted development |
| [docs/PERSISTENCE.md](PERSISTENCE.md) | Adapter pattern, entities, repositories |
| [docs/COMPLIANCE.md](COMPLIANCE.md) | Tool readiness requirements and checks |
| [docs/EVALUATION.md](EVALUATION.md) | LLM judge infrastructure |
| [docs/REPORTS.md](REPORTS.md) | dbt analyses and reports |
| [docs/TOOL_INTEGRATION_CHECKLIST.md](TOOL_INTEGRATION_CHECKLIST.md) | Creating and integrating new tools |
