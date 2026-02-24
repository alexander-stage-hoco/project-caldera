# Production Modes Design

**Version:** 1.0 Draft
**Date:** 2026-02-19
**Status:** Draft for Review

---

## Overview

Project Caldera supports multiple production modes. **For v1**, the recommended path is:

- **LOCAL** for end-to-end runs on analyst laptops
- **BUNDLE** when tool execution needs isolation (e.g., a separate machine or containers) but ingestion/dbt/reporting should happen locally

| Mode | Target | Tool Execution | Results Delivery |
|------|--------|---------------|------------------|
| **LOCAL** | Analyst laptop | Native tool Makefiles (Docker optional per tool) | Local filesystem |
| **BUNDLE** | Hybrid (runner + laptop) | Tools run elsewhere, artifacts shipped to laptop | Local filesystem |
| **DOCKERIZED** | Cloud VM / single machine | Everything in containers | Git results repository |

All modes aim to produce the same *logical* outputs (tool JSON artifacts → DuckDB → dbt marts → HTML report + optional LLM eval). The difference is where tool execution happens and how artifacts move between machines.

---

## Mode 1: LOCAL (Analyst Laptop)

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ANALYST LAPTOP                                     │
│                                                                      │
│  $ make analyze REPO=/path/to/target                                │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     ORCHESTRATOR (native)                      │   │
│  │  Python 3.12 in .venv/                                        │   │
│  │  DuckDB at ~/.caldera/caldera_sot.duckdb                     │   │
│  └──────────┬───────────────────────────────────────────────────┘   │
│             │                                                        │
│  ┌──────────▼──────────────────────────────────────────────────┐    │
│  │               TOOL EXECUTION (hybrid)                         │    │
│  │                                                               │    │
│  │  Tool Makefiles (17 by default + optional coverage-ingest):    │    │
│  │  Each tool runs via `make analyze` in its own `.venv/`.      │    │
│  │                                                               │    │
│  │  Some tools may optionally use Docker:                        │    │
│  │  • sonarqube (server via docker-compose is common)            │    │
│  │  • dotcover (optional linux/amd64 runner workaround)          │    │
│  └──────────┬────────────────────────────────────────────────────┘   │
│             │ JSON artifacts                                         │
│  ┌──────────▼──────────────────────────────────────────────────┐    │
│  │            INGESTION + TRANSFORM (native)                     │    │
│  │  Adapters → DuckDB LZ → dbt run → Marts                     │    │
│  └──────────┬────────────────────────────────────────────────────┘   │
│             │                                                        │
│  ┌──────────▼──────────────────────────────────────────────────┐    │
│  │               REPORTING (native)                              │    │
│  │  Insights → HTML report + optional LLM eval                  │    │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Characteristics

| Aspect | Detail |
|--------|--------|
| **Host prerequisites** | Python 3.12, git, make (tool-specific deps: e.g. .NET SDK for `roslyn-analyzers` and `dotcover`; Docker optional per tool) |
| **Tool execution** | Native per-tool `.venv/` environments (tools may optionally use Docker) |
| **DuckDB location** | `~/.caldera/caldera_sot.duckdb` |
| **Max parallelism** | Sequential (v1). Optional continue-on-failure mode. |
| **Results location** | `src/insights/output/pipeline/runs/<repo_id>/<run_id>/` |
| **LLM evaluation** | Claude Code CLI by default (or other providers); can be disabled |
| **Iteration speed** | Fast (no container overhead) |
| **Reproducibility** | Depends on host environment |

### Invocation

```bash
# Analyze a local repository (default = local mode)
make analyze REPO=/path/to/repo

# Analyze a remote repository (clones first)
make analyze REPO=https://github.com/org/repo

# Skip heavyweight tools for faster iteration
make analyze REPO=/path SKIP_TOOLS=sonarqube,dotcover,roslyn-analyzers

# Skip LLM evaluation
make analyze REPO=/path PIPELINE_LLM=0

# Continue running tools even if one fails (partial results)
make analyze REPO=/path CONTINUE_ON_TOOL_FAILURE=1

# Replace an existing run
make analyze REPO=/path REPLACE=1
```

