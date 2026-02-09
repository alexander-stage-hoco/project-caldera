"""Tests for severity mapper utilities."""

from __future__ import annotations

import pytest

from shared.severity.mapper import (
    SeverityLevel,
    SEVERITY_ORDER,
    PRODUCTION_PATH_PATTERNS,
    normalize_severity,
    compare_severity,
    is_valid_severity,
    escalate_for_production_path,
)


class TestSeverityLevel:
    """Tests for SeverityLevel enum."""

    def test_severity_level_values(self):
        """SeverityLevel should have expected values."""
        assert SeverityLevel.CRITICAL.value == "CRITICAL"
        assert SeverityLevel.HIGH.value == "HIGH"
        assert SeverityLevel.MEDIUM.value == "MEDIUM"
        assert SeverityLevel.LOW.value == "LOW"
        assert SeverityLevel.INFO.value == "INFO"
        assert SeverityLevel.UNKNOWN.value == "UNKNOWN"

    def test_severity_level_str(self):
        """SeverityLevel should convert to string."""
        assert str(SeverityLevel.CRITICAL) == "CRITICAL"
        assert str(SeverityLevel.HIGH) == "HIGH"


class TestSeverityOrder:
    """Tests for SEVERITY_ORDER constant."""

    def test_severity_order_contains_all_levels(self):
        """SEVERITY_ORDER should contain all severity levels."""
        assert "CRITICAL" in SEVERITY_ORDER
        assert "HIGH" in SEVERITY_ORDER
        assert "MEDIUM" in SEVERITY_ORDER
        assert "LOW" in SEVERITY_ORDER
        assert "INFO" in SEVERITY_ORDER
        assert "UNKNOWN" in SEVERITY_ORDER

    def test_severity_order_is_ascending(self):
        """SEVERITY_ORDER should be in ascending order."""
        assert SEVERITY_ORDER["UNKNOWN"] < SEVERITY_ORDER["INFO"]
        assert SEVERITY_ORDER["INFO"] < SEVERITY_ORDER["LOW"]
        assert SEVERITY_ORDER["LOW"] < SEVERITY_ORDER["MEDIUM"]
        assert SEVERITY_ORDER["MEDIUM"] < SEVERITY_ORDER["HIGH"]
        assert SEVERITY_ORDER["HIGH"] < SEVERITY_ORDER["CRITICAL"]


class TestNormalizeSeverity:
    """Tests for normalize_severity function."""

    def test_normalize_uppercase(self):
        """Should return uppercase as-is."""
        assert normalize_severity("HIGH") == "HIGH"
        assert normalize_severity("CRITICAL") == "CRITICAL"

    def test_normalize_lowercase(self):
        """Should normalize lowercase to uppercase."""
        assert normalize_severity("high") == "HIGH"
        assert normalize_severity("critical") == "CRITICAL"
        assert normalize_severity("medium") == "MEDIUM"

    def test_normalize_mixed_case(self):
        """Should normalize mixed case to uppercase."""
        assert normalize_severity("High") == "HIGH"
        assert normalize_severity("MEDIUM") == "MEDIUM"

    def test_normalize_aliases(self):
        """Should map common aliases."""
        assert normalize_severity("warning") == "MEDIUM"
        assert normalize_severity("error") == "HIGH"
        assert normalize_severity("blocker") == "CRITICAL"
        assert normalize_severity("major") == "HIGH"
        assert normalize_severity("minor") == "MEDIUM"
        assert normalize_severity("note") == "LOW"
        assert normalize_severity("hint") == "INFO"
        assert normalize_severity("informational") == "INFO"

    def test_normalize_none(self):
        """Should return default for None."""
        assert normalize_severity(None) == "MEDIUM"
        assert normalize_severity(None, default="LOW") == "LOW"

    def test_normalize_empty_string(self):
        """Should return default for empty string."""
        assert normalize_severity("") == "MEDIUM"
        assert normalize_severity("", default="HIGH") == "HIGH"

    def test_normalize_unknown_value(self):
        """Should return default for unknown values."""
        assert normalize_severity("foobar") == "MEDIUM"
        assert normalize_severity("foobar", default="LOW") == "LOW"


