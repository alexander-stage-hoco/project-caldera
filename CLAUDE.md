# CLAUDE.md - Project Caldera

## Project Overview

Project Caldera is a tool-first workspace for building and validating code analysis tools before integration into a Source-of-Truth (SoT) engine. It collects, evaluates, and persists code metrics from multiple analysis tools into a unified data warehouse.

**Core Pipeline:** Tools produce JSON → Adapters validate & persist to Landing Zone (DuckDB) → dbt transforms to Marts → Reports generated

## Start Here

| Goal | Document |
|------|----------|
| Get started as a new user | [docs/USER_GUIDE.md](docs/USER_GUIDE.md) |
| Create or integrate a new tool | [docs/TOOL_INTEGRATION_CHECKLIST.md](docs/TOOL_INTEGRATION_CHECKLIST.md) |
| Migrate from Vulcan | [docs/TOOL_INTEGRATION_CHECKLIST.md](docs/TOOL_INTEGRATION_CHECKLIST.md#appendix-a-migrating-from-vulcan) |
| Create a new adapter | [docs/PERSISTENCE.md](docs/PERSISTENCE.md) |
| Fix compliance failures | [docs/COMPLIANCE.md](docs/COMPLIANCE.md) |
| Understand technical specs | [docs/REFERENCE.md](docs/REFERENCE.md) |
| Set up LLM judges | [docs/EVALUATION.md](docs/EVALUATION.md) |
| Run reports | [docs/REPORTS.md](docs/REPORTS.md) |
| Review tool architecture | [src/architecture-review/README.md](src/architecture-review/README.md) |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TOOL LAYER                                     │
│  layout-scanner │ scc │ lizard │ semgrep │ roslyn-analyzers │ sonarqube │  │
│  trivy │ gitleaks │ symbol-scanner │ scancode │ pmd-cpd │ devskim │       │
│  dotcover │ git-fame │ git-sizer │ git-blame-scanner │ dependensee │        │
│  coverage-ingest │                                                          │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ JSON outputs
┌────────────────────────────────────▼────────────────────────────────────────┐
│                           ADAPTER LAYER                                     │
│  Schema validation → Quality validation → Entity creation → Persistence     │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────────┐
│                         LANDING ZONE (DuckDB)                               │
│  lz_collection_runs │ lz_tool_runs │ lz_<tool>_* (18 tool-specific tables) │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ dbt run
┌────────────────────────────────────▼────────────────────────────────────────┐
│                              MARTS (dbt)                                    │
│  stg_* (staging) → unified_file_metrics │ unified_run_summary │ rollup_*    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
src/
├── common/                  # Shared utilities (path normalization)
├── insights/                # Consolidated reporting component
├── shared/                  # Shared evaluation utilities
│   ├── evaluation/          # LLM judge infrastructure (BaseJudge, JudgeResult)
│   └── observability/       # LLM interaction logging and tracing
├── tool-compliance/         # Tool readiness verification scanner
├── tools/                   # Individual analysis tools (18 total)
│   ├── layout-scanner/      # Repository file structure analysis
│   ├── scc/                 # Size & LOC analysis
│   ├── lizard/              # Function-level complexity (CCN, NLOC)
│   ├── semgrep/             # Code smell detection
│   ├── roslyn-analyzers/    # .NET Roslyn analyzer violations
│   ├── sonarqube/           # SonarQube issue and metric analysis
│   ├── trivy/               # Container/IaC vulnerability scanning
│   ├── gitleaks/            # Secret detection in git history
│   ├── symbol-scanner/      # Code symbol extraction
│   ├── scancode/            # License and copyright detection
│   ├── pmd-cpd/             # Copy-paste detection
│   ├── devskim/             # Security linting rules
│   ├── dotcover/            # .NET code coverage (Coverlet)
│   ├── git-fame/            # Git contributor statistics
│   ├── git-sizer/           # Git repository size analysis
│   ├── git-blame-scanner/   # Per-file authorship and knowledge risk
│   ├── dependensee/         # Dependency visualization
│   └── coverage-ingest/     # Multi-format test coverage (LCOV, Cobertura, JaCoCo, Istanbul)
└── sot-engine/              # Core engine
    ├── dbt/                 # Data transformation (staging → marts)
    ├── persistence/         # Data layer (adapters, entities, repositories)
    └── orchestrator.py      # End-to-end workflow coordinator
docs/                        # Documentation (see Key Files Reference)
scripts/                     # Automation scripts
```

## Key Commands

### User-Facing (from project root)

```bash
make setup                   # One-time project + tool setup
make analyze REPO=<path>     # Full E2E pipeline (local path or GitHub URL)
make report                  # Regenerate report (optionally RUN_PK=N)
make list-runs               # Show all collection runs
make status                  # Check prerequisites and health
make clean-db                # Remove database, start fresh
```

### Advanced (from project root)

```bash
make compliance              # Structural compliance checks (all tools, ~10s)
make compliance-preflight   # Fast structure checks only (~100ms)
make compliance-full        # Full compliance with tool execution (~30min)
make arch-review ARCH_REVIEW_TARGET=<tool>  # Run programmatic architecture review
make tools-setup             # Run 'make setup' for tools
make tools-analyze           # Run analysis for all tools
make tools-evaluate          # Run programmatic evaluations
make tools-evaluate-llm      # Run LLM evaluations for tools
make tools-test              # Execute all tool tests
make tools-clean             # Clean tool outputs
make test                    # Run all project tests (pytest + tools + dbt)
make dbt-run                 # Execute dbt models
make dbt-test                # Run dbt tests
make dbt-test-reports        # Run report-specific dbt tests
make orchestrate             # Full end-to-end pipeline
make pipeline-eval           # Full E2E: orchestrate -> insights -> LLM eval -> top 3
```

### Orchestrator

```bash
# Basic usage (required: --repo-path and --repo-id)
.venv/bin/python src/sot-engine/orchestrator.py \
    --repo-path /path/to/repo \
    --repo-id my-project \
    --commit abc123def...  # Full 40-char SHA (optional, defaults to zeros for non-git repos)

# Current directory with replace mode
.venv/bin/python src/sot-engine/orchestrator.py \
    --repo-path . \
    --repo-id $(basename $(pwd)) \
    --commit $(git rev-parse HEAD) \
    --replace

# Run tools as part of orchestration
.venv/bin/python src/sot-engine/orchestrator.py \
    --repo-path . \
    --repo-id my-project \
    --run-tools \
    --run-dbt
```

**Note:** `--commit` defaults to all zeros (`0000...`) if not specified. For non-git repos, tools can compute their own content-based fallback hash.

### Testing

```bash
pytest                       # Run all tests
pytest src/sot-engine/tests  # SoT engine tests only
pytest -v -k "test_name"     # Run specific test
```

### Tool Creation & Automation

```bash
python scripts/create-tool.py <name>                        # Create new tool
python scripts/create-tool.py <name> --sot-integration      # With SoT adapter files
python scripts/seed_ground_truth.py <tool> <output.json>    # Seed ground truth
python scripts/generate_dbt_models.py <tool> --table <tbl> --metrics <cols>
```

## Virtual Environment

### Architecture

Project Caldera uses a two-tier virtual environment architecture:

| Level | Location | Purpose | Setup |
|-------|----------|---------|-------|
| Project | `.venv/` | Core components (orchestrator, compliance, dbt, tests) | `python3.12 -m venv .venv` |
| Tool | `src/tools/<tool>/.venv/` | Isolated tool execution | `make setup` in tool dir |

### Usage Rules

1. **Always use venv Python** - Never invoke `python` directly
2. **Use `make` targets** - They handle venv automatically
3. **For manual commands**: `.venv/bin/python <script>`

### Shared Modules

Tools can import from `src/shared/` via PYTHONPATH set in `Makefile.common`:
```python
from shared.evaluation.base_judge import BaseJudge
```

### Common Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `VENV` | Override tool venv path | `VENV=/tmp/scc-venv` |
| `SKIP_SETUP=1` | Skip venv creation (use existing) | `make test SKIP_SETUP=1` |

## Code Conventions

### Python Style

- **Python 3.12** with type hints everywhere
- Use `from __future__ import annotations` at top of every file
- Use PEP 604 union syntax: `str | None` not `Optional[str]`
- Frozen dataclasses for entities with `__post_init__` validation

### Entity Pattern

```python
@dataclass(frozen=True)
class SccFileMetric:
    tool_run_id: str
    file_path: str  # Must be repo-relative
    language: str
    lines: int

    def __post_init__(self) -> None:
        _validate_identifier(self.tool_run_id, "tool_run_id")
        _validate_repo_relative_path(self.file_path, "file_path")
```

### Path Normalization

**Critical:** All file paths must be repo-relative:
- No leading `/`, `./`, or `..`
- POSIX separators (`/` not `\`)
- Use `src/common/path_normalization.py`

```python
# Good: "src/main.py"
# Bad: "/Users/foo/repo/src/main.py", "./src/main.py", "src\\main.py"
```

## Key Files Reference

### Documentation

| File | Purpose |
|------|---------|
| `docs/USER_GUIDE.md` | Getting started guide for new users |
| `docs/TOOL_INTEGRATION_CHECKLIST.md` | Creating, migrating, and integrating tools |
| `docs/PERSISTENCE.md` | Adapter pattern, entities, repositories |
| `docs/COMPLIANCE.md` | Compliance requirements and checks |
| `docs/REFERENCE.md` | Technical specifications (envelope, paths, patterns) |
| `docs/EVALUATION.md` | LLM judge infrastructure and observability |
| `docs/REPORTS.md` | dbt analyses and reports |
| `docs/INSIGHTS_PRODUCT_SPEC.md` | Insights component product specification |
| `docs/ARCHITECTURE_V2_PROPOSAL.md` | Proposed architecture improvements |
| `docs/PLAN.md` | Current development plan and roadmap |
| `docs/templates/BLUEPRINT.md.template` | Architecture document template |
| `docs/templates/EVAL_STRATEGY.md.template` | Evaluation strategy template |

### Core Implementation

| File | Purpose |
|------|---------|
| `src/sot-engine/orchestrator.py` | Main entry point for full pipeline |
| `src/sot-engine/persistence/entities.py` | All dataclass definitions |
| `src/sot-engine/persistence/repositories.py` | Database CRUD operations |
| `src/sot-engine/persistence/schema.sql` | Landing zone table definitions |
| `src/sot-engine/persistence/adapters/` | Tool-specific JSON → entity adapters |
| `src/sot-engine/dbt/models/` | Staging and mart SQL models |

### Utilities

| File | Purpose |
|------|---------|
| `src/tool-compliance/tool_compliance.py` | Tool readiness scanner |
| `src/common/path_normalization.py` | Path validation utilities |
| `src/shared/evaluation/base_judge.py` | Shared LLM judge base class |
| `scripts/create-tool.py` | Tool directory generator |
| `scripts/seed_ground_truth.py` | Ground truth auto-seeding |
| `scripts/generate_dbt_models.py` | dbt model generator |
| `scripts/check_observability_compliance.py` | CI compliance checker |

## Data Model Concepts

### Collection Run

Groups tool runs for a single `(repo_id, commit)` pair. Tracks status: running → completed/failed.

### Rollups (Directory Aggregations)

- **Recursive**: Aggregates all files in directory subtree
- **Direct**: Aggregates only files directly in directory
- Invariant: `recursive_count >= direct_count`

### Distribution Statistics

22 metrics per distribution: count, min, max, mean, median, stddev, percentiles (p25-p99), skewness, kurtosis, cv, iqr, gini, theil, hoover, palma, top/bottom shares.

## Architecture Reviewer Sub-Agent

An LLM-powered sub-agent that reviews tool implementations for architectural conformance. Complements the rule-based compliance scanner with deeper code pattern analysis.

### Invocation

Ask Claude Code to review a tool, and it will spawn a `general-purpose` sub-agent with the architecture reviewer prompt:

| Command | Review type | Dimensions |
|---------|------------|------------|
| "Review the architecture of [tool]" | `tool_implementation` | D1-D4, D6 |
| "Run a cross-tool architecture consistency check" | `cross_tool` | D5 |
| "Check BLUEPRINT alignment for [tool]" | `blueprint_alignment` | D6 |

### What It Checks (6 Dimensions)

| # | Dimension | Weight | Examples |
|---|-----------|--------|----------|
| D1 | Entity & Persistence | 0.20 | Frozen dataclass, `__post_init__`, adapter constants, schema.sql match |
| D2 | Output Schema & Envelope | 0.20 | Draft 2020-12, `const` schema_version, 8 metadata fields, path normalization |
| D3 | Code Conventions | 0.15 | `__future__` annotations, PEP 604 unions, Makefile includes |
| D4 | Evaluation Infrastructure | 0.15 | Shared BaseJudge, 4+ judges, `{{ evidence }}` placeholders |
| D5 | Cross-Tool Consistency | 0.15 | Envelope drift, naming formula, adapter structure |
| D6 | BLUEPRINT Alignment | 0.15 | Required sections, no placeholders, evaluation data |

### Output

Results written to `src/architecture-review/results/<tool>-<timestamp>.json`. Schema at `src/architecture-review/schemas/review_result.schema.json`.

### Key Files

| File | Purpose |
|------|---------|
| `src/architecture-review/agent_prompt.md` | Full agent prompt with all rules |
| `src/architecture-review/schemas/review_result.schema.json` | Output JSON Schema |
| `src/architecture-review/README.md` | Usage guide |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Path validation errors | Ensure paths are repo-relative (no leading `/` or `./`) |
| Collection run exists | Use `REPLACE=1`: `make analyze REPO=... REPLACE=1` |
| dbt test failures | Check rollup invariant: `recursive >= direct` |
| Schema validation errors | Compare output against `schemas/output.schema.json` |
| Compliance failures | See [docs/COMPLIANCE.md](docs/COMPLIANCE.md) for fix actions |
| "No module named 'duckdb'" | Use `.venv/bin/python` not system `python` |
| Import errors for shared modules | Check PYTHONPATH includes `src/` |

## Common Tasks

### Investigating a failed run

```bash
duckdb /tmp/caldera_sot.duckdb "SELECT * FROM lz_collection_runs WHERE status = 'failed'"
```

### Checking tool output validity

```bash
cd src/tools/scc && make analyze
python -c "import json; json.load(open('outputs/<run-id>/output.json'))"
```

### Running dbt in isolation

```bash
cd src/sot-engine/dbt
dbt run --profiles-dir .
dbt test --profiles-dir .
```

### Running compliance scanner

```bash
# All tools — structural checks (~10s)
make compliance

# Fast structure checks only (~100ms)
make compliance-preflight

# Full compliance with tool execution (~30min)
make compliance-full

# Single tool (direct Python)
python src/tool-compliance/tool_compliance.py src/tools/<name>

# Single tool preflight
python src/tool-compliance/tool_compliance.py src/tools/<name> --preflight
```
