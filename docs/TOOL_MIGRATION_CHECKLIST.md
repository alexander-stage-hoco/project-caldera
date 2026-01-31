# Tool Migration Checklist: Vulcan → Caldera

This checklist guides the migration of analysis tools from Project Vulcan to Project Caldera.

## Overview

| Aspect | Project Vulcan | Project Caldera |
|--------|---------------|-----------------|
| **Output Format** | Simple JSON (`data` only) | Envelope JSON (`metadata` + `data`) |
| **Output Path** | `$(OUTPUT_DIR)/$(REPO_NAME).json` | `outputs/<run-id>/output.json` |
| **Makefile Targets** | 4 (`setup`, `analyze`, `evaluate`, `clean`) | 6 (+`evaluate-llm`, `test`) |
| **Persistence** | Aggregator (post-processing) | SoT adapters + dbt models |
| **Compliance** | Informal | Automated scanner (4 gates) |
| **Schema Version** | Optional | Required in metadata |
| **Layout Dependency** | External tool | Ingested as a tool run (layout-scanner) |

---

## Pre-Migration Checklist

### 1. Understand the Source Tool

- [ ] **Read tool documentation** (README.md, BLUEPRINT.md, EVAL_STRATEGY.md)
- [ ] **Understand input/output format**
  - What does the tool analyze?
  - What is the current output JSON structure?
  - What are the key metrics/fields?
- [ ] **Identify dependencies**
  - External binaries (e.g., scc, lizard)
  - Python packages
  - System requirements (Docker, .NET, etc.)
- [ ] **Review evaluation framework**
  - Programmatic checks
  - LLM judges
  - Ground truth files
- [ ] **Check test coverage**
  - Unit tests
  - Integration tests

---

## Migration Steps

### Step 1: Copy Tool Directory

```bash
# From Project Vulcan
cp -r src/tools/<tool-name> /path/to/caldera/src/tools/<tool-name>

# Or for tools outside src/tools/
cp -r src/<tool-name> /path/to/caldera/src/tools/<tool-name>
```

**Checklist:**
- [ ] Copy all source files (scripts/, schemas/, rules/, etc.)
- [ ] Copy evaluation framework (evaluation/, ground-truth/)
- [ ] Copy test repositories (eval-repos/)
- [ ] Copy tests (tests/)
- [ ] Do NOT copy: `.venv/`, `output/`, `__pycache__/`, `.pytest_cache/`

---

### Step 2: Update Makefile

Transform the Makefile to match Caldera conventions.

**Required Variables:**
```makefile
# Variables from orchestrator (with defaults)
REPO_PATH ?= eval-repos/synthetic
REPO_NAME ?= synthetic
OUTPUT_DIR ?= outputs/$(RUN_ID)
RUN_ID ?= $(shell uuidgen)
REPO_ID ?= $(shell uuidgen)
BRANCH ?= main
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "unknown")
EVAL_OUTPUT_DIR ?= evaluation/results
```

**Required Targets:**
```makefile
# Required targets
setup:          # Install tool binary and Python dependencies
analyze:        # Run analysis, output to outputs/<run-id>/output.json
evaluate:       # Run programmatic evaluation
evaluate-llm:   # Run LLM judges
test:           # Run unit + integration tests
clean:          # Remove generated files
```

**Checklist:**
- [ ] Add `RUN_ID`, `REPO_ID`, `BRANCH`, `COMMIT` variables
- [ ] Update `OUTPUT_DIR` to use `outputs/$(RUN_ID)` pattern
- [ ] Add `EVAL_OUTPUT_DIR` variable
- [ ] Update `analyze` target to pass all required args to script
- [ ] Add `evaluate-llm` target (or rename `llm-evaluate`)
- [ ] Ensure `test` target exists and runs pytest
- [ ] Update help text

---

### Step 3: Update analyze.py for Envelope Format

Transform the main analysis script to emit the Caldera envelope format.

