# Project Caldera

Run 18 code analysis tools against any repository, persist results to a DuckDB warehouse, and generate an actionable insights report — all in one command.

## What is Project Caldera?

Most code analysis relies on a single tool or a handful of loosely connected scanners. The results live in separate dashboards, use different taxonomies, and leave teams piecing together a fragmented picture of their codebase. When stakeholders need a clear answer — "Is this codebase healthy?" or "What are the top risks?" — no single tool can provide one.

Project Caldera solves this by running **18 analysis tools** in a single pass, normalizing every result into a shared data model, and loading it into a DuckDB warehouse where dbt transforms raw findings into unified metrics. An insights engine then queries those metrics, applies evidence-backed risk scoring, and produces a comprehensive HTML report — complete with LLM-powered top-3 priorities — that gives a cohesive view of size, complexity, quality, security, coverage, duplication, licensing, and git history.

The result is a **Source-of-Truth (SoT) engine**: a repeatable, auditable pipeline that turns any Git repository into a structured dataset and a stakeholder-ready report.

## What It Delivers

- **HTML report with 42 sections** covering all major analysis dimensions — size, complexity, code smells, security vulnerabilities, secret detection, license compliance, duplication, coverage, dependency structure, and git authorship
- **DuckDB warehouse** (168 dbt models) for ad-hoc SQL queries against unified file-level, directory-level, and repository-level metrics
- **LLM-powered top-3 insights** that distill hundreds of findings into the most actionable priorities with supporting evidence
- **Evidence-backed execution risks** with composite risk scoring, rewrite assessment, and sampling rationale
- **Stakeholder-tailored reports** — CTO, Investor, and CEO profiles that select the sections most relevant to each audience
- **Trend analysis** via dbt snapshots and run-over-run comparison queries

## Use Cases

- **Technical due diligence** — Evaluate an acquisition target or vendor codebase with a single command
- **Code quality baseline** — Establish measurable starting metrics before a refactoring or modernization effort
- **Architecture review** — Understand structural patterns, dependency graphs, complexity hotspots, and knowledge risk across a codebase
- **Migration planning** — Assess rewrite risk, identify structural vs addressable constraints, and prioritize effort
- **Ongoing health monitoring** — Re-run periodically and use trend analyses to track improvement or regression

## Key Features

- **18 analysis tools** — size, complexity, code quality, security, coverage, duplication, licensing, symbols, dependencies, and git history (see full list below)
- **3 production modes** — LOCAL (analyst laptop), BUNDLE (hybrid runner + laptop), DOCKERIZED (cloud VM or single machine)
- **Cloud runs** — Spin up an ephemeral Hetzner VM, analyze, download results, and destroy — all via `make cloud-run`
- **Artifact bundles** — Collect tool outputs into a portable bundle for offline ingestion and reporting
- **dbt warehouse** — 168 models (51 staging + 117 marts), 2 snapshots, 23 analyses, with unified file/directory/repo metrics
- **CI/CD with 5 gates** — Preflight, Quality, Compliance, Production Smoke, and LLM Evaluation across branch promotion (develop → release → main)
- **Unified CLI** — `caldera` entry point with 10 subcommand groups (analyze, report, db, compliance, tools, dbt, export, cloud, docker, status)
- **LLM evaluation infrastructure** — Shared BaseJudge pattern with observability logging for all LLM interactions

---

## Getting Started

### Prerequisites

