"""Unit tests for checks/integration.py module."""

import pytest

from checks.integration import (
    CATEGORY,
    check_age_for_patch_currency,
    check_cve_counts_for_security,
    check_directory_rollups,
    check_evidence_transformability,
    check_iac_for_infrastructure,
    check_sbom_for_inventory,
    run_integration_checks,
)


class TestCheckCveCountsForSecurity:
    """Tests for check_cve_counts_for_security function."""

    def test_all_counts_present(self, sample_normalized_analysis):
        """Test when all CVE counts are present."""
        result = check_cve_counts_for_security(sample_normalized_analysis)

        assert result.passed is True
        assert result.category == CATEGORY
        assert "CVE counts present" in result.message

    def test_missing_critical_count(self):
        """Test when critical_count is missing."""
        analysis = {
            "summary": {
                "high_count": 5,
                "total_vulnerabilities": 10,
            }
        }

        result = check_cve_counts_for_security(analysis)

        assert result.passed is False
        assert "critical_count" in result.message

    def test_all_counts_missing(self):
        """Test when all counts are missing."""
        analysis = {"summary": {}}

        result = check_cve_counts_for_security(analysis)

        assert result.passed is False


class TestCheckAgeForPatchCurrency:
    """Tests for check_age_for_patch_currency function."""

    def test_age_present(self, sample_normalized_analysis):
        """Test when oldest_cve_days is present."""
        result = check_age_for_patch_currency(sample_normalized_analysis)

        assert result.passed is True
        assert "Patch currency metrics present" in result.message

    def test_age_missing(self):
        """Test when oldest_cve_days is missing."""
        analysis = {"summary": {}}

        result = check_age_for_patch_currency(analysis)

        assert result.passed is False
        assert "oldest_cve_days" in result.message

    def test_vuln_age_days_present(self, sample_normalized_analysis):
        """Test that vulnerabilities have age_days field."""
        result = check_age_for_patch_currency(sample_normalized_analysis)

        assert result.passed is True

    def test_vuln_age_days_missing(self):
        """Test when vulnerabilities are missing age_days."""
        analysis = {
            "summary": {"oldest_cve_days": 100},
            "vulnerabilities": [
                {"id": "CVE-1"},  # Missing age_days
            ],
        }

        result = check_age_for_patch_currency(analysis)

        assert result.passed is False
        assert "age_days missing" in result.message


class TestCheckIacForInfrastructure:
    """Tests for check_iac_for_infrastructure function."""

    def test_iac_present(self, sample_normalized_analysis):
        """Test when IaC data is present."""
        result = check_iac_for_infrastructure(sample_normalized_analysis)

        assert result.passed is True
        assert "IaC metrics present" in result.message

    def test_iac_fields_missing(self):
        """Test when IaC fields are missing."""
        analysis = {
            "iac_misconfigurations": {
                "total_count": 0,
                # Missing critical_count, high_count, misconfigurations
            }
        }

        result = check_iac_for_infrastructure(analysis)

        assert result.passed is False
        assert "Missing" in result.message


class TestCheckDirectoryRollups:
    """Tests for check_directory_rollups function."""

    def test_valid_rollups(self, sample_normalized_analysis):
        """Test with valid directory rollups."""
        result = check_directory_rollups(sample_normalized_analysis)

        assert result.passed is True
        assert "Directory rollups valid" in result.message

    def test_missing_directories(self):
        """Test when directories section is missing."""
        analysis = {}

        result = check_directory_rollups(analysis)

        assert result.passed is False
        assert "missing" in result.message.lower()

    def test_missing_directory_count(self):
        """Test when directory_count is missing."""
        analysis = {"directories": {"directories": []}}

        result = check_directory_rollups(analysis)

        assert result.passed is False

    def test_missing_direct_recursive(self):
        """Test when directory is missing direct/recursive."""
        analysis = {
            "directories": {
                "directory_count": 1,
                "directories": [
                    {"path": "."}  # Missing direct and recursive
                ],
            }
        }

        result = check_directory_rollups(analysis)

        assert result.passed is False

    def test_recursive_less_than_direct(self):
        """Test when recursive count is less than direct."""
        analysis = {
            "directories": {
                "directory_count": 1,
                "directories": [
                    {
                        "path": ".",
                        "direct": {"vulnerability_count": 10},
                        "recursive": {"vulnerability_count": 5},  # Should be >= direct
                    }
                ],
            }
        }

        result = check_directory_rollups(analysis)

        assert result.passed is False


class TestCheckEvidenceTransformability:
    """Tests for check_evidence_transformability function."""

    def test_valid_structure(self, sample_normalized_analysis):
        """Test with valid DD-compatible structure."""
        result = check_evidence_transformability(sample_normalized_analysis)

        assert result.passed is True
        assert "compatible with DD evidence schema" in result.message

    def test_missing_dd_fields(self):
        """Test when DD-required fields are missing."""
        analysis = {
            "summary": {},
            # Missing repository, timestamp
        }

        result = check_evidence_transformability(analysis)

        assert result.passed is False
        assert "Missing DD-required" in result.message

    def test_vuln_missing_target(self):
        """Test when vulnerabilities are missing target field."""
        analysis = {
            "repository": "test",
            "timestamp": "2026-01-01T00:00:00Z",
            "summary": {
                "critical_count": 1,
                "high_count": 2,
                "total_vulnerabilities": 3,
            },
            "vulnerabilities": [
                {"id": "CVE-1"},  # Missing target
            ],
        }

        result = check_evidence_transformability(analysis)

        assert result.passed is False
        assert "target field" in result.message


class TestCheckSbomForInventory:
    """Tests for check_sbom_for_inventory function."""

    def test_valid_sbom(self, sample_normalized_analysis):
        """Test with valid SBOM data."""
        result = check_sbom_for_inventory(sample_normalized_analysis)

        assert result.passed is True
        assert "SBOM present" in result.message

    def test_missing_sbom(self):
        """Test when SBOM section is missing."""
        analysis = {}

        result = check_sbom_for_inventory(analysis)

        assert result.passed is False
        assert "Missing sbom section" in result.message

    def test_missing_sbom_fields(self):
        """Test when SBOM fields are missing."""
        analysis = {
            "sbom": {
                "format": "trivy-json",
                # Missing total_packages, vulnerable_packages, clean_packages
            }
        }

        result = check_sbom_for_inventory(analysis)

        assert result.passed is False
        assert "Missing SBOM fields" in result.message


class TestRunIntegrationChecks:
    """Tests for run_integration_checks generator."""

    def test_yields_six_checks(self, sample_normalized_analysis):
        """Test that six checks are yielded."""
        ground_truth = {}

        results = list(run_integration_checks(sample_normalized_analysis, ground_truth))

        assert len(results) == 6

    def test_all_checks_have_category(self, sample_normalized_analysis):
        """Test that all checks have correct category."""
        ground_truth = {}

        results = list(run_integration_checks(sample_normalized_analysis, ground_truth))

        for result in results:
            assert result.category == CATEGORY

    def test_check_ids(self, sample_normalized_analysis):
        """Test that correct check IDs are returned."""
        ground_truth = {}

        results = list(run_integration_checks(sample_normalized_analysis, ground_truth))

        check_ids = [r.check_id for r in results]
        assert "cve_counts_for_security" in check_ids
        assert "age_for_patch_currency" in check_ids
        assert "iac_for_infrastructure" in check_ids
        assert "directory_rollups" in check_ids
        assert "evidence_transformability" in check_ids
        assert "sbom_for_inventory" in check_ids
