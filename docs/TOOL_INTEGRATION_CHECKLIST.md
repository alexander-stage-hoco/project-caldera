# Tool Integration Checklist

A complete, step-by-step checklist for building, migrating, or integrating tools into Project Caldera. Follow this guide to avoid forgotten steps and integration bugs.

---

## Quick Start

**Decision tree:**
- **New tool?** → Start at [Phase 1: Initial Setup](#phase-1-initial-setup-structure)
- **Migrating from Vulcan?** → Start at [Appendix A: Migrating from Vulcan](#appendix-a-migrating-from-vulcan)
- **Adding SoT integration to existing tool?** → Start at [Phase 5: SoT Integration](#phase-5-sot-integration-persistence)

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

**Quick Navigation:**
- [Phase 1: Initial Setup](#phase-1-initial-setup-structure)
- [Phase 2: Analysis Script & Output](#phase-2-analysis-script--output)
- [Phase 3: Evaluation Infrastructure](#phase-3-evaluation-infrastructure)
- [Phase 4: Testing](#phase-4-testing)
- [Phase 5: SoT Integration](#phase-5-sot-integration-persistence)
- [Phase 6: dbt Models & Verification](#phase-6-dbt-models--verification)
- [Quick Reference Commands](#quick-reference-commands)
- [Common Pitfalls](#common-pitfalls)
- [Troubleshooting](#troubleshooting)
- [Appendix A: Migrating from Vulcan](#appendix-a-migrating-from-vulcan)
- [Appendix B: Automation Scripts](#appendix-b-automation-scripts)

---

## Phase 1: Initial Setup (Structure)

### 1.1 Create Tool Directory

```bash
# Generate complete skeleton with SoT integration
python scripts/create-tool.py <tool-name> --sot-integration

# Or basic structure only
python scripts/create-tool.py <tool-name>

# Preview without creating files
python scripts/create-tool.py <tool-name> --dry-run
```

### 1.2 Required Paths Checklist (18 paths)

Verify all 18 required paths exist:

| # | Path | Purpose | Check |
|---|------|---------|:-----:|
| 1 | `Makefile` | Build orchestration | [ ] |
| 2 | `README.md` | Tool overview and usage | [ ] |
| 3 | `BLUEPRINT.md` | Architecture and design decisions | [ ] |
| 4 | `EVAL_STRATEGY.md` | Evaluation methodology | [ ] |
| 5 | `requirements.txt` | Python dependencies | [ ] |
| 6 | `scripts/analyze.py` | Main analysis script | [ ] |
| 7 | `scripts/evaluate.py` | Programmatic evaluation | [ ] |
| 8 | `scripts/checks/` | Evaluation check modules | [ ] |
| 9 | `schemas/output.schema.json` | Output JSON Schema | [ ] |
| 10 | `eval-repos/synthetic/` | Synthetic test repositories | [ ] |
| 11 | `eval-repos/real/` | Real-world test repositories | [ ] |
| 12 | `evaluation/ground-truth/` | Expected outputs for evaluation | [ ] |
| 13 | `evaluation/llm/orchestrator.py` | LLM evaluation runner | [ ] |
| 14 | `evaluation/llm/judges/` | LLM judge implementations | [ ] |
| 15 | `evaluation/llm/prompts/` | LLM prompt templates | [ ] |
| 16 | `evaluation/scorecard.md` | Latest evaluation scorecard | [ ] |
| 17 | `tests/unit/` | Unit tests | [ ] |
| 18 | `tests/integration/` | Integration tests | [ ] |

**Quick create missing paths:**
```bash
mkdir -p tests/integration tests/unit
mkdir -p eval-repos/synthetic eval-repos/real
mkdir -p evaluation/ground-truth evaluation/llm/judges evaluation/llm/prompts
mkdir -p scripts/checks
touch tests/integration/__init__.py tests/unit/__init__.py
touch evaluation/scorecard.md scripts/checks/__init__.py
```

### 1.3 Copy Document Templates

```bash
cp docs/templates/BLUEPRINT.md.template src/tools/<tool>/BLUEPRINT.md
cp docs/templates/EVAL_STRATEGY.md.template src/tools/<tool>/EVAL_STRATEGY.md
```

- [ ] Fill in BLUEPRINT.md sections: Executive Summary, Architecture, Implementation Plan, Configuration, Performance, Evaluation, Risk
- [ ] Fill in EVAL_STRATEGY.md sections: Philosophy, Dimension Summary, Check Catalog, Scoring, Decision Thresholds, Ground Truth

### 1.4 Configure Makefile

**Required 6 targets:**

| Target | Description | Check |
|--------|-------------|:-----:|
| `setup` | Install tool binary and Python dependencies | [ ] |
| `analyze` | Run analysis, output to `outputs/<run-id>/output.json` | [ ] |
| `evaluate` | Run programmatic evaluation | [ ] |
| `evaluate-llm` | Run LLM judges | [ ] |
| `test` | Run unit + integration tests | [ ] |
| `clean` | Remove generated files | [ ] |

**Makefile template:**
```makefile
SHELL := /bin/bash
include ../Makefile.common

# Tool-specific variables
REPO_PATH ?= eval-repos/synthetic
REPO_NAME ?= synthetic
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000")

.PHONY: setup analyze evaluate evaluate-llm test clean

setup: $(VENV_READY)
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

**Checklist:**
- [ ] Includes `../Makefile.common` at top
- [ ] Uses `$(OUTPUT_DIR)` (inherits `outputs/$(RUN_ID)` from Makefile.common)
- [ ] Target is `evaluate-llm` (NOT `llm-evaluate`)
- [ ] analyze produces `output.json` (singular, not custom names)

### 1.5 Compliance Expectations by Phase

Run compliance checks frequently during development:

```bash
# Quick structure check (~100ms)
python src/tool-compliance/tool_compliance.py src/tools/<tool> --preflight

# Full check (after analysis works)
python src/tool-compliance/tool_compliance.py src/tools/<tool>
```

#### Phase 1-2: Expected Results

**Should Pass:** structure.paths, make.targets, make.uses_common, schema.*, docs.*

**Expected to Fail (fix later):**
- `evaluation.*` - No evaluation outputs yet
- `adapter.*`, `sot.*`, `dbt.*`, `entity.*` - No SoT integration yet

#### Phase 5 Prerequisite: Create Rules File

Before SoT integration passes, create `src/tool-compliance/rules/<tool>.yaml`:

```yaml
required_check_modules:
  - accuracy.py
  - coverage.py

required_prompts:
  - accuracy.md
  - actionability.md

adapter:
  module: persistence.adapters.<tool>_adapter
  class: <Tool>Adapter
```

And register entities in `src/tool-compliance/rules/common.yaml`:

```yaml
tool_entities:
  <tool>:
    - <Tool>Entity1
    - <Tool>Entity2

entity_repository_map:
  <Tool>Entity1:
    repository: <Tool>Repository
    method: insert_entity1s
```

### 1.6 Set Up Python Environment

```bash
cd src/tools/<tool>
make setup
```

**Minimum requirements.txt:**
```
pytest>=7.0.0
pytest-cov>=4.0.0  # Required for test.coverage_threshold check
jsonschema>=4.0.0
```

- [ ] `requirements.txt` includes all tool dependencies
- [ ] `pytest-cov>=4.0.0` in requirements.txt (required for compliance)
- [ ] Virtual environment created at `.venv/`
- [ ] Tool binary is installed and accessible

---

## Phase 2: Analysis Script & Output

### 2.1 Implement scripts/analyze.py

**Required 7 CLI arguments:**

| Argument | Type | Required | Description |
|----------|------|:--------:|-------------|
| `--repo-path` | Path | Yes | Path to repository being analyzed |
| `--repo-name` | str | Yes | Repository name |
| `--output-dir` | Path | Yes | Directory for output |
| `--run-id` | UUID | Yes | Collection run identifier |
| `--repo-id` | UUID | Yes | Repository identifier |
| `--branch` | str | No | Git branch (default: main) |
| `--commit` | str | Yes | 40-character commit SHA |

**Template:**
```python
#!/usr/bin/env python3
"""Main analysis script for <tool>."""
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
        ["<tool>", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip().split()[0]


def run_analysis(repo_path: Path) -> dict:
    """Run the tool and parse output."""
    result = subprocess.run(
        ["<tool>", "--json", str(repo_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def build_envelope(data: dict, args: argparse.Namespace, tool_version: str) -> dict:
    """Wrap tool output in Caldera envelope format."""
    return {
        "metadata": {
            "tool_name": "<tool>",
            "tool_version": tool_version,
            "run_id": args.run_id,
            "repo_id": args.repo_id,
            "branch": args.branch,
            "commit": args.commit,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "<tool>",
            "tool_version": tool_version,
            **data,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run <tool> analysis")
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

**Checklist:**
- [ ] Accepts all 7 required CLI arguments
- [ ] Wraps output in envelope format
- [ ] Output file is `output.json`
- [ ] All paths normalized with `normalize_file_path()`

### 2.2 Envelope Format (Required 8 Metadata Fields)

```json
{
  "metadata": {
    "tool_name": "<tool>",
    "tool_version": "1.0.0",
    "run_id": "<uuid>",
    "repo_id": "<uuid>",
    "branch": "main",
    "commit": "abc123...40chars",
    "timestamp": "2025-01-15T10:30:00Z",
    "schema_version": "1.0.0"
  },
  "data": {
    "tool": "<tool>",
    "tool_version": "1.0.0",
    "files": [ ... ]
  }
}
```

| Field | Format | Check |
|-------|--------|:-----:|
| `tool_name` | string | [ ] |
| `tool_version` | semver (`^\d+\.\d+\.\d+$`) | [ ] |
| `run_id` | UUID | [ ] |
| `repo_id` | UUID | [ ] |
| `branch` | string | [ ] |
| `commit` | 40-hex SHA (`^[0-9a-fA-F]{40}$`) | [ ] |
| `timestamp` | ISO8601 date-time | [ ] |
| `schema_version` | semver | [ ] |

### 2.3 Create Output Schema

Create `schemas/output.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "<Tool> Output",
  "type": "object",
  "required": ["metadata", "data"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": [
        "tool_name", "tool_version", "run_id", "repo_id",
        "branch", "commit", "timestamp", "schema_version"
      ],
      "properties": {
        "tool_name": { "type": "string" },
        "tool_version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
        "run_id": { "type": "string", "format": "uuid" },
        "repo_id": { "type": "string", "format": "uuid" },
        "branch": { "type": "string" },
        "commit": { "type": "string", "pattern": "^[0-9a-fA-F]{40}$" },
        "timestamp": { "type": "string", "format": "date-time" },
        "schema_version": { "const": "1.0.0" }
      }
    },
    "data": { "type": "object" }
  }
}
```

**Checklist:**
- [ ] Uses `$schema`: `https://json-schema.org/draft/2020-12/schema`
- [ ] Uses `const` for `schema_version` (NOT `pattern`)
- [ ] All 8 metadata fields in `required` array
- [ ] Both `metadata` and `data` are required

### 2.4 Path Normalization

**Rules:**
- No leading `/` (absolute paths)
- No leading `./` (explicit relative)
- No `..` segments (parent directory)
- POSIX separators (`/` not `\`)
- Root directory is `.` (not `/` or empty)

| Valid | Invalid |
|-------|---------|
| `src/main.py` | `/src/main.py` |
| `lib/utils.ts` | `./lib/utils.ts` |
| `tests/test_foo.py` | `../outside/file.py` |
| `src/foo/bar.py` | `src\foo\bar.py` |
| `.` | `/` or empty string |

**Implementation:**
```python
from common.path_normalization import (
    normalize_file_path,
    normalize_dir_path,
    is_repo_relative_path,
)

# Normalize file path
normalized = normalize_file_path(raw_path, repo_root)

# Validate
if not is_repo_relative_path(normalized):
    raise ValueError(f"Path not repo-relative: {normalized}")
```

### 2.5 Commit Hash Handling

**For git repositories:**
```python
commit = subprocess.check_output(
    ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
    text=True,
).strip()
```

**For non-git repositories (fallback hash):**
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

- [ ] Commit is always 40 hexadecimal characters
- [ ] Fallback hash used for non-git repos

---

## Phase 3: Evaluation Infrastructure

### 3.1 Create Ground Truth Files

Create `evaluation/ground-truth/synthetic.json`:

```json
{
  "repo_name": "synthetic",
  "expected_file_count": 10,
  "files": {
    "src/main.py": {
      "metric_a": 42,
      "metric_b": 3.14
    }
  }
}
```

**Ground truth modes:**
| Mode | Required File | Description |
|------|---------------|-------------|
| `synthetic_json` | `evaluation/ground-truth/synthetic.json` | Single file for synthetic repo |
| `per_language` | `evaluation/ground-truth/<repo>.json` | One file per repository |
| `any` | At least one `.json` file | Flexible |

- [ ] Ground truth file created for synthetic repo
- [ ] Expected values documented

### 3.2 Implement LLM Judges (Minimum 4)

| Judge | File | Purpose | Check |
|-------|------|---------|:-----:|
| Accuracy | `evaluation/llm/judges/accuracy.py` | Validates findings match expected | [ ] |
| Actionability | `evaluation/llm/judges/actionability.py` | Assesses if findings are useful | [ ] |
| False Positive | `evaluation/llm/judges/false_positive.py` | Evaluates false positive rate | [ ] |
| Integration Fit | `evaluation/llm/judges/integration.py` | Validates SoT schema compatibility | [ ] |

**Base judge template:**
```python
# evaluation/llm/judges/base.py
from __future__ import annotations

from pathlib import Path
from shared.evaluation.base_judge import BaseJudge as SharedBaseJudge


class BaseJudge(SharedBaseJudge):
    """Tool-specific base judge with extensions."""

    def __init__(
        self,
        model: str = "opus-4.5",
        timeout: int = 120,
        evaluation_mode: str | None = None,  # Required for synthetic context
    ):
        super().__init__(
            model=model,
            timeout=timeout,
            evaluation_mode=evaluation_mode,
        )

    @property
    def prompt_file(self) -> Path:
        return self.working_dir / "evaluation" / "llm" / "prompts" / f"{self.dimension_name}.md"
```

### 3.3 Create LLM Prompts

Create prompt files in `evaluation/llm/prompts/`:

- [ ] `evaluation/llm/prompts/accuracy.md`
- [ ] `evaluation/llm/prompts/actionability.md`
- [ ] `evaluation/llm/prompts/false_positive.md`
- [ ] `evaluation/llm/prompts/integration.md`

**Prompt template (with synthetic context placeholders):**
```markdown
# <Dimension> Evaluation

## Context

{{ interpretation_guidance }}

### Synthetic Baseline
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

## Evidence

{{ evidence }}

## Scoring Criteria

[Your criteria here]

## Output Format

Provide JSON with:
- score: 0-100
- reasoning: explanation
- findings: list of specific observations
```

### 3.4 Implement Synthetic Context Pattern

**In primary judge's `collect_evidence()`:**
```python
def collect_evidence(self) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "evaluation_mode": self.evaluation_mode,
        # ... other evidence
    }

    # Always set synthetic context (with fallbacks)
    if self.evaluation_mode == "real_world":
        synthetic_context = self.load_synthetic_evaluation_context()
        if synthetic_context:
            evidence["synthetic_baseline"] = synthetic_context
            evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                synthetic_context
            )
        else:
            evidence["synthetic_baseline"] = "No synthetic baseline available"
            evidence["interpretation_guidance"] = "Evaluate based on ground truth comparison only"
    else:
        evidence["synthetic_baseline"] = "N/A - synthetic mode uses direct ground truth comparison"
        evidence["interpretation_guidance"] = "Strict ground truth evaluation"

    return evidence
```

- [ ] base.py accepts `evaluation_mode` parameter
- [ ] Primary judge sets `synthetic_baseline` key
- [ ] Primary judge sets `interpretation_guidance` key
- [ ] Primary prompt has `{{ evaluation_mode }}` placeholder
- [ ] Primary prompt has `{{ synthetic_baseline }}` placeholder
- [ ] Primary prompt has `{{ interpretation_guidance }}` placeholder

### 3.5 Create scripts/evaluate.py

```python
#!/usr/bin/env python3
"""Programmatic evaluation script."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run programmatic evaluation")
    parser.add_argument("--output-path", required=True, type=Path)
    parser.add_argument("--ground-truth-dir", required=True, type=Path)
    parser.add_argument("--results-dir", required=True, type=Path)
    args = parser.parse_args()

    # Load output
    output = json.loads(args.output_path.read_text())

    # Load ground truth
    gt_file = args.ground_truth_dir / "synthetic.json"
    ground_truth = json.loads(gt_file.read_text())

    # Run checks
    results = run_checks(output, ground_truth)

    # Write results
    args.results_dir.mkdir(parents=True, exist_ok=True)
    (args.results_dir / "checks.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
```

---

## Phase 4: Testing

### 4.1 Configure Test Coverage (High Priority)

The compliance scanner requires minimum **80% test coverage** on `scripts/` directory. This is a **high-severity** check.

#### 4.1.1 Add pytest-cov Dependency

Ensure `requirements.txt` includes:
```
pytest>=7.0.0
pytest-cov>=4.0.0
```

#### 4.1.2 Run Coverage Locally

```bash
# See current coverage with line-by-line detail
pytest tests/ --cov=scripts --cov-report=term-missing

# Generate coverage.json for compliance check
pytest tests/ --cov=scripts --cov-report=json \
  --cov-omit="scripts/checks/*,scripts/evaluate.py,**/conftest.py"

# Generate both JSON and HTML reports
pytest tests/ --cov=scripts --cov-report=json --cov-report=html
```

#### 4.1.3 Configuration

Coverage rules are configured in `src/tool-compliance/rules/common.yaml`:

| Setting | Default | Description |
|---------|---------|-------------|
| Threshold | 80% | Minimum coverage required |
| Source dirs | `["scripts"]` | Directories to measure |
| Omit patterns | `scripts/checks/*`, `scripts/evaluate.py`, `**/conftest.py` | Excluded files |

**Checklist:**
- [ ] pytest-cov>=4.0.0 in requirements.txt
- [ ] Tests achieve >= 80% coverage on scripts/
- [ ] coverage.json generated (or use `--run-coverage` flag during compliance scan)

### 4.2 Create Test Structure

```bash
mkdir -p tests/unit tests/integration
touch tests/__init__.py
touch tests/unit/__init__.py tests/unit/conftest.py
touch tests/integration/__init__.py tests/integration/conftest.py
```

- [ ] `tests/unit/` directory exists
- [ ] `tests/integration/` directory exists
- [ ] Test files use `test_*.py` naming convention

### 4.3 Required Test Patterns

**test_analyze.py:**
```python
"""Tests for analyze.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_analyze_produces_valid_output(tmp_path: Path):
    """Test that analyze produces valid JSON output."""
    # Your test implementation
    pass


def test_analyze_envelope_has_required_fields(tmp_path: Path):
    """Test envelope contains all 8 required metadata fields."""
    pass


def test_analyze_paths_are_repo_relative(tmp_path: Path):
    """Test all paths in output are repo-relative."""
    pass
```

**test_schema.py:**
```python
"""Schema validation tests."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest


def test_output_validates_against_schema():
    """Test output validates against schema."""
    schema_path = Path(__file__).parents[2] / "schemas" / "output.schema.json"
    # Load schema and output, validate
    pass
```

**Checklist:**
- [ ] Test for analyze produces valid output
- [ ] Test for schema validation
- [ ] Test for path normalization
- [ ] `make test` passes
- [ ] Test coverage >= 80% (run `pytest --cov=scripts --cov-report=term`)

---

## Phase 5: SoT Integration (Persistence)

### 5.1 Define Entity Dataclass

Add to `src/sot-engine/persistence/entities.py`:

```python
@dataclass(frozen=True)
class <Tool>Metric:
    """Per-file metric from <tool> analysis."""
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    # tool-specific fields...
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

**Checklist:**
- [ ] `@dataclass(frozen=True)` decorator (entity is immutable)
- [ ] `__post_init__` validation implemented
- [ ] Standard fields: `run_pk`, `file_id`, `directory_id`, `relative_path`

### 5.2 Implement Repository Class

Add to `src/sot-engine/persistence/repositories.py`:

```python
class <Tool>Repository(BaseRepository):
    """Repository for <tool> analysis data."""

    _COLUMNS = (
        "run_pk", "file_id", "directory_id", "relative_path",
        "metric_a", "metric_b",
    )

    def insert_metrics(self, rows: Iterable[<Tool>Metric]) -> None:
        self._insert_bulk(
            "lz_<tool>_metrics",
            self._COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.directory_id, r.relative_path,
                r.metric_a, r.metric_b,
            ),
        )
```

- [ ] Extends `BaseRepository`
- [ ] `_COLUMNS` tuple defined
- [ ] `insert_*` method implemented

### 5.3 Create Adapter

Create `src/sot-engine/persistence/adapters/<tool>_adapter.py`:

```python
"""Adapter for <tool> output persistence."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from .base_adapter import BaseAdapter
from ..entities import <Tool>Metric
from ..repositories import LayoutRepository, <Tool>Repository, ToolRunRepository
from common.path_normalization import is_repo_relative_path, normalize_file_path

# Required module constants
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "<tool>" / "schemas" / "output.schema.json"

LZ_TABLES = {
    "lz_<tool>_metrics": {
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
    "lz_<tool>_metrics": """
        CREATE TABLE IF NOT EXISTS lz_<tool>_metrics (
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


class <Tool>Adapter(BaseAdapter):
    """Adapter for persisting <tool> output to the landing zone."""

    @property
    def tool_name(self) -> str:
        return "<tool>"

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
        tool_repo: <Tool>Repository,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._tool_repo = tool_repo

    def _do_persist(self, payload: dict) -> int:
        """Persist <tool> output to landing zone."""
        metadata = payload.get("metadata") or {}
        data = payload.get("data") or {}

        run_pk = self._create_tool_run(metadata)
        layout_run_pk = self._get_layout_run_pk(metadata["run_id"])

        files = data.get("files", [])
        self.validate_quality(files)

        metrics = list(self._map_file_metrics(run_pk, layout_run_pk, files))
        self._tool_repo.insert_metrics(metrics)

        self._log(f"Persisted {len(metrics)} <tool> metrics")
        return run_pk

    def validate_quality(self, files: Any) -> None:
        """Validate data quality rules."""
        errors = []
        for idx, entry in enumerate(files):
            raw_path = entry.get("path", "")
            normalized = normalize_file_path(raw_path, self._repo_root)
            if not is_repo_relative_path(normalized):
                errors.append(f"file[{idx}] path invalid: {raw_path}")
        self._raise_quality_errors(errors)

    def _map_file_metrics(
        self, run_pk: int, layout_run_pk: int, files: Iterable[dict]
    ) -> Iterable[<Tool>Metric]:
        """Map JSON file entries to entity objects."""
        for entry in files:
            relative_path = self._normalize_path(entry.get("path", ""))
            try:
                file_id, directory_id = self._layout_repo.get_file_record(
                    layout_run_pk, relative_path
                )
            except KeyError:
                self._log(f"WARN: skipping file not in layout: {relative_path}")
                continue

            yield <Tool>Metric(
                run_pk=run_pk,
                file_id=file_id,
                directory_id=directory_id,
                relative_path=relative_path,
                metric_a=entry.get("metric_a"),
                metric_b=entry.get("metric_b"),
            )
```

**Adapter checklist:**
- [ ] `SCHEMA_PATH` points to tool's output.schema.json
- [ ] `LZ_TABLES` defines expected columns and types
- [ ] `QUALITY_RULES` lists validation rules
- [ ] `TABLE_DDL` contains CREATE TABLE statement
- [ ] Adapter extends `BaseAdapter`
- [ ] Implements `_do_persist()`, `validate_quality()`

### 5.4 Add Tables to schema.sql

Add to `src/sot-engine/persistence/schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS lz_<tool>_metrics (
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

- [ ] Table added to schema.sql
- [ ] DDL matches `TABLE_DDL` in adapter

### 5.5 Export Adapter

Add to `src/sot-engine/persistence/adapters/__init__.py`:

```python
from .<tool>_adapter import <Tool>Adapter

__all__ = [
    # ... existing exports
    "<Tool>Adapter",
]
```

- [ ] Adapter imported in `__init__.py`
- [ ] Adapter added to `__all__`

### 5.6 Register in Orchestrator

Add to `src/sot-engine/orchestrator.py`:

```python
from persistence.adapters import <Tool>Adapter
from persistence.repositories import <Tool>Repository

TOOL_INGESTION_CONFIGS = [
    # ... existing configs
    ToolIngestionConfig(
        tool_name="<tool>",
        makefile_dir="src/tools/<tool>",
        adapter_class=<Tool>Adapter,
    ),
]
```

- [ ] Adapter imported in orchestrator.py
- [ ] Tool added to `TOOL_INGESTION_CONFIGS`

---

## Phase 6: dbt Models & Verification

### 6.1 Create Staging Models

Use automation:
```bash
python scripts/generate_dbt_models.py <tool> --table lz_<tool>_metrics --metrics metric_a,metric_b
```

Or create manually in `src/sot-engine/dbt/models/staging/`:

**stg_<tool>_file_metrics.sql:**
```sql
with raw_data as (
    select
        run_pk,
        file_id,
        directory_id,
        relative_path,
        metric_a,
        metric_b
    from {{ source('lz', 'lz_<tool>_metrics') }}
)
select * from raw_data
```

- [ ] Staging model created
- [ ] Source added to `schema.yml`

### 6.2 Create Rollup Models (if applicable)

**Direct rollup (`rollup_<tool>_directory_counts_direct.sql`):**
```sql
with file_metrics as (
    select * from {{ ref('stg_<tool>_file_metrics') }}
)
select
    run_pk,
    directory_id,
    count(*) as file_count,
    sum(metric_a) as total_metric_a
from file_metrics
group by run_pk, directory_id
```

**Recursive rollup (`rollup_<tool>_directory_counts_recursive.sql`):**
```sql
-- Uses path prefix matching for directory subtrees
-- See docs/REFERENCE.md for pattern
```

- [ ] Direct rollup model created
- [ ] Recursive rollup model created

### 6.3 Add Rollup Invariant Test

Create `src/sot-engine/dbt/tests/test_rollup_<tool>_direct_vs_recursive.sql`:

```sql
select
    r.run_pk,
    r.directory_id,
    r.total_metric_a as recursive_count,
    d.total_metric_a as direct_count
from {{ ref('rollup_<tool>_directory_counts_recursive') }} r
join {{ ref('rollup_<tool>_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.total_metric_a < d.total_metric_a
   or r.file_count < d.file_count
```

- [ ] Test returns no rows (invariant holds: recursive >= direct)

### 6.4 Update EVAL_STRATEGY.md

Add `## Rollup Validation` section:

```markdown
---

## Rollup Validation

Rollups:
- directory_direct_counts (metrics for files directly in directory)
- directory_recursive_counts (metrics for all files in subtree)

Tests:
- src/sot-engine/dbt/tests/test_rollup_<tool>_direct_vs_recursive.sql

### Invariants Tested

| Invariant | Description |
|-----------|-------------|
| recursive >= direct | Recursive counts include all descendants |
```

- [ ] EVAL_STRATEGY.md has `## Rollup Validation` section
- [ ] Section has `Rollups:` list
- [ ] Section has `Tests:` list

### 6.5 Run Full Compliance Scan

```bash
# Preflight (fast, ~100ms)
python src/tool-compliance/tool_compliance.py src/tools/<tool> --preflight

# Full scan
python src/tool-compliance/tool_compliance.py src/tools/<tool>
```

- [ ] All preflight checks pass
- [ ] All compliance checks pass

### 6.6 Execute End-to-End Pipeline

```bash
python src/sot-engine/orchestrator.py --repo-path . --commit HEAD --replace
```

- [ ] Orchestrator completes successfully
- [ ] Data appears in landing zone tables
- [ ] dbt models build: `cd src/sot-engine/dbt && dbt run --profiles-dir .`
- [ ] dbt tests pass: `cd src/sot-engine/dbt && dbt test --profiles-dir .`

---

## Quick Reference Commands

### Tool Creation & Setup
```bash
# Create new tool skeleton
python scripts/create-tool.py <name> --sot-integration

# Preview without creating
python scripts/create-tool.py <name> --dry-run
```

### Compliance Scanning
```bash
# Preflight mode (~100ms)
python src/tool-compliance/tool_compliance.py src/tools/<tool> --preflight

# Full compliance scan
python src/tool-compliance/tool_compliance.py src/tools/<tool>

# All tools
make compliance
```

### Testing & Validation
```bash
# Run tool tests
cd src/tools/<tool> && make test

# Validate JSON output
python -c "import json; json.load(open('outputs/<run-id>/output.json'))"

# Validate against schema
python -c "import json, jsonschema; \
  schema=json.load(open('schemas/output.schema.json')); \
  data=json.load(open('outputs/<run-id>/output.json')); \
  jsonschema.validate(data, schema)"

# Check paths are repo-relative
python -c "import json; d=json.load(open('outputs/<run-id>/output.json')); \
  paths=[f['path'] for f in d.get('data',{}).get('files',[])]; \
  invalid=[p for p in paths if p.startswith('/') or p.startswith('./') or '\\\\' in p]; \
  print('Invalid:', invalid) if invalid else print('All paths valid')"
```

### dbt Operations
```bash
# Generate dbt models
python scripts/generate_dbt_models.py <tool> --table lz_<tool>_metrics --metrics col1,col2

# Run dbt models
cd src/sot-engine/dbt && dbt run --profiles-dir .

# Run dbt tests
cd src/sot-engine/dbt && dbt test --profiles-dir .
```

### Full Pipeline
```bash
# End-to-end orchestration
python src/sot-engine/orchestrator.py --repo-path . --commit HEAD --replace

# Ground truth seeding
python scripts/seed_ground_truth.py <tool> <output.json>
```

---

## Common Pitfalls

### Makefile Issues

| Pitfall | Wrong | Correct |
|---------|-------|---------|
| Target naming | `llm-evaluate` | `evaluate-llm` |
| Output directory | `OUTPUT_DIR = output/...` | `OUTPUT_DIR = outputs/...` (plural) |
| Output filename | `$(REPO_NAME).json` | `output.json` |
| Missing common include | (none) | `include ../Makefile.common` |

### Schema Issues

| Pitfall | Wrong | Correct |
|---------|-------|---------|
| Version constraint | `"pattern": "^\\d+\\.\\d+\\.\\d+$"` | `"const": "1.0.0"` |
| Draft version | draft-07, draft-04 | `draft/2020-12/schema` |
| Missing required | `"required": ["tool_name"]` | All 8 metadata fields |

### Path Issues

| Pitfall | Wrong | Correct |
|---------|-------|---------|
| Absolute paths | `/Users/foo/repo/src/main.py` | `src/main.py` |
| Explicit relative | `./src/main.py` | `src/main.py` |
| Parent directory | `../other/file.py` | Not allowed |
| Windows separators | `src\foo\bar.py` | `src/foo/bar.py` |
| Root directory | `/` or empty | `.` |

### Entity & Adapter Issues

| Pitfall | Wrong | Correct |
|---------|-------|---------|
| Entity mutability | `@dataclass` | `@dataclass(frozen=True)` |
| Missing validation | No `__post_init__` | `__post_init__` with validation |
| Missing directory | No `tests/integration/` | Create `tests/integration/` |
| Cross-tool join key | `run_pk` | `collection_run_id` |

### dbt Issues

| Pitfall | Wrong | Correct |
|---------|-------|---------|
| Missing run mapping | Direct `run_pk` join | Use `collection_run_id` mapping |
| Rollup invariant | `recursive < direct` | `recursive >= direct` always |
| Missing source | Use table name directly | Define in `schema.yml` sources |
| Incomplete integration | Infrastructure only | Infrastructure + dbt models + evaluations |

---

## Troubleshooting

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

## Final Verification Checklist

Run through this final checklist before considering the tool complete:

### Phase 1: Structure
- [ ] All 18 required paths exist
- [ ] Makefile has all 6 required targets
- [ ] Makefile includes `../Makefile.common`
- [ ] BLUEPRINT.md and EVAL_STRATEGY.md filled in

### Phase 2: Output
- [ ] analyze.py accepts all 7 required CLI arguments
- [ ] Output uses envelope format with all 8 metadata fields
- [ ] Schema uses draft 2020-12 and `const` for version
- [ ] All paths are repo-relative

### Phase 3: Evaluation
- [ ] Minimum 4 LLM judges implemented
- [ ] Ground truth files created
- [ ] Synthetic context pattern implemented
- [ ] Prompts have required placeholders

### Phase 4: Testing
- [ ] pytest-cov>=4.0.0 in requirements.txt
- [ ] Unit tests in `tests/unit/`
- [ ] Integration tests in `tests/integration/`
- [ ] `make test` passes
- [ ] Test coverage >= 80% on scripts/

### Phase 5: SoT Integration
- [ ] Entity dataclass is frozen with validation
- [ ] Repository class with insert methods
- [ ] Adapter exposes SCHEMA_PATH, LZ_TABLES, QUALITY_RULES, TABLE_DDL
- [ ] Tables added to schema.sql
- [ ] Adapter exported in `__init__.py`
- [ ] Adapter registered in orchestrator.py

### Phase 6: dbt & Verification
- [ ] Staging models created
- [ ] Rollup models created (if applicable)
- [ ] Rollup invariant test added
- [ ] EVAL_STRATEGY.md has Rollup Validation section
- [ ] `python src/tool-compliance/tool_compliance.py src/tools/<tool>` passes
- [ ] Full pipeline executes successfully

---

## Integration Completeness Levels

Not all tool integrations need to be 100% complete. This table defines completeness levels:

| Level | Description | Use Case |
|-------|-------------|----------|
| **Prototype** | Tool runs, produces output | Exploration, feasibility |
| **Functional** | Passes structural + output checks | Development iteration |
| **Integrated** | Infrastructure layer complete | Data collection ready |
| **Complete** | All checks pass | Production ready |

### Prototype (Passes: ~20 checks)
- Directory structure exists
- analyze.py runs and produces JSON
- Output validates against schema

### Functional (Passes: ~30 checks)
- All Prototype checks
- Makefile targets work
- Ground truth files exist
- LLM judges implemented

### Integrated (Passes: ~40 checks)
- All Functional checks
- Entity/Repository/Adapter implemented
- Schema tables defined
- Orchestrator wired

### Complete (Passes: 51 checks)
- All Integrated checks
- dbt staging models
- dbt rollup models + test
- Evaluations run with results
- Adapter integration test passes

### Example: PMD-CPD (2026-02-04)

**Level:** Integrated (37/51 = 73%)

**What worked:** Full infrastructure layer - the tool can be invoked by the orchestrator and data would flow to landing zone tables.

**What's missing:** Data transformation layer (dbt) and evaluation outputs. Without dbt models, data sits in landing zone but cannot be queried through marts. Without evaluation runs, quality cannot be assessed.

**Impact:** Tool is usable for data collection but not for reporting or analysis.

---

## Appendix A: Migrating from Vulcan

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
2. Wrap output in envelope format (see [Phase 2](#phase-2-analysis-script--output))
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

#### pmd-cpd (New Tool)
- Infrastructure (adapter/entity/repository) can be complete while dbt layer is missing
- Compliance scanner catches this gap via `sot.dbt_staging_model` and `dbt.model_coverage` checks
- Running `make evaluate` and `make evaluate-llm` is required even if tool works correctly
- Adapter integration test requires both fixture file AND correct constructor signature

---

## Appendix B: Automation Scripts

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

## References

- [PERSISTENCE.md](./PERSISTENCE.md) - Adapter pattern, entities, repositories
- [COMPLIANCE.md](./COMPLIANCE.md) - Compliance requirements and checks
- [REFERENCE.md](./REFERENCE.md) - Technical specifications (envelope, paths, patterns)
- [EVALUATION.md](./EVALUATION.md) - LLM judge infrastructure
- [templates/BLUEPRINT.md.template](./templates/BLUEPRINT.md.template) - Architecture template
- [templates/EVAL_STRATEGY.md.template](./templates/EVAL_STRATEGY.md.template) - Evaluation template
