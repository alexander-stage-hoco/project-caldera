# Technical Reference

This document is the single source of truth for technical specifications used throughout Project Caldera. Other documentation references this file instead of duplicating these patterns.

---

## Output Schema (Envelope Format)

All tool outputs use the Caldera envelope format with `metadata` and `data` sections:

```json
{
  "metadata": {
    "tool_name": "<tool>",
    "tool_version": "<semver>",
    "run_id": "<uuid>",
    "repo_id": "<uuid>",
    "branch": "<branch>",
    "commit": "<40-hex-sha>",
    "timestamp": "<ISO8601>",
    "schema_version": "<semver>"
  },
  "data": {
    "tool": "<tool>",
    "tool_version": "<semver>",
    "files": [ ... ]
  }
}
```

### Required Metadata Fields (8)

| Field | Type | Pattern/Format | Description |
|-------|------|----------------|-------------|
| `tool_name` | string | - | Tool identifier (e.g., `scc`, `lizard`) |
| `tool_version` | string | `^\d+\.\d+\.\d+$` | Semver version |
| `run_id` | string | UUID | Collection run UUID |
| `repo_id` | string | UUID | Repository UUID |
| `branch` | string | - | Git branch name |
| `commit` | string | `^[0-9a-fA-F]{40}$` | Full 40-character git SHA |
| `timestamp` | string | ISO8601 date-time | Analysis timestamp |
| `schema_version` | string | semver | Output schema version |

### Schema Requirements

- Use `$schema`: `https://json-schema.org/draft/2020-12/schema`
- Use `const` for `schema_version` (enables version alignment validation):
  ```json
  "schema_version": { "const": "1.0.0" }
  ```
- Define both `metadata` and `data` as required top-level properties
- All 8 metadata fields must be listed in `required` array

---

## Path Rules

All file paths in tool output must be **repo-relative**:

| Rule | Valid | Invalid |
|------|-------|---------|
| No leading `/` | `src/main.py` | `/src/main.py` |
| No leading `./` | `lib/utils.ts` | `./lib/utils.ts` |
| No `..` segments | `tests/test_foo.py` | `../outside/file.py` |
| POSIX separators | `src/foo/bar.py` | `src\foo\bar.py` |
| Root directory | `.` | `/` or empty string |

### Path Normalization

Use the shared path normalization module:

```python
from common.path_normalization import (
    normalize_file_path,
    normalize_dir_path,
    is_repo_relative_path,
)

# For file paths
normalized = normalize_file_path(raw_path, repo_root)

# For directory paths (handles "." for root)
normalized = normalize_dir_path(raw_path, repo_root)

# Validate
if not is_repo_relative_path(normalized):
    raise ValueError(f"Path not repo-relative: {normalized}")
```

### Commit Hash for Non-Git Repos

When no git metadata is available, compute a deterministic content hash:

```python
def fallback_commit_hash(repo_path: Path) -> str:
    import hashlib
    sha1 = hashlib.sha1()
    for path in sorted(repo_path.rglob("*")):
        if path.is_file() and ".git" not in path.parts:
            sha1.update(path.relative_to(repo_path).as_posix().encode())
            sha1.update(b"\0")
            try:
                sha1.update(path.read_bytes())
            except OSError:
                continue
    return sha1.hexdigest()
```

---

## Makefile Contract

### Required Targets (6)

| Target | Description |
|--------|-------------|
| `setup` | Install tool binary and Python dependencies |
| `analyze` | Run analysis, output to `outputs/<run-id>/output.json` |
| `evaluate` | Run programmatic evaluation |
| `evaluate-llm` | Run LLM judges |
| `test` | Run unit + integration tests |
| `clean` | Remove generated files |

### Required Variables (8)

| Variable | Source | Description |
|----------|--------|-------------|
| `REPO_PATH` | Orchestrator | Path to repository being analyzed |
| `REPO_NAME` | Orchestrator | Repository name for output naming |
| `OUTPUT_DIR` | Orchestrator | Directory for analysis outputs (`outputs/$(RUN_ID)`) |
| `RUN_ID` | Orchestrator | UUID for this collection run |
| `REPO_ID` | Orchestrator | UUID for the repository |
| `BRANCH` | Orchestrator | Git branch being analyzed |
| `COMMIT` | Orchestrator | 40-character commit SHA |
| `EVAL_OUTPUT_DIR` | Local | Directory for evaluation outputs |

### Makefile.common Usage

