# Project Caldera

Run 18 code analysis tools against any repository, persist results to a DuckDB warehouse, and generate an actionable insights report — all in one command.

## Getting Started

```bash
make setup                                          # one-time setup
make analyze REPO=/path/to/repo                     # analyze a local repository
make analyze REPO=https://github.com/user/project   # or a remote one
make analyze REPO=/path/to/repo PIPELINE_LLM=0      # skip LLM eval + top3 extraction
make analyze REPO=/path/to/repo SKIP_TOOLS=a,b      # skip tools (comma-separated)
make collect REPO=/path/to/repo                     # artifacts-only bundle (manifest + outputs + logs)
make analyze-bundle REPO=/path/to/repo BUNDLE=artifacts/<repo_id>/<run_id>  # ingest + report from bundle
```

See [docs/USER_GUIDE.md](docs/USER_GUIDE.md) for the full getting-started guide, or run `make help` for all available targets.

## How It Works

```
 18 Analysis Tools          DuckDB Landing Zone         dbt Transforms            Report
┌──────────────────┐      ┌─────────────────────┐     ┌──────────────────┐     ┌──────────────┐
│ scc, lizard,     │ JSON │ Schema validation    │ SQL │ Staging models   │     │ HTML report  │
│ semgrep, trivy,  │─────>│ Quality rules        │────>│ Unified metrics  │────>│ LLM eval     │
│ gitleaks, ...    │      │ Entity persistence   │     │ Directory rollups│     │ Top 3 insights│
└──────────────────┘      └─────────────────────┘     └──────────────────┘     └──────────────┘
```

## Tools (18)

Each tool is self-contained under `src/tools/<tool>/` with its own Makefile, schemas, and tests:

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

## Repository Layout

```
docs/                       # Architecture + standards
src/tools/                  # Individual tools (18 total)
src/sot-engine/             # SoT engine (dbt + persistence)
src/insights/               # Report generation and evaluation
src/common/                 # Shared utilities
src/shared/                 # Shared evaluation infrastructure
src/tool-compliance/        # Tool compliance scanner
src/architecture-review/    # Architecture conformance reviewer
```

## Commands

```bash
make setup                  # One-time project + tool setup
make analyze REPO=<path>    # Full pipeline (tools + dbt + report + eval)
make report                 # Regenerate report (optionally RUN_PK=N)
make list-runs              # Show all collection runs
make status                 # Check prerequisites and health
make clean-db               # Remove database, start fresh
make compliance             # Run tool compliance scanner
make test                   # Run all tests (pytest + tools + dbt)
```

Run `make help` for the complete list including advanced targets and variables.

## Virtual Environment

**Always use the project venv for Python commands.** All `make` targets handle this automatically. For manual commands: `.venv/bin/python <script>`.

## Evaluation Workflow

Per tool (from within `src/tools/<tool>/`):

1. `make setup` — install dependencies
2. `make analyze` — generate `outputs/<run-id>/output.json`
3. `make evaluate` — programmatic checks (writes to `evaluation/results/`)
4. `make evaluate-llm` — LLM judge results (also in `evaluation/results/`)

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | Getting started guide for new users |
| [docs/COMPLIANCE.md](docs/COMPLIANCE.md) | Tool readiness requirements and checks |
| [docs/PERSISTENCE.md](docs/PERSISTENCE.md) | Adapter pattern, entities, repositories |
| [docs/EVALUATION.md](docs/EVALUATION.md) | LLM judge infrastructure |
| [docs/REPORTS.md](docs/REPORTS.md) | dbt analyses and reports |
| [docs/TOOL_INTEGRATION_CHECKLIST.md](docs/TOOL_INTEGRATION_CHECKLIST.md) | Creating and integrating new tools |
| [docs/REFERENCE.md](docs/REFERENCE.md) | Technical specifications |
