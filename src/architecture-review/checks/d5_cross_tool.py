"""D5: Cross-Tool Consistency checks.

Validates envelope reference consistency, naming formula adherence,
adapter structure drift, and eval strategy format across all tools.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from discovery import ToolFiles, discover_tool_files, list_all_tools
from models import Finding

DIMENSION = "cross_tool_consistency"
WEIGHT = 0.15

REQUIRED_METADATA_FIELDS = {
    # Caldera envelope metadata fields (docs/REFERENCE.md)
    "tool_name",
    "tool_version",
    "run_id",
    "repo_id",
    "branch",
    "commit",
    "timestamp",
    "schema_version",
}

ADAPTER_REQUIRED_CONSTANTS = {"SCHEMA_PATH", "LZ_TABLES", "TABLE_DDL", "QUALITY_RULES"}

EVAL_STRATEGY_SECTIONS = [
    "Philosophy", "Dimension Summary", "Check Catalog",
    "Scoring", "Decision Thresholds", "Ground Truth",
]


def check_d5(project_root: Path) -> list[Finding]:
    """Run all D5 cross-tool consistency checks."""
    findings: list[Finding] = []
    tools = list_all_tools(project_root)

    findings.extend(_check_envelope_reference(tools, project_root))
    findings.extend(_check_naming_formula(tools, project_root))
    findings.extend(_check_adapter_structure_drift(tools, project_root))
    findings.extend(_check_eval_strategy_format(tools, project_root))

    return findings


def _resolve_local_ref(schema: dict, ref: str) -> dict | None:
    """Resolve a local JSON pointer ref within a schema dict.

    Supports refs like '#/$defs/metadata'. Returns None if unsupported.
    """
    if not ref.startswith("#/"):
        return None
    node: object = schema
    for part in ref[2:].split("/"):
        if not isinstance(node, dict):
            return None
        part = part.replace("~1", "/").replace("~0", "~")
        node = node.get(part)
    return node if isinstance(node, dict) else None


def _get_metadata_schema(schema: dict) -> dict | None:
    """Extract the schema node for the envelope's metadata object."""
    root_props = schema.get("properties", {}) if isinstance(schema.get("properties", {}), dict) else {}
    metadata = root_props.get("metadata")
    if not isinstance(metadata, dict):
        return None
    if "$ref" in metadata and isinstance(metadata["$ref"], str):
        resolved = _resolve_local_ref(schema, metadata["$ref"])
        return resolved
    return metadata


def _check_envelope_reference(tools: list[str], project_root: Path) -> list[Finding]:
    """Check that all tool schemas include the standard envelope metadata fields."""
    findings: list[Finding] = []
    for tool in tools:
        tf = discover_tool_files(tool, project_root)
        if not tf.output_schema:
            continue
        try:
            schema = json.loads(tf.output_schema.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        metadata_schema = _get_metadata_schema(schema)
        if not metadata_schema:
            findings.append(Finding(
                severity="warning",
                rule_id="ENVELOPE_REFERENCE",
                message=f"Tool '{tool}' schema missing 'metadata' object definition",
                category="inconsistency",
                file=_rel(tf.output_schema),
            ))
            continue

        metadata_props = set(metadata_schema.get("properties", {}).keys())
        metadata_required = set(metadata_schema.get("required", []))
        all_fields = metadata_props | metadata_required
        missing = REQUIRED_METADATA_FIELDS - all_fields
        if missing:
            findings.append(Finding(
                severity="warning",
                rule_id="ENVELOPE_REFERENCE",
                message=f"Tool '{tool}' schema missing metadata fields: {sorted(missing)}",
                category="inconsistency",
                file=_rel(tf.output_schema),
            ))
    return findings


def _expected_class_name(tool_name: str) -> str:
    """Convert tool name to expected adapter class name.

    Formula: hyphen-separated words → PascalCase + 'Adapter'
    e.g., 'pmd-cpd' → 'PmdCpdAdapter', 'scc' → 'SccAdapter'
    """
    parts = tool_name.split("-")
    pascal = "".join(p.capitalize() for p in parts)
    return f"{pascal}Adapter"


def _check_naming_formula(tools: list[str], project_root: Path) -> list[Finding]:
    """Check that adapter class names follow the naming formula."""
    findings: list[Finding] = []
    for tool in tools:
        tf = discover_tool_files(tool, project_root)
        if not tf.adapter_class:
            continue
        expected = _expected_class_name(tool)
        if tf.adapter_class != expected:
            findings.append(Finding(
                severity="info",
                rule_id="NAMING_FORMULA",
                message=f"Tool '{tool}': adapter class '{tf.adapter_class}' != expected '{expected}'",
                category="naming_drift",
            ))
    return findings


def _check_adapter_structure_drift(tools: list[str], project_root: Path) -> list[Finding]:
    """Check that all adapters define the required module-level constants."""
    findings: list[Finding] = []
    for tool in tools:
        tf = discover_tool_files(tool, project_root)
        if not tf.adapter_file:
            continue
        content = tf.adapter_file.read_text()
        defined = set()
        for const in ADAPTER_REQUIRED_CONSTANTS:
            if re.search(rf"^{re.escape(const)}\s*=", content, re.MULTILINE):
                defined.add(const)
        missing = ADAPTER_REQUIRED_CONSTANTS - defined
        if missing:
            findings.append(Finding(
                severity="warning",
                rule_id="ADAPTER_STRUCTURE_DRIFT",
                message=f"Tool '{tool}' adapter missing constants: {sorted(missing)}",
                category="inconsistency",
                file=_rel(tf.adapter_file),
            ))
    return findings


def _check_eval_strategy_format(tools: list[str], project_root: Path) -> list[Finding]:
    """Check that EVAL_STRATEGY.md files have required sections."""
    findings: list[Finding] = []
    for tool in tools:
        tf = discover_tool_files(tool, project_root)
        if not tf.eval_strategy:
            continue
        content = tf.eval_strategy.read_text()
        missing_sections = []
        for section in EVAL_STRATEGY_SECTIONS:
            if section not in content:
                missing_sections.append(section)
        if missing_sections:
            findings.append(Finding(
                severity="info",
                rule_id="EVAL_STRATEGY_FORMAT",
                message=f"Tool '{tool}' EVAL_STRATEGY.md missing sections: {missing_sections}",
                category="missing_requirement",
                file=_rel(tf.eval_strategy),
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