class TestIsValidSeverity:
    """Tests for is_valid_severity function."""

    def test_valid_severities(self):
        """Should return True for valid severities."""
        assert is_valid_severity("CRITICAL") is True
        assert is_valid_severity("HIGH") is True
        assert is_valid_severity("MEDIUM") is True
        assert is_valid_severity("LOW") is True
        assert is_valid_severity("INFO") is True
        assert is_valid_severity("UNKNOWN") is True

    def test_valid_lowercase(self):
        """Should return True for lowercase valid severities."""
        assert is_valid_severity("high") is True
        assert is_valid_severity("medium") is True

    def test_invalid_severities(self):
        """Should return False for invalid severities."""
        assert is_valid_severity("FOOBAR") is False
        assert is_valid_severity("") is False
        assert is_valid_severity(None) is False


class TestCompareSeverity:
    """Tests for compare_severity function."""

    def test_compare_equal(self):
        """Should return 0 for equal severities."""
        assert compare_severity("HIGH", "HIGH") == 0
        assert compare_severity("MEDIUM", "MEDIUM") == 0

    def test_compare_greater(self):
        """Should return 1 when first is greater."""
        assert compare_severity("HIGH", "LOW") == 1
        assert compare_severity("CRITICAL", "MEDIUM") == 1
        assert compare_severity("MEDIUM", "INFO") == 1

    def test_compare_less(self):
        """Should return -1 when first is less."""
        assert compare_severity("LOW", "HIGH") == -1
        assert compare_severity("MEDIUM", "CRITICAL") == -1
        assert compare_severity("INFO", "MEDIUM") == -1

    def test_compare_normalizes_input(self):
        """Should normalize input before comparing."""
        assert compare_severity("high", "HIGH") == 0
        assert compare_severity("warning", "MEDIUM") == 0


class TestEscalateForProductionPath:
    """Tests for escalate_for_production_path function."""

    def test_escalate_medium_to_high(self):
        """Should escalate MEDIUM to HIGH for production paths."""
        assert escalate_for_production_path("MEDIUM", ".env.production") == "HIGH"
        assert escalate_for_production_path("MEDIUM", "config/prod/db.yaml") == "HIGH"
        assert escalate_for_production_path("MEDIUM", "deploy/prod/secrets.yaml") == "HIGH"

    def test_escalate_high_to_critical(self):
        """Should escalate HIGH to CRITICAL for production paths."""
        assert escalate_for_production_path("HIGH", ".env.production") == "CRITICAL"
        assert escalate_for_production_path("HIGH", "production/config.yaml") == "CRITICAL"

    def test_no_escalate_non_production(self):
        """Should not escalate for non-production paths."""
        assert escalate_for_production_path("MEDIUM", "src/utils.py") == "MEDIUM"
        assert escalate_for_production_path("HIGH", "tests/test_app.py") == "HIGH"
        assert escalate_for_production_path("MEDIUM", ".env.development") == "MEDIUM"

    def test_no_escalate_critical(self):
        """Should not escalate CRITICAL (already max)."""
        assert escalate_for_production_path("CRITICAL", ".env.production") == "CRITICAL"

    def test_empty_path(self):
        """Should return original for empty path."""
        assert escalate_for_production_path("MEDIUM", "") == "MEDIUM"

    def test_custom_patterns(self):
        """Should use custom patterns when provided."""
        custom_patterns = ["custom/", "special.config"]
        assert escalate_for_production_path("MEDIUM", "custom/file.py", custom_patterns) == "HIGH"
        assert escalate_for_production_path("MEDIUM", "special.config", custom_patterns) == "HIGH"
        assert escalate_for_production_path("MEDIUM", ".env.production", custom_patterns) == "MEDIUM"


class TestProductionPathPatterns:
    """Tests for PRODUCTION_PATH_PATTERNS constant."""

    def test_contains_expected_patterns(self):
        """Should contain expected production path patterns."""
        assert ".env.production" in PRODUCTION_PATH_PATTERNS
        assert ".env.prod" in PRODUCTION_PATH_PATTERNS
        assert "prod/" in PRODUCTION_PATH_PATTERNS
        assert "production/" in PRODUCTION_PATH_PATTERNS
        assert ".aws/credentials" in PRODUCTION_PATH_PATTERNS
