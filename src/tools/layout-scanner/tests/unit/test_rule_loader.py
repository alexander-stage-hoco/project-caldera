"""
Unit tests for rule_loader.py
"""

import pytest
from pathlib import Path
import tempfile
import os

from scripts.rule_loader import (
    RuleSet,
    DEFAULT_WEIGHTS,
    DEFAULT_CATEGORIES,
    DEFAULT_SUBCATEGORIES,
    load_rules,
    merge_rules,
    load_default_rules,
    find_rules_file,
    save_rules,
)


class TestRuleSetDataclass:
    """Tests for RuleSet dataclass."""

    def test_default_values(self):
        """RuleSet should have sensible defaults."""
        rules = RuleSet()
        assert rules.path_rules == {}
        assert rules.filename_rules == {}
        assert rules.extension_rules == {}
        assert rules.weights == DEFAULT_WEIGHTS
        assert rules.categories == DEFAULT_CATEGORIES
        assert rules.subcategories == {}
        assert rules.version == "1.0"

    def test_custom_values(self):
        """RuleSet should accept custom values."""
        rules = RuleSet(
            path_rules={"vendor": ["vendor/"]},
            filename_rules={"test": [r"^test_.*\.py$"]},
            extension_rules={"config": [".json"]},
            weights={"path": 0.95, "filename": 0.85, "extension": 0.45},
            categories=["source", "test", "custom"],
            subcategories={"test": ["unit", "integration"]},
            version="2.0",
        )
        assert rules.path_rules == {"vendor": ["vendor/"]}
        assert rules.filename_rules == {"test": [r"^test_.*\.py$"]}
        assert rules.extension_rules == {"config": [".json"]}
        assert rules.weights["path"] == 0.95
        assert "custom" in rules.categories
        assert rules.subcategories["test"] == ["unit", "integration"]
        assert rules.version == "2.0"


class TestRuleSetGetAllCategories:
    """Tests for RuleSet.get_all_categories method."""

    def test_base_categories_only(self):
        """Should return base categories when no subcategories."""
        rules = RuleSet(
            categories=["source", "test"],
            subcategories={},
        )
        all_cats = rules.get_all_categories()
        assert "source" in all_cats
        assert "test" in all_cats
        assert len(all_cats) == 2

    def test_includes_subcategories(self):
        """Should include subcategory forms."""
        rules = RuleSet(
            categories=["source", "test"],
            subcategories={"test": ["unit", "integration"]},
        )
        all_cats = rules.get_all_categories()
        assert "source" in all_cats
        assert "test" in all_cats
        assert "test::unit" in all_cats
        assert "test::integration" in all_cats

    def test_no_duplicates(self):
        """Should not include duplicate categories."""
        rules = RuleSet(
            categories=["source", "test"],
            subcategories={"test": ["unit"]},
        )
        all_cats = rules.get_all_categories()
        # Count occurrences
        assert all_cats.count("test") == 1


class TestRuleSetIsValidCategory:
    """Tests for RuleSet.is_valid_category method."""

    def test_valid_base_category(self):
        """Should recognize valid base categories."""
        rules = RuleSet(categories=["source", "test"])
        assert rules.is_valid_category("source") is True
        assert rules.is_valid_category("test") is True

    def test_invalid_base_category(self):
        """Should reject invalid base categories."""
        rules = RuleSet(categories=["source", "test"])
        assert rules.is_valid_category("invalid") is False

    def test_valid_subcategory(self):
        """Should recognize valid subcategories."""
        rules = RuleSet(
            categories=["source", "test"],
            subcategories={"test": ["unit", "integration"]},
        )
        assert rules.is_valid_category("test::unit") is True
        assert rules.is_valid_category("test::integration") is True

    def test_invalid_subcategory(self):
        """Should reject invalid subcategories."""
        rules = RuleSet(
            categories=["source", "test"],
            subcategories={"test": ["unit"]},
        )
        assert rules.is_valid_category("test::invalid") is False
        assert rules.is_valid_category("source::unit") is False


