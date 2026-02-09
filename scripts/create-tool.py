#!/usr/bin/env python3
"""Tool generator for Project Caldera.

Creates a compliant tool directory structure with all required files.
Generated tools pass preflight compliance checks immediately.

Usage:
    python scripts/create-tool.py my-new-tool
    python scripts/create-tool.py my-new-tool --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "src" / "tools"


def get_makefile_template(tool_name: str) -> str:
    """Generate Makefile content."""
    tool_name_underscored = tool_name.replace("-", "_")
    return f'''# {tool_name} - Analysis Tool
# Caldera-compliant Makefile
#
# Quick start:
#   make setup        - Install dependencies
#   make analyze      - Run analysis
#   make evaluate     - Run programmatic evaluation
#   make evaluate-llm - Run LLM evaluation
#   make test         - Run all tests
#   make clean        - Remove generated files

SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help setup analyze evaluate evaluate-llm test test-quick clean clean-all

# Include shared configuration (provides VENV, RUN_ID, REPO_ID, OUTPUT_DIR, etc.)
include ../Makefile.common

# Tool-specific defaults
REPO_PATH ?= eval-repos/synthetic
REPO_NAME ?= synthetic
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000")

help:  ## Show this help message
	@echo "{tool_name} - Analysis Tool"
	@echo ""
	@echo "Usage: make <target> [REPO_PATH=<path>] [REPO_NAME=<name>]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {{FS = ":.*?## "}}; {{printf "  %-20s %s\\n", $$1, $$2}}'

# ============================================
# Setup targets
# ============================================

setup: $(VENV_READY)  ## Set up virtual environment
	@echo "Setup complete"

# ============================================
# Analysis targets
# ============================================

analyze: $(VENV_READY)  ## Run analysis on a repository
	@mkdir -p $(OUTPUT_DIR)
	@echo "Analyzing $(REPO_PATH) as project '$(REPO_NAME)'"
	$(PYTHON_VENV) -m scripts.analyze \\
		--repo-path $(REPO_PATH) \\
		--repo-name $(REPO_NAME) \\
		--output-dir $(OUTPUT_DIR) \\
		--run-id $(RUN_ID) \\
		--repo-id $(REPO_ID) \\
		--branch $(BRANCH) \\
		--commit $(COMMIT)

# ============================================
# Evaluation targets
# ============================================

evaluate: $(VENV_READY)  ## Run programmatic evaluation
	@mkdir -p $(EVAL_OUTPUT_DIR)
	$(PYTHON_VENV) -m scripts.evaluate \\
		--results-dir $(OUTPUT_DIR) \\
		--ground-truth-dir evaluation/ground-truth \\
		--output $(EVAL_OUTPUT_DIR)/evaluation_report.json
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/evaluation_report.json"

evaluate-llm: $(VENV_READY)  ## Run LLM evaluation
	@mkdir -p $(EVAL_OUTPUT_DIR)
	@mkdir -p evaluation/results
	$(PYTHON_VENV) -m evaluation.llm.orchestrator \\
		$(OUTPUT_DIR) \\
		--output $(EVAL_OUTPUT_DIR)/llm_evaluation.json \\
		--model $(LLM_MODEL)
	@if [ -w evaluation/results ]; then cp $(EVAL_OUTPUT_DIR)/llm_evaluation.json evaluation/results/llm_evaluation.json; fi
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/llm_evaluation.json"

# ============================================
# Test targets
# ============================================

test: _common-test  ## Run all tests

test-quick: _common-test-quick  ## Run quick tests (stop on first failure)

# ============================================
# Cleanup targets
# ============================================

clean: _common-clean  ## Clean build artifacts

clean-all: _common-clean-all  ## Clean all including venv
'''


def get_requirements_template() -> str:
    """Generate requirements.txt content."""
    return '''# Python dependencies for this tool
pytest>=7.0.0
jsonschema>=4.0.0
'''


def get_analyze_template(tool_name: str) -> str:
    """Generate scripts/analyze.py content."""
    tool_name_underscored = tool_name.replace("-", "_")
    return f'''"""Main analysis script for {tool_name}.

This script follows the Caldera tool envelope format and produces output
conforming to schemas/output.schema.json.

For implementation examples, see:
- src/tools/scc/scripts/analyze.py - File metrics (lines, complexity)
- src/tools/lizard/scripts/analyze.py - Function-level analysis
- src/tools/semgrep/scripts/analyze.py - Code smell detection

Documentation:
- docs/DEVELOPMENT.md - Step-by-step tutorial for implementing tools
- docs/TOOL_REQUIREMENTS.md - Output format requirements
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add shared src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

TOOL_NAME = "{tool_name}"
TOOL_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"


def compute_content_hash(repo_path: Path) -> str:
    """Compute a deterministic hash for non-git repos."""
    sha1 = hashlib.sha1()
    for path in sorted(repo_path.rglob("*")):
        if path.is_file() and ".git" not in path.parts:
            sha1.update(path.relative_to(repo_path).as_posix().encode())
            sha1.update(b"\\0")
            try:
                sha1.update(path.read_bytes())
            except OSError:
                continue
    return sha1.hexdigest()


def resolve_commit(repo_path: Path, commit_arg: str | None) -> str:
    """Resolve commit SHA, falling back to content hash."""
    if commit_arg and len(commit_arg) == 40:
        return commit_arg
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return compute_content_hash(repo_path)


def analyze_repo(repo_path: Path) -> dict:
    """Run analysis on the repository.

    TODO: Implement your analysis logic here.

    Steps to implement:
    1. Decide what metrics your tool collects (per-file, per-function, repo-level)
    2. Call your underlying tool (subprocess) or implement analysis directly
    3. Normalize all file paths to be repo-relative (use common.path_normalization)
    4. Structure results to match your schemas/output.schema.json

    Example - calling an external tool (like scc does):
        result = subprocess.run(
            ["my-tool", "--json", str(repo_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        raw_output = json.loads(result.stdout)

    Example - implementing analysis directly (like layout-scanner does):
        for path in repo_path.rglob("*"):
            if path.is_file():
                # Analyze each file...

    Path normalization (REQUIRED - see docs/TOOL_REQUIREMENTS.md):
        from shared.path_utils import normalize_file_path
        relative_path = normalize_file_path(absolute_path, repo_path)
    """
    # Import path normalization utilities (uncomment when implementing)
    # from shared.path_utils import normalize_file_path, normalize_dir_path

    files = []
    for path in sorted(repo_path.rglob("*")):
        if path.is_file() and ".git" not in path.parts:
            # IMPORTANT: All paths must be repo-relative
            # Valid: "src/main.py"
            # Invalid: "/Users/foo/repo/src/main.py", "./src/main.py"
            relative_path = path.relative_to(repo_path).as_posix()
            files.append({{
                "path": relative_path,
                "size_bytes": path.stat().st_size,
                # TODO: Add tool-specific metrics. Examples:
                # For code metrics: "lines", "code", "comment", "blank", "complexity"
                # For smell detection: "rule_id", "severity", "message", "line_start"
                # For function analysis: "function_name", "ccn", "nloc", "params"
            }})

    return {{
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "files": files,
        "summary": {{
            "file_count": len(files),
            "total_bytes": sum(f["size_bytes"] for f in files),
            # TODO: Add summary statistics. Examples:
            # "total_lines": ..., "avg_complexity": ..., "smell_count": ...
        }},
    }}


