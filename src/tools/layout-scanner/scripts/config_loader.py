"""
Configuration Loader for Layout Scanner.

Loads configuration from:
1. CLI flags (highest priority)
2. .layout-scanner.json in repository root
3. ~/.config/layout-scanner/config.json (user default)
4. Built-in defaults (lowest priority)
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ClassificationConfig:
    """Configuration for file classification."""
    confidence_threshold: float = 0.5
    rules_path: Path | None = None  # Path to YAML rules file
    custom_path_rules: dict[str, list[str]] = field(default_factory=dict)
    custom_filename_rules: dict[str, list[str]] = field(default_factory=dict)
    custom_extension_rules: dict[str, list[str]] = field(default_factory=dict)
    overrides: dict[str, str] = field(default_factory=dict)
    weights: dict[str, float] | None = None  # Override signal weights


@dataclass
class IgnoreConfig:
    """Configuration for file/directory ignoring."""
    additional_patterns: list[str] = field(default_factory=list)
    respect_gitignore: bool = True


@dataclass
class PerformanceConfig:
    """Configuration for performance tuning."""
    max_file_size_bytes: int = 104857600  # 100MB
    skip_binary_detection: bool = False


@dataclass
class GitConfig:
    """Configuration for git metadata enrichment."""
    enabled: bool = False
    timeout_seconds: int = 120


@dataclass
class ContentConfig:
    """Configuration for content metadata enrichment."""
    enabled: bool = False
    hash_algorithm: str = "sha256"
    max_file_size_bytes: int = 104857600  # 100MB
    binary_sample_size: int = 8192


@dataclass
class ScannerConfig:
    """Complete configuration for the layout scanner."""
    classification: ClassificationConfig = field(default_factory=ClassificationConfig)
    ignore: IgnoreConfig = field(default_factory=IgnoreConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    git: GitConfig = field(default_factory=GitConfig)
    content: ContentConfig = field(default_factory=ContentConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScannerConfig":
        """Create config from dictionary."""
        config = cls()

        if "classification" in data:
            c = data["classification"]
            rules_path_str = c.get("rules_path")
            config.classification = ClassificationConfig(
                confidence_threshold=c.get("confidence_threshold", 0.5),
                rules_path=Path(rules_path_str) if rules_path_str else None,
                custom_path_rules=c.get("custom_rules", {}).get("path", {}),
                custom_filename_rules=c.get("custom_rules", {}).get("filename", {}),
                custom_extension_rules=c.get("custom_rules", {}).get("extension", {}),
                overrides=c.get("override", {}),
                weights=c.get("weights"),
            )

        if "ignore" in data:
            i = data["ignore"]
            config.ignore = IgnoreConfig(
                additional_patterns=i.get("additional_patterns", []),
                respect_gitignore=i.get("respect_gitignore", True),
            )

        if "performance" in data:
            p = data["performance"]
            config.performance = PerformanceConfig(
                max_file_size_bytes=p.get("max_file_size_bytes", 104857600),
                skip_binary_detection=p.get("skip_binary_detection", False),
            )

        if "git" in data:
            g = data["git"]
            config.git = GitConfig(
                enabled=g.get("enabled", False),
                timeout_seconds=g.get("timeout_seconds", 120),
            )

        if "content" in data:
            c = data["content"]
            config.content = ContentConfig(
                enabled=c.get("enabled", False),
                hash_algorithm=c.get("hash_algorithm", "sha256"),
                max_file_size_bytes=c.get("max_file_size_bytes", 104857600),
                binary_sample_size=c.get("binary_sample_size", 8192),
            )

        return config

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        classification_dict: dict[str, Any] = {
            "confidence_threshold": self.classification.confidence_threshold,
            "custom_rules": {
                "path": self.classification.custom_path_rules,
                "filename": self.classification.custom_filename_rules,
                "extension": self.classification.custom_extension_rules,
            },
            "override": self.classification.overrides,
        }
        if self.classification.rules_path:
            classification_dict["rules_path"] = str(self.classification.rules_path)
        if self.classification.weights:
            classification_dict["weights"] = self.classification.weights

        return {
            "classification": classification_dict,
            "ignore": {
                "additional_patterns": self.ignore.additional_patterns,
                "respect_gitignore": self.ignore.respect_gitignore,
            },
            "performance": {
                "max_file_size_bytes": self.performance.max_file_size_bytes,
                "skip_binary_detection": self.performance.skip_binary_detection,
            },
            "git": {
                "enabled": self.git.enabled,
                "timeout_seconds": self.git.timeout_seconds,
            },
            "content": {
                "enabled": self.content.enabled,
                "hash_algorithm": self.content.hash_algorithm,
                "max_file_size_bytes": self.content.max_file_size_bytes,
                "binary_sample_size": self.content.binary_sample_size,
            },
        }


def validate_config(data: dict[str, Any]) -> list[str]:
    """
    Validate configuration structure and return list of errors.

    Args:
        data: Configuration dictionary to validate

    Returns:
        List of error messages (empty if valid)
    """
    errors: list[str] = []

    # Validate classification section
    if "classification" in data:
        c = data["classification"]
        if not isinstance(c, dict):
            errors.append("classification must be an object")
        else:
            if "confidence_threshold" in c:
                if not isinstance(c["confidence_threshold"], (int, float)):
                    errors.append("classification.confidence_threshold must be a number")
                elif not 0.0 <= c["confidence_threshold"] <= 1.0:
                    errors.append("classification.confidence_threshold must be between 0.0 and 1.0")

            if "weights" in c:
                if not isinstance(c["weights"], dict):
                    errors.append("classification.weights must be an object")
                else:
                    valid_keys = {"path", "filename", "extension"}
                    for key in c["weights"]:
                        if key not in valid_keys:
                            errors.append(f"classification.weights has unknown key: {key}")
                        elif not isinstance(c["weights"][key], (int, float)):
                            errors.append(f"classification.weights.{key} must be a number")

            if "custom_rules" in c:
                if not isinstance(c["custom_rules"], dict):
                    errors.append("classification.custom_rules must be an object")

            if "override" in c:
                if not isinstance(c["override"], dict):
                    errors.append("classification.override must be an object")

    # Validate ignore section
    if "ignore" in data:
        i = data["ignore"]
        if not isinstance(i, dict):
            errors.append("ignore must be an object")
        else:
            if "additional_patterns" in i:
                if not isinstance(i["additional_patterns"], list):
                    errors.append("ignore.additional_patterns must be an array")
                else:
                    for idx, pattern in enumerate(i["additional_patterns"]):
                        if not isinstance(pattern, str):
                            errors.append(f"ignore.additional_patterns[{idx}] must be a string")

            if "respect_gitignore" in i:
                if not isinstance(i["respect_gitignore"], bool):
                    errors.append("ignore.respect_gitignore must be a boolean")

    # Validate performance section
    if "performance" in data:
        p = data["performance"]
        if not isinstance(p, dict):
            errors.append("performance must be an object")
        else:
            if "max_file_size_bytes" in p:
                if not isinstance(p["max_file_size_bytes"], int):
                    errors.append("performance.max_file_size_bytes must be an integer")
                elif p["max_file_size_bytes"] < 0:
                    errors.append("performance.max_file_size_bytes must be non-negative")

    return errors


def load_config_file(path: Path) -> dict[str, Any] | None:
    """
    Load configuration from a JSON file.

    Args:
        path: Path to config file

    Returns:
        Parsed config dict or None if file doesn't exist
    """
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Failed to load config from {path}: {e}")
        return None


def merge_configs(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Deep merge two config dictionaries.

    Override values take precedence.
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value

    return result


def load_config(
    repo_path: Path | None = None,
    config_path: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> ScannerConfig:
    """
    Load configuration with proper priority ordering.

    Priority (highest to lowest):
    1. CLI overrides
    2. Explicit config file (if provided)
    3. .layout-scanner.json in repo root
    4. ~/.config/layout-scanner/config.json
    5. Built-in defaults

    Args:
        repo_path: Path to repository root
        config_path: Explicit path to config file
        cli_overrides: Overrides from CLI flags

    Returns:
        Merged ScannerConfig
    """
    config_data: dict[str, Any] = {}

    # Load user default config
    user_config_path = Path.home() / ".config" / "layout-scanner" / "config.json"
    user_config = load_config_file(user_config_path)
    if user_config:
        config_data = merge_configs(config_data, user_config)

    # Load repo-level config
    if repo_path:
        repo_config_path = repo_path / ".layout-scanner.json"
        repo_config = load_config_file(repo_config_path)
        if repo_config:
            config_data = merge_configs(config_data, repo_config)

    # Load explicit config file
    if config_path:
        explicit_config = load_config_file(config_path)
        if explicit_config:
            config_data = merge_configs(config_data, explicit_config)

    # Apply CLI overrides
    if cli_overrides:
        config_data = merge_configs(config_data, cli_overrides)

    return ScannerConfig.from_dict(config_data)


def get_default_config() -> ScannerConfig:
    """Get default configuration."""
    return ScannerConfig()


def save_config(config: ScannerConfig, path: Path) -> None:
    """
    Save configuration to a JSON file.

    Args:
        config: Configuration to save
        path: Path to save to
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, indent=2)
