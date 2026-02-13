"""D6: BLUEPRINT Alignment checks.

Validates required sections, no placeholder content, evaluation data populated,
and tool name reference.
"""

from __future__ import annotations

import re
from pathlib import Path

from discovery import ToolFiles
from models import Finding

DIMENSION = "blueprint_alignment"
WEIGHT = 0.15

REQUIRED_SECTIONS = [
    "Executive Summary",
    "Architecture",
    "Implementation Plan",
    "Configuration",
    "Performance",
    "Evaluation",
    "Risk",
]

PLACEHOLDER_PATTERNS = [
    r"\bTODO\b",
    r"\bFIXME\b",
    r"\bTBD\b",
    r"\[INSERT\b",
    r"\[PLACEHOLDER\b",
    r"\bXXX\b",
]


def check_d6(tool_files: ToolFiles) -> list[Finding]:
    """Run all D6 checks for a tool."""
    findings: list[Finding] = []

    if not tool_files.blueprint:
        findings.append(Finding(
            severity="error",
            rule_id="BLUEPRINT_MISSING",
            message="BLUEPRINT.md not found",
            category="missing_requirement",
        ))
        return findings

    content = tool_files.blueprint.read_text()
    findings.extend(_check_blueprint_sections(content, tool_files))
    findings.extend(_check_blueprint_no_placeholders(content, tool_files))
    findings.extend(_check_blueprint_has_eval_data(content, tool_files))
    findings.extend(_check_blueprint_tool_referenced(content, tool_files))

    return findings


def _check_blueprint_sections(content: str, tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    missing = []
    for section in REQUIRED_SECTIONS:
        # Check for markdown headers containing section name
        if not re.search(rf"^#+\s+.*{re.escape(section)}", content, re.MULTILINE | re.IGNORECASE):
            missing.append(section)
    if missing:
        findings.append(Finding(
            severity="warning",
            rule_id="BLUEPRINT_SECTIONS",
            message=f"BLUEPRINT.md missing sections: {missing}",
            category="missing_requirement",
            file=_rel(tf.blueprint),
            recommendation=f"Add markdown headers for: {missing}",
        ))
    return findings


def _check_blueprint_no_placeholders(content: str, tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    found = []
    for pattern in PLACEHOLDER_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        found.extend(matches)
    if found:
        findings.append(Finding(
            severity="warning",
            rule_id="BLUEPRINT_NO_PLACEHOLDERS",
            message=f"BLUEPRINT.md contains placeholder text: {found[:5]}",
            category="placeholder_content",
            file=_rel(tf.blueprint),
            recommendation="Replace placeholder text with actual content",
        ))
    return findings


def _check_blueprint_has_eval_data(content: str, tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    # Look for the Evaluation section and check for numeric data
    eval_match = re.search(r"^#+\s+.*Evaluation.*$", content, re.MULTILINE | re.IGNORECASE)
    if not eval_match:
        return findings

    eval_section = content[eval_match.start():]
    # Find next top-level header to delimit the section
    next_header = re.search(r"^#+\s+", eval_section[len(eval_match.group()):], re.MULTILINE)
    if next_header:
        eval_section = eval_section[:eval_match.end() - eval_match.start() + next_header.start()]

    # Check for numeric data (percentages, decimals)
    has_numbers = bool(re.search(r"\d+\.\d+", eval_section)) or bool(re.search(r"\d+%", eval_section))
    if not has_numbers:
        findings.append(Finding(
            severity="info",
            rule_id="BLUEPRINT_HAS_EVAL_DATA",
            message="BLUEPRINT Evaluation section has no numeric data (scores, percentages)",
            category="placeholder_content",
            file=_rel(tf.blueprint),
            recommendation="Populate Evaluation section with actual metric data",
        ))
    return findings


def _check_blueprint_tool_referenced(content: str, tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    if tf.tool_name not in content.lower():
        findings.append(Finding(
            severity="info",
            rule_id="BLUEPRINT_TOOL_REFERENCED",
            message=f"BLUEPRINT.md does not reference tool name '{tf.tool_name}'",
            category="inconsistency",
            file=_rel(tf.blueprint),
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