### Tools with optional Docker components (LOCAL mode)

Some tools can optionally use Docker in local mode (either as a backend or to run a dependency):

| Tool | Why Docker | Image |
|------|-----------|-------|
| **dotcover** | Optional linux/amd64 runner workaround on macOS ARM64 | tool-local Dockerfile |
| **sonarqube** | Optional SonarQube server (often easiest via docker-compose) | `sonarqube:10.7.0-community` |

All other tools run natively via their per-tool `.venv/` environments.

Note: in v1, the orchestrator **does not manage Docker lifecycle**; tool Makefiles/scripts own any Docker they require.

Note: Some tools also require native host dependencies. For example, `roslyn-analyzers` requires a working `.NET SDK` installed on the laptop (or you can skip it via `SKIP_TOOLS=roslyn-analyzers`).

---

## Mode 2: BUNDLE (Artifacts-only collection + local analysis)

This mode matches the “tools in a container / analysis on the laptop” workflow:

1) Run tools anywhere (another machine, CI worker, or containers) and produce a **bundle**: tool `output.json` + logs + `manifest.json`  
2) Ship that bundle to the analyst laptop  
3) Ingest + dbt + reporting happens locally (no tool execution)

### Invocation

```bash
# On the tool runner machine (or inside a container host):
make collect REPO=/path/to/repo

# On the analyst laptop:
make analyze-bundle REPO=/path/to/repo BUNDLE=artifacts/<repo_id>/<run_id>
```

Notes:
- `coverage-ingest` is skipped by default in `collect` because it requires an explicit coverage file input.
- `make collect` can also produce a `.tar.gz` bundle (controlled by `BUNDLE_TAR=0|1`). `make analyze-bundle` accepts either a directory or `.tar.gz`.
- The laptop still needs a local checkout of the target repo for `--repo-path` (used for path normalization in adapters).

### Bundle structure (v1)

```
artifacts/<repo_id>/<run_id>/
├── manifest.json
├── <tool>/
│   ├── output.json
│   └── execution.log
└── ... (per tool)
```

### Characteristics

| Aspect | Detail |
|--------|--------|
| **Host prerequisites (runner)** | Tool-specific (can include Docker) |
| **Host prerequisites (laptop)** | Python 3.12, git, make |
| **Tool execution** | Outside the laptop |
| **DuckDB/dbt/report** | On the laptop |
| **Reproducibility** | High when tools run in controlled runners/containers |

---

## Mode 3: DOCKERIZED (Cloud / Single Machine)

This mode runs the full pipeline in containers. Implemented in Phase 3-4 (per-tool Dockerfiles, runner, orchestrator, compose stack).

Recommended direction: use the **bundle layout** as the contract between tool execution and ingestion. A dockerized runner can execute tools in containers, write `/workspace/artifacts/<repo-id>/<run-id>/...`, then invoke the orchestrator in BUNDLE mode.

### Architecture (bundle-first)

