"""Tool compliance scanner for Project Caldera."""

from __future__ import annotations

import argparse
import json
import os
import re
import ast
import subprocess
import sys
import shutil
import tempfile
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Optional

# Import config loader for YAML-based rules
from config import (
    get_tool_rules,
    get_required_paths,
    get_required_make_targets,
    get_blueprint_required_sections,
    get_eval_strategy_required_sections,
    get_tool_entities,
    get_entity_repository_map,
    get_quality_rule_patterns,
    get_data_completeness_rules,
    get_path_consistency_rules,
    get_test_coverage_rules,
    load_tool_rules,
)

# Threshold for staleness warnings on pre-existing outputs
STALE_THRESHOLD_DAYS = 14

# Configuration is loaded from YAML files in rules/ directory
# These lazy properties provide backwards compatibility with existing code
REQUIRED_PATHS = get_required_paths()
REQUIRED_MAKE_TARGETS = get_required_make_targets()
BLUEPRINT_REQUIRED_SECTIONS = get_blueprint_required_sections()
EVAL_STRATEGY_REQUIRED_SECTIONS = get_eval_strategy_required_sections()

# Tool-specific rules loaded from YAML files in rules/ directory
TOOL_RULES = get_tool_rules()

# Entity-to-repository mapping loaded from YAML
TOOL_ENTITIES = get_tool_entities()
ENTITY_REPOSITORY_MAP = get_entity_repository_map()

SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")

# Key patterns for path detection
_PATH_KEY_PATTERNS = {"path", "file", "dir", "folder", "location", "source"}
_EXCLUDED_KEY_PATTERNS = {"endpoint", "url", "uri", "href", "schema", "ref", "api", "snapshot", "repo"}

# Patterns that indicate implementation of specific quality rules (loaded from YAML)
QUALITY_RULE_PATTERNS = get_quality_rule_patterns()


@dataclass
class CheckResult:
    check_id: str
    status: str
    severity: str
    message: str
    evidence: list[str]
    duration_ms: Optional[float] = None
    stdout_summary: Optional[str] = None
    stderr_summary: Optional[str] = None


@dataclass
class ToolResult:
    name: str
    status: str
    checks: list[CheckResult]


def _parse_make_targets(makefile: Path) -> set[str]:
    targets: set[str] = set()
    for line in makefile.read_text().splitlines():
        if not line or line.startswith(("\t", " ", "#")):
            continue
        if ":" not in line:
            continue
        target = line.split(":", 1)[0].strip()
        if target:
            targets.add(target)
    return targets


def _looks_like_file_path(value: str) -> bool:
    """Detect if a string value looks like a file system path.

    This heuristic identifies file paths while excluding URLs, API endpoints,
    and regex/pattern strings.
    """
    if not value or not isinstance(value, str):
        return False

    # Exclude URLs
    if value.startswith(("http://", "https://", "ftp://", "file://")):
        return False

    # Exclude API endpoints (short paths starting with /api/, /v1/, etc.)
    if re.match(r"^/(?:api|v\d+|graphql)/", value):
        return False

    # Exclude schema references
    if value.startswith(("$", "#")):
        return False

    # Exclude regex patterns (contain regex metacharacters)
    # Common regex patterns: .*, \., ?, +, ^, $, [], (), |
    regex_indicators = (".*", "\\.", "?", "^", "[", "]", "(", ")", "|", "\\\\")
    if any(ind in value for ind in regex_indicators):
        return False

    # Exclude pattern-like strings (contain colon-separated patterns like "path:test/")
    if ":" in value:
        parts = value.split(":", 1)
        # Check if it looks like "key:pattern" format (but not Windows drive letters)
        # Drive letters are single characters, so exclude those from pattern matching
        if len(parts) == 2 and 2 <= len(parts[0]) < 20 and "/" in parts[1]:
            return False

    # Only detect ABSOLUTE paths for value-based heuristic (to minimize false positives)
    # Absolute paths are the main concern for repo-relative compliance
    is_absolute = (
        value.startswith(("/", "\\", "~"))
        or bool(re.match(r"^[A-Za-z]:[/\\]", value))
    )

    # Must have some depth (multiple path segments) to be considered a path
    has_depth = value.count("/") >= 2 or (value.count("\\") >= 1 and "\\" in value)

    # For absolute paths with depth, flag them
    if is_absolute and has_depth:
        return True

    return False


def _collect_path_values(payload: object, include_heuristic: bool = True) -> list[str]:
    """Collect path values from a payload using key patterns and value heuristics.

    Args:
        payload: JSON-like data structure to search
        include_heuristic: Whether to include values that look like paths even if
                          their key doesn't match path patterns

    Returns:
        List of string values that appear to be file paths
    """
    paths: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_lower = key.lower() if isinstance(key, str) else ""

            # Skip excluded keys (URLs, endpoints, schema refs)
            if any(excl in key_lower for excl in _EXCLUDED_KEY_PATTERNS):
                paths.extend(_collect_path_values(value, include_heuristic))
                continue

            # Include if key matches path patterns
            key_matches = any(pat in key_lower for pat in _PATH_KEY_PATTERNS)

            if isinstance(value, str):
                # Collect if key matches OR value looks like a path
                if key_matches or (include_heuristic and _looks_like_file_path(value)):
                    paths.append(value)

            # Recurse into nested structures
            paths.extend(_collect_path_values(value, include_heuristic))
    elif isinstance(payload, list):
        for item in payload:
            paths.extend(_collect_path_values(item, include_heuristic))
    return paths


def _is_invalid_path(value: str) -> bool:
    if not value:
        return False
    if value.startswith(("/", "\\", "~")):
        return True
    if re.match(r"^[A-Za-z]:[\\/]", value):
        return True
    if value.startswith("./"):
        return True
    if ".." in value.split("/"):
        return True
    if "\\" in value:
        return True
    return False


# ---------------------------------------------------------------------------
# Data Completeness and Path Consistency Helper Functions
# ---------------------------------------------------------------------------


def _validate_count_list_consistency(
    data: dict, count_field: str, list_field: str
) -> list[str]:
    """Validate that a count field matches the length of its corresponding list.

    Returns a list of issue descriptions (empty if valid).
    """
    issues: list[str] = []

    count_value = data.get(count_field)
    list_value = data.get(list_field)

    # Skip if neither field exists
    if count_value is None and list_value is None:
        return issues

    # Check consistency if both exist
    if count_value is not None and list_value is not None:
        if isinstance(list_value, list):
            actual_count = len(list_value)
            try:
                expected_count = int(count_value)
                if expected_count != actual_count:
                    issues.append(
                        f"{count_field}={expected_count} but {list_field} has {actual_count} items"
                    )
            except (TypeError, ValueError):
                issues.append(f"{count_field} is not a valid integer: {count_value}")

    # Check for count > 0 but empty list
    if count_value is not None and list_value is not None:
        try:
            expected = int(count_value)
            if expected > 0 and isinstance(list_value, list) and len(list_value) == 0:
                issues.append(f"{count_field}={expected} but {list_field} is empty")
        except (TypeError, ValueError):
            pass

    return issues


def _validate_required_data_fields(
    items: list[dict], required_fields: list[str], context: str
) -> list[str]:
    """Validate that all items have required fields non-null.

    Args:
        items: List of dictionaries to validate
        required_fields: Fields that must be present and non-null
        context: Description for error messages (e.g., "files", "findings")

    Returns a list of issue descriptions.
    """
    issues: list[str] = []

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            issues.append(f"{context}[{i}] is not a dict")
            continue

        for field in required_fields:
            if field not in item:
                issues.append(f"{context}[{i}] missing required field: {field}")
            elif item[field] is None:
                issues.append(f"{context}[{i}].{field} is null")

    return issues


def _validate_aggregate_consistency(data: dict) -> list[str]:
    """Validate aggregate sum consistency (e.g., recursive >= direct for rollups).

    Returns a list of issue descriptions.
    """
    issues: list[str] = []

    # Check for rollup invariants: recursive counts should >= direct counts
    recursive_fields = [k for k in data.keys() if "recursive" in k.lower() and "count" in k.lower()]
    direct_fields = [k for k in data.keys() if "direct" in k.lower() and "count" in k.lower()]

    for rec_field in recursive_fields:
        # Try to find matching direct field
        base_name = rec_field.lower().replace("recursive", "").replace("count", "").strip("_")
        for dir_field in direct_fields:
            dir_base = dir_field.lower().replace("direct", "").replace("count", "").strip("_")
            if base_name == dir_base:
                try:
                    rec_val = int(data.get(rec_field, 0))
                    dir_val = int(data.get(dir_field, 0))
                    if rec_val < dir_val:
                        issues.append(
                            f"Rollup invariant violated: {rec_field}={rec_val} < {dir_field}={dir_val}"
                        )
                except (TypeError, ValueError):
                    pass

    return issues


def _extract_all_paths_by_section(output: dict) -> dict[str, list[str]]:
    """Extract all path values from output, grouped by section.

    Returns a dict mapping section name to list of paths found in that section.
    """
    paths_by_section: dict[str, list[str]] = {}

    data = output.get("data", {})
    if not isinstance(data, dict):
        return paths_by_section

    # Define sections and their path fields
    section_path_fields = {
        "files": ["path", "file_path"],
        "findings": ["file_path"],
        "vulnerabilities": ["file_path", "target_path"],
        "secrets": ["file_path"],
        "issues": ["file_path", "component"],
        "violations": ["file_path"],
        "smells": ["file_path"],
        "functions": ["file_path"],
        "symbols": ["file_path"],
        "directories": ["path"],
    }

    for section_name, path_fields in section_path_fields.items():
        section_data = data.get(section_name, [])
        if not isinstance(section_data, list):
            continue

        paths: list[str] = []
        for item in section_data:
            if not isinstance(item, dict):
                continue
            for field in path_fields:
                value = item.get(field)
                if isinstance(value, str) and value:
                    paths.append(value)

        if paths:
            paths_by_section[section_name] = paths

    return paths_by_section


def _find_path_inconsistencies(paths_by_section: dict[str, list[str]]) -> list[str]:
    """Find inconsistencies across path sections.

    Returns a list of issue descriptions.
    """
    issues: list[str] = []

    # Collect all paths
    all_paths: list[str] = []
    for paths in paths_by_section.values():
        all_paths.extend(paths)

    if not all_paths:
        return issues

    # Check for mixed absolute/relative
    absolute_paths = [p for p in all_paths if _is_invalid_path(p)]
    if absolute_paths:
        issues.append(f"Found {len(absolute_paths)} non-repo-relative paths")

    # Check for path separator inconsistency
    unix_paths = [p for p in all_paths if "/" in p and "\\" not in p]
    win_paths = [p for p in all_paths if "\\" in p]
    if unix_paths and win_paths:
        issues.append(
            f"Mixed path separators: {len(unix_paths)} POSIX, {len(win_paths)} Windows"
        )

    return issues


def _validate_path_references(output: dict) -> list[str]:
    """Validate that file references in findings exist in files list.

    Returns a list of issue descriptions.
    """
    issues: list[str] = []

    data = output.get("data", {})
    if not isinstance(data, dict):
        return issues

    # Get the set of known file paths
    files = data.get("files", [])
    known_paths: set[str] = set()
    if isinstance(files, list):
        for f in files:
            if isinstance(f, dict):
                path = f.get("path") or f.get("file_path")
                if path:
                    known_paths.add(path)

    # If no files list, skip cross-reference check
    if not known_paths:
        return issues

    # Check references in other sections
    sections_to_check = ["findings", "vulnerabilities", "secrets", "issues", "violations", "smells", "functions", "symbols"]

    for section_name in sections_to_check:
        section_data = data.get(section_name, [])
        if not isinstance(section_data, list):
            continue

        for i, item in enumerate(section_data):
            if not isinstance(item, dict):
                continue

            file_path = item.get("file_path")
            if file_path and file_path not in known_paths:
                # Only report first few to avoid spam
                if len(issues) < 10:
                    issues.append(
                        f"{section_name}[{i}].file_path '{file_path}' not found in files list"
                    )
                elif len(issues) == 10:
                    issues.append("... (more path reference issues omitted)")
                    break

    return issues


def _load_json(path: Path) -> tuple[Optional[dict], Optional[str]]:
    try:
        return json.loads(path.read_text()), None
    except json.JSONDecodeError as exc:
        return None, str(exc)