def main() -> int:
    parser = argparse.ArgumentParser(description=f"{{TOOL_NAME}} analysis tool")
    parser.add_argument("--repo-path", required=True, type=Path)
    parser.add_argument("--repo-name", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--commit", default=None)
    args = parser.parse_args()

    repo_path = args.repo_path.resolve()
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {{repo_path}}", file=sys.stderr)
        return 1

    # Resolve commit
    commit = resolve_commit(repo_path, args.commit)

    # Run analysis
    data = analyze_repo(repo_path)

    # Create envelope
    envelope = {{
        "metadata": {{
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "run_id": args.run_id,
            "repo_id": args.repo_id,
            "branch": args.branch,
            "commit": commit,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "schema_version": SCHEMA_VERSION,
        }},
        "data": data,
    }}

    # Write output
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "output.json"
    output_path.write_text(json.dumps(envelope, indent=2))

    print(f"Analysis complete. Output: {{output_path}}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def get_evaluate_template(tool_name: str) -> str:
    """Generate scripts/evaluate.py content."""
    return f'''"""Programmatic evaluation script for {tool_name}."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any


def load_checks() -> list[tuple[str, Any]]:
    """Load all check modules from scripts/checks/."""
    checks_dir = Path(__file__).parent / "checks"
    check_modules = []

    for check_file in sorted(checks_dir.glob("*.py")):
        if check_file.name.startswith("_"):
            continue
        module_name = f"scripts.checks.{{check_file.stem}}"
        try:
            module = importlib.import_module(module_name)
            check_modules.append((check_file.stem, module))
        except ImportError as e:
            print(f"Warning: Could not load {{module_name}}: {{e}}", file=sys.stderr)

    return check_modules


def run_checks(output: dict, ground_truth: dict | None) -> list[dict]:
    """Run all checks and collect results."""
    results = []
    check_modules = load_checks()

    for name, module in check_modules:
        # Find all check_* functions in the module
        for attr_name in dir(module):
            if not attr_name.startswith("check_"):
                continue
            check_fn = getattr(module, attr_name)
            if not callable(check_fn):
                continue

            try:
                result = check_fn(output, ground_truth)
                if isinstance(result, dict):
                    results.append(result)
                elif isinstance(result, list):
                    results.extend(result)
            except Exception as e:
                results.append({{
                    "check_id": f"{{name}}.{{attr_name}}",
                    "status": "error",
                    "message": str(e),
                }})

    return results


def compute_summary(results: list[dict]) -> dict:
    """Compute summary statistics from check results."""
    total = len(results)
    passed = sum(1 for r in results if r.get("status") == "pass")
    failed = sum(1 for r in results if r.get("status") == "fail")
    warned = sum(1 for r in results if r.get("status") == "warn")
    errored = sum(1 for r in results if r.get("status") == "error")

    score = passed / total if total > 0 else 0.0

    return {{
        "total": total,
        "passed": passed,
        "failed": failed,
        "warned": warned,
        "errored": errored,
        "score": round(score, 4),
        "decision": "PASS" if failed == 0 and errored == 0 else "FAIL",
    }}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run programmatic evaluation")
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--ground-truth-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    # Load analysis output
    output_path = args.results_dir / "output.json"
    if not output_path.exists():
        # Try finding in subdirectories
        candidates = list(args.results_dir.glob("*/output.json"))
        if candidates:
            output_path = max(candidates, key=lambda p: p.stat().st_mtime)
        else:
            print(f"Error: No output.json found in {{args.results_dir}}", file=sys.stderr)
            return 1

    output = json.loads(output_path.read_text())

    # Load ground truth if available
    ground_truth = None
    gt_path = args.ground_truth_dir / "synthetic.json"
    if gt_path.exists():
        ground_truth = json.loads(gt_path.read_text())

    # Run checks
    results = run_checks(output, ground_truth)
    summary = compute_summary(results)

    # Write report
    report = {{
        "summary": summary,
        "checks": results,
    }}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))

    print(f"Evaluation complete. Decision: {{summary['decision']}}")
    print(f"Score: {{summary['score']:.1%}} ({{summary['passed']}}/{{summary['total']}} passed)")

    return 0 if summary["decision"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
'''


def get_checks_init_template() -> str:
    """Generate scripts/checks/__init__.py content."""
    return '''"""Check modules for programmatic evaluation."""

from __future__ import annotations
'''


def get_accuracy_check_template(tool_name: str) -> str:
    """Generate scripts/checks/accuracy.py content."""
    return f'''"""Accuracy checks for {tool_name}.

This module contains programmatic evaluation checks for accuracy.
Each check_* function receives the tool output and ground truth,
and returns a dict with check_id, status, and message.

For implementation examples, see:
- src/tools/scc/scripts/checks/per_file.py - Per-file metric validation
- src/tools/lizard/scripts/checks/accuracy.py - Function detection accuracy
- src/tools/semgrep/scripts/checks/accuracy.py - Smell detection precision/recall

Documentation:
- docs/TOOL_REQUIREMENTS.md - Check format requirements
- Your EVAL_STRATEGY.md - Defines which checks to implement
"""

from __future__ import annotations


def check_file_count_accuracy(output: dict, ground_truth: dict | None) -> dict:
    """Check if file count matches ground truth.

    This is a basic example check. You should implement checks specific
    to your tool's metrics and accuracy requirements.
    """
    if ground_truth is None:
        return {{
            "check_id": "accuracy.file_count",
            "status": "pass",
            "message": "No ground truth available (skipped)",
        }}

    data = output.get("data", {{}})
    actual_count = len(data.get("files", []))
    expected_count = ground_truth.get("expected_file_count", 0)

    if actual_count == expected_count:
        return {{
            "check_id": "accuracy.file_count",
            "status": "pass",
            "message": f"File count matches: {{actual_count}}",
        }}
    else:
        return {{
            "check_id": "accuracy.file_count",
            "status": "fail",
            "message": f"File count mismatch: expected {{expected_count}}, got {{actual_count}}",
        }}


# TODO: Add your tool-specific accuracy checks below.
#
# Example check patterns:
#
# def check_metric_precision(output: dict, ground_truth: dict | None) -> dict:
#     """Check precision of detected metrics against ground truth."""
#     # Precision = true_positives / (true_positives + false_positives)
#     ...
#
# def check_metric_recall(output: dict, ground_truth: dict | None) -> dict:
#     """Check recall of detected metrics against ground truth."""
#     # Recall = true_positives / (true_positives + false_negatives)
#     ...
#
# def check_threshold_compliance(output: dict, ground_truth: dict | None) -> dict:
#     """Check that metrics meet minimum thresholds defined in ground truth."""
#     ...
'''


def get_coverage_check_template(tool_name: str) -> str:
    """Generate scripts/checks/coverage.py content."""
    return f'''"""Coverage checks for {tool_name}."""

from __future__ import annotations


def check_all_files_analyzed(output: dict, ground_truth: dict | None) -> dict:
    """Check that all expected files were analyzed."""
    data = output.get("data", {{}})
    files = data.get("files", [])

    if not files:
        return {{
            "check_id": "coverage.files_analyzed",
            "status": "warn",
            "message": "No files in output",
        }}

    return {{
        "check_id": "coverage.files_analyzed",
        "status": "pass",
        "message": f"{{len(files)}} files analyzed",
    }}
'''


def get_performance_check_template(tool_name: str) -> str:
    """Generate scripts/checks/performance.py content."""
    return f'''"""Performance checks for {tool_name}."""

from __future__ import annotations


def check_execution_time(output: dict, ground_truth: dict | None) -> dict:
    """Check if execution completed in reasonable time."""
    # TODO: Implement timing measurement
    return {{
        "check_id": "performance.execution_time",
        "status": "pass",
        "message": "Execution time check not implemented",
    }}
'''


def get_schema_template(tool_name: str) -> str:
    """Generate schemas/output.schema.json content.

    The schema defines the contract for tool output. It must:
    1. Use JSON Schema draft 2020-12
    2. Require metadata + data top-level objects
    3. Require all 8 metadata fields
    4. Use 'const' for schema_version (not 'pattern')

    For examples, see:
    - src/tools/scc/schemas/output.schema.json - File metrics
    - src/tools/semgrep/schemas/output.schema.json - Code smells
    """
    # Build schema with clear structure and comments for customization
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": f"{tool_name} Output",
        "description": f"Output schema for {tool_name} analysis tool. "
                       "Customize the data.files.items section for your tool's metrics.",
        "type": "object",
        "required": ["metadata", "data"],
        "properties": {
            "metadata": {
                "type": "object",
                "description": "Standard Caldera envelope metadata (DO NOT MODIFY)",
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
                    "tool_name": {"type": "string"},
                    "tool_version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
                    "run_id": {"type": "string", "format": "uuid"},
                    "repo_id": {"type": "string", "format": "uuid"},
                    "branch": {"type": "string"},
                    "commit": {"type": "string", "pattern": "^[0-9a-fA-F]{40}$"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "schema_version": {"const": "1.0.0"}
                }
            },
            "data": {
                "type": "object",
                "description": "Tool-specific analysis data. Customize properties below.",
                "required": ["tool", "files"],
                "properties": {
                    "tool": {"type": "string"},
                    "tool_version": {"type": "string"},
                    "files": {
                        "type": "array",
                        "description": "Per-file analysis results. Add your metrics to items.properties.",
                        "items": {
                            "type": "object",
                            "required": ["path"],
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Repo-relative path (e.g., 'src/main.py', NOT '/abs/path')"
                                },
                                "size_bytes": {"type": "integer", "minimum": 0}
                                # TODO: Add your tool-specific file properties here
                                # Examples:
                                # "lines": {"type": "integer", "minimum": 0},
                                # "complexity": {"type": "integer", "minimum": 0},
                                # "smells": {"type": "array", "items": {...}}
                            }
                        }
                    },
                    "summary": {
                        "type": "object",
                        "description": "Aggregate statistics. Add summary metrics here.",
                        "properties": {
                            "file_count": {"type": "integer", "minimum": 0},
                            "total_bytes": {"type": "integer", "minimum": 0}
                            # TODO: Add your tool-specific summary properties here
                            # Examples:
                            # "total_lines": {"type": "integer"},
                            # "avg_complexity": {"type": "number"},
                            # "smell_count": {"type": "integer"}
                        }
                    }
                }
            }
        }
    }
    return json.dumps(schema, indent=2)


