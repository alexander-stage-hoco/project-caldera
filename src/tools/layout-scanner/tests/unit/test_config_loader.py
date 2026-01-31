"""
Unit tests for config_loader.py
"""

import json
import pytest
from pathlib import Path

from scripts.config_loader import (
    ClassificationConfig,
    IgnoreConfig,
    PerformanceConfig,
    ScannerConfig,
    load_config_file,
    merge_configs,
    load_config,
    get_default_config,
    save_config,
)


class TestClassificationConfigDataclass:
    """Tests for ClassificationConfig dataclass."""

    def test_default_values(self):
        """ClassificationConfig should have sensible defaults."""
        config = ClassificationConfig()
        assert config.confidence_threshold == 0.5
        assert config.custom_path_rules == {}
        assert config.custom_filename_rules == {}
        assert config.overrides == {}

    def test_custom_values(self):
        """ClassificationConfig should accept custom values."""
        config = ClassificationConfig(
            confidence_threshold=0.8,
            custom_path_rules={"vendor": ["myvendor/"]},
            custom_filename_rules={"test": [r".*_bench\.py$"]},
            overrides={"lib/": "vendor"},
        )
        assert config.confidence_threshold == 0.8
        assert "vendor" in config.custom_path_rules
        assert "test" in config.custom_filename_rules
        assert config.overrides["lib/"] == "vendor"


class TestIgnoreConfigDataclass:
    """Tests for IgnoreConfig dataclass."""

    def test_default_values(self):
        """IgnoreConfig should have sensible defaults."""
        config = IgnoreConfig()
        assert config.additional_patterns == []
        assert config.respect_gitignore is True

    def test_custom_values(self):
        """IgnoreConfig should accept custom values."""
        config = IgnoreConfig(
            additional_patterns=["*.log", "temp/"],
            respect_gitignore=False,
        )
        assert "*.log" in config.additional_patterns
        assert config.respect_gitignore is False


class TestPerformanceConfigDataclass:
    """Tests for PerformanceConfig dataclass."""

    def test_default_values(self):
        """PerformanceConfig should have sensible defaults."""
        config = PerformanceConfig()
        assert config.max_file_size_bytes == 104857600  # 100MB
        assert config.skip_binary_detection is False

    def test_custom_values(self):
        """PerformanceConfig should accept custom values."""
        config = PerformanceConfig(
            max_file_size_bytes=50_000_000,
            skip_binary_detection=True,
        )
        assert config.max_file_size_bytes == 50_000_000
        assert config.skip_binary_detection is True


