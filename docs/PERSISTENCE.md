# Persistence Layer Guide

This guide documents the SoT engine persistence layer for Project Caldera, covering the adapter pattern, entity design, repository operations, and how to create new adapters.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [BaseAdapter Reference](#3-baseadapter-reference)
4. [Creating a New Adapter - Step-by-Step](#4-creating-a-new-adapter---step-by-step)
5. [Entity Design Patterns](#5-entity-design-patterns)
6. [Repository Patterns](#6-repository-patterns)
7. [Validation Reference](#7-validation-reference)
8. [Layout Linkage](#8-layout-linkage)
9. [Testing Adapters](#9-testing-adapters)
10. [Special Cases](#10-special-cases)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Overview

The persistence layer transforms tool JSON output into validated, queryable data in DuckDB. It sits between tool execution and dbt transformation:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PIPELINE FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────┘

  Tools (scc, lizard, etc.)
           │
           │  JSON outputs (envelope format)
           ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                        ADAPTERS (This Layer)                            │
  │                                                                         │
  │  1. JSON Schema Validation    - Validates against output.schema.json    │
  │  2. Data Quality Validation   - Business rule checks                    │
  │  3. Entity Creation           - Maps JSON → frozen dataclasses          │
  │  4. Repository Persistence    - Bulk inserts to DuckDB                  │
  └─────────────────────────────────────────────────────────────────────────┘
           │
           │  Validated data
           ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                    LANDING ZONE (DuckDB)                                │
  │  lz_tool_runs │ lz_layout_* │ lz_scc_* │ lz_lizard_* │ lz_semgrep_*    │
  └─────────────────────────────────────────────────────────────────────────┘
           │
           │  dbt run
           ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                         MARTS (dbt)                                     │
  │  stg_* (staging) │ unified_file_metrics │ rollup_* distributions        │
  └─────────────────────────────────────────────────────────────────────────┘
```

### Design Goals

| Goal | How Achieved |
|------|--------------|
| **Consistency** | All adapters extend `BaseAdapter` with template method pattern |
| **Validation** | Three-tier validation: JSON schema → LZ schema → data quality |
| **Extensibility** | Add new tools by implementing abstract methods |
| **Traceability** | Every record links to `run_pk` for audit trail |
| **Layout Linkage** | File-level data joins to layout via `file_id`/`directory_id` |

---

## 2. Architecture

### Components

```
src/sot-engine/persistence/
├── adapters/
│   ├── __init__.py           # Exports all adapters
│   ├── base_adapter.py       # Abstract base class (Template Method)
│   ├── layout_adapter.py     # Special: writes TO layout tables
│   ├── scc_adapter.py        # File metrics adapter
│   ├── lizard_adapter.py     # Function complexity adapter
│   ├── semgrep_adapter.py    # Code smell adapter
│   ├── gitleaks_adapter.py   # Secret detection adapter
│   ├── roslyn_adapter.py     # .NET analyzer adapter
│   ├── sonarqube_adapter.py  # Two-table adapter
│   ├── trivy_adapter.py      # Multi-table adapter
│   └── git_sizer_adapter.py  # Repository-level metrics
├── entities.py               # Frozen dataclasses with validation
├── repositories.py           # Database CRUD operations
├── validation.py             # Shared validation utilities
├── schema.sql                # Landing zone DDL
└── tests/
    ├── conftest.py           # Test fixtures
    └── test_*.py             # Adapter tests
```

### Component Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BaseAdapter                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ persist(payload) ─── Template Method                                │   │
│  │   1. validate_schema(payload)         ← uses schema_path property   │   │
│  │   2. ensure_lz_tables()               ← uses table_ddl property     │   │
│  │   3. validate_lz_schema()             ← uses lz_tables property     │   │
│  │   4. _do_persist(payload)             ← ABSTRACT (subclass impl)    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ extends
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │ SccAdapter   │ │ SemgrepAdapter│ │ TrivyAdapter │
            │              │ │              │ │              │
            │ _do_persist()│ │ _do_persist()│ │ _do_persist()│
            │  │           │ │  │           │ │  │           │
            │  └─→ SccRepo │ │  └─→ Smells  │ │  └─→ Targets │
            │              │ │     Repo     │ │     Vulns    │
            └──────────────┘ └──────────────┘ │     IaC Repo │
                                              └──────────────┘
```

### Key Design Patterns

| Pattern | Where Used | Purpose |
|---------|------------|---------|
| **Template Method** | `BaseAdapter.persist()` | Ensures consistent validation flow |
| **Repository** | `*Repository` classes | Encapsulates database operations |
| **Frozen Dataclass** | Entity classes | Immutable, validated data objects |
| **Factory Method** | `_create_tool_run()` | Standardizes ToolRun creation |

---

## 3. BaseAdapter Reference

### Abstract Properties

| Property | Return Type | Purpose | Example |
|----------|-------------|---------|---------|
| `tool_name` | `str` | Identifier for logging/errors | `"scc"`, `"semgrep"` |
| `schema_path` | `Path` | Path to JSON schema file | `Path(".../output.schema.json")` |
| `lz_tables` | `dict[str, dict[str, str]]` | Expected LZ table columns/types | `{"lz_scc_file_metrics": {"run_pk": "BIGINT"}}` |
| `table_ddl` | `dict[str, str]` | CREATE TABLE statements | `{"lz_scc_file_metrics": "CREATE TABLE..."}` |

### Abstract Methods

| Method | Signature | Purpose |
|--------|-----------|---------|
| `_do_persist` | `(payload: dict) -> int` | Tool-specific persistence logic; returns `run_pk` |
| `validate_quality` | `(data: Any) -> None` | Business rule validation; raises `ValueError` on failure |

### Provided Methods

| Method | Purpose | When Called |
|--------|---------|-------------|
| `persist(payload)` | Template method orchestrating the full flow | Entry point from orchestrator |
| `validate_schema(payload)` | JSON schema validation | Automatically in `persist()` |
| `ensure_lz_tables()` | Creates tables from DDL if missing | Automatically in `persist()` |
| `validate_lz_schema()` | Verifies LZ columns exist with correct types | Automatically in `persist()` |
| `_create_tool_run(metadata)` | Creates ToolRun entity and inserts it | Called from `_do_persist()` |
| `_get_layout_run_pk(run_id)` | Looks up layout tool run PK | Called from `_do_persist()` |
| `_normalize_path(raw_path)` | Normalizes to repo-relative path | Called during entity mapping |
| `_log(message)` | Logs if logger configured | Throughout adapter |
| `_raise_quality_errors(errors)` | Logs and raises if errors non-empty | End of `validate_quality()` |
| `check_line_range(start, end, prefix)` | Validates line number ranges | In `validate_quality()` |

### Template Method Flow

```
persist(payload)
    │
    ├──→ validate_schema(payload)
    │         │
    │         └──→ validate_json_schema() from validation.py
    │
    ├──→ ensure_lz_tables()
    │         │
    │         └──→ Creates tables from table_ddl if missing
    │
    ├──→ validate_lz_schema()
    │         │
    │         └──→ Verifies columns exist with expected types
    │
    └──→ _do_persist(payload)  ← Subclass implements this
              │
              ├──→ _create_tool_run(metadata)
              │         │
              │         └──→ Returns run_pk (auto-incremented)
              │
              ├──→ _get_layout_run_pk(run_id)  [if file-level data]
              │
              ├──→ validate_quality(data)
              │
              └──→ Map entities → Repository bulk insert
```

---

## 4. Creating a New Adapter - Step-by-Step

This section walks through creating a complete adapter for a hypothetical tool called `my-tool`.

### Step 1: Define Module Constants

Create `src/sot-engine/persistence/adapters/my_tool_adapter.py`:

```python
"""Adapter for my-tool output persistence."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from .base_adapter import BaseAdapter
from ..entities import MyToolMetric
from ..repositories import LayoutRepository, MyToolRepository, ToolRunRepository
from ..validation import check_non_negative, check_required
from common.path_normalization import is_repo_relative_path, normalize_file_path

# Point to the tool's JSON schema
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "my-tool" / "schemas" / "output.schema.json"

# Define expected LZ table structure (for validation)
LZ_TABLES = {
    "lz_my_tool_metrics": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "metric_a": "INTEGER",
        "metric_b": "DOUBLE",
    }
}

# DDL for auto-creating tables
TABLE_DDL = {
    "lz_my_tool_metrics": """
        CREATE TABLE IF NOT EXISTS lz_my_tool_metrics (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            metric_a INTEGER,
            metric_b DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, file_id)
        )
    """,
}

# Document what quality rules are checked
QUALITY_RULES = ["paths", "ranges", "required_fields"]
```

### Step 2: Create Entity Dataclass

Add to `src/sot-engine/persistence/entities.py`:

```python
@dataclass(frozen=True)
class MyToolMetric:
    """Per-file metric from my-tool analysis."""
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    metric_a: int | None
    metric_b: float | None

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.relative_path, "relative_path")
        _validate_fields_non_negative({
            "metric_a": self.metric_a,
            "metric_b": self.metric_b,
        })
```

### Step 3: Create Repository Class

Add to `src/sot-engine/persistence/repositories.py`:

```python
class MyToolRepository(BaseRepository):
    """Repository for my-tool analysis data."""

    _COLUMNS = (
        "run_pk", "file_id", "directory_id", "relative_path",
        "metric_a", "metric_b",
    )

    def insert_metrics(self, rows: Iterable[MyToolMetric]) -> None:
        self._insert_bulk(
            "lz_my_tool_metrics",
            self._COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.directory_id, r.relative_path,
                r.metric_a, r.metric_b,
            ),
        )
```

### Step 4: Implement Adapter Class

Complete the adapter in `my_tool_adapter.py`:

```python
class MyToolAdapter(BaseAdapter):
    """Adapter for persisting my-tool output to the landing zone."""

    @property
    def tool_name(self) -> str:
        return "my-tool"

    @property
    def schema_path(self) -> Path:
        return SCHEMA_PATH

    @property
    def lz_tables(self) -> dict[str, dict[str, str]]:
        return LZ_TABLES

    @property
    def table_ddl(self) -> dict[str, str]:
        return TABLE_DDL

    def __init__(
        self,
        run_repo: ToolRunRepository,
        layout_repo: LayoutRepository,
        my_tool_repo: MyToolRepository,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._my_tool_repo = my_tool_repo

    def _do_persist(self, payload: dict) -> int:
        """Persist my-tool output to landing zone."""
        metadata = payload.get("metadata") or {}
        data = payload.get("data") or {}

        # 1. Create tool run record
        run_pk = self._create_tool_run(metadata)

        # 2. Get layout run for file linkage
        layout_run_pk = self._get_layout_run_pk(metadata["run_id"])

        # 3. Validate data quality
        files = data.get("files", [])
        self.validate_quality(files)

        # 4. Map and insert metrics
        metrics = list(self._map_file_metrics(run_pk, layout_run_pk, files))
        self._my_tool_repo.insert_metrics(metrics)

        self._log(f"Persisted {len(metrics)} my-tool metrics")
        return run_pk

    def validate_quality(self, files: Any) -> None:
        """Validate data quality rules for my-tool files."""
        errors = []
        for idx, entry in enumerate(files):
            # Path validation
            raw_path = entry.get("path", "")
            normalized = normalize_file_path(raw_path, self._repo_root)
            if not is_repo_relative_path(normalized):
                errors.append(f"file[{idx}] path invalid: {raw_path} -> {normalized}")

            # Required fields
            errors.extend(check_required(entry.get("path"), f"file[{idx}].path"))

            # Range validation
            errors.extend(check_non_negative(entry.get("metric_a"), f"file[{idx}].metric_a"))
            errors.extend(check_non_negative(entry.get("metric_b"), f"file[{idx}].metric_b"))

        self._raise_quality_errors(errors)

    def _map_file_metrics(
        self, run_pk: int, layout_run_pk: int, files: Iterable[dict]
    ) -> Iterable[MyToolMetric]:
        """Map JSON file entries to MyToolMetric entities."""
        for entry in files:
            relative_path = self._normalize_path(entry.get("path", ""))

            # Look up file_id and directory_id from layout
            try:
                file_id, directory_id = self._layout_repo.get_file_record(
                    layout_run_pk, relative_path
                )
            except KeyError:
                self._log(f"WARN: skipping file not in layout: {relative_path}")
                continue

            yield MyToolMetric(
                run_pk=run_pk,
                file_id=file_id,
                directory_id=directory_id,
                relative_path=relative_path,
                metric_a=entry.get("metric_a"),
                metric_b=entry.get("metric_b"),
            )
```

### Step 5: Add Table to schema.sql

Add to `src/sot-engine/persistence/schema.sql`:

```sql
CREATE TABLE lz_my_tool_metrics (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    directory_id VARCHAR NOT NULL,
    relative_path VARCHAR NOT NULL,
    metric_a INTEGER,
    metric_b DOUBLE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, file_id)
);
```

### Step 6: Export from `__init__.py`

Add to `src/sot-engine/persistence/adapters/__init__.py`:

```python
from .my_tool_adapter import MyToolAdapter

__all__ = [
    # ... existing exports
    "MyToolAdapter",
]
```

### Step 7: Wire into Orchestrator

Add to `src/sot-engine/orchestrator.py`:

```python
from persistence.adapters import MyToolAdapter
from persistence.repositories import MyToolRepository

# Add to TOOL_CONFIGS
TOOL_CONFIGS = [
    # ... existing configs
    ToolConfig("my-tool", "src/tools/my-tool"),
]

# Add to TOOL_INGESTION_CONFIGS
TOOL_INGESTION_CONFIGS = [
    # ... existing configs
    ToolIngestionConfig(
        name="my-tool",
        adapter_class=MyToolAdapter,
        repo_class=MyToolRepository,
        validate_metadata=True,  # Set False for tools like sonarqube/trivy that have non-standard metadata
    ),
]
```

---

## 5. Entity Design Patterns

### Frozen Dataclass Requirement

All entities use `@dataclass(frozen=True)` for immutability:

```python
@dataclass(frozen=True)
class SccFileMetric:
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    # ... metric fields
```

Benefits:
- Immutable after creation (no accidental modifications)
- Hashable (can be used in sets/dicts)
- Thread-safe by design

### Standard Fields

| Field | Type | Purpose |
|-------|------|---------|
| `run_pk` | `int` | Foreign key to `lz_tool_runs` |
| `file_id` | `str` | Foreign key to `lz_layout_files` |
| `directory_id` | `str` | Foreign key to `lz_layout_directories` |
| `relative_path` | `str` | Repo-relative path (for debugging/display) |

### `__post_init__` Validation

All entities validate in `__post_init__`:

```python
def __post_init__(self) -> None:
    _validate_positive_pk(self.run_pk)
    _validate_relative_path(self.relative_path, "relative_path")
    _validate_fields_non_negative({
        "lines_total": self.lines_total,
        "code_lines": self.code_lines,
    })
```

### Helper Validation Functions

From `entities.py`:

| Function | Purpose | Example |
|----------|---------|---------|
| `_validate_identifier(value, field)` | Non-empty, no whitespace | UUIDs, IDs |
| `_validate_relative_path(value, field)` | Repo-relative path rules | File paths |
| `_validate_non_negative(value, field)` | Value >= 0 or None | Counts, sizes |
| `_validate_positive_pk(value)` | Value > 0 | Primary keys |
| `_validate_required_string(value, field)` | Non-empty string | Required text |
| `_validate_line_range(start, end, prefix)` | Line numbers >= 1 | Code locations |
| `_validate_fields_non_negative(dict)` | Batch non-negative check | Multiple metrics |

### Entity Examples

**Simple file metric (SccFileMetric):**
```python
@dataclass(frozen=True)
class SccFileMetric:
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    language: str | None
    lines_total: int | None
    code_lines: int | None
    # ... more metrics
```

**Finding with location (SemgrepSmell):**
```python
@dataclass(frozen=True)
class SemgrepSmell:
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    rule_id: str
    severity: str | None
    line_start: int | None
    line_end: int | None
    message: str | None
```

**Repository-level metrics (GitSizerMetric):**
```python
@dataclass(frozen=True)
class GitSizerMetric:
    run_pk: int
    repo_id: str
    health_grade: str
    commit_count: int
    blob_total_size: int
    # ... no file_id/directory_id (repo-level)
```

---

## 6. Repository Patterns

### BaseRepository

All repositories extend `BaseRepository` for bulk insert support:

```python
class BaseRepository:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def _insert_bulk(
        self,
        table: str,
        columns: Sequence[str],
        entities: Iterable[T],
        to_tuple: Callable[[T], tuple[Any, ...]],
    ) -> None:
        """Generic bulk insert method."""
        records = [to_tuple(e) for e in entities]
        if not records:
            return
        placeholders = ", ".join(["?"] * len(columns))
        column_list = ", ".join(columns)
        self._conn.executemany(
            f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})",
            records,
        )
```

### Column Tuple Pattern

Define columns as a class-level tuple for consistency:

```python
class SccRepository(BaseRepository):
    _COLUMNS = (
        "run_pk", "file_id", "directory_id", "relative_path", "filename",
        "extension", "language", "lines_total", "code_lines", "comment_lines",
        # ... all columns in order
    )

    def insert_file_metrics(self, rows: Iterable[SccFileMetric]) -> None:
        self._insert_bulk(
            "lz_scc_file_metrics",
            self._COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.directory_id, r.relative_path, r.filename,
                r.extension, r.language, r.lines_total, r.code_lines, r.comment_lines,
                # ... all fields in same order as _COLUMNS
            ),
        )
```

### Multi-Table Repositories

Some tools write to multiple tables:

```python
class TrivyRepository(BaseRepository):
    _VULN_COLUMNS = (...)
    _TARGET_COLUMNS = (...)
    _IAC_COLUMNS = (...)

    def insert_vulnerabilities(self, rows: Iterable[TrivyVulnerability]) -> None:
        self._insert_bulk("lz_trivy_vulnerabilities", self._VULN_COLUMNS, rows, ...)

    def insert_targets(self, rows: Iterable[TrivyTarget]) -> None:
        self._insert_bulk("lz_trivy_targets", self._TARGET_COLUMNS, rows, ...)

    def insert_iac_misconfigs(self, rows: Iterable[TrivyIacMisconfig]) -> None:
        self._insert_bulk("lz_trivy_iac_misconfigs", self._IAC_COLUMNS, rows, ...)
```

---

## 7. Validation Reference

### Three-Tier Validation

1. **JSON Schema Validation** - Structure and types
2. **Landing Zone Schema Validation** - Database columns exist
3. **Data Quality Validation** - Business rules

### JSON Schema Validation

```python
def validate_json_schema(payload: dict, schema_path: Path) -> list[str]:
    """Validate payload against a JSON schema, returning error messages."""
    schema = json.loads(schema_path.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(payload), key=str):
        location = "/".join(str(part) for part in error.path) or "<root>"
        errors.append(f"{location}: {error.message}")
    return errors
```

### Landing Zone Schema Validation

```python
def validate_lz_schema(
    conn: duckdb.DuckDBPyConnection,
    expected: dict[str, dict[str, str]],
) -> list[str]:
    """Validate landing zone tables/columns exist with expected types."""
    errors: list[str] = []
    for table, columns in expected.items():
        # Check table exists
        # Check each column exists with expected type
    return errors
```

### Quality Check Helpers

From `validation.py`:

```python
def check_non_negative(value: int | float | None, field: str) -> Iterable[str]:
    """Returns error if value < 0."""
    if value is None:
        return []
    if value < 0:
        return [f"{field} must be >= 0 (got {value})"]
    return []

def check_ratio(value: float | None, field: str) -> Iterable[str]:
    """Returns error if value not in [0, 1]."""
    if value is None:
        return []
    if value < 0 or value > 1:
        return [f"{field} must be between 0 and 1 (got {value})"]
    return []

def check_required(value: object, field: str) -> Iterable[str]:
    """Returns error if value is None or empty string."""
    if value in (None, ""):
        return [f"{field} is required"]
    return []
```

### Line Range Validation

From `BaseAdapter`:

```python
@staticmethod
def check_line_range(
    line_start: int | None,
    line_end: int | None,
    field_prefix: str,
) -> list[str]:
    """Validate line number range and return any errors."""
    errors = []
    if line_start is not None and line_start < 1:
        errors.append(f"{field_prefix}.line_start must be >= 1")
    if line_end is not None and line_end < 1:
        errors.append(f"{field_prefix}.line_end must be >= 1")
    if line_start is not None and line_end is not None and line_end < line_start:
        errors.append(f"{field_prefix}.line_end must be >= line_start")
    return errors
```

---

## 8. Layout Linkage

### Why Layout Must Run First

Layout-scanner establishes the canonical file/directory IDs that other tools reference. This enables:

- Consistent `file_id` across all tool outputs
- Directory-level aggregations in dbt
- Cross-tool joins on the same files

### Layout Linkage Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LAYOUT RUN (First)                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
          Creates canonical file/directory IDs
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
          ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
          │lz_layout_    │ │lz_layout_    │ │Provides      │
          │files         │ │directories   │ │IDs to other  │
          │              │ │              │ │tools         │
          │file_id ──────┼─┼───────────────→│              │
          │directory_id ─┼─→              │ │              │
          └──────────────┘ └──────────────┘ └──────────────┘
                                    │
                                    ▼
          ┌──────────────────────────────────────────────────────────────────┐
          │                    OTHER TOOL ADAPTERS                           │
          │                                                                  │
          │  layout_run_pk = self._get_layout_run_pk(run_id)                 │
          │  file_id, dir_id = self._layout_repo.get_file_record(            │
          │      layout_run_pk, relative_path                                │
          │  )                                                               │
          └──────────────────────────────────────────────────────────────────┘
```

### Using `_get_layout_run_pk()`

Every file-level adapter needs the layout run's primary key:

```python
def _do_persist(self, payload: dict) -> int:
    metadata = payload.get("metadata") or {}

    run_pk = self._create_tool_run(metadata)
    layout_run_pk = self._get_layout_run_pk(metadata["run_id"])

    # Now can look up files...
```

### Using `get_file_record()`

Look up `file_id` and `directory_id` for each file:

```python
def _map_file_metrics(self, run_pk: int, layout_run_pk: int, files: Iterable[dict]):
    for entry in files:
        relative_path = self._normalize_path(entry.get("path", ""))

        try:
            file_id, directory_id = self._layout_repo.get_file_record(
                layout_run_pk, relative_path
            )
        except KeyError:
            # File not in layout (e.g., generated file, node_modules)
            self._log(f"WARN: skipping file not in layout: {relative_path}")
            continue

        yield MyEntity(
            run_pk=run_pk,
            file_id=file_id,
            directory_id=directory_id,
            relative_path=relative_path,
            # ...
        )
```

### Handling Missing Files

Some files may not be in layout (e.g., generated files, dependencies). Options:

1. **Skip with warning** (most common):
   ```python
   except KeyError:
       self._log(f"WARN: skipping file not in layout: {relative_path}")
       continue
   ```

2. **Use None for optional linkage** (Trivy):
   ```python
   file_id = None
   directory_id = None
   try:
       file_id, directory_id = self._layout_repo.get_file_record(...)
   except KeyError:
       self._log(f"WARN: target not in layout: {relative_path}")
   # Continue with None values
   ```

---

## 9. Testing Adapters

### Test File Location

Tests go in `src/sot-engine/persistence/tests/test_<tool>_adapter.py`.

### Test Fixtures from conftest.py

```python
@pytest.fixture
def duckdb_conn() -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with schema loaded."""
    conn = duckdb.connect(":memory:")
    _load_schema(conn)  # Loads schema.sql
    return conn

@pytest.fixture
def tool_run_repo(duckdb_conn) -> ToolRunRepository:
    return ToolRunRepository(duckdb_conn)

@pytest.fixture
def layout_repo(duckdb_conn) -> LayoutRepository:
    return LayoutRepository(duckdb_conn)

@pytest.fixture
def seed_layout(tool_run_repo, layout_repo):
    """Factory fixture to seed layout data for tests."""
    def _seed(
        repo_id: str,
        run_id: str,
        layout_files: list[tuple[str, str, str]],  # (file_id, dir_id, path)
    ) -> int:
        # Creates layout tool run and inserts files
        ...
    return _seed
```

### Using `seed_layout` Fixture

```python
def test_adapter_inserts_metrics(
    duckdb_conn,
    tool_run_repo,
    layout_repo,
    seed_layout,
):
    # Load test fixture
    fixture_path = Path(__file__).parents[1] / "fixtures" / "my_tool_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Seed layout with files referenced in fixture
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000002", "src/app.py"),
            ("f-000000000002", "d-000000000003", "src/utils/helpers.py"),
        ],
    )

    # Create and run adapter
    adapter = MyToolAdapter(
        tool_run_repo,
        layout_repo,
        MyToolRepository(duckdb_conn),
    )
    run_pk = adapter.persist(payload)

    # Verify results
    rows = duckdb_conn.execute(
        "SELECT file_id, metric_a FROM lz_my_tool_metrics WHERE run_pk = ?",
        [run_pk],
    ).fetchall()

    assert rows == [("f-000000000001", 42), ("f-000000000002", 17)]
```

### Key Test Scenarios

| Scenario | What to Test |
|----------|--------------|
| Happy path | Correct data inserted |
| Missing layout | `KeyError` raised with helpful message |
| File not in layout | Skipped with warning logged |
| Schema validation | `ValueError` on invalid JSON |
| Quality validation | `ValueError` on business rule violations |
| Duplicate handling | De-duplication or constraint violation |
| Edge cases | Empty input, null values, boundary values |

### Example Test for Missing Layout

```python
def test_adapter_raises_on_missing_layout(
    duckdb_conn,
    tool_run_repo,
    layout_repo,
):
    fixture_path = Path(__file__).parents[1] / "fixtures" / "my_tool_output.json"
    payload = json.loads(fixture_path.read_text())

    adapter = MyToolAdapter(tool_run_repo, layout_repo, MyToolRepository(duckdb_conn))

    try:
        adapter.persist(payload)
    except KeyError as exc:
        assert "layout" in str(exc).lower()
    else:
        raise AssertionError("Expected KeyError for missing layout run")
```

---

## 10. Special Cases

### LayoutAdapter: Writes TO Layout

Unlike other adapters, `LayoutAdapter` writes to layout tables rather than reading from them:

```python
class LayoutAdapter(BaseAdapter):
    """Unlike other adapters, LayoutAdapter writes TO the layout repository
    rather than reading from it to resolve file IDs."""

    def __init__(self, run_repo, layout_repo, repo_root=None, logger=None):
        # Note: layout_repo is for WRITING, not reading
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)

    def _do_persist(self, payload: dict) -> int:
        run_pk = self._create_tool_run(metadata)

        # NO call to _get_layout_run_pk() - we ARE the layout

        files = list(self._map_files(run_pk, files_map))
        self._layout_repo.insert_files(files)  # WRITE, not read

        directories = list(self._map_directories(run_pk, directories_map))
        self._layout_repo.insert_directories(directories)

        return run_pk
```

### TrivyAdapter: Multi-Table Output

Trivy writes to three tables: targets, vulnerabilities, and IaC misconfigurations:

```python
class TrivyAdapter(BaseAdapter):
    def _do_persist(self, payload: dict) -> int:
        # ... setup ...

        # Insert targets first (for target_key linkage)
        targets = list(self._map_targets(run_pk, layout_run_pk, targets_data))
        self._trivy_repo.insert_targets(targets)

        # Insert vulnerabilities (references target_key)
        vulns = list(self._map_vulnerabilities(run_pk, vulnerabilities_data))
        self._trivy_repo.insert_vulnerabilities(vulns)

        # Insert IaC misconfigs if present
        if iac_data:
            misconfigs = list(self._map_iac_misconfigs(run_pk, layout_run_pk, iac_data))
            self._trivy_repo.insert_iac_misconfigs(misconfigs)

        return run_pk
```

### SonarqubeAdapter: Two Tables

SonarQube has separate tables for issues and metrics:

```python
class SonarqubeAdapter(BaseAdapter):
    def _do_persist(self, payload: dict) -> int:
        # Issues (findings)
        issues = list(self._map_issues(run_pk, layout_run_pk, issues_data))
        self._sonarqube_repo.insert_issues(issues)

        # Metrics (per-file aggregates)
        metrics = list(self._map_metrics(run_pk, layout_run_pk, metrics_data))
        self._sonarqube_repo.insert_metrics(metrics)

        return run_pk
```

### GitSizerAdapter: Repository-Level Metrics

git-sizer provides repository-wide metrics, not per-file:

```python
class GitSizerAdapter(BaseAdapter):
    """git-sizer provides repository-level metrics (not per-file), so this adapter
    handles a single metrics record per run, plus violations and LFS candidates."""

    def __init__(self, run_repo, layout_repo=None, git_sizer_repo=None, ...):
        # layout_repo is optional - not needed for repo-level metrics
        super().__init__(run_repo, layout_repo, ...)

    def _do_persist(self, payload: dict) -> int:
        run_pk = self._create_tool_run(metadata)

        # NO layout linkage needed - repo-level data

        # Single metrics record
        metric = GitSizerMetric(run_pk=run_pk, ...)
        self._git_sizer_repo.insert_metrics(metric)

        # Violations array
        violations = [GitSizerViolation(...) for v in data.get("violations", [])]
        self._git_sizer_repo.insert_violations(violations)

        # LFS candidates (file paths, but no layout linkage)
        lfs_candidates = [GitSizerLfsCandidate(run_pk, path) for path in ...]
        self._git_sizer_repo.insert_lfs_candidates(lfs_candidates)

        return run_pk
```

---

## 11. Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `KeyError: "layout run not found"` | Layout adapter didn't run first | Ensure layout-scanner runs before other tools |
| `KeyError: "layout file not found: <path>"` | File not in layout scan | Check path normalization; file may be excluded |
| `ValueError: "schema validation failed"` | JSON doesn't match schema | Check required fields, types, patterns |
| `ValueError: "data quality validation failed"` | Business rule violation | Check logged `DATA_QUALITY_ERROR` messages |
| `ValueError: "relative_path must be repo-relative"` | Path has leading `/` or `./` | Use `normalize_file_path()` |
| `IntegrityError: duplicate key` | Same entity inserted twice | De-duplicate before insert; check primary key |
| `TypeError: 'NoneType' object is not iterable` | Null data section | Use `payload.get("data") or {}` |
| Table doesn't exist | DDL not applied | Verify `TABLE_DDL` is complete; check `schema.sql` |
| Column type mismatch | LZ_TABLES doesn't match DDL | Align `LZ_TABLES` with `TABLE_DDL` |
| Import errors | Missing sys.path setup | Check test file has proper path setup |

### Debugging Tips

1. **Enable logging**: Pass a logger function to see detailed progress:
   ```python
   logs = []
   adapter = MyAdapter(..., logger=logs.append)
   adapter.persist(payload)
   print("\n".join(logs))
   ```

2. **Check raw payload**: Verify JSON structure before persistence:
   ```python
   import json
   print(json.dumps(payload, indent=2))
   ```

3. **Query DuckDB directly**: Inspect landing zone state:
   ```sql
   SELECT * FROM lz_tool_runs WHERE tool_name = 'my-tool';
   SELECT COUNT(*) FROM lz_my_tool_metrics;
   ```

4. **Validate schema separately**:
   ```python
   from persistence.validation import validate_json_schema
   errors = validate_json_schema(payload, SCHEMA_PATH)
   print(errors)
   ```

---

## Quick Reference: LZ Tables

| Table | Primary Key | Tool | Description |
|-------|-------------|------|-------------|
| `lz_collection_runs` | `collection_run_id` | orchestrator | Groups tool runs |
| `lz_tool_runs` | `run_pk` | all | Individual tool executions |
| `lz_layout_files` | `(run_pk, file_id)` | layout-scanner | Canonical file list |
| `lz_layout_directories` | `(run_pk, directory_id)` | layout-scanner | Directory hierarchy |
| `lz_scc_file_metrics` | `(run_pk, file_id)` | scc | Lines, complexity, size |
| `lz_lizard_file_metrics` | `(run_pk, file_id)` | lizard | File-level CCN stats |
| `lz_lizard_function_metrics` | `(run_pk, file_id, function_name, line_start)` | lizard | Per-function metrics |
| `lz_semgrep_smells` | `(run_pk, file_id, rule_id, line_start)` | semgrep | Code smell findings |
| `lz_gitleaks_secrets` | `(run_pk, file_id, rule_id, line_number, fingerprint)` | gitleaks | Secret findings |
| `lz_roslyn_violations` | `(run_pk, file_id, rule_id, line_start, column_start)` | roslyn-analyzers | .NET violations |
| `lz_sonarqube_issues` | `(run_pk, file_id, issue_key)` | sonarqube | SonarQube issues |
| `lz_sonarqube_metrics` | `(run_pk, file_id)` | sonarqube | Per-file SQ metrics |
| `lz_trivy_targets` | `(run_pk, target_key)` | trivy | Scan targets |
| `lz_trivy_vulnerabilities` | `(run_pk, target_key, vulnerability_id, package_name)` | trivy | CVE findings |
| `lz_trivy_iac_misconfigs` | `(run_pk, relative_path, misconfig_id, start_line)` | trivy | IaC issues |
| `lz_git_sizer_metrics` | `run_pk` | git-sizer | Repository health |
| `lz_git_sizer_violations` | `(run_pk, metric)` | git-sizer | Threshold violations |
| `lz_git_sizer_lfs_candidates` | `(run_pk, file_path)` | git-sizer | LFS migration targets |

---

## References

- [TOOL_INTEGRATION_CHECKLIST.md](./TOOL_INTEGRATION_CHECKLIST.md) - Creating and integrating tools
- [REFERENCE.md](./REFERENCE.md) - Technical specifications (envelope format, paths)
- [COMPLIANCE.md](./COMPLIANCE.md) - Compliance requirements and checks
- [REPORTS.md](./REPORTS.md) - dbt analyses and reports
