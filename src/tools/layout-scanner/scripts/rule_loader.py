"""
Rule Loader for Layout Scanner Classification.

Loads classification rules from YAML files, supporting:
- Custom categories and subcategories
- Configurable signal weights
- Path, filename, and extension rules

Provides rule merging and default rule management.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# Default signal weights
DEFAULT_WEIGHTS = {
    "path": 0.9,
    "filename": 0.8,
    "extension": 0.5,
}

# Default categories
DEFAULT_CATEGORIES = [
    "source",
    "test",
    "config",
    "generated",
    "docs",
    "vendor",
    "build",
    "ci",
    "other",
]

# Default subcategories
DEFAULT_SUBCATEGORIES: Dict[str, List[str]] = {
    "test": ["unit", "integration", "e2e"],
    "config": ["build", "lint", "ci"],
}


@dataclass
class RuleSet:
    """A complete set of classification rules."""

    path_rules: Dict[str, List[str]] = field(default_factory=dict)
    filename_rules: Dict[str, List[str]] = field(default_factory=dict)
    extension_rules: Dict[str, List[str]] = field(default_factory=dict)
    weights: Dict[str, float] = field(default_factory=lambda: DEFAULT_WEIGHTS.copy())
    categories: List[str] = field(default_factory=lambda: DEFAULT_CATEGORIES.copy())
    subcategories: Dict[str, List[str]] = field(default_factory=dict)
    version: str = "1.0"

    def get_all_categories(self) -> List[str]:
        """Get all valid categories including subcategories."""
        result = list(self.categories)
        for parent, subs in self.subcategories.items():
            for sub in subs:
                full_cat = f"{parent}::{sub}"
                if full_cat not in result:
                    result.append(full_cat)
        return result

    def is_valid_category(self, category: str) -> bool:
        """Check if a category (including subcategory) is valid."""
        # Check if it's a base category
        if category in self.categories:
            return True

        # Check if it's a subcategory
        if "::" in category:
            parent, sub = category.split("::", 1)
            if parent in self.subcategories:
                return sub in self.subcategories[parent]

        return False

    def resolve_category(self, category: str) -> str:
        """
        Resolve a category to its base form.

        For example: "test::unit" -> "test" (for validation against schema)
        """
        if "::" in category:
            return category.split("::")[0]
        return category


def load_rules(rules_path: Path) -> RuleSet:
    """
    Load classification rules from a YAML file.

    Args:
        rules_path: Path to YAML rules file

    Returns:
        RuleSet loaded from the file

    Raises:
        FileNotFoundError: If the rules file doesn't exist
        yaml.YAMLError: If the YAML is invalid
        ValueError: If the rules structure is invalid
    """
    if not rules_path.exists():
        raise FileNotFoundError(f"Rules file not found: {rules_path}")

    with open(rules_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid rules file format: expected dict, got {type(data)}")

    return _parse_rules(data)


def _parse_rules(data: Dict[str, Any]) -> RuleSet:
    """Parse a rules dictionary into a RuleSet."""
    rules = RuleSet()

    # Version
    if "version" in data:
        rules.version = str(data["version"])

    # Weights
    if "weights" in data:
        weights = data["weights"]
        if isinstance(weights, dict):
            for key in ["path", "filename", "extension"]:
                if key in weights:
                    try:
                        rules.weights[key] = float(weights[key])
                    except (TypeError, ValueError):
                        pass  # Keep default

    # Categories
    if "categories" in data:
        cats = data["categories"]
        if isinstance(cats, list):
            rules.categories = [str(c) for c in cats if c]

    # Subcategories
    if "subcategories" in data:
        subs = data["subcategories"]
        if isinstance(subs, dict):
            for parent, children in subs.items():
                if isinstance(children, list):
                    rules.subcategories[str(parent)] = [str(c) for c in children if c]

    # Path rules
    if "path_rules" in data:
        path_rules = data["path_rules"]
        if isinstance(path_rules, dict):
            for category, patterns in path_rules.items():
                if isinstance(patterns, list):
                    rules.path_rules[str(category)] = [str(p) for p in patterns if p]

    # Filename rules (regex patterns)
    if "filename_rules" in data:
        filename_rules = data["filename_rules"]
        if isinstance(filename_rules, dict):
            for category, patterns in filename_rules.items():
                if isinstance(patterns, list):
                    rules.filename_rules[str(category)] = [str(p) for p in patterns if p]

    # Extension rules
    if "extension_rules" in data:
        ext_rules = data["extension_rules"]
        if isinstance(ext_rules, dict):
            for category, extensions in ext_rules.items():
                if isinstance(extensions, list):
                    rules.extension_rules[str(category)] = [str(e) for e in extensions if e]

    return rules


def merge_rules(base: RuleSet, custom: RuleSet) -> RuleSet:
    """
    Merge custom rules with base rules.

    Custom rules extend (not replace) base rules.
    Weights from custom override base.

    Args:
        base: Base rule set (usually defaults)
        custom: Custom rule set to merge in

    Returns:
        New RuleSet with merged rules
    """
    merged = RuleSet()

    # Use custom weights if provided, otherwise base
    merged.weights = {**base.weights, **custom.weights}

    # Merge categories (union)
    all_categories = set(base.categories) | set(custom.categories)
    merged.categories = list(all_categories)

    # Merge subcategories
    merged.subcategories = {**base.subcategories}
    for parent, subs in custom.subcategories.items():
        if parent in merged.subcategories:
            existing = set(merged.subcategories[parent])
            merged.subcategories[parent] = list(existing | set(subs))
        else:
            merged.subcategories[parent] = list(subs)

    # Merge path rules (extend lists)
    merged.path_rules = {**base.path_rules}
    for category, patterns in custom.path_rules.items():
        if category in merged.path_rules:
            # Extend, avoiding duplicates
            existing = set(merged.path_rules[category])
            new_patterns = [p for p in patterns if p not in existing]
            merged.path_rules[category] = merged.path_rules[category] + new_patterns
        else:
            merged.path_rules[category] = list(patterns)

    # Merge filename rules (extend lists)
    merged.filename_rules = {**base.filename_rules}
    for category, patterns in custom.filename_rules.items():
        if category in merged.filename_rules:
            existing = set(merged.filename_rules[category])
            new_patterns = [p for p in patterns if p not in existing]
            merged.filename_rules[category] = merged.filename_rules[category] + new_patterns
        else:
            merged.filename_rules[category] = list(patterns)

    # Merge extension rules (extend lists)
    merged.extension_rules = {**base.extension_rules}
    for category, extensions in custom.extension_rules.items():
        if category in merged.extension_rules:
            existing = set(merged.extension_rules[category])
            new_exts = [e for e in extensions if e not in existing]
            merged.extension_rules[category] = merged.extension_rules[category] + new_exts
        else:
            merged.extension_rules[category] = list(extensions)

    # Use newer version if available
    merged.version = custom.version if custom.version else base.version

    return merged


def load_default_rules() -> RuleSet:
    """
    Load the default built-in rules.

    Looks for rules/default.yaml relative to this module,
    or returns hardcoded defaults if not found.
    """
    default_path = Path(__file__).parent.parent / "rules" / "default.yaml"

    if default_path.exists():
        return load_rules(default_path)

    # Fall back to hardcoded defaults
    return _get_hardcoded_defaults()


def _get_hardcoded_defaults() -> RuleSet:
    """Get hardcoded default rules (fallback if default.yaml not found)."""
    from .classifier import PATH_RULES, FILENAME_RULES, EXTENSION_RULES

    return RuleSet(
        path_rules=dict(PATH_RULES),
        filename_rules=dict(FILENAME_RULES),
        extension_rules=dict(EXTENSION_RULES),
        weights=DEFAULT_WEIGHTS.copy(),
        categories=DEFAULT_CATEGORIES.copy(),
        subcategories=DEFAULT_SUBCATEGORIES.copy(),
        version="1.0",
    )


def find_rules_file(repo_path: Path) -> Optional[Path]:
    """
    Find a rules file in a repository.

    Looks for (in order):
    1. .layout-scanner-rules.yaml
    2. .layout-scanner-rules.yml
    3. layout-scanner-rules.yaml
    4. layout-scanner-rules.yml

    Args:
        repo_path: Path to repository root

    Returns:
        Path to rules file, or None if not found
    """
    candidates = [
        ".layout-scanner-rules.yaml",
        ".layout-scanner-rules.yml",
        "layout-scanner-rules.yaml",
        "layout-scanner-rules.yml",
    ]

    for candidate in candidates:
        path = repo_path / candidate
        if path.exists():
            return path

    return None


def save_rules(rules: RuleSet, output_path: Path) -> None:
    """
    Save rules to a YAML file.

    Args:
        rules: RuleSet to save
        output_path: Path to write YAML file
    """
    data = {
        "version": rules.version,
        "weights": rules.weights,
        "categories": rules.categories,
    }

    if rules.subcategories:
        data["subcategories"] = rules.subcategories

    if rules.path_rules:
        data["path_rules"] = rules.path_rules

    if rules.filename_rules:
        data["filename_rules"] = rules.filename_rules

    if rules.extension_rules:
        data["extension_rules"] = rules.extension_rules

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