def get_readme_template(tool_name: str) -> str:
    """Generate README.md content."""
    return f'''# {tool_name}

> Brief description of what this tool does.

## Quick Start

```bash
# Setup
make setup

# Run analysis
make analyze REPO_PATH=/path/to/repo

# Run evaluation
make evaluate
```

## Output

Analysis produces `outputs/<run-id>/output.json` with:

```json
{{
  "metadata": {{ ... }},
  "data": {{
    "files": [...],
    "summary": {{ ... }}
  }}
}}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| REPO_PATH | eval-repos/synthetic | Repository to analyze |
| OUTPUT_DIR | outputs/$(RUN_ID) | Output directory |

## Development

```bash
# Run tests
make test

# Run quick tests (stop on first failure)
make test-quick

# Clean outputs
make clean
```
'''


def get_blueprint_template(tool_name: str) -> str:
    """Generate BLUEPRINT.md content."""
    return f'''# {tool_name} - Architecture Blueprint

> Brief description of what this tool analyzes.

<!--
Template instructions (delete this section when done):
- Review docs/templates/BLUEPRINT.md.template for full guidance
- See src/tools/scc/BLUEPRINT.md for a complete example
- Run `make compliance` to verify all required sections are present
-->

## Executive Summary

[TODO: Describe what the tool analyzes, key metrics, and why it was selected for Caldera]

**Example** (from scc):
> scc provides fast, accurate source code counting with per-file metrics including
> lines of code, comments, blanks, and cyclomatic complexity estimates.

## Gap Analysis

### Current State

| Aspect | Status |
|--------|--------|
| Tool maturity | [alpha/beta/stable] |
| Output format | JSON |
| Language support | [All/Specific languages] |
| Performance | [Fast/Moderate/Slow] |

### Integration Gaps

| Gap | Impact | Resolution |
|-----|--------|------------|
| [TODO: Identify gaps] | [Impact level] | [Resolution plan] |

## Architecture

### Data Flow

```
Repository
    |
    v
+-------------+
| analyze.py  |  Parse, normalize, wrap in envelope
+-------------+
    |
    v
+-------------+
| output.json |  Caldera envelope format
+-------------+
    |
    v
+-------------+
| SoT Adapter |  Persist to landing zone
+-------------+
```

### Output Schema

See `schemas/output.schema.json` for complete schema.

Key data structures:
- `files[]`: Per-file metrics (path, [TODO: your metrics])
- `summary`: Aggregate statistics

## Implementation Plan

### Phase 1: Standalone Tool

- [x] Create directory structure (done by create-tool.py)
- [ ] Implement analyze.py with envelope output
- [ ] Customize output.schema.json for tool metrics
- [ ] Add test files to eval-repos/synthetic/
- [ ] Implement programmatic checks in scripts/checks/
- [ ] Pass compliance scanner: `make compliance`

### Phase 2: SoT Integration

- [ ] Create entity dataclass in persistence/entities.py
- [ ] Create repository class in persistence/repositories.py
- [ ] Create adapter in persistence/adapters/
- [ ] Add dbt staging models

### Phase 3: Evaluation

- [ ] Create ground truth in evaluation/ground-truth/
- [ ] Implement LLM judges in evaluation/llm/judges/
- [ ] Generate and review scorecard

## Configuration Reference

### Makefile Variables

| Variable | Default | Description |
|----------|---------|-------------|
| REPO_PATH | `eval-repos/synthetic` | Repository to analyze |
| OUTPUT_DIR | `outputs/$(RUN_ID)` | Output directory |
| [TODO: Add tool-specific variables] | | |

## Performance Characteristics

[TODO: Add benchmarks after implementation]

Target performance:
- 10K files: < 60 seconds
- 100K files: < 10 minutes

## Evaluation Results

See [evaluation/scorecard.md](./evaluation/scorecard.md) for results.

## Risk Assessment

### Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| [TODO: Document limitations] | [Impact] | [Mitigation] |
'''


