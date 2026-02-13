"""D3: Code Conventions checks.

Validates __future__ annotations, PEP 604 unions, type hints,
Makefile includes, and venv readiness.
"""

from __future__ import annotations

import re
from pathlib import Path

from discovery import ToolFiles
from models import Finding

DIMENSION = "code_conventions"
WEIGHT = 0.15


def check_d3(tool_files: ToolFiles) -> list[Finding]:
    """Run all D3 checks for a tool."""
    findings: list[Finding] = []

    # Collect Python files in the tool's scripts directory
    py_files = _collect_python_files(tool_files)
    for py_file in py_files:
        content = py_file.read_text()
        findings.extend(_check_future_annotations(content, py_file))
        findings.extend(_check_pep604_unions(content, py_file))

    if tool_files.makefile:
        makefile_content = tool_files.makefile.read_text()
        findings.extend(_check_makefile_common(makefile_content, tool_files))
        findings.extend(_check_makefile_venv_ready(makefile_content, tool_files))
    else:
        findings.append(Finding(
            severity="error",
            rule_id="MAKEFILE_MISSING",
            message="Makefile not found",
            category="missing_requirement",
        ))

    return findings


def _collect_python_files(tool_files: ToolFiles) -> list[Path]:
    """Collect key Python files from the tool directory."""
    files: list[Path] = []
    scripts_dir = tool_files.tool_dir / "scripts"
    if scripts_dir.exists():
        files.extend(scripts_dir.glob("*.py"))
    return files


def _check_future_annotations(content: str, py_file: Path) -> list[Finding]:
    findings: list[Finding] = []
    if "from __future__ import annotations" not in content:
        findings.append(Finding(
            severity="info",
            rule_id="FUTURE_ANNOTATIONS",
            message=f"Missing 'from __future__ import annotations'",
            category="pattern_violation",
            file=_rel(py_file),
            recommendation="Add 'from __future__ import annotations' at top of file",
        ))
    return findings


def _check_pep604_unions(content: str, py_file: Path) -> list[Finding]:
    findings: list[Finding] = []
    # Check for Optional[...] usage (should use X | None instead)
    if re.search(r"\bOptional\[", content):
        findings.append(Finding(
            severity="info",
            rule_id="PEP604_UNIONS",
            message="Uses Optional[X] instead of PEP 604 'X | None' syntax",
            category="pattern_violation",
            file=_rel(py_file),
            recommendation="Replace Optional[X] with X | None",
        ))
    return findings


def _check_makefile_common(content: str, tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    if "Makefile.common" not in content:
        findings.append(Finding(
            severity="warning",
            rule_id="MAKEFILE_COMMON",
            message="Makefile does not include Makefile.common",
            category="pattern_violation",
            file=_rel(tf.makefile),
            recommendation="Add 'include ../../Makefile.common' to Makefile",
        ))
    return findings


def _check_makefile_venv_ready(content: str, tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    # Check for VENV variable or .venv reference
    has_venv = "VENV" in content or ".venv" in content
    if not has_venv:
        findings.append(Finding(
            severity="info",
            rule_id="MAKEFILE_VENV_READY",
            message="Makefile does not reference VENV or .venv",
            category="pattern_violation",
            file=_rel(tf.makefile),
            recommendation="Use $(VENV) variable for Python paths in Makefile",
        ))
    return findings


def _rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        p = path
        while p != p.parent:
            if (p / "CLAUDE.md").exists():
                return str(path.relative_to(p))
            p = p.parent
    except (ValueError, OSError):
        pass
    return str(path)
