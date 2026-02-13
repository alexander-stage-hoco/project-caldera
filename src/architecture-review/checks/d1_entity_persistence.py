"""D1: Entity & Persistence Pattern checks.

Validates frozen dataclasses, __post_init__ validation, adapter constants,
schema.sql alignment, and orchestrator registration.
"""

from __future__ import annotations

import re
from pathlib import Path

from discovery import ToolFiles
from models import Finding

DIMENSION = "entity_persistence_pattern"
WEIGHT = 0.20


def check_d1(tool_files: ToolFiles, project_root: Path) -> list[Finding]:
    """Run all D1 checks for a tool."""
    findings: list[Finding] = []

    entities_content = _read(tool_files.entities_file)
    adapter_content = _read(tool_files.adapter_file) if tool_files.adapter_file else None
    init_content = _read(tool_files.adapter_init)
    orch_content = _read(tool_files.orchestrator_file)
    schema_sql_content = _read(tool_files.schema_sql)
    repo_content = _read(tool_files.repositories_file)

    if not tool_files.entity_names:
        findings.append(Finding(
            severity="warning",
            rule_id="ENTITY_NOT_REGISTERED",
            message=f"No entities registered in common.yaml for tool '{tool_files.tool_name}'",
            category="missing_requirement",
        ))
        return findings

    findings.extend(_check_entity_frozen(entities_content, tool_files.entity_names, tool_files))
    findings.extend(_check_entity_post_init(entities_content, tool_files.entity_names, tool_files))
    findings.extend(_check_entity_run_pk(entities_content, tool_files.entity_names, tool_files))
    findings.extend(_check_entity_path_validated(entities_content, tool_files.entity_names, tool_files))

    if adapter_content is not None:
        findings.extend(_check_adapter_constants(adapter_content, tool_files))
        findings.extend(_check_adapter_base_class(adapter_content, tool_files))
        findings.extend(_check_adapter_schema_sql(adapter_content, schema_sql_content, tool_files))
    else:
        findings.append(Finding(
            severity="error",
            rule_id="ADAPTER_MISSING",
            message=f"Adapter file not found for tool '{tool_files.tool_name}'",
            category="missing_requirement",
        ))

    if tool_files.adapter_class:
        findings.extend(_check_adapter_exported(init_content, tool_files.adapter_class, tool_files))
        findings.extend(_check_orchestrator_registered(orch_content, tool_files.tool_name, tool_files.adapter_class, tool_files))

    if adapter_content is not None:
        findings.extend(_check_repo_table_whitelist(repo_content, adapter_content, tool_files))

    return findings


