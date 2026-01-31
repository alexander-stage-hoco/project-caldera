# Development Guide: Adding New Tools to Caldera

This guide covers how to add a new analysis tool to Project Caldera, from initial setup through compliance validation.

---

## Prerequisites

Before starting, ensure you have:

- Python 3.11+
- Access to the tool binary (e.g., `scc`, `lizard`, `trivy`)
- Understanding of the tool's output format
- Familiarity with JSON Schema (draft 2020-12)

---

## Quick Start

```bash
# 1. Create tool directory structure
mkdir -p src/tools/my-tool/{scripts/checks,schemas,tests/{unit,integration},eval-repos/{synthetic,real},evaluation/{ground-truth,llm/{judges,prompts,results},results}}

# 2. Copy template files
cp docs/templates/BLUEPRINT.md.template src/tools/my-tool/BLUEPRINT.md
cp docs/templates/EVAL_STRATEGY.md.template src/tools/my-tool/EVAL_STRATEGY.md

# 3. Create Makefile and scripts (see sections below)

# 4. Run compliance scanner to verify
python src/tool-compliance/tool_compliance.py --root .
```

---

## Directory Structure

Every tool MUST follow this layout:

```
src/tools/<tool-name>/
├── Makefile                    # Build orchestration (6 required targets)
├── README.md                   # Tool overview and usage
├── BLUEPRINT.md                # Architecture and design decisions
├── EVAL_STRATEGY.md            # Evaluation methodology
├── requirements.txt            # Python dependencies
│
├── scripts/
│   ├── analyze.py              # Main analysis script
│   ├── evaluate.py             # Programmatic evaluation
│   └── checks/                 # Evaluation check modules
│       ├── __init__.py
│       ├── accuracy.py
│       └── coverage.py
│
├── schemas/
│   └── output.schema.json      # Output JSON Schema (draft 2020-12)
│
├── tests/
│   ├── unit/                   # Unit tests
│   │   └── test_*.py
│   └── integration/            # Integration tests
│       └── test_*.py
│
├── eval-repos/
│   ├── synthetic/              # Synthetic test repositories
│   └── real/                   # Real-world test repositories
│
├── evaluation/
│   ├── ground-truth/           # Expected outputs for evaluation
│   │   └── *.json
│   ├── results/                # Evaluation run outputs
│   ├── scorecard.md            # Latest evaluation scorecard
│   └── llm/
│       ├── orchestrator.py     # LLM evaluation runner
│       ├── judges/             # LLM judge implementations
│       └── prompts/            # LLM prompt templates
│
└── outputs/                    # Analysis outputs (gitignored)
```

---

## Makefile Requirements

### Required Targets

```makefile
.PHONY: setup analyze evaluate evaluate-llm test clean

# Variables from orchestrator (with defaults)
REPO_PATH ?= eval-repos/synthetic
REPO_NAME ?= synthetic
OUTPUT_DIR ?= outputs/$(RUN_ID)
RUN_ID ?= $(shell uuidgen)
REPO_ID ?= $(shell uuidgen)
BRANCH ?= main
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "unknown")
EVAL_OUTPUT_DIR ?= evaluation/results

# Tool-specific
TOOL_VERSION ?= $(shell my-tool --version 2>/dev/null | head -1)

setup:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	# Install tool binary if needed

analyze:
	@mkdir -p $(OUTPUT_DIR)
	python -m scripts.analyze \
		--repo-path $(REPO_PATH) \
		--repo-name $(REPO_NAME) \
		--output-dir $(OUTPUT_DIR) \
		--run-id $(RUN_ID) \
		--repo-id $(REPO_ID) \
		--branch $(BRANCH) \
		--commit $(COMMIT)

evaluate:
	@mkdir -p $(EVAL_OUTPUT_DIR)
	python -m scripts.evaluate \
		--output-path $(OUTPUT_DIR)/output.json \
		--ground-truth-dir evaluation/ground-truth \
		--results-dir $(EVAL_OUTPUT_DIR)

evaluate-llm:
	python -m evaluation.llm.orchestrator \
		--output-path $(OUTPUT_DIR)/output.json \
		--results-dir $(EVAL_OUTPUT_DIR)

test:
	pytest tests/ -v

clean:
	rm -rf outputs/ evaluation/results/ __pycache__ .pytest_cache
```