| Requirement | Check | Install |
|-------------|-------|---------|
| Python 3.12+ | `python3 --version` | [python.org](https://www.python.org/downloads/) |
| git | `git --version` | `brew install git` |
| make | `make --version` | Included with Xcode CLI tools |
| duckdb CLI (optional) | `duckdb --version` | `brew install duckdb` (for ad-hoc queries) |

Run `make status` to verify all prerequisites at once.

### Quick Start

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

## Production Modes

| Mode | Target | Tool Execution | Results Delivery |
|------|--------|---------------|------------------|
| **LOCAL** | Analyst laptop | Native tool Makefiles | Local filesystem |
| **BUNDLE** | Hybrid (runner + laptop) | Tools run elsewhere, artifacts shipped | Local filesystem |
| **DOCKERIZED** | Cloud VM / single machine | Everything in containers | Git results repository |

All modes produce the same logical outputs: tool JSON artifacts → DuckDB → dbt marts → HTML report. See [docs/PRODUCTION_MODES.md](docs/PRODUCTION_MODES.md) for full details.

## Repository Layout

```
src/tools/                  # Individual tools (18 total)
src/sot-engine/             # SoT engine: orchestrator, persistence (adapters/entities/repos), dbt
src/insights/               # Report generation (95 SQL queries, 84 Jinja2 templates)
src/common/                 # Shared utilities (path normalization, CLI parser, envelope formatter)
src/shared/                 # Shared evaluation infrastructure (BaseJudge, observability)
src/tool-compliance/        # Tool compliance scanner
src/architecture-review/    # Architecture conformance reviewer
scripts/                    # Automation (cloud-run, docker runner, export, bundle, CLI)
infra/                      # Terraform (Hetzner cloud runs, GitHub IaC)
docker/                     # Base images (python, java, dotnet, runner, orchestrator)
docs/                       # Architecture, standards, and guides
```

## Commands

### Core

```bash
make setup                  # One-time project + tool setup
make analyze REPO=<path>    # Full pipeline (tools + dbt + report + eval)
make report                 # Regenerate report (optionally COLLECTION_RUN_ID=<uuid>)
make list-runs              # Show all collection runs
make status                 # Check prerequisites and health
make clean-db               # Remove database, start fresh
make compliance             # Run tool compliance scanner
make test                   # Run all tests (pytest + tools + dbt)
```

### Cloud

```bash
make cloud-setup            # One-time: terraform init
make cloud-run REPO=<url>   # Spin up Hetzner VM, analyze, download results, destroy
make cloud-destroy           # Destroy cloud server (if KEEP_SERVER=1 was used)
make cloud-cleanup           # Destroy orphaned VMs older than TTL
```

### Docker

```bash
make docker-build-all                    # Build all images (bases + tools + runner + orchestrator)
make docker-build-tool TOOL=<name>       # Build a single tool image
make docker-test-tool TOOL=<name> REPO=<path>  # Test Docker vs native parity
./scripts/caldera-run --repo=<url>       # Full dockerized pipeline (Mode 3)
```

### Advanced

```bash
make collect REPO=<path>     # Collect artifacts into portable bundle
make analyze-bundle REPO=<path> BUNDLE=<dir>  # Ingest bundle + generate report
make export-results          # Export latest run to git results repository
make promote                 # Push current branch and open PR to correct base
make release                 # Create + push version tag (RELEASE_TYPE=major|minor|patch)
make pipeline-eval           # Full E2E: orchestrate → insights → LLM eval → top 3
```

Run `make help` for the complete list including all variables.

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `REPO` | (required) | Repository path or GitHub URL |
| `DB_PATH` | `~/.caldera/caldera_sot.duckdb` | Database location |
| `SKIP_TOOLS` | unset | Comma-separated tool names to skip |
| `PIPELINE_LLM` | `1` | Set to `0` to skip LLM evaluation |
| `CLOUD_SERVER` | `cx33` | Hetzner server type or preset name |
| `MAX_PARALLEL` | `1` | Max parallel tool containers (docker/cloud) |
| `CLONE_DEPTH` | unset | Clone depth for remote URLs (empty = full) |

See [CLAUDE.md](CLAUDE.md) for the full variable reference.

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
| [docs/PRODUCTION_MODES.md](docs/PRODUCTION_MODES.md) | Production deployment modes |
| [docs/CLOUD_ANALYSIS_GUIDE.md](docs/CLOUD_ANALYSIS_GUIDE.md) | Running analysis on cloud VMs |
| [docs/CI_CD.md](docs/CI_CD.md) | CI/CD pipeline and branch strategy |
| [docs/STATUS_AND_ROADMAP.md](docs/STATUS_AND_ROADMAP.md) | Project status and forward roadmap |
| [docs/INSIGHTS_PRODUCT_SPEC.md](docs/INSIGHTS_PRODUCT_SPEC.md) | Insights component product specification |
