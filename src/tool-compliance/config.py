"""Configuration loader for tool compliance scanner.

Loads tool rules and common configuration from YAML files in the rules/ directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Use standard library for YAML-like parsing to avoid extra dependencies
# For simple configs, we parse YAML manually or use a fallback

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


RULES_DIR = Path(__file__).parent / "rules"


def _parse_simple_yaml(content: str) -> dict[str, Any]:
    """Parse a simple YAML file without external dependencies.

    Handles basic YAML features:
    - Key-value pairs
    - Lists (with - prefix)
    - Nested dicts (indentation-based)

    Note: This is a simplified parser. For complex YAML, install PyYAML.
    """
    result: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[str] | None = None
    current_dict: dict[str, Any] | None = None
    nested_key: str | None = None

    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()

        # Skip comments and empty lines
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        # Calculate indentation
        indent = len(line) - len(line.lstrip())
        content_line = stripped.lstrip()

        # Top-level key (no indentation)
        if indent == 0 and ":" in content_line:
            # Save any pending list/dict
            if current_key and current_list is not None:
                result[current_key] = current_list
            elif current_key and current_dict is not None:
                result[current_key] = current_dict

            key, _, value = content_line.partition(":")
            key = key.strip()
            value = value.strip()

            if value:
                result[key] = value
                current_key = None
                current_list = None
                current_dict = None
            else:
                current_key = key
                current_list = None
                current_dict = None

        # List item (starts with -)
        elif content_line.startswith("- ") and current_key:
            if current_list is None:
                current_list = []
                current_dict = None
            item = content_line[2:].strip()
            current_list.append(item)

        # Nested key-value (indented, contains :)
        elif indent > 0 and ":" in content_line and current_key:
            if current_dict is None:
                current_dict = {}
                current_list = None

            nested_parts = content_line.split(":", 1)
            nested_k = nested_parts[0].strip()
            nested_v = nested_parts[1].strip() if len(nested_parts) > 1 else ""

            # Check if this is a nested dict (value is empty, followed by indented items)
            if not nested_v:
                # Look ahead for nested items
                nested_items: list[str] | dict[str, Any] = []
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    next_stripped = next_line.rstrip()
                    if not next_stripped or next_stripped.startswith("#"):
                        j += 1
                        continue
                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_indent <= indent:
                        break
                    next_content = next_stripped.lstrip()
                    if next_content.startswith("- "):
                        if not isinstance(nested_items, list):
                            nested_items = []
                        nested_items.append(next_content[2:].strip())
                    elif ":" in next_content:
                        if isinstance(nested_items, list) and not nested_items:
                            nested_items = {}
                        if isinstance(nested_items, dict):
                            nk, nv = next_content.split(":", 1)
                            nested_items[nk.strip()] = nv.strip()
                    j += 1
                current_dict[nested_k] = nested_items
                i = j - 1
            else:
                current_dict[nested_k] = nested_v

        i += 1

    # Save any pending list/dict
    if current_key:
        if current_list is not None:
            result[current_key] = current_list
        elif current_dict is not None:
            result[current_key] = current_dict

    return result


def load_yaml_file(path: Path) -> dict[str, Any]:
    """Load a YAML file, using PyYAML if available."""
    content = path.read_text()
    if HAS_YAML:
        return yaml.safe_load(content) or {}
    return _parse_simple_yaml(content)


def load_common_config() -> dict[str, Any]:
    """Load common configuration from rules/common.yaml."""
    common_path = RULES_DIR / "common.yaml"
    if common_path.exists():
        return load_yaml_file(common_path)
    return {}


def load_tool_rules(tool_name: str) -> dict[str, Any]:
    """Load rules for a specific tool from rules/<tool>.yaml."""
    tool_path = RULES_DIR / f"{tool_name}.yaml"
    if tool_path.exists():
        config = load_yaml_file(tool_path)
        # Convert adapter dict to tuple format expected by existing code
        if "adapter" in config and isinstance(config["adapter"], dict):
            adapter = config["adapter"]
            config["adapter"] = (adapter.get("module", ""), adapter.get("class", ""))
        return config
    return {}


def load_all_tool_rules() -> dict[str, dict[str, Any]]:
    """Load rules for all tools from YAML files.

    Returns:
        Dict mapping tool name to its rules config.
    """
    rules: dict[str, dict[str, Any]] = {}

    for yaml_file in RULES_DIR.glob("*.yaml"):
        if yaml_file.name == "common.yaml":
            continue
        tool_name = yaml_file.stem
        rules[tool_name] = load_tool_rules(tool_name)

    return rules


# Cached configs
_common_config: dict[str, Any] | None = None
_tool_rules: dict[str, dict[str, Any]] | None = None


def get_common_config() -> dict[str, Any]:
    """Get common config (cached)."""
    global _common_config
    if _common_config is None:
        _common_config = load_common_config()
    return _common_config


def get_tool_rules() -> dict[str, dict[str, Any]]:
    """Get all tool rules (cached)."""
    global _tool_rules
    if _tool_rules is None:
        _tool_rules = load_all_tool_rules()
    return _tool_rules


def get_required_paths() -> list[str]:
    """Get REQUIRED_PATHS from config."""
    return get_common_config().get("required_paths", [])


def get_required_make_targets() -> set[str]:
    """Get REQUIRED_MAKE_TARGETS from config."""
    return set(get_common_config().get("required_make_targets", []))


def get_blueprint_required_sections() -> list[str]:
    """Get BLUEPRINT_REQUIRED_SECTIONS from config."""
    return get_common_config().get("blueprint_required_sections", [])


def get_eval_strategy_required_sections() -> list[str]:
    """Get EVAL_STRATEGY_REQUIRED_SECTIONS from config."""
    return get_common_config().get("eval_strategy_required_sections", [])


def get_tool_entities() -> dict[str, list[str]]:
    """Get TOOL_ENTITIES from config."""
    return get_common_config().get("tool_entities", {})


def get_entity_repository_map() -> dict[str, tuple[str, str]]:
    """Get ENTITY_REPOSITORY_MAP from config, converting to tuple format."""
    raw = get_common_config().get("entity_repository_map", {})
    result: dict[str, tuple[str, str]] = {}
    for entity, mapping in raw.items():
        if isinstance(mapping, dict):
            result[entity] = (mapping.get("repository", ""), mapping.get("method", ""))
        elif isinstance(mapping, (list, tuple)) and len(mapping) >= 2:
            result[entity] = (mapping[0], mapping[1])
    return result


def get_quality_rule_patterns() -> dict[str, list[str]]:
    """Get QUALITY_RULE_PATTERNS from config."""
    return get_common_config().get("quality_rule_patterns", {})


def get_data_completeness_rules(tool_name: str | None = None) -> dict[str, Any]:
    """Get DATA_COMPLETENESS_RULES from config, with optional tool-specific overrides.

    Args:
        tool_name: If provided, apply tool-specific overrides from
                   required_data_fields_overrides section.

    Returns:
        Data completeness rules dict with any tool-specific overrides applied.
    """
    rules = get_common_config().get("data_completeness_rules", {}).copy()

    # Apply tool-specific overrides if present
    if tool_name:
        overrides = rules.get("required_data_fields_overrides", {}).get(tool_name, {})
        if overrides:
            # Deep copy required_data_fields before modifying
            required_fields = dict(rules.get("required_data_fields", {}))
            required_fields.update(overrides)
            rules["required_data_fields"] = required_fields

    return rules


def get_path_consistency_rules() -> dict[str, Any]:
    """Get PATH_CONSISTENCY_RULES from config."""
    return get_common_config().get("path_consistency_rules", {})


def get_test_coverage_rules() -> dict[str, Any]:
    """Get TEST_COVERAGE_RULES from config.

    Returns:
        Dict with keys:
        - threshold: int (default 80)
        - source_dirs: list[str] (default ["scripts"])
        - omit_patterns: list[str] (patterns to exclude from coverage)
    """
    rules = get_common_config().get("test_coverage_rules", {})
    # Apply defaults
    return {
        "threshold": rules.get("threshold", 80),
        "source_dirs": rules.get("source_dirs", ["scripts"]),
        "omit_patterns": rules.get("omit_patterns", []),
    }