**Envelope Format:**
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
    "schema_version": "1.0.0"
  },
  "data": {
    "tool": "<tool>",
    "tool_version": "<semver>",
    // ... original tool output ...
  }
}
```

**Required CLI Arguments:**
```python
parser.add_argument("--repo-path", required=True)
parser.add_argument("--repo-name", required=True)
parser.add_argument("--output-dir", required=True)
parser.add_argument("--run-id", required=True)
parser.add_argument("--repo-id", required=True)
parser.add_argument("--branch", default="main")
parser.add_argument("--commit", required=True)
```

**Output Location:**
```python
output_path = Path(args.output_dir) / "output.json"
```

**Checklist:**
- [ ] Add required CLI arguments (run-id, repo-id, branch, commit)
- [ ] Add envelope wrapper function
- [ ] Update output path to `outputs/<run-id>/output.json`
- [ ] Add commit resolution logic (git HEAD or content hash)
- [ ] Ensure all paths in output are repo-relative with `/` separators
- [ ] Remove any absolute paths from output
- [ ] Ensure `metadata.run_id` equals the **collection run id** passed by the orchestrator
- [ ] Update evaluation/check scripts to unwrap `data` from envelope for schema validation

---

### Step 4: Update Output Schema

Update the JSON Schema to reflect envelope format.

**Checklist:**
- [ ] Update `$schema` to `https://json-schema.org/draft/2020-12/schema`
- [ ] Add `metadata` object definition with required fields:
  - `tool_name` (string, required)
  - `tool_version` (string, semver pattern, required)
  - `run_id` (string, uuid pattern, required)
  - `repo_id` (string, uuid pattern, required)
  - `branch` (string, required)
  - `commit` (string, 40-hex pattern, required)
  - `timestamp` (string, date-time format, required)
  - `schema_version` (string, semver pattern, required)
- [ ] Wrap existing `data` definition
- [ ] Update `required` array at root level
- [ ] Save to `schemas/output.schema.json`
- [ ] Ensure referenced schemas resolve (`$defs` or local refs only)

---

### Step 5: Create SoT Adapter

Create an adapter to persist tool output to the landing zone.

**Location:** `src/sot-engine/persistence/adapters/<tool>_adapter.py`

**Template:**
```python
"""Adapter for <tool> output persistence."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from ..entities import <Tool>FileMetric, ToolRun
from ..repositories import <Tool>Repository, LayoutRepository, ToolRunRepository
from common.path_normalization import normalize_file_path


class <Tool>Adapter:
    """Adapts <tool> JSON output to entity objects for persistence."""

    def __init__(
        self,
        run_repo: ToolRunRepository,
        layout_repo: LayoutRepository,
        tool_repo: <Tool>Repository,
        repo_root: Optional[Path] = None,
    ) -> None:
        self._run_repo = run_repo
        self._layout_repo = layout_repo
        self._tool_repo = tool_repo
        self._repo_root = repo_root

    def persist(self, payload: dict) -> int:
        """Persist <tool> output to landing zone.

        Args:
            payload: Envelope-formatted JSON with metadata and data sections

        Returns:
            run_pk: The primary key of the inserted tool run
        """
        metadata = payload.get("metadata") or {}
        data = payload.get("data") or {}

        # Create tool run record
        run = ToolRun(
            collection_run_id=metadata["run_id"],
            repo_id=metadata["repo_id"],
            run_id=metadata["run_id"],
            tool_name=metadata["tool_name"],
            tool_version=metadata["tool_version"],
            schema_version=metadata["schema_version"],
            branch=metadata["branch"],
            commit=metadata["commit"],
            timestamp=datetime.fromisoformat(metadata["timestamp"].replace("Z", "+00:00")),
        )
        run_pk = self._run_repo.insert(run)

        # Get layout run for file ID resolution
        layout_run_pk = self._run_repo.get_run_pk(metadata["run_id"], "layout-scanner")

        # Map and persist file metrics
        metrics = list(self._map_file_metrics(run_pk, layout_run_pk, data.get("files", [])))
        self._tool_repo.insert_file_metrics(metrics)

        return run_pk

    def _map_file_metrics(
        self, run_pk: int, layout_run_pk: int, files: Iterable[dict]
    ) -> Iterable[<Tool>FileMetric]:
        for entry in files:
            relative_path = normalize_file_path(entry.get("path", ""), self._repo_root)
            file_id, directory_id = self._layout_repo.get_file_record(layout_run_pk, relative_path)
            yield <Tool>FileMetric(
                run_pk=run_pk,
                file_id=file_id,
                directory_id=directory_id,
                relative_path=relative_path,
                # ... map tool-specific fields ...
            )
```

