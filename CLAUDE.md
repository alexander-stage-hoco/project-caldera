# CLAUDE.md - Project Caldera

## Project Overview

Project Caldera is a tool-first workspace for building and validating code analysis tools before integration into a Source-of-Truth (SoT) engine. It collects, evaluates, and persists code metrics from multiple analysis tools into a unified data warehouse.

**Core Pipeline:** Tools produce JSON → Adapters validate & persist to Landing Zone (DuckDB) → dbt transforms to Marts → Reports generated

## Start Here

| Goal | Document |
|------|----------|
| Create a new tool | [docs/TOOL_GUIDE.md](docs/TOOL_GUIDE.md) |
| Migrate from Vulcan | [docs/TOOL_GUIDE.md](docs/TOOL_GUIDE.md#part-2-migrating-from-vulcan) |
| Fix compliance failures | [docs/COMPLIANCE.md](docs/COMPLIANCE.md) |
| Understand technical specs | [docs/REFERENCE.md](docs/REFERENCE.md) |
| Set up LLM judges | [docs/EVALUATION.md](docs/EVALUATION.md) |
| Run reports | [docs/REPORTS.md](docs/REPORTS.md) |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TOOL LAYER                                     │
│  layout-scanner │ scc │ lizard │ semgrep │ roslyn-analyzers │ sonarqube │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ JSON outputs
┌────────────────────────────────────▼────────────────────────────────────────┐
│                           ADAPTER LAYER                                     │
│  Schema validation → Quality validation → Entity creation → Persistence     │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────────┐
│                         LANDING ZONE (DuckDB)                               │
│  lz_collection_runs │ lz_tool_runs │ lz_layout_* │ lz_scc_* │ lz_lizard_* │
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
│   └── evaluation/          # LLM judge infrastructure (BaseJudge, observability)
├── tool-compliance/         # Tool readiness verification scanner
├── tools/                   # Individual analysis tools
│   ├── layout-scanner/      # Repository file structure analysis
│   ├── lizard/              # Function-level complexity analysis (CCN, NLOC)
│   ├── roslyn-analyzers/    # .NET Roslyn analyzer violations
│   ├── scc/                 # Size & LOC analysis (lines, blanks, comments)
│   ├── semgrep/             # Code smell detection
│   └── sonarqube/           # SonarQube issue and metric analysis
└── sot-engine/              # Core engine
    ├── dbt/                 # Data transformation (staging → marts)
    ├── persistence/         # Data layer (adapters, entities, repositories)
    └── orchestrator.py      # End-to-end workflow coordinator
docs/                        # Documentation (see Key Files Reference)
scripts/                     # Automation scripts
```

## Key Commands

### Top-Level (from project root)

```bash
make compliance              # Run tool compliance scanner
make tools-analyze           # Run analysis for all tools
make tools-evaluate          # Run programmatic evaluations
make tools-test              # Execute all tool tests
make dbt-run                 # Execute dbt models
make dbt-test                # Run dbt tests
make orchestrate             # Full end-to-end pipeline
```

### Orchestrator

```bash
python src/sot-engine/orchestrator.py --repo-path /path/to/repo --commit abc123
python src/sot-engine/orchestrator.py --repo-path . --commit HEAD --replace
```

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
| `docs/TOOL_GUIDE.md` | Creating and migrating tools |
| `docs/COMPLIANCE.md` | Compliance requirements and checks |
| `docs/REFERENCE.md` | Technical specifications (envelope, paths, patterns) |
| `docs/EVALUATION.md` | LLM judge infrastructure and observability |
| `docs/REPORTS.md` | dbt analyses and reports |
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

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Path validation errors | Ensure paths are repo-relative (no leading `/` or `./`) |
| Collection run exists | Use `--replace` flag with orchestrator |
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
# Single tool (fast)
python src/tool-compliance/tool_compliance.py src/tools/<name>

# Preflight mode (~100ms)
python src/tool-compliance/tool_compliance.py src/tools/<name> --preflight

# All tools
make compliance
```