def get_eval_strategy_template(tool_name: str) -> str:
    """Generate EVAL_STRATEGY.md content."""
    return f'''# {tool_name} - Evaluation Strategy

> How we measure the quality and accuracy of this tool's output.

<!--
Template instructions (delete this section when done):
- Review docs/templates/EVAL_STRATEGY.md.template for full guidance
- See src/tools/scc/EVAL_STRATEGY.md for a complete example
- The Rollup Validation section is REQUIRED for compliance
-->

## Philosophy & Approach

[TODO: Describe what "correct" means for this tool]

**Example approaches:**
- **Metric accuracy**: Comparing detected metrics against manually verified values
- **Detection coverage**: Ensuring all relevant files/functions are analyzed
- **Precision/Recall**: For tools that detect issues (smells, vulnerabilities)

## Dimension Summary

| Dimension | Weight | Method | Target |
|-----------|--------|--------|--------|
| Accuracy | 40% | Programmatic + LLM | >95% |
| Coverage | 30% | Programmatic | >90% |
| Performance | 15% | Programmatic | <60s/10K files |
| Actionability | 15% | LLM | >80% |

[TODO: Adjust weights and targets based on your tool's priorities]

## Check Catalog

### Programmatic Checks

Located in `scripts/checks/`:

| Check Module | Dimension | Description |
|--------------|-----------|-------------|
| `accuracy.py` | Accuracy | Compare output against ground truth |
| `coverage.py` | Coverage | Verify all files are analyzed |
| `performance.py` | Performance | Measure execution time |

[TODO: Add your tool-specific checks]

### LLM Judges

Located in `evaluation/llm/judges/`:

| Judge | Dimension | Evaluates |
|-------|-----------|-----------|
| `accuracy.py` | Accuracy | Do findings match expected results? |
| `actionability.py` | Actionability | Are findings useful for developers? |
| `false_positive_rate.py` | Precision | Are findings actual issues? |
| `integration_fit.py` | Integration | Does output fit SoT schema? |

[TODO: Implement 4 standard judges - see docs/TOOL_REQUIREMENTS.md]

## Scoring Methodology

### Aggregate Score Calculation

```
total_score = (
    accuracy_score * 0.40 +
    coverage_score * 0.30 +
    performance_score * 0.15 +
    actionability_score * 0.15
)
```

### Per-Check Scoring

- `pass`: 100 points
- `warn`: 50 points
- `fail`: 0 points

## Decision Thresholds

| Dimension | Pass | Warn | Fail |
|-----------|------|------|------|
| Accuracy | >=95% | 85-95% | <85% |
| Coverage | >=90% | 80-90% | <80% |
| Performance | <60s | 60-120s | >120s |
| Actionability | >=80% | 60-80% | <60% |

## Ground Truth Specifications

### Synthetic Repositories

Located in `eval-repos/synthetic/`:

| Repo | Purpose | Key Scenarios |
|------|---------|---------------|
| [TODO] | Basic functionality | Happy path, simple inputs |
| [TODO] | Edge cases | Empty files, large files, special chars |
| [TODO] | Language coverage | One file per supported language |

### Ground Truth Format

See `evaluation/ground-truth/synthetic.json`.

**Tip:** After running analysis, use `make seed-ground-truth` to auto-populate
expected values from actual output.

---

## Rollup Validation

Rollups: (none - file-level tool with no directory aggregations)

Tests:
- src/tools/{tool_name}/tests/unit/test_analyze.py

<!--
NOTE: If your tool produces directory-level rollups, update this section:

Rollups:
- directory_direct_distributions
- directory_recursive_distributions

Tests:
- src/sot-engine/dbt/tests/test_rollup_{tool_name}_invariants.sql
-->
'''


def get_orchestrator_template(tool_name: str) -> str:
    """Generate evaluation/llm/orchestrator.py content."""
    return f'''"""LLM evaluation orchestrator for {tool_name}."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run LLM evaluation")
    parser.add_argument("results_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()

    # TODO: Implement LLM evaluation
    # For now, return a placeholder result

    result = {{
        "summary": {{
            "verdict": "PASS",
            "score": 0.85,
        }},
        "judges": [],
    }}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2))

    print(f"LLM evaluation complete. Verdict: {{result['summary']['verdict']}}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def get_judges_init_template() -> str:
    """Generate evaluation/llm/judges/__init__.py content."""
    return '''"""LLM judges for evaluation."""

from __future__ import annotations
'''


def get_base_judge_template(tool_name: str) -> str:
    """Generate evaluation/llm/judges/base.py content."""
    return f'''"""Base judge class for {tool_name}."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseJudge(ABC):
    """Base class for LLM judges."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Judge name."""
        ...

    @property
    @abstractmethod
    def dimension(self) -> str:
        """Evaluation dimension."""
        ...

    @abstractmethod
    def evaluate(self, output: dict, context: dict) -> dict:
        """Evaluate the output.

        Returns:
            dict with keys: score (0-1), verdict (PASS/FAIL), reasoning
        """
        ...
'''


def get_prompt_template(tool_name: str, prompt_name: str) -> str:
    """Generate evaluation/llm/prompts/<prompt>.md content."""
    return f'''# {prompt_name.replace("_", " ").title()} Evaluation

## Task

Evaluate the {tool_name} output for {prompt_name.replace("_", " ")}.

## Input

You will receive:
1. The tool's JSON output
2. Repository context

## Evaluation Criteria

Rate on a scale of 1-5:
- 5: Excellent
- 4: Good
- 3: Acceptable
- 2: Poor
- 1: Unacceptable

## Output Format

