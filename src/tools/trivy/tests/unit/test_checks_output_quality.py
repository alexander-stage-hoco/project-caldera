"""Unit tests for checks/output_quality.py module."""

import pytest

from checks.output_quality import (
    CATEGORY,
    check_json_validity,
    check_numeric_types,
    check_provenance,
    check_required_summary_fields,
    check_required_vuln_fields,
    check_schema_version,
    check_timestamp_format,
    run_output_quality_checks,
)


class TestCheckJsonValidity:
    """Tests for check_json_validity function."""

    def test_valid_json_structure(self, sample_normalized_analysis):
        """Test with valid JSON structure."""
        result = check_json_validity(sample_normalized_analysis)

        assert result.passed is True
        assert result.category == CATEGORY
        assert result.check_id == "json_validity"

    def test_missing_schema_version(self):
        """Test with missing schema_version."""
        analysis = {
            "repository": "test",
            "timestamp": "2026-01-01T00:00:00Z",
            "summary": {},
        }

        result = check_json_validity(analysis)

        assert result.passed is False
        assert "schema_version" in result.message

    def test_missing_summary(self):
        """Test with missing summary."""
        analysis = {
            "schema_version": "1.0.0",
            "repository": "test",
            "timestamp": "2026-01-01T00:00:00Z",
        }

        result = check_json_validity(analysis)

        assert result.passed is False
        assert "summary" in result.message

    def test_missing_multiple_keys(self):
        """Test with multiple missing keys."""
        analysis = {}

        result = check_json_validity(analysis)

        assert result.passed is False


class TestCheckSchemaVersion:
    """Tests for check_schema_version function."""

    def test_valid_version_1_0_0(self):
        """Test with valid version 1.0.0."""
        result = check_schema_version({"schema_version": "1.0.0"})

        assert result.passed is True

    def test_valid_version_1_0(self):
        """Test with valid version 1.0."""
        result = check_schema_version({"schema_version": "1.0"})

        assert result.passed is True

    def test_valid_version_1_1_0(self):
        """Test with valid version 1.1.0."""
        result = check_schema_version({"schema_version": "1.1.0"})

        assert result.passed is True

    def test_missing_schema_version(self):
        """Test with missing schema_version."""
        result = check_schema_version({})

        assert result.passed is False
        assert "missing" in result.message.lower()

    def test_invalid_schema_version(self):
        """Test with invalid schema_version."""
        result = check_schema_version({"schema_version": "2.0.0"})

        assert result.passed is False
        assert "Unexpected" in result.message

    def test_non_string_schema_version(self):
        """Test with non-string schema_version."""
        result = check_schema_version({"schema_version": 1.0})

        assert result.passed is False
        assert "string" in result.message


class TestCheckRequiredSummaryFields:
    """Tests for check_required_summary_fields function."""

    def test_all_fields_present(self, sample_normalized_analysis):
        """Test with all required fields present."""
        result = check_required_summary_fields(sample_normalized_analysis)

        assert result.passed is True

    def test_missing_field(self):
        """Test with missing field."""
        analysis = {
            "summary": {
                "total_vulnerabilities": 5,
                "critical_count": 1,
                # Missing high_count and others
            }
        }

        result = check_required_summary_fields(analysis)

        assert result.passed is False
        assert "Missing" in result.message

    def test_empty_summary(self):
        """Test with empty summary."""
        result = check_required_summary_fields({"summary": {}})

        assert result.passed is False


class TestCheckRequiredVulnFields:
    """Tests for check_required_vuln_fields function."""

    def test_valid_vulnerabilities(self, sample_normalized_analysis):
        """Test with valid vulnerability entries."""
        result = check_required_vuln_fields(sample_normalized_analysis)

        assert result.passed is True

    def test_empty_vulnerabilities(self):
        """Test with empty vulnerabilities list."""
        result = check_required_vuln_fields({"vulnerabilities": []})

        assert result.passed is True
        assert "empty list" in result.message.lower()

    def test_missing_vuln_fields(self):
        """Test with missing vulnerability fields."""
        analysis = {
            "vulnerabilities": [
                {
                    "id": "CVE-2021-0001",
                    # Missing severity, package, etc.
                }
            ]
        }

        result = check_required_vuln_fields(analysis)

        assert result.passed is False