The dockerized mode uses a two-stage pipeline. Stage 1 (the **runner**) executes tools in containers and writes outputs into the standard **bundle layout**. Stage 2 (the **orchestrator**) ingests the bundle in BUNDLE mode — the same code path used by `make analyze-bundle` locally. This avoids docker.sock access in the orchestrator container and keeps its responsibilities identical across all modes.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        HOST MACHINE / VM                                  │
│                                                                          │
│  $ caldera-run --repo=https://github.com/org/target \                   │
│                --results-repo=git@github.com:org/caldera-results.git    │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  STAGE 1: TOOL RUNNER (docker compose)                              │ │
│  │                                                                     │ │
│  │  ┌──────────────────────────────────────────────────────────┐      │ │
│  │  │  caldera-runner (container)                                │      │ │
│  │  │  • Clones target repo to /workspace/repo                  │      │ │
│  │  │  • Generates repo_id + run_id, resolves commit            │      │ │
│  │  │  • Runs tool containers sequentially/parallel              │      │ │
│  │  │  • Writes bundle: /workspace/artifacts/<repo_id>/<run_id>/│      │ │
│  │  │    └── <tool>/output.json + execution.log                  │      │ │
│  │  │  • Writes manifest.json into bundle root                  │      │ │
│  │  └──────────┬───────────────────────────────────────────────┘      │ │
│  │             │ docker run (per tool)                                  │ │
│  │  ┌──────────▼──────────────────────────────────────────────┐       │ │
│  │  │  TOOL CONTAINERS (N images)                               │       │ │
│  │  │  caldera-tool-scc, caldera-tool-lizard, ...              │       │ │
│  │  │                                                           │       │ │
│  │  │  Mounts:                                                  │       │ │
│  │  │    /repo     ← target repo (read-only)                  │       │ │
│  │  │    /output   ← tool output dir (read-write)              │       │ │
│  │  │                                                           │       │ │
│  │  │  Each writes: /output/output.json                        │       │ │
│  │  └───────────────────────────────────────────────────────────┘      │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│           │ bundle (shared volume or directory)                           │
│                                                                          │
│  ┌────────▼───────────────────────────────────────────────────────────┐ │
│  │  STAGE 2: ORCHESTRATOR (container, BUNDLE mode)                     │ │
│  │  • Ingests bundle → adapters → DuckDB LZ                          │ │
│  │  • Runs dbt transforms → marts                                     │ │
│  │  • Generates HTML report + optional LLM eval                       │ │
│  │  • Optionally exports results to a git results repo                │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  Post-run: results pushed to git results repo                           │
└─────────────────────────────────────────────────────────────────────────┘
```

**Why bundle-first?**
- The orchestrator container needs no docker.sock access (security + portability).
- The orchestrator's ingestion path is the same as LOCAL and BUNDLE modes — no new code.
- Tool containers are simple: mount repo + output dir, run `make analyze`, exit.
- The runner is a thin shell script (or container) that manages tool dispatch and writes the bundle layout.

### Characteristics

| Aspect | Detail |
|--------|--------|
| **Host prerequisites** | Docker only (zero other dependencies) |
| **Tool execution** | All analysis tools in isolated containers (via runner) |
| **Orchestrator role** | BUNDLE-mode ingestion only (no docker.sock) |
| **DuckDB location** | Shared volume `/workspace/db/caldera_sot.duckdb` |
| **Max parallelism** | 8+ tools (configurable via `MAX_PARALLEL`) |
| **Results delivery** | Committed to a git results repository |
| **LLM evaluation** | Anthropic API key passed via environment |
| **Iteration speed** | Slower (container overhead, image builds) |
| **Reproducibility** | Fully reproducible (pinned images) |

### Invocation

```bash
# Single-command full run (future dockerized wrapper)
caldera-run \
  --repo=https://github.com/org/target \
  --results-repo=git@github.com:org/caldera-results.git

# Current (v1) cloud runner uses Terraform + a VM:
./scripts/cloud-run.sh https://github.com/org/target

# Or via docker compose directly
REPO_URL=https://github.com/org/target \
RESULTS_REPO=git@github.com:org/caldera-results.git \
ANTHROPIC_API_KEY=sk-... \
docker compose -f docker-compose.yml up

# With options
caldera-run \
  --repo=https://github.com/org/target \
  --results-repo=git@github.com:org/caldera-results.git \
  --max-parallel=12 \
  --skip-tools=sonarqube \
  --no-llm
```

### Container Images

#### Runner Image

The runner dispatches tool containers and writes the bundle layout. It needs Docker CLI access to spawn sibling containers.

```dockerfile
# Dockerfile.runner
FROM python:3.12-slim
WORKDIR /caldera

