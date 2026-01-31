# CLAUDE.md - Project Caldera

## Project Overview

Project Caldera is a tool-first workspace for building and validating code analysis tools before integration into a Source-of-Truth (SoT) engine. It collects, evaluates, and persists code metrics from multiple analysis tools into a unified data warehouse.

**Core Pipeline:** Tools produce JSON → Adapters validate & persist to Landing Zone (DuckDB) → dbt transforms to Marts → Reports generated

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
│  lz_collection_runs │ lz_tool_runs │ lz_layout_* │ lz_scc_* │ lz_lizard_* │ lz_semgrep_* │ lz_roslyn_* │
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
├── explorer/                # DuckDB exploration CLI & report runner
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
    │   ├── models/          # SQL models (staging/, marts/)
    │   ├── analyses/        # Report queries
    │   └── tests/           # dbt SQL tests
    ├── persistence/         # Data layer
    │   ├── adapters/        # Tool-specific JSON → entity mapping
    │   ├── entities.py      # Frozen dataclasses with validation
    │   ├── repositories.py  # CRUD operations
    │   └── schema.sql       # Landing zone DDL
    └── orchestrator.py      # End-to-end workflow coordinator
docs/                        # Architecture & standards documentation
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
make explore                 # Interactive DuckDB CLI
make report-health           # Generate repo health report
make report-hotspots         # Generate hotspot report
```

### Orchestrator

```bash
python src/sot-engine/orchestrator.py --repo-path /path/to/repo --commit abc123
python src/sot-engine/orchestrator.py --repo-path . --commit HEAD --replace  # Overwrite existing
```

### Testing

```bash
pytest                       # Run all tests
pytest src/sot-engine/tests  # SoT engine tests only
pytest -v -k "test_name"     # Run specific test
```

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
    # ...

    def __post_init__(self) -> None:
        _validate_identifier(self.tool_run_id, "tool_run_id")
        _validate_repo_relative_path(self.file_path, "file_path")
```

**All entity classes in `entities.py`:**
- Core: `ToolRun`, `CollectionRun`
- Layout: `LayoutFile`, `LayoutDirectory`
- SCC: `SccFileMetric`
- Lizard: `LizardFileMetric`, `LizardFunctionMetric`
- Semgrep: `SemgrepSmell`
- Roslyn: `RoslynViolation`, `RoslynatorViolation`

### Adapter Pattern

Each tool has an adapter in `src/sot-engine/persistence/adapters/` that:
1. Validates JSON schema
2. Validates landing zone schema compatibility
3. Validates data quality rules (ranges, ratios, required fields)
4. Persists to DuckDB via repository

### Path Normalization