class TestRuleSetResolveCategory:
    """Tests for RuleSet.resolve_category method."""

    def test_base_category_unchanged(self):
        """Base categories should return unchanged."""
        rules = RuleSet()
        assert rules.resolve_category("source") == "source"
        assert rules.resolve_category("test") == "test"

    def test_subcategory_resolves_to_base(self):
        """Subcategories should resolve to base category."""
        rules = RuleSet()
        assert rules.resolve_category("test::unit") == "test"
        assert rules.resolve_category("test::integration") == "test"
        assert rules.resolve_category("config::build") == "config"


class TestLoadRules:
    """Tests for load_rules function."""

    def test_load_valid_yaml(self, tmp_path):
        """Should load rules from valid YAML file."""
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text("""
version: "2.0"
weights:
  path: 0.95
  filename: 0.85
  extension: 0.45
categories:
  - source
  - test
  - custom
subcategories:
  test:
    - unit
    - integration
path_rules:
  vendor:
    - "myvendor/"
filename_rules:
  test:
    - "^test_.*\\\\.py$"
extension_rules:
  config:
    - ".json"
""")
        rules = load_rules(rules_file)
        assert rules.version == "2.0"
        assert rules.weights["path"] == 0.95
        assert "custom" in rules.categories
        assert "myvendor/" in rules.path_rules["vendor"]
        assert rules.subcategories["test"] == ["unit", "integration"]

    def test_load_minimal_yaml(self, tmp_path):
        """Should load minimal YAML with defaults."""
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text("""
version: "1.0"
path_rules:
  custom:
    - "custom/"
""")
        rules = load_rules(rules_file)
        assert rules.version == "1.0"
        assert rules.path_rules["custom"] == ["custom/"]
        assert rules.weights == DEFAULT_WEIGHTS  # Uses defaults

    def test_load_nonexistent_file_raises(self, tmp_path):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_rules(tmp_path / "nonexistent.yaml")

    def test_load_invalid_yaml_structure(self, tmp_path):
        """Should raise ValueError for non-dict YAML."""
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text("- item1\n- item2")
        with pytest.raises(ValueError, match="expected dict"):
            load_rules(rules_file)

    def test_load_empty_yaml(self, tmp_path):
        """Should handle empty YAML file gracefully."""
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text("")
        with pytest.raises(ValueError, match="expected dict"):
            load_rules(rules_file)


class TestMergeRules:
    """Tests for merge_rules function."""

    def test_merge_path_rules_extends(self):
        """Custom path rules should extend base rules."""
        base = RuleSet(path_rules={"vendor": ["vendor/", "node_modules/"]})
        custom = RuleSet(path_rules={"vendor": ["myvendor/"]})
        merged = merge_rules(base, custom)
        assert "vendor/" in merged.path_rules["vendor"]
        assert "node_modules/" in merged.path_rules["vendor"]
        assert "myvendor/" in merged.path_rules["vendor"]

    def test_merge_avoids_duplicates(self):
        """Merged rules should not have duplicates."""
        base = RuleSet(path_rules={"vendor": ["vendor/"]})
        custom = RuleSet(path_rules={"vendor": ["vendor/", "custom/"]})
        merged = merge_rules(base, custom)
        assert merged.path_rules["vendor"].count("vendor/") == 1

    def test_merge_weights_overrides(self):
        """Custom weights should override base weights."""
        base = RuleSet(weights={"path": 0.9, "filename": 0.8, "extension": 0.5})
        custom = RuleSet(weights={"path": 0.95, "filename": 0.8, "extension": 0.5})
        merged = merge_rules(base, custom)
        assert merged.weights["path"] == 0.95

    def test_merge_categories_union(self):
        """Categories should be union of base and custom."""
        base = RuleSet(categories=["source", "test"])
        custom = RuleSet(categories=["test", "custom"])
        merged = merge_rules(base, custom)
        assert "source" in merged.categories
        assert "test" in merged.categories
        assert "custom" in merged.categories

    def test_merge_subcategories_extends(self):
        """Subcategories should extend when parent exists."""
        base = RuleSet(subcategories={"test": ["unit"]})
        custom = RuleSet(subcategories={"test": ["integration"], "config": ["build"]})
        merged = merge_rules(base, custom)
        assert "unit" in merged.subcategories["test"]
        assert "integration" in merged.subcategories["test"]
        assert "build" in merged.subcategories["config"]

    def test_merge_new_category_rules(self):
        """New categories from custom should be added."""
        base = RuleSet(path_rules={"vendor": ["vendor/"]})
        custom = RuleSet(path_rules={"infra": ["terraform/"]})
        merged = merge_rules(base, custom)
        assert "vendor" in merged.path_rules
        assert "infra" in merged.path_rules

    def test_merge_preserves_base_when_custom_empty(self):
        """Base rules should be preserved when custom is empty."""
        base = RuleSet(
            path_rules={"vendor": ["vendor/"]},
            filename_rules={"test": [r"^test_.*\.py$"]},
        )
        custom = RuleSet()
        merged = merge_rules(base, custom)
        assert merged.path_rules == base.path_rules
        assert merged.filename_rules == base.filename_rules