# Docker CLI for spawning tool containers
RUN apt-get update && \
    apt-get install -y --no-install-recommends docker.io git && \
    rm -rf /var/lib/apt/lists/*

COPY scripts/ /caldera/scripts/

# Note: the runner entrypoint is intentionally omitted here. In practice it must:
# - clone the target repo into a shared volume (e.g. /workspace/repo)
# - execute tool containers and write the canonical bundle layout under /workspace/artifacts/<repo_id>/<run_id>/
# - write /workspace/artifacts/LATEST.json for the orchestrator stage
```

#### Orchestrator Image

The orchestrator runs in BUNDLE mode — no Docker CLI needed.

```dockerfile
# Dockerfile.orchestrator
FROM python:3.12-slim
WORKDIR /caldera

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv .venv && .venv/bin/pip install -r requirements.txt

COPY src/ /caldera/src/
COPY scripts/ /caldera/scripts/
COPY Makefile Makefile.common /caldera/

# Note: the orchestrator entrypoint must be a small wrapper that reads
# /workspace/artifacts/LATEST.json and invokes ingestion+dbt+report generation.
# The core ingestion engine remains `src/sot-engine/orchestrator.py` in BUNDLE mode.
```

#### Tool Image Template

Most tools follow a common Dockerfile pattern:

```dockerfile
# src/tools/<tool>/Dockerfile
FROM python:3.12-slim AS base
WORKDIR /caldera

# Install system deps (tool-specific)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

# Copy shared modules (needed by analyze.py)
COPY src/common/ /caldera/src/common/
COPY src/shared/ /caldera/src/shared/

# Copy tool
COPY src/tools/<tool>/ /caldera/src/tools/<tool>/
WORKDIR /caldera/src/tools/<tool>

# Install dependencies
RUN python -m venv .venv && .venv/bin/pip install -r requirements.txt

# Standard entrypoint
ENTRYPOINT [".venv/bin/python", "scripts/analyze.py"]
```

#### Special-Case Tool Images

| Tool | Base Image | Extra Dependencies |
|------|-----------|-------------------|
| **dotcover** | `mcr.microsoft.com/dotnet/sdk:10.0` (amd64) | JetBrains.dotCover CLI |
| **roslyn-analyzers** | `mcr.microsoft.com/dotnet/sdk:10.0` | MSBuild, Roslyn analyzers |
| **sonarqube** | `python:3.12-slim` + sidecar `sonarqube:10.7.0-community` | sonar-scanner CLI |
| **semgrep** | `python:3.12-slim` | `semgrep` binary |
| **trivy** | `python:3.12-slim` | `trivy` binary |
| **gitleaks** | `python:3.12-slim` | `gitleaks` binary |
| **pmd-cpd** | `python:3.12-slim` | JRE + PMD binary |
| **scc** | `python:3.12-slim` | `scc` binary |
| **git-sizer** | `python:3.12-slim` | `git-sizer` binary |

#### docker-compose.yml (top-level)

```yaml
# docker-compose.yml
services:
  # Stage 1: run tools, write bundle
  runner:
    build:
      context: .
      dockerfile: Dockerfile.runner
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # needed to spawn tool containers
      - caldera-repo:/workspace/repo
      - caldera-artifacts:/workspace/artifacts
    environment:
      - REPO_URL=${REPO_URL}
      - MAX_PARALLEL=${MAX_PARALLEL:-4}
      - SKIP_TOOLS=${SKIP_TOOLS:-}

  # Stage 2: ingest bundle, dbt, report
  orchestrator:
    build:
      context: .
      dockerfile: Dockerfile.orchestrator
    depends_on:
      runner:
        condition: service_completed_successfully
    volumes:
      - caldera-repo:/workspace/repo:ro
      - caldera-artifacts:/workspace/artifacts:ro
      - caldera-db:/workspace/db
      - caldera-results:/workspace/results
    environment:
      - CALDERA_MODE=bundle
      - PIPELINE_LLM=${PIPELINE_LLM:-1}
      - RESULTS_REPO=${RESULTS_REPO}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

volumes:
  caldera-repo:
  caldera-artifacts:
  caldera-db:
  caldera-results:
```

**Runner → orchestrator contract (recommended):**

The orchestrator needs to know which bundle root to ingest (repo_id + run_id). In a two-stage compose flow, the simplest contract is:

- Runner writes the canonical bundle at `/workspace/artifacts/<repo_id>/<run_id>/manifest.json`
- Runner also writes a small pointer file at `/workspace/artifacts/LATEST.json` containing `{ "repo_id": "...", "run_id": "...", "bundle_root": "..." }`
- Orchestrator reads `LATEST.json` and then runs `scripts/analyze_bundle.py` (or invokes `src/sot-engine/orchestrator.py` in BUNDLE mode directly)

---

## Results Repository

In **DOCKERIZED** mode, all run outputs can be committed to a git repository. This allows analysts to clone results locally and run arbitrary analytics, queries, and reports.

### Repository Structure

```
caldera-results/
├── runs/
│   └── <repo-id>/
│       └── <run-id>/
│           ├── manifest.json                # Bundle manifest (tool outputs)
│           ├── run_manifest.json            # Post-ingest manifest (DuckDB state)
│           ├── artifacts/                   # Raw tool JSON outputs
│           │   ├── layout-scanner/
│           │   │   └── output.json
│           │   ├── scc/
│           │   │   └── output.json
│           │   ├── lizard/
│           │   │   └── output.json
│           │   └── ... (all tools)
│           ├── tool_run_summary.json        # Written even on failure
│           ├── dbt_summary.json             # Written even on failure
│           ├── database/
│           │   └── caldera_sot.duckdb       # Complete DuckDB (LZ + marts)
│           ├── reports/
│           │   ├── insights_report.html     # Full HTML report
│           │   ├── insights_report.json     # Machine-readable report
│           │   ├── executive_summary.json   # ~50KB executive context pack
│           │   └── top3_insights.json       # LLM-extracted top findings
│           ├── dbt/
│           │   ├── manifest.json            # dbt manifest (lineage)
│           │   └── run_results.json         # dbt test results
│           └── evaluation/
│               ├── llm_eval_results.json    # LLM judge scores
│               └── programmatic_checks.json # Programmatic check results
├── index.json                               # Catalog of all runs
└── README.md                                # Auto-generated latest run summary
```

### manifest.json Schema (canonical — matches `collect_artifacts.py`)

All **bundle-producing** modes should emit the same `manifest.json` schema. This is the canonical schema written by `scripts/collect_artifacts.py`; the cloud runner (`infra/run-analysis.sh`) and future dockerized runner should match the same top-level keys (using an extension key for cloud-specific fields if needed).

```json
{
  "schema_version": 1,
  "created_at": "2026-02-19T10:15:30.123456+00:00",
  "bundle_root": "/path/to/artifacts/myproject-a1b2c3d4e5/550e8400-...",
  "repo": {
    "repo_id": "myproject-a1b2c3d4e5",
    "repo_path": "/path/to/target/repo",
    "is_git": true,
    "branch": "main",
    "commit": "abc123def456789012345678901234567890abcd"
  },
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "tools": [
    {
      "name": "scc",
      "status": "success",
      "duration_seconds": 12.5,
      "output_json": "scc/output.json",
      "log_path": "scc/execution.log"
    },
    {
      "name": "sonarqube",
      "status": "failed",
      "duration_seconds": 120.0,
      "output_json": null,
      "log_path": "sonarqube/execution.log"
    }
  ]
}
```

**Note:** A separate post-ingest manifest (`run_manifest.json`, produced by `scripts/write_run_manifest.py`) summarises what was ingested into DuckDB — it has a different schema keyed on `collection_run` and `run_pk`. These serve different purposes: bundle `manifest.json` describes tool execution outputs; `run_manifest.json` describes ingested database state.

### Analyst Workflow (after cloud run)

```bash
# 1. Clone the results repo
git clone git@github.com:org/caldera-results.git
cd caldera-results

# 2. Browse available runs
cat index.json | python -m json.tool

# 3. Open the HTML report
open runs/myproject-a1b2c3/550e8400.../reports/insights_report.html

# 4. Query the DuckDB directly
duckdb runs/myproject-a1b2c3/550e8400.../database/caldera_sot.duckdb <<SQL
  SELECT relative_path, complexity, loc
  FROM unified_file_metrics
  WHERE complexity > 20
  ORDER BY complexity DESC
  LIMIT 20;
SQL

# 5. Re-run dbt locally with modified models
DB_PATH=runs/myproject-a1b2c3/550e8400.../database/caldera_sot.duckdb \
  make dbt-run

# 6. Regenerate reports from existing data
make report \
  DB_PATH=runs/myproject-a1b2c3/550e8400.../database/caldera_sot.duckdb

# 7. Compare two runs
duckdb <<SQL
  ATTACH 'runs/myproject/run-1/database/caldera_sot.duckdb' AS r1;
  ATTACH 'runs/myproject/run-2/database/caldera_sot.duckdb' AS r2;
  SELECT r1.loc, r2.loc, r2.loc - r1.loc AS delta
  FROM r1.unified_file_metrics r1m
  JOIN r2.unified_file_metrics r2m USING (relative_path);
SQL
```

---

## Results Repository

After any pipeline run (LOCAL, BUNDLE, or cloud), results can be exported to a git-based results repository for persistent, shareable archival.

### Setup

1. Create a git repository for results (e.g., on GitHub)
2. Set `RESULTS_REPO_URL` in `.env` (or export it)
3. Ensure `git-lfs` is installed (`brew install git-lfs`)

### Usage

```bash
# Export the latest run (commit only)
make export-results

# Export and push to remote
make export-results PUSH=1

# Export a specific collection run
make export-results COLLECTION_RUN_ID=<uuid>

# Use a local results repo for testing
RESULTS_REPO_URL=/path/to/local/repo make export-results
```

### What gets exported

Each run is stored under `runs/<repo_id>/<run_id>/` in the results repo:

| File | Always | Description |
|------|--------|-------------|
| `run_manifest.json` | Yes | Pipeline metadata (repo, commit, tools, timing) |
| `report.html` | Yes | HTML insights report |
| `caldera_sot.duckdb` | Yes | Complete database (LZ + marts), tracked via Git LFS |
| `evaluation.json` | If LLM eval ran | LLM judge scores |
| `top3_insights.json` | If LLM eval ran | Top 3 extracted insights |

An `index.json` catalog at the repo root is regenerated on each export, listing all runs sorted by recency.

### DuckDB and Git LFS

DuckDB files are tracked via Git LFS. The export script automatically initializes LFS and adds `*.duckdb` tracking if not already configured.

---

## Configuration Matrix

| Aspect | LOCAL | BUNDLE | DOCKERIZED |
|--------|-------|--------|--------------------|
| **Host prerequisites** | Python 3.12 (+ optional Docker per tool) | Runner: tool-specific; Laptop: Python 3.12 | Docker only |
| **Tool execution** | On laptop | On runner machine/container host | In containers |
| **Docker usage** | Optional per tool | Optional/on runner | Everything |
| **DuckDB location** | `~/.caldera/caldera_sot.duckdb` | `~/.caldera/caldera_sot.duckdb` | Shared volume `/workspace/db/` |
| **Max parallelism** | Sequential (v1) | Runner-defined | 8+ (configurable) |
| **Results delivery** | Local filesystem | Local filesystem | Git results repository |
| **LLM evaluation** | Optional (Claude Code CLI by default) | Optional (on laptop) | Optional (in container env) |
| **Invocation** | `make analyze REPO=...` | `make collect` → ship bundle → `make analyze-bundle` | `caldera-run` or `docker compose up` |
| **Iteration speed** | Fast | Medium (bundle transfer) | Slower (images/builds) |
| **Reproducibility** | Host-dependent | High if runner is controlled | Fully reproducible (pinned images) |
| **Offline capable** | Partially | Laptop analysis is offline-capable | Depends on image availability |
| **Target audience** | Analysts iterating locally | Analysts with isolated tool runners | CI/CD, automated DD runs |

---

## Orchestrator Changes Required

For **v1 LOCAL + BUNDLE**, the orchestrator already supports the key production behaviors:

- **LOCAL**: `--run-tools --run-dbt` runs tool Makefiles and then ingests + runs dbt.
- **BUNDLE**: `--output-root <bundle_root> --run-dbt` discovers tool outputs under `<bundle_root>/<tool>/output.json` and ingests without running tools.
- **Failure diagnostics**: `tool_run_summary.json` and `dbt_summary.json` are written even if the run fails.
- **Operational resilience**: `--continue-on-tool-failure` can be enabled to collect a full failure map before ingest.

### Future: DOCKERIZED backend (optional)

To implement a “fully dockerized” mode, the simplest path is to keep the orchestrator as-is and introduce an external runner that:

- Executes tools in containers and writes outputs into the **bundle layout**.
- Invokes the orchestrator in **BUNDLE** mode to ingest/dbt/report.
- Optionally exports the resulting bundle/DB/report to a results repository.

---

## Implementation Roadmap

### Phase 1: Foundation (tools + images)

| Task | Priority | Effort |
|------|----------|--------|
| Per-tool Dockerfiles (all tools) | High | Medium |
| Orchestrator Dockerfile | High | Small |
| Top-level `docker-compose.yml` | High | Small |
| `caldera-run` wrapper script (dockerized) | High | Small |
| Image build + tag automation (`Makefile` targets) | High | Small |

### Phase 2: Orchestrator Backend (optional — not required for bundle-first)

The bundle-first approach means DOCKERIZED mode can work without changing the orchestrator: the runner writes the bundle layout, and the orchestrator ingests it in BUNDLE mode (the same path as `make analyze-bundle`). The `ExecutionBackend` refactor is a cleanliness improvement, not a blocker.

| Task | Priority | Effort |
|------|----------|--------|
| `ExecutionMode` enum + `--mode` flag | Low | Small |
| `ExecutionBackend` interface | Low | Small |
| `LocalBackend` (extract from current code) | Low | Small |
| `DockerBackend` (new) | Low | Medium |
| Parallel execution within phases | Medium | Medium |

### Phase 3: Results Repository

| Task | Priority | Effort |
|------|----------|--------|
| `ResultsExporter` class | High | Medium |
| `manifest.json` generation | High | Small |
| `index.json` catalog maintenance | Medium | Small |
| Git commit + push automation | High | Small |

### Phase 4: Polish

| Task | Priority | Effort |
|------|----------|--------|
| CI pipeline to build/push images | Medium | Medium |
| Image size optimization (multi-stage builds) | Low | Medium |
| Health checks and timeout handling | Medium | Small |
| Documentation updates (USER_GUIDE, CLAUDE.md) | Medium | Small |

---

## Architecture V2 Alignment

This production modes design implements the following V2 proposal sections:

| V2 Section | Status | Notes |
|-----------|--------|-------|
| §2.5 Execution Modes (LOCAL/DOCKER/VM) | **Partially implemented** — LOCAL exists, DOCKER designed here, VM deferred |
| §3.6 Out-of-Process Execution | **Designed** — artifacts-only rule, volume mounts, validation before import |
| §3.6 Canonical Ingestion Rule | **Already implemented** — tools produce JSON, SoT engine does all DuckDB writes |
| §3.7 Run Lifecycle & Retention | **Not yet implemented** — TTL, cold storage deferred to later |
| §4.5 vulcan-core Package | **Not yet implemented** — shared primitives still in `src/shared/` |
| §4.6 CI Compliance Gates | **Not yet implemented** — GitHub Actions for image builds would include this |

### What V2 Proposed vs What We're Building

| V2 Concept | Our Implementation |
|-----------|-------------------|
| `ExecutionBackend` ABC | Optional — bundle-first makes this unnecessary for DOCKERIZED; nice-to-have for code cleanliness |
| `ExecutionConfig` dataclass | Simplified to `ExecutionMode` enum + CLI flags (optional) |
| `VMBackend` | Deferred (DOCKER mode covers cloud use cases) |
| `OutputCollector` | Simplified — shared volume mount, no `docker cp` needed |
| `PreImportValidator` | Already implemented in adapter layer |
| Tool Configuration Contract (`--config`) | Deferred — current `make analyze` + env vars sufficient |

---

## Open Questions

1. **Git LFS for DuckDB files?** — Result repo DuckDB files can be 50–500MB. Should we use Git LFS, or export to Parquet instead?
2. **SonarQube in dockerized mode** — Run as a sidecar service in compose, or as a pre-started dependency?
3. **Image registry** — Where to host tool images? GitHub Container Registry, Docker Hub, or private registry?
4. **Secrets management** — How to pass `ANTHROPIC_API_KEY` in CI/cloud environments?
5. **Result repo retention** — How many runs to keep per repo before pruning old results?
