# Project Caldera — Engineering Handover

> **Version:** v0.14.0-dev · **Date:** 2026-03-01 · **Status:** Production-ready

This document is a single-file deep reference for an incoming engineer. It covers every aspect of Project Caldera: architecture, all 18 analysis tools, all operation modes, the orchestrator, the dbt data warehouse, LLM evaluation infrastructure, CI/CD, and the forward roadmap.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [All 18 Analysis Tools](#3-all-18-analysis-tools)
4. [SoT Engine & Orchestrator](#4-sot-engine--orchestrator)
5. [dbt Data Warehouse](#5-dbt-data-warehouse)
6. [LLM Usage: Tool Evaluation](#6-llm-usage-tool-evaluation)
7. [LLM Usage: Insights & Reporting](#7-llm-usage-insights--reporting)
8. [All Operation Modes](#8-all-operation-modes)
9. [Running Caldera on a Large Repository](#9-running-caldera-on-a-large-repository)
10. [CI/CD Pipeline](#10-cicd-pipeline)
11. [Complete Command Reference](#11-complete-command-reference)
12. [Forward Roadmap](#12-forward-roadmap)

---

## 1. Executive Summary

Project Caldera is a **tool-first code analysis platform** that collects metrics from 18 independent analysis tools into a DuckDB warehouse, transforms them through dbt, and generates rich stakeholder reports. It was designed for technical due diligence, codebase health assessment, and ongoing quality monitoring.

**Core pipeline:**

```
Tools → JSON outputs → Adapters (validate + persist) → Landing Zone (DuckDB)
  → dbt transforms (staging → marts) → Insights reports (HTML/Markdown)
```

**Key characteristics:**

- **18 analysis tools** covering structure, size, complexity, code quality, security, dependencies, git history, coverage, and licensing
- **Unified data model** — every tool's output is normalized into a single DuckDB warehouse with 42 landing zone tables, 56 staging models, 121 mart models, and 2 SCD Type 2 snapshots
- **3 production modes** — LOCAL (analyst laptop), BUNDLE (portable artifacts), DOCKERIZED (containers) — plus ephemeral cloud VMs via Hetzner/Terraform
- **LLM evaluation** — 104 LLM judges across all 18 tools for automated quality assessment, plus insight-level report evaluation
- **Full CI/CD** — 5 pipeline gates from preflight to deep LLM evaluation, with branch promotion `develop → release → main`
- **layout-scanner as spine** — all tools join against a canonical file/directory registry, enabling cross-tool correlation

The platform is **production-ready** with all 18 tools at full maturity, Docker images published to GHCR, and cloud analysis operational.

---

## 2. Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TOOL LAYER (18 tools)                          │
│  layout-scanner │ scc │ lizard │ semgrep │ roslyn-analyzers │ sonarqube │  │
│  trivy │ gitleaks │ symbol-scanner │ scancode │ pmd-cpd │ devskim │       │
│  dotcover │ git-fame │ git-sizer │ git-blame-scanner │ dependensee │        │
│  coverage-ingest │                                                          │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ JSON outputs (envelope format)
┌────────────────────────────────────▼────────────────────────────────────────┐
│                           ADAPTER LAYER                                     │
│  Schema validation → Quality checks → Entity creation → Persistence         │
│  (18 tool-specific adapters in src/sot-engine/persistence/adapters/)        │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────────┐
│                         LANDING ZONE (DuckDB)                               │
│  lz_collection_runs │ lz_tool_runs │ lz_<tool>_* (42 tables total)         │
│  lz_run_quality_summary │ lz_quality_checks │ lz_evidence │ lz_claims │    │
│  lz_risks │ lz_warnings                                                    │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ dbt run
┌────────────────────────────────────▼────────────────────────────────────────┐
│                              MARTS (dbt)                                    │
│  56 staging → 121 marts (unified_file_metrics │ unified_run_summary │       │
│  unified_directory_metrics │ unified_repo_metrics │ rollup_* │ mart_*)      │
│  2 snapshots │ 25 analyses                                                  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────────┐
│                      INSIGHTS & REPORTING                                   │
│  44 report sections │ 89 SQL queries │ 90+ Jinja2 templates                 │
│  HTML + Markdown output │ LLM-enhanced executive summary │ Top-3 insights   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
src/
├── common/                  # Shared utilities (path normalization, CLI parser, envelope formatter)
├── insights/                # Consolidated reporting component
│   ├── sections/            # 44 report section modules
│   ├── queries/             # 89 SQL insight queries
│   ├── templates/           # 90+ Jinja2 templates (HTML + Markdown)
│   ├── scripts/             # evaluate.py, extract_top_insights.py, checks.py
│   └── evaluation/          # Insight-level LLM judges
├── shared/                  # Shared infrastructure
│   ├── evaluation/          # BaseJudge, JudgeResult, prompt templates
│   ├── llm/                 # LLM client (Claude CLI + SDK fallback)
│   └── observability/       # LLM interaction logging and tracing
├── tool-compliance/         # Tool readiness verification scanner
├── architecture-review/     # LLM-powered architecture reviewer sub-agent
├── tools/                   # Individual analysis tools (18 total)
│   └── <tool>/              # Each with: analyze.py, Makefile, schemas/, evaluation/, tests/
└── sot-engine/              # Core engine
    ├── orchestrator.py      # End-to-end workflow coordinator
    ├── execution.py         # Execution backend abstraction (LOCAL/DOCKER)
    ├── persistence/         # Data layer
    │   ├── entities.py      # Frozen dataclass definitions
    │   ├── repositories.py  # DuckDB CRUD operations
    │   ├── schema.sql       # Landing zone DDL (42 tables)
    │   ├── quality.py       # Data quality framework
    │   └── adapters/        # 18 tool-specific JSON → entity adapters
    └── dbt/                 # Data transformation
        ├── models/          # staging/ (56) + marts/ (121)
        ├── snapshots/       # SCD Type 2 (2)
        ├── analysis/        # Ad-hoc queries (25)
        └── profiles.yml     # DuckDB connection config

scripts/                     # Automation: collect, analyze_bundle, export_results, docker_runner, etc.
docker/                      # Container images: 3 bases + runner + orchestrator
infra/                       # Terraform for Hetzner cloud VMs + GitHub IaC
docs/                        # Documentation (this file + 15 reference docs)
tests/                       # Project-level integration tests
.github/                     # CI/CD workflows (5 gates)
```

### Key Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Tool independence** | Each tool is a standalone directory with its own venv, Makefile, and output schema. Tools know nothing about each other. |
| **Pluggable adapters** | Each tool has a dedicated adapter that maps JSON → frozen entities → DuckDB. Adding a tool requires only a new adapter. |
| **Frozen entities with validation** | All data entities are `@dataclass(frozen=True)` with `__post_init__` validation. No mutable state. |
| **Repo-relative paths everywhere** | All file paths are normalized: no leading `/`, `./`, or `..`; POSIX separators only. Enforced by `src/common/path_normalization.py`. |
| **layout-scanner as spine** | The layout-scanner creates canonical `file_id` and `directory_id` values. All other tools join against these IDs via foreign keys. |
| **Append-only data model** | Collection runs are immutable once completed. Use `--replace` to overwrite a `(repo_id, commit)` pair. |
| **Quality checks are advisory** | Data quality scores are computed and persisted but never block ingestion. |

---

## 3. All 18 Analysis Tools

### Tool Summary

| # | Tool | Category | Purpose | External Dependency | Judges |
|---|------|----------|---------|---------------------|--------|
| 1 | layout-scanner | Structure | Canonical file/directory registry with classification and language detection | None (pure Python) | 5 |
| 2 | scc | Size/Metrics | LOC, comments, blank lines, complexity per file and language | `scc` binary (v3.x) | 11 |
| 3 | lizard | Size/Metrics | Per-function cyclomatic complexity (CCN) and NLOC | None (`lizard` Python pkg) | 5 |
| 4 | semgrep | Code Quality | Code smell and quality issue detection via static patterns | `semgrep` CLI | 6 |
| 5 | roslyn-analyzers | Code Quality | .NET Roslyn analyzer violations (200+ rules) | .NET SDK 8+ | 6 |
| 6 | sonarqube | Code Quality | Full SonarQube CE analysis (issues, metrics, quality gates) | Docker + `sonar-scanner` | 5 |
| 7 | trivy | Security | CVE scanning, IaC misconfiguration, SBOM generation | `trivy` binary | 8 |
| 8 | gitleaks | Security | Secret detection across full git history | `gitleaks` binary | 5 |
| 9 | symbol-scanner | Dependencies | Code symbol extraction, call graphs, import maps | None (`tree-sitter` Python pkg) | 5 |
| 10 | scancode | Dependencies | License and copyright detection, risk classification | None (`spdx-tools` Python pkg) | 5 |
| 11 | pmd-cpd | Code Quality | Token-based copy-paste detection | Java 11+, PMD 7.0.0 | 5 |
| 12 | devskim | Security | Regex-based security linting (no compile needed) | .NET SDK + DevSkim CLI | 5 |
| 13 | dotcover | Coverage | .NET code coverage at assembly/class/method level | dotCover CLI or Coverlet (.NET) | 5 |
| 14 | git-fame | Git History | Git contributor statistics and ownership attribution | None (`git-fame` Python pkg) | 8 |
| 15 | git-sizer | Git History | Repository health and size metrics | `git-sizer` binary (v1.5.0) | 5 |
| 16 | git-blame-scanner | Git History | Per-file bus factor and knowledge concentration | `git` CLI | 6 |
| 17 | dependensee | Dependencies | .NET project/NuGet dependency graph analysis | DependenSee .NET global tool | 5 |
| 18 | coverage-ingest | Coverage | Multi-format coverage normalization (LCOV/Cobertura/JaCoCo/Istanbul) | None (pure Python) | 5 |

**Total LLM judges across all tools: 104** (range: 5–11 per tool).

### Tool Categories

**Structure & Registry:**
- **layout-scanner** — The foundational "Tool 0". Scans the filesystem to create a canonical registry of all files and directories. Produces stable `file_id` and `directory_id` values that all other tools reference via foreign keys. Classifies files (source, test, config, generated, docs, vendor), detects languages, and computes recursive/direct directory metrics. If layout-scanner fails, the entire pipeline aborts.

**Size & Metrics:**
- **scc** — Uses the `scc` binary (Sloc Cloc Code) for per-file and per-language line counts (code, comment, blank), complexity estimates, and an 18-section rich dashboard with Gini coefficient and language breakdown.
- **lizard** — Per-function complexity analysis. Produces cyclomatic complexity (CCN), NLOC, token count, parameter count, start/end lines, and fully qualified function names. Complements scc's file-level metrics with function-level granularity.

**Code Quality:**
- **semgrep** — Pattern-based code smell detection across Python, JavaScript, TypeScript, C#, Java, Go, Rust. Produces violation records with rule ID, severity, message, and location.
- **roslyn-analyzers** — .NET-specific: security vulnerabilities (SQL injection, XSS, weak crypto), design violations, resource management, dead code, performance issues via 200+ Roslyn rules. Requires .NET SDK.
- **sonarqube** — Starts an ephemeral SonarQube CE container, runs `sonar-scanner`, and extracts issues/metrics via REST APIs. Supports C#, Java, JavaScript, TypeScript.
- **pmd-cpd** — Token-based copy/paste detection using PMD's CPD. Can detect renamed variables (semantic comparison). Requires Java 11+.
- **devskim** — Microsoft DevSkim regex-based security linter. Works without compilation — ideal for due diligence on incomplete codebases.

**Security:**
- **trivy** — Comprehensive scanner by Aqua Security. CVEs in npm/pip/Maven/NuGet/Go, Terraform/CloudFormation/K8s misconfiguration, SBOM generation. Classifies by CRITICAL/HIGH/MEDIUM/LOW.
- **gitleaks** — Secret detection including historical secrets removed from current code but still in git history. Identifies API keys, credentials, tokens.

**Dependencies:**
- **symbol-scanner** — Extracts function/class definitions, call relationships, and import graphs. Supports Python (via `ast`) and C# (via tree-sitter/Roslyn). Enables coupling analysis and blast radius computation.
- **scancode** — License detection via pattern matching and SPDX header identification. Classifies by category (permissive, weak-copyleft, copyleft) and assesses overall risk level.
- **dependensee** — .NET-specific: project-to-project references, NuGet package dependencies, graph structure, circular dependency detection.

**Git History:**
- **git-fame** — Per-author contribution metrics: line counts, file ownership, commit attribution. Enables knowledge concentration analysis.
- **git-sizer** — Repository health using GitHub's `git-sizer`. Identifies size issues, scaling problems, LFS candidates. Reports pack sizes, object counts, blob sizes.
- **git-blame-scanner** — Per-file authorship via `git blame`. Computes knowledge silos, bus factor risks, and code churn patterns.

**Coverage:**
- **dotcover** — .NET code coverage via JetBrains dotCover or Coverlet. Assembly → namespace → type → method hierarchy.
- **coverage-ingest** — Reads LCOV, Cobertura XML, JaCoCo XML, and Istanbul JSON. Normalizes into a unified schema for cross-format gap analysis.

### Per-Tool Make Targets

Every tool supports these make targets (via `Makefile.common`):

```bash
cd src/tools/<tool>
make setup          # Create venv, install dependencies, download binaries
make analyze        # Run analysis (requires REPO_PATH or prior run)
make evaluate       # Programmatic evaluation (ground-truth assertions)
make evaluate-llm   # LLM evaluation (requires Claude CLI or API key)
make test           # Run tool-specific tests
make clean          # Remove outputs
```

### Tool Compliance Requirements

The compliance scanner (`src/tool-compliance/tool_compliance.py`) checks 6 gates per tool:

| Gate | What it checks |
|------|----------------|
| Structure | Required files: `analyze.py`, `Makefile`, `schemas/output.schema.json`, `evaluation/` |
| Schema | JSON Schema Draft 2020-12, `const` schema_version, 8 metadata fields, path normalization |
| Evaluation | Shared BaseJudge usage, 4+ judges, `{{ evidence }}` prompt placeholders |
| Testing | Test files exist, pytest passes |
| dbt | Staging and mart models exist for the tool |
| Adapter | Adapter module exists with `SCHEMA_PATH`, `LZ_TABLES`, `TABLE_DDL`, `QUALITY_RULES` |

### Adding a New Tool

```bash
# Generate tool scaffold with SoT integration files
python scripts/create-tool.py my-new-tool --sot-integration

# This creates:
# src/tools/my-new-tool/
#   ├── analyze.py
#   ├── Makefile
#   ├── requirements.txt
#   ├── schemas/output.schema.json
#   ├── evaluation/
#   │   ├── ground-truth/
#   │   └── llm/
#   │       ├── judges/
#   │       ├── orchestrator.py
#   │       └── prompts/
#   └── tests/

# Generate dbt models
python scripts/generate_dbt_models.py my-new-tool --table lz_my_new_tool_metrics --metrics col1,col2

# Seed ground truth
python scripts/seed_ground_truth.py my-new-tool src/tools/my-new-tool/outputs/run-id/output.json
```

See [docs/TOOL_INTEGRATION_CHECKLIST.md](TOOL_INTEGRATION_CHECKLIST.md) for the full integration guide.

---

## 4. SoT Engine & Orchestrator

### Orchestrator (`src/sot-engine/orchestrator.py`)

The orchestrator is the main entry point for the full pipeline. It coordinates tool execution, JSON ingestion, dbt transformation, and report generation.

#### CLI Arguments

**Required:**

| Argument | Description |
|----------|-------------|
| `--repo-path` | Path to the repository to analyze |
| `--repo-id` | Repository identifier (alphanumeric + `.`, `-`, `_`) |

**Run Identity:**

| Argument | Default | Description |
|----------|---------|-------------|
| `--run-id` | Random UUID | Unique run identifier |
| `--branch` | `"main"` | Branch name |
| `--commit` | `"0" * 40` | Git commit SHA (40 chars). Falls back to content-hash for non-git repos. |

**Storage:**

| Argument | Default | Description |
|----------|---------|-------------|
| `--db-path` | `~/.caldera/caldera_sot.duckdb` | DuckDB database path |
| `--output-root` | Tool-specific | Override root for tool outputs |
| `--schema-path` | `src/sot-engine/persistence/schema.sql` | DDL file path |
| `--log-path` | `~/.caldera/caldera_orchestrator_<run_id>.log` | Orchestrator log |
| `--summary-path` | Alongside log | JSON run summary output |
| `--dbt-summary-path` | None | JSON dbt summary output |

**Execution Control:**

| Argument | Default | Description |
|----------|---------|-------------|
| `--run-tools` | `false` | Execute tools (else ingest existing outputs) |
| `--run-dbt` | `false` | Run dbt after ingestion |
| `--replace` | `false` | Overwrite existing `(repo_id, commit)` run |
| `--continue-on-tool-failure` | `false` | Don't abort if a tool fails; status → `partial_success` |
| `--mode` | `"local"` | Execution mode: `local` or `docker` |
| `--max-parallel` | `1` | Parallel tool execution count |
| `--skip-tools` | None | Comma-separated tool names to skip |
| `--no-progress` | `false` | Disable rich progress display |

**Per-Tool Output Overrides:**
`--layout-output`, `--scc-output`, `--lizard-output`, `--roslyn-output`, `--semgrep-output`, `--sonarqube-output`, `--trivy-output`, `--gitleaks-output`, `--symbol-scanner-output`, `--scancode-output`, `--pmd-cpd-output`, `--devskim-output`, `--dotcover-output`, `--git-fame-output`, `--git-sizer-output`, `--git-blame-scanner-output`, `--dependensee-output`, `--coverage-output`

**Docker Config:** `--docker-image-prefix`, `--docker-network`, `--docker-repo-volume`, `--docker-artifacts-volume`

**dbt Config:** `--dbt-bin`, `--dbt-project-dir`, `--dbt-profiles-dir`, `--dbt-target-path`, `--dbt-log-path`

#### Pipeline Flow

```
Step 1/3 — Run Tools (if --run-tools)
  ├── Build ToolTask list from TOOL_CONFIGS, skip --skip-tools
  ├── Create ExecutionConfig → dispatch to backend.execute_batch()
  ├── layout-scanner is mandatory: if it fails, pipeline aborts
  └── If --output-root without --run-tools: discover existing JSON outputs

Step 2/3 — Ingest (always)
  ├── Call ingest_outputs(conn, ...) with all 18 tool output paths
  ├── Each adapter: validate JSON → create entities → persist to LZ tables
  └── Compute and persist run quality (trust score) → lz_run_quality_summary

Step 3/3 — dbt (if --run-dbt)
  └── Run dbt run + dbt test
```

#### Commit Hash Handling

The `--commit` argument defaults to 40 zeros (`0000000000000000000000000000000000000000`). If the provided commit is all-zeros:

1. The orchestrator calls `_compute_content_hash(repo_path)` — a deterministic SHA-1 over sorted file paths and contents
2. This content-based hash substitutes for the commit, enabling analysis of non-git repositories
3. During tool execution, each commit is validated via `git cat-file -e`; if it doesn't resolve, tools receive all-zeros

### Persistence Layer

#### Entities (`src/sot-engine/persistence/entities.py`)

All entities are frozen dataclasses with `__post_init__` validation:

```python
@dataclass(frozen=True)
class SccFileMetric:
    tool_run_id: str
    file_path: str       # Must be repo-relative
    language: str
    lines: int
    code: int
    comments: int
    blanks: int
    complexity: int
    bytes: int

    def __post_init__(self) -> None:
        _validate_identifier(self.tool_run_id, "tool_run_id")
        _validate_repo_relative_path(self.file_path, "file_path")
```

**Universal field:** `run_pk` (BIGINT from sequence `lz_run_pk_seq`) is the join key across all tool tables. Other fields like `file_id`, `directory_id`, `relative_path` vary by tool.

#### Repositories (`src/sot-engine/persistence/repositories.py`)

Bulk-insert CRUD classes:
- `CollectionRunRepository` — create/update/find collection runs
- `ToolRunRepository` — create/find tool runs within a collection
- 18 tool-specific repositories (e.g., `SccFileMetricRepository`) for bulk entity insertion

#### Schema (`src/sot-engine/persistence/schema.sql`)

42 landing zone tables organized as:

**Infrastructure:**
- `lz_collection_runs` — one row per `(repo_id, commit)` pair, unique constraint
- `lz_tool_runs` — one row per `(collection_run_id, tool_name)`, `run_pk` via sequence

**Layout-scanner (spine):**
- `lz_layout_files` — canonical file registry (`file_id`, path, language, classification)
- `lz_layout_directories` — canonical directory registry (`directory_id`, path, recursive/direct counts)

**Per-Tool Tables (selected):**

| Tool | Tables |
|------|--------|
| scc | `lz_scc_file_metrics` |
| lizard | `lz_lizard_file_metrics`, `lz_lizard_function_metrics`, `lz_lizard_excluded_files` |
| semgrep | `lz_semgrep_smells` |
| gitleaks | `lz_gitleaks_secrets` |
| roslyn | `lz_roslyn_violations` |
| devskim | `lz_devskim_findings` |
| sonarqube | `lz_sonarqube_issues`, `lz_sonarqube_metrics` |
| trivy | `lz_trivy_vulnerabilities`, `lz_trivy_targets`, `lz_trivy_iac_misconfigs` |
| git-sizer | `lz_git_sizer_metrics`, `lz_git_sizer_violations`, `lz_git_sizer_lfs_candidates` |
| symbol-scanner | `lz_code_symbols`, `lz_symbol_calls`, `lz_file_imports` |
| scancode | `lz_scancode_file_licenses`, `lz_scancode_summary` |
| pmd-cpd | `lz_pmd_cpd_file_metrics`, `lz_pmd_cpd_duplications`, `lz_pmd_cpd_occurrences` |
| dotcover | `lz_dotcover_assembly_coverage`, `lz_dotcover_type_coverage`, `lz_dotcover_method_coverage` |
| dependensee | `lz_dependensee_projects`, `lz_dependensee_project_refs`, `lz_dependensee_package_refs` |
| git-fame | `lz_git_fame_authors`, `lz_git_fame_summary` |
| git-blame-scanner | `lz_git_blame_summary`, `lz_git_blame_author_stats` |
| coverage-ingest | `lz_coverage_summary` |

**Quality & Observability:**
- `lz_run_quality_summary` — per-collection-run trust score and budget flags
- `lz_warnings` — per-warning detail rows for trend analysis
- `lz_quality_checks` — per-tool, per-check quality results

**Insights Persistence:**
- `lz_evidence` — evidence items from insight sections
- `lz_claims` — claims derived from evidence
- `lz_risks` — risks derived from claims

#### Data Quality Framework (`src/sot-engine/persistence/quality.py`)

```python
class CheckLevel(Enum):
    L1 = "L1"   # Pre-insert (schema, metadata)
    L2 = "L2"   # Post-insert (FK integrity, uniqueness)

class CheckSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
```

**`QualityScore`** — four weighted dimensions, each in `[0.0, 1.0]`:

| Dimension | Weight | Calculation |
|-----------|--------|-------------|
| Completeness | 0.30 | 1.0 if all 8 metadata fields present, else 0.5 |
| Validity | 0.30 | 1.0 if JSON schema validation passed, else 0.0 |
| Consistency | 0.25 | Ratio of passed L2 checks (FK + uniqueness) |
| Timeliness | 0.15 | Always 1.0 (real-time ingestion) |

The `overall` property is a weighted average rounded to 4 decimal places.

**`DataQualityChecker`** methods:
- `check_metadata(metadata, tool_name)` — verifies 8 required envelope fields
- `check_fk_integrity(table, fk_column, run_pk, tool_name)` — counts orphan FK references against `lz_layout_files`
- `check_uniqueness(table, key_columns, tool_name)` — counts duplicates
- `build_report(tool_name, checks, ...)` → `QualityReport`
- `persist_report(report, collection_run_id)` — upserts to `lz_quality_checks` (advisory, never raises)

#### Adapter Pattern (`src/sot-engine/persistence/adapters/`)

Each tool has an adapter module (e.g., `scc_adapter.py`) with module-level constants:

```python
SCHEMA_PATH = Path(__file__).parent / "..." / "schemas/output.schema.json"
LZ_TABLES = ["lz_scc_file_metrics"]          # Key columns only
TABLE_DDL = {"lz_scc_file_metrics": "..."}   # Full CREATE TABLE DDL
QUALITY_RULES = [...]                         # Post-persist quality checks
```

**Adapter flow:**
1. Validate JSON against `SCHEMA_PATH`
2. Ensure landing zone tables exist (via `TABLE_DDL`)
3. Map JSON fields → frozen entity instances
4. Bulk insert entities via repository
5. Run post-persist quality checks (`QUALITY_RULES`)
6. Resolve FKs via layout-scanner's `file_id` / `directory_id`

### Execution Backends (`src/sot-engine/execution.py`)

```python
class ExecutionMode(Enum):
    LOCAL = "local"
    DOCKER = "docker"
```

**`ExecutionConfig`** (frozen dataclass): `repo_path`, `repo_name`, `run_id`, `repo_id`, `branch`, `commit`, `output_root`, `max_parallel`

**`ToolTask`** (frozen dataclass): `name`, `tool_root`, `extra_env`

**`ExecutionResult`** (frozen dataclass): `tool_name`, `status` ("success"/"failed"), `duration_seconds`, `output_path`, `output_exists`, `output_bytes`, `error`, `returncode`

**`LocalBackend`** — runs each tool via `make analyze` subprocess. Sets environment: `REPO_PATH`, `REPO_NAME`, `RUN_ID`, `REPO_ID`, `BRANCH`, `OUTPUT_DIR`, `COMMIT`. Uses `ThreadPoolExecutor` when `max_parallel > 1`.

**`DockerBackend`** — runs `docker run --rm` with volume mounts for repo (read-only) and artifacts. Writes `execution.log` per tool.

**`get_backend(mode, docker_config)`** — factory function returning the appropriate backend.

---

## 5. dbt Data Warehouse

### Model Inventory

| Layer | Count | Location |
|-------|-------|----------|
| Staging | 56 | `src/sot-engine/dbt/models/staging/` |
| Marts | 121 | `src/sot-engine/dbt/models/marts/` |
| Snapshots | 2 | `src/sot-engine/dbt/snapshots/` |
| Analyses | 25 | `src/sot-engine/dbt/analysis/` |

### Staging Models (`models/staging/`)

One `stg_*` model per landing zone table. These normalize and aggregate data from the raw landing zone. Example: `stg_scc_file_metrics` selects from `lz_scc_file_metrics`, joins `lz_tool_runs` for the `collection_run_id`, and adds computed fields.

### Unified Marts

| Model | Purpose | Key Columns |
|-------|---------|-------------|
| `unified_file_metrics` | File-level join of all 18 tools via layout spine | 90+ columns: path, language, LOC, CCN, coverage, violations, secrets, duplication, authorship |
| `unified_directory_metrics` | Directory-level rollups with 22 distribution stats per metric | Uses layout-scanner recursive rollup as spine, joins 15 tool rollups via collection_run_id |
| `unified_run_summary` | Per-collection-run aggregation | Total LOC, CCN, coverage %, trust score, tool counts, status |
| `unified_repo_metrics` | Cross-run repo-level metrics | Latest and historical aggregations per repo_id |

### Rollup Models

Each tool gets up to 4 rollup models:

| Pattern | Description |
|---------|-------------|
| `rollup_<tool>_directory_counts_recursive` | Count aggregation for all files in directory subtree |
| `rollup_<tool>_directory_counts_direct` | Count aggregation for files directly in directory |
| `rollup_<tool>_directory_recursive_distributions` | 22 distribution statistics for recursive rollup |
| `rollup_<tool>_directory_direct_distributions` | 22 distribution statistics for direct rollup |

**Invariant:** `recursive_count >= direct_count` (enforced by dbt tests).

#### Distribution Statistics (22 per metric)

Every distribution rollup computes: `count`, `min`, `max`, `mean`, `median`, `stddev`, `p25`, `p50`, `p75`, `p90`, `p95`, `p99`, `skewness`, `kurtosis`, `cv` (coefficient of variation), `iqr` (interquartile range), `gini`, `theil`, `hoover`, `palma`, `top_share`, `bottom_share`.

### Hotspot Marts

Named `mart_*_hotspots` or `mart_*_risk`, these surface the most problematic files/directories:

- `mart_complexity_hotspots`, `mart_coverage_hotspots`, `mart_composite_file_hotspots`
- `mart_semgrep_rule_hotspots`, `mart_roslyn_rule_hotspots`, `mart_devskim_rule_hotspots`
- `mart_gitleaks_secret_hotspots`, `mart_pmd_cpd_clone_hotspots`
- `mart_authorship_risk`, `mart_git_blame_knowledge_risk`
- `mart_blast_radius_symbol`, `mart_circular_dependencies`, `mart_project_dependency_cycles`
- `mart_scancode_license_hotspots`, `mart_coverage_gap_analysis`
- And more (see `models/marts/` for complete list)

### Snapshots (SCD Type 2)

| Snapshot | Strategy | Purpose |
|----------|----------|---------|
| `snap_unified_run_summary` | Check (all columns) | Track run-level metrics over time |
| `snap_unified_repo_metrics` | Check (all columns) | Track repo-level metrics over time |

These add `dbt_valid_from` / `dbt_valid_to` columns for historical queries.

### Analyses (25 ad-hoc queries)

| Analysis | Purpose |
|----------|---------|
| `run_over_run_comparison` | Delta between two collection runs for the same repo |
| `file_regressions` | Files that got worse between runs |
| `report_repo_health_snapshot` | Comprehensive single-run health report |
| `quality_score_trend` | Trust score over time |
| `warning_trend` | Warning count over time |
| `inequality_by_gini` | Gini coefficient analysis per metric |
| `inequality_by_palma` | Palma ratio analysis |
| `inequality_concentration` | Concentration metrics across tools |
| `inequality_cross_tool` | Cross-tool inequality comparison |
| `module_health_scores` | Per-directory health scoring |
| `distribution_shape_patterns` | Distribution shape classification |
| `distribution_tail_risk` | Right-tail risk identification |
| `report_file_hotspots` | File-level hotspot report |
| `report_directory_hotspots_full` | Directory-level hotspot report |
| `report_cross_tool_insights` | Multi-tool correlation insights |
| And 10 more... | |

### Running dbt

```bash
# From project root (via Make):
make dbt-run           # Execute all models
make dbt-test          # Run all tests
make dbt-test-reports  # Report-specific tests only

# Directly:
cd src/sot-engine/dbt
dbt run --profiles-dir .
dbt test --profiles-dir .

# With specific repo filtering (analyses):
dbt run-operation run_over_run_comparison --vars '{"repo_id": "my-project"}'
```

**Configuration:** `profiles.yml` uses the `$CALDERA_DB_PATH` environment variable (default: `~/.caldera/caldera_sot.duckdb`).

---

## 6. LLM Usage: Tool Evaluation

### Overview

Every tool has 4–11 LLM judges that score tool output quality on a 1–5 scale. The evaluation infrastructure is built on a shared `BaseJudge` class with observability, heuristic fallbacks, and synthetic repo detection.

### BaseJudge (`src/shared/evaluation/base_judge.py`)

#### Class Interface

```python
class BaseJudge(ABC):
    # Subclasses MUST implement:
    @property
    def dimension_name(self) -> str: ...    # e.g., "accuracy", "coverage"
    @property
    def weight(self) -> float: ...          # 0.0–1.0
    def collect_evidence(self) -> dict[str, Any]: ...

    # Constructor
    def __init__(
        self,
        model: str = "opus-4.5",
        timeout: int = 120,
        working_dir: Path | None = None,
        output_dir: Path | None = None,
        ground_truth_dir: Path | None = None,
        use_llm: bool = True,
        trace_id: str | None = None,
        enable_observability: bool = True,
        evaluation_mode: str | None = None,  # "synthetic" or "real_world"
    )
```

#### JudgeResult

```python
@dataclass
class JudgeResult:
    dimension: str              # Evaluation dimension name
    score: int                  # 1–5 scale
    confidence: float           # 0.0–1.0
    reasoning: str              # Explanation of score
    evidence_cited: list[str]   # Evidence points referenced
    recommendations: list[str]  # Improvement suggestions
    sub_scores: dict[str, int]  # Sub-dimension scores
    raw_response: str = ""      # Raw LLM response

    def is_passing(threshold: int = 3) -> bool  # score >= threshold
```

#### Evaluation Pipeline

```
evaluate()
  ├── collect_evidence()          # Abstract: subclass gathers tool-specific evidence
  ├── if use_llm=False:
  │   └── run_heuristic_evaluation(evidence)  # Default: score=3, confidence=0.6
  └── if use_llm=True:
      ├── build_prompt(evidence)   # Load template, replace {{ evidence }} placeholders
      ├── invoke_claude(prompt)    # Call LLM via shared client
      └── parse_response(response) # Extract JSON → JudgeResult (fallback: regex score parse)
```

#### Prompt Templates

Located in `evaluation/llm/prompts/{dimension}.md` per tool. Key features:
- `{{ evidence }}` placeholder replaced with collected evidence JSON
- Individual `{{ key_name }}` placeholders for specific evidence fields
- 1–5 scoring rubric embedded in prompt
- JSON response format specified
- `build_prompt()` raises `ValueError` if any unresolved `{{ ... }}` placeholders remain

#### Model Mapping

```python
MODEL_MAP = {
    "sonnet":   "claude-sonnet-4-20250514",
    "opus":     "claude-opus-4-20250514",
    "opus-4.5": "claude-opus-4-5-20250514",
    "haiku":    "claude-haiku-4-20250514",
}

CLI_MODEL_MAP = {
    "opus-4.5": "opus",  # Claude CLI uses short aliases
}
```

#### Synthetic Repo Detection

The `evaluation_mode` property auto-detects synthetic test repositories by checking `output_dir` path components against known patterns:

```python
SYNTHETIC_PATTERNS = {
    "api-keys", "aws-credentials", "database-creds", "private-keys",
    "no-secrets", "mixed-secrets", "historical-secrets", "cloud-mixed",
    "synthetic", "vulnerable-npm", "clean-npm", "null-safety",
    "async-patterns", "resource-management", "api-conventions",
}
```

When detected, `load_synthetic_evaluation_context()` and `get_interpretation_guidance()` provide additional context for calibrated scoring.

### LLM Client (`src/shared/llm/client.py`)

Two invocation paths with automatic fallback:

**SDK Path** (opt-in via `USE_ANTHROPIC_SDK=1`):
- Requires `anthropic` Python package + `ANTHROPIC_API_KEY`
- Direct `anthropic.Anthropic().messages.create()`
- Returns `None` if prerequisites missing → triggers CLI fallback

**CLI Path** (default):
- Locates `claude` binary via `shutil.which`
- Command: `claude --print - --model {model} --output-format text --max-turns 5 --system-prompt "..."`
- Prompt passed via **stdin** (avoids ARG_MAX limits and Claude misinterpreting file content)
- Strips `CLAUDECODE` and `CLAUDE_CODE` env vars to prevent nesting detection

**Error classification:** permission errors, ENOENT, auth/API key issues, rate limits, empty responses, timeouts.

### Observability (`src/shared/observability/`)

Every LLM invocation is logged for auditability:

**`ObservabilityConfig`** — configurable via `LLM_OBSERVABILITY_*` env vars:
- `enabled`, `log_dir` (default: `output/llm_logs`), `retention_days` (30)
- Optional: `include_prompts`, `include_responses`, `capture_token_usage`
- `enable_trace_correlation` — UUID-based trace IDs across all judges in a run

**`LLMInteraction`** — captures per-invocation data:
- Identification: `interaction_id`, `trace_id`
- Timing: `timestamp_start`, `timestamp_end`, `duration_ms`
- I/O: `user_prompt`, `response_content`, token counts, `status` (success/error/timeout)
- Parsed: `parsed_score`, `parsed_reasoning`, `parsed_sub_scores`

**`FileStore`** — date-partitioned JSONL persistence:
- Files at `{log_dir}/{YYYY-MM-DD}/interactions.jsonl`
- Query methods: `query_by_trace()`, `query_by_judge()`, `query_by_status()`
- `get_evaluation_span(trace_id)` — aggregates interactions into an `EvaluationSpan`
- `cleanup_old_logs(retention_days)` — removes old date directories

**`LLMLogger`** — wraps `FileStore` with `start_interaction()` / `complete_interaction()` lifecycle:
- Maintains `_pending` dict for in-flight interactions
- Logs to console via `structlog` (optional)

### Per-Tool Judge Structure

Each tool has:
- `evaluation/llm/judges/` — individual judge classes inheriting from `BaseJudge`
- `evaluation/llm/orchestrator.py` — runs all judges, computes weighted overall score
- `evaluation/llm/prompts/` — Markdown prompt templates per dimension

**Example: trivy has 8 judges:**
- `vulnerability_accuracy` — CVE detection accuracy
- `severity_accuracy` — severity classification correctness
- `false_positive_rate` — false positive assessment
- `iac_quality` — IaC misconfiguration detection quality
- `sbom_completeness` — SBOM generation completeness
- `freshness_quality` — vulnerability data freshness
- `vulnerability_detection` — overall detection capability
- Plus base

### Invocation

```bash
# All tools:
make tools-evaluate-llm

# Single tool:
cd src/tools/trivy && make evaluate-llm

# Without LLM (heuristic fallback):
cd src/tools/trivy && make evaluate
```

---

## 7. LLM Usage: Insights & Reporting

### Insights Component (`src/insights/`)

The insights component generates stakeholder reports from dbt mart data.

**Scale:** 44 report section modules, 89 SQL queries, 90+ Jinja2 templates (HTML + Markdown).

#### Data Flow

```
dbt marts (DuckDB)
  → data_fetcher.py loads + parameterizes SQL from queries/
  → section .py modules produce structured data
  → Jinja2 templates render HTML + Markdown output
  → optional LLM enhancement (executive summary, top-3 insights)
```

#### Report Sections (44 sections across 12 categories)

| Category | Sections |
|----------|----------|
| Executive | `executive_summary`, `composite_risk`, `delta_summary` |
| Structure | `directory_structure`, `directory_analysis`, `component_inventory`, `language_coverage` |
| Size/Complexity | `code_size_hotspots`, `function_complexity`, `file_hotspots`, `distribution_insights` |
| Quality | `code_quality_rules`, `roslyn_violations`, `sonarqube_deep_dive`, `code_inequality` |
| Security | `vulnerabilities`, `iac_misconfigs`, `devskim_security`, `secrets` |
| Duplication | `code_duplication` |
| Dependencies | `dependency_health`, `import_dependencies`, `coupling_analysis`, `coupling_debt`, `blast_radius`, `circular_dependencies` |
| Coverage | `coverage_gap`, `dotcover_coverage`, `tool_coverage_dashboard`, `tool_readiness` |
| Authorship | `authorship_risk`, `knowledge_risk`, `rewrite_risk` |
| Git Health | `git_sizer`, `repo_health`, `module_health` |
| Licensing | `license_compliance` |
| Evidence | `evidence_pack`, `claim_register`, `risk_register`, `sampling_rationale`, `cross_tool`, `technical_debt_summary` |

#### LLM in Insights

**1. Report Quality Evaluation** (`src/insights/scripts/evaluate.py`):
- **60% programmatic checks** — structural, content, and data-backed assertions
- **40% LLM judges** — via `LLMOrchestrator` with multiple insight-quality judges
- Produces `EvaluationSummary` with `overall_score`, `pass_status`, per-check details, and suggestions

**2. Top-3 Insight Extraction** (`src/insights/scripts/extract_top_insights.py`):
- `InsightQualityJudge` identifies the 3 most impactful findings from report data
- Outputs: `TopInsight` (rank, insight, evidence, rationale), `ImprovementProposal`, `missed_critical_issues`
- Verdict: PASS / WEAK_PASS / FAIL

**3. Executive Summary** — LLM-enhanced narrative section in the report.

#### Stakeholder Profiles

Reports can be tailored to different audiences:
- **CTO** — technical depth, architecture, quality trends
- **Investor** — risk assessment, compliance, maturity
- **CEO** — executive summary, top findings, action items

### Report Generation

```bash
# Generate report from latest run:
make report

# Generate report for specific run:
make report COLLECTION_RUN_ID=<uuid>

# Full pipeline with evaluation:
make pipeline-eval
```

Reports are written to `src/insights/output/pipeline/runs/<repo_id>/<run_id>/`.

---

## 8. All Operation Modes

Caldera supports three production modes, all producing the same logical output. A fourth "cloud" path extends Mode 3 to ephemeral VMs.

### Mode 1: LOCAL (Analyst Laptop)

```
┌──────────────────────────────────────────────────┐
│                  Analyst Laptop                    │
│                                                    │
│  make analyze REPO=/path/to/repo                  │
│    ├── Tools run natively (per-tool .venv)         │
│    ├── Orchestrator ingests JSON → DuckDB          │
│    ├── dbt transforms LZ → marts                   │
│    └── Insights generates HTML/MD report           │
│                                                    │
│  DB: ~/.caldera/caldera_sot.duckdb                │
│  Reports: src/insights/output/pipeline/runs/...   │
└──────────────────────────────────────────────────┘
```

**Invocation:**
```bash
make analyze REPO=/path/to/repo
# Or with URL:
make analyze REPO=https://github.com/org/project
```

**Characteristics:**
- Sequential tool execution (parallel via `MAX_PARALLEL`)
- Fast iteration cycle
- Host-dependent reproducibility (depends on installed binaries)
- All prerequisites must be on the laptop

**Prerequisites:** Python 3.12, git, make. Optional per tool: .NET SDK 8+ (roslyn/dotcover/devskim/dependensee), Java 11+ (pmd-cpd), Docker (sonarqube).

**Key variables:**

| Variable | Default | Purpose |
|----------|---------|---------|
| `REPO` | required | Local path or GitHub URL |
| `SKIP_TOOLS` | unset | Comma-separated tools to skip |
| `PIPELINE_LLM` | `1` | Set `0` to skip LLM evaluation |
| `REPLACE` | unset | Set `1` to overwrite existing run |
| `CONTINUE_ON_TOOL_FAILURE` | unset | Set `1` to keep going if a tool fails |

### Mode 2: BUNDLE (Portable Artifacts)

```
┌──────────────────────┐        ┌──────────────────────┐
│   Runner Machine      │  ship  │   Analyst Laptop      │
│                        │ ────► │                        │
│  make collect          │       │  make analyze-bundle   │
│    └── Tools run       │       │    ├── Ingest bundle   │
│    └── Bundle created  │       │    ├── dbt transforms  │
│                        │       │    └── Generate report  │
└──────────────────────┘        └──────────────────────┘
```

**Two-phase workflow:**

```bash
# Phase 1: Collect artifacts (on runner machine)
make collect REPO=/path/to/repo BUNDLE_DIR=artifacts BUNDLE_TAR=1

# Phase 2: Ingest + report (on analyst laptop)
make analyze-bundle REPO=/path/to/repo BUNDLE=artifacts/<repo_id>/<run_id>
```

**Bundle structure:**
```
artifacts/
└── <repo_id>/
    └── <run_id>/
        ├── layout-scanner/output.json
        ├── scc/output.json
        ├── lizard/output.json
        ├── ... (one dir per tool)
        └── manifest.json
```

**Characteristics:**
- High reproducibility (bundle is immutable)
- Runner needs tool dependencies; laptop only needs Python 3.12 + git + make
- Useful for CI pipelines and air-gapped environments

### Mode 3: DOCKERIZED (Containers)

```
┌─────────────────────────────────────────────────────────────┐
│                        Docker Host                           │
│                                                              │
│  Stage 1: caldera-runner                                     │
│    ├── Spawns 17 tool containers (max-parallel configurable) │
│    ├── Each tool writes output.json to shared volume         │
│    └── Writes LATEST.json pointer file                       │
│                                                              │
│  Stage 2: caldera-orchestrator                               │
│    ├── Reads LATEST.json → finds bundle                      │
│    ├── BUNDLE-mode ingest → DuckDB                          │
│    ├── dbt transforms                                        │
│    └── Generate report                                       │
│                                                              │
│  Volumes: caldera-repo, caldera-artifacts, caldera-db,       │
│           caldera-results                                    │
└─────────────────────────────────────────────────────────────┘
```

**Invocation:**
```bash
./scripts/caldera-run --repo=https://github.com/org/project
```

**Container images (22 total):**

| Image | Purpose |
|-------|---------|
| `caldera-python-base` | Shared Python 3.12 base |
| `caldera-java-base` | Java 21 for pmd-cpd |
| `caldera-dotnet-base` | .NET SDK for roslyn/dotcover/devskim/dependensee |
| `caldera-tool-<name>` × 17 | One per analysis tool (layout-scanner shares python-base) |
| `caldera-runner` | Tool dispatcher (Python + Docker CLI) |
| `caldera-orchestrator` | Bundle ingest + dbt + reporting |

**Docker commands:**
```bash
make docker-build-all                          # Build everything
make docker-pull-all                           # Pull pre-built from GHCR
make docker-build-tool TOOL=scc                # Build single tool image
make docker-test-tool TOOL=scc REPO=/path      # Compare Docker vs native output
make docker-test-all REPO=/path                # Batch parity test
```

**Key variables:**

| Variable | Default | Purpose |
|----------|---------|---------|
| `MAX_PARALLEL` | `4` | Concurrent tool containers |
| `GHCR_REGISTRY` | `ghcr.io/alexander-stage-hoco` | Pre-built image registry |
| `CALDERA_TOOL_IMAGE_PREFIX` | `caldera-tool-` | Tool image name prefix |
| `CALDERA_RUNNER_IMAGE` | `caldera-runner` | Runner image name |
| `CALDERA_ORCHESTRATOR_IMAGE` | `caldera-orchestrator` | Orchestrator image name |

### Mode 4: Cloud (Hetzner VM)

```
Local machine                          Hetzner Cloud VM
─────────────                          ─────────────────
terraform apply ──────────────────────► Create VM (cloud-init: git, python, docker)
                                        Clone Caldera + target repo
                                        make analyze (full pipeline)
scp results ◄─────────────────────────  Export DuckDB + reports + manifest.json
terraform destroy ────────────────────► Destroy VM
```

**Invocation:**
```bash
# One-time setup:
make cloud-setup

# Run analysis:
make cloud-run REPO=https://github.com/org/project

# Check status:
make cloud-status

# Manual cleanup:
make cloud-destroy
make cloud-cleanup TTL_HOURS=4 DRY_RUN=1
```

**Server presets:**

| Preset | Hetzner Type | vCPUs | RAM | Disk | Use Case |
|--------|-------------|-------|-----|------|----------|
| small | cx23 | 2 | 4 GB | 40 GB | Small repos (<10k files) |
| medium | cx33 | 4 | 8 GB | 80 GB | Medium repos (default) |
| large | cx43 | 8 | 16 GB | 160 GB | Large repos (>100k files) |
| xlarge | cx53 | 16 | 32 GB | 320 GB | Monorepos |

**Budget guards:**

| Variable | Purpose |
|----------|---------|
| `MAX_DURATION` | Max analysis duration in seconds |
| `MAX_COST` | Max estimated cost in EUR |
| `KEEP_SERVER` | Set `1` to keep VM alive after run |
| `TTL_HOURS` | Max VM age for `cloud-cleanup` (default: 4) |

**Prerequisites:** `terraform` CLI, `infra/terraform.tfvars` with `HCLOUD_TOKEN` and SSH key path, `.env` with API keys.

**Cloud pipeline defaults:** `PIPELINE_LLM=0` (LLM disabled), `MAX_PARALLEL=4`.

---

## 9. Running Caldera on a Large Repository

### LOCAL Mode

```bash
make analyze REPO=/path/to/large-repo \
    SKIP_TOOLS=sonarqube,dotcover,dependensee \
    PIPELINE_LLM=0 \
    CONTINUE_ON_TOOL_FAILURE=1
```

**Tips:**
- Skip .NET tools if not analyzing a .NET codebase
- Disable LLM evaluation for speed (`PIPELINE_LLM=0`)
- Use `CONTINUE_ON_TOOL_FAILURE=1` — some tools may time out on very large repos
- Consider `SKIP_TOOLS=git-fame,git-blame-scanner` for repos with >50k commits (these scan full history)

### BUNDLE Mode

```bash
# On a powerful machine or CI:
make collect REPO=/path/to/large-repo \
    SKIP_TOOLS=git-fame,git-blame-scanner,gitleaks \
    BUNDLE_TAR=1

# Transfer the tarball, then on laptop:
make analyze-bundle REPO=/path/to/large-repo \
    BUNDLE=artifacts/<repo_id>/<run_id>
```

### DOCKERIZED Mode

```bash
./scripts/caldera-run \
    --repo=https://github.com/org/large-repo \
    --max-parallel=8 \
    --skip-tools=git-fame,git-blame-scanner
```

### Cloud Mode (Recommended for Very Large Repos)

```bash
make cloud-run \
    REPO=https://github.com/org/large-repo \
    CLOUD_SERVER=large \
    SKIP_TOOLS=git-fame,git-blame-scanner,gitleaks \
    MAX_PARALLEL=8 \
    CLONE_DEPTH=1 \
    MAX_DURATION=1800 \
    MAX_COST=0.05
```

### Sizing Guide

| Repo Size | Files | Commits | Recommended Server | Estimated Duration |
|-----------|-------|---------|-------------------|-------------------|
| Small | <10k | <5k | small (cx23) | 5–15 min |
| Medium | 10k–50k | 5k–20k | medium (cx33) | 15–45 min |
| Large | 50k–200k | 20k–100k | large (cx43) | 45–120 min |
| Monorepo | >200k | >100k | xlarge (cx53) | 2–4 hours |

### Clone Depth Strategy

| Scenario | `CLONE_DEPTH` | Why |
|----------|--------------|-----|
| Code quality assessment | `1` | Only need current state |
| Security audit | unset (full) | gitleaks needs full history for historical secrets |
| Due diligence | `100` | Balance: recent history without full clone |

### Tools That Are Slow on Large Repos

| Tool | Why It's Slow | Mitigation |
|------|--------------|------------|
| git-fame | Scans every commit for attribution | Skip on >50k commits |
| git-blame-scanner | Runs `git blame` on every file | Skip on >100k files |
| gitleaks | Scans full git history | Use `CLONE_DEPTH` or skip |
| semgrep | Pattern matching across all source files | Generally fast, but >500k files can be slow |
| pmd-cpd | Token comparison across all files | Skip on non-Java projects |

### Performance Tuning

```bash
# Maximize parallelism (Docker/cloud only):
MAX_PARALLEL=8

# Skip irrelevant tools:
SKIP_TOOLS=dotcover,dependensee,roslyn-analyzers  # Non-.NET project

# Shallow clone:
CLONE_DEPTH=1

# Disable LLM:
PIPELINE_LLM=0
```

---

## 10. CI/CD Pipeline

### Branch Strategy

```
feature/* ─┐
fix/*      ─┼─ PR ──► develop ──► PR ──► release ──► PR ──► main ──► tag vX.Y.Z
tool/*/**  ─┤
infra/*    ─┘
```

**Branch naming conventions:**
- `feature/*`, `fix/*`, `tool/*/**`, `infra/*` → PR to `develop`
- `develop` → PR to `release` (pre-production staging)
- `release` → PR to `main` (production)
- Tags `vX.Y.Z` cut from `main` via `make release RELEASE_TYPE=major|minor|patch`

### Pipeline Gates

| Gate | Name | Trigger | Duration | What It Checks |
|------|------|---------|----------|----------------|
| 0 | Preflight | Push to feature branches | ~30 s | `make compliance-preflight` |
| A | Fast Quality | Every PR | ~2 min | Preflight + unit tests + observability compliance |
| B | Compliance Report | PRs to `release`/`main` | ~10 s | Full compliance scan; uploads JSON + MD artifacts |
| C | Production Smoke | PRs to `release` | ~10–15 min | Clean DB + LOCAL pipeline + BUNDLE ingest + report; trust score >= 50 |
| E | Deep Tool Evaluation | Tag `vX.0.0` on `main` | ~30–45 min | `make compliance-full` with LLM judges; environment-protected |

### Workflow Files

| File | Purpose |
|------|---------|
| `.github/workflows/preflight.yml` | Gate 0: fast compliance checks |
| `.github/workflows/ci.yml` | Gates A–C: router workflow |
| `.github/workflows/tool-evaluation-major.yml` | Gate E: LLM judges on major releases |
| `.github/workflows/release.yml` | Auto-create GitHub Release from tag |
| `.github/workflows/docker-images.yml` | Build + push images to GHCR (main, tags) |
| `.github/workflows/cloud-smoke.yml` | Cloud smoke test (manual + major tags) |
| `.github/actions/caldera-setup/action.yml` | Composite action: Python 3.12 + venv cache |

### Branch Protection

| Branch | Required Gates | Additional Rules |
|--------|---------------|-----------------|
| `develop` | Gate A | Require PR |
| `release` | Gates A, B, C | Require PR from `develop` |
| `main` | Gates A, B | Require PR from `release` (promotion policy) |

### GitHub Environments

| Environment | Secrets | Protection |
|-------------|---------|------------|
| `llm-eval` | `ANTHROPIC_API_KEY` | Manual approval required |
| `cloud` | `HCLOUD_TOKEN`, `SSH_PRIVATE_KEY` | Manual approval required |

### Caching

- Project `.venv/` — keyed on `requirements.txt` hash
- pip cache
- Tool venvs and binaries (`scc`, `git-sizer`, `gitleaks`, `trivy`) — keyed on tool Makefile hashes
- Used in Gates C and E for faster execution

### Docker Image CI

Triggered on: push to `main`, tags, manual dispatch. Workflow: detect-changes → build-bases → build-tools (matrix, max-parallel 10) → build-infra (runner + orchestrator). Publishes to `ghcr.io/alexander-stage-hoco/`.

### GitHub IaC

Branch protection rules, environments, and long-lived branches are managed as Terraform code in `infra/github/`:

```bash
make github-setup   # terraform init
make github-plan    # Preview changes
make github-apply   # Apply (requires GITHUB_TOKEN)
```

---

## 11. Complete Command Reference

### User-Facing

| Command | Purpose |
|---------|---------|
| `make setup` | One-time project + all tool venv setup |
| `make setup-core` | Project venv only (no tool venvs) |
| `make cli-install` | Install `caldera` CLI in editable mode |
| `make analyze REPO=<path\|url>` | Full E2E pipeline |
| `make report` | Regenerate report (optional `COLLECTION_RUN_ID=<uuid>`) |
| `make list-runs` | Show all collection runs |
| `make status` | Check prerequisites |
| `make doctor` | Extended health check (dbt, secrets, docker) |
| `make clean-db` | Remove database, start fresh |
| `make collect REPO=<path>` | Collect tool artifacts into bundle |
| `make analyze-bundle REPO=<path> BUNDLE=<dir>` | Ingest bundle + generate report |
| `make prune-outputs` | Delete tool outputs (requires `CONFIRM=1`) |
| `make promote` | Push branch and open PR to correct base |
| `make promote-develop` | PR current branch → develop |
| `make promote-release` | PR develop → release |
| `make promote-main` | PR release → main |
| `make release RELEASE_TYPE=<type>` | Create + push version tag (major/minor/patch) |
| `make export-results` | Export latest run to results repo |
| `make create-risk-issues` | Create GitHub issues from risk register (`APPLY=1`) |

### Tool Operations

| Command | Purpose |
|---------|---------|
| `make tools-setup` | Run `make setup` for all 18 tools |
| `make tools-analyze` | Run analysis for all tools |
| `make tools-evaluate` | Run programmatic evaluations |
| `make tools-evaluate-llm` | Run LLM evaluations |
| `make tools-test` | Execute all tool tests |
| `make tools-clean` | Clean tool outputs |

### dbt

| Command | Purpose |
|---------|---------|
| `make dbt-migrate` | Apply schema migrations |
| `make dbt-run` | Execute all dbt models |
| `make dbt-test` | Run all dbt tests |
| `make dbt-test-reports` | Run report-specific tests only |

### Compliance & Review

| Command | Purpose |
|---------|---------|
| `make compliance` | Structural compliance (~10 s) |
| `make compliance-preflight` | Fast structure checks (~100 ms) |
| `make compliance-full` | Full compliance with tool execution (~30 min) |
| `make arch-review ARCH_REVIEW_TARGET=<tool>` | LLM architecture review |

### Testing

| Command | Purpose |
|---------|---------|
| `make test` | Fast unit tests only |
| `make test-unit` | Unit tests (explicit) |
| `make test-integration` | Tools tests + dbt |
| `make test-all` | Full suite |

### Orchestration

| Command | Purpose |
|---------|---------|
| `make orchestrate` | Run orchestrator directly |
| `make pipeline-eval` | Full E2E: orchestrate → insights → LLM eval → top-3 |

### Docker

| Command | Purpose |
|---------|---------|
| `make docker-build-base` | Build base images |
| `make docker-build-tool TOOL=<name>` | Build single tool image |
| `make docker-build-tools` | Build all 17 tool images |
| `make docker-build-runner` | Build runner image |
| `make docker-build-orchestrator` | Build orchestrator image |
| `make docker-build-all` | Build everything |
| `make docker-pull-all` | Pull pre-built from GHCR |
| `make docker-test-tool TOOL=<name> REPO=<path>` | Docker vs native parity test |
| `make docker-test-all REPO=<path>` | Batch parity test |

### Cloud

| Command | Purpose |
|---------|---------|
| `make cloud-setup` | One-time terraform init |
| `make cloud-run REPO=<url>` | Ephemeral VM analysis |
| `make cloud-status` | Check active VMs and results |
| `make cloud-destroy` | Destroy VM (after `KEEP_SERVER=1`) |
| `make cloud-cleanup` | Destroy orphaned VMs (`TTL_HOURS=`, `DRY_RUN=1`) |

### GitHub IaC

| Command | Purpose |
|---------|---------|
| `make github-setup` | terraform init for GitHub |
| `make github-plan` | Preview settings changes |
| `make github-apply` | Apply settings (`GITHUB_TOKEN` required) |

### All Pipeline Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `REPO` | required | Target repository (path or URL) |
| `DB_PATH` | `~/.caldera/caldera_sot.duckdb` | Database location |
| `SKIP_TOOLS` | unset | Comma-separated tool names to skip |
| `PIPELINE_LLM` | `1` | Set `0` to skip LLM evaluation |
| `REPLACE` | unset | Set `1` to overwrite existing run |
| `CONTINUE_ON_TOOL_FAILURE` | unset | Set `1` to keep going on tool failure |
| `BUNDLE_DIR` | `artifacts` | Bundle output directory |
| `BUNDLE_TAR` | `1` | Create `.tar.gz` from bundle |
| `CLONE_DEPTH` | unset | Git clone depth (empty = full) |
| `MAX_PARALLEL` | `1` (local) / `4` (docker/cloud) | Parallel tool execution |
| `COLLECTION_RUN_ID` | latest | Target a specific collection run |
| `CLOUD_SERVER` | `cx33` | Hetzner server type or preset |
| `CLOUD_RESULTS` | `infra/results` | Local directory for cloud results |
| `KEEP_SERVER` | unset | Set `1` to keep VM alive |
| `TTL_HOURS` | `4` | Max VM age for cleanup |
| `DRY_RUN` | unset | Set `1` for dry-run mode |
| `MAX_DURATION` | unset | Max analysis duration (seconds) |
| `MAX_COST` | unset | Max estimated cost (EUR) |
| `RESULTS_REPO_URL` | unset | Git URL for results export |
| `PUSH` | unset | Set `1` to push after export |
| `GHCR_REGISTRY` | `ghcr.io/alexander-stage-hoco` | GHCR image registry |
| `CALDERA_TOOL_IMAGE_PREFIX` | `caldera-tool-` | Docker image prefix |
| `CALDERA_RUNNER_IMAGE` | `caldera-runner` | Runner image name |
| `CALDERA_ORCHESTRATOR_IMAGE` | `caldera-orchestrator` | Orchestrator image name |
| `DOCKER_TEST_SKIP` | `coverage-ingest,git-blame-scanner` | Tools to skip in Docker parity tests |
| `CONFIRM` | unset | Required for destructive operations (`prune-outputs`) |
| `APPLY` | unset | Required for external actions (`create-risk-issues`) |
| `RELEASE_TYPE` | required for `release` | `major`, `minor`, or `patch` |
| `ARCH_REVIEW_TARGET` | required for `arch-review` | Tool name to review |

---

## 12. Forward Roadmap

### Current State (v0.14.0-dev)

- All 18 tools at full maturity (compliance, adapters, dbt models, Docker images)
- 3 production modes operational (LOCAL, BUNDLE, DOCKERIZED)
- Cloud analysis via Hetzner VMs working
- Full CI/CD with 5 pipeline gates
- 104 LLM judges across all tools
- Trust score with trend tracking
- Results export to git repository

### Near-Term: v0.14 — Platform Polish

| Feature | Status | Description |
|---------|--------|-------------|
| PDF report generation | Not started | Formal stakeholder deliverables as PDF |
| arm64 Docker images | Not started | Multi-platform builds for M-series Macs |
| Incremental pipeline | Not started | Content-hash caching to skip unchanged tools |

### Mid-Term: v0.15–v1.0

| Feature | Status | Description |
|---------|--------|-------------|
| Policy Layer | Not started | Configurable quality gates per repo/team; PR/release enforcement; waivers with expiry; drift tracking |
| Portfolio Layer | Not started | Multi-repo dashboards; cross-repo health scoring; organizational metrics |

### Tool Maturity Matrix

All 18 tools are **Mature** (highest level):

| Maturity Level | Requirements | Tools |
|----------------|-------------|-------|
| Mature | Compliance + adapter + dbt (staging → mart → rollup) + Docker + 4+ LLM judges | All 18 |

---

## Key Files Quick Reference

### Documentation

| File | Purpose |
|------|---------|
| `CLAUDE.md` | AI assistant instructions and project overview |
| `docs/USER_GUIDE.md` | Getting started for new users |
| `docs/TOOL_INTEGRATION_CHECKLIST.md` | Creating and integrating tools |
| `docs/PERSISTENCE.md` | Adapter pattern and data layer |
| `docs/COMPLIANCE.md` | Compliance requirements and fixes |
| `docs/REFERENCE.md` | Technical specifications |
| `docs/EVALUATION.md` | LLM judge infrastructure |
| `docs/REPORTS.md` | dbt analyses and reports |
| `docs/INSIGHTS_PRODUCT_SPEC.md` | Insights component spec |
| `docs/PRODUCTION_MODES.md` | All production deployment modes |
| `docs/CI_CD.md` | CI/CD pipeline details |
| `docs/CLOUD_ANALYSIS_GUIDE.md` | Large repo cloud analysis |
| `docs/STATUS_AND_ROADMAP.md` | Project status and roadmap |

### Core Implementation

| File | Purpose |
|------|---------|
| `src/sot-engine/orchestrator.py` | Main pipeline entry point |
| `src/sot-engine/execution.py` | Execution backend abstraction |
| `src/sot-engine/persistence/entities.py` | All entity dataclasses |
| `src/sot-engine/persistence/repositories.py` | Database CRUD |
| `src/sot-engine/persistence/schema.sql` | Landing zone DDL (42 tables) |
| `src/sot-engine/persistence/quality.py` | Data quality framework |
| `src/sot-engine/persistence/adapters/*.py` | 18 tool adapters |
| `src/shared/evaluation/base_judge.py` | Shared LLM judge base class |
| `src/shared/llm/client.py` | LLM client (CLI + SDK) |
| `src/shared/observability/*.py` | LLM interaction logging |
| `src/insights/data_fetcher.py` | SQL query executor for reports |
| `src/insights/scripts/evaluate.py` | Report evaluation orchestrator |
| `src/common/path_normalization.py` | Path validation utilities |

### Automation Scripts

| File | Purpose |
|------|---------|
| `scripts/create-tool.py` | Tool scaffold generator |
| `scripts/collect_artifacts.py` | Artifact bundle collector |
| `scripts/analyze_bundle.py` | Bundle ingest + report |
| `scripts/docker_runner.py` | Dockerized tool dispatcher |
| `scripts/docker_orchestrator_entrypoint.py` | Orchestrator container entry |
| `scripts/export_results.py` | Results repository exporter |
| `scripts/write_run_manifest.py` | Post-ingest manifest writer |
| `scripts/build_results_index.py` | Results catalog builder |
| `scripts/cloud-run.sh` | Cloud analysis orchestrator |
| `scripts/caldera-run` | Top-level Docker pipeline wrapper |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Path validation errors | Ensure paths are repo-relative (no leading `/` or `./`) |
| Collection run exists | Use `REPLACE=1`: `make analyze REPO=... REPLACE=1` |
| dbt test failures | Check rollup invariant: `recursive >= direct` |
| Schema validation errors | Compare output against `schemas/output.schema.json` |
| Compliance failures | See [docs/COMPLIANCE.md](COMPLIANCE.md) |
| "No module named 'duckdb'" | Use `.venv/bin/python` not system `python` |
| Import errors for shared modules | Check PYTHONPATH includes `src/` |
| Cloud: terraform.tfvars not found | `cp infra/terraform.tfvars.example infra/terraform.tfvars` and fill in values |
| Cloud: SSH timeout | Check Hetzner API token + SSH key path in tfvars |
| Cloud: .NET tools skipped | Expected — .NET not installed on VM |
| Cloud: server still running | `make cloud-destroy` |
| Docker: image not found | `make docker-build-all` or `make docker-pull-all` |
| LLM: Claude CLI not found | Install Claude Code: `npm install -g @anthropic-ai/claude-code` |
| LLM: API key missing | Set `ANTHROPIC_API_KEY` in `.env` or use `USE_ANTHROPIC_SDK=0` for CLI mode |
| Trust score < 50 | Check `lz_quality_checks` for error-severity failures; fix adapter issues |