class TestLoadDefaultRules:
    """Tests for load_default_rules function."""

    def test_loads_default_rules(self):
        """Should load default rules."""
        rules = load_default_rules()
        assert isinstance(rules, RuleSet)
        assert len(rules.categories) > 0

    def test_default_rules_have_path_rules(self):
        """Default rules should have path rules."""
        rules = load_default_rules()
        assert "vendor" in rules.path_rules
        assert "test" in rules.path_rules

    def test_default_rules_have_filename_rules(self):
        """Default rules should have filename rules."""
        rules = load_default_rules()
        assert "test" in rules.filename_rules

    def test_default_rules_have_extension_rules(self):
        """Default rules should have extension rules."""
        rules = load_default_rules()
        assert "config" in rules.extension_rules or "docs" in rules.extension_rules

    def test_default_rules_have_subcategories(self):
        """Default rules should have subcategories."""
        rules = load_default_rules()
        assert "test" in rules.subcategories


class TestFindRulesFile:
    """Tests for find_rules_file function."""

    def test_finds_dotfile_yaml(self, tmp_path):
        """Should find .layout-scanner-rules.yaml."""
        rules_file = tmp_path / ".layout-scanner-rules.yaml"
        rules_file.write_text("version: '1.0'")
        found = find_rules_file(tmp_path)
        assert found == rules_file

    def test_finds_dotfile_yml(self, tmp_path):
        """Should find .layout-scanner-rules.yml."""
        rules_file = tmp_path / ".layout-scanner-rules.yml"
        rules_file.write_text("version: '1.0'")
        found = find_rules_file(tmp_path)
        assert found == rules_file

    def test_finds_non_dotfile_yaml(self, tmp_path):
        """Should find layout-scanner-rules.yaml."""
        rules_file = tmp_path / "layout-scanner-rules.yaml"
        rules_file.write_text("version: '1.0'")
        found = find_rules_file(tmp_path)
        assert found == rules_file

    def test_finds_non_dotfile_yml(self, tmp_path):
        """Should find layout-scanner-rules.yml."""
        rules_file = tmp_path / "layout-scanner-rules.yml"
        rules_file.write_text("version: '1.0'")
        found = find_rules_file(tmp_path)
        assert found == rules_file

    def test_priority_order(self, tmp_path):
        """Should prefer dotfile yaml over non-dotfile."""
        (tmp_path / ".layout-scanner-rules.yaml").write_text("version: '1.0'")
        (tmp_path / "layout-scanner-rules.yaml").write_text("version: '2.0'")
        found = find_rules_file(tmp_path)
        assert found.name == ".layout-scanner-rules.yaml"

    def test_returns_none_when_not_found(self, tmp_path):
        """Should return None when no rules file found."""
        found = find_rules_file(tmp_path)
        assert found is None


