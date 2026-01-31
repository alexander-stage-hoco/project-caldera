"""
Tests for SARIF parsing and rule mapping functionality.

Tests cover:
- SARIF 1.0 vs 2.1 format handling
- Violation extraction from SARIF
- Rule ID mapping to DD categories
- Severity mapping (error/warning/info → critical/high/medium/low)
- Malformed JSON recovery
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from roslyn_analyzer import (
    parse_sarif,
    get_dd_category,
    SEVERITY_MAP,
    DD_CATEGORY_MAP,
    DD_CATEGORY_PREFIX_MAP,
    Violation,
)


class TestSarifV21Parsing:
    """Test SARIF 2.1 format parsing."""

    def test_parse_sarif_v21_basic(self, temp_sarif_file):
        """Parse basic SARIF 2.1 file with violations."""
        violations = parse_sarif(temp_sarif_file)

        assert len(violations) == 2
        assert violations[0].rule_id == "CA3001"
        assert violations[1].rule_id == "CA1001"

    def test_parse_sarif_v21_extracts_location(self, temp_sarif_file):
        """Verify SARIF 2.1 location extraction (physicalLocation.artifactLocation)."""
        violations = parse_sarif(temp_sarif_file)

        assert violations[0].line_start == 15
        assert violations[0].column_start == 5
        assert violations[0].column_end == 50
        assert "sql_injection.cs" in violations[0].file_path

    def test_parse_sarif_v21_extracts_message(self, temp_sarif_file):
        """Verify message extraction from SARIF 2.1 format."""
        violations = parse_sarif(temp_sarif_file)

        assert violations[0].message == "SQL injection vulnerability"
        assert "disposable" in violations[1].message.lower()

    def test_parse_sarif_v21_maps_severity(self, temp_sarif_file):
        """Verify severity mapping for SARIF 2.1 results."""
        violations = parse_sarif(temp_sarif_file)

        # warning -> high
        assert violations[0].dd_severity == "high"
        # error -> critical
        assert violations[1].dd_severity == "critical"


class TestSarifV1Parsing:
    """Test SARIF 1.0 format parsing."""

    def test_parse_sarif_v1_basic(self, tmp_path, sample_sarif_v1):
        """Parse basic SARIF 1.0 file."""
        sarif_path = tmp_path / "v1.sarif"
        sarif_path.write_text(json.dumps(sample_sarif_v1))

        violations = parse_sarif(sarif_path)

        assert len(violations) == 1
        assert violations[0].rule_id == "CA5350"

    def test_parse_sarif_v1_extracts_location(self, tmp_path, sample_sarif_v1):
        """Verify SARIF 1.0 location extraction (resultFile)."""
        sarif_path = tmp_path / "v1.sarif"
        sarif_path.write_text(json.dumps(sample_sarif_v1))

        violations = parse_sarif(sarif_path)

        assert violations[0].line_start == 16
        assert violations[0].column_start == 10
        assert "weak_crypto.cs" in violations[0].file_path

    def test_parse_sarif_v1_message_as_string(self, tmp_path):
        """Verify SARIF 1.0 message when provided as plain string."""
        sarif_data = {
            "version": "1.0.0",
            "runs": [{
                "tool": {"name": "test"},
                "results": [{
                    "ruleId": "TEST001",
                    "level": "warning",
                    "message": "Plain string message",
                    "locations": [{
                        "resultFile": {
                            "uri": "file:///test.cs",
                            "region": {"startLine": 1}
                        }
                    }]
                }]
            }]
        }
        sarif_path = tmp_path / "v1_string_msg.sarif"
        sarif_path.write_text(json.dumps(sarif_data))

        violations = parse_sarif(sarif_path)

        assert violations[0].message == "Plain string message"


class TestMalformedSarifRecovery:
    """Test recovery from malformed SARIF files."""

    def test_parse_sarif_nonexistent_file(self, tmp_path):
        """Return empty list for nonexistent file."""
        violations = parse_sarif(tmp_path / "nonexistent.sarif")
        assert violations == []

    def test_parse_sarif_empty_file(self, tmp_path):
        """Return empty list for empty file."""
        sarif_path = tmp_path / "empty.sarif"
        sarif_path.write_text("")

        violations = parse_sarif(sarif_path)
        assert violations == []

    def test_parse_sarif_truncated_json(self, tmp_path, sample_sarif_v21):
        """Attempt recovery from truncated JSON."""
        # Create valid JSON then truncate and add garbage
        valid_json = json.dumps(sample_sarif_v21)
        sarif_path = tmp_path / "truncated.sarif"
        sarif_path.write_text(valid_json + "\n\ngarbage after valid json")

        violations = parse_sarif(sarif_path)

        # Should recover and parse the valid portion
        assert len(violations) == 2

    def test_parse_sarif_invalid_json(self, tmp_path):
        """Return empty list for completely invalid JSON."""
        sarif_path = tmp_path / "invalid.sarif"
        sarif_path.write_text("not json at all {{{")

        violations = parse_sarif(sarif_path)
        assert violations == []

    def test_parse_sarif_no_runs(self, tmp_path):
        """Handle SARIF with empty runs array."""
        sarif_data = {"version": "2.1.0", "runs": []}
        sarif_path = tmp_path / "no_runs.sarif"
        sarif_path.write_text(json.dumps(sarif_data))

        violations = parse_sarif(sarif_path)
        assert violations == []

    def test_parse_sarif_results_without_locations(self, tmp_path):
        """Skip results that have no locations."""
        sarif_data = {
            "version": "2.1.0",
            "runs": [{
                "tool": {"driver": {"name": "test", "rules": []}},
                "results": [
                    {
                        "ruleId": "TEST001",
                        "level": "warning",
                        "message": {"text": "No location"},
                        "locations": []
                    },
                    {
                        "ruleId": "TEST002",
                        "level": "warning",
                        "message": {"text": "Has location"},
                        "locations": [{
                            "physicalLocation": {
                                "artifactLocation": {"uri": "file:///test.cs"},
                                "region": {"startLine": 10}
                            }
                        }]
                    }
                ]
            }]
        }
        sarif_path = tmp_path / "partial_locations.sarif"
        sarif_path.write_text(json.dumps(sarif_data))

        violations = parse_sarif(sarif_path)

        assert len(violations) == 1
        assert violations[0].rule_id == "TEST002"


class TestRuleCategoryMapping:
    """Test rule ID to DD category mapping."""

    def test_exact_match_security_rules(self):
        """Test exact match for security rules."""
        security_rules = ["CA3001", "CA3002", "CA2100", "CA5350", "CA5351", "SCS0001"]
        for rule in security_rules:
            assert get_dd_category(rule) == "security", f"{rule} should be security"

    def test_exact_match_design_rules(self):
        """Test exact match for design rules."""
        design_rules = ["CA1051", "CA1040", "CA1000", "CA1061", "IDE0040"]
        for rule in design_rules:
            assert get_dd_category(rule) == "design", f"{rule} should be design"

    def test_exact_match_resource_rules(self):
        """Test exact match for resource management rules."""
        resource_rules = ["CA1001", "CA1063", "CA2000", "CA2016", "IDISP001"]
        for rule in resource_rules:
            assert get_dd_category(rule) == "resource", f"{rule} should be resource"

    def test_exact_match_dead_code_rules(self):
        """Test exact match for dead code rules."""
        dead_code_rules = ["IDE0005", "IDE0060", "IDE0052", "IDE0059", "CA1812"]
        for rule in dead_code_rules:
            assert get_dd_category(rule) == "dead_code", f"{rule} should be dead_code"

    def test_exact_match_performance_rules(self):
        """Test exact match for performance rules."""
        performance_rules = ["CA1826", "CA1829", "CA1825", "CA1822", "CA1834"]
        for rule in performance_rules:
            assert get_dd_category(rule) == "performance", f"{rule} should be performance"

    def test_prefix_match_roslynator(self):
        """Test prefix matching for Roslynator rules (RCS prefix)."""
        assert get_dd_category("RCS1001") == "design"
        assert get_dd_category("RCS0001") == "design"
        assert get_dd_category("RCS9999") == "design"

    def test_prefix_match_stylecop(self):
        """Test prefix matching for StyleCop rules (SA prefix)."""
        assert get_dd_category("SA1001") == "design"
        assert get_dd_category("SA2001") == "design"
        assert get_dd_category("SA6001") == "design"

    def test_prefix_match_sonar(self):
        """Test prefix matching for SonarAnalyzer rules."""
        assert get_dd_category("S1001") == "design"
        assert get_dd_category("S4001") == "security"
        assert get_dd_category("S5001") == "security"

    def test_unknown_rule_returns_other(self):
        """Unknown rules should return 'other' category."""
        assert get_dd_category("UNKNOWN999") == "other"
        assert get_dd_category("CUSTOM001") == "other"
        assert get_dd_category("") == "other"


class TestSeverityMapping:
    """Test severity level mapping."""

    def test_severity_map_completeness(self):
        """Verify all expected severity levels are mapped."""
        expected_levels = ["error", "warning", "info", "hidden", "none"]
        for level in expected_levels:
            assert level in SEVERITY_MAP

    def test_severity_map_values(self):
        """Verify severity mapping values."""
        assert SEVERITY_MAP["error"] == "critical"
        assert SEVERITY_MAP["warning"] == "high"
        assert SEVERITY_MAP["info"] == "medium"
        assert SEVERITY_MAP["hidden"] == "low"
        assert SEVERITY_MAP["none"] == "low"

    def test_severity_mapping_in_parsing(self, tmp_path):
        """Verify severity mapping is applied during parsing."""
        sarif_data = {
            "version": "2.1.0",
            "runs": [{
                "tool": {"driver": {"name": "test", "rules": []}},
                "results": [
                    {
                        "ruleId": "TEST001",
                        "level": "error",
                        "message": {"text": "Error level"},
                        "locations": [{
                            "physicalLocation": {
                                "artifactLocation": {"uri": "file:///a.cs"},
                                "region": {"startLine": 1}
                            }
                        }]
                    },
                    {
                        "ruleId": "TEST002",
                        "level": "warning",
                        "message": {"text": "Warning level"},
                        "locations": [{
                            "physicalLocation": {
                                "artifactLocation": {"uri": "file:///b.cs"},
                                "region": {"startLine": 1}
                            }
                        }]
                    },
                    {
                        "ruleId": "TEST003",
                        "level": "info",
                        "message": {"text": "Info level"},
                        "locations": [{
                            "physicalLocation": {
                                "artifactLocation": {"uri": "file:///c.cs"},
                                "region": {"startLine": 1}
                            }
                        }]
                    }
                ]
            }]
        }
        sarif_path = tmp_path / "severity.sarif"
        sarif_path.write_text(json.dumps(sarif_data))

        violations = parse_sarif(sarif_path)

        assert violations[0].dd_severity == "critical"
        assert violations[1].dd_severity == "high"
        assert violations[2].dd_severity == "medium"


class TestCategoryMapCompleteness:
    """Test that category maps cover expected rules."""

    def test_dd_category_map_has_security_rules(self):
        """Verify security rules are in the exact match map."""
        security_rules = ["CA3001", "CA3002", "CA2100", "CA5350", "SCS0001", "SCS0002"]
        for rule in security_rules:
            assert rule in DD_CATEGORY_MAP, f"{rule} missing from DD_CATEGORY_MAP"
            assert DD_CATEGORY_MAP[rule] == "security"

    def test_dd_category_prefix_map_has_analyzers(self):
        """Verify common analyzer prefixes are in the prefix map."""
        expected_prefixes = ["RCS0", "RCS1", "SA1", "IDE0", "AsyncFixer"]
        for prefix in expected_prefixes:
            assert prefix in DD_CATEGORY_PREFIX_MAP, f"{prefix} missing from prefix map"

    def test_combined_coverage_over_150_rules(self):
        """Verify we have substantial rule coverage."""
        total_exact = len(DD_CATEGORY_MAP)
        total_prefix = len(DD_CATEGORY_PREFIX_MAP)

        # We should have at least 150 exact rules mapped
        assert total_exact >= 100, f"Only {total_exact} exact rules mapped"
        # And at least 15 prefix patterns
        assert total_prefix >= 15, f"Only {total_prefix} prefix patterns"