Respond with:
```json
{{
  "score": <1-5>,
  "verdict": "PASS" | "FAIL",
  "reasoning": "<explanation>"
}}
```
'''


def get_ground_truth_template() -> str:
    """Generate evaluation/ground-truth/synthetic.json content."""
    ground_truth = {
        "_comment": "Ground truth for evaluation. See docs/TOOL_REQUIREMENTS.md for format.",
        "repo_name": "synthetic",
        "expected_file_count": 0,
        "files": {
            "_example_file.py": {
                "_comment": "Add expected metrics for each file here",
                "expected_lines": 100,
                "expected_complexity": 5
            }
        },
        "tolerance": {
            "_comment": "Define acceptable variance for metric comparisons",
            "line_count": 0.05,
            "complexity": 0.10
        },
        "_instructions": [
            "1. Create test files in eval-repos/synthetic/",
            "2. Run 'make analyze' to get actual output",
            "3. Review output.json and add expected values here",
            "4. Tip: Use 'make seed-ground-truth' after analysis to auto-populate"
        ]
    }
    return json.dumps(ground_truth, indent=2)


def get_scorecard_template(tool_name: str) -> str:
    """Generate evaluation/scorecard.md content."""
    return f'''# {tool_name} Evaluation Scorecard

*Run `make evaluate` to generate evaluation results.*

## Summary

| Dimension | Score | Status |
|-----------|-------|--------|
| Accuracy | - | - |
| Coverage | - | - |
| Performance | - | - |
| Actionability | - | - |

**Overall: PENDING**

## Details

Run evaluation to populate results.
'''


def get_test_analyze_template(tool_name: str) -> str:
    """Generate tests/unit/test_analyze.py content."""
    return f'''"""Unit tests for {tool_name} analyze script.

For implementation examples, see:
- src/tools/scc/tests/unit/test_analyze.py
- src/tools/lizard/tests/unit/test_analyze.py
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pytest


# Fixture: sample analysis output
@pytest.fixture
def sample_output() -> dict:
    """Load a sample output.json for testing.

    TODO: Replace with actual output from your tool.
    Option 1: Load from evaluation/results/output.json
    Option 2: Create minimal valid output inline
    """
    return {{
        "metadata": {{
            "tool_name": "{tool_name}",
            "tool_version": "1.0.0",
            "run_id": "test-run-id",
            "repo_id": "test-repo-id",
            "branch": "main",
            "commit": "a" * 40,
            "timestamp": "2025-01-01T00:00:00Z",
            "schema_version": "1.0.0",
        }},
        "data": {{
            "tool": "{tool_name}",
            "tool_version": "1.0.0",
            "files": [
                {{"path": "src/main.py", "size_bytes": 100}},
            ],
            "summary": {{
                "file_count": 1,
                "total_bytes": 100,
            }},
        }},
    }}


def test_analyze_output_structure(sample_output: dict):
    """Test that analyze produces valid output structure."""
    # Verify top-level structure
    assert "metadata" in sample_output
    assert "data" in sample_output

    # Verify data structure
    data = sample_output["data"]
    assert "tool" in data
    assert "files" in data
    assert isinstance(data["files"], list)


def test_analyze_metadata_fields(sample_output: dict):
    """Test that all required metadata fields are present."""
    required_fields = [
        "tool_name", "tool_version", "run_id", "repo_id",
        "branch", "commit", "timestamp", "schema_version"
    ]
    metadata = sample_output["metadata"]

    for field in required_fields:
        assert field in metadata, f"Missing required field: {{field}}"
        assert metadata[field], f"Field is empty: {{field}}"


def test_path_normalization(sample_output: dict):
    """Test that all paths are repo-relative.

    Paths MUST be repo-relative (no leading /, ./, or ..)
    See docs/TOOL_REQUIREMENTS.md for path requirements.
    """
    data = sample_output["data"]

    for file_entry in data.get("files", []):
        path = file_entry.get("path", "")
        # Must not be absolute
        assert not path.startswith("/"), f"Absolute path found: {{path}}"
        # Must not have ./ prefix
        assert not path.startswith("./"), f"Path has ./ prefix: {{path}}"
        # Must not contain .. segments
        assert ".." not in path.split("/"), f"Path has .. segment: {{path}}"
        # Must use forward slashes
        assert "\\\\" not in path, f"Path has backslash: {{path}}"


# TODO: Add tool-specific tests below
#
# def test_metric_values_in_range(sample_output: dict):
#     """Test that metric values are within expected ranges."""
#     ...
#
# def test_schema_validation():
#     """Test that output validates against schemas/output.schema.json."""
#     import jsonschema
#     schema_path = Path(__file__).parents[2] / "schemas" / "output.schema.json"
#     schema = json.loads(schema_path.read_text())
#     jsonschema.validate(sample_output, schema)
'''


def get_test_evaluate_template(tool_name: str) -> str:
    """Generate tests/unit/test_evaluate.py content."""
    return f'''"""Unit tests for {tool_name} evaluate script."""

from __future__ import annotations

import pytest


def test_check_loading():
    """Test that check modules load correctly."""
    from scripts.evaluate import load_checks
    checks = load_checks()
    assert len(checks) > 0


def test_summary_computation():
    """Test summary statistics computation."""
    from scripts.evaluate import compute_summary

    results = [
        {{"check_id": "test.a", "status": "pass"}},
        {{"check_id": "test.b", "status": "fail"}},
    ]
    summary = compute_summary(results)
    assert summary["total"] == 2
    assert summary["passed"] == 1
    assert summary["failed"] == 1
'''


def get_conftest_template() -> str:
    """Generate tests/conftest.py content."""
    return '''"""Pytest configuration for tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))
'''


def get_integration_test_template(tool_name: str) -> str:
    """Generate tests/integration/test_e2e.py content."""
    return f'''"""End-to-end integration tests for {tool_name}.

Integration tests verify the complete pipeline works:
1. analyze.py produces valid output
2. evaluate.py scores the output
3. Output matches schema

For examples, see:
- src/tools/scc/tests/integration/test_e2e.py
- src/tools/git-sizer/tests/integration/test_e2e.py
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tool_root() -> Path:
    """Return the tool root directory."""
    return Path(__file__).parents[2]


@pytest.fixture
def synthetic_repo(tool_root: Path) -> Path:
    """Return the synthetic test repository path."""
    return tool_root / "eval-repos" / "synthetic"


def test_full_pipeline(tool_root: Path, synthetic_repo: Path):
    """Test complete analysis and evaluation pipeline.

    This test runs:
    1. make analyze on synthetic repo
    2. Verifies output.json is created
    3. Verifies output validates against schema

    TODO: Implement once analyze.py is complete
    """
    # Skip if synthetic repo is empty
    if not synthetic_repo.exists() or not any(synthetic_repo.iterdir()):
        pytest.skip("Synthetic repo is empty - add test files first")

    # Create temp output directory
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Run analysis
        env = os.environ.copy()
        env.update({{
            "REPO_PATH": str(synthetic_repo),
            "REPO_NAME": "synthetic",
            "OUTPUT_DIR": str(output_dir),
            "RUN_ID": "test-integration",
            "REPO_ID": "test-repo",
            "BRANCH": "main",
            "SKIP_SETUP": "1",
        }})

        # Run make analyze
        result = subprocess.run(
            ["make", "analyze"],
            cwd=tool_root,
            env=env,
            capture_output=True,
            text=True,
        )

        # Check analysis succeeded
        assert result.returncode == 0, f"make analyze failed: {{result.stderr}}"

        # Check output file was created
        output_path = output_dir / "output.json"
        assert output_path.exists(), "output.json not created"

        # Load and validate structure
        output = json.loads(output_path.read_text())
        assert "metadata" in output
        assert "data" in output
        assert output["metadata"]["tool_name"] == "{tool_name}"


def test_schema_validation(tool_root: Path):
    """Test that existing output validates against schema.

    Loads the most recent output and validates it against the schema.
    """
    # Find most recent output
    outputs_dir = tool_root / "outputs"
    if not outputs_dir.exists():
        pytest.skip("No outputs directory - run make analyze first")

    output_dirs = sorted(
        [d for d in outputs_dir.iterdir() if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    if not output_dirs:
        pytest.skip("No output directories found")

    output_path = output_dirs[0] / "output.json"
    if not output_path.exists():
        pytest.skip("No output.json in latest output directory")

    # Load schema
    schema_path = tool_root / "schemas" / "output.schema.json"
    assert schema_path.exists(), "Schema file missing"

    # Validate
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed")

    schema = json.loads(schema_path.read_text())
    output = json.loads(output_path.read_text())
    jsonschema.validate(output, schema)
'''


# =============================================================================
# SoT Integration Templates
# =============================================================================


def get_sot_adapter_template(tool_name: str) -> str:
    """Generate SoT adapter class template."""
    class_name = "".join(word.capitalize() for word in tool_name.replace("-", "_").split("_"))
    tool_underscored = tool_name.replace("-", "_")
    return f'''"""Adapter for persisting {tool_name} output to the landing zone.