### Variable Descriptions

| Variable | Source | Description |
|----------|--------|-------------|
| `REPO_PATH` | Orchestrator | Path to repository being analyzed |
| `REPO_NAME` | Orchestrator | Repository name for output naming |
| `OUTPUT_DIR` | Orchestrator | Directory for analysis outputs |
| `RUN_ID` | Orchestrator | UUID for this collection run |
| `REPO_ID` | Orchestrator | UUID for the repository |
| `BRANCH` | Orchestrator | Git branch being analyzed |
| `COMMIT` | Orchestrator | 40-character commit SHA |
| `EVAL_OUTPUT_DIR` | Local | Directory for evaluation outputs |

---

## Output Format (Envelope)

All tool outputs MUST use the Caldera envelope format:

```json
{
  "metadata": {
    "tool_name": "my-tool",
    "tool_version": "1.2.3",
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "repo_id": "660e8400-e29b-41d4-a716-446655440001",
    "branch": "main",
    "commit": "abc123def456abc123def456abc123def456abc1",
    "timestamp": "2025-01-30T10:00:00Z",
    "schema_version": "1.0.0"
  },
  "data": {
    "tool": "my-tool",
    "tool_version": "1.2.3",
    "files": [
      {
        "path": "src/main.py",
        "metric_a": 42,
        "metric_b": 3.14
      }
    ]
  }
}
```

### Required Metadata Fields (8)

| Field | Type | Description |
|-------|------|-------------|
| `tool_name` | string | Tool identifier (e.g., `scc`, `lizard`) |
| `tool_version` | semver | Tool version (e.g., `1.2.3`) |
| `run_id` | uuid | Collection run UUID |
| `repo_id` | uuid | Repository UUID |
| `branch` | string | Git branch name |
| `commit` | 40-hex | Git commit SHA |
| `timestamp` | ISO8601 | Analysis timestamp |
| `schema_version` | semver | Output schema version |

### Path Requirements