def _read(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text()


def _find_class_body(content: str, class_name: str) -> str:
    """Extract the body of a class from source content."""
    pattern = rf"class\s+{re.escape(class_name)}\b[^:]*:"
    match = re.search(pattern, content)
    if not match:
        return ""
    start = match.start()
    # Find the end of the class (next class/function at same indent, or EOF)
    lines = content[start:].split("\n")
    body_lines = [lines[0]]
    for line in lines[1:]:
        if line and not line[0].isspace() and not line.startswith("#"):
            break
        body_lines.append(line)
    return "\n".join(body_lines)


def _check_entity_frozen(content: str, entity_names: list[str], tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    for name in entity_names:
        # Look for @dataclass(frozen=True) immediately before the class
        pattern = rf"@dataclass\(frozen=True\)\s*\nclass\s+{re.escape(name)}\b"
        if not re.search(pattern, content):
            findings.append(Finding(
                severity="error",
                rule_id="ENTITY_FROZEN",
                message=f"Entity '{name}' is not declared with @dataclass(frozen=True)",
                category="pattern_violation",
                file=_rel(tf.entities_file),
                recommendation=f"Add @dataclass(frozen=True) to class {name}",
            ))
    return findings


def _check_entity_post_init(content: str, entity_names: list[str], tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    for name in entity_names:
        body = _find_class_body(content, name)
        if "__post_init__" not in body:
            findings.append(Finding(
                severity="warning",
                rule_id="ENTITY_POST_INIT",
                message=f"Entity '{name}' has no __post_init__ validation",
                category="pattern_violation",
                file=_rel(tf.entities_file),
                recommendation=f"Add __post_init__ to {name} for field validation",
            ))
    return findings


def _check_entity_run_pk(content: str, entity_names: list[str], tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    for name in entity_names:
        body = _find_class_body(content, name)
        if "run_pk:" not in body and "run_pk :" not in body:
            findings.append(Finding(
                severity="info",
                rule_id="ENTITY_RUN_PK",
                message=f"Entity '{name}' does not have a run_pk field (may use different key)",
                category="inconsistency",
                file=_rel(tf.entities_file),
            ))
    return findings


def _check_entity_path_validated(content: str, entity_names: list[str], tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    for name in entity_names:
        body = _find_class_body(content, name)
        has_path_field = "relative_path:" in body or "file_path:" in body
        has_validation = "_validate_relative_path" in body or "_validate_repo_relative_path" in body
        if has_path_field and not has_validation:
            findings.append(Finding(
                severity="warning",
                rule_id="ENTITY_PATH_VALIDATED",
                message=f"Entity '{name}' has a path field but no path validation in __post_init__",
                category="pattern_violation",
                file=_rel(tf.entities_file),
                recommendation="Add _validate_relative_path call in __post_init__",
            ))
    return findings


def _check_adapter_constants(content: str, tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    required = ["SCHEMA_PATH", "LZ_TABLES", "TABLE_DDL", "QUALITY_RULES"]
    for const in required:
        if not re.search(rf"^{re.escape(const)}\s*=", content, re.MULTILINE):
            findings.append(Finding(
                severity="error",
                rule_id="ADAPTER_CONSTANTS",
                message=f"Adapter missing required constant '{const}'",
                category="missing_requirement",
                file=_rel(tf.adapter_file),
                recommendation=f"Add module-level {const} constant to adapter",
            ))
    return findings


def _check_adapter_base_class(content: str, tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    if "(BaseAdapter)" not in content:
        findings.append(Finding(
            severity="error",
            rule_id="ADAPTER_BASE_CLASS",
            message="Adapter does not inherit from BaseAdapter",
            category="pattern_violation",
            file=_rel(tf.adapter_file),
            recommendation="Inherit from BaseAdapter",
        ))
    return findings


def _check_adapter_schema_sql(adapter_content: str, schema_sql_content: str, tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    # Extract table names from adapter's LZ_TABLES/TABLE_DDL
    table_pattern = r'"(lz_\w+)"'
    adapter_tables = set(re.findall(table_pattern, adapter_content))
    for table in adapter_tables:
        if table not in schema_sql_content:
            findings.append(Finding(
                severity="error",
                rule_id="ADAPTER_SCHEMA_SQL",
                message=f"Table '{table}' defined in adapter but not found in schema.sql",
                category="inconsistency",
                file=_rel(tf.schema_sql),
                recommendation=f"Add CREATE TABLE for {table} in schema.sql",
            ))
    return findings


def _check_adapter_exported(init_content: str, adapter_class: str, tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    if adapter_class not in init_content:
        findings.append(Finding(
            severity="error",
            rule_id="ADAPTER_EXPORTED",
            message=f"Adapter class '{adapter_class}' not exported in __init__.py",
            category="missing_requirement",
            file=_rel(tf.adapter_init),
            recommendation=f"Add {adapter_class} to adapters/__init__.py exports",
        ))
    return findings


def _check_orchestrator_registered(orch_content: str, tool_name: str, adapter_class: str, tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    # Check for ToolIngestionConfig("tool_name", AdapterClass, ...)
    if f'"{tool_name}"' not in orch_content or adapter_class not in orch_content:
        findings.append(Finding(
            severity="error",
            rule_id="ORCHESTRATOR_REGISTERED",
            message=f"Tool '{tool_name}' not registered in orchestrator TOOL_INGESTION_CONFIGS",
            category="missing_requirement",
            file=_rel(tf.orchestrator_file),
            recommendation=f"Add ToolIngestionConfig(\"{tool_name}\", {adapter_class}, ...) to TOOL_INGESTION_CONFIGS",
        ))
    return findings


def _check_repo_table_whitelist(repo_content: str, adapter_content: str, tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    # Extract table names from adapter
    table_pattern = r'"(lz_\w+)"'
    adapter_tables = set(re.findall(table_pattern, adapter_content))
    for table in adapter_tables:
        if table not in repo_content:
            findings.append(Finding(
                severity="warning",
                rule_id="REPO_TABLE_WHITELIST",
                message=f"Table '{table}' not found in repositories.py _VALID_LZ_TABLES",
                category="inconsistency",
                file=_rel(tf.repositories_file),
                recommendation=f"Add '{table}' to _VALID_LZ_TABLES in repositories.py",
            ))
    return findings


def _rel(path: Path | None) -> str | None:
    """Convert absolute path to a project-relative string."""
    if path is None:
        return None
    try:
        # Walk up to find project root (contains CLAUDE.md)
        p = path
        while p != p.parent:
            if (p / "CLAUDE.md").exists():
                return str(path.relative_to(p))
            p = p.parent
    except (ValueError, OSError):
        pass
    return str(path)