For implementation examples, see:
- persistence/adapters/scc_adapter.py - File metrics adapter
- persistence/adapters/semgrep_adapter.py - Code smell adapter

Documentation:
- docs/TOOL_REQUIREMENTS.md - Adapter requirements
- docs/DEVELOPMENT.md - Integration tutorial
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from .base_adapter import BaseAdapter
from ..entities import {class_name}FileMetric
from ..repositories import LayoutRepository, {class_name}Repository, ToolRunRepository
from shared.path_utils import is_repo_relative_path, normalize_file_path
from ..validation import (
    check_non_negative,
    check_ratio,
    check_required,
)

# Path to the tool's JSON schema for validation
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "{tool_name}" / "schemas" / "output.schema.json"

# Landing zone table column definitions (used for validation)
# These must match the columns defined in TABLE_DDL
LZ_TABLES = {{
    "lz_{tool_underscored}_file_metrics": {{
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        # TODO: Add your tool's columns here
    }}
}}

# DDL statements for creating landing zone tables
# Must match the definitions in schema.sql
TABLE_DDL = {{
    "lz_{tool_underscored}_file_metrics": """
        CREATE TABLE IF NOT EXISTS lz_{tool_underscored}_file_metrics (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            -- TODO: Add your tool's columns here
            -- Example columns:
            -- lines INTEGER,
            -- complexity INTEGER,
            -- score DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, file_id)
        )
    """,
}}

# Quality rules that this adapter validates
QUALITY_RULES = ["paths", "ranges", "required_fields"]


class {class_name}Adapter(BaseAdapter):
    """Adapter for persisting {tool_name} output to the landing zone."""

    @property
    def tool_name(self) -> str:
        return "{tool_name}"

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
        {tool_underscored}_repo: {class_name}Repository,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._{tool_underscored}_repo = {tool_underscored}_repo

    def _do_persist(self, payload: dict) -> int:
        """Persist {tool_name} output to landing zone."""
        metadata = payload.get("metadata") or {{}}
        data = payload.get("data") or {{}}

        run_pk = self._create_tool_run(metadata)
        layout_run_pk = self._get_layout_run_pk(metadata["run_id"])

        self.validate_quality(data.get("files", []))
        metrics = list(self._map_file_metrics(run_pk, layout_run_pk, data.get("files", [])))
        self._{tool_underscored}_repo.insert_file_metrics(metrics)
        return run_pk

    def validate_quality(self, files: Any) -> None:
        """Validate data quality rules for {tool_name} files.

        TODO: Implement validation for your tool's specific rules.
        """
        errors = []
        for idx, entry in enumerate(files):
            # Path validation (required for all tools)
            raw_path = entry.get("path", "")
            normalized = normalize_file_path(raw_path, self._repo_root)
            if not is_repo_relative_path(normalized):
                errors.append(f"{tool_name} file[{{idx}}] path invalid: {{raw_path}} -> {{normalized}}")

            # TODO: Add your tool-specific validations
            # Example: errors.extend(check_non_negative(entry.get("lines", 0), f"file[{{idx}}].lines"))
            # Example: errors.extend(check_required(entry.get("language"), f"file[{{idx}}].language"))

        if errors:
            for error in errors:
                self._log(f"DATA_QUALITY_ERROR: {{error}}")
            raise ValueError(f"{tool_name} data quality validation failed ({{len(errors)}} errors)")

    def _map_file_metrics(
        self, run_pk: int, layout_run_pk: int, files: Iterable[dict]
    ) -> Iterable[{class_name}FileMetric]:
        """Map raw file entries to entity objects.

        TODO: Update this to match your entity's fields.
        """
        for entry in files:
            relative_path = self._normalize_path(entry.get("path", ""))
            file_id, directory_id = self._layout_repo.get_file_record(
                layout_run_pk, relative_path
            )
            yield {class_name}FileMetric(
                run_pk=run_pk,
                file_id=file_id,
                directory_id=directory_id,
                relative_path=relative_path,
                # TODO: Map your tool's fields here
                # Example: lines=entry.get("lines"),
                # Example: complexity=entry.get("complexity"),
            )
'''


def get_sot_entity_snippet(tool_name: str) -> str:
    """Generate entity dataclass snippet to append to entities.py."""
    class_name = "".join(word.capitalize() for word in tool_name.replace("-", "_").split("_"))
    tool_underscored = tool_name.replace("-", "_")
    return f'''

# =============================================================================
# {tool_name} Entities
# =============================================================================

@dataclass(frozen=True)
class {class_name}FileMetric:
    """Per-file metrics from {tool_name} analysis.

    TODO: Add your tool's metric fields.
    See SccFileMetric for an example with many fields.
    """
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    # TODO: Add your metric fields here
    # Example fields:
    # lines: Optional[int]
    # complexity: Optional[int]
    # score: Optional[float]

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.relative_path, "relative_path")
        # TODO: Add validation for your fields
        # Example: _validate_non_negative(self.lines, "lines")
'''


def get_sot_repository_snippet(tool_name: str) -> str:
    """Generate repository class snippet to append to repositories.py."""
    class_name = "".join(word.capitalize() for word in tool_name.replace("-", "_").split("_"))
    tool_underscored = tool_name.replace("-", "_")
    return f'''