Include the shared Makefile.common to inherit standard variables and targets:

```makefile
# At the top of your Makefile (after SHELL if present)
include ../Makefile.common

# This provides:
# - RUN_ID, REPO_ID, OUTPUT_DIR, EVAL_OUTPUT_DIR, BRANCH
# - VENV, VENV_READY, PYTHON_VENV, PIP
# - _common-test, _common-clean, _common-clean-all targets

# Your tool only needs to define:
REPO_PATH ?= eval-repos/synthetic
REPO_NAME ?= synthetic
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000")
```

### Common Pitfalls

| Mistake | Correct |
|---------|---------|
| Target `llm-evaluate` | Target `evaluate-llm` |
| `OUTPUT_DIR = output/...` | `OUTPUT_DIR = outputs/...` (plural) |
| `$(REPO_NAME).json` output | `output.json` |

---

## Adapter Contract

Each tool adapter in `src/sot-engine/persistence/adapters/` must expose:

### Module-Level Constants

```python
# Path to the tool's output schema
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "<tool>" / "schemas" / "output.schema.json"

# Landing zone table schema (column name → DuckDB type)
LZ_TABLES = {
    "lz_<tool>_<entity>": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        # tool-specific columns...
    }
}

# Quality rules to validate (paths, ranges, required_fields)
QUALITY_RULES = ["paths", "ranges", "required_fields"]

# DDL for auto-creating tables
TABLE_DDL = {
    "lz_<tool>_<entity>": """
        CREATE TABLE IF NOT EXISTS lz_<tool>_<entity> (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            -- tool-specific columns --
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, file_id, <unique_key_columns>)
        )
    """,
}
```

### Required Class Methods

| Method | Purpose |
|--------|---------|
| `validate_schema(payload)` | Validate JSON against SCHEMA_PATH |
| `validate_lz_schema()` | Validate landing zone schema matches LZ_TABLES |
| `validate_quality(files)` | Validate data quality per QUALITY_RULES |
| `ensure_lz_tables()` | Create tables from TABLE_DDL if missing |
| `persist(payload)` | Full persistence pipeline |

### persist() Pattern

```python
def persist(self, payload: dict) -> int:
    # 1. Validate JSON schema
    self.validate_schema(payload)

    # 2. Ensure tables exist (auto-create if missing)
    self.ensure_lz_tables()

    # 3. Validate LZ schema matches expected
    self.validate_lz_schema()

    # 4. Extract metadata and data
    metadata = payload.get("metadata") or {}
    data = payload.get("data") or {}

    # 5. Create tool run record
    run = ToolRun(
        collection_run_id=metadata["run_id"],
        repo_id=metadata["repo_id"],
        # ... other fields
    )
    run_pk = self._run_repo.insert(run)

    # 6. Get layout run for file ID resolution
    layout_run_pk = self._run_repo.get_run_pk_any(
        metadata["run_id"],
        ["layout-scanner", "layout"],
    )

    # 7. Validate data quality
    files = data.get("files", [])
    self.validate_quality(files)

    # 8. Map and persist entities
    entities = list(self._map_entities(run_pk, layout_run_pk, files))
    self._tool_repo.insert_entities(entities)

    return run_pk
```

---

## Entity & Repository Patterns

### Entity Dataclass

```python
@dataclass(frozen=True)  # Must be frozen
class <Tool>Metric:
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    # tool-specific fields...

    def __post_init__(self) -> None:
        if not self.file_id:
            raise ValueError("file_id required")
        if not self.relative_path:
            raise ValueError("relative_path required")
```

### Repository Class

```python
class <Tool>Repository:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def insert_<entities>(self, items: Iterable[<Tool>Metric]) -> int:
        data = [
            (i.run_pk, i.file_id, i.directory_id, i.relative_path, ...)
            for i in items
        ]
        if not data:
            return 0
        self._conn.executemany(
            """
            INSERT INTO lz_<tool>_<entity> (run_pk, file_id, directory_id, relative_path, ...)
            VALUES (?, ?, ?, ?, ...)
            """,
            data,
        )
        return len(data)
```

---

## dbt Patterns

### Source Definition (schema.yml)

Add landing zone tables under `sources.lz.tables`:

```yaml
sources:
  - name: lz
    tables:
      - name: lz_<tool>_<entity>
```

### Staging Model Pattern

