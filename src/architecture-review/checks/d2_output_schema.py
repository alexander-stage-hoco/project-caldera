"""D2: Output Schema & Envelope checks.

Validates JSON Schema draft version, const schema_version, 8 metadata fields,
path normalization in analyze.py, CLI args pattern, and envelope creation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from discovery import ToolFiles
from models import Finding

DIMENSION = "output_schema_envelope"
WEIGHT = 0.20

REQUIRED_ENVELOPE_FIELDS = {
    "schema_version", "tool_name", "tool_version", "repo_id",
    "run_id", "branch", "commit", "timestamp",
}


def check_d2(tool_files: ToolFiles) -> list[Finding]:
    """Run all D2 checks for a tool."""
    findings: list[Finding] = []

    if tool_files.output_schema:
        schema_content = tool_files.output_schema.read_text()
        findings.extend(_check_schema_draft_2020(schema_content, tool_files))
        findings.extend(_check_schema_version_const(schema_content, tool_files))
        findings.extend(_check_envelope_8_fields(schema_content, tool_files))
    else:
        findings.append(Finding(
            severity="error",
            rule_id="SCHEMA_MISSING",
            message="output.schema.json not found",
            category="missing_requirement",
        ))

    if tool_files.analyze_py:
        analyze_content = tool_files.analyze_py.read_text()
        findings.extend(_check_analyze_path_norm(analyze_content, tool_files))
        findings.extend(_check_analyze_cli_args(analyze_content, tool_files))
        findings.extend(_check_analyze_envelope(analyze_content, tool_files))
    else:
        findings.append(Finding(
            severity="error",
            rule_id="ANALYZE_MISSING",
            message="scripts/analyze.py not found",
            category="missing_requirement",
        ))

    return findings


def _check_schema_draft_2020(content: str, tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    try:
        schema = json.loads(content)
    except json.JSONDecodeError:
        findings.append(Finding(
            severity="error",
            rule_id="SCHEMA_INVALID_JSON",
            message="output.schema.json is not valid JSON",
            category="pattern_violation",
            file=_rel(tf.output_schema),
        ))
        return findings

    draft = schema.get("$schema", "")
    if "2020-12" not in draft:
        findings.append(Finding(
            severity="warning",
            rule_id="SCHEMA_DRAFT_2020",
            message=f"Schema uses '{draft}' instead of Draft 2020-12",
            category="pattern_violation",
            file=_rel(tf.output_schema),
            evidence=f'"$schema": "{draft}"',
            recommendation='Use "$schema": "https://json-schema.org/draft/2020-12/schema"',
        ))
    return findings


def _check_schema_version_const(content: str, tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    try:
        schema = json.loads(content)
    except json.JSONDecodeError:
        return findings

    # Navigate to properties.metadata.properties.schema_version (envelope nesting)
    metadata_props = (
        schema.get("properties", {})
        .get("metadata", {})
        .get("properties", {})
    )
    sv = metadata_props.get("schema_version", {})
    if not sv:
        # Fallback: check top-level properties (flat schema)
        sv = schema.get("properties", {}).get("schema_version", {})
    if "const" not in sv:
        findings.append(Finding(
            severity="warning",
            rule_id="SCHEMA_VERSION_CONST",
            message="schema_version should use 'const' not 'pattern' or 'enum'",
            category="pattern_violation",
            file=_rel(tf.output_schema),
            recommendation='Use {"const": "1.0.0"} for schema_version',
        ))
    return findings


def _check_envelope_8_fields(content: str, tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    try:
        schema = json.loads(content)
    except json.JSONDecodeError:
        return findings

    # Envelope fields live inside properties.metadata (nested structure)
    metadata_schema = schema.get("properties", {}).get("metadata", {})
    required = set(metadata_schema.get("required", []))
    props = set(metadata_schema.get("properties", {}).keys())
    all_fields = required | props
    if not all_fields:
        # Fallback: check top-level (flat schema)
        required = set(schema.get("required", []))
        props = set(schema.get("properties", {}).keys())
        all_fields = required | props

    missing = REQUIRED_ENVELOPE_FIELDS - all_fields
    if missing:
        findings.append(Finding(
            severity="warning",
            rule_id="ENVELOPE_8_FIELDS",
            message=f"Schema missing envelope fields: {sorted(missing)}",
            category="missing_requirement",
            file=_rel(tf.output_schema),
            recommendation=f"Add {sorted(missing)} to schema properties and required",
        ))
    return findings


def _check_analyze_path_norm(content: str, tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    has_shared = "from shared.path_utils import" in content
    has_common = "from common.path_normalization import" in content
    if not has_shared and not has_common:
        # Downgrade to info if tool uses common modules (normalization may be elsewhere)
        uses_common = "from common." in content
        findings.append(Finding(
            severity="info" if uses_common else "warning",
            rule_id="ANALYZE_PATH_NORM",
            message="analyze.py does not import path normalization utilities",
            category="missing_requirement",
            file=_rel(tf.analyze_py),
            recommendation="Import from shared.path_utils or common.path_normalization",
        ))
    return findings


def _check_analyze_cli_args(content: str, tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    has_common_args = "add_common_args" in content
    has_many_args = len(re.findall(r"add_argument|click\.option|click\.argument", content)) >= 7
    if not has_common_args and not has_many_args:
        findings.append(Finding(
            severity="info",
            rule_id="ANALYZE_CLI_ARGS",
            message="analyze.py does not use add_common_args or define sufficient CLI arguments",
            category="pattern_violation",
            file=_rel(tf.analyze_py),
            recommendation="Use common.cli_parser.add_common_args for standard CLI arguments",
        ))
    return findings


def _check_analyze_envelope(content: str, tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    has_envelope = "create_envelope" in content
    has_manual = "schema_version" in content and "tool_name" in content
    has_delegated = "result_to_output" in content or "to_envelope" in content
    if not has_envelope and not has_manual and not has_delegated:
        findings.append(Finding(
            severity="warning",
            rule_id="ANALYZE_ENVELOPE",
            message="analyze.py does not use create_envelope or manually build envelope",
            category="missing_requirement",
            file=_rel(tf.analyze_py),
            recommendation="Use common.envelope_formatter.create_envelope",
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