**Checklist:**
- [ ] Create adapter file in `src/sot-engine/persistence/adapters/`
- [ ] Define entity dataclass(es) for the tool's output (in `entities.py`)
- [ ] Define `TABLE_DDL` constant with `CREATE TABLE IF NOT EXISTS` statements for all tool tables
- [ ] Define `LZ_TABLES` constant for schema validation (column name → type mapping)
- [ ] Implement `ensure_lz_tables()` method to auto-create missing tables
- [ ] Implement `persist(payload)` method that calls `ensure_lz_tables()` before `validate_lz_schema()`
- [ ] Use `common.path_normalization` for all path handling
- [ ] Add unit tests in `src/sot-engine/persistence/tests/`
- [ ] Adapter uses `metadata.run_id` as `collection_run_id`
- [ ] Adapter stores `metadata.tool_name` in `lz_tool_runs`
- [ ] Adapter resolves file IDs from layout run via `LayoutRepository.get_file_record()`
- [ ] Export adapter class in `adapters/__init__.py`

**TABLE_DDL Pattern:**
```python
from ..validation import ensure_lz_tables

TABLE_DDL = {
    "lz_<tool>_<entity>": """
        CREATE TABLE IF NOT EXISTS lz_<tool>_<entity> (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            -- tool-specific columns --
            PRIMARY KEY (run_pk, file_id)
        )
    """,
}

def ensure_lz_tables(self) -> list[str]:
    """Create landing zone tables if they don't exist."""
    conn = self._run_repo._conn
    created = ensure_lz_tables(conn, TABLE_DDL)
    if created and self._logger:
        for table in created:
            self._logger(f"Created landing zone table: {table}")
    return created
```

---

### Step 6: Wire Orchestrator + dbt for Layout Dependencies

If the tool depends on layout IDs (e.g., file-level metrics), ensure:

**Checklist:**
- [ ] Orchestrator runs `layout-scanner` before dependent tools
- [ ] Layout output is ingested via `LayoutAdapter` (no filesystem walk fallback)
- [ ] dbt models accept layout tool names (`layout` or `layout-scanner`)
- [ ] Tool adapters resolve layout run via `get_run_pk_any(["layout-scanner","layout"])`

---

### Step 7: Create Landing Zone Tables

Add tables to persist raw tool output.

**Location:** `src/sot-engine/persistence/schema.sql`

**Naming Convention:** `lz_<tool>_<entity>`

**Template:**
```sql
CREATE TABLE lz_<tool>_<entity> (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    -- tool-specific columns --
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, file_id)
);
```

**Checklist:**
- [ ] Add table definition to `schema.sql`
- [ ] Use `run_pk` as foreign key to `lz_tool_runs`
- [ ] Include `file_id` if file-level data (FK to `lz_layout_files`)
- [ ] Add appropriate indexes
- [ ] Update repository class in `repositories.py`

---

### Step 8: Create dbt Staging Model

Create a staging model to aggregate landing zone data to file-level metrics.

**Location:** `src/sot-engine/dbt/models/staging/stg_<tool>_file_metrics.sql`

**Template:**
```sql
-- Aggregates lz_<tool>_<entity> to file-level metrics
-- Produces one row per file with counts by severity and category

with raw_data as (
    select
        run_pk,
        file_id,
        directory_id,
        relative_path,
        severity,
        dd_category
    from {{ source('lz', 'lz_<tool>_<entity>') }}
),
file_metrics as (
    select
        run_pk,
        file_id,
        directory_id,
        min(relative_path) as relative_path,
        count(*) as <metric>_count,
        -- Severity counts
        count(case when severity = 'CRITICAL' then 1 end) as severity_critical,
        count(case when severity = 'HIGH' then 1 end) as severity_high,
        count(case when severity = 'MEDIUM' then 1 end) as severity_medium,
        count(case when severity = 'LOW' then 1 end) as severity_low,
        count(case when severity = 'INFO' then 1 end) as severity_info,
        count(case when severity in ('CRITICAL', 'HIGH') then 1 end) as severity_high_plus,
        -- Category counts (tool-specific)
        count(case when dd_category = 'security' then 1 end) as cat_security
        -- ... additional categories ...
    from raw_data
    group by run_pk, file_id, directory_id
)
select * from file_metrics
```

**Checklist:**
- [ ] Create staging model SQL file with naming: `stg_<tool>_file_metrics.sql`
- [ ] Add source definition to `schema.yml` under `sources.lz.tables`
- [ ] Aggregate from raw entity rows to file-level metrics
- [ ] Include severity and category breakdowns for downstream rollups
- [ ] Use `min(relative_path)` in GROUP BY to pick one path per file