class TestCheckProvenance:
    """Tests for check_provenance function."""

    def test_all_provenance_present(self, sample_normalized_analysis):
        """Test with all provenance fields present."""
        result = check_provenance(sample_normalized_analysis)

        assert result.passed is True

    def test_missing_tool(self):
        """Test with missing tool field."""
        analysis = {
            "tool_version": "0.58.0",
            "timestamp": "2026-01-01T00:00:00Z",
            "repository": "test",
        }

        result = check_provenance(analysis)

        assert result.passed is False
        assert "tool" in result.message.lower()


class TestCheckTimestampFormat:
    """Tests for check_timestamp_format function."""

    def test_valid_timestamp_with_z(self):
        """Test with valid ISO8601 timestamp with Z."""
        result = check_timestamp_format({"timestamp": "2026-01-15T10:00:00Z"})

        assert result.passed is True

    def test_valid_timestamp_with_offset(self):
        """Test with valid ISO8601 timestamp with offset."""
        result = check_timestamp_format({"timestamp": "2026-01-15T10:00:00+00:00"})

        assert result.passed is True

    def test_missing_timestamp(self):
        """Test with missing timestamp."""
        result = check_timestamp_format({})

        assert result.passed is False
        assert "missing" in result.message.lower()

    def test_invalid_timestamp_format(self):
        """Test with invalid timestamp format."""
        result = check_timestamp_format({"timestamp": "not-a-date"})

        assert result.passed is False
        assert "Invalid" in result.message


class TestCheckNumericTypes:
    """Tests for check_numeric_types function."""

    def test_correct_types(self, sample_normalized_analysis):
        """Test with correct numeric types."""
        result = check_numeric_types(sample_normalized_analysis)

        assert result.passed is True

    def test_string_instead_of_int(self):
        """Test with string where int expected."""
        analysis = {
            "summary": {
                "total_vulnerabilities": "5",  # Should be int
                "critical_count": 1,
                "high_count": 2,
                "medium_count": 2,
                "low_count": 0,
                "fix_available_count": 5,
                "dependency_count": 3,
                "oldest_cve_days": 100,
                "targets_scanned": 1,
                "fix_available_pct": 100.0,
            }
        }

        result = check_numeric_types(analysis)

        assert result.passed is False
        assert "total_vulnerabilities" in result.message

    def test_string_instead_of_float(self):
        """Test with string where float expected."""
        analysis = {
            "summary": {
                "total_vulnerabilities": 5,
                "critical_count": 1,
                "high_count": 2,
                "medium_count": 2,
                "low_count": 0,
                "fix_available_count": 5,
                "dependency_count": 3,
                "oldest_cve_days": 100,
                "targets_scanned": 1,
                "fix_available_pct": "100.0",  # Should be numeric
            }
        }

        result = check_numeric_types(analysis)

        assert result.passed is False


class TestRunOutputQualityChecks:
    """Tests for run_output_quality_checks generator."""

    def test_yields_all_checks(self, sample_normalized_analysis, sample_ground_truth_flat):
        """Test that all checks are yielded."""
        results = list(
            run_output_quality_checks(sample_normalized_analysis, sample_ground_truth_flat)
        )

        assert len(results) == 7
        check_ids = [r.check_id for r in results]
        assert "json_validity" in check_ids
        assert "schema_version" in check_ids
        assert "required_summary_fields" in check_ids
        assert "required_vuln_fields" in check_ids
        assert "provenance" in check_ids
        assert "timestamp_format" in check_ids
        assert "numeric_types" in check_ids

    def test_all_same_category(self, sample_normalized_analysis, sample_ground_truth_flat):
        """Test that all results have correct category."""
        results = list(
            run_output_quality_checks(sample_normalized_analysis, sample_ground_truth_flat)
        )

        for result in results:
            assert result.category == CATEGORY