```sql
-- stg_<tool>_file_metrics.sql
-- Aggregates lz_<tool>_<entity> to file-level metrics

with raw_data as (
    select
        run_pk,
        file_id,
        directory_id,
        relative_path,
        -- tool-specific fields
    from {{ source('lz', 'lz_<tool>_<entity>') }}
),
file_metrics as (
    select
        run_pk,
        file_id,
        directory_id,
        min(relative_path) as relative_path,
        count(*) as <metric>_count,
        -- severity/category aggregations
    from raw_data
    group by run_pk, file_id, directory_id
)
select * from file_metrics
```

### Run Mapping Pattern (Required for Rollups)

Map tool runs to layout runs via `collection_run_id`:

```sql
with tool_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = '<tool>'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
run_map as (
    select
        tr.run_pk as tool_run_pk,
        lr.run_pk as layout_run_pk,
        tr.collection_run_id
    from tool_runs tr
    join layout_runs lr on lr.collection_run_id = tr.collection_run_id
)
```

### Direct vs Recursive Rollups

| Type | Join Pattern | Purpose |
|------|-------------|---------|
| **Direct** | Exact `directory_id` match | Files directly in directory |
| **Recursive** | Path prefix match | All files in directory subtree |

**Recursive join pattern:**
```sql
files_recursive as (
    select
        rm.tool_run_pk as run_pk,
        ld.directory_id as ancestor_directory_id,
        lf.file_id
    from {{ source('lz', 'lz_layout_files') }} lf
    join run_map rm on rm.layout_run_pk = lf.run_pk
    join {{ source('lz', 'lz_layout_directories') }} ld
        on ld.run_pk = lf.run_pk
        and (lf.directory_id = ld.directory_id
             or lf.relative_path like ld.relative_path || '/%')
)
```

### Required dbt Test (Direct vs Recursive Invariant)

```sql
-- test_rollup_<tool>_direct_vs_recursive.sql
select
    r.run_pk,
    r.directory_id,
    r.total_<metric>_count as recursive_count,
    d.total_<metric>_count as direct_count
from {{ ref('rollup_<tool>_directory_counts_recursive') }} r
join {{ ref('rollup_<tool>_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.total_<metric>_count < d.total_<metric>_count
   or r.file_count < d.file_count
```

### Distribution Statistics

22 metrics per distribution:
- Basic: count, min, max, mean, median, stddev
- Percentiles: p25, p50, p75, p90, p95, p99
- Shape: skewness, kurtosis, cv, iqr
- Concentration: gini, theil, hoover, palma, top/bottom shares

---

## Directory Structure (Required Paths)

Every tool in `src/tools/<tool-name>/` must have these 18 paths:

```
Makefile                    # Build orchestration (6 required targets)
README.md                   # Tool overview and usage
BLUEPRINT.md                # Architecture and design decisions
EVAL_STRATEGY.md            # Evaluation methodology
requirements.txt            # Python dependencies
scripts/analyze.py          # Main analysis script
scripts/evaluate.py         # Programmatic evaluation
scripts/checks/             # Evaluation check modules
schemas/output.schema.json  # Output JSON Schema (draft 2020-12)
eval-repos/synthetic/       # Synthetic test repositories
eval-repos/real/            # Real-world test repositories
evaluation/ground-truth/    # Expected outputs for evaluation
evaluation/llm/orchestrator.py  # LLM evaluation runner
evaluation/llm/judges/      # LLM judge implementations
evaluation/llm/prompts/     # LLM prompt templates
evaluation/scorecard.md     # Latest evaluation scorecard
tests/unit/                 # Unit tests
tests/integration/          # Integration tests
```

---

## Quick Validation Commands

```bash
# Validate JSON output
python -c "import json; json.load(open('outputs/<run-id>/output.json'))"

# Validate schema structure
python -c "import json, jsonschema; \
  schema=json.load(open('schemas/output.schema.json')); \
  data=json.load(open('outputs/<run-id>/output.json')); \
  jsonschema.validate(data, schema); \
  print('Valid!')"

# Check paths in output are repo-relative
python -c "import json; d=json.load(open('outputs/<run-id>/output.json')); \
  paths=[f['path'] for f in d['data']['files']]; \
  invalid=[p for p in paths if p.startswith('/') or p.startswith('./') or '\\\\' in p]; \
  print('Invalid paths:', invalid) if invalid else print('All paths valid')"

# Run preflight compliance check (~100ms)
python src/tool-compliance/tool_compliance.py src/tools/<tool> --preflight
```