---

### Step 9: Create dbt Rollup Models

Create directory-level rollup models (4 models per tool).

**Location:** `src/sot-engine/dbt/models/marts/`

**Required Models:**
1. `rollup_<tool>_directory_counts_direct.sql` - Counts for files directly in directory
2. `rollup_<tool>_directory_counts_recursive.sql` - Counts for all files in subtree
3. `rollup_<tool>_directory_direct_distributions.sql` - Distribution stats (direct)
4. `rollup_<tool>_directory_recursive_distributions.sql` - Distribution stats (recursive)

**Key Pattern - Run Mapping:**
```sql
-- Map tool runs to layout runs via collection_run_id
with tool_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = '<tool-name>'  -- Use exact tool_name from adapter
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')  -- Accept both names
),
run_map as (
    select
        tr.run_pk as tool_run_pk,
        lr.run_pk as layout_run_pk,
        tr.collection_run_id
    from tool_runs tr
    join layout_runs lr on lr.collection_run_id = tr.collection_run_id
),
```

**Direct vs Recursive:**
- **Direct:** Join `lz_layout_files.directory_id` directly
- **Recursive:** Join on directory ancestry (file path starts with directory path)

**Checklist:**
- [ ] Create all 4 rollup models
- [ ] Use run_map pattern to link tool and layout runs
- [ ] Direct models join on exact directory_id match
- [ ] Recursive models use path prefix matching for ancestry
- [ ] Include same columns in both direct and recursive for invariant testing
- [ ] Add columns to `schema.yml` if dbt tests need column definitions

---

### Step 10: Create dbt Tests

Add SQL tests to validate rollup invariants.

**Location:** `src/sot-engine/dbt/tests/`

**Required Test - Direct vs Recursive Invariant:**

```sql
-- test_rollup_<tool>_direct_vs_recursive.sql
-- Validates that recursive counts >= direct counts for each directory
-- This invariant must hold: a directory's recursive count includes all
-- files in its subtree, while direct only counts files directly in that directory.

select
    r.run_pk,
    r.directory_id,
    r.total_<metric>_count as recursive_count,
    d.total_<metric>_count as direct_count,
    r.file_count as recursive_file_count,
    d.file_count as direct_file_count
from {{ ref('rollup_<tool>_directory_counts_recursive') }} r
join {{ ref('rollup_<tool>_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.total_<metric>_count < d.total_<metric>_count
   or r.file_count < d.file_count
   or r.severity_high_plus < d.severity_high_plus
   -- Add all columns that should satisfy recursive >= direct
```

**Optional Tests - Distribution Ranges:**

```sql
-- test_rollup_<tool>_distribution_ranges.sql
-- Validates distribution statistics are within valid ranges

select *
from {{ ref('rollup_<tool>_directory_recursive_distributions') }}
where gini < 0 or gini > 1
   or p50 < min_value or p50 > max_value
   or value_count < 0
```

**Checklist:**
- [ ] Create `test_rollup_<tool>_direct_vs_recursive.sql` (required for compliance)
- [ ] Test all count columns satisfy recursive >= direct
- [ ] Optionally add distribution range tests
- [ ] Run `dbt test --profiles-dir . --select test_rollup_<tool>*` to verify

---

### Step 11: Wire Orchestrator

Update the orchestrator to call the new adapter.

**Location:** `src/sot-engine/orchestrator.py`

**Changes Required:**

1. **Add import:**
```python
from persistence.adapters.<tool>_adapter import <Tool>Adapter
```

2. **Add CLI argument:**
```python
parser.add_argument("--<tool>-output", type=Path, help="Path to <tool> output JSON")
```

3. **Add to `ingest_outputs()` function:**
```python
def ingest_outputs(
    conn,
    # ... existing args ...
    <tool>_output: Path | None = None,
    # ...
) -> None:
```

4. **Add adapter call in `ingest_outputs()`:**
```python
if <tool>_output and <tool>_output.exists():
    payload = json.loads(<tool>_output.read_text())
    <tool>_adapter = <Tool>Adapter(
        run_repo=run_repo,
        layout_repo=layout_repo,
        <tool>_repo=<Tool>Repository(conn),
        repo_root=repo_path,
        logger=print,
    )
    <tool>_adapter.persist(payload)
```

5. **Update existing tests** that call `ingest_outputs()` to pass the new argument (even as `None`)

