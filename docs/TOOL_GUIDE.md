# Tool Implementation Guide

This guide covers how to add new analysis tools to Project Caldera and migrate existing tools from Project Vulcan.

---

## Quick Start

**Decision tree:**
- **New tool?** → Start at [Part 1: Creating a New Tool](#part-1-creating-a-new-tool)
- **Migrating from Vulcan?** → Start at [Part 2: Migrating from Vulcan](#part-2-migrating-from-vulcan)
- **Adding SoT integration to existing tool?** → Start at [Part 3: SoT Integration](#part-3-sot-integration)

**Fastest path for new tools:**
```bash
# Generate complete tool skeleton
python scripts/create-tool.py my-tool --sot-integration

# Verify structure
python src/tool-compliance/tool_compliance.py src/tools/my-tool --preflight
```

---

## Prerequisites

- Python 3.12+
- Access to the tool binary (e.g., `scc`, `lizard`, `trivy`)
- Understanding of the tool's output format
- Familiarity with JSON Schema (draft 2020-12)

---

## Part 1: Creating a New Tool

### Step 1: Generate Tool Skeleton

```bash
# Basic structure
python scripts/create-tool.py my-tool

# With SoT adapter files
python scripts/create-tool.py my-tool --sot-integration

# Preview without creating files
python scripts/create-tool.py my-tool --dry-run
```

This creates the complete directory structure with template files.

### Step 2: Copy Document Templates

```bash
cp docs/templates/BLUEPRINT.md.template src/tools/my-tool/BLUEPRINT.md
cp docs/templates/EVAL_STRATEGY.md.template src/tools/my-tool/EVAL_STRATEGY.md
```

Fill in the templates with your tool's specifics.

### Step 3: Implement analyze.py

The main analysis script must:
1. Accept required CLI arguments
2. Run the tool binary
3. Wrap output in envelope format
4. Normalize all paths to repo-relative

```python
#!/usr/bin/env python3
"""Main analysis script for my-tool."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from common.path_normalization import normalize_file_path


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


def build_envelope(data: dict, args: argparse.Namespace, tool_version: str) -> dict:
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
            file_entry["path"] = normalize_file_path(file_entry["path"], repo_root)

    envelope = build_envelope(raw_output, args, tool_version)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "output.json"
    output_path.write_text(json.dumps(envelope, indent=2))


if __name__ == "__main__":
    main()
```

### Step 4: Create Output Schema

Create `schemas/output.schema.json` following the envelope format. See [REFERENCE.md](./REFERENCE.md) for the complete schema template.

Key requirements:
- Use `$schema`: `https://json-schema.org/draft/2020-12/schema`
- Use `const` for `schema_version`
- All 8 metadata fields must be required

### Step 5: Set Up Makefile

Include Makefile.common and define tool-specific variables:

```makefile
SHELL := /bin/bash
include ../Makefile.common

# Tool-specific variables
REPO_PATH ?= eval-repos/synthetic
REPO_NAME ?= synthetic
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000")
TOOL_VERSION ?= $(shell my-tool --version 2>/dev/null | head -1)

# Required targets
.PHONY: setup analyze evaluate evaluate-llm test clean

setup: $(VENV_READY)
	@echo "Installing dependencies..."
	$(PIP) install -r requirements.txt

analyze: $(VENV_READY)
	@mkdir -p $(OUTPUT_DIR)
	$(PYTHON_VENV) -m scripts.analyze \
		--repo-path $(REPO_PATH) \
		--repo-name $(REPO_NAME) \
		--output-dir $(OUTPUT_DIR) \
		--run-id $(RUN_ID) \
		--repo-id $(REPO_ID) \
		--branch $(BRANCH) \
		--commit $(COMMIT)

evaluate: $(VENV_READY)
	@mkdir -p $(EVAL_OUTPUT_DIR)
	$(PYTHON_VENV) -m scripts.evaluate \
		--output-path $(OUTPUT_DIR)/output.json \
		--ground-truth-dir evaluation/ground-truth \
		--results-dir $(EVAL_OUTPUT_DIR)

evaluate-llm: $(VENV_READY)
	$(PYTHON_VENV) -m evaluation.llm.orchestrator \
		--output-path $(OUTPUT_DIR)/output.json \
		--results-dir $(EVAL_OUTPUT_DIR)

test: $(VENV_READY)
	$(PYTHON_VENV) -m pytest tests/ -v

clean:
	rm -rf outputs/ evaluation/results/ __pycache__ .pytest_cache
```

### Step 6: Create LLM Judges

Tools require minimum 4 LLM judges. See [EVALUATION.md](./EVALUATION.md) for the complete guide.

Quick setup:
```python
# src/tools/my-tool/evaluation/llm/judges/base.py
from shared.evaluation import BaseJudge as SharedBaseJudge

class BaseJudge(SharedBaseJudge):
    """Tool-specific extensions."""

    @property
    def prompt_file(self) -> Path:
        return self.working_dir / "evaluation" / "llm" / "prompts" / f"{self.dimension_name}.md"
```

### Step 7: Run Compliance Scanner

```bash
# Preflight check (fast)
python src/tool-compliance/tool_compliance.py src/tools/my-tool --preflight

# Full check
python src/tool-compliance/tool_compliance.py src/tools/my-tool
```

See [COMPLIANCE.md](./COMPLIANCE.md) for fixing any failures.

---

## Part 2: Migrating from Vulcan

### Overview

| Aspect | Vulcan | Caldera |
|--------|--------|---------|
| Output Format | Simple JSON (`data` only) | Envelope JSON (`metadata` + `data`) |
| Output Path | `$(OUTPUT_DIR)/$(REPO_NAME).json` | `outputs/<run-id>/output.json` |
| Makefile Targets | 4 | 6 (+`evaluate-llm`, `test`) |
| Persistence | Aggregator | SoT adapters + dbt |
| Compliance | Informal | Automated scanner |

### Migration Steps

#### Step 1: Copy Tool Directory

```bash
cp -r /vulcan/src/tools/<tool> /caldera/src/tools/<tool>

# Do NOT copy: .venv/, output/, __pycache__/, .pytest_cache/
```

#### Step 2: Update Makefile

1. Add `include ../Makefile.common` at top
2. Change `OUTPUT_DIR` to `outputs/$(RUN_ID)` pattern
3. Add `evaluate-llm` target (not `llm-evaluate`)
4. Add `test` target if missing

**Common pitfalls:**
- Target must be `evaluate-llm` not `llm-evaluate`
- OUTPUT_DIR must be `outputs/...` (plural) not `output/...`

#### Step 3: Update analyze.py

1. Add required CLI arguments: `--run-id`, `--repo-id`, `--branch`, `--commit`
2. Wrap output in envelope format (see Part 1)
3. Change output path to `output.json`
4. Normalize all paths with `common.path_normalization`

**Critical:** `commit` must be 40-character hex SHA.

#### Step 4: Update Output Schema

1. Change `$schema` to draft 2020-12
2. Add `metadata` object with 8 required fields
3. Use `const` for `schema_version` (not pattern)

#### Step 5: Create Tests/Integration Directory

```bash
mkdir -p tests/integration
touch tests/integration/__init__.py
```

#### Step 6: Add Rollup Validation to EVAL_STRATEGY.md

```markdown
## Rollup Validation

Rollups:
- directory_direct_counts
- directory_recursive_counts

Tests:
- src/sot-engine/dbt/tests/test_rollup_<tool>_direct_vs_recursive.sql
```

#### Step 7: Run Compliance Scanner

```bash
python src/tool-compliance/tool_compliance.py src/tools/<tool>
```

### Tool-Specific Lessons Learned

#### layout-scanner
- Missing `pyyaml` dependency → Added to requirements.txt
- Relative imports fail → Run as module: `python -m scripts.analyze`
- `repository_path` contained absolute path → Override in analyze.py

#### semgrep
- Schema contract required `schema_version` as const
- Adapter needs `TABLE_DDL` for auto-creating tables
- Add source definition in dbt schema.yml

#### roslyn-analyzers
- Schema version alignment check failed → Use `const` not pattern
- Missing `tests/integration/` directory
- Tool name contains hyphen → Use underscore in entity classes

#### trivy
- Multi-table output → Create separate LZ tables for each
- CVSS scores nested → Extract in priority order (nvd, redhat, ghsa)
- Package vulnerabilities lack line numbers → Use -1 sentinel

---

## Part 3: SoT Integration

### Step 1: Create Entity Dataclass

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

    def __post_init__(self) -> None:
        if not self.file_id:
            raise ValueError("file_id required")
```

### Step 2: Create Repository

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

### Step 3: Create Adapter

Create `src/sot-engine/persistence/adapters/my_tool_adapter.py`:

```python
"""Adapter for my-tool output persistence."""
from __future__ import annotations

from pathlib import Path

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

See [REFERENCE.md](./REFERENCE.md) for complete adapter patterns.

### Step 4: Add Table to schema.sql

```sql
CREATE TABLE IF NOT EXISTS lz_my_tool_metrics (
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

### Step 5: Export Adapter

Add to `src/sot-engine/persistence/adapters/__init__.py`:

```python
from .my_tool_adapter import MyToolAdapter
```

### Step 6: Wire Orchestrator

Update `src/sot-engine/orchestrator.py`:

```python
TOOL_INGESTION_CONFIGS = [
    # ... existing configs
    ToolIngestionConfig(
        tool_name="my-tool",
        makefile_dir="src/tools/my-tool",
        adapter_class=MyToolAdapter,
    ),
]
```

### Step 7: Create dbt Models

Generate with automation or create manually:

```bash
python scripts/generate_dbt_models.py my-tool --table lz_my_tool_metrics --metrics metric_a,metric_b
```

This creates:
- Staging model
- Direct/recursive rollup models
- Distribution models

### Step 8: Create dbt Test

Create `src/sot-engine/dbt/tests/test_rollup_my_tool_direct_vs_recursive.sql`:

```sql
select
    r.run_pk,
    r.directory_id,
    r.total_count as recursive_count,
    d.total_count as direct_count
from {{ ref('rollup_my_tool_directory_counts_recursive') }} r
join {{ ref('rollup_my_tool_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.total_count < d.total_count
   or r.file_count < d.file_count
```

---

## Part 4: Automation Scripts

### Tool Creation Script

```bash
python scripts/create-tool.py <name>                    # Basic structure
python scripts/create-tool.py <name> --sot-integration  # With adapter files
python scripts/create-tool.py <name> --sot-only         # SoT files only
python scripts/create-tool.py <name> --dry-run          # Preview
```

### Ground Truth Seeding

Auto-seed from analysis output:

```bash
python scripts/seed_ground_truth.py <tool> <output.json>
python scripts/seed_ground_truth.py <tool> <output.json> --dry-run
```

Supported tools: scc, lizard, semgrep, layout-scanner, roslyn-analyzers, trivy, git-sizer

### dbt Model Generator

```bash
python scripts/generate_dbt_models.py <tool> --table <lz_table> --metrics <col1,col2>
```

Generates staging, rollup, and distribution models.

### Pre-commit Hooks

Install for automatic compliance checking:

```bash
pip install pre-commit
pre-commit install
```

Runs preflight compliance checks on modified tool directories.

---

## Part 5: Verification

### Verification Commands

| Checkpoint | Command |
|------------|---------|
| After copying directory | `python src/tool-compliance/tool_compliance.py src/tools/<tool> --preflight` |
| After Makefile changes | `make -n analyze` (dry run) |
| After analyze.py changes | `make analyze && cat outputs/*/output.json \| python -m json.tool` |
| After schema changes | `python -c "import json, jsonschema; ..."` |
| Full compliance | `python src/tool-compliance/tool_compliance.py src/tools/<tool>` |
| Run all tests | `make test` |
| dbt models | `cd src/sot-engine/dbt && dbt run --profiles-dir . && dbt test --profiles-dir .` |

### Post-Implementation Checklist

- [ ] `make test` passes in tool directory
- [ ] `make analyze` produces valid output
- [ ] `make evaluate` completes successfully
- [ ] Output validates against schema
- [ ] All paths are repo-relative
- [ ] Compliance scanner shows all checks passing
- [ ] dbt models build and tests pass
- [ ] Layout linkage works (file_id resolution)

---

## Common Issues & Solutions

### Path Issues

**Problem:** Paths contain absolute paths or backslashes

**Solution:**
```python
from common.path_normalization import normalize_file_path, is_repo_relative_path

normalized = normalize_file_path(raw_path, repo_root)
if not is_repo_relative_path(normalized):
    raise ValueError(f"Path not repo-relative: {normalized}")
```

### Commit Not Found

**Problem:** Non-git repository has no commit SHA

**Solution:** Use fallback content hash (see [REFERENCE.md](./REFERENCE.md)).

### Schema Validation Fails

**Check for:**
- Missing required fields
- Wrong types (string vs integer)
- Pattern mismatches (UUID, semver, date-time)
- `schema_version` uses `const` not pattern

### Collection Run Already Exists

**Solution:** Use `--replace` flag:
```bash
python src/sot-engine/orchestrator.py --repo-path . --commit HEAD --replace
```

### dbt Test Failures

**Check:** Rollup invariant: recursive count >= direct count

**Verify:** Run mapping correctly links tool and layout runs.

---

## References

- [REFERENCE.md](./REFERENCE.md) - Technical specifications (envelope, paths, patterns)
- [COMPLIANCE.md](./COMPLIANCE.md) - Compliance requirements and checks
- [EVALUATION.md](./EVALUATION.md) - LLM judge infrastructure
- [REPORTS.md](./REPORTS.md) - dbt analyses and reports
- [templates/BLUEPRINT.md.template](./templates/BLUEPRINT.md.template) - Architecture template
- [templates/EVAL_STRATEGY.md.template](./templates/EVAL_STRATEGY.md.template) - Evaluation template