class TestSaveRules:
    """Tests for save_rules function."""

    def test_save_and_load_roundtrip(self, tmp_path):
        """Saved rules should be loadable."""
        original = RuleSet(
            path_rules={"vendor": ["vendor/"]},
            filename_rules={"test": [r"^test_.*\.py$"]},
            extension_rules={"config": [".json"]},
            weights={"path": 0.95, "filename": 0.85, "extension": 0.45},
            categories=["source", "test", "custom"],
            subcategories={"test": ["unit", "integration"]},
            version="2.0",
        )
        output_path = tmp_path / "saved_rules.yaml"
        save_rules(original, output_path)

        loaded = load_rules(output_path)
        assert loaded.version == original.version
        assert loaded.weights == original.weights
        assert loaded.path_rules == original.path_rules
        assert loaded.filename_rules == original.filename_rules
        assert set(loaded.categories) == set(original.categories)

    def test_creates_parent_directories(self, tmp_path):
        """Should create parent directories if needed."""
        output_path = tmp_path / "subdir" / "nested" / "rules.yaml"
        rules = RuleSet()
        save_rules(rules, output_path)
        assert output_path.exists()


class TestDefaultWeightsAndCategories:
    """Tests for module-level defaults."""

    def test_default_weights_complete(self):
        """DEFAULT_WEIGHTS should have all signal types."""
        assert "path" in DEFAULT_WEIGHTS
        assert "filename" in DEFAULT_WEIGHTS
        assert "extension" in DEFAULT_WEIGHTS

    def test_default_weights_sum(self):
        """DEFAULT_WEIGHTS should sum to approximately 2.2."""
        total = sum(DEFAULT_WEIGHTS.values())
        assert 2.0 < total < 2.5  # Reasonable range

    def test_default_categories_complete(self):
        """DEFAULT_CATEGORIES should have expected categories."""
        assert "source" in DEFAULT_CATEGORIES
        assert "test" in DEFAULT_CATEGORIES
        assert "config" in DEFAULT_CATEGORIES
        assert "generated" in DEFAULT_CATEGORIES
        assert "docs" in DEFAULT_CATEGORIES
        assert "vendor" in DEFAULT_CATEGORIES
        assert "other" in DEFAULT_CATEGORIES

    def test_default_subcategories_structure(self):
        """DEFAULT_SUBCATEGORIES should have test subcategories."""
        assert "test" in DEFAULT_SUBCATEGORIES
        assert "unit" in DEFAULT_SUBCATEGORIES["test"]
        assert "integration" in DEFAULT_SUBCATEGORIES["test"]


class TestRulesIntegration:
    """Integration tests for rule loading and merging."""

    def test_load_and_merge_workflow(self, tmp_path):
        """Should support typical load and merge workflow."""
        # Create a custom rules file
        custom_rules_file = tmp_path / "custom.yaml"
        custom_rules_file.write_text("""
version: "1.0"
weights:
  path: 0.95
path_rules:
  infra:
    - "terraform/"
    - "k8s/"
subcategories:
  test:
    - benchmark
  infra:
    - terraform
    - kubernetes
""")
        # Load default and custom
        default_rules = load_default_rules()
        custom_rules = load_rules(custom_rules_file)
        merged = merge_rules(default_rules, custom_rules)

        # Verify merge
        assert merged.weights["path"] == 0.95
        assert "infra" in merged.path_rules
        assert "vendor" in merged.path_rules  # From default
        assert "benchmark" in merged.subcategories["test"]
        assert "unit" in merged.subcategories["test"]  # From default

    def test_subcategory_classification_valid(self, tmp_path):
        """Subcategory classifications should be valid."""
        rules = load_default_rules()
        # Verify test::unit is valid
        assert rules.is_valid_category("test::unit")
        assert rules.is_valid_category("test::integration")
        assert rules.is_valid_category("test::e2e")
        # Verify invalid ones fail
        assert not rules.is_valid_category("test::invalid")