class TestScannerConfigDataclass:
    """Tests for ScannerConfig dataclass."""

    def test_default_values(self):
        """ScannerConfig should have sensible defaults."""
        config = ScannerConfig()
        assert isinstance(config.classification, ClassificationConfig)
        assert isinstance(config.ignore, IgnoreConfig)
        assert isinstance(config.performance, PerformanceConfig)

    def test_from_dict_empty(self):
        """ScannerConfig.from_dict should handle empty dict."""
        config = ScannerConfig.from_dict({})
        assert config.classification.confidence_threshold == 0.5
        assert config.ignore.respect_gitignore is True

    def test_from_dict_classification(self):
        """ScannerConfig.from_dict should parse classification section."""
        data = {
            "classification": {
                "confidence_threshold": 0.7,
                "custom_rules": {
                    "path": {"vendor": ["myvendor/"]},
                    "filename": {"test": [r".*_bench\.py$"]},
                },
                "override": {"lib/": "vendor"},
            }
        }
        config = ScannerConfig.from_dict(data)
        assert config.classification.confidence_threshold == 0.7
        assert "vendor" in config.classification.custom_path_rules
        assert config.classification.overrides["lib/"] == "vendor"

    def test_from_dict_ignore(self):
        """ScannerConfig.from_dict should parse ignore section."""
        data = {
            "ignore": {
                "additional_patterns": ["*.log", "temp/"],
                "respect_gitignore": False,
            }
        }
        config = ScannerConfig.from_dict(data)
        assert "*.log" in config.ignore.additional_patterns
        assert config.ignore.respect_gitignore is False

    def test_from_dict_performance(self):
        """ScannerConfig.from_dict should parse performance section."""
        data = {
            "performance": {
                "max_file_size_bytes": 50_000_000,
                "skip_binary_detection": True,
            }
        }
        config = ScannerConfig.from_dict(data)
        assert config.performance.max_file_size_bytes == 50_000_000
        assert config.performance.skip_binary_detection is True

    def test_to_dict(self):
        """ScannerConfig.to_dict should serialize to dict."""
        config = ScannerConfig(
            classification=ClassificationConfig(confidence_threshold=0.8),
            ignore=IgnoreConfig(additional_patterns=["*.log"]),
            performance=PerformanceConfig(max_file_size_bytes=50_000_000),
        )
        data = config.to_dict()
        assert data["classification"]["confidence_threshold"] == 0.8
        assert "*.log" in data["ignore"]["additional_patterns"]
        assert data["performance"]["max_file_size_bytes"] == 50_000_000

    def test_roundtrip(self):
        """ScannerConfig should survive roundtrip through dict."""
        original = ScannerConfig(
            classification=ClassificationConfig(
                confidence_threshold=0.7,
                custom_path_rules={"vendor": ["myvendor/"]},
                overrides={"lib/": "vendor"},
            ),
            ignore=IgnoreConfig(
                additional_patterns=["*.log"],
                respect_gitignore=False,
            ),
            performance=PerformanceConfig(
                max_file_size_bytes=25_000_000,
                skip_binary_detection=True,
            ),
        )
        data = original.to_dict()
        restored = ScannerConfig.from_dict(data)

        assert restored.classification.confidence_threshold == original.classification.confidence_threshold
        assert restored.ignore.respect_gitignore == original.ignore.respect_gitignore
        assert restored.performance.max_file_size_bytes == original.performance.max_file_size_bytes