**Checklist:**
- [ ] Add adapter import to orchestrator.py
- [ ] Add CLI argument for tool output path
- [ ] Add parameter to `ingest_outputs()` function
- [ ] Add adapter instantiation and persist() call
- [ ] Update all tests calling `ingest_outputs()` to include new argument
- [ ] Run `make test` to verify no regressions

---

### Step 12: Update Compliance Scanner

Register the tool with the compliance scanner (usually not needed).

**Location:** `src/tool-compliance/tool_compliance.py`

**Checklist:**
- [ ] Tool is auto-discovered in `src/tools/` - no registration needed
- [ ] Add tool to `TOOL_RULES` dict only if custom rules are needed
- [ ] Verify tool passes all gates (see Step 13)

---

### Step 13: Run Compliance Scanner

Validate the migration is complete.

```bash
cd /path/to/caldera
python src/tool-compliance/tool_compliance.py --root . --out-md /tmp/compliance.md
```

**All gates must pass:**
- [ ] Gate A: Structure checks pass
- [ ] Gate B: Schema checks pass
- [ ] Gate C: Evaluation checks pass
- [ ] Gate D: Output checks pass (requires `--run-analysis`)

---

## Post-Migration Checklist

- [ ] **Run all tests**: `make test` in tool directory
- [ ] **Run analysis on synthetic repos**: `make analyze`
- [ ] **Run evaluation**: `make evaluate`
- [ ] **Verify output format**: Check `outputs/<run-id>/output.json` structure
- [ ] **Test SoT pipeline**: Run orchestrator with new tool
- [ ] **Verify dbt models**: Run `make dbt-run` and `make dbt-test`
- [ ] **Update top-level Makefile**: Add tool to `TOOLS` list if needed
- [ ] **Update documentation**: Add tool to README.md
- [ ] **Verify layout linkage**: Confirm `lz_layout_*` rows are created from layout-scanner output (no internal walk)

---

## Common Issues & Solutions

### Issue: Paths contain absolute paths or backslashes

**Solution:** Use the shared path normalization module:
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

# Validate path is repo-relative
if not is_repo_relative_path(normalized):
    raise ValueError(f"Path not repo-relative: {normalized}")
```

**Note:** Always use the shared module rather than inline normalization to ensure consistency across all tools.

### Issue: Commit not found

**Solution:** Add fallback content hash:
```python
def fallback_commit_hash(repo_path: Path) -> str:
    """Compute stable hash for non-git repos."""
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

### Issue: Schema validation fails

**Solution:** Check for:
- Missing required fields
- Wrong types (string vs integer)
- Extra fields not in schema (use `additionalProperties: false`)
- Pattern mismatches (UUID, semver, date-time)

---

## Tool-Specific Lessons Learned

Document gotchas and solutions discovered during each tool's migration.

### layout-scanner

| Issue | Solution |
|-------|----------|
| Missing `pyyaml` dependency | Added `pyyaml>=6.0.0` to requirements.txt |
| Relative imports fail when run directly | Run as module: `python -m scripts.analyze` instead of `python scripts/analyze.py` |
| `repository_path` contained absolute path | Override in analyze.py: `scan_result["repository_path"] = repo_name` |
| Schema version mismatch | Ensure `data.schema_version` matches `metadata.schema_version` |

### scc

| Issue | Solution |
|-------|----------|
| (Add lessons learned during scc migration) | |

### lizard

| Issue | Solution |
|-------|----------|
| (Add lessons learned during lizard migration) | |

### semgrep

| Issue | Solution |
|-------|----------|
| Schema contract required `metadata.schema_version` as const `1.0.0` | Updated output.schema.json to use `"const": "1.0.0"` instead of pattern |
| Relative imports fail when run directly | Run as module: `python -m scripts.analyze` instead of `python scripts/analyze.py` |
| Adapter needs `TABLE_DDL` for auto-creating tables | Define DDL dict and call `ensure_lz_tables()` before `validate_lz_schema()` |
| Landing zone table needs source definition in dbt | Add table to `models/schema.yml` under `sources.lz.tables` |
| Files not in layout cause errors | Adapter rejects import and logs missing paths (compliance fails) |

### roslyn-analyzers

