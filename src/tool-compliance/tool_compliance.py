"""Tool compliance scanner for Project Caldera."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import shutil
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Optional

# Threshold for staleness warnings on pre-existing outputs
STALE_THRESHOLD_DAYS = 14


REQUIRED_PATHS = [
    "Makefile",
    "README.md",
    "BLUEPRINT.md",
    "EVAL_STRATEGY.md",
    "requirements.txt",
    "scripts/analyze.py",
    "scripts/evaluate.py",
    "scripts/checks",
    "schemas/output.schema.json",
    "eval-repos/synthetic",
    "eval-repos/real",
    "evaluation/ground-truth",
    "evaluation/llm/orchestrator.py",
    "evaluation/llm/judges",
    "evaluation/llm/prompts",
    "evaluation/scorecard.md",
    "tests/unit",
    "tests/integration",
]

REQUIRED_MAKE_TARGETS = {
    "setup",
    "analyze",
    "evaluate",
    "evaluate-llm",
    "test",
    "clean",
}

TOOL_RULES = {
    "scc": {
        "required_check_modules": [
            "cocomo.py",
            "coverage.py",
            "directory_analysis.py",
            "installation.py",
            "integration_fit.py",
            "license.py",
            "output_quality.py",
            "per_file.py",
            "performance.py",
            "reliability.py",
        ],
        "required_prompts": [
            "api_design.md",
            "code_quality.md",
            "comparative.md",
            "directory_analysis.md",
            "documentation.md",
            "edge_cases.md",
            "error_messages.md",
            "integration_fit.md",
            "risk.md",
            "statistics.md",
        ],
        "ground_truth_mode": "synthetic_json",
        "evaluation_outputs": [
            "scorecard.md",
            "checks.json",
        ],
        "adapter": ("persistence.adapters.scc_adapter", "SccAdapter"),
    },
    "lizard": {
        "required_check_modules": [
            "accuracy.py",
            "coverage.py",
            "edge_cases.py",
            "performance.py",
        ],
        "required_prompts": [
            "ccn_accuracy.md",
            "function_detection.md",
            "hotspot_ranking.md",
            "statistics.md",
        ],
        "ground_truth_mode": "per_language",
        "evaluation_outputs": [
            "scorecard.md",
            "evaluation_report.json",
        ],
        "adapter": ("persistence.adapters.lizard_adapter", "LizardAdapter"),
    },
    "layout-scanner": {
        "required_check_modules": [
            "accuracy.py",
            "classification.py",
            "content_metadata.py",
            "edge_cases.py",
            "git_metadata.py",
            "output_quality.py",
            "performance.py",
            "scc_comparison.py",
        ],
        "required_prompts": [
            "classification_reasoning.md",
            "directory_taxonomy.md",
            "hierarchy_consistency.md",
            "language_detection.md",
        ],
        "adapter": ("persistence.adapters.layout_adapter", "LayoutAdapter"),
    },
    "semgrep": {
        "required_check_modules": [
            "accuracy.py",
            "coverage.py",
            "edge_cases.py",
            "integration_fit.py",
            "output_quality.py",
            "performance.py",
            "security.py",
        ],
        "required_prompts": [
            "actionability.md",
            "false_positive_rate.md",
            "rule_coverage.md",
            "smell_accuracy.md",
        ],
        "adapter": ("persistence.adapters.semgrep_adapter", "SemgrepAdapter"),
    },
    "roslyn-analyzers": {
        "required_check_modules": [
            "accuracy.py",
            "coverage.py",
            "edge_cases.py",
            "performance.py",
        ],
        "required_prompts": [
            "actionability.md",
            "detection_accuracy.md",
            "false_positive_rate.md",
            "security_coverage.md",
        ],
        "adapter": ("persistence.adapters.roslyn_adapter", "RoslynAdapter"),
    },
    "trivy": {
        "required_check_modules": [
            "accuracy.py",
            "detection.py",
            "freshness.py",
            "iac.py",
            "integration.py",
            "output_quality.py",
            "performance.py",
        ],
        "required_prompts": [
            "actionability.md",
            "coverage_completeness.md",
            "false_positive_rate.md",
            "freshness_quality.md",
            "iac_quality.md",
            "sbom_completeness.md",
            "severity_accuracy.md",
            "vulnerability_accuracy.md",
            "vulnerability_detection.md",
        ],
        "adapter": ("persistence.adapters.trivy_adapter", "TrivyAdapter"),
    },
    "sonarqube": {
        "required_check_modules": [
            "accuracy.py",
            "completeness.py",
            "coverage.py",
            "edge_cases.py",
            "performance.py",
        ],
        "required_prompts": [
            "issue_accuracy.md",
            "coverage_completeness.md",
            "actionability.md",
        ],
        "adapter": ("persistence.adapters.sonarqube_adapter", "SonarqubeAdapter"),
    },
    "git-sizer": {
        "required_check_modules": [
            "accuracy.py",
            "coverage.py",
            "edge_cases.py",
            "performance.py",
        ],
        "required_prompts": [
            "size_accuracy.md",
            "threshold_quality.md",
            "actionability.md",
            "integration_fit.md",
        ],
        "ground_truth_mode": "per_language",
        "evaluation_outputs": [
            "scorecard.md",
        ],
        "adapter": ("persistence.adapters.git_sizer_adapter", "GitSizerAdapter"),
    },
}

# Entity-to-repository mapping for entity.repository_alignment check
TOOL_ENTITIES = {
    "scc": ["SccFileMetric"],
    "lizard": ["LizardFileMetric", "LizardFunctionMetric"],
    "semgrep": ["SemgrepSmell"],
    "roslyn-analyzers": ["RoslynViolation"],
    "layout-scanner": ["LayoutFile", "LayoutDirectory"],
    "trivy": ["TrivyVulnerability", "TrivyTarget", "TrivyIacMisconfig"],
    "sonarqube": ["SonarqubeIssue", "SonarqubeMetric"],
    "git-sizer": ["GitSizerMetric", "GitSizerViolation", "GitSizerLfsCandidate"],
}

ENTITY_REPOSITORY_MAP = {
    "SccFileMetric": ("SccRepository", "insert_file_metrics"),
    "LizardFileMetric": ("LizardRepository", "insert_file_metrics"),
    "LizardFunctionMetric": ("LizardRepository", "insert_function_metrics"),
    "SemgrepSmell": ("SemgrepRepository", "insert_smells"),
    "RoslynViolation": ("RoslynRepository", "insert_violations"),
    "LayoutFile": ("LayoutRepository", "insert_files"),
    "LayoutDirectory": ("LayoutRepository", "insert_directories"),
    "TrivyVulnerability": ("TrivyRepository", "insert_vulnerabilities"),
    "TrivyTarget": ("TrivyRepository", "insert_targets"),
    "TrivyIacMisconfig": ("TrivyRepository", "insert_iac_misconfigs"),
    "SonarqubeIssue": ("SonarqubeRepository", "insert_issues"),
    "SonarqubeMetric": ("SonarqubeRepository", "insert_metrics"),
    "GitSizerMetric": ("GitSizerRepository", "insert_metrics"),
    "GitSizerViolation": ("GitSizerRepository", "insert_violations"),
    "GitSizerLfsCandidate": ("GitSizerRepository", "insert_lfs_candidates"),
}

SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")

# Key patterns for path detection
_PATH_KEY_PATTERNS = {"path", "file", "dir", "folder", "location", "source"}
_EXCLUDED_KEY_PATTERNS = {"endpoint", "url", "uri", "href", "schema", "ref", "api"}

# Patterns that indicate implementation of specific quality rules
QUALITY_RULE_PATTERNS = {
    "paths": ["is_repo_relative", "normalize_file_path", "path invalid", "normalize_dir_path"],
    "ranges": ["check_non_negative", ">= 0", "<= ", "must be"],
    "ratios": ["check_ratio", "ratio", "/ 0", "division"],
    "required_fields": ["check_required", "is None", "required"],
    "line_numbers": ["line_start", "line_end", ">= 1"],
}


@dataclass
class CheckResult:
    check_id: str
    status: str
    severity: str
    message: str
    evidence: list[str]


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
    """Find LLM evaluation output (results directory with content)."""
    llm_results = tool_root / "evaluation" / "llm" / "results"
    if llm_results.exists():
        # Check for any result files
        result_files = list(llm_results.glob("*.json")) + list(llm_results.glob("*.md"))
        if result_files:
            # Return the most recent one
            return max(result_files, key=lambda p: p.stat().st_mtime)
    return None


def _run_make(tool_root: Path, target: str, env: dict[str, str]) -> Optional[str]:
    result = subprocess.run(
        ["make", target],
        cwd=tool_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return result.stdout.strip()
    return None


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


def _check_check_modules(tool_root: Path) -> CheckResult:
    rules = TOOL_RULES.get(tool_root.name, {})
    expected = rules.get("required_check_modules")
    if not expected:
        return CheckResult(
            check_id="evaluation.check_modules",
            status="fail",
            severity="high",
            message="No check module requirements configured",
            evidence=[],
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
    rules = TOOL_RULES.get(tool_root.name, {})
    expected = rules.get("required_prompts")
    if not expected:
        return CheckResult(
            check_id="evaluation.llm_prompts",
            status="fail",
            severity="high",
            message="No LLM prompt requirements configured",
            evidence=[],
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
    try:
        import jsonschema  # type: ignore
    except ImportError:
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
    # Split by comma, handling constraints
    for line in body.split(","):
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
    )
    repos = {
        "scc": SccRepository,
        "lizard": LizardRepository,
        "semgrep": SemgrepRepository,
        "roslyn-analyzers": RoslynRepository,
        "trivy": TrivyRepository,
        "sonarqube": SonarqubeRepository,
        "git-sizer": GitSizerRepository,
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
    sys.path.insert(0, str(project_root / "src" / "sot-engine"))
    sys.path.insert(0, str(project_root / "src"))

    missing: list[str] = []

    try:
        from persistence import entities as entity_module
        from persistence import repositories as repo_module
        import dataclasses

        for entity_name in entities:
            # Check entity exists and is frozen dataclass
            entity_cls = getattr(entity_module, entity_name, None)
            if entity_cls is None:
                missing.append(f"{entity_name}: entity class not found")
                continue

            if not dataclasses.is_dataclass(entity_cls):
                missing.append(f"{entity_name}: not a dataclass")
                continue

            # Check if frozen
            if not entity_cls.__dataclass_fields__:
                missing.append(f"{entity_name}: no dataclass fields")
                continue

            # Check frozen attribute via dataclass params
            try:
                # Access the frozen parameter from dataclass
                if not getattr(entity_cls, "__dataclass_params__", None):
                    # For older dataclass versions, try to detect immutability
                    pass
                else:
                    params = entity_cls.__dataclass_params__
                    if hasattr(params, "frozen") and not params.frozen:
                        missing.append(f"{entity_name}: dataclass not frozen")
                        continue
            except Exception:
                pass  # Can't verify frozen status, continue

            # Check repository mapping
            repo_mapping = ENTITY_REPOSITORY_MAP.get(entity_name)
            if not repo_mapping:
                missing.append(f"{entity_name}: no repository mapping defined")
                continue

            repo_name, method_name = repo_mapping
            repo_cls = getattr(repo_module, repo_name, None)
            if repo_cls is None:
                missing.append(f"{entity_name}: repository {repo_name} not found")
                continue

            if not hasattr(repo_cls, method_name):
                missing.append(f"{entity_name}: repository missing {method_name} method")
                continue

    except ImportError as exc:
        return CheckResult(
            check_id="entity.repository_alignment",
            status="fail",
            severity="high",
            message=f"Failed to import persistence modules: {exc}",
            evidence=[str(exc)],
        )

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


def scan_tool(
    tool_root: Path,
    run_analysis: bool = False,
    run_evaluate: bool = False,
    run_llm: bool = False,
    venv: Optional[str] = None,
) -> ToolResult:
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
        error = _run_make(tool_root, "analyze", env)
        if error:
            checks.append(
                CheckResult(
                    check_id="run.analyze",
                    status="fail",
                    severity="critical",
                    message="make analyze failed",
                    evidence=[error],
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
                )
            )

    if run_evaluate:
        eval_output_dir = Path(tempfile.mkdtemp(prefix="tool-compliance-eval-"))
        temp_dirs.append(eval_output_dir)
        env["EVAL_OUTPUT_DIR"] = str(eval_output_dir)
        env["VENV_READY"] = str(eval_output_dir / ".venv_ready")
        env["SKIP_SETUP"] = "1"
        error = _run_make(tool_root, "evaluate", env)
        if error:
            checks.append(
                CheckResult(
                    check_id="run.evaluate",
                    status="fail",
                    severity="high",
                    message="make evaluate failed",
                    evidence=[error],
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
                )
            )

    if run_llm:
        error = _run_make(tool_root, "evaluate-llm", env)
        if error:
            checks.append(
                CheckResult(
                    check_id="run.evaluate_llm",
                    status="fail",
                    severity="medium",
                    message="make evaluate-llm failed",
                    evidence=[error],
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
                )
            )
            expected = tool_root / "evaluation" / "results" / "llm_evaluation.json"
            if not expected.exists():
                checks.append(
                    CheckResult(
                        check_id="evaluation.llm_results",
                        status="fail",
                        severity="medium",
                        message="LLM evaluation output missing",
                        evidence=["evaluation/results/llm_evaluation.json"],
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
                )
            )

    output, error, output_source = _load_output_for_checks(tool_root, output_path)
    if output is None:
        checks.append(
            CheckResult(
                check_id="output.load",
                status="fail",
                severity="high",
                message="No output.json available",
                evidence=[error or ""],
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
            )
        )
        checks.append(_check_output_paths(output))
        checks.extend(_check_output_metadata(output))
        checks.append(_check_output_metadata_consistency(output))
        checks.append(_check_schema_version_alignment(tool_root, output))
        if output_source:
            checks.append(_check_output_schema(tool_root, output_source, venv))

    tool_name = tool_root.name
    checks.extend(
        [
            _check_required_paths(tool_root),
            _check_make_targets(tool_root),
            _check_schema_valid_json(tool_root),
            _check_schema_contract(tool_root),
            _check_check_modules(tool_root),
            _check_llm_prompts(tool_root),
            _check_ground_truth(tool_root),
            _check_scorecard(tool_root),
            _check_rollup_validation(tool_root),
            _check_adapter_compliance(tool_root, tool_name),
            _check_adapter_schema_alignment(tool_root, tool_name),
            _check_adapter_integration(tool_root, tool_name),
            _check_adapter_quality_rules_coverage(tool_root, tool_name),
            _check_dbt_model_coverage(tool_root, tool_name),
            _check_entity_repository_alignment(tool_root, tool_name),
            _check_test_structure_naming(tool_root),
        ]
    )

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
    venv: Optional[str] = None,
    venv_map: Optional[dict[str, str]] = None,
) -> dict:
    tool_results = [
        scan_tool(
            tool_root,
            run_analysis=run_analysis,
            run_evaluate=run_evaluate,
            run_llm=run_llm,
            venv=(venv_map or {}).get(tool_root.name, venv),
        )
        for tool_root in find_tools(tools_root)
    ]
    passed = sum(1 for t in tool_results if t.status == "pass")
    failed = sum(1 for t in tool_results if t.status == "fail")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tools_root": str(tools_root),
        "summary": {
            "tool_count": len(tool_results),
            "passed": passed,
            "failed": failed,
        },
        "tools": [
            {
                "name": t.name,
                "status": t.status,
                "checks": [asdict(c) for c in t.checks],
            }
            for t in tool_results
        ],
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
    lines.append("| Tool | Status | Failed Checks |")
    lines.append("| --- | --- | --- |")
    for tool in report["tools"]:
        failed_checks = [c for c in tool["checks"] if c["status"] == "fail"]
        failed_ids = ", ".join(c["check_id"] for c in failed_checks) or "-"
        lines.append(f"| {tool['name']} | {tool['status']} | {failed_ids} |")
    lines.append("")
    for tool in report["tools"]:
        failed_checks = [c for c in tool["checks"] if c["status"] == "fail"]
        if not failed_checks:
            continue
        lines.append(f"## {tool['name']} failures")
        for check in failed_checks:
            evidence = ", ".join(check["evidence"]) if check["evidence"] else "-"
            lines.append(
                f"- `{check['check_id']}` ({check['severity']}): {check['message']} "
                f"[{evidence}]"
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
        default=str(Path(__file__).parents[1]),
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
        "--venv",
        default="",
        help="Virtualenv path to pass to Makefile (optional)",
    )
    parser.add_argument(
        "--venv-map",
        default="",
        help="Tool-specific venv mapping (e.g., scc=/tmp/scc-venv,lizard=/tmp/lizard-venv)",
    )
    args = parser.parse_args()

    project_root = Path(args.root).resolve()
    tools_root = (project_root / args.tools_root).resolve()
    report = build_report(
        tools_root,
        run_analysis=args.run_analysis,
        run_evaluate=args.run_evaluate,
        run_llm=args.run_llm,
        venv=args.venv or None,
        venv_map=_parse_venv_map(args.venv_map),
    )

    out_json = (project_root / args.out_json).resolve()
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True))

    out_md = (project_root / args.out_md).resolve()
    write_markdown(report, out_md)

    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