- All paths MUST be repo-relative (no leading `/`, `./`, or absolute paths)
- Use `/` as path separator (never `\`)
- No `..` segments allowed
- Directory paths use `.` for repository root

---

## analyze.py Template

```python
#!/usr/bin/env python3
"""Main analysis script for <tool-name>."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def get_tool_version() -> str:
    """Get the installed tool version."""
    result = subprocess.run(
        ["my-tool", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip().split()[0]


def run_analysis(repo_path: Path) -> dict:
    """Run the tool and parse output."""
    result = subprocess.run(
        ["my-tool", "--json", str(repo_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def normalize_path(path: str, repo_root: Path) -> str:
    """Normalize path to repo-relative format."""
    p = Path(path)
    if p.is_absolute():
        try:
            p = p.relative_to(repo_root)
        except ValueError:
            pass
    return str(p).replace("\\", "/").lstrip("./")


def build_envelope(
    data: dict,
    args: argparse.Namespace,
    tool_version: str,
) -> dict:
    """Wrap tool output in Caldera envelope format."""
    return {
        "metadata": {
            "tool_name": "my-tool",
            "tool_version": tool_version,
            "run_id": args.run_id,
            "repo_id": args.repo_id,
            "branch": args.branch,
            "commit": args.commit,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "my-tool",
            "tool_version": tool_version,
            **data,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run my-tool analysis")
    parser.add_argument("--repo-path", required=True, type=Path)
    parser.add_argument("--repo-name", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()

    tool_version = get_tool_version()
    raw_output = run_analysis(args.repo_path)

    # Normalize paths in output
    repo_root = args.repo_path.resolve()
    for file_entry in raw_output.get("files", []):
        if "path" in file_entry:
            file_entry["path"] = normalize_path(file_entry["path"], repo_root)

    envelope = build_envelope(raw_output, args, tool_version)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "output.json"
    output_path.write_text(json.dumps(envelope, indent=2))


if __name__ == "__main__":
    main()
```

---

## Output Schema Requirements

Create `schemas/output.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://caldera.internal/schemas/my-tool/output.schema.json",
  "title": "My Tool Output Schema",
  "type": "object",
  "required": ["metadata", "data"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": [
        "tool_name",
        "tool_version",
        "run_id",
        "repo_id",
        "branch",
        "commit",
        "timestamp",
        "schema_version"
      ],
      "properties": {
        "tool_name": { "type": "string", "const": "my-tool" },
        "tool_version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+" },
        "run_id": { "type": "string", "format": "uuid" },
        "repo_id": { "type": "string", "format": "uuid" },
        "branch": { "type": "string" },
        "commit": { "type": "string", "pattern": "^[0-9a-fA-F]{40}$" },
        "timestamp": { "type": "string", "format": "date-time" },
        "schema_version": { "type": "string", "const": "1.0.0" }
      }
    },
    "data": {
      "type": "object",
      "required": ["tool", "files"],
      "properties": {
        "tool": { "type": "string" },
        "tool_version": { "type": "string" },
        "files": {
          "type": "array",
          "items": { "$ref": "#/$defs/FileMetric" }
        }
      }
    }
  },
  "$defs": {
    "FileMetric": {
      "type": "object",
      "required": ["path"],
      "properties": {
        "path": { "type": "string" },
        "metric_a": { "type": "integer", "minimum": 0 },
        "metric_b": { "type": "number" }
      }
    }
  }
}
```

### Schema Requirements

- Use `$schema`: `https://json-schema.org/draft/2020-12/schema`
- Use `const` for `schema_version` (not pattern) for version alignment check
- Define `metadata` and `data` as required top-level properties
- All 8 metadata fields must be required

---

## SoT Adapter Integration

After the standalone tool is working, integrate with the SoT engine.

### 1. Create Entity Dataclass

Add to `src/sot-engine/persistence/entities.py`:

```python
@dataclass(frozen=True)
class MyToolMetric:
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    metric_a: int
    metric_b: float
```

### 2. Create Repository

Add to `src/sot-engine/persistence/repositories.py`:

```python
class MyToolRepository:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def insert_metrics(self, items: Iterable[MyToolMetric]) -> int:
        data = [(i.run_pk, i.file_id, i.directory_id, i.relative_path,
                 i.metric_a, i.metric_b) for i in items]
        if not data:
            return 0
        self._conn.executemany(
            """INSERT INTO lz_my_tool_metrics
               (run_pk, file_id, directory_id, relative_path, metric_a, metric_b)
               VALUES (?, ?, ?, ?, ?, ?)""",
            data,
        )
        return len(data)
```

### 3. Create Adapter

Create `src/sot-engine/persistence/adapters/my_tool_adapter.py`:

```python
"""Adapter for my-tool output persistence."""

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "my-tool" / "schemas" / "output.schema.json"

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

QUALITY_RULES = ["paths", "ranges", "required_fields"]

TABLE_DDL = {
    "lz_my_tool_metrics": """
        CREATE TABLE IF NOT EXISTS lz_my_tool_metrics (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            metric_a INTEGER,
            metric_b DOUBLE,
            PRIMARY KEY (run_pk, file_id)
        )
    """,
}


class MyToolAdapter:
    def __init__(self, run_repo, layout_repo, tool_repo):
        self._run_repo = run_repo
        self._layout_repo = layout_repo
        self._tool_repo = tool_repo

    def validate_schema(self, payload: dict) -> None:
        # Validate against SCHEMA_PATH
        pass

    def validate_lz_schema(self) -> None:
        # Validate LZ_TABLES columns exist
        pass

    def validate_quality(self, files: list) -> None:
        # Validate QUALITY_RULES
        pass

    def ensure_lz_tables(self) -> list[str]:
        # Create tables from TABLE_DDL if missing
        pass

    def persist(self, payload: dict) -> int:
        self.validate_schema(payload)
        self.ensure_lz_tables()
        self.validate_lz_schema()
        # ... persist logic ...
```

### 4. Register Tool-Specific Rules

Add to `src/tool-compliance/tool_compliance.py` `TOOL_RULES`:

```python
TOOL_RULES = {
    # ...
    "my-tool": {
        "required_check_modules": ["accuracy.py", "coverage.py"],
        "required_prompts": ["accuracy.md", "coverage.md"],
        "adapter": ("persistence.adapters.my_tool_adapter", "MyToolAdapter"),
    },
}
```

---

## dbt Rollup Models

After creating the adapter, add dbt models for directory-level aggregations.

### Required Models (4 per tool)

Create in `src/sot-engine/dbt/models/marts/`:

| Model | Purpose |
|-------|---------|
| `rollup_<tool>_directory_counts_direct.sql` | Counts for files directly in directory |
| `rollup_<tool>_directory_counts_recursive.sql` | Counts for all files in subtree |
| `rollup_<tool>_directory_direct_distributions.sql` | Distribution stats (direct) |
| `rollup_<tool>_directory_recursive_distributions.sql` | Distribution stats (recursive) |

### Run Mapping Pattern

All rollup models must map tool runs to layout runs:

```sql
with tool_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'my-tool'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
run_map as (
    select
        tr.run_pk as tool_run_pk,
        lr.run_pk as layout_run_pk
    from tool_runs tr
    join layout_runs lr on lr.collection_run_id = tr.collection_run_id
)
```

### Direct vs Recursive

- **Direct:** Join on exact `directory_id` match (files in this directory only)
- **Recursive:** Join on path prefix (files in this directory or any descendant)

### Required dbt Test

Create `src/sot-engine/dbt/tests/test_rollup_<tool>_direct_vs_recursive.sql`:

```sql
-- Validates recursive counts >= direct counts
select
    r.run_pk,
    r.directory_id,
    r.total_count as recursive_count,
    d.total_count as direct_count
from {{ ref('rollup_<tool>_directory_counts_recursive') }} r
join {{ ref('rollup_<tool>_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.total_count < d.total_count
   or r.file_count < d.file_count
```

### Update EVAL_STRATEGY.md

Add a `## Rollup Validation` section to your tool's EVAL_STRATEGY.md:

```markdown
## Rollup Validation

Rollups:
- directory_counts_direct
- directory_counts_recursive

Tests:
- src/sot-engine/dbt/tests/test_rollup_<tool>_direct_vs_recursive.sql
```

This section is **required** for compliance scanner (`evaluation.rollup_validation` check).

---

## Running the Compliance Scanner

```bash
# Basic scan (structure and schema checks only)
python src/tool-compliance/tool_compliance.py --root .

# Full scan with execution
python src/tool-compliance/tool_compliance.py --root . \
  --run-analysis --run-evaluate --run-llm

# Output reports
python src/tool-compliance/tool_compliance.py --root . \
  --out-json /tmp/report.json \
  --out-md /tmp/report.md
```

### Compliance Check Categories

See [TOOL_REQUIREMENTS.md](./TOOL_REQUIREMENTS.md) for the complete list of 36+ compliance checks.

---

## Common Issues

### Paths contain absolute paths

Use the shared path normalization module:

```python
from common.path_normalization import normalize_file_path

normalized = normalize_file_path(raw_path, repo_root)
```

### Commit not found (non-git repo)

Compute deterministic content hash:

```python
def fallback_commit_hash(repo_path: Path) -> str:
    import hashlib
    sha1 = hashlib.sha1()
    for path in sorted(repo_path.rglob("*")):
        if path.is_file() and ".git" not in path.parts:
            sha1.update(path.relative_to(repo_path).as_posix().encode())
            sha1.update(b"\0")
            sha1.update(path.read_bytes())
    return sha1.hexdigest()
```

### Schema validation fails

Check for:
- Missing required fields
- Wrong types (string vs integer)
- Pattern mismatches (UUID, semver, date-time)
- `schema_version` uses `const` not pattern

---

## References

- [TOOL_REQUIREMENTS.md](./TOOL_REQUIREMENTS.md) - Complete requirements specification
- [TOOL_MIGRATION_CHECKLIST.md](./TOOL_MIGRATION_CHECKLIST.md) - Vulcan to Caldera migration guide
- [templates/BLUEPRINT.md.template](./templates/BLUEPRINT.md.template) - Architecture document template
- [templates/EVAL_STRATEGY.md.template](./templates/EVAL_STRATEGY.md.template) - Evaluation strategy template