| Issue | Solution |
|-------|----------|
| Schema version alignment check failed | Use `"const": "1.0.0"` not pattern for schema_version |
| Missing `tests/integration/` directory | Create directory with `__init__.py` placeholder |
| Rollup validation section missing from EVAL_STRATEGY.md | Add `## Rollup Validation` section listing rollups and dbt test paths |
| Duplicate violations in output (same file/rule/line) | De-duplicate by primary key tuple before inserting |
| Schema file doesn't exist during early development | Adapter fails validation if schema path is missing |
| Tool name contains hyphen (`roslyn-analyzers`) | Entity/repo classes use underscore (e.g., `RoslynViolation`, `RoslynRepository`) |

### trivy

| Issue | Solution |
|-------|----------|
| Multi-table output (targets, vulnerabilities, IaC misconfigs) | Create separate LZ tables and entities for each data type |
| Target paths may not match layout file paths | Use best-effort file_id resolution, log warnings for missing files |
| IaC misconfigurations use 0 for file-level line numbers | Convert 0 to -1 sentinel for DuckDB primary key compatibility |
| Vulnerability CVSS scores nested in different sources | Extract from `nvd`, `redhat`, or `ghsa` nested objects in priority order |
| Package vulnerabilities lack line numbers | Use -1 sentinel value (package vulns are file-level, not line-level) |
| Target key generation for vulnerability linkage | Generate SHA256-based key from path + type for consistent joining |

**Key Patterns:**
- **Envelope Structure**: `metadata` + `data` with nested `targets[]`, `vulnerabilities[]`, and `iac_misconfigurations{}` sections
- **File Linkage**: Targets are linked to layout via `file_id` resolution from `relative_path`
- **Severity Aggregation**: Pre-compute severity counts (`critical_count`, `high_count`, etc.) at target level
- **Multi-Entity Persistence**: Three separate insert methods for targets, vulnerabilities, and IaC misconfigs

**Gotchas:**
- Trivy's `Results[]` array contains targets with nested `Vulnerabilities[]` - flatten during transform
- CVSS scores are optional and may be missing from the source CVE database
- `FixedVersion` may be empty string when no fix is available - check for both `None` and `""`
- IaC misconfigurations include line numbers in `CauseMetadata` object, not at top level

---

## Partial Integration Pattern

Some tools may have sot-engine persistence integration (adapter, entities, dbt models) but lack the full standalone tool directory (`src/tools/<tool>/`). This is an acceptable intermediate state when:

1. The data ingestion pipeline is production-ready
2. The tool's analysis is run externally (CI, manual, etc.)
3. Compliance scanning is not required

**Trivy Example**: Full sot-engine integration exists:
- `persistence/adapters/trivy_adapter.py` (398 lines)
- `persistence/entities.py` (TrivyVulnerability, TrivyTarget, TrivyIacMisconfig)
- `persistence/repositories.py` (TrivyRepository)
- `dbt/models/staging/stg_trivy_*` (4 models)
- `dbt/models/marts/rollup_trivy_*` (2 models)
- Orchestrator wired with `--trivy-output` CLI flag

For full compliance, create `src/tools/trivy/` with all required components (Makefile, analyze.py, evaluate.py, schemas, tests, etc.).

---

## Tool Migration Status

| Tool | Phase | Status | Notes |
|------|-------|--------|-------|
| scc | Complete | ✅ | Pilot tool |
| lizard | Complete | ✅ | Pilot tool |
| layout-scanner | Complete | ✅ | Foundation tool |
| semgrep | Complete | ✅ | Adapter + dbt models done |
| roslyn-analyzers | Complete | ✅ | Adapter + dbt models done |
| trivy | Complete | ✅ | sot-engine + standalone tool directory |
| jscpd | Planned | ⬜ | |
| gitleaks | Planned | ⬜ | |

---

## Quick Reference: Full Adapter + dbt Migration

