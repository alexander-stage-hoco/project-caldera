"""File discovery protocol for architecture reviews.

Resolves all relevant file paths for a given tool by reading the tool-compliance
YAML configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ToolFiles:
    """Resolved file paths and metadata for a tool."""

    tool_name: str
    tool_dir: Path
    adapter_file: Path | None
    entity_names: list[str]
    adapter_class: str | None
    repo_class: str | None
    entities_file: Path
    repositories_file: Path
    schema_sql: Path
    orchestrator_file: Path
    adapter_init: Path
    analyze_py: Path | None
    output_schema: Path | None
    blueprint: Path | None
    makefile: Path | None
    judges_dir: Path | None
    eval_orchestrator: Path | None
    prompts_dir: Path | None
    eval_strategy: Path | None


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file."""
    return yaml.safe_load(path.read_text()) or {}


def discover_tool_files(tool_name: str, project_root: Path) -> ToolFiles:
    """Discover all relevant files for a tool.

    Args:
        tool_name: Tool name (e.g., 'scc', 'lizard', 'pmd-cpd').
        project_root: Path to the project root directory.

    Returns:
        ToolFiles dataclass with all resolved paths.
    """
    src = project_root / "src"
    tool_dir = src / "tools" / tool_name
    sot = src / "sot-engine"

    # Load common config for entity names
    common_yaml = src / "tool-compliance" / "rules" / "common.yaml"
    common_config = _load_yaml(common_yaml) if common_yaml.exists() else {}
    tool_entities = common_config.get("tool_entities", {})
    entity_names = tool_entities.get(tool_name, [])

    # Load tool-specific rules for adapter info
    tool_yaml = src / "tool-compliance" / "rules" / f"{tool_name}.yaml"
    tool_config = _load_yaml(tool_yaml) if tool_yaml.exists() else {}
    adapter_info = tool_config.get("adapter", {})

    adapter_module = adapter_info.get("module", "") if isinstance(adapter_info, dict) else ""
    adapter_class = adapter_info.get("class") if isinstance(adapter_info, dict) else None

    # Derive repo class from entity_repository_map
    entity_repo_map = common_config.get("entity_repository_map", {})
    repo_class = None
    if entity_names:
        first_entity = entity_names[0]
        repo_info = entity_repo_map.get(first_entity, {})
        if isinstance(repo_info, dict):
            repo_class = repo_info.get("repository")

    # Resolve adapter file path
    adapter_file = None
    if adapter_module:
        # Convert module path like 'persistence.adapters.scc_adapter' to file path
        module_parts = adapter_module.replace(".", "/")
        adapter_file = sot / f"{module_parts}.py"

    # Standard paths
    analyze_py = tool_dir / "scripts" / "analyze.py"
    output_schema = tool_dir / "schemas" / "output.schema.json"
    blueprint = tool_dir / "BLUEPRINT.md"
    makefile = tool_dir / "Makefile"
    judges_dir = tool_dir / "evaluation" / "llm" / "judges"
    eval_orchestrator = tool_dir / "evaluation" / "llm" / "orchestrator.py"
    prompts_dir = tool_dir / "evaluation" / "llm" / "prompts"
    eval_strategy = tool_dir / "evaluation" / "EVAL_STRATEGY.md"

    return ToolFiles(
        tool_name=tool_name,
        tool_dir=tool_dir,
        adapter_file=adapter_file if adapter_file and adapter_file.exists() else None,
        entity_names=entity_names,
        adapter_class=adapter_class,
        repo_class=repo_class,
        entities_file=sot / "persistence" / "entities.py",
        repositories_file=sot / "persistence" / "repositories.py",
        schema_sql=sot / "persistence" / "schema.sql",
        orchestrator_file=sot / "orchestrator.py",
        adapter_init=sot / "persistence" / "adapters" / "__init__.py",
        analyze_py=analyze_py if analyze_py.exists() else None,
        output_schema=output_schema if output_schema.exists() else None,
        blueprint=blueprint if blueprint.exists() else None,
        makefile=makefile if makefile.exists() else None,
        judges_dir=judges_dir if judges_dir.exists() else None,
        eval_orchestrator=eval_orchestrator if eval_orchestrator.exists() else None,
        prompts_dir=prompts_dir if prompts_dir.exists() else None,
        eval_strategy=eval_strategy if eval_strategy.exists() else None,
    )


def list_all_tools(project_root: Path) -> list[str]:
    """List all tools registered in common.yaml.

    Returns:
        Sorted list of tool names.
    """
    common_yaml = project_root / "src" / "tool-compliance" / "rules" / "common.yaml"
    if not common_yaml.exists():
        return []
    config = _load_yaml(common_yaml)
    tool_entities = config.get("tool_entities", {})
    return sorted(tool_entities.keys())