class TestLoadConfigFile:
    """Tests for load_config_file function."""

    def test_load_existing_file(self, tmp_path):
        """Should load existing JSON config file."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"ignore": {"respect_gitignore": false}}')

        result = load_config_file(config_file)
        assert result is not None
        assert result["ignore"]["respect_gitignore"] is False

    def test_load_missing_file(self, tmp_path):
        """Should return None for missing file."""
        result = load_config_file(tmp_path / "nonexistent.json")
        assert result is None

    def test_load_invalid_json(self, tmp_path):
        """Should return None for invalid JSON."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("not valid json {{{")

        result = load_config_file(config_file)
        assert result is None

    def test_load_complex_config(self, tmp_path):
        """Should load complex nested config."""
        config_data = {
            "classification": {
                "confidence_threshold": 0.8,
                "custom_rules": {
                    "path": {"vendor": ["custom_vendor/"]},
                },
            },
            "ignore": {
                "additional_patterns": ["*.tmp", "cache/"],
            },
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        result = load_config_file(config_file)
        assert result["classification"]["confidence_threshold"] == 0.8
        assert "custom_vendor/" in result["classification"]["custom_rules"]["path"]["vendor"]


class TestMergeConfigs:
    """Tests for merge_configs function."""

    def test_merge_empty_base(self):
        """Override should apply to empty base."""
        result = merge_configs({}, {"key": "value"})
        assert result["key"] == "value"

    def test_merge_empty_override(self):
        """Empty override should preserve base."""
        result = merge_configs({"key": "value"}, {})
        assert result["key"] == "value"

    def test_override_simple_value(self):
        """Override should replace simple values."""
        base = {"key": "original"}
        override = {"key": "updated"}
        result = merge_configs(base, override)
        assert result["key"] == "updated"

    def test_merge_nested_dicts(self):
        """Should deep merge nested dictionaries."""
        base = {
            "level1": {
                "a": 1,
                "b": 2,
            }
        }
        override = {
            "level1": {
                "b": 3,
                "c": 4,
            }
        }
        result = merge_configs(base, override)
        assert result["level1"]["a"] == 1
        assert result["level1"]["b"] == 3
        assert result["level1"]["c"] == 4

    def test_override_dict_with_value(self):
        """Value should replace dict entirely."""
        base = {"key": {"nested": "value"}}
        override = {"key": "simple"}
        result = merge_configs(base, override)
        assert result["key"] == "simple"

    def test_override_value_with_dict(self):
        """Dict should replace value entirely."""
        base = {"key": "simple"}
        override = {"key": {"nested": "value"}}
        result = merge_configs(base, override)
        assert result["key"]["nested"] == "value"


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_defaults_only(self, tmp_path):
        """Should return defaults with no config files."""
        config = load_config(repo_path=tmp_path)
        assert config.classification.confidence_threshold == 0.5
        assert config.ignore.respect_gitignore is True

    def test_load_from_repo_config(self, tmp_path):
        """Should load from .layout-scanner.json in repo."""
        config_data = {
            "ignore": {"respect_gitignore": False}
        }
        config_file = tmp_path / ".layout-scanner.json"
        config_file.write_text(json.dumps(config_data))

        config = load_config(repo_path=tmp_path)
        assert config.ignore.respect_gitignore is False

    def test_load_from_explicit_path(self, tmp_path):
        """Should load from explicit config path."""
        config_data = {
            "classification": {"confidence_threshold": 0.9}
        }
        config_file = tmp_path / "custom.json"
        config_file.write_text(json.dumps(config_data))

        config = load_config(config_path=config_file)
        assert config.classification.confidence_threshold == 0.9

    def test_cli_overrides_take_precedence(self, tmp_path):
        """CLI overrides should take precedence over file config."""
        config_data = {
            "ignore": {"respect_gitignore": True}
        }
        config_file = tmp_path / ".layout-scanner.json"
        config_file.write_text(json.dumps(config_data))

        cli_overrides = {"ignore": {"respect_gitignore": False}}
        config = load_config(repo_path=tmp_path, cli_overrides=cli_overrides)
        assert config.ignore.respect_gitignore is False

    def test_explicit_config_over_repo_config(self, tmp_path):
        """Explicit config should take precedence over repo config."""
        repo_config = {"classification": {"confidence_threshold": 0.5}}
        explicit_config = {"classification": {"confidence_threshold": 0.9}}

        (tmp_path / ".layout-scanner.json").write_text(json.dumps(repo_config))
        explicit_path = tmp_path / "custom.json"
        explicit_path.write_text(json.dumps(explicit_config))

        config = load_config(repo_path=tmp_path, config_path=explicit_path)
        assert config.classification.confidence_threshold == 0.9


class TestGetDefaultConfig:
    """Tests for get_default_config function."""

    def test_returns_defaults(self):
        """Should return default configuration."""
        config = get_default_config()
        assert config.classification.confidence_threshold == 0.5
        assert config.ignore.respect_gitignore is True
        assert config.performance.max_file_size_bytes == 104857600


class TestSaveConfig:
    """Tests for save_config function."""

    def test_save_creates_file(self, tmp_path):
        """Should create config file."""
        config = ScannerConfig()
        config_path = tmp_path / "config.json"

        save_config(config, config_path)

        assert config_path.exists()

    def test_save_creates_parent_dirs(self, tmp_path):
        """Should create parent directories if needed."""
        config = ScannerConfig()
        config_path = tmp_path / "nested" / "dir" / "config.json"

        save_config(config, config_path)

        assert config_path.exists()
        assert config_path.parent.exists()

    def test_save_valid_json(self, tmp_path):
        """Should save valid JSON."""
        config = ScannerConfig(
            ignore=IgnoreConfig(additional_patterns=["*.log"])
        )
        config_path = tmp_path / "config.json"

        save_config(config, config_path)

        # Should be loadable as JSON
        with open(config_path) as f:
            data = json.load(f)

        assert "*.log" in data["ignore"]["additional_patterns"]

    def test_save_and_load_roundtrip(self, tmp_path):
        """Saved config should be loadable."""
        original = ScannerConfig(
            classification=ClassificationConfig(confidence_threshold=0.8),
            ignore=IgnoreConfig(
                additional_patterns=["*.tmp"],
                respect_gitignore=False,
            ),
        )
        config_path = tmp_path / "config.json"

        save_config(original, config_path)
        loaded = load_config(config_path=config_path)

        assert loaded.classification.confidence_threshold == 0.8
        assert "*.tmp" in loaded.ignore.additional_patterns
        assert loaded.ignore.respect_gitignore is False