class {class_name}Repository(BaseRepository):
    """Repository for {tool_name} analysis data."""

    _COLUMNS = (
        "run_pk", "file_id", "directory_id", "relative_path",
        # TODO: Add your columns here
    )

    def insert_file_metrics(self, rows: Iterable[{class_name}FileMetric]) -> None:
        self._insert_bulk(
            "lz_{tool_underscored}_file_metrics",
            self._COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.directory_id, r.relative_path,
                # TODO: Add your field mappings here
            ),
        )
'''


def get_sot_schema_snippet(tool_name: str) -> str:
    """Generate schema.sql snippet to append."""
    tool_underscored = tool_name.replace("-", "_")
    return f'''
-- =============================================================================
-- {tool_name}: File-level metrics
-- =============================================================================

CREATE TABLE lz_{tool_underscored}_file_metrics (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    directory_id VARCHAR NOT NULL,
    relative_path VARCHAR NOT NULL,
    -- TODO: Add your columns here
    -- Example columns:
    -- lines INTEGER,
    -- complexity INTEGER,
    -- score DOUBLE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, file_id)
);
'''


def get_sot_dbt_staging_model(tool_name: str) -> str:
    """Generate dbt staging model SQL."""
    tool_underscored = tool_name.replace("-", "_")
    return f'''-- Staging model for {tool_name} file metrics
-- This model prepares raw landing zone data for downstream use

SELECT
    run_pk,
    file_id,
    directory_id,
    relative_path
    -- TODO: Add your columns here
    -- , lines
    -- , complexity