**Critical:** All file paths must be repo-relative:
- No leading `/`, `./`, or `..`
- POSIX separators (`/` not `\`)
- Validated by `src/common/path_normalization.py`

```python
# Good: "src/main.py"
# Bad: "/Users/foo/repo/src/main.py", "./src/main.py", "src\\main.py"
```

## Testing

### Test Locations

- `src/sot-engine/tests/` - Engine tests
- `src/sot-engine/persistence/tests/` - Persistence layer tests
- `src/explorer/tests/` - Explorer tests
- `src/tools/<tool>/tests/` - Per-tool unit & integration tests
- `src/sot-engine/dbt/tests/` - dbt SQL tests

### Test Patterns

- Use DuckDB in-memory databases for isolation
- Fixtures in `persistence/fixtures/` (JSON payloads)
- dbt tests validate ranges, uniqueness, and rollup invariants

## Key Files Reference

| File | Purpose |
|------|---------|
| `src/sot-engine/orchestrator.py` | Main entry point for full pipeline |
| `src/sot-engine/persistence/entities.py` | All dataclass definitions |
| `src/sot-engine/persistence/repositories.py` | Database CRUD operations |
| `src/sot-engine/persistence/schema.sql` | Landing zone table definitions |
| `src/tool-compliance/tool_compliance.py` | Tool readiness scanner |
| `src/common/path_normalization.py` | Path validation utilities |
| `docs/DEVELOPMENT.md` | Step-by-step tutorial for adding new tools |
| `docs/TOOL_REQUIREMENTS.md` | Tool compliance requirements spec |
| `docs/TOOL_MIGRATION_CHECKLIST.md` | Vulcan → Caldera migration guide |
| `docs/templates/BLUEPRINT.md.template` | Architecture document template |
| `docs/templates/EVAL_STRATEGY.md.template` | Evaluation strategy template |
| `src/sot-engine/persistence/adapters/` | Tool-specific JSON → entity adapters |
| `src/sot-engine/dbt/models/` | Staging and mart SQL models |

## Adding New Tools

### Documentation Resources

| Document | Purpose |
|----------|---------|
| `docs/DEVELOPMENT.md` | **Start here** - Step-by-step tutorial with examples |
| `docs/TOOL_REQUIREMENTS.md` | Complete requirements spec & compliance gates |
| `docs/TOOL_MIGRATION_CHECKLIST.md` | For migrating existing Vulcan tools |
| `docs/templates/BLUEPRINT.md.template` | Architecture document template |
| `docs/templates/EVAL_STRATEGY.md.template` | Evaluation strategy template |

### Quick Reference

**Directory structure:**
```
src/tools/<name>/
├── BLUEPRINT.md            # Architecture & design (use template)
├── EVAL_STRATEGY.md        # Evaluation approach (use template)
├── Makefile                # Standard targets
├── README.md               # User-facing documentation
├── schemas/
│   └── output.schema.json  # JSON Schema for output
├── scripts/
│   └── analyze.py          # Main analysis script
├── evaluation/
│   ├── ground-truth/       # Expected results per test repo
│   └── llm/judges/         # LLM evaluation judges
├── eval-repos/synthetic/   # Test repositories
└── tests/                  # Unit & integration tests
```

**Required Makefile targets:** `setup`, `analyze`, `evaluate`, `evaluate-llm`, `test`, `clean`

**Key requirements:**
1. All file paths must be repo-relative (no leading `/` or `./`)
2. JSON output must conform to `schemas/output.schema.json`
3. Must pass compliance scanner: `make compliance`
4. Adapter in `src/sot-engine/persistence/adapters/` for SoT integration

### Compliance Verification

```bash
# Check single tool
python src/tool-compliance/tool_compliance.py src/tools/<name>

# Check all tools
make compliance
```

The compliance scanner verifies 5 gates: structure, schema, makefile, tests, evaluation.

## Data Model Concepts

### Collection Run

Groups tool runs for a single `(repo_id, commit)` pair. Tracks status: running → completed/failed.

### Rollups (Directory Aggregations)

- **Recursive**: Aggregates all files in directory subtree
- **Direct**: Aggregates only files directly in directory
- Invariant: `recursive_count >= direct_count`

### Distribution Statistics

22 metrics per distribution: count, min, max, mean, median, stddev, percentiles (p25-p99), skewness, kurtosis, cv, iqr, gini, theil, hoover, palma, top/bottom shares.

## Common Tasks

### Investigating a failed run

```bash
python src/explorer/explorer.py
> query SELECT * FROM lz_collection_runs WHERE status = 'failed'
```

### Checking tool output validity

```bash
cd src/tools/scc && make analyze
python -c "from persistence.adapters.scc_adapter import SccAdapter; SccAdapter().validate_schema(json.load(open('output/output.json')))"
```

### Running dbt in isolation

```bash
cd src/sot-engine/dbt
dbt run --profiles-dir .
dbt test --profiles-dir .
```

## Troubleshooting

- **Path validation errors**: Ensure all paths are repo-relative (no leading `/` or `./`)
- **Collection run exists**: Use `--replace` flag with orchestrator
- **dbt test failures**: Check `rollup_*` models for recursive >= direct invariant
- **Schema validation errors**: Compare output against `output.schema.json` in tool directory