This section provides a complete checklist for adding a new tool to the SoT engine persistence layer.

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/sot-engine/persistence/entities.py` | Add | Frozen dataclass for tool entity |
| `src/sot-engine/persistence/repositories.py` | Add | Repository class with insert method |
| `src/sot-engine/persistence/adapters/<tool>_adapter.py` | Create | Adapter with TABLE_DDL, LZ_TABLES, persist() |
| `src/sot-engine/persistence/adapters/__init__.py` | Add | Export adapter class |
| `src/sot-engine/persistence/schema.sql` | Add | Landing zone table DDL |
| `src/sot-engine/dbt/models/schema.yml` | Add | Source table under `sources.lz.tables` |
| `src/sot-engine/dbt/models/staging/stg_<tool>_file_metrics.sql` | Create | File-level aggregation from LZ |
| `src/sot-engine/dbt/models/marts/rollup_<tool>_directory_counts_direct.sql` | Create | Direct directory rollup |
| `src/sot-engine/dbt/models/marts/rollup_<tool>_directory_counts_recursive.sql` | Create | Recursive directory rollup |
| `src/sot-engine/dbt/models/marts/rollup_<tool>_directory_direct_distributions.sql` | Create | Direct distribution stats |
| `src/sot-engine/dbt/models/marts/rollup_<tool>_directory_recursive_distributions.sql` | Create | Recursive distribution stats |
| `src/sot-engine/dbt/tests/test_rollup_<tool>_direct_vs_recursive.sql` | Create | Invariant test (recursive >= direct) |
| `src/tools/<tool>/EVAL_STRATEGY.md` | Add | Rollup Validation section |
| `src/tools/<tool>/tests/integration/__init__.py` | Create | Integration test directory |

### Entity Pattern (entities.py)

```python
@dataclass(frozen=True)
class <Tool>Metric:  # or <Tool>Violation, <Tool>Smell, etc.
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

### Repository Pattern (repositories.py)

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

### Adapter Constants Pattern

```python
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "<tool>" / "schemas" / "output.schema.json"

LZ_TABLES = {
    "lz_<tool>_<entity>": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        # tool-specific columns...
    }
}

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

### Adapter persist() Pattern

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
        run_id=metadata["run_id"],
        tool_name=metadata["tool_name"],
        tool_version=metadata["tool_version"],
        schema_version=metadata["schema_version"],
        branch=metadata["branch"],
        commit=metadata["commit"],
        timestamp=datetime.fromisoformat(metadata["timestamp"]),
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

### dbt Source Definition (schema.yml)

Add under `sources.lz.tables`:

```yaml
sources:
  - name: lz
    tables:
      # ... existing tables ...
      - name: lz_<tool>_<entity>
```

### dbt Staging Model Pattern

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

### dbt Rollup Direct Pattern

```sql
-- rollup_<tool>_directory_counts_direct.sql
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
),
files_direct as (
    select
        rm.tool_run_pk as run_pk,
        rm.layout_run_pk,
        lf.directory_id,
        lf.file_id
    from {{ source('lz', 'lz_layout_files') }} lf
    join run_map rm on rm.layout_run_pk = lf.run_pk
),
-- ... aggregate by directory_id ...
```

### dbt Rollup Recursive Pattern

```sql
-- rollup_<tool>_directory_counts_recursive.sql
-- Same as direct but join on directory ancestry:
files_recursive as (
    select
        rm.tool_run_pk as run_pk,
        rm.layout_run_pk,
        ld.directory_id as ancestor_directory_id,
        lf.file_id
    from {{ source('lz', 'lz_layout_files') }} lf
    join run_map rm on rm.layout_run_pk = lf.run_pk
    join {{ source('lz', 'lz_layout_directories') }} ld
        on ld.run_pk = lf.run_pk
        and (lf.directory_id = ld.directory_id
             or lf.relative_path like ld.relative_path || '/%')
),
-- ... aggregate by ancestor_directory_id ...
```

### dbt Test Pattern (direct vs recursive invariant)

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
   -- add other invariants...
```

### EVAL_STRATEGY.md Rollup Validation Section

Add at end of file:

```markdown
---

## Rollup Validation

Rollups:
- directory_direct_counts (<metric>s directly in directory)
- directory_recursive_counts (<metric>s in directory subtree)

Tests:
- src/sot-engine/dbt/tests/test_rollup_<tool>_direct_vs_recursive.sql
```

### Compliance Scanner Checks

After migration, verify all checks pass:

```bash
source .venv/bin/activate
python src/tool-compliance/tool_compliance.py --root .
```

Key checks for adapter + dbt layer:
- `schema.version_alignment` - schema_version uses `const` not pattern
- `structure.paths` - `tests/integration/` directory exists
- `evaluation.rollup_validation` - EVAL_STRATEGY.md has Rollup Validation section

---

## References

- [Caldera TOOL_REQUIREMENTS.md](./TOOL_REQUIREMENTS.md)
- [Caldera ARCHITECTURE_V2_PROPOSAL.md](./ARCHITECTURE_V2_PROPOSAL.md)
- [Vulcan DEVELOPMENT.md](../docs/DEVELOPMENT.md)