FROM {{{{ source('landing_zone', 'lz_{tool_underscored}_file_metrics') }}}}
'''


def get_sot_adapter_test_template(tool_name: str) -> str:
    """Generate adapter test file template."""
    class_name = "".join(word.capitalize() for word in tool_name.replace("-", "_").split("_"))
    tool_underscored = tool_name.replace("-", "_")
    return f'''"""Tests for {tool_name} adapter.

For implementation examples, see:
- persistence/tests/test_scc_adapter.py
- persistence/tests/test_semgrep_adapter.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pytest

from persistence.adapters.{tool_underscored}_adapter import {class_name}Adapter, SCHEMA_PATH
from persistence.entities import {class_name}FileMetric
from persistence.repositories import (
    LayoutRepository,
    {class_name}Repository,
    ToolRunRepository,
)


@pytest.fixture
def in_memory_db():
    """Create in-memory DuckDB with schema."""
    conn = duckdb.connect(":memory:")
    schema_path = Path(__file__).resolve().parents[2] / "schema.sql"
    conn.execute(schema_path.read_text())
    return conn


@pytest.fixture
def sample_payload() -> dict:
    """Create a minimal valid payload for testing."""
    return {{
        "metadata": {{
            "tool_name": "{tool_name}",
            "tool_version": "1.0.0",
            "run_id": "test-run-id",
            "repo_id": "test-repo-id",
            "branch": "main",
            "commit": "a" * 40,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "schema_version": "1.0.0",
        }},
        "data": {{
            "tool": "{tool_name}",
            "files": [
                {{"path": "src/main.py"}},  # TODO: Add your fields
            ],
        }},
    }}


def test_adapter_schema_path_exists():
    """Verify the schema path is correctly configured."""
    assert SCHEMA_PATH.exists(), f"Schema not found at {{SCHEMA_PATH}}"


def test_adapter_validate_quality():
    """Test data quality validation."""
    # TODO: Implement when adapter is complete
    pass


def test_adapter_persist(in_memory_db, sample_payload):
    """Test persisting data through the adapter."""
    # TODO: Implement when adapter and repositories are complete
    pass
'''


def get_sot_orchestrator_snippet(tool_name: str) -> str:
    """Generate snippet to add to orchestrator.py TOOL_INGESTION_CONFIGS."""
    class_name = "".join(word.capitalize() for word in tool_name.replace("-", "_").split("_"))
    return f'''
# Add to TOOL_INGESTION_CONFIGS list:
# ToolIngestionConfig("{tool_name}", {class_name}Adapter, {class_name}Repository),

# Add to imports:
# from persistence.adapters import {class_name}Adapter
# from persistence.repositories import {class_name}Repository
'''


def get_sot_adapters_init_snippet(tool_name: str) -> str:
    """Generate snippet to add to adapters/__init__.py."""
    class_name = "".join(word.capitalize() for word in tool_name.replace("-", "_").split("_"))
    tool_underscored = tool_name.replace("-", "_")
    return f'''
# Add to adapters/__init__.py:
# from .{tool_underscored}_adapter import {class_name}Adapter

# Add to __all__:
# "{class_name}Adapter",
'''


def get_sot_schema_yml_snippet(tool_name: str) -> str:
    """Generate snippet to add to dbt/models/schema.yml."""
    tool_underscored = tool_name.replace("-", "_")
    return f'''
# Add to sources.tables in schema.yml:
#       - name: lz_{tool_underscored}_file_metrics
#         description: Per-file metrics from {tool_name} analysis
'''


def create_sot_integration(tool_name: str, dry_run: bool = False) -> int:
    """Create SoT integration files for an existing tool."""
    tool_underscored = tool_name.replace("-", "_")
    class_name = "".join(word.capitalize() for word in tool_name.replace("-", "_").split("_"))

    # Paths for SoT integration files
    project_root = Path(__file__).resolve().parents[1]
    sot_dir = project_root / "src" / "sot-engine"

    files_to_create = {
        sot_dir / "persistence" / "adapters" / f"{tool_underscored}_adapter.py":
            get_sot_adapter_template(tool_name),
        sot_dir / "persistence" / "tests" / f"test_{tool_underscored}_adapter.py":
            get_sot_adapter_test_template(tool_name),
        sot_dir / "dbt" / "models" / "staging" / f"stg_{tool_underscored}_file_metrics.sql":
            get_sot_dbt_staging_model(tool_name),
    }

    # Snippets to append to existing files
    snippets = {
        sot_dir / "persistence" / "entities.py": get_sot_entity_snippet(tool_name),
        sot_dir / "persistence" / "repositories.py": get_sot_repository_snippet(tool_name),
        sot_dir / "persistence" / "schema.sql": get_sot_schema_snippet(tool_name),
    }

    # Instructions for manual updates
    manual_updates = {
        "adapters/__init__.py": get_sot_adapters_init_snippet(tool_name),
        "orchestrator.py": get_sot_orchestrator_snippet(tool_name),
        "dbt/models/schema.yml": get_sot_schema_yml_snippet(tool_name),
    }

    if dry_run:
        print(f"Would create SoT integration for: {tool_name}")
        print()
        print("Files to create:")
        for path in sorted(files_to_create.keys()):
            print(f"  {path.relative_to(project_root)}")
        print()
        print("Files to append to:")
        for path in sorted(snippets.keys()):
            print(f"  {path.relative_to(project_root)}")
        print()
        print("Manual updates required:")
        for path in sorted(manual_updates.keys()):
            print(f"  {path}")
        return 0

    print(f"Creating SoT integration for: {tool_name}")
    print()

    # Create new files
    print("Creating files:")
    for path, content in files_to_create.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        print(f"  Created: {path.relative_to(project_root)}")

    # Append to existing files
    print()
    print("Appending to existing files:")
    for path, snippet in snippets.items():
        if path.exists():
            existing = path.read_text()
            path.write_text(existing + snippet)
            print(f"  Appended to: {path.relative_to(project_root)}")
        else:
            print(f"  WARNING: File not found: {path.relative_to(project_root)}")

    # Print manual update instructions
    print()
    print("=" * 60)
    print("MANUAL UPDATES REQUIRED:")
    print("=" * 60)
    for file_path, snippet in manual_updates.items():
        print(f"\\n--- {file_path} ---")
        print(snippet)

    print()
    print("SoT integration scaffolding created!")
    print()
    print("Next steps:")
    print(f"  1. Update entities.py with your metric fields")
    print(f"  2. Update repositories.py column mappings")
    print(f"  3. Update schema.sql with actual columns")
    print(f"  4. Complete {tool_underscored}_adapter.py implementation")
    print(f"  5. Run tests: pytest src/sot-engine/persistence/tests/test_{tool_underscored}_adapter.py")

    return 0


def create_tool(
    tool_name: str,
    dry_run: bool = False,
    sot_integration: bool = False,
    sot_only: bool = False,
) -> int:
    """Create a new tool directory with all required files.

    Args:
        tool_name: Name of the tool (e.g., "my-new-tool")
        dry_run: If True, only show what would be created
        sot_integration: If True, also create SoT integration files
        sot_only: If True, only create SoT integration (tool must exist)
    """
    tool_dir = TOOLS_DIR / tool_name

    # If sot_only, just create SoT integration for existing tool
    if sot_only:
        if not tool_dir.exists():
            print(f"Error: Tool directory does not exist: {tool_dir}", file=sys.stderr)
            print("Use --sot-integration to create both tool and SoT files")
            return 1
        return create_sot_integration(tool_name, dry_run=dry_run)

    if tool_dir.exists():
        print(f"Error: Tool directory already exists: {tool_dir}", file=sys.stderr)
        return 1

    # Define all files to create
    files = {
        "Makefile": get_makefile_template(tool_name),
        "README.md": get_readme_template(tool_name),
        "BLUEPRINT.md": get_blueprint_template(tool_name),
        "EVAL_STRATEGY.md": get_eval_strategy_template(tool_name),
        "requirements.txt": get_requirements_template(),
        "scripts/__init__.py": "",
        "scripts/analyze.py": get_analyze_template(tool_name),
        "scripts/evaluate.py": get_evaluate_template(tool_name),
        "scripts/checks/__init__.py": get_checks_init_template(),
        "scripts/checks/accuracy.py": get_accuracy_check_template(tool_name),
        "scripts/checks/coverage.py": get_coverage_check_template(tool_name),
        "scripts/checks/performance.py": get_performance_check_template(tool_name),
        "schemas/output.schema.json": get_schema_template(tool_name),
        "eval-repos/synthetic/.gitkeep": "",
        "eval-repos/real/.gitkeep": "",
        "evaluation/ground-truth/synthetic.json": get_ground_truth_template(),
        "evaluation/llm/orchestrator.py": get_orchestrator_template(tool_name),
        "evaluation/llm/judges/__init__.py": get_judges_init_template(),
        "evaluation/llm/judges/base.py": get_base_judge_template(tool_name),
        "evaluation/llm/prompts/actionability.md": get_prompt_template(tool_name, "actionability"),
        "evaluation/llm/prompts/accuracy.md": get_prompt_template(tool_name, "accuracy"),
        "evaluation/scorecard.md": get_scorecard_template(tool_name),
        "evaluation/results/.gitkeep": "",
        "tests/__init__.py": "",
        "tests/conftest.py": get_conftest_template(),
        "tests/unit/__init__.py": "",
        "tests/unit/test_analyze.py": get_test_analyze_template(tool_name),
        "tests/unit/test_evaluate.py": get_test_evaluate_template(tool_name),
        "tests/integration/__init__.py": "",
        "tests/integration/test_e2e.py": get_integration_test_template(tool_name),
        "outputs/.gitkeep": "",
    }

    if dry_run:
        print(f"Would create tool: {tool_name}")
        print(f"Directory: {tool_dir}")
        print("\nFiles to create:")
        for path in sorted(files.keys()):
            print(f"  {path}")
        return 0

    # Create tool directory and files
    print(f"Creating tool: {tool_name}")
    print(f"Directory: {tool_dir}")
    print()

    for relative_path, content in files.items():
        file_path = tool_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        print(f"  Created: {relative_path}")

        # Make Makefile executable (required by compliance scanner)
        if relative_path == "Makefile":
            import os
            os.chmod(file_path, 0o755)
            print(f"  Set permissions: {relative_path} -> 755")

    print()
    print("Tool created successfully!")
    print()

    # If sot_integration requested, also create SoT files
    if sot_integration:
        print("=" * 60)
        print("Creating SoT integration...")
        print("=" * 60)
        print()
        result = create_sot_integration(tool_name, dry_run=False)
        if result != 0:
            return result

    print("Next steps:")
    print(f"  1. cd {tool_dir}")
    print("  2. make setup")
    print("  3. Implement analyze.py")
    print("  4. Run: python src/tool-compliance/tool_compliance.py " + str(tool_dir) + " --preflight")
    if sot_integration:
        print("  5. Complete SoT integration (see MANUAL UPDATES above)")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a new Caldera-compliant tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new tool (basic structure only)
  python scripts/create-tool.py my-new-tool

  # Create a new tool with SoT integration scaffolding
  python scripts/create-tool.py my-new-tool --sot-integration

  # Add SoT integration to an existing tool
  python scripts/create-tool.py my-existing-tool --sot-only

  # Preview what would be created
  python scripts/create-tool.py my-new-tool --dry-run
  python scripts/create-tool.py my-new-tool --sot-integration --dry-run
        """,
    )
    parser.add_argument("tool_name", help="Name of the tool (e.g., my-new-tool)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without creating files",
    )
    parser.add_argument(
        "--sot-integration",
        action="store_true",
        help="Also create SoT integration files (adapter, entity, repository, dbt model)",
    )
    parser.add_argument(
        "--sot-only",
        action="store_true",
        help="Only create SoT integration for an existing tool (tool directory must exist)",
    )
    args = parser.parse_args()

    # Validate tool name
    tool_name = args.tool_name.lower()
    if not tool_name.replace("-", "").replace("_", "").isalnum():
        print(f"Error: Invalid tool name: {tool_name}", file=sys.stderr)
        print("Tool name should contain only letters, numbers, hyphens, and underscores")
        return 1

    # Validate flag combinations
    if args.sot_only and args.sot_integration:
        print("Error: Cannot use both --sot-only and --sot-integration", file=sys.stderr)
        return 1

    return create_tool(
        tool_name,
        dry_run=args.dry_run,
        sot_integration=args.sot_integration,
        sot_only=args.sot_only,
    )


if __name__ == "__main__":
    sys.exit(main())