def _find_latest_output(tool_root: Path) -> Optional[Path]:
    eval_output = tool_root / "evaluation" / "results" / "output.json"
    if eval_output.exists():
        return eval_output

    # Check subdirectories of evaluation/results/ (e.g., evaluation/results/healthy/output.json)
    eval_results_dir = tool_root / "evaluation" / "results"
    if eval_results_dir.exists():
        candidates = sorted(
            (p for p in eval_results_dir.iterdir() if p.is_dir() and (p / "output.json").exists()),
            key=lambda p: (p / "output.json").stat().st_mtime,
            reverse=True,
        )
        if candidates:
            return candidates[0] / "output.json"

    # Check outputs/ directory (legacy/alternate location)
    outputs_dir = tool_root / "outputs"
    if not outputs_dir.exists():
        return None
    candidates = sorted(
        (p for p in outputs_dir.iterdir() if (p / "output.json").exists()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return None
    return candidates[0] / "output.json"


def _is_output_stale(path: Path) -> tuple[bool, int]:
    """Check if output file is older than staleness threshold.

    Returns:
        Tuple of (is_stale, age_in_days)
    """
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    age = datetime.now(timezone.utc) - mtime
    return age.days > STALE_THRESHOLD_DAYS, age.days


def _find_evaluation_output(tool_root: Path) -> Optional[Path]:
    """Find evaluation output (scorecard.md or results directory)."""
    scorecard = tool_root / "evaluation" / "scorecard.md"
    if scorecard.exists():
        return scorecard
    results_dir = tool_root / "evaluation" / "results"
    if results_dir.exists() and any(results_dir.iterdir()):
        return results_dir
    return None


def _find_llm_evaluation_output(tool_root: Path) -> Optional[Path]:
    """Find LLM evaluation output (results directory with content).

    Checks multiple locations where tools may store LLM evaluation outputs:
    1. evaluation/llm/results/*.json (preferred)
    2. evaluation/results/llm_evaluation.json (alternate)
    3. evaluation/llm/results/*.md (fallback for reporting)

    Prefers .json files over .md files since JSON is needed for quality checks.
    """
    # Primary location: evaluation/llm/results/
    llm_results = tool_root / "evaluation" / "llm" / "results"
    if llm_results.exists():
        # Prefer JSON files for quality checking
        json_files = list(llm_results.glob("*.json"))
        if json_files:
            return max(json_files, key=lambda p: p.stat().st_mtime)

    # Alternate location: evaluation/results/llm_evaluation.json
    # Check this before falling back to markdown
    alt_path = tool_root / "evaluation" / "results" / "llm_evaluation.json"
    if alt_path.exists():
        return alt_path

    # Fall back to markdown if no JSON anywhere
    if llm_results.exists():
        md_files = list(llm_results.glob("*.md"))
        if md_files:
            return max(md_files, key=lambda p: p.stat().st_mtime)

    return None


def _check_evaluation_quality(results_path: Path) -> CheckResult:
    payload, error = _load_json(results_path)
    if error:
        return CheckResult(
            check_id="evaluation.quality",
            status="fail",
            severity="high",
            message="Evaluation results are invalid JSON",
            evidence=[error],
        )
    decision = (
        payload.get("decision")
        or payload.get("classification")
        or payload.get("summary", {}).get("decision")
    )
    if decision:
        decision_value = str(decision).upper()
        if decision_value not in {"PASS", "STRONG_PASS", "WEAK_PASS"}:
            return CheckResult(
                check_id="evaluation.quality",
                status="fail",
                severity="high",
                message="Evaluation decision below required threshold",
                evidence=[decision_value],
            )
        return CheckResult(
            check_id="evaluation.quality",
            status="pass",
            severity="high",
            message="Evaluation decision meets threshold",
            evidence=[decision_value],
        )

    summary = payload.get("summary", {})
    score = payload.get("score")
    if score is None:
        score = payload.get("total_score")
    if score is None:
        score = payload.get("overall_score")
    if score is None:
        score = summary.get("score")
    if score is None:
        score = summary.get("total_score")
    if score is None:
        score = summary.get("overall_score")
    if score is None:
        score = summary.get("weighted_score")

    failed = payload.get("failed")
    if failed is None:
        failed = payload.get("checks_failed")
    if failed is None:
        failed = summary.get("failed")
    if failed is None:
        failed = summary.get("checks_failed")

    total = payload.get("total") or payload.get("checks_total") or summary.get("total")

    # Handle score-based evaluation with failed count (traditional format)
    if isinstance(score, (int, float)) and failed is not None:
        if score >= 0.9 and int(failed) == 0:
            return CheckResult(
                check_id="evaluation.quality",
                status="pass",
                severity="high",
                message="Evaluation score meets threshold (computed)",
                evidence=[f"score={score}", f"failed={failed}", f"total={total}"],
            )
        return CheckResult(
            check_id="evaluation.quality",
            status="fail",
            severity="high",
            message="Evaluation score below required threshold",
            evidence=[f"score={score}", f"failed={failed}", f"total={total}"],
        )

    # Handle LLM evaluation format (weighted_score on 1-5 scale, no failed count)
    if isinstance(score, (int, float)) and failed is None:
        # LLM evaluations use 1-5 scale; >= 3.5 is passing
        if score >= 3.5:
            return CheckResult(
                check_id="evaluation.quality",
                status="pass",
                severity="high",
                message="LLM evaluation score meets threshold",
                evidence=[f"weighted_score={score}"],
            )
        return CheckResult(
            check_id="evaluation.quality",
            status="fail",
            severity="high",
            message="LLM evaluation score below required threshold",
            evidence=[f"weighted_score={score}"],
        )

    return CheckResult(
        check_id="evaluation.quality",
        status="fail",
        severity="high",
        message="Evaluation decision missing",
        evidence=["missing decision and summary score"],
    )


def _check_llm_quality(results_path: Path) -> CheckResult:
    payload, error = _load_json(results_path)
    if error:
        return CheckResult(
            check_id="evaluation.llm_quality",
            status="fail",
            severity="medium",
            message="LLM evaluation results are invalid JSON",
            evidence=[error],
        )
    decision = payload.get("decision") or payload.get("summary", {}).get("verdict")
    if decision:
        decision_value = str(decision).upper()
        if decision_value not in {"PASS", "STRONG_PASS", "WEAK_PASS"}:
            return CheckResult(
                check_id="evaluation.llm_quality",
                status="fail",
                severity="medium",
                message="LLM evaluation decision below required threshold",
                evidence=[decision_value],
            )
        return CheckResult(
            check_id="evaluation.llm_quality",
            status="pass",
            severity="medium",
            message="LLM evaluation decision meets threshold",
            evidence=[decision_value],
        )

    # Fall back to score-based evaluation (LLM evaluations use 1-5 scale)
    summary = payload.get("summary", {})
    score = (
        payload.get("combined_score")
        or payload.get("score")
        or payload.get("weighted_score")
        or summary.get("combined_score")
        or summary.get("score")
        or summary.get("weighted_score")
    )
    if isinstance(score, (int, float)):
        if score >= 3.5:
            return CheckResult(
                check_id="evaluation.llm_quality",
                status="pass",
                severity="medium",
                message="LLM evaluation score meets threshold",
                evidence=[f"score={score}"],
            )
        return CheckResult(
            check_id="evaluation.llm_quality",
            status="fail",
            severity="medium",
            message="LLM evaluation score below required threshold",
            evidence=[f"score={score}"],
        )

    return CheckResult(
        check_id="evaluation.llm_quality",
        status="fail",
        severity="medium",
        message="LLM evaluation missing decision and score",
        evidence=["missing decision and score fields"],
    )


# ---------------------------------------------------------------------------
# Programmatic and LLM Evaluation File Checks
# ---------------------------------------------------------------------------
# These checks enforce the uniform evaluation pipeline:
# 1. Programmatic evaluation -> evaluation/results/evaluation_report.json
# 2. LLM evaluation -> evaluation/results/llm_evaluation.json (includes programmatic_input)

PROGRAMMATIC_EVAL_PATH = Path("evaluation") / "results" / "evaluation_report.json"
LLM_EVAL_PATH = Path("evaluation") / "results" / "llm_evaluation.json"

PROGRAMMATIC_REQUIRED_FIELDS = ["timestamp", "decision", "score", "checks", "summary"]
LLM_REQUIRED_FIELDS = ["timestamp", "model", "decision", "score", "programmatic_input", "dimensions"]
PASSING_DECISIONS = {"PASS", "STRONG_PASS", "WEAK_PASS"}


def _check_programmatic_exists(tool_root: Path) -> CheckResult:
    """Check that evaluation_report.json exists at uniform path."""
    path = tool_root / PROGRAMMATIC_EVAL_PATH
    if path.exists():
        return CheckResult(
            check_id="evaluation.programmatic_exists",
            status="pass",
            severity="high",
            message="Programmatic evaluation file exists",
            evidence=[str(PROGRAMMATIC_EVAL_PATH)],
        )
    return CheckResult(
        check_id="evaluation.programmatic_exists",
        status="fail",
        severity="high",
        message="Missing evaluation_report.json at uniform path",
        evidence=[str(PROGRAMMATIC_EVAL_PATH)],
    )


def _check_programmatic_schema(tool_root: Path) -> CheckResult:
    """Validate that evaluation_report.json has required fields."""
    path = tool_root / PROGRAMMATIC_EVAL_PATH
    if not path.exists():
        return CheckResult(
            check_id="evaluation.programmatic_schema",
            status="fail",
            severity="high",
            message="Cannot validate schema - file missing",
            evidence=[str(PROGRAMMATIC_EVAL_PATH)],
        )
    payload, error = _load_json(path)
    if error:
        return CheckResult(
            check_id="evaluation.programmatic_schema",
            status="fail",
            severity="high",
            message="Invalid JSON in evaluation_report.json",
            evidence=[error],
        )
    # Check required fields - allow aliases for common field names
    missing = []
    for field in PROGRAMMATIC_REQUIRED_FIELDS:
        if field == "decision":
            if "decision" not in payload and "classification" not in payload:
                missing.append(field)
        elif field == "score":
            if "score" not in payload and "total_score" not in payload and "overall_score" not in payload:
                missing.append(field)
        elif field == "checks":
            # Allow 'dimensions' as alternative (each dimension may have nested checks)
            if "checks" not in payload and "dimensions" not in payload:
                missing.append(field)
        elif field == "summary":
            # summary is optional if dimensions with checks_passed/checks_total exist
            if "summary" not in payload:
                dims = payload.get("dimensions", [])
                has_dimension_counts = any(
                    "checks_passed" in d and "checks_total" in d for d in dims
                ) if isinstance(dims, list) else False
                if not has_dimension_counts:
                    missing.append(field)
        elif field not in payload:
            missing.append(field)
    if missing:
        return CheckResult(
            check_id="evaluation.programmatic_schema",
            status="fail",
            severity="high",
            message="Missing required fields in evaluation_report.json",
            evidence=missing,
        )
    return CheckResult(
        check_id="evaluation.programmatic_schema",
        status="pass",
        severity="high",
        message="Programmatic evaluation schema valid",
        evidence=list(payload.keys())[:10],
    )


def _check_programmatic_quality(tool_root: Path) -> CheckResult:
    """Check that programmatic evaluation decision is passing."""
    path = tool_root / PROGRAMMATIC_EVAL_PATH
    if not path.exists():
        return CheckResult(
            check_id="evaluation.programmatic_quality",
            status="fail",
            severity="high",
            message="Cannot check quality - file missing",
            evidence=[str(PROGRAMMATIC_EVAL_PATH)],
        )
    payload, error = _load_json(path)
    if error:
        return CheckResult(
            check_id="evaluation.programmatic_quality",
            status="fail",
            severity="high",
            message="Invalid JSON",
            evidence=[error],
        )
    decision = payload.get("decision") or payload.get("classification")
    if decision:
        decision_upper = str(decision).upper()
        if decision_upper in PASSING_DECISIONS:
            return CheckResult(
                check_id="evaluation.programmatic_quality",
                status="pass",
                severity="high",
                message="Programmatic evaluation passed",
                evidence=[decision_upper],
            )
        return CheckResult(
            check_id="evaluation.programmatic_quality",
            status="fail",
            severity="high",
            message="Programmatic evaluation failed",
            evidence=[decision_upper],
        )
    # Fall back to score-based check
    score = payload.get("score") or payload.get("overall_score") or payload.get("total_score")
    if isinstance(score, (int, float)):
        # For 0-1 scale, >= 0.7 passes; for 1-5 scale, >= 3.5 passes
        if score <= 1.0 and score >= 0.7:
            return CheckResult(
                check_id="evaluation.programmatic_quality",
                status="pass",
                severity="high",
                message="Programmatic score passes threshold",
                evidence=[f"score={score}"],
            )
        elif score > 1.0 and score >= 3.5:
            return CheckResult(
                check_id="evaluation.programmatic_quality",
                status="pass",
                severity="high",
                message="Programmatic score passes threshold",
                evidence=[f"score={score}"],
            )
        return CheckResult(
            check_id="evaluation.programmatic_quality",
            status="fail",
            severity="high",
            message="Programmatic score below threshold",
            evidence=[f"score={score}"],
        )
    return CheckResult(
        check_id="evaluation.programmatic_quality",
        status="fail",
        severity="high",
        message="Missing decision and score in evaluation_report.json",
        evidence=[],
    )


def _check_llm_exists(tool_root: Path) -> CheckResult:
    """Check that llm_evaluation.json exists at uniform path."""
    path = tool_root / LLM_EVAL_PATH
    if path.exists():
        return CheckResult(
            check_id="evaluation.llm_exists",
            status="pass",
            severity="medium",
            message="LLM evaluation file exists",
            evidence=[str(LLM_EVAL_PATH)],
        )
    return CheckResult(
        check_id="evaluation.llm_exists",
        status="fail",
        severity="medium",
        message="Missing llm_evaluation.json at uniform path",
        evidence=[str(LLM_EVAL_PATH)],
    )


def _check_llm_schema(tool_root: Path) -> CheckResult:
    """Validate that llm_evaluation.json has required fields including programmatic_input."""
    path = tool_root / LLM_EVAL_PATH
    if not path.exists():
        return CheckResult(
            check_id="evaluation.llm_schema",
            status="fail",
            severity="medium",
            message="Cannot validate schema - file missing",
            evidence=[str(LLM_EVAL_PATH)],
        )
    payload, error = _load_json(path)
    if error:
        return CheckResult(
            check_id="evaluation.llm_schema",
            status="fail",
            severity="medium",
            message="Invalid JSON in llm_evaluation.json",
            evidence=[error],
        )
    # Check required fields - allow 'judges' as alias for 'dimensions'
    missing = []
    for field in LLM_REQUIRED_FIELDS:
        if field == "dimensions":
            if "dimensions" not in payload and "judges" not in payload:
                missing.append(field)
        elif field not in payload:
            missing.append(field)
    if missing:
        return CheckResult(
            check_id="evaluation.llm_schema",
            status="fail",
            severity="medium",
            message="Missing required fields in llm_evaluation.json",
            evidence=missing,
        )
    return CheckResult(
        check_id="evaluation.llm_schema",
        status="pass",
        severity="medium",
        message="LLM evaluation schema valid",
        evidence=list(payload.keys())[:10],
    )


def _check_llm_includes_programmatic(tool_root: Path) -> CheckResult:
    """Verify that llm_evaluation.json includes programmatic_input field with required data."""
    path = tool_root / LLM_EVAL_PATH
    if not path.exists():
        return CheckResult(
            check_id="evaluation.llm_includes_programmatic",
            status="fail",
            severity="medium",
            message="Cannot check - file missing",
            evidence=[str(LLM_EVAL_PATH)],
        )
    payload, error = _load_json(path)
    if error:
        return CheckResult(
            check_id="evaluation.llm_includes_programmatic",
            status="fail",
            severity="medium",
            message="Invalid JSON",
            evidence=[error],
        )
    prog_input = payload.get("programmatic_input")
    if not prog_input:
        return CheckResult(
            check_id="evaluation.llm_includes_programmatic",
            status="fail",
            severity="medium",
            message="Missing programmatic_input field in llm_evaluation.json",
            evidence=["LLM evaluation must include programmatic results"],
        )
    # Check required sub-fields
    required_sub = ["file", "decision", "score"]
    missing_sub = [f for f in required_sub if f not in prog_input]
    if missing_sub:
        return CheckResult(
            check_id="evaluation.llm_includes_programmatic",
            status="fail",
            severity="medium",
            message="Incomplete programmatic_input in llm_evaluation.json",
            evidence=[f"missing: {', '.join(missing_sub)}"],
        )
    return CheckResult(
        check_id="evaluation.llm_includes_programmatic",
        status="pass",
        severity="medium",
        message="LLM evaluation includes programmatic input",
        evidence=[f"file={prog_input.get('file')}", f"decision={prog_input.get('decision')}"],
    )


def _check_llm_decision_quality(tool_root: Path) -> CheckResult:
    """Check that LLM evaluation decision is passing."""
    path = tool_root / LLM_EVAL_PATH
    if not path.exists():
        return CheckResult(
            check_id="evaluation.llm_decision_quality",
            status="fail",
            severity="medium",
            message="Cannot check quality - file missing",
            evidence=[str(LLM_EVAL_PATH)],
        )
    payload, error = _load_json(path)
    if error:
        return CheckResult(
            check_id="evaluation.llm_decision_quality",
            status="fail",
            severity="medium",
            message="Invalid JSON",
            evidence=[error],
        )
    decision = (
        payload.get("decision")
        or payload.get("summary", {}).get("verdict")
        or payload.get("summary", {}).get("decision")
    )
    if decision:
        decision_upper = str(decision).upper()
        if decision_upper in PASSING_DECISIONS:
            return CheckResult(
                check_id="evaluation.llm_decision_quality",
                status="pass",
                severity="medium",
                message="LLM evaluation passed",
                evidence=[decision_upper],
            )
        return CheckResult(
            check_id="evaluation.llm_decision_quality",
            status="fail",
            severity="medium",
            message="LLM evaluation failed",
            evidence=[decision_upper],
        )
    # Fall back to score-based check (LLM uses 1-5 scale, >= 3.5 passes)
    score = (
        payload.get("score")
        or payload.get("combined_score")
        or payload.get("summary", {}).get("weighted_score")
    )
    if isinstance(score, (int, float)):
        if score >= 3.5:
            return CheckResult(
                check_id="evaluation.llm_decision_quality",
                status="pass",
                severity="medium",
                message="LLM score passes threshold",
                evidence=[f"score={score}"],
            )
        return CheckResult(
            check_id="evaluation.llm_decision_quality",
            status="fail",
            severity="medium",
            message="LLM score below threshold",
            evidence=[f"score={score}"],
        )
    return CheckResult(
        check_id="evaluation.llm_decision_quality",
        status="fail",
        severity="medium",
        message="Missing decision and score in llm_evaluation.json",
        evidence=[],
    )


def _summarize_output(output: str, limit: int = 800) -> str:
    cleaned = output.strip()
    if not cleaned:
        return ""
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rstrip() + "…"


def _run_make(
    tool_root: Path, target: str, env: dict[str, str]
) -> tuple[int, str, str, float]:
    start = time.perf_counter()
    result = subprocess.run(
        ["make", target],
        cwd=tool_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    duration_ms = (time.perf_counter() - start) * 1000.0
    return result.returncode, result.stdout.strip(), result.stderr.strip(), duration_ms


def _attach_duration(check: CheckResult, duration_ms: float) -> CheckResult:
    if check.duration_ms is None:
        check.duration_ms = round(duration_ms, 2)
    return check


def _attach_duration_many(checks: Iterable[CheckResult], duration_ms: float) -> list[CheckResult]:
    return [_attach_duration(check, duration_ms) for check in checks]


def _validate_schema_with_venv(
    venv_path: str, schema_path: Path, output_path: Path
) -> Optional[str]:
    venv_python = Path(venv_path) / "bin" / "python"
    if not venv_python.exists():
        return f"Venv python not found: {venv_python}"
    code = (
        "import json, jsonschema, sys; "
        "schema=json.load(open(sys.argv[1])); "
        "data=json.load(open(sys.argv[2])); "
        "jsonschema.validate(data, schema)"
    )
    result = subprocess.run(
        [str(venv_python), "-c", code, str(schema_path), str(output_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return result.stdout.strip()
    return None


def _check_required_paths(tool_root: Path) -> CheckResult:
    missing = [p for p in REQUIRED_PATHS if not (tool_root / p).exists()]
    if missing:
        return CheckResult(
            check_id="structure.paths",
            status="fail",
            severity="high",
            message="Missing required paths",
            evidence=missing,
        )
    return CheckResult(
        check_id="structure.paths",
        status="pass",
        severity="high",
        message="All required paths present",
        evidence=[],
    )


def _check_make_targets(tool_root: Path) -> CheckResult:
    makefile = tool_root / "Makefile"
    if not makefile.exists():
        return CheckResult(
            check_id="make.targets",
            status="fail",
            severity="high",
            message="Makefile missing",
            evidence=["Makefile"],
        )
    targets = _parse_make_targets(makefile)
    missing = sorted(REQUIRED_MAKE_TARGETS - targets)
    if missing:
        return CheckResult(
            check_id="make.targets",
            status="fail",
            severity="high",
            message="Missing required Makefile targets",
            evidence=missing,
        )
    return CheckResult(
        check_id="make.targets",
        status="pass",
        severity="high",
        message="Makefile targets present",
        evidence=[],
    )


def _check_makefile_permissions(tool_root: Path) -> CheckResult:
    """Check if Makefile has correct permissions (readable/executable)."""
    makefile = tool_root / "Makefile"
    if not makefile.exists():
        return CheckResult(
            check_id="make.permissions",
            status="fail",
            severity="low",
            message="Makefile missing",
            evidence=["Makefile"],
        )

    mode = makefile.stat().st_mode
    # Check if file is readable by owner (0o400) and group/others (0o044)
    is_readable = (mode & 0o444) != 0

    if not is_readable:
        return CheckResult(
            check_id="make.permissions",
            status="fail",
            severity="low",
            message="Makefile is not readable",
            evidence=[f"Current mode: {oct(mode)}"],
        )

    return CheckResult(
        check_id="make.permissions",
        status="pass",
        severity="low",
        message="Makefile has correct permissions",
        evidence=[],
    )


def _check_check_modules(tool_root: Path) -> CheckResult:
    rules = _get_tool_rules(tool_root)
    expected = rules.get("required_check_modules")
    if not expected:
        # Auto-discovery didn't find any, check if directory exists
        checks_dir = tool_root / "scripts" / "checks"
        if not checks_dir.exists():
            return CheckResult(
                check_id="evaluation.check_modules",
                status="fail",
                severity="medium",
                message="scripts/checks/ directory missing",
                evidence=["scripts/checks/"],
            )
        modules = [f.name for f in checks_dir.glob("*.py") if f.name != "__init__.py"]
        if not modules:
            return CheckResult(
                check_id="evaluation.check_modules",
                status="fail",
                severity="medium",
                message="No check modules found in scripts/checks/",
                evidence=[],
            )
        return CheckResult(
            check_id="evaluation.check_modules",
            status="pass",
            severity="medium",
            message="Check modules present (auto-discovered)",
            evidence=modules,
        )
    checks_dir = tool_root / "scripts" / "checks"
    missing = [name for name in expected if not (checks_dir / name).exists()]
    if missing:
        return CheckResult(
            check_id="evaluation.check_modules",
            status="fail",
            severity="medium",
            message="Missing required check modules",
            evidence=missing,
        )
    return CheckResult(
        check_id="evaluation.check_modules",
        status="pass",
        severity="medium",
        message="Check modules present",
        evidence=[],
    )


def _check_llm_prompts(tool_root: Path) -> CheckResult:
    rules = _get_tool_rules(tool_root)
    expected = rules.get("required_prompts")
    if not expected:
        # Auto-discovery didn't find any, check if directory exists
        prompts_dir = tool_root / "evaluation" / "llm" / "prompts"
        if not prompts_dir.exists():
            return CheckResult(
                check_id="evaluation.llm_prompts",
                status="fail",
                severity="medium",
                message="evaluation/llm/prompts/ directory missing",
                evidence=["evaluation/llm/prompts/"],
            )
        prompts = [f.name for f in prompts_dir.glob("*.md")]
        if not prompts:
            return CheckResult(
                check_id="evaluation.llm_prompts",
                status="fail",
                severity="medium",
                message="No LLM prompts found in evaluation/llm/prompts/",
                evidence=[],
            )
        return CheckResult(
            check_id="evaluation.llm_prompts",
            status="pass",
            severity="medium",
            message="LLM prompts present (auto-discovered)",
            evidence=prompts,
        )
    prompts_dir = tool_root / "evaluation" / "llm" / "prompts"
    missing = [name for name in expected if not (prompts_dir / name).exists()]
    if missing:
        return CheckResult(
            check_id="evaluation.llm_prompts",
            status="fail",
            severity="medium",
            message="Missing required LLM prompts",
            evidence=missing,
        )
    return CheckResult(
        check_id="evaluation.llm_prompts",
        status="pass",
        severity="medium",
        message="LLM prompts present",
        evidence=[],
    )


# Minimum number of LLM judges required per TOOL_REQUIREMENTS.md
MIN_LLM_JUDGES = 4


def _check_llm_judge_count(tool_root: Path) -> CheckResult:
    """Check that tool has minimum required LLM judges (4).

    Per TOOL_REQUIREMENTS.md, tools must have at least 4 LLM judges:
    - accuracy or equivalent (detection accuracy)
    - actionability (developer usefulness)
    - false_positive_rate or equivalent
    - integration_fit (SoT compatibility)
    """
    judges_dir = tool_root / "evaluation" / "llm" / "judges"
    if not judges_dir.exists():
        return CheckResult(
            check_id="evaluation.llm_judge_count",
            status="fail",
            severity="medium",
            message="evaluation/llm/judges/ directory missing",
            evidence=["evaluation/llm/judges/"],
        )

    # Count judge files (exclude __init__.py and base.py)
    judge_files = [
        f.name for f in judges_dir.glob("*.py")
        if f.name not in ("__init__.py", "base.py", "__pycache__")
    ]
    judge_count = len(judge_files)

    if judge_count < MIN_LLM_JUDGES:
        return CheckResult(
            check_id="evaluation.llm_judge_count",
            status="fail",
            severity="medium",
            message=f"Insufficient LLM judges: {judge_count} found, minimum {MIN_LLM_JUDGES} required",
            evidence=judge_files,
        )

    return CheckResult(
        check_id="evaluation.llm_judge_count",
        status="pass",
        severity="medium",
        message=f"LLM judge count meets minimum ({judge_count} >= {MIN_LLM_JUDGES})",
        evidence=judge_files,
    )


# Required evidence keys for synthetic evaluation context pattern
SYNTHETIC_CONTEXT_EVIDENCE_KEYS = {"evaluation_mode", "synthetic_baseline", "interpretation_guidance"}

# Required placeholders in prompt template
SYNTHETIC_CONTEXT_PROMPT_PLACEHOLDERS = {"{{ evaluation_mode }}", "{{ synthetic_baseline }}", "{{ interpretation_guidance }}"}


def _find_primary_judge(judges_dir: Path) -> tuple[Path | None, str | None]:
    """Find the primary judge file (highest weight or first alphabetically).

    Returns:
        Tuple of (judge_path, dimension_name) or (None, None) if not found.
    """
    judge_files = [
        f for f in judges_dir.glob("*.py")
        if f.name not in ("__init__.py", "base.py", "__pycache__")
    ]
    if not judge_files:
        return None, None

    # Try to find the judge with highest weight by parsing AST
    best_judge: Path | None = None
    best_weight = 0.0
    best_dimension: str | None = None

    for judge_file in sorted(judge_files):
        try:
            source = judge_file.read_text()
            tree = ast.parse(source)

            # Look for weight property definition
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "weight":
                    # Look for return statement with numeric value
                    for stmt in ast.walk(node):
                        if isinstance(stmt, ast.Return) and stmt.value:
                            if isinstance(stmt.value, ast.Constant):
                                weight = float(stmt.value.value)
                                if weight > best_weight:
                                    best_weight = weight
                                    best_judge = judge_file
                                    # Also extract dimension_name
                                    for n in ast.walk(tree):
                                        if isinstance(n, ast.FunctionDef) and n.name == "dimension_name":
                                            for s in ast.walk(n):
                                                if isinstance(s, ast.Return) and s.value:
                                                    if isinstance(s.value, ast.Constant):
                                                        best_dimension = s.value.value
        except (SyntaxError, ValueError):
            continue

    if best_judge is None and judge_files:
        # Fall back to first alphabetically
        best_judge = sorted(judge_files)[0]
        try:
            source = best_judge.read_text()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "dimension_name":
                    for stmt in ast.walk(node):
                        if isinstance(stmt, ast.Return) and stmt.value:
                            if isinstance(stmt.value, ast.Constant):
                                best_dimension = stmt.value.value
        except SyntaxError:
            best_dimension = best_judge.stem

    return best_judge, best_dimension


def _check_base_has_evaluation_mode_param(base_path: Path) -> tuple[bool, str]:
    """Check if base.py accepts evaluation_mode parameter in __init__.

    Returns:
        Tuple of (has_param, error_message_if_missing).
    """
    if not base_path.exists():
        return False, "base.py not found"

    try:
        source = base_path.read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        # Check args for evaluation_mode
                        for arg in item.args.args:
                            if arg.arg == "evaluation_mode":
                                return True, ""
                        # Also check kwonlyargs
                        for arg in item.args.kwonlyargs:
                            if arg.arg == "evaluation_mode":
                                return True, ""

        return False, "base.py __init__ missing evaluation_mode parameter"
    except SyntaxError as e:
        return False, f"base.py has syntax error: {e}"


def _check_judge_collect_evidence_keys(judge_path: Path) -> tuple[bool, list[str]]:
    """Check if judge's collect_evidence() sets required synthetic context keys.

    Returns:
        Tuple of (all_present, list_of_missing_keys).
    """
    if not judge_path.exists():
        return False, ["judge file not found"]

    try:
        source = judge_path.read_text()
    except OSError as e:
        return False, [f"cannot read judge file: {e}"]

    # Look for evidence assignments in collect_evidence method
    # We use simple string matching since the pattern is consistent:
    # evidence["evaluation_mode"] = self.evaluation_mode
    # evidence["synthetic_baseline"] = ...
    # evidence["interpretation_guidance"] = ...

    missing = []
    for key in SYNTHETIC_CONTEXT_EVIDENCE_KEYS:
        # Check for both dictionary assignment patterns
        patterns = [
            f'evidence["{key}"]',
            f"evidence['{key}']",
            f'"{key}":', # dict literal pattern
            f"'{key}':", # dict literal pattern
        ]
        if not any(p in source for p in patterns):
            missing.append(key)

    return len(missing) == 0, missing


def _check_prompt_has_placeholders(prompts_dir: Path, dimension_name: str | None) -> tuple[bool, list[str]]:
    """Check if the primary prompt has required synthetic context placeholders.

    Returns:
        Tuple of (all_present, list_of_missing_placeholders).
    """
    if dimension_name is None:
        return False, ["cannot determine dimension name for prompt lookup"]

    prompt_path = prompts_dir / f"{dimension_name}.md"
    if not prompt_path.exists():
        return False, [f"prompt file not found: {dimension_name}.md"]

    try:
        content = prompt_path.read_text()
    except OSError as e:
        return False, [f"cannot read prompt file: {e}"]

    missing = []
    for placeholder in SYNTHETIC_CONTEXT_PROMPT_PLACEHOLDERS:
        if placeholder not in content:
            missing.append(placeholder)

    return len(missing) == 0, missing


def _check_synthetic_evaluation_context(tool_root: Path) -> CheckResult:
    """Check that tool implements synthetic evaluation context pattern.

    The synthetic evaluation context pattern ensures LLM judges don't penalize
    low finding counts on clean real-world repos by providing context about
    tool validation on synthetic repos.

    Requirements:
    1. base.py must accept evaluation_mode parameter in __init__
    2. Primary judge's collect_evidence() must set: evaluation_mode,
       synthetic_baseline, interpretation_guidance
    3. Primary prompt must have placeholders: {{ evaluation_mode }},
       {{ synthetic_baseline }}, {{ interpretation_guidance }}
    """
    judges_dir = tool_root / "evaluation" / "llm" / "judges"
    prompts_dir = tool_root / "evaluation" / "llm" / "prompts"

    if not judges_dir.exists():
        return CheckResult(
            check_id="evaluation.synthetic_context",
            status="fail",
            severity="high",
            message="evaluation/llm/judges/ directory missing",
            evidence=["evaluation/llm/judges/"],
        )

    # Check 1: base.py has evaluation_mode parameter
    base_path = judges_dir / "base.py"
    has_param, base_error = _check_base_has_evaluation_mode_param(base_path)
    if not has_param:
        return CheckResult(
            check_id="evaluation.synthetic_context",
            status="fail",
            severity="high",
            message="base.py missing evaluation_mode parameter",
            evidence=[base_error],
        )

    # Check 2: Find primary judge and verify collect_evidence sets required keys
    primary_judge, dimension_name = _find_primary_judge(judges_dir)
    if primary_judge is None:
        return CheckResult(
            check_id="evaluation.synthetic_context",
            status="fail",
            severity="high",
            message="No primary judge found in evaluation/llm/judges/",
            evidence=[],
        )

    has_keys, missing_keys = _check_judge_collect_evidence_keys(primary_judge)
    if not has_keys:
        return CheckResult(
            check_id="evaluation.synthetic_context",
            status="fail",
            severity="high",
            message=f"Primary judge ({primary_judge.name}) missing synthetic context injection in collect_evidence()",
            evidence=[f"missing keys: {', '.join(missing_keys)}"],
        )

    # Check 3: Primary prompt has required placeholders
    has_placeholders, missing_placeholders = _check_prompt_has_placeholders(prompts_dir, dimension_name)
    if not has_placeholders:
        return CheckResult(
            check_id="evaluation.synthetic_context",
            status="fail",
            severity="high",
            message=f"Primary prompt ({dimension_name}.md) missing required placeholders",
            evidence=[f"missing: {', '.join(missing_placeholders)}"],
        )

    return CheckResult(
        check_id="evaluation.synthetic_context",
        status="pass",
        severity="high",
        message="Synthetic evaluation context pattern implemented correctly",
        evidence=[
            f"base.py: evaluation_mode parameter present",
            f"primary judge: {primary_judge.name}",
            f"prompt: {dimension_name}.md has all placeholders",
        ],
    )


def _check_ground_truth(tool_root: Path) -> CheckResult:
    ground_truth_dir = tool_root / "evaluation" / "ground-truth"
    if not ground_truth_dir.exists():
        return CheckResult(
            check_id="evaluation.ground_truth",
            status="fail",
            severity="high",
            message="Ground truth directory missing",
            evidence=["evaluation/ground-truth"],
        )
    rules = TOOL_RULES.get(tool_root.name, {})
    mode = rules.get("ground_truth_mode", "any")
    if mode == "synthetic_json":
        required = ground_truth_dir / "synthetic.json"
        if not required.exists():
            return CheckResult(
                check_id="evaluation.ground_truth",
                status="fail",
                severity="high",
                message="synthetic.json ground truth missing",
                evidence=["evaluation/ground-truth/synthetic.json"],
            )
        return CheckResult(
            check_id="evaluation.ground_truth",
            status="pass",
            severity="high",
            message="synthetic.json ground truth present",
            evidence=[],
        )
    if mode == "per_language":
        synthetic_root = tool_root / "eval-repos" / "synthetic"
        missing: list[str] = []
        if synthetic_root.exists():
            for entry in sorted(synthetic_root.iterdir()):
                if entry.is_dir() and not entry.name.startswith("."):
                    expected = ground_truth_dir / f"{entry.name}.json"
                    if not expected.exists():
                        missing.append(expected.name)
        if missing:
            return CheckResult(
                check_id="evaluation.ground_truth",
                status="fail",
                severity="high",
                message="Missing per-language ground truth",
                evidence=missing,
            )
        return CheckResult(
            check_id="evaluation.ground_truth",
            status="pass",
            severity="high",
            message="Ground truth covers synthetic repos",
            evidence=[],
        )
    files = list(ground_truth_dir.glob("*.json"))
    if not files:
        return CheckResult(
            check_id="evaluation.ground_truth",
            status="fail",
            severity="high",
            message="No ground truth JSON files found",
            evidence=[],
        )
    return CheckResult(
        check_id="evaluation.ground_truth",
        status="pass",
        severity="high",
        message="Ground truth files present",
        evidence=[f.name for f in files],
    )


def _check_scorecard(tool_root: Path) -> CheckResult:
    scorecard = tool_root / "evaluation" / "scorecard.md"
    if not scorecard.exists():
        return CheckResult(
            check_id="evaluation.scorecard",
            status="fail",
            severity="medium",
            message="Scorecard missing",
            evidence=["evaluation/scorecard.md"],
        )
    if scorecard.stat().st_size == 0:
        return CheckResult(
            check_id="evaluation.scorecard",
            status="fail",
            severity="low",
            message="Scorecard is empty",
            evidence=["evaluation/scorecard.md"],
        )
    return CheckResult(
        check_id="evaluation.scorecard",
        status="pass",
        severity="low",
        message="Scorecard present",
        evidence=[],
    )


def _is_markdown_list_item(line: str) -> bool:
    """Check if line is a markdown list item (not bold/italic markers)."""
    # Must start with - or * followed by a space
    if len(line) < 2:
        return False
    if line[0] not in ("-", "*"):
        return False
    # Markdown bold (**) or italic (*) markers should not be treated as list items
    if line.startswith("**") or line.startswith("__"):
        return False
    # List items must have a space after the marker
    return line[1] == " " or line[1] == "\t"


def _parse_rollup_validation(section_lines: list[str]) -> tuple[list[str], list[str]]:
    rollups: list[str] = []
    tests: list[str] = []

    def _parse_inline(line: str) -> list[str]:
        value = line.split(":", 1)[1].strip()
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    current: Optional[str] = None
    for raw in section_lines:
        line = raw.strip()
        if not line:
            continue
        if line.lower().startswith("rollups:"):
            current = "rollups"
            rollups.extend(_parse_inline(line))
            continue
        if line.lower().startswith("tests:"):
            current = "tests"
            tests.extend(_parse_inline(line))
            continue
        if line.startswith("#"):
            break
        # Treat markdown separators (---) as section breaks
        if line == "---":
            break
        if current == "tests" and not _is_markdown_list_item(line):
            break
        if _is_markdown_list_item(line):
            item = line[1:].strip()
            if not item:
                continue
            if current == "rollups":
                rollups.append(item)
            elif current == "tests":
                tests.append(item)
    return rollups, tests


def _check_rollup_validation(tool_root: Path) -> CheckResult:
    eval_strategy = tool_root / "EVAL_STRATEGY.md"
    if not eval_strategy.exists():
        return CheckResult(
            check_id="evaluation.rollup_validation",
            status="fail",
            severity="high",
            message="EVAL_STRATEGY.md missing",
            evidence=["EVAL_STRATEGY.md"],
        )
    lines = eval_strategy.read_text().splitlines()
    section_start = None
    for idx, line in enumerate(lines):
        if line.strip().lower().startswith("#") and "rollup validation" in line.lower():
            section_start = idx + 1
            break
    if section_start is None:
        return CheckResult(
            check_id="evaluation.rollup_validation",
            status="fail",
            severity="high",
            message="Rollup Validation section not declared",
            evidence=[],
        )
    section_lines = lines[section_start:]
    rollups, tests = _parse_rollup_validation(section_lines)
    missing: list[str] = []
    # Allow empty rollups if tests exist (e.g., repo-level-only tools like git-sizer)
    # These tools validate they have no directory rollups via their test
    if not rollups and not tests:
        missing.append("Rollups or Tests list is required")
    if not tests:
        missing.append("Tests list is missing or empty")
    project_root = tool_root.parents[2] if len(tool_root.parents) > 2 else tool_root.parent
    missing_tests = []
    for test_path in tests:
        candidate = (project_root / test_path).resolve()
        if not candidate.exists():
            missing_tests.append(test_path)
    if missing_tests:
        missing.append("Missing test paths: " + ", ".join(missing_tests))
    if missing:
        return CheckResult(
            check_id="evaluation.rollup_validation",
            status="fail",
            severity="high",
            message="Rollup Validation section incomplete",
            evidence=missing,
        )
    return CheckResult(
        check_id="evaluation.rollup_validation",
        status="pass",
        severity="high",
        message="Rollup Validation declared with valid tests",
        evidence=tests,
    )


def _check_output_schema(
    tool_root: Path, output_path: Path, venv: Optional[str]
) -> CheckResult:
    schema_path = tool_root / "schemas" / "output.schema.json"
    schema, error = _load_json(schema_path)
    if error:
        return CheckResult(
            check_id="output.schema_validate",
            status="fail",
            severity="critical",
            message="Schema is invalid JSON",
            evidence=[error],
        )
    output, error = _load_json(output_path)
    if error:
        return CheckResult(
            check_id="output.schema_validate",
            status="fail",
            severity="critical",
            message="Output is invalid JSON",
            evidence=[error],
        )
    if venv:
        error = _validate_schema_with_venv(venv, schema_path, output_path)
        if error:
            return CheckResult(
                check_id="output.schema_validate",
                status="fail",
                severity="critical",
                message="Schema validation failed in venv",
                evidence=[error],
            )
        return CheckResult(
            check_id="output.schema_validate",
            status="pass",
            severity="critical",
            message="Output validates against schema (venv)",
            evidence=[],
        )
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return CheckResult(
            check_id="output.schema_validate",
            status="fail",
            severity="critical",
            message="jsonschema not installed for validation",
            evidence=[],
        )
    try:
        jsonschema.validate(output, schema)
    except Exception as exc:  # pragma: no cover - jsonschema varies by version
        return CheckResult(
            check_id="output.schema_validate",
            status="fail",
            severity="critical",
            message="Output does not validate against schema",
            evidence=[str(exc)],
        )
    return CheckResult(
        check_id="output.schema_validate",
        status="pass",
        severity="critical",
        message="Output validates against schema",
        evidence=[],
    )


def _check_adapter_compliance(tool_root: Path, tool_name: str) -> CheckResult:
    adapter = TOOL_RULES.get(tool_name, {}).get("adapter")
    if not adapter:
        return CheckResult(
            check_id="adapter.compliance",
            status="FAIL",
            severity="high",
            message="No adapter compliance rule defined",
            evidence=[],
        )
    module_name, class_name = adapter
    project_root = tool_root.parents[2]
    sys.path.insert(0, str(project_root / "src" / "sot-engine"))
    sys.path.insert(0, str(project_root / "src"))
    try:
        module = __import__(module_name, fromlist=[class_name])
        adapter_cls = getattr(module, class_name)
    except Exception as exc:
        return CheckResult(
            check_id="adapter.compliance",
            status="FAIL",
            severity="high",
            message=f"Unable to import adapter {module_name}.{class_name}: {exc}",
            evidence=[str(exc)],
        )
    missing = []
    # Check for module-level constants
    for attr in ("SCHEMA_PATH", "LZ_TABLES", "QUALITY_RULES", "TABLE_DDL"):
        if not hasattr(module, attr):
            missing.append(attr)
    # Check for instance methods on the adapter class
    for method in ("validate_schema", "validate_lz_schema", "validate_quality", "ensure_lz_tables"):
        if not hasattr(adapter_cls, method):
            missing.append(method)
    schema_path = getattr(module, "SCHEMA_PATH", None)
    if schema_path and not Path(schema_path).exists():
        missing.append(f"SCHEMA_PATH not found: {schema_path}")
    if missing:
        return CheckResult(
            check_id="adapter.compliance",
            status="FAIL",
            severity="high",
            message="Adapter missing required contract elements",
            evidence=missing,
        )
    return CheckResult(
        check_id="adapter.compliance",
        status="PASS",
        severity="info",
        message="Adapter exposes schema, LZ contract, and validation hooks",
        evidence=[],
    )


def _parse_schema_sql(schema_path: Path) -> dict[str, dict[str, str]]:
    """Parse schema.sql to extract table definitions.

    Returns:
        Dict mapping table_name -> {column_name: column_type}
    """
    content = schema_path.read_text()
    tables: dict[str, dict[str, str]] = {}

    # Regex to match CREATE TABLE statements - match the table name
    table_pattern = re.compile(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\(",
        re.IGNORECASE,
    )

    for match in table_pattern.finditer(content):
        table_name = match.group(1)
        # Find the matching closing paren by counting parens
        start_idx = match.end()
        body = _extract_table_body(content, start_idx)
        if body:
            columns = _parse_column_definitions(body)
            tables[table_name] = columns

    return tables


def _extract_table_body(content: str, start_idx: int) -> str | None:
    """Extract table body by matching parentheses."""
    depth = 1
    end_idx = start_idx
    while end_idx < len(content) and depth > 0:
        char = content[end_idx]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        end_idx += 1
    if depth == 0:
        return content[start_idx : end_idx - 1]
    return None


def _parse_column_definitions(body: str) -> dict[str, str]:
    """Parse column definitions from CREATE TABLE body."""
    columns: dict[str, str] = {}
    # Remove SQL comments before parsing
    cleaned_lines = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("--"):
            continue
        if "--" in line:
            line = line.split("--", 1)[0].strip()
            if not line:
                continue
        cleaned_lines.append(line)
    cleaned_body = "\n".join(cleaned_lines)

    # Split by comma, handling constraints
    for line in cleaned_body.split(","):
        line = line.strip()
        if not line:
            continue
        # Skip constraints (PRIMARY KEY, UNIQUE, FOREIGN KEY, CHECK)
        upper_line = line.upper()
        if any(
            kw in upper_line
            for kw in ("PRIMARY KEY", "UNIQUE", "FOREIGN KEY", "CHECK")
        ):
            continue
        # Parse column: name type [constraints]
        parts = line.split()
        if len(parts) >= 2:
            col_name = parts[0]
            col_type = parts[1].upper()
            columns[col_name] = col_type
    return columns


def _parse_ddl_columns(ddl: str) -> dict[str, str]:
    """Parse columns from a CREATE TABLE DDL statement.

    Extracts the table body from a full DDL statement and parses columns.
    """
    # Find the opening paren after CREATE TABLE
    table_pattern = re.compile(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\(",
        re.IGNORECASE,
    )
    match = table_pattern.search(ddl)
    if not match:
        return {}

    start_idx = match.end()
    body = _extract_table_body(ddl, start_idx)
    if not body:
        return {}

    return _parse_column_definitions(body)


def _types_match(adapter_type: str, schema_type: str) -> bool:
    """Check if types match (exact or compatible)."""
    # Normalize types
    a = adapter_type.upper().strip()
    s = schema_type.upper().strip()

    # Exact match
    if a == s:
        return True

    # Compatible matches (VARCHAR vs TEXT, etc.)
    compatible = {
        ("VARCHAR", "TEXT"),
        ("TEXT", "VARCHAR"),
        ("INTEGER", "INT"),
        ("INT", "INTEGER"),
        ("BIGINT", "INTEGER"),
        ("INTEGER", "BIGINT"),
    }
    return (a, s) in compatible or (s, a) in compatible


def _check_adapter_schema_alignment(tool_root: Path, tool_name: str) -> CheckResult:
    """Validate adapter TABLE_DDL matches canonical schema.sql."""
    adapter = TOOL_RULES.get(tool_name, {}).get("adapter")
    if not adapter:
        return CheckResult(
            check_id="adapter.schema_alignment",
            status="FAIL",
            severity="high",
            message="No adapter rule defined",
            evidence=[],
        )

    module_name, class_name = adapter
    project_root = tool_root.parents[2]
    sys.path.insert(0, str(project_root / "src" / "sot-engine"))
    sys.path.insert(0, str(project_root / "src"))
    try:
        module = __import__(module_name, fromlist=[class_name])
    except Exception as exc:
        return CheckResult(
            check_id="adapter.schema_alignment",
            status="FAIL",
            severity="high",
            message=f"Unable to import adapter: {exc}",
            evidence=[str(exc)],
        )

    table_ddl = getattr(module, "TABLE_DDL", None)
    if not table_ddl:
        return CheckResult(
            check_id="adapter.schema_alignment",
            status="FAIL",
            severity="high",
            message="Adapter has no TABLE_DDL to validate",
            evidence=[],
        )

    # Parse schema.sql
    schema_path = project_root / "src" / "sot-engine" / "persistence" / "schema.sql"
    if not schema_path.exists():
        return CheckResult(
            check_id="adapter.schema_alignment",
            status="FAIL",
            severity="high",
            message="schema.sql not found",
            evidence=[str(schema_path)],
        )

    canonical_schema = _parse_schema_sql(schema_path)

    # Compare TABLE_DDL against canonical schema
    mismatches: list[str] = []
    for table_name, ddl in table_ddl.items():
        if table_name not in canonical_schema:
            mismatches.append(f"{table_name}: not in schema.sql")
            continue

        # Parse columns from DDL string (extracts body and parses)
        adapter_columns = _parse_ddl_columns(ddl)
        canonical_columns = canonical_schema[table_name]

        # Compare columns
        for col_name, col_type in canonical_columns.items():
            if col_name not in adapter_columns:
                mismatches.append(f"{table_name}.{col_name}: missing in TABLE_DDL")
            elif not _types_match(adapter_columns[col_name], col_type):
                mismatches.append(
                    f"{table_name}.{col_name}: type mismatch "
                    f"(adapter={adapter_columns[col_name]}, schema={col_type})"
                )

        # Check for extra columns in adapter that aren't in schema
        for col_name in adapter_columns:
            if col_name not in canonical_columns:
                mismatches.append(
                    f"{table_name}.{col_name}: in TABLE_DDL but not in schema.sql"
                )

    if mismatches:
        return CheckResult(
            check_id="adapter.schema_alignment",
            status="FAIL",
            severity="high",
            message="TABLE_DDL does not match schema.sql",
            evidence=mismatches,
        )

    return CheckResult(
        check_id="adapter.schema_alignment",
        status="PASS",
        severity="high",
        message="TABLE_DDL matches schema.sql",
        evidence=[],
    )


def _seed_layout_for_fixture(
    conn,
    tool_run_repo,
    layout_repo,
    payload: dict,
) -> None:
    """Seed layout data to allow tool adapter to find file_ids."""
    from datetime import datetime as dt
    # Dynamically import to avoid circular imports
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sot-engine"))
    from persistence.entities import LayoutDirectory, LayoutFile, ToolRun

    metadata = payload.get("metadata", {})
    run_pk = tool_run_repo.insert(ToolRun(
        collection_run_id=metadata["run_id"],
        repo_id=metadata["repo_id"],
        run_id=metadata["run_id"],
        tool_name="layout-scanner",
        tool_version="1.0.0",
        schema_version="1.0.0",
        branch=metadata["branch"],
        commit=metadata["commit"],
        timestamp=dt.fromisoformat(metadata["timestamp"].replace("Z", "+00:00")),
    ))

    # Extract unique file paths from fixture
    files_data = payload.get("data", {}).get("files", [])
    # Handle dict format (e.g., gitleaks) - convert to list
    if isinstance(files_data, dict):
        files_data = [
            {"path": k, "filename": Path(k).name, **v}
            for k, v in files_data.items()
        ]
    if not files_data:
        # Try extracting from findings (e.g., gitleaks, semgrep)
        findings = payload.get("data", {}).get("findings", [])
        if findings:
            seen_paths: set[str] = set()
            files_data = []
            for f in findings:
                path = f.get("file_path", "")
                if path and path not in seen_paths:
                    seen_paths.add(path)
                    files_data.append({"path": path, "filename": Path(path).name})
    if not files_data:
        results = payload.get("data", {}).get("results", {})
        components = results.get("components", {}).get("by_key", {})
        if isinstance(components, dict):
            files_data = [
                {"path": comp.get("path", ""), "filename": Path(comp.get("path", "")).name}
                for comp in components.values()
                if comp.get("path")
            ]
    layout_files = []
    for idx, f in enumerate(files_data):
        path = f.get("path", "")
        directory = f.get("directory", path.rsplit("/", 1)[0] if "/" in path else ".")
        layout_files.append(LayoutFile(
            run_pk=run_pk,
            file_id=f"f-{idx:012d}",
            directory_id=f"d-{idx:012d}",
            relative_path=path,
            filename=f.get("filename", path.split("/")[-1]),
            extension=f".{path.split('.')[-1]}" if "." in path else "",
            language=f.get("language", "unknown"),
            category=f.get("classification", "source"),
            size_bytes=f.get("bytes", 100),
            line_count=f.get("lines", f.get("lines_total", 10)),
            is_binary=f.get("is_binary", False),
        ))
    if layout_files:
        layout_repo.insert_files(layout_files)

    # Insert a root directory
    layout_repo.insert_directories([LayoutDirectory(
        run_pk=run_pk,
        directory_id="d-root",
        relative_path=".",
        parent_id=None,
        depth=0,
        file_count=len(layout_files),
        total_size_bytes=sum(f.size_bytes or 0 for f in layout_files),
    )])


def _get_tool_repository(conn, tool_name: str):
    """Get the appropriate repository for a tool."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sot-engine"))
    from persistence.repositories import (
        SccRepository,
        LizardRepository,
        SemgrepRepository,
        RoslynRepository,
        TrivyRepository,
        SonarqubeRepository,
        GitSizerRepository,
        GitleaksRepository,
        SymbolScannerRepository,
        ScancodeRepository,
        PmdCpdRepository,
        DevskimRepository,
        DotcoverRepository,
    )
    repos = {
        "scc": SccRepository,
        "lizard": LizardRepository,
        "semgrep": SemgrepRepository,
        "roslyn-analyzers": RoslynRepository,
        "trivy": TrivyRepository,
        "sonarqube": SonarqubeRepository,
        "git-sizer": GitSizerRepository,
        "gitleaks": GitleaksRepository,
        "symbol-scanner": SymbolScannerRepository,
        "scancode": ScancodeRepository,
        "pmd-cpd": PmdCpdRepository,
        "devskim": DevskimRepository,
        "dotcover": DotcoverRepository,
    }
    repo_cls = repos.get(tool_name)
    return repo_cls(conn) if repo_cls else None


def _check_adapter_integration(tool_root: Path, tool_name: str) -> CheckResult:
    """Attempt to persist fixture data through adapter using in-memory DB."""
    adapter_rule = TOOL_RULES.get(tool_name, {}).get("adapter")
    if not adapter_rule:
        return CheckResult(
            check_id="adapter.integration",
            status="FAIL",
            severity="high",
            message="No adapter rule defined",
            evidence=[],
        )

    module_name, class_name = adapter_rule
    project_root = tool_root.parents[2]

    # Find fixture file - try multiple naming patterns
    # Handle special case: layout-scanner uses "layout_output.json"
    base_names = [
        tool_name.replace("-", "_"),  # layout_scanner
        tool_name,  # layout-scanner
        tool_name.replace("-scanner", "").replace("-analyzers", ""),  # layout, roslyn
    ]
    fixture_paths = []
    for base in base_names:
        fixture_paths.append(
            project_root / "src" / "sot-engine" / "persistence" / "fixtures" / f"{base}_output.json"
        )
    fixture_paths.append(tool_root / "evaluation" / "ground-truth" / "synthetic.json")
    fixture_path = next((p for p in fixture_paths if p.exists()), None)
    if not fixture_path:
        return CheckResult(
            check_id="adapter.integration",
            status="FAIL",
            severity="high",
            message="No fixture file found for integration test",
            evidence=[str(p) for p in fixture_paths],
        )

    try:
        import duckdb
        conn = duckdb.connect(":memory:")
        schema_path = project_root / "src" / "sot-engine" / "persistence" / "schema.sql"
        conn.execute(schema_path.read_text())

        # Import and instantiate adapter
        sys.path.insert(0, str(project_root / "src" / "sot-engine"))
        sys.path.insert(0, str(project_root / "src"))
        module = __import__(module_name, fromlist=[class_name])
        adapter_cls = getattr(module, class_name)

        # Import repositories
        from persistence.repositories import ToolRunRepository, LayoutRepository
        tool_run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)

        payload = json.loads(fixture_path.read_text())

        # For non-layout tools, seed a layout run first
        if tool_name != "layout-scanner":
            _seed_layout_for_fixture(conn, tool_run_repo, layout_repo, payload)

        # Get tool-specific repository
        repo = _get_tool_repository(conn, tool_name)

        # Create adapter and persist
        if repo:
            adapter = adapter_cls(tool_run_repo, layout_repo, repo)
        else:
            adapter = adapter_cls(tool_run_repo, layout_repo)
        adapter.persist(payload)

        return CheckResult(
            check_id="adapter.integration",
            status="PASS",
            severity="high",
            message="Adapter successfully persisted fixture data",
            evidence=[f"Fixture: {fixture_path.name}"],
        )
    except Exception as exc:
        return CheckResult(
            check_id="adapter.integration",
            status="FAIL",
            severity="high",
            message=f"Adapter failed to persist fixture: {exc}",
            evidence=[str(exc)],
        )


def _check_adapter_quality_rules_coverage(tool_root: Path, tool_name: str) -> CheckResult:
    """Validate that QUALITY_RULES are actually implemented in validate_quality."""
    adapter_rule = TOOL_RULES.get(tool_name, {}).get("adapter")
    if not adapter_rule:
        return CheckResult(
            check_id="adapter.quality_rules_coverage",
            status="FAIL",
            severity="high",
            message="No adapter rule defined",
            evidence=[],
        )

    project_root = tool_root.parents[2]

    # Find adapter source file - try multiple naming patterns
    # Handles: layout-scanner -> layout_adapter.py, roslyn-analyzers -> roslyn_adapter.py
    base_names = [
        tool_name.replace("-", "_"),  # layout_scanner
        tool_name.replace("-scanner", "").replace("-analyzers", "").replace("-", "_"),  # layout, roslyn
        tool_name,  # layout-scanner
    ]
    adapter_candidates = [
        project_root / "src" / "sot-engine" / "persistence" / "adapters" / f"{base}_adapter.py"
        for base in base_names
    ]
    adapter_path = next((p for p in adapter_candidates if p.exists()), None)

    if not adapter_path:
        return CheckResult(
            check_id="adapter.quality_rules_coverage",
            status="FAIL",
            severity="medium",
            message="Adapter source file not found",
            evidence=[str(p) for p in adapter_candidates],
        )

    source = adapter_path.read_text()

    # Extract QUALITY_RULES
    match = re.search(r'QUALITY_RULES\s*=\s*\[(.*?)\]', source, re.DOTALL)
    if not match:
        return CheckResult(
            check_id="adapter.quality_rules_coverage",
            status="FAIL",
            severity="medium",
            message="QUALITY_RULES not found in adapter",
            evidence=[],
        )

    rules_str = match.group(1)
    declared_rules = re.findall(r'"(\w+)"', rules_str)

    # Extract validate_quality method body
    vq_match = re.search(r'def validate_quality\(.*?\).*?:\s*\n(.*?)(?=\n    def |\nclass |\Z)', source, re.DOTALL)
    if not vq_match:
        return CheckResult(
            check_id="adapter.quality_rules_coverage",
            status="FAIL",
            severity="medium",
            message="validate_quality method not found",
            evidence=[],
        )

    vq_body = vq_match.group(1)

    # Check each declared rule has implementation patterns
    missing = []
    for rule in declared_rules:
        patterns = QUALITY_RULE_PATTERNS.get(rule, [])
        if patterns and not any(p.lower() in vq_body.lower() for p in patterns):
            missing.append(f"{rule}: expected patterns {patterns}")

    if missing:
        return CheckResult(
            check_id="adapter.quality_rules_coverage",
            status="FAIL",
            severity="medium",
            message=f"QUALITY_RULES declared but not implemented: {', '.join(declared_rules)}",
            evidence=missing,
        )

    return CheckResult(
        check_id="adapter.quality_rules_coverage",
        status="PASS",
        severity="info",
        message=f"All {len(declared_rules)} quality rules have implementation coverage",
        evidence=declared_rules,
    )


def _normalize_tool_name_for_dbt(tool_name: str) -> str:
    """Convert tool name to dbt model naming convention.

    Examples:
        layout-scanner -> layout
        roslyn-analyzers -> roslyn
        git-sizer -> git_sizer
        scc -> scc
    """
    # Remove common suffixes
    for suffix in ("-scanner", "-analyzers"):
        if tool_name.endswith(suffix):
            tool_name = tool_name[: -len(suffix)]
    # dbt uses underscores, not dashes
    return tool_name.replace("-", "_")


def _parse_rollup_names_from_eval_strategy(eval_strategy_path: Path) -> list[str]:
    """Extract rollup type names from EVAL_STRATEGY.md Rollup Validation section.

    Returns list like ['directory_direct_distributions', 'directory_recursive_distributions']
    """
    if not eval_strategy_path.exists():
        return []

    lines = eval_strategy_path.read_text().splitlines()
    section_start = None
    for idx, line in enumerate(lines):
        if line.strip().lower().startswith("#") and "rollup validation" in line.lower():
            section_start = idx + 1
            break

    if section_start is None:
        return []

    rollups: list[str] = []
    in_rollups = False
    for raw in lines[section_start:]:
        line = raw.strip()
        if not line:
            continue
        if line.lower().startswith("rollups:"):
            in_rollups = True
            # Check for inline values
            value = line.split(":", 1)[1].strip()
            if value:
                rollups.extend([item.strip() for item in value.split(",") if item.strip()])
            continue
        if line.lower().startswith("tests:"):
            break
        if line.startswith(("#",)):
            break
        if in_rollups and line.startswith(("-", "*")):
            item = line[1:].strip()
            if item:
                rollups.append(item)

    return rollups


def _is_valid_iso8601(timestamp: str) -> bool:
    """Check if timestamp is valid ISO8601 format."""
    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return True
    except (ValueError, AttributeError):
        return False


# ===========================================================================
# Cross-Tool SQL Join Pattern Detection
# ===========================================================================

# Table patterns used to identify which tool a table belongs to
TOOL_TABLE_PATTERNS: dict[str, list[str]] = {
    "scc": ["scc_file_metrics", "scc_directory", "rollup_scc_"],
    "lizard": ["lizard_file_metrics", "lizard_function", "rollup_lizard_"],
    "layout-scanner": ["layout_files", "layout_directories", "rollup_layout_"],
    "semgrep": ["semgrep_smells", "semgrep_file_metrics", "rollup_semgrep_"],
    "roslyn-analyzers": ["roslyn_violations", "roslyn_file_metrics", "rollup_roslyn_"],
    "sonarqube": ["sonarqube_issues", "sonarqube_file_metrics", "rollup_sonarqube_"],
    "trivy": ["trivy_vulnerabilities", "trivy_targets", "trivy_iac", "rollup_trivy_"],
    "git-sizer": ["git_sizer_metrics", "git_sizer_violations", "git_sizer_lfs"],
    "gitleaks": ["gitleaks_secrets", "rollup_gitleaks_"],
}

# Regex to detect direct run_pk joins between aliases
CROSS_TOOL_RUN_PK_JOIN = re.compile(
    r"\b(\w+)\.run_pk\s*=\s*(\w+)\.run_pk\b",
    re.IGNORECASE,
)

# Patterns indicating correct cross-tool join approach
COLLECTION_RUN_ID_PATTERN = re.compile(r"\bcollection_run_id\b", re.IGNORECASE)
TOOL_SPECIFIC_RUN_PK = re.compile(
    r"\b(scc_run_pk|lizard_run_pk|semgrep_run_pk|layout_run_pk|trivy_run_pk|roslyn_run_pk|sonarqube_run_pk|git_sizer_run_pk|gitleaks_run_pk)\b",
    re.IGNORECASE,
)
LZ_TOOL_RUNS_PATTERN = re.compile(r"\blz_tool_runs\b", re.IGNORECASE)


def _identify_tools_in_sql(sql_content: str) -> set[str]:
    """Identify which tools are referenced by table names in SQL content."""
    tools_found: set[str] = set()
    sql_lower = sql_content.lower()
    for tool_name, patterns in TOOL_TABLE_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in sql_lower:
                tools_found.add(tool_name)
                break
    return tools_found


def _extract_table_aliases(sql_content: str) -> dict[str, str]:
    """Extract table aliases and map them to their likely tool.

    Returns dict mapping alias -> tool_name (or 'unknown' if not identifiable).
    """
    aliases: dict[str, str] = {}
    sql_lower = sql_content.lower()

    # Pattern: FROM/JOIN table_name alias or FROM/JOIN table_name AS alias
    alias_patterns = [
        # FROM stg_lz_scc_file_metrics sm
        re.compile(r"\b(?:from|join)\s+([\w_]+)\s+(?:as\s+)?(\w+)\b", re.IGNORECASE),
        # CTE pattern: cte_name AS (...)
        re.compile(r"\b(\w+)\s+as\s*\(", re.IGNORECASE),
    ]

    for pattern in alias_patterns:
        for match in pattern.finditer(sql_content):
            if len(match.groups()) == 2:
                table_name, alias = match.groups()
                table_lower = table_name.lower()
                # Determine which tool this table belongs to
                tool = "unknown"
                for tool_name, patterns in TOOL_TABLE_PATTERNS.items():
                    for p in patterns:
                        if p.lower() in table_lower:
                            tool = tool_name
                            break
                    if tool != "unknown":
                        break
                aliases[alias.lower()] = tool
            else:
                # CTE name - mark as unknown unless we can determine from content
                cte_name = match.group(1)
                aliases[cte_name.lower()] = "cte"

    return aliases


def _check_cross_tool_join_patterns_in_file(
    sql_path: Path, sql_content: str
) -> list[str]:
    """Check a single SQL file for incorrect cross-tool join patterns.

    Returns list of error messages (empty if no issues found).
    """
    issues: list[str] = []

    # First, identify which tools are referenced in this file
    tools_in_file = _identify_tools_in_sql(sql_content)

    # If fewer than 2 tools referenced, no cross-tool join possible
    if len(tools_in_file) < 2:
        return []

    # Check if file uses correct patterns (collection_run_id or tool-specific run_pk)
    uses_collection_run_id = bool(COLLECTION_RUN_ID_PATTERN.search(sql_content))
    uses_tool_specific_run_pk = bool(TOOL_SPECIFIC_RUN_PK.search(sql_content))
    uses_lz_tool_runs = bool(LZ_TOOL_RUNS_PATTERN.search(sql_content))

    # Look for the anti-pattern: direct run_pk = run_pk joins
    for match in CROSS_TOOL_RUN_PK_JOIN.finditer(sql_content):
        alias1, alias2 = match.group(1).lower(), match.group(2).lower()

        # Skip self-joins (same alias)
        if alias1 == alias2:
            continue

        # Extract table aliases to see if these are from different tools
        aliases = _extract_table_aliases(sql_content)

        tool1 = aliases.get(alias1, "unknown")
        tool2 = aliases.get(alias2, "unknown")

        # If both aliases are from the same tool or unknown, skip
        if tool1 == tool2:
            continue
        if tool1 == "unknown" or tool2 == "unknown":
            continue
        if tool1 == "cte" or tool2 == "cte":
            # CTEs might be intermediate - check if file has correct patterns
            if uses_collection_run_id or uses_tool_specific_run_pk or uses_lz_tool_runs:
                continue

        # Found a potential cross-tool direct run_pk join
        # Check if the file also uses the correct pattern
        if uses_collection_run_id or uses_tool_specific_run_pk or uses_lz_tool_runs:
            # File uses correct pattern, but let's verify this specific join is okay
            # by checking if one of the aliases is from a CTE that properly maps runs
            continue

        # Find line number for the match
        line_num = sql_content[:match.start()].count("\n") + 1
        issues.append(
            f"{sql_path.name}:{line_num}: Direct run_pk join between "
            f"'{alias1}' ({tool1}) and '{alias2}' ({tool2}) - "
            f"use collection_run_id or tool-specific run_pk columns instead"
        )

    return issues


def _check_cross_tool_join_patterns(project_root: Path) -> CheckResult:
    """Check that cross-tool SQL joins use collection_run_id, not direct run_pk joins.

    This check scans SQL files in:
    - src/sot-engine/dbt/models/
    - src/sot-engine/dbt/analysis/
    - src/insights/queries/

    When queries reference tables from 2+ different tools, they should NOT join
    directly on run_pk (which never matches across tools). Instead, they should:
    1. Use collection_run_id to correlate tool runs, OR
    2. Use tool-specific run_pk columns (e.g., lizard_run_pk, scc_run_pk), OR
    3. Join via lz_tool_runs to find related run_pk values

    Returns a CheckResult with pass/fail status and any issues found.
    """
    sql_dirs = [
        project_root / "src" / "sot-engine" / "dbt" / "models",
        project_root / "src" / "sot-engine" / "dbt" / "analysis",
        project_root / "src" / "insights" / "queries",
    ]

    all_issues: list[str] = []
    files_checked = 0

    for sql_dir in sql_dirs:
        if not sql_dir.exists():
            continue
        for sql_file in sql_dir.glob("**/*.sql"):
            files_checked += 1
            try:
                sql_content = sql_file.read_text()
                issues = _check_cross_tool_join_patterns_in_file(sql_file, sql_content)
                all_issues.extend(issues)
            except Exception as e:
                all_issues.append(f"{sql_file.name}: Error reading file: {e}")

    if all_issues:
        return CheckResult(
            check_id="sql.cross_tool_join_patterns",
            status="fail",
            severity="high",
            message=f"Found {len(all_issues)} incorrect cross-tool run_pk join(s)",
            evidence=all_issues[:10],  # Limit evidence to first 10 issues
        )

    return CheckResult(
        check_id="sql.cross_tool_join_patterns",
        status="pass",
        severity="high",
        message=f"Cross-tool SQL joins use correct patterns ({files_checked} files checked)",
        evidence=[],
    )


# ===========================================================================
# SoT Integration Checks
# ===========================================================================


def _check_sot_adapter_registered(tool_root: Path, tool_name: str) -> CheckResult:
    """Check that adapter class is exported from adapters/__init__.py."""
    adapter_rule = TOOL_RULES.get(tool_name, {}).get("adapter")
    if not adapter_rule:
        return CheckResult(
            check_id="sot.adapter_registered",
            status="skip",
            severity="medium",
            message="No adapter rule defined - skipping registration check",
            evidence=[],
        )

    module_name, class_name = adapter_rule
    project_root = tool_root.parents[2]
    init_path = project_root / "src" / "sot-engine" / "persistence" / "adapters" / "__init__.py"

    if not init_path.exists():
        return CheckResult(
            check_id="sot.adapter_registered",
            status="fail",
            severity="medium",
            message="adapters/__init__.py not found",
            evidence=[str(init_path)],
        )

    init_content = init_path.read_text()

    # Check for import statement
    import_pattern = rf"from\s+\.[\w_]+\s+import\s+.*{class_name}"
    has_import = bool(re.search(import_pattern, init_content))

    # Check for __all__ export
    all_pattern = rf'["\']?{class_name}["\']?'
    has_export = bool(re.search(all_pattern, init_content))

    if not has_import:
        return CheckResult(
            check_id="sot.adapter_registered",
            status="fail",
            severity="medium",
            message=f"Adapter {class_name} not imported in adapters/__init__.py",
            evidence=[class_name],
        )

    if not has_export:
        return CheckResult(
            check_id="sot.adapter_registered",
            status="fail",
            severity="medium",
            message=f"Adapter {class_name} not in __all__ export list",
            evidence=[class_name],
        )

    return CheckResult(
        check_id="sot.adapter_registered",
        status="pass",
        severity="medium",
        message=f"Adapter {class_name} properly registered in adapters/__init__.py",
        evidence=[],
    )


def _check_sot_schema_table(tool_root: Path, tool_name: str) -> CheckResult:
    """Check that schema.sql contains tables for this tool."""
    adapter_rule = TOOL_RULES.get(tool_name, {}).get("adapter")
    if not adapter_rule:
        return CheckResult(
            check_id="sot.schema_table",
            status="skip",
            severity="high",
            message="No adapter rule defined - skipping schema table check",
            evidence=[],
        )

    project_root = tool_root.parents[2]
    schema_path = project_root / "src" / "sot-engine" / "persistence" / "schema.sql"

    if not schema_path.exists():
        return CheckResult(
            check_id="sot.schema_table",
            status="fail",
            severity="high",
            message="schema.sql not found",
            evidence=[str(schema_path)],
        )

    schema_content = schema_path.read_text()

    # Normalize tool name for table naming convention (e.g., roslyn-analyzers -> roslyn)
    normalized_name = tool_name.replace("-", "_").replace("_scanner", "").replace("_analyzers", "")

    # Look for lz_ prefixed tables for this tool
    table_pattern = rf"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?lz_{normalized_name}"
    tables = re.findall(table_pattern, schema_content, re.IGNORECASE)

    if not tables:
        # Also try without normalization
        alt_pattern = rf"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?lz_{tool_name.replace('-', '_')}"
        tables = re.findall(alt_pattern, schema_content, re.IGNORECASE)

    if not tables:
        return CheckResult(
            check_id="sot.schema_table",
            status="fail",
            severity="high",
            message=f"No landing zone tables found for tool (expected lz_{normalized_name}_*)",
            evidence=[f"Pattern: lz_{normalized_name}_*"],
        )

    return CheckResult(
        check_id="sot.schema_table",
        status="pass",
        severity="high",
        message=f"Schema tables found for tool",
        evidence=[f"Found {len(tables)} table(s)"],
    )


def _check_sot_orchestrator_wired(tool_root: Path, tool_name: str) -> CheckResult:
    """Check that tool is wired into TOOL_INGESTION_CONFIGS in orchestrator.py.

    Note: layout-scanner is handled specially in the orchestrator as it's a prerequisite
    for other tools. It doesn't use TOOL_INGESTION_CONFIGS.
    """
    # layout-scanner is handled specially - it's a prerequisite for other tools
    if tool_name == "layout-scanner":
        return CheckResult(
            check_id="sot.orchestrator_wired",
            status="pass",
            severity="high",
            message="layout-scanner handled specially as prerequisite tool",
            evidence=["Layout is ingested before TOOL_INGESTION_CONFIGS loop"],
        )

    adapter_rule = TOOL_RULES.get(tool_name, {}).get("adapter")
    if not adapter_rule:
        return CheckResult(
            check_id="sot.orchestrator_wired",
            status="skip",
            severity="high",
            message="No adapter rule defined - skipping orchestrator wiring check",
            evidence=[],
        )

    project_root = tool_root.parents[2]
    orchestrator_path = project_root / "src" / "sot-engine" / "orchestrator.py"

    if not orchestrator_path.exists():
        return CheckResult(
            check_id="sot.orchestrator_wired",
            status="fail",
            severity="high",
            message="orchestrator.py not found",
            evidence=[str(orchestrator_path)],
        )

    orchestrator_content = orchestrator_path.read_text()

    # Check for TOOL_INGESTION_CONFIGS entry
    # Pattern: ToolIngestionConfig("tool-name", AdapterClass, RepositoryClass)
    config_pattern = rf'ToolIngestionConfig\s*\(\s*["\']?{re.escape(tool_name)}["\']?\s*,'
    has_config = bool(re.search(config_pattern, orchestrator_content))

    if not has_config:
        return CheckResult(
            check_id="sot.orchestrator_wired",
            status="fail",
            severity="high",
            message=f"Tool '{tool_name}' not found in TOOL_INGESTION_CONFIGS",
            evidence=["Add ToolIngestionConfig entry to orchestrator.py"],
        )

    return CheckResult(
        check_id="sot.orchestrator_wired",
        status="pass",
        severity="high",
        message=f"Tool '{tool_name}' wired in TOOL_INGESTION_CONFIGS",
        evidence=[],
    )


def _check_sot_dbt_staging_model(tool_root: Path, tool_name: str) -> CheckResult:
    """Check that a dbt staging model exists for this tool."""
    adapter_rule = TOOL_RULES.get(tool_name, {}).get("adapter")
    if not adapter_rule:
        return CheckResult(
            check_id="sot.dbt_staging_model",
            status="skip",
            severity="high",
            message="No adapter rule defined - skipping dbt staging model check",
            evidence=[],
        )

    project_root = tool_root.parents[2]
    staging_dir = project_root / "src" / "sot-engine" / "dbt" / "models" / "staging"

    if not staging_dir.exists():
        return CheckResult(
            check_id="sot.dbt_staging_model",
            status="fail",
            severity="high",
            message="dbt staging directory not found",
            evidence=[str(staging_dir)],
        )

    # Normalize tool name for dbt naming convention
    dbt_tool_name = _normalize_tool_name_for_dbt(tool_name)

    # Look for staging models matching pattern stg_*<tool>*.sql
    staging_pattern = f"stg_*{dbt_tool_name}*.sql"
    staging_files = list(staging_dir.glob(staging_pattern))

    if not staging_files:
        # Also try lz_ prefix pattern
        staging_lz_pattern = f"stg_lz_{dbt_tool_name}*.sql"
        staging_files = list(staging_dir.glob(staging_lz_pattern))

    if not staging_files:
        return CheckResult(
            check_id="sot.dbt_staging_model",
            status="fail",
            severity="high",
            message=f"No dbt staging models found for tool",
            evidence=[f"Expected: stg_*{dbt_tool_name}*.sql in {staging_dir}"],
        )

    return CheckResult(
        check_id="sot.dbt_staging_model",
        status="pass",
        severity="high",
        message="dbt staging model(s) found",
        evidence=[f.name for f in staging_files],
    )


def _check_dbt_model_coverage(tool_root: Path, tool_name: str) -> CheckResult:
    """Validate tools with adapters have corresponding dbt staging/rollup models."""
    adapter = TOOL_RULES.get(tool_name, {}).get("adapter")
    if not adapter:
        return CheckResult(
            check_id="dbt.model_coverage",
            status="fail",
            severity="high",
            message="No adapter defined for this tool",
            evidence=[],
        )

    project_root = tool_root.parents[2]
    dbt_models_dir = project_root / "src" / "sot-engine" / "dbt" / "models"

    dbt_tool_name = _normalize_tool_name_for_dbt(tool_name)
    missing: list[str] = []

    # Check for staging models
    staging_dir = dbt_models_dir / "staging"
    staging_pattern = f"stg_*{dbt_tool_name}*.sql"
    staging_files = list(staging_dir.glob(staging_pattern)) if staging_dir.exists() else []
    if not staging_files:
        # Also check for lz_ prefix pattern
        staging_lz_pattern = f"stg_lz_{dbt_tool_name}*.sql"
        staging_files = list(staging_dir.glob(staging_lz_pattern)) if staging_dir.exists() else []
    if not staging_files:
        missing.append(f"No staging models matching {staging_pattern}")

    # Check for rollup models if declared in EVAL_STRATEGY.md
    eval_strategy = tool_root / "EVAL_STRATEGY.md"
    declared_rollups = _parse_rollup_names_from_eval_strategy(eval_strategy)

    if declared_rollups:
        marts_dir = dbt_models_dir / "marts"
        for rollup_type in declared_rollups:
            # Pattern: rollup_<tool>_<rollup_type>.sql
            rollup_pattern = f"rollup_{dbt_tool_name}_{rollup_type}.sql"
            rollup_files = list(marts_dir.glob(rollup_pattern)) if marts_dir.exists() else []
            if not rollup_files:
                # Also try with directory_ prefix already in rollup_type
                alt_pattern = f"rollup_{dbt_tool_name}_*.sql"
                all_rollups = list(marts_dir.glob(alt_pattern)) if marts_dir.exists() else []
                matching = [f for f in all_rollups if rollup_type in f.name]
                if not matching:
                    missing.append(f"Missing rollup model for {rollup_type}")

    if missing:
        return CheckResult(
            check_id="dbt.model_coverage",
            status="fail",
            severity="high",
            message="Missing dbt model coverage",
            evidence=missing,
        )

    return CheckResult(
        check_id="dbt.model_coverage",
        status="pass",
        severity="high",
        message="dbt models present for tool",
        evidence=[f.name for f in staging_files],
    )


def _check_entity_repository_alignment(tool_root: Path, tool_name: str) -> CheckResult:
    """Validate entity dataclasses have corresponding repository classes."""
    entities = TOOL_ENTITIES.get(tool_name)
    if not entities:
        return CheckResult(
            check_id="entity.repository_alignment",
            status="fail",
            severity="high",
            message="No entity mappings defined for this tool",
            evidence=[],
        )

    project_root = tool_root.parents[2]
    entities_path = project_root / "src" / "sot-engine" / "persistence" / "entities.py"
    repos_path = project_root / "src" / "sot-engine" / "persistence" / "repositories.py"

    missing: list[str] = []

    if not entities_path.exists():
        return CheckResult(
            check_id="entity.repository_alignment",
            status="fail",
            severity="high",
            message="Entities module not found",
            evidence=[str(entities_path)],
        )
    if not repos_path.exists():
        return CheckResult(
            check_id="entity.repository_alignment",
            status="fail",
            severity="high",
            message="Repositories module not found",
            evidence=[str(repos_path)],
        )

    try:
        entities_ast = ast.parse(entities_path.read_text())
        repos_ast = ast.parse(repos_path.read_text())
    except SyntaxError as exc:
        return CheckResult(
            check_id="entity.repository_alignment",
            status="fail",
            severity="high",
            message=f"Failed to parse persistence modules: {exc}",
            evidence=[str(exc)],
        )

    entity_defs: dict[str, dict[str, bool]] = {}
    for node in entities_ast.body:
        if isinstance(node, ast.ClassDef):
            is_dataclass = False
            frozen = None
            for deco in node.decorator_list:
                if isinstance(deco, ast.Name) and deco.id == "dataclass":
                    is_dataclass = True
                if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Name) and deco.func.id == "dataclass":
                    is_dataclass = True
                    for kw in deco.keywords:
                        if kw.arg == "frozen":
                            if isinstance(kw.value, ast.Constant):
                                frozen = bool(kw.value.value)
            entity_defs[node.name] = {
                "is_dataclass": is_dataclass,
                "frozen": frozen if frozen is not None else True,
            }

    repo_defs: dict[str, set[str]] = {}
    for node in repos_ast.body:
        if isinstance(node, ast.ClassDef):
            methods = {item.name for item in node.body if isinstance(item, ast.FunctionDef)}
            repo_defs[node.name] = methods

    for entity_name in entities:
        entity_info = entity_defs.get(entity_name)
        if not entity_info:
            missing.append(f"{entity_name}: entity class not found")
            continue
        if not entity_info.get("is_dataclass"):
            missing.append(f"{entity_name}: not a dataclass")
            continue
        if entity_info.get("frozen") is False:
            missing.append(f"{entity_name}: dataclass not frozen")
            continue

        repo_mapping = ENTITY_REPOSITORY_MAP.get(entity_name)
        if not repo_mapping:
            missing.append(f"{entity_name}: no repository mapping defined")
            continue

        repo_name, method_name = repo_mapping
        repo_methods = repo_defs.get(repo_name)
        if not repo_methods:
            missing.append(f"{entity_name}: repository {repo_name} not found")
            continue
        if method_name not in repo_methods:
            missing.append(f"{entity_name}: repository missing {method_name} method")
            continue

    if missing:
        return CheckResult(
            check_id="entity.repository_alignment",
            status="fail",
            severity="high",
            message="Entity-repository alignment issues",
            evidence=missing,
        )

    return CheckResult(
        check_id="entity.repository_alignment",
        status="pass",
        severity="high",
        message="All entities have aligned repositories",
        evidence=entities,
    )


def _check_output_metadata_consistency(output: dict) -> CheckResult:
    """Validate metadata field formats and consistency."""
    metadata = output.get("metadata", {})
    data = output.get("data", {})
    issues: list[str] = []

    # Validate commit is 40-hex SHA
    commit = metadata.get("commit", "")
    if commit and not re.match(r"^[0-9a-fA-F]{40}$", str(commit)):
        issues.append(f"commit is not 40-hex SHA: {commit}")

    # Validate timestamp is ISO8601
    timestamp = metadata.get("timestamp", "")
    if timestamp and not _is_valid_iso8601(str(timestamp)):
        issues.append(f"timestamp is not valid ISO8601: {timestamp}")

    # Validate tool_version matches data.tool_version if both present
    meta_version = metadata.get("tool_version")
    data_version = data.get("tool_version")
    if meta_version and data_version and str(meta_version) != str(data_version):
        issues.append(f"tool_version mismatch: metadata={meta_version}, data={data_version}")

    if issues:
        return CheckResult(
            check_id="output.metadata_consistency",
            status="fail",
            severity="medium",
            message="Metadata format/consistency issues",
            evidence=issues,
        )

    return CheckResult(
        check_id="output.metadata_consistency",
        status="pass",
        severity="medium",
        message="Metadata formats are consistent",
        evidence=[],
    )


def _check_test_structure_naming(tool_root: Path) -> CheckResult:
    """Verify test directory structure and naming conventions."""
    issues: list[str] = []

    tests_dir = tool_root / "tests"
    if not tests_dir.exists():
        return CheckResult(
            check_id="test.structure_naming",
            status="fail",
            severity="medium",
            message="tests/ directory missing",
            evidence=["tests/"],
        )

    unit_dir = tests_dir / "unit"
    integration_dir = tests_dir / "integration"

    if not unit_dir.exists():
        issues.append("tests/unit/ directory missing")
    if not integration_dir.exists():
        issues.append("tests/integration/ directory missing")

    # Check test file naming convention
    bad_names: list[str] = []
    for test_dir in [unit_dir, integration_dir]:
        if not test_dir.exists():
            continue
        for py_file in test_dir.glob("**/*.py"):
            if py_file.name == "__init__.py":
                continue
            if py_file.name == "conftest.py":
                continue
            if not py_file.name.startswith("test_"):
                bad_names.append(str(py_file.relative_to(tool_root)))

    if bad_names:
        issues.append(f"Test files not following test_*.py convention: {', '.join(bad_names)}")

    if issues:
        return CheckResult(
            check_id="test.structure_naming",
            status="fail",
            severity="medium",
            message="Test structure/naming issues",
            evidence=issues,
        )

    return CheckResult(
        check_id="test.structure_naming",
        status="pass",
        severity="medium",
        message="Test structure and naming conventions followed",
        evidence=[],
    )


def _run_coverage_test(
    tool_root: Path, env: dict[str, str]
) -> tuple[int, float | None, str, str, float]:
    """Run pytest with coverage and return results.

    Args:
        tool_root: Path to the tool directory
        env: Environment variables to use

    Returns:
        Tuple of (returncode, coverage_percent, stdout, stderr, duration_ms)
    """
    coverage_rules = get_test_coverage_rules()
    source_dirs = coverage_rules.get("source_dirs", ["scripts"])
    omit_patterns = coverage_rules.get("omit_patterns", [])

    # Build coverage command arguments
    cov_args = []
    for source_dir in source_dirs:
        cov_args.extend(["--cov", source_dir])

    for pattern in omit_patterns:
        cov_args.extend(["--cov-config", "/dev/null"])  # Disable .coveragerc
        break  # Only need to add once

    # Add omit patterns
    if omit_patterns:
        omit_str = ",".join(omit_patterns)
        cov_args.extend(["--cov-report", f"json:coverage.json", "--cov-fail-under=0"])
    else:
        cov_args.extend(["--cov-report", "json:coverage.json", "--cov-fail-under=0"])

    # Construct pytest command
    venv_python = env.get("PYTHON", ".venv/bin/python")
    if not Path(tool_root / ".venv" / "bin" / "python").exists():
        # Try project-level venv
        project_venv = tool_root.parents[2] / ".venv" / "bin" / "python"
        if project_venv.exists():
            venv_python = str(project_venv)

    cmd = [
        venv_python,
        "-m",
        "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "-q",
    ] + cov_args

    start = time.perf_counter()
    result = subprocess.run(
        cmd,
        cwd=tool_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=300,  # 5 minute timeout
    )
    duration_ms = (time.perf_counter() - start) * 1000.0

    # Parse coverage.json for percentage
    coverage_percent: float | None = None
    coverage_json = tool_root / "coverage.json"
    if coverage_json.exists():
        try:
            coverage_data = json.loads(coverage_json.read_text())
            totals = coverage_data.get("totals", {})
            coverage_percent = totals.get("percent_covered")
        except (json.JSONDecodeError, KeyError):
            pass
        finally:
            # Clean up coverage.json
            try:
                coverage_json.unlink()
            except OSError:
                pass

    return (
        result.returncode,
        coverage_percent,
        result.stdout.strip(),
        result.stderr.strip(),
        duration_ms,
    )


def _check_test_coverage_threshold(
    tool_root: Path, env: dict[str, str], run_coverage: bool = False
) -> CheckResult:
    """Check that test coverage meets minimum threshold (80%).

    Args:
        tool_root: Path to the tool directory
        env: Environment variables to use
        run_coverage: If True, run tests with coverage. If False, check existing coverage.json.

    Returns:
        CheckResult with coverage validation status
    """
    coverage_rules = get_test_coverage_rules()
    threshold = coverage_rules.get("threshold", 80)

    # Check prerequisites
    tests_dir = tool_root / "tests"
    if not tests_dir.exists():
        return CheckResult(
            check_id="test.coverage_threshold",
            status="skip",
            severity="high",
            message="tests/ directory missing - coverage check skipped",
            evidence=["tests/ not found"],
        )

    requirements_file = tool_root / "requirements.txt"
    if requirements_file.exists():
        requirements_content = requirements_file.read_text().lower()
        if "pytest-cov" not in requirements_content:
            return CheckResult(
                check_id="test.coverage_threshold",
                status="fail",
                severity="high",
                message="pytest-cov not in requirements.txt",
                evidence=["Add pytest-cov>=4.0.0 to requirements.txt"],
            )
    else:
        return CheckResult(
            check_id="test.coverage_threshold",
            status="fail",
            severity="high",
            message="requirements.txt missing",
            evidence=["requirements.txt not found"],
        )

    if not run_coverage:
        # Check for existing coverage report
        coverage_json = tool_root / "coverage.json"
        htmlcov_index = tool_root / "htmlcov" / "index.html"

        if not coverage_json.exists() and not htmlcov_index.exists():
            return CheckResult(
                check_id="test.coverage_threshold",
                status="skip",
                severity="high",
                message="No coverage report found - run with --run-coverage",
                evidence=["coverage.json not found"],
            )

        if coverage_json.exists():
            try:
                coverage_data = json.loads(coverage_json.read_text())
                totals = coverage_data.get("totals", {})
                coverage_percent = totals.get("percent_covered")
                if coverage_percent is None:
                    return CheckResult(
                        check_id="test.coverage_threshold",
                        status="fail",
                        severity="high",
                        message="Invalid coverage.json - missing percent_covered",
                        evidence=["percent_covered field not found in totals"],
                    )

                if coverage_percent >= threshold:
                    return CheckResult(
                        check_id="test.coverage_threshold",
                        status="pass",
                        severity="high",
                        message=f"Test coverage {coverage_percent:.1f}% >= {threshold}% threshold",
                        evidence=[f"coverage={coverage_percent:.1f}%", f"threshold={threshold}%"],
                    )
                else:
                    return CheckResult(
                        check_id="test.coverage_threshold",
                        status="fail",
                        severity="high",
                        message=f"Test coverage {coverage_percent:.1f}% < {threshold}% threshold",
                        evidence=[f"coverage={coverage_percent:.1f}%", f"threshold={threshold}%"],
                    )
            except json.JSONDecodeError as e:
                return CheckResult(
                    check_id="test.coverage_threshold",
                    status="fail",
                    severity="high",
                    message="Invalid coverage.json - parse error",
                    evidence=[str(e)],
                )

        # Fall back to skip if only htmlcov exists (can't parse percentage)
        return CheckResult(
            check_id="test.coverage_threshold",
            status="skip",
            severity="high",
            message="Only htmlcov found - run with --run-coverage for accurate check",
            evidence=["coverage.json not found"],
        )

    # Run coverage tests
    try:
        returncode, coverage_percent, stdout, stderr, duration_ms = _run_coverage_test(
            tool_root, env
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            check_id="test.coverage_threshold",
            status="fail",
            severity="high",
            message="Coverage tests timed out (5 minute limit)",
            evidence=["pytest timed out"],
        )
    except FileNotFoundError as e:
        return CheckResult(
            check_id="test.coverage_threshold",
            status="fail",
            severity="high",
            message="Python or pytest not found",
            evidence=[str(e)],
        )

    # Check if tests passed
    if returncode != 0 and coverage_percent is None:
        return CheckResult(
            check_id="test.coverage_threshold",
            status="fail",
            severity="high",
            message="Tests failed - cannot determine coverage",
            evidence=[_summarize_output(stdout or stderr)],
            duration_ms=round(duration_ms, 2),
            stdout_summary=_summarize_output(stdout),
            stderr_summary=_summarize_output(stderr),
        )

    if coverage_percent is None:
        return CheckResult(
            check_id="test.coverage_threshold",
            status="fail",
            severity="high",
            message="Coverage report not generated",
            evidence=["coverage.json was not created"],
            duration_ms=round(duration_ms, 2),
        )

    if coverage_percent >= threshold:
        return CheckResult(
            check_id="test.coverage_threshold",
            status="pass",
            severity="high",
            message=f"Test coverage {coverage_percent:.1f}% >= {threshold}% threshold",
            evidence=[
                f"coverage={coverage_percent:.1f}%",
                f"threshold={threshold}%",
            ],
            duration_ms=round(duration_ms, 2),
        )

    return CheckResult(
        check_id="test.coverage_threshold",
        status="fail",
        severity="high",
        message=f"Test coverage {coverage_percent:.1f}% < {threshold}% threshold",
        evidence=[
            f"coverage={coverage_percent:.1f}%",
            f"threshold={threshold}%",
            "Increase test coverage to meet threshold",
        ],
        duration_ms=round(duration_ms, 2),
    )


def _check_output_metadata(output: dict) -> list[CheckResult]:
    checks: list[CheckResult] = []
    metadata = output.get("metadata", {})
    data = output.get("data", {})
    required = [
        "tool_name",
        "tool_version",
        "run_id",
        "repo_id",
        "branch",
        "commit",
        "timestamp",
        "schema_version",
    ]
    missing = [field for field in required if not metadata.get(field)]
    if missing:
        checks.append(
            CheckResult(
                check_id="output.required_fields",
                status="fail",
                severity="high",
                message="Missing required metadata fields",
                evidence=missing,
            )
        )
    else:
        checks.append(
            CheckResult(
                check_id="output.required_fields",
                status="pass",
                severity="high",
                message="Required metadata fields present",
                evidence=[],
            )
        )
    schema_version = metadata.get("schema_version", "")
    if schema_version and SEMVER_PATTERN.match(str(schema_version)):
        checks.append(
            CheckResult(
                check_id="output.schema_version",
                status="pass",
                severity="medium",
                message="Schema version is semver",
                evidence=[str(schema_version)],
            )
        )
    else:
        checks.append(
            CheckResult(
                check_id="output.schema_version",
                status="fail",
                severity="medium",
                message="Schema version is not semver",
                evidence=[str(schema_version)],
            )
        )
    if metadata.get("tool_name") and data.get("tool"):
        status = "pass" if metadata.get("tool_name") == data.get("tool") else "fail"
        message = "Tool name matches data.tool" if status == "pass" else "Tool name mismatch"
        checks.append(
            CheckResult(
                check_id="output.tool_name_match",
                status=status,
                severity="low",
                message=message,
                evidence=[str(metadata.get("tool_name")), str(data.get("tool"))],
            )
        )
    return checks


def _check_output_paths(output: dict) -> CheckResult:
    paths = _collect_path_values(output)
    invalid = [value for value in paths if _is_invalid_path(value)]
    if invalid:
        return CheckResult(
            check_id="output.paths",
            status="fail",
            severity="high",
            message="Invalid path values detected",
            evidence=invalid,
        )
    return CheckResult(
        check_id="output.paths",
        status="pass",
        severity="high",
        message="Path values are repo-relative",
        evidence=[],
    )


def _check_data_completeness(output: dict, tool_name: str | None = None) -> CheckResult:
    """Validate data completeness: count/list consistency, required fields, aggregates.

    This check ensures:
    1. Count fields match their corresponding list lengths
    2. Required fields in data items are present and non-null
    3. Aggregate values are consistent (e.g., recursive >= direct)

    Args:
        output: The tool output JSON to validate.
        tool_name: Optional tool name for tool-specific field overrides.
    """
    issues: list[str] = []

    data = output.get("data", {})
    if not isinstance(data, dict):
        return CheckResult(
            check_id="output.data_completeness",
            status="fail",
            severity="high",
            message="Data field is not a dictionary",
            evidence=[f"data type: {type(data).__name__}"],
        )

    # Load rules from config (with tool-specific overrides if tool_name provided)
    completeness_rules = get_data_completeness_rules(tool_name)
    count_list_pairs = completeness_rules.get("count_list_pairs", [])
    required_data_fields = completeness_rules.get("required_data_fields", {})

    # 1. Validate count/list consistency
    for pair in count_list_pairs:
        if isinstance(pair, dict):
            count_field = pair.get("count_field", "")
            list_field = pair.get("list_field", "")
        else:
            continue

        pair_issues = _validate_count_list_consistency(data, count_field, list_field)
        issues.extend(pair_issues)

    # 2. Validate required fields in data lists
    for section_name, required_fields in required_data_fields.items():
        section_data = data.get(section_name, [])
        if isinstance(section_data, list) and section_data:
            if isinstance(required_fields, list):
                field_issues = _validate_required_data_fields(
                    section_data, required_fields, section_name
                )
                # Limit to first 5 issues per section to avoid spam
                issues.extend(field_issues[:5])
                if len(field_issues) > 5:
                    issues.append(f"... {len(field_issues) - 5} more issues in {section_name}")

    # 3. Validate aggregate consistency
    aggregate_issues = _validate_aggregate_consistency(data)
    issues.extend(aggregate_issues)

    if issues:
        return CheckResult(
            check_id="output.data_completeness",
            status="fail",
            severity="high",
            message="Data completeness issues detected",
            evidence=issues[:15],  # Limit evidence to avoid huge reports
        )

    return CheckResult(
        check_id="output.data_completeness",
        status="pass",
        severity="high",
        message="Data completeness validated",
        evidence=[],
    )


def _check_path_consistency(output: dict) -> CheckResult:
    """Validate path consistency across output sections.

    This check ensures:
    1. All paths are repo-relative (no absolute paths)
    2. Path separators are consistent (POSIX-style)
    3. File references in findings exist in files list (when applicable)
    """
    issues: list[str] = []

    # Extract paths by section
    paths_by_section = _extract_all_paths_by_section(output)

    if not paths_by_section:
        # No paths to check - this is OK for some tools
        return CheckResult(
            check_id="output.path_consistency",
            status="pass",
            severity="medium",
            message="No path fields found to validate",
            evidence=[],
        )

    # 1. Check for path inconsistencies (absolute paths, mixed separators)
    inconsistency_issues = _find_path_inconsistencies(paths_by_section)
    issues.extend(inconsistency_issues)

    # 2. Validate cross-references (file_path in findings should exist in files)
    reference_issues = _validate_path_references(output)
    issues.extend(reference_issues)

    if issues:
        return CheckResult(
            check_id="output.path_consistency",
            status="fail",
            severity="medium",
            message="Path consistency issues detected",
            evidence=issues[:15],
        )

    return CheckResult(
        check_id="output.path_consistency",
        status="pass",
        severity="medium",
        message="Path consistency validated",
        evidence=[f"Checked {sum(len(p) for p in paths_by_section.values())} paths across {len(paths_by_section)} sections"],
    )


def _load_output_for_checks(
    tool_root: Path, output_path: Optional[Path]
) -> tuple[Optional[dict], Optional[str], Optional[Path]]:
    path = output_path if output_path and output_path.exists() else _find_latest_output(tool_root)
    if not path:
        return None, "No output.json found", None
    output, error = _load_json(path)
    if error:
        return None, error, path
    return output, None, path


def _check_schema_valid_json(tool_root: Path) -> CheckResult:
    schema_path = tool_root / "schemas" / "output.schema.json"
    if not schema_path.exists():
        return CheckResult(
            check_id="schema.valid_json",
            status="fail",
            severity="medium",
            message="Schema file missing",
            evidence=["schemas/output.schema.json"],
        )
    schema, error = _load_json(schema_path)
    if error:
        return CheckResult(
            check_id="schema.valid_json",
            status="fail",
            severity="medium",
            message="Schema is invalid JSON",
            evidence=[error],
        )
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        return CheckResult(
            check_id="schema.draft",
            status="fail",
            severity="medium",
            message="Schema draft is not 2020-12",
            evidence=[str(schema.get("$schema", ""))],
        )
    return CheckResult(
        check_id="schema.draft",
        status="pass",
        severity="medium",
        message="Schema draft is 2020-12",
        evidence=[],
    )


def _check_schema_contract(tool_root: Path) -> CheckResult:
    schema_path = tool_root / "schemas" / "output.schema.json"
    schema, error = _load_json(schema_path)
    if error:
        return CheckResult(
            check_id="schema.contract",
            status="fail",
            severity="high",
            message="Schema is invalid JSON",
            evidence=[error],
        )
    required_top = set(schema.get("required", []))
    missing = [field for field in ("metadata", "data") if field not in required_top]
    metadata_required = set(
        schema.get("properties", {})
        .get("metadata", {})
        .get("required", [])
    )
    for field in (
        "tool_name",
        "tool_version",
        "run_id",
        "repo_id",
        "branch",
        "commit",
        "timestamp",
        "schema_version",
    ):
        if field not in metadata_required:
            missing.append(f"metadata.{field}")
    if missing:
        return CheckResult(
            check_id="schema.contract",
            status="fail",
            severity="high",
            message="Schema missing required fields",
            evidence=missing,
        )
    return CheckResult(
        check_id="schema.contract",
        status="pass",
        severity="high",
        message="Schema requires metadata and data fields",
        evidence=[],
    )


def _check_makefile_uses_common(tool_root: Path) -> CheckResult:
    """Check if Makefile includes ../Makefile.common."""
    makefile = tool_root / "Makefile"
    if not makefile.exists():
        return CheckResult(
            check_id="make.uses_common",
            status="fail",
            severity="medium",
            message="Makefile missing",
            evidence=["Makefile"],
        )
    content = makefile.read_text()
    # Check for include statement - can be "include ../Makefile.common" or "-include"
    include_pattern = re.compile(r"^-?include\s+\.\./Makefile\.common", re.MULTILINE)
    if include_pattern.search(content):
        return CheckResult(
            check_id="make.uses_common",
            status="pass",
            severity="medium",
            message="Makefile includes ../Makefile.common",
            evidence=[],
        )
    return CheckResult(
        check_id="make.uses_common",
        status="fail",
        severity="medium",
        message="Makefile does not include ../Makefile.common",
        evidence=[
            "Add: include ../Makefile.common",
            "This provides shared variables (RUN_ID, OUTPUT_DIR, VENV_READY) and common targets",
        ],
    )


def _check_output_dir_convention(tool_root: Path) -> CheckResult:
    """Check if OUTPUT_DIR follows outputs/$(RUN_ID) convention."""
    makefile = tool_root / "Makefile"
    if not makefile.exists():
        return CheckResult(
            check_id="make.output_dir_convention",
            status="fail",
            severity="low",
            message="Makefile missing",
            evidence=["Makefile"],
        )
    content = makefile.read_text()

    # Check if Makefile includes common (which provides correct OUTPUT_DIR default)
    uses_common = re.search(r"^-?include\s+\.\./Makefile\.common", content, re.MULTILINE)

    # Look for OUTPUT_DIR definition
    output_dir_match = re.search(r"^OUTPUT_DIR\s*\??\s*=\s*(.+)$", content, re.MULTILINE)

    if not output_dir_match:
        # If no OUTPUT_DIR defined and uses common, that's fine (inherited)
        if uses_common:
            return CheckResult(
                check_id="make.output_dir_convention",
                status="pass",
                severity="low",
                message="OUTPUT_DIR inherited from Makefile.common",
                evidence=["outputs/$(RUN_ID)"],
            )
        return CheckResult(
            check_id="make.output_dir_convention",
            status="fail",
            severity="low",
            message="OUTPUT_DIR not defined",
            evidence=["Add: OUTPUT_DIR ?= outputs/$(RUN_ID)"],
        )

    output_dir_value = output_dir_match.group(1).strip()

    # Valid patterns: outputs/$(RUN_ID), $(EVAL_OUTPUT_DIR) (for override)
    valid_patterns = [
        r"outputs/\$\(RUN_ID\)",
        r"outputs/\$\{RUN_ID\}",
    ]

    for pattern in valid_patterns:
        if re.match(pattern, output_dir_value):
            return CheckResult(
                check_id="make.output_dir_convention",
                status="pass",
                severity="low",
                message="OUTPUT_DIR follows convention",
                evidence=[output_dir_value],
            )

    # Check for common non-compliant patterns
    issues = []
    if "output/" in output_dir_value and "outputs/" not in output_dir_value:
        issues.append("Uses singular 'output/' instead of 'outputs/'")
    if "/runs" in output_dir_value:
        issues.append("Uses hardcoded '/runs' instead of '$(RUN_ID)'")
    if "$(RUN_ID)" not in output_dir_value and "${RUN_ID}" not in output_dir_value:
        issues.append("Does not use $(RUN_ID) for unique output directories")

    if issues:
        return CheckResult(
            check_id="make.output_dir_convention",
            status="fail",
            severity="low",
            message="OUTPUT_DIR does not follow convention",
            evidence=issues + [f"Current: {output_dir_value}", "Expected: outputs/$(RUN_ID)"],
        )

    return CheckResult(
        check_id="make.output_dir_convention",
        status="pass",
        severity="low",
        message="OUTPUT_DIR defined",
        evidence=[output_dir_value],
    )


def _check_output_filename_convention(tool_root: Path) -> CheckResult:
    """Check if analyze target produces OUTPUT_DIR/output.json."""
    makefile = tool_root / "Makefile"
    if not makefile.exists():
        return CheckResult(
            check_id="make.output_filename",
            status="fail",
            severity="medium",
            message="Makefile missing",
            evidence=["Makefile"],
        )
    content = makefile.read_text()

    # Look for the analyze target and check its commands
    # Pattern: analyze: followed by commands that include output.json or OUTPUT_DIR
    analyze_match = re.search(
        r"^analyze:.*?\n((?:\t.*\n)*)",
        content,
        re.MULTILINE,
    )

    if not analyze_match:
        return CheckResult(
            check_id="make.output_filename",
            status="fail",
            severity="medium",
            message="No analyze target found in Makefile",
            evidence=[],
        )

    analyze_commands = analyze_match.group(1)

    # Check for output.json in the commands
    if "output.json" in analyze_commands:
        return CheckResult(
            check_id="make.output_filename",
            status="pass",
            severity="medium",
            message="analyze target produces output.json",
            evidence=[],
        )

    # Check if it uses --output-dir or similar that would create output.json
    if "--output-dir" in analyze_commands or "--output" in analyze_commands:
        # Likely produces output.json - we'll trust the pattern
        return CheckResult(
            check_id="make.output_filename",
            status="pass",
            severity="medium",
            message="analyze target uses output directory argument",
            evidence=[],
        )

    # Check for non-standard patterns like $(REPO_NAME).json
    repo_name_json = re.search(r"\$\(REPO_NAME\)\.json", analyze_commands)
    if repo_name_json:
        return CheckResult(
            check_id="make.output_filename",
            status="fail",
            severity="medium",
            message="analyze target uses $(REPO_NAME).json instead of output.json",
            evidence=[
                "Non-standard: $(REPO_NAME).json",
                "Standard: output.json or --output $(OUTPUT_DIR)/output.json",
            ],
        )

    return CheckResult(
        check_id="make.output_filename",
        status="pass",
        severity="medium",
        message="analyze target output pattern acceptable",
        evidence=[],
    )


def _extract_markdown_sections(content: str) -> list[str]:
    """Extract section headings from markdown content."""
    sections = []
    for line in content.splitlines():
        line = line.strip()
        # Match ## Heading or # Heading patterns
        match = re.match(r"^#{1,3}\s+(.+)$", line)
        if match:
            sections.append(match.group(1).strip())
    return sections


def _check_blueprint_structure(tool_root: Path) -> CheckResult:
    """Validate BLUEPRINT.md has required sections."""
    blueprint_path = tool_root / "BLUEPRINT.md"
    if not blueprint_path.exists():
        return CheckResult(
            check_id="docs.blueprint_structure",
            status="fail",
            severity="medium",
            message="BLUEPRINT.md missing",
            evidence=["BLUEPRINT.md"],
        )

    content = blueprint_path.read_text()
    sections = _extract_markdown_sections(content)
    sections_lower = [s.lower() for s in sections]

    missing = []
    for required in BLUEPRINT_REQUIRED_SECTIONS:
        # Check if any section contains the required keyword
        found = any(required.lower() in s for s in sections_lower)
        if not found:
            missing.append(required)

    if missing:
        return CheckResult(
            check_id="docs.blueprint_structure",
            status="fail",
            severity="medium",
            message="BLUEPRINT.md missing required sections",
            evidence=missing,
        )

    return CheckResult(
        check_id="docs.blueprint_structure",
        status="pass",
        severity="medium",
        message="BLUEPRINT.md has required sections",
        evidence=[],
    )


def _check_eval_strategy_structure(tool_root: Path) -> CheckResult:
    """Validate EVAL_STRATEGY.md has required sections."""
    eval_strategy_path = tool_root / "EVAL_STRATEGY.md"
    if not eval_strategy_path.exists():
        return CheckResult(
            check_id="docs.eval_strategy_structure",
            status="fail",
            severity="high",
            message="EVAL_STRATEGY.md missing",
            evidence=["EVAL_STRATEGY.md"],
        )

    content = eval_strategy_path.read_text()
    sections = _extract_markdown_sections(content)
    sections_lower = [s.lower() for s in sections]

    missing = []
    for required in EVAL_STRATEGY_REQUIRED_SECTIONS:
        # Check if any section contains the required keyword
        found = any(required.lower() in s for s in sections_lower)
        if not found:
            missing.append(required)

    if missing:
        return CheckResult(
            check_id="docs.eval_strategy_structure",
            status="fail",
            severity="high",
            message="EVAL_STRATEGY.md missing required sections",
            evidence=missing,
        )

    return CheckResult(
        check_id="docs.eval_strategy_structure",
        status="pass",
        severity="high",
        message="EVAL_STRATEGY.md has required sections",
        evidence=[],
    )


def _discover_tool_rules(tool_root: Path) -> dict:
    """Auto-discover tool rules from directory structure when not in TOOL_RULES.

    This provides a fallback for new tools that haven't been manually registered.
    """
    rules: dict = {}

    # Discover check modules
    checks_dir = tool_root / "scripts" / "checks"
    if checks_dir.exists():
        check_modules = [
            f.name for f in checks_dir.glob("*.py")
            if f.name != "__init__.py" and not f.name.startswith("_")
        ]
        if check_modules:
            rules["required_check_modules"] = check_modules

    # Discover LLM prompts
    prompts_dir = tool_root / "evaluation" / "llm" / "prompts"
    if prompts_dir.exists():
        prompts = [f.name for f in prompts_dir.glob("*.md")]
        if prompts:
            rules["required_prompts"] = prompts

    # Determine ground truth mode
    ground_truth_dir = tool_root / "evaluation" / "ground-truth"
    if ground_truth_dir.exists():
        if (ground_truth_dir / "synthetic.json").exists():
            rules["ground_truth_mode"] = "synthetic_json"
        else:
            rules["ground_truth_mode"] = "any"

    # Try to discover adapter (common naming patterns)
    tool_name = tool_root.name
    adapter_candidates = [
        tool_name.replace("-", "_"),  # git-sizer -> git_sizer
        tool_name.replace("-scanner", "").replace("-analyzers", "").replace("-", "_"),  # layout-scanner -> layout
    ]

    project_root = tool_root.parents[2] if len(tool_root.parents) > 2 else tool_root.parent
    adapters_dir = project_root / "src" / "sot-engine" / "persistence" / "adapters"

    for base in adapter_candidates:
        adapter_path = adapters_dir / f"{base}_adapter.py"
        if adapter_path.exists():
            # Try to find the class name
            content = adapter_path.read_text()
            class_match = re.search(r"class\s+(\w+Adapter)\s*\(", content)
            if class_match:
                class_name = class_match.group(1)
                rules["adapter"] = (f"persistence.adapters.{base}_adapter", class_name)
                break

    return rules


def _get_tool_rules(tool_root: Path) -> dict:
    """Get rules from TOOL_RULES or auto-discover from directory structure."""
    tool_name = tool_root.name
    if tool_name in TOOL_RULES:
        return TOOL_RULES[tool_name]
    return _discover_tool_rules(tool_root)


def _extract_schema_versions(schema: dict) -> Optional[set[str]]:
    metadata = schema.get("properties", {}).get("metadata", {})
    props = metadata.get("properties", {})
    version_spec = props.get("schema_version", {})
    if "const" in version_spec:
        return {str(version_spec["const"])}
    if "enum" in version_spec:
        return {str(value) for value in version_spec["enum"]}
    return None


def _check_schema_version_alignment(tool_root: Path, output: dict) -> CheckResult:
    schema_path = tool_root / "schemas" / "output.schema.json"
    schema, error = _load_json(schema_path)
    if error:
        return CheckResult(
            check_id="schema.version_alignment",
            status="fail",
            severity="high",
            message="Schema is invalid JSON",
            evidence=[error],
        )
    expected_versions = _extract_schema_versions(schema)
    if not expected_versions:
        return CheckResult(
            check_id="schema.version_alignment",
            status="fail",
            severity="medium",
            message="Schema does not constrain metadata.schema_version",
            evidence=[],
        )
    actual = output.get("metadata", {}).get("schema_version")
    if str(actual) not in expected_versions:
        return CheckResult(
            check_id="schema.version_alignment",
            status="fail",
            severity="high",
            message="Output schema_version does not match schema constraint",
            evidence=[f"expected={sorted(expected_versions)}", f"actual={actual}"],
        )
    return CheckResult(
        check_id="schema.version_alignment",
        status="pass",
        severity="medium",
        message="Output schema_version matches schema constraint",
        evidence=[str(actual)],
    )


def preflight_scan(tool_root: Path) -> ToolResult:
    """Fast preflight validation (~100ms) for structure and Makefile checks only.

    This mode skips adapter checks, output validation, and execution.
    Useful for rapid iteration during tool development.
    """
    def _time_check(fn, *args) -> CheckResult:
        start = time.perf_counter()
        result = fn(*args)
        duration_ms = (time.perf_counter() - start) * 1000.0
        return _attach_duration(result, duration_ms)

    checks: list[CheckResult] = [
        _time_check(_check_required_paths, tool_root),
        _time_check(_check_make_targets, tool_root),
        _time_check(_check_makefile_permissions, tool_root),
        _time_check(_check_makefile_uses_common, tool_root),
        _time_check(_check_output_dir_convention, tool_root),
        _time_check(_check_output_filename_convention, tool_root),
        _time_check(_check_schema_valid_json, tool_root),
        _time_check(_check_schema_contract, tool_root),
        _time_check(_check_blueprint_structure, tool_root),
        _time_check(_check_eval_strategy_structure, tool_root),
        _time_check(_check_test_structure_naming, tool_root),
    ]

    status = "fail" if any(c.status == "fail" for c in checks) else "pass"
    return ToolResult(name=tool_root.name, status=status, checks=checks)


def scan_tool(
    tool_root: Path,
    run_analysis: bool = False,
    run_evaluate: bool = False,
    run_llm: bool = False,
    run_coverage: bool = False,
    venv: Optional[str] = None,
    preflight: bool = False,
) -> ToolResult:
    # Fast preflight mode
    if preflight:
        return preflight_scan(tool_root)
    def _time_check(fn, *args) -> CheckResult:
        start = time.perf_counter()
        result = fn(*args)
        duration_ms = (time.perf_counter() - start) * 1000.0
        return _attach_duration(result, duration_ms)

    env = os.environ.copy()
    if venv:
        env["VENV"] = venv
        env["PYTHON"] = f"{venv}/bin/python"

    output_path: Optional[Path] = None
    eval_output_dir: Optional[Path] = None
    temp_dirs: list[Path] = []
    checks: list[CheckResult] = []

    if run_analysis:
        tmp_path = Path(tempfile.mkdtemp(prefix="tool-compliance-"))
        temp_dirs.append(tmp_path)
        env["OUTPUT_DIR"] = str(tmp_path)
        env["REPO_PATH"] = str(tool_root / "eval-repos" / "synthetic")
        env["REPO_NAME"] = "synthetic"
        env["RUN_ID"] = "compliance"
        env["REPO_ID"] = "compliance"
        env["VENV_READY"] = str(tmp_path / ".venv_ready")
        env["SKIP_SETUP"] = "1"
        returncode, stdout, stderr, duration_ms = _run_make(tool_root, "analyze", env)
        if returncode != 0:
            checks.append(
                CheckResult(
                    check_id="run.analyze",
                    status="fail",
                    severity="critical",
                    message="make analyze failed",
                    evidence=[_summarize_output(stdout or stderr)],
                    duration_ms=round(duration_ms, 2),
                    stdout_summary=_summarize_output(stdout),
                    stderr_summary=_summarize_output(stderr),
                )
            )
        else:
            checks.append(
                CheckResult(
                    check_id="run.analyze",
                    status="pass",
                    severity="critical",
                    message="make analyze succeeded",
                    evidence=[],
                    duration_ms=round(duration_ms, 2),
                    stdout_summary=_summarize_output(stdout),
                    stderr_summary=_summarize_output(stderr),
                )
            )
            output_candidate = tmp_path / "output.json"
            if output_candidate.exists():
                output_path = output_candidate
            else:
                output_path = _find_latest_output(tool_root)
    else:
        # Check for pre-existing analysis output
        existing_output = _find_latest_output(tool_root)
        if existing_output:
            is_stale, age_days = _is_output_stale(existing_output)
            evidence = [str(existing_output)]
            if is_stale:
                evidence.append(
                    f"WARNING: Output is {age_days} days old (threshold: {STALE_THRESHOLD_DAYS} days)"
                )
            checks.append(
                CheckResult(
                    check_id="run.analyze",
                    status="pass",
                    severity="critical",
                    message="Pre-existing analysis output found" + (" (stale)" if is_stale else ""),
                    evidence=evidence,
                    duration_ms=0.0,
                )
            )
            output_path = existing_output
        else:
            checks.append(
                CheckResult(
                    check_id="run.analyze",
                    status="fail",
                    severity="critical",
                    message="No analysis output found - run with --run-analysis or execute 'make analyze'",
                    evidence=[],
                    duration_ms=0.0,
                )
            )

    if run_evaluate:
        eval_output_dir = Path(tempfile.mkdtemp(prefix="tool-compliance-eval-"))
        temp_dirs.append(eval_output_dir)
        env["EVAL_OUTPUT_DIR"] = str(eval_output_dir)
        env["VENV_READY"] = str(eval_output_dir / ".venv_ready")
        env["SKIP_SETUP"] = "1"
        returncode, stdout, stderr, duration_ms = _run_make(tool_root, "evaluate", env)
        if returncode != 0:
            checks.append(
                CheckResult(
                    check_id="run.evaluate",
                    status="fail",
                    severity="high",
                    message="make evaluate failed",
                    evidence=[_summarize_output(stdout or stderr)],
                    duration_ms=round(duration_ms, 2),
                    stdout_summary=_summarize_output(stdout),
                    stderr_summary=_summarize_output(stderr),
                )
            )
        else:
            checks.append(
                CheckResult(
                    check_id="run.evaluate",
                    status="pass",
                    severity="high",
                    message="make evaluate succeeded",
                    evidence=[],
                    duration_ms=round(duration_ms, 2),
                    stdout_summary=_summarize_output(stdout),
                    stderr_summary=_summarize_output(stderr),
                )
            )
            expected = [
                eval_output_dir / name
                for name in TOOL_RULES.get(tool_root.name, {}).get(
                    "evaluation_outputs", ["scorecard.md", "checks.json"]
                )
            ]
            missing = [str(path) for path in expected if not path.exists()]
            if missing:
                checks.append(
                    CheckResult(
                        check_id="evaluation.results",
                        status="fail",
                        severity="high",
                        message="Missing evaluation outputs",
                        evidence=missing,
                    )
                )
            else:
                checks.append(
                    CheckResult(
                        check_id="evaluation.results",
                        status="pass",
                        severity="high",
                        message="Evaluation outputs present",
                        evidence=[],
                    )
                )
            if (eval_output_dir / "output.json").exists():
                output_path = eval_output_dir / "output.json"
            eval_checks = eval_output_dir / "checks.json"
            eval_report = eval_output_dir / "evaluation_report.json"
            eval_llm = eval_output_dir / "llm_evaluation.json"
            eval_candidate = (
                eval_checks if eval_checks.exists()
                else eval_report if eval_report.exists()
                else eval_llm
            )
            if eval_candidate.exists():
                checks.append(_time_check(_check_evaluation_quality, eval_candidate))
            else:
                checks.append(
                    CheckResult(
                        check_id="evaluation.quality",
                        status="fail",
                        severity="high",
                        message="Evaluation results JSON missing",
                        evidence=[str(eval_checks), str(eval_report), str(eval_llm)],
                        duration_ms=0.0,
                    )
                )
    else:
        # Check for pre-existing evaluation output
        existing_eval = _find_evaluation_output(tool_root)
        if existing_eval:
            is_stale, age_days = _is_output_stale(existing_eval)
            evidence = [str(existing_eval)]
            if is_stale:
                evidence.append(
                    f"WARNING: Output is {age_days} days old (threshold: {STALE_THRESHOLD_DAYS} days)"
                )
            checks.append(
                CheckResult(
                    check_id="run.evaluate",
                    status="pass",
                    severity="high",
                    message="Pre-existing evaluation output found" + (" (stale)" if is_stale else ""),
                    evidence=evidence,
                    duration_ms=0.0,
                )
            )
            eval_checks = tool_root / "evaluation" / "results" / "checks.json"
            eval_report = tool_root / "evaluation" / "results" / "evaluation_report.json"
            eval_llm = tool_root / "evaluation" / "results" / "llm_evaluation.json"
            eval_scorecard = tool_root / "evaluation" / "scorecard.json"
            candidate = (
                eval_checks if eval_checks.exists()
                else eval_report if eval_report.exists()
                else eval_llm if eval_llm.exists()
                else eval_scorecard
            )
            if candidate.exists():
                checks.append(_time_check(_check_evaluation_quality, candidate))
            else:
                checks.append(
                    CheckResult(
                        check_id="evaluation.quality",
                        status="fail",
                        severity="high",
                        message="Evaluation results JSON missing",
                        evidence=[str(eval_checks), str(eval_report), str(eval_llm), str(eval_scorecard)],
                        duration_ms=0.0,
                    )
                )
        else:
            checks.append(
                CheckResult(
                    check_id="run.evaluate",
                    status="fail",
                    severity="high",
                    message="No evaluation output found - run with --run-evaluate or execute 'make evaluate'",
                    evidence=[],
                    duration_ms=0.0,
                )
            )
            checks.append(
                CheckResult(
                    check_id="evaluation.quality",
                    status="fail",
                    severity="high",
                    message="Evaluation quality check skipped (no outputs)",
                    evidence=[],
                    duration_ms=0.0,
                )
            )

    if run_llm:
        llm_output_dir = Path(tempfile.mkdtemp(prefix="tool-compliance-eval-"))
        temp_dirs.append(llm_output_dir)
        env["EVAL_OUTPUT_DIR"] = str(llm_output_dir)
        env["VENV_READY"] = str(llm_output_dir / ".venv_ready")
        env["SKIP_SETUP"] = "1"
        env["LLM_MODEL"] = "opus-4.5"
        env["CLAUDE_MODEL"] = "opus-4.5"
        env["CLAUDE_MAX_TURNS"] = env.get("CLAUDE_MAX_TURNS", "40")
        env["LLM_RETRIES"] = env.get("LLM_RETRIES", "2")

        returncode, stdout, stderr, duration_ms = _run_make(tool_root, "evaluate-llm", env)
        if returncode != 0:
            checks.append(
                CheckResult(
                    check_id="run.evaluate_llm",
                    status="fail",
                    severity="medium",
                    message="make evaluate-llm failed",
                    evidence=[_summarize_output(stdout or stderr)],
                    duration_ms=round(duration_ms, 2),
                    stdout_summary=_summarize_output(stdout),
                    stderr_summary=_summarize_output(stderr),
                )
            )
        else:
            checks.append(
                CheckResult(
                    check_id="run.evaluate_llm",
                    status="pass",
                    severity="medium",
                    message="make evaluate-llm succeeded",
                    evidence=[],
                    duration_ms=round(duration_ms, 2),
                    stdout_summary=_summarize_output(stdout),
                    stderr_summary=_summarize_output(stderr),
                )
            )
            expected_temp = llm_output_dir / "llm_evaluation.json"
            expected_repo = tool_root / "evaluation" / "results" / "llm_evaluation.json"
            expected = expected_temp if expected_temp.exists() else expected_repo
            if not expected.exists():
                checks.append(
                    CheckResult(
                        check_id="evaluation.llm_results",
                        status="fail",
                        severity="medium",
                        message="LLM evaluation output missing",
                        evidence=[str(expected_temp), str(expected_repo)],
                    )
                )
            else:
                checks.append(
                    CheckResult(
                        check_id="evaluation.llm_results",
                        status="pass",
                        severity="medium",
                        message="LLM evaluation output present",
                        evidence=[],
                    )
                )
            llm_results = llm_output_dir / "llm_evaluation.json"
            if llm_results.exists():
                checks.append(_time_check(_check_llm_quality, llm_results))
            else:
                checks.append(
                    CheckResult(
                        check_id="evaluation.llm_quality",
                        status="fail",
                        severity="medium",
                        message="LLM evaluation JSON missing",
                        evidence=[str(llm_results)],
                        duration_ms=0.0,
                    )
                )
    else:
        # Check for pre-existing LLM evaluation output
        existing_llm = _find_llm_evaluation_output(tool_root)
        if existing_llm:
            is_stale, age_days = _is_output_stale(existing_llm)
            evidence = [str(existing_llm)]
            if is_stale:
                evidence.append(
                    f"WARNING: Output is {age_days} days old (threshold: {STALE_THRESHOLD_DAYS} days)"
                )
            checks.append(
                CheckResult(
                    check_id="run.evaluate_llm",
                    status="pass",
                    severity="medium",
                    message="Pre-existing LLM evaluation output found" + (" (stale)" if is_stale else ""),
                    evidence=evidence,
                    duration_ms=0.0,
                )
            )
            if existing_llm.suffix == ".json":
                checks.append(_time_check(_check_llm_quality, existing_llm))
            else:
                candidate = tool_root / "evaluation" / "llm" / "results" / "llm_evaluation.json"
                if candidate.exists():
                    checks.append(_time_check(_check_llm_quality, candidate))
                else:
                    checks.append(
                        CheckResult(
                            check_id="evaluation.llm_quality",
                            status="fail",
                            severity="medium",
                            message="LLM evaluation JSON missing",
                            evidence=[str(candidate)],
                            duration_ms=0.0,
                        )
                    )
        else:
            checks.append(
                CheckResult(
                    check_id="run.evaluate_llm",
                    status="fail",
                    severity="medium",
                    message="No LLM evaluation output found - run with --run-llm or execute 'make evaluate-llm'",
                    evidence=[],
                    duration_ms=0.0,
                )
            )
            checks.append(
                CheckResult(
                    check_id="evaluation.llm_quality",
                    status="fail",
                    severity="medium",
                    message="LLM evaluation quality check skipped (no outputs)",
                    evidence=[],
                    duration_ms=0.0,
                )
            )

    load_start = time.perf_counter()
    output, error, output_source = _load_output_for_checks(tool_root, output_path)
    load_duration = (time.perf_counter() - load_start) * 1000.0
    if output is None:
        checks.append(
            CheckResult(
                check_id="output.load",
                status="fail",
                severity="high",
                message="No output.json available",
                evidence=[error or ""],
                duration_ms=round(load_duration, 2),
            )
        )
    else:
        checks.append(
            CheckResult(
                check_id="output.load",
                status="pass",
                severity="high",
                message="Output JSON loaded",
                evidence=[str(output_source)] if output_source else [],
                duration_ms=round(load_duration, 2),
            )
        )
        checks.append(_time_check(_check_output_paths, output))
        checks.append(_time_check(_check_data_completeness, output, tool_root.name))
        checks.append(_time_check(_check_path_consistency, output))
        meta_start = time.perf_counter()
        metadata_checks = _check_output_metadata(output)
        meta_duration = (time.perf_counter() - meta_start) * 1000.0
        checks.extend(_attach_duration_many(metadata_checks, meta_duration))
        checks.append(_time_check(_check_output_metadata_consistency, output))
        checks.append(_time_check(_check_schema_version_alignment, tool_root, output))
        if output_source:
            checks.append(_time_check(_check_output_schema, tool_root, output_source, venv))

    tool_name = tool_root.name
    # Derive project root from tool_root (tools are at src/tools/<name>)
    project_root = tool_root.parents[2] if len(tool_root.parents) > 2 else tool_root.parent

    checks.extend(
        [
            _time_check(_check_required_paths, tool_root),
            _time_check(_check_make_targets, tool_root),
            _time_check(_check_makefile_permissions, tool_root),
            _time_check(_check_makefile_uses_common, tool_root),
            _time_check(_check_output_dir_convention, tool_root),
            _time_check(_check_output_filename_convention, tool_root),
            _time_check(_check_schema_valid_json, tool_root),
            _time_check(_check_schema_contract, tool_root),
            _time_check(_check_blueprint_structure, tool_root),
            _time_check(_check_eval_strategy_structure, tool_root),
            _time_check(_check_check_modules, tool_root),
            _time_check(_check_llm_prompts, tool_root),
            _time_check(_check_llm_judge_count, tool_root),
            _time_check(_check_synthetic_evaluation_context, tool_root),
            _time_check(_check_ground_truth, tool_root),
            _time_check(_check_scorecard, tool_root),
            # Uniform evaluation pipeline checks
            _time_check(_check_programmatic_exists, tool_root),
            _time_check(_check_programmatic_schema, tool_root),
            _time_check(_check_programmatic_quality, tool_root),
            _time_check(_check_llm_exists, tool_root),
            _time_check(_check_llm_schema, tool_root),
            _time_check(_check_llm_includes_programmatic, tool_root),
            _time_check(_check_llm_decision_quality, tool_root),
            _time_check(_check_rollup_validation, tool_root),
            _time_check(_check_adapter_compliance, tool_root, tool_name),
            _time_check(_check_adapter_schema_alignment, tool_root, tool_name),
            _time_check(_check_adapter_integration, tool_root, tool_name),
            _time_check(_check_adapter_quality_rules_coverage, tool_root, tool_name),
            _time_check(_check_sot_adapter_registered, tool_root, tool_name),
            _time_check(_check_sot_schema_table, tool_root, tool_name),
            _time_check(_check_sot_orchestrator_wired, tool_root, tool_name),
            _time_check(_check_sot_dbt_staging_model, tool_root, tool_name),
            _time_check(_check_dbt_model_coverage, tool_root, tool_name),
            _time_check(_check_entity_repository_alignment, tool_root, tool_name),
            _time_check(_check_test_structure_naming, tool_root),
            _time_check(_check_cross_tool_join_patterns, project_root),
        ]
    )

    # Coverage check (separate due to conditional execution)
    checks.append(_time_check(_check_test_coverage_threshold, tool_root, env, run_coverage))

    status = "fail" if any(c.status == "fail" for c in checks) else "pass"
    for temp_dir in temp_dirs:
        shutil.rmtree(temp_dir, ignore_errors=True)
    return ToolResult(name=tool_root.name, status=status, checks=checks)


def find_tools(tools_root: Path) -> Iterable[Path]:
    for entry in sorted(tools_root.iterdir()):
        if not entry.is_dir():
            continue
        if (entry / "Makefile").exists():
            yield entry


def build_report(
    tools_root: Path,
    run_analysis: bool = False,
    run_evaluate: bool = False,
    run_llm: bool = False,
    run_coverage: bool = False,
    venv: Optional[str] = None,
    venv_map: Optional[dict[str, str]] = None,
    preflight: bool = False,
    single_tool: Optional[Path] = None,
) -> dict:
    if single_tool:
        # Scan only a single tool
        tool_results = [
            scan_tool(
                single_tool,
                run_analysis=run_analysis,
                run_evaluate=run_evaluate,
                run_llm=run_llm,
                run_coverage=run_coverage,
                venv=(venv_map or {}).get(single_tool.name, venv),
                preflight=preflight,
            )
        ]
    else:
        tool_results = [
            scan_tool(
                tool_root,
                run_analysis=run_analysis,
                run_evaluate=run_evaluate,
                run_llm=run_llm,
                run_coverage=run_coverage,
                venv=(venv_map or {}).get(tool_root.name, venv),
                preflight=preflight,
            )
            for tool_root in find_tools(tools_root)
        ]
    passed = sum(1 for t in tool_results if str(t.status).lower() == "pass")
    failed = sum(1 for t in tool_results if str(t.status).lower() == "fail")
    tools_payload = []
    for t in tool_results:
        normalized_checks = []
        for c in t.checks:
            status = c.status.lower() if isinstance(c.status, str) else c.status
            normalized_checks.append(
                {
                    **asdict(c),
                    "status": status,
                }
            )
        tool_status = "fail" if any(c["status"] == "fail" for c in normalized_checks) else "pass"
        tools_payload.append(
            {
                "name": t.name,
                "status": tool_status,
                "checks": normalized_checks,
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tools_root": str(tools_root),
        "summary": {
            "tool_count": len(tool_results),
            "passed": sum(1 for t in tools_payload if t["status"] == "pass"),
            "failed": sum(1 for t in tools_payload if t["status"] == "fail"),
        },
        "tools": tools_payload,
    }


def write_markdown(report: dict, output_path: Path) -> None:
    lines: List[str] = []
    lines.append("# Tool Compliance Report")
    lines.append("")
    lines.append(f"Generated: `{report['generated_at']}`")
    lines.append("")
    summary = report["summary"]
    lines.append(
        f"Summary: {summary['passed']} passed, {summary['failed']} failed, "
        f"{summary['tool_count']} total"
    )
    lines.append("")
    lines.append("| Tool | Status | Checks Passed | Checks Failed | Failed Check IDs |")
    lines.append("| --- | --- | --- | --- | --- |")
    for tool in report["tools"]:
        failed_checks = [c for c in tool["checks"] if c["status"] == "fail"]
        passed_checks = [c for c in tool["checks"] if c["status"] == "pass"]
        failed_ids = ", ".join(c["check_id"] for c in failed_checks) or "-"
        lines.append(
            f"| {tool['name']} | {tool['status']} | {len(passed_checks)} | {len(failed_checks)} | {failed_ids} |"
        )
    lines.append("")

    # Performance summary
    durations: list[tuple[str, str, float]] = []
    per_tool_totals: dict[str, float] = {}
    for tool in report["tools"]:
        tool_name = tool["name"]
        for check in tool["checks"]:
            duration = check.get("duration_ms")
            if isinstance(duration, (int, float)):
                per_tool_totals[tool_name] = per_tool_totals.get(tool_name, 0.0) + float(duration)
                durations.append((tool_name, check["check_id"], float(duration)))

    if durations:
        lines.append("## Performance Summary")
        lines.append("")
        lines.append("### Slowest Checks")
        lines.append("")
        lines.append("| Tool | Check ID | Duration (ms) |")
        lines.append("| --- | --- | --- |")
        for tool_name, check_id, duration in sorted(durations, key=lambda x: x[2], reverse=True)[:10]:
            lines.append(f"| {tool_name} | `{check_id}` | {duration:.2f} |")
        lines.append("")
        lines.append("### Total Time Per Tool")
        lines.append("")
        lines.append("| Tool | Total (s) |")
        lines.append("| --- | --- |")
        for tool_name, total_ms in sorted(per_tool_totals.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {tool_name} | {total_ms / 1000.0:.2f} |")
        lines.append("")

    for tool in report["tools"]:
        lines.append(f"## {tool['name']}")
        lines.append("")
        lines.append("| Check ID | Status | Severity | Duration (ms) | Message | Evidence | Stdout | Stderr |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for check in tool["checks"]:
            evidence = ", ".join(check["evidence"]) if check["evidence"] else "-"
            message = check["message"].replace("\n", " ").strip()
            duration = check.get("duration_ms")
            duration_display = f"{duration:.2f}" if isinstance(duration, (int, float)) else "-"
            stdout_summary = (check.get("stdout_summary") or "-").replace("\n", " ").strip()
            stderr_summary = (check.get("stderr_summary") or "-").replace("\n", " ").strip()
            lines.append(
                f"| `{check['check_id']}` | {check['status']} | {check['severity']} | {duration_display} | {message} | {evidence} | {stdout_summary} | {stderr_summary} |"
            )
        lines.append("")
    output_path.write_text("\n".join(lines).rstrip() + "\n")


def _parse_venv_map(raw: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    if not raw:
        return mapping
    for item in raw.split(","):
        if not item.strip():
            continue
        if "=" not in item:
            continue
        name, value = item.split("=", 1)
        mapping[name.strip()] = value.strip()
    return mapping


def main() -> int:
    parser = argparse.ArgumentParser(description="Tool compliance scanner")
    parser.add_argument(
        "--root",
        default=str(Path(__file__).parents[2]),
        help="Project root (default: repository root)",
    )
    parser.add_argument(
        "--tools-root",
        default="src/tools",
        help="Tools directory relative to project root",
    )
    parser.add_argument(
        "--out-json",
        default="docs/tool_compliance_report.json",
        help="Path for JSON report output",
    )
    parser.add_argument(
        "--out-md",
        default="docs/tool_compliance_report.md",
        help="Path for Markdown report output",
    )
    parser.add_argument(
        "--run-analysis",
        action="store_true",
        help="Execute make analyze before validating outputs",
    )
    parser.add_argument(
        "--run-evaluate",
        action="store_true",
        help="Execute make evaluate and verify evaluation outputs",
    )
    parser.add_argument(
        "--run-llm",
        action="store_true",
        help="Execute make evaluate-llm and verify LLM outputs",
    )
    parser.add_argument(
        "--run-coverage",
        action="store_true",
        help="Run pytest with coverage and verify >= 80%% threshold",
    )
    parser.add_argument(
        "--venv",
        default="",
        help="Virtualenv path to pass to Makefile (optional)",
    )
    parser.add_argument(
        "--venv-map",
        default="",
        help="Tool-specific venv mapping (e.g., scc=/tmp/scc-venv,lizard=/tmp/lizard-venv)",
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Fast preflight validation (~100ms) - structure and Makefile checks only",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress normal output; only show failures (useful for CI/hooks)",
    )
    parser.add_argument(
        "tool_path",
        nargs="?",
        default=None,
        help="Single tool path to scan (e.g., src/tools/scc). If provided, only this tool is scanned.",
    )
    args = parser.parse_args()

    project_root = Path(args.root).resolve()
    tools_root = (project_root / args.tools_root).resolve()
    default_venv = args.venv or None
    if not default_venv:
        candidate = project_root / ".venv"
        if candidate.exists():
            default_venv = str(candidate)

    # Handle single tool path argument
    single_tool: Optional[Path] = None
    if args.tool_path:
        single_tool = Path(args.tool_path).resolve()
        if not single_tool.exists():
            # Try relative to project root
            single_tool = (project_root / args.tool_path).resolve()
        if not single_tool.exists() or not single_tool.is_dir():
            print(f"Error: Tool path not found: {args.tool_path}", file=sys.stderr)
            return 1

    report = build_report(
        tools_root,
        run_analysis=args.run_analysis,
        run_evaluate=args.run_evaluate,
        run_llm=args.run_llm,
        run_coverage=args.run_coverage,
        venv=default_venv,
        venv_map=_parse_venv_map(args.venv_map),
        preflight=args.preflight,
        single_tool=single_tool,
    )

    # Write report files (unless in quiet mode with single tool)
    if not (args.quiet and single_tool):
        out_json = (project_root / args.out_json).resolve()
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True))

        out_md = (project_root / args.out_md).resolve()
        write_markdown(report, out_md)

    # In quiet mode, only print failures
    if args.quiet:
        failed_checks = []
        for tool in report["tools"]:
            for check in tool["checks"]:
                if check["status"] == "fail":
                    failed_checks.append((tool["name"], check["check_id"], check["message"]))
        if failed_checks:
            for tool_name, check_id, message in failed_checks:
                print(f"FAIL: {tool_name} - {check_id}: {message}", file=sys.stderr)
        return 0 if report["summary"]["failed"] == 0 else 1

    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
