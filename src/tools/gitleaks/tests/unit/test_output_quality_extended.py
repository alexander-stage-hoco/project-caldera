"""Extended tests for checks/output_quality.py covering all validation paths."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.output_quality import _validate_caldera_envelope, run_output_quality_checks


# ---------------------------------------------------------------------------
# _validate_caldera_envelope - Caldera envelope format (metadata + data)
# ---------------------------------------------------------------------------
class TestValidateCalderaEnvelopeFormat:
    """Test the new Caldera envelope format validation path."""

    def test_valid_envelope(self) -> None:
        """Complete valid envelope should produce no errors."""
        payload = {
            "metadata": {
                "tool_name": "gitleaks",
                "tool_version": "8.18.4",
                "run_id": "run-1",
                "repo_id": "repo-1",
                "branch": "main",
                "commit": "a" * 40,
                "timestamp": "2026-01-01T00:00:00Z",
                "schema_version": "1.0.0",
            },
            "data": {
                "tool": "gitleaks",
                "tool_version": "8.18.4",
                "total_secrets": 0,
                "findings": [],
            },
        }
        errors = _validate_caldera_envelope(payload)
        assert errors == []

    def test_missing_metadata_fields(self) -> None:
        """Missing required metadata fields should produce errors."""
        payload = {
            "metadata": {"tool_name": "gitleaks"},
            "data": {
                "tool": "gitleaks",
                "tool_version": "8.18.4",
                "total_secrets": 0,
                "findings": [],
            },
        }
        errors = _validate_caldera_envelope(payload)
        assert any("Missing metadata field" in e for e in errors)

    def test_wrong_tool_name(self) -> None:
        """tool_name not 'gitleaks' should produce error."""
        payload = {
            "metadata": {
                "tool_name": "trivy",
                "tool_version": "1.0",
                "run_id": "r",
                "repo_id": "r",
                "branch": "main",
                "commit": "a" * 40,
                "timestamp": "t",
                "schema_version": "1.0.0",
            },
            "data": {
                "tool": "gitleaks",
                "tool_version": "1.0",
                "total_secrets": 0,
                "findings": [],
            },
        }
        errors = _validate_caldera_envelope(payload)
        assert any("tool_name must be 'gitleaks'" in e for e in errors)

    def test_missing_data_fields(self) -> None:
        """Missing required data fields should produce errors."""
        payload = {
            "metadata": {
                "tool_name": "gitleaks",
                "tool_version": "1.0",
                "run_id": "r",
                "repo_id": "r",
                "branch": "main",
                "commit": "a" * 40,
                "timestamp": "t",
                "schema_version": "1.0.0",
            },
            "data": {},
        }
        errors = _validate_caldera_envelope(payload)
        assert any("Missing data field" in e for e in errors)

    def test_wrong_data_tool(self) -> None:
        """data.tool not 'gitleaks' should produce error."""
        payload = {
            "metadata": {
                "tool_name": "gitleaks",
                "tool_version": "1.0",
                "run_id": "r",
                "repo_id": "r",
                "branch": "main",
                "commit": "a" * 40,
                "timestamp": "t",
                "schema_version": "1.0.0",
            },
            "data": {
                "tool": "wrong",
                "tool_version": "1.0",
                "total_secrets": 0,
                "findings": [],
            },
        }
        errors = _validate_caldera_envelope(payload)
        assert any("data.tool must be 'gitleaks'" in e for e in errors)

    def test_total_secrets_not_int(self) -> None:
        """total_secrets must be an integer."""
        payload = {
            "metadata": {
                "tool_name": "gitleaks",
                "tool_version": "1.0",
                "run_id": "r",
                "repo_id": "r",
                "branch": "main",
                "commit": "a" * 40,
                "timestamp": "t",
                "schema_version": "1.0.0",
            },
            "data": {
                "tool": "gitleaks",
                "tool_version": "1.0",
                "total_secrets": "five",
                "findings": [],
            },
        }
        errors = _validate_caldera_envelope(payload)
        assert any("total_secrets must be an integer" in e for e in errors)

    def test_findings_not_list(self) -> None:
        """findings must be a list."""
        payload = {
            "metadata": {
                "tool_name": "gitleaks",
                "tool_version": "1.0",
                "run_id": "r",
                "repo_id": "r",
                "branch": "main",
                "commit": "a" * 40,
                "timestamp": "t",
                "schema_version": "1.0.0",
            },
            "data": {
                "tool": "gitleaks",
                "tool_version": "1.0",
                "total_secrets": 0,
                "findings": "not-a-list",
            },
        }
        errors = _validate_caldera_envelope(payload)
        assert any("findings must be a list" in e for e in errors)


# ---------------------------------------------------------------------------
# _validate_caldera_envelope - Legacy format (results wrapper)
# ---------------------------------------------------------------------------
class TestValidateLegacyFormat:
    """Test the legacy format validation path."""

    def test_valid_legacy(self) -> None:
        """Complete valid legacy format should have no errors."""
        payload = {
            "schema_version": "2.0.0",
            "generated_at": "2026-01-01T00:00:00Z",
            "repo_name": "test",
            "repo_path": "/tmp/test",
            "results": {
                "tool": "gitleaks",
                "tool_version": "8.18.4",
                "total_secrets": 0,
                "findings": [],
            },
        }
        errors = _validate_caldera_envelope(payload)
        assert errors == []

    def test_missing_root_fields(self) -> None:
        """Missing root-level fields in legacy format."""
        payload = {
            "results": {
                "tool": "gitleaks",
                "tool_version": "1.0",
                "total_secrets": 0,
                "findings": [],
            },
        }
        errors = _validate_caldera_envelope(payload)
        assert any("Missing root field" in e for e in errors)

    def test_wrong_results_tool(self) -> None:
        """results.tool not 'gitleaks' should produce error."""
        payload = {
            "schema_version": "2.0.0",
            "generated_at": "t",
            "repo_name": "test",
            "repo_path": "/tmp/test",
            "results": {
                "tool": "semgrep",
                "tool_version": "1.0",
                "total_secrets": 0,
                "findings": [],
            },
        }
        errors = _validate_caldera_envelope(payload)
        assert any("results.tool must be 'gitleaks'" in e for e in errors)

    def test_results_total_secrets_not_int(self) -> None:
        payload = {
            "schema_version": "2.0.0",
            "generated_at": "t",
            "repo_name": "test",
            "repo_path": "/tmp/test",
            "results": {
                "tool": "gitleaks",
                "tool_version": "1.0",
                "total_secrets": 3.5,
                "findings": [],
            },
        }
        errors = _validate_caldera_envelope(payload)
        assert any("total_secrets must be an integer" in e for e in errors)

    def test_results_findings_not_list(self) -> None:
        payload = {
            "schema_version": "2.0.0",
            "generated_at": "t",
            "repo_name": "test",
            "repo_path": "/tmp/test",
            "results": {
                "tool": "gitleaks",
                "tool_version": "1.0",
                "total_secrets": 0,
                "findings": {},
            },
        }
        errors = _validate_caldera_envelope(payload)
        assert any("findings must be a list" in e for e in errors)


# ---------------------------------------------------------------------------
# _validate_caldera_envelope - Unknown format
# ---------------------------------------------------------------------------
class TestValidateUnknownFormat:
    """Test unknown/invalid format path."""

    def test_unknown_format(self) -> None:
        """Neither metadata+data nor results -> error."""
        payload = {"something_else": True}
        errors = _validate_caldera_envelope(payload)
        assert any("Missing required envelope structure" in e for e in errors)


# ---------------------------------------------------------------------------
# run_output_quality_checks - integration paths
# ---------------------------------------------------------------------------
class TestRunOutputQualityChecks:
    """Test run_output_quality_checks wrapper function."""

    def test_with_root_key(self) -> None:
        """Analysis with _root key for schema validation."""
        root = {
            "metadata": {
                "tool_name": "gitleaks",
                "tool_version": "1.0",
                "run_id": "r",
                "repo_id": "r",
                "branch": "main",
                "commit": "a" * 40,
                "timestamp": "t",
                "schema_version": "1.0.0",
            },
            "data": {
                "tool": "gitleaks",
                "tool_version": "1.0",
                "total_secrets": 0,
                "findings": [],
            },
        }
        analysis = {"_root": root}
        results = run_output_quality_checks(analysis)

        assert len(results) >= 1
        assert results[0].check_id == "OQ-1"
        assert results[0].passed is True

    def test_analysis_is_envelope_directly(self) -> None:
        """Analysis dict itself has metadata/data -> use it as root."""
        analysis = {
            "metadata": {
                "tool_name": "gitleaks",
                "tool_version": "1.0",
                "run_id": "r",
                "repo_id": "r",
                "branch": "main",
                "commit": "a" * 40,
                "timestamp": "t",
                "schema_version": "1.0.0",
            },
            "data": {
                "tool": "gitleaks",
                "tool_version": "1.0",
                "total_secrets": 0,
                "findings": [],
            },
        }
        results = run_output_quality_checks(analysis)
        assert results[0].passed is True

    def test_analysis_is_results_directly(self) -> None:
        """Analysis dict has 'results' key -> use it as root."""
        analysis = {
            "schema_version": "2.0.0",
            "generated_at": "t",
            "repo_name": "test",
            "repo_path": "/tmp",
            "results": {
                "tool": "gitleaks",
                "tool_version": "1.0",
                "total_secrets": 0,
                "findings": [],
            },
        }
        results = run_output_quality_checks(analysis)
        assert results[0].passed is True

    def test_no_root_no_envelope_fails(self) -> None:
        """Analysis without _root and without envelope keys -> FAIL."""
        analysis = {"total_secrets": 0, "findings": []}
        results = run_output_quality_checks(analysis)

        assert len(results) == 1
        assert results[0].check_id == "OQ-1"
        assert results[0].passed is False
        assert "Missing root wrapper" in results[0].message

    def test_validation_errors_shown(self) -> None:
        """When validation produces errors, they should appear in actual."""
        root = {"metadata": {}, "data": {}}
        analysis = {"_root": root}
        results = run_output_quality_checks(analysis)

        assert results[0].passed is False
        assert isinstance(results[0].actual, list)
        assert len(results[0].actual) > 0
