"""Tests for miscellaneous check modules: license, installation, performance, per_file, cocomo.

These checks mostly call subprocess for the scc binary. We test them using mocking
to avoid needing the actual binary.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from scripts.checks import CheckResult
from scripts.checks.license import (
    check_mit_license,
    check_open_source,
    check_no_usage_fees,
    run_license_checks,
)
from scripts.checks.installation import (
    check_binary_exists,
    check_version,
    check_help_available,
    check_no_dependencies,
    run_installation_checks,
)
from scripts.checks.performance import (
    run_performance_checks,
)
from scripts.checks.cocomo import (
    run_scc_json2,
    check_cocomo_output_present,
    check_custom_params_applied,
    check_preset_values_match,
    run_cocomo_checks,
)
from scripts.checks.per_file import (
    run_scc_by_file,
    check_per_file_json_valid,
    run_per_file_checks,
)


# ---------------------------------------------------------------------------
# Tests: License checks (CL-1 to CL-3) - static checks
# ---------------------------------------------------------------------------

class TestLicenseChecks:
    def test_mit_license(self, tmp_path):
        result = check_mit_license(tmp_path)
        assert result.passed is True
        assert result.check_id == "CL-1"
        assert "MIT" in result.message

    def test_open_source(self, tmp_path):
        result = check_open_source(tmp_path)
        assert result.passed is True
        assert result.check_id == "CL-2"

    def test_no_usage_fees(self, tmp_path):
        result = check_no_usage_fees(tmp_path)
        assert result.passed is True
        assert result.check_id == "CL-3"

    def test_run_license_checks(self, tmp_path):
        results = run_license_checks(tmp_path)
        assert len(results) == 3
        assert all(r.passed for r in results)


# ---------------------------------------------------------------------------
# Tests: Installation checks (IN-1 to IN-4)
# ---------------------------------------------------------------------------

class TestInstallationChecks:
    def test_binary_exists_true(self, tmp_path):
        """Binary exists and is executable."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        scc = bin_dir / "scc"
        scc.write_text("#!/bin/sh\necho ok")
        scc.chmod(0o755)

        result = check_binary_exists(tmp_path)
        assert result.passed is True
        assert result.check_id == "IN-1"

    def test_binary_not_found(self, tmp_path):
        result = check_binary_exists(tmp_path)
        assert result.passed is False

    @patch("scripts.checks.installation.subprocess.run")
    def test_version_check(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="scc version 3.6.0", stderr=""
        )
        result = check_version(tmp_path)
        assert result.passed is True
        assert result.check_id == "IN-2"

    @patch("scripts.checks.installation.subprocess.run")
    def test_help_available(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="Usage: scc [options] [directory]\n\n-f --format", stderr=""
        )
        result = check_help_available(tmp_path)
        assert result.passed is True
        assert result.check_id == "IN-3"

    @patch("scripts.checks.installation.subprocess.run")
    def test_no_dependencies(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="[]", stderr=""
        )
        result = check_no_dependencies(tmp_path)
        assert result.passed is True
        assert result.check_id == "IN-4"

    @patch("scripts.checks.installation.subprocess.run")
    def test_dependency_error_detected(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="library not found: libfoo"
        )
        result = check_no_dependencies(tmp_path)
        assert result.passed is False

    def test_run_installation_checks_count(self, tmp_path):
        # Just verify structure - these will fail without the real binary
        results = run_installation_checks(tmp_path)
        assert len(results) == 4
        assert all(isinstance(r, CheckResult) for r in results)


# ---------------------------------------------------------------------------
# Tests: Performance checks (PF-1 to PF-4) - via mock
# ---------------------------------------------------------------------------

class TestPerformanceChecks:
    @patch("scripts.checks.performance.subprocess.run")
    def test_run_performance_returns_4_checks(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="[]", stderr=""
        )
        results = run_performance_checks(tmp_path)
        assert len(results) == 4


# ---------------------------------------------------------------------------
# Tests: COCOMO checks (CO-1 to CO-3) - via mock
# ---------------------------------------------------------------------------

class TestCocomoChecks:
    @patch("scripts.checks.cocomo.subprocess.run")
    def test_cocomo_output_present(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "estimatedCost": 100000,
                "estimatedScheduleMonths": 10.5,
                "estimatedPeople": 2.3,
            }),
            stderr=""
        )
        result = check_cocomo_output_present(tmp_path)
        assert result.passed is True
        assert result.check_id == "CO-1"

    @patch("scripts.checks.cocomo.subprocess.run")
    def test_cocomo_missing_field(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"estimatedCost": 100000}),
            stderr=""
        )
        result = check_cocomo_output_present(tmp_path)
        assert result.passed is False

    @patch("scripts.checks.cocomo.subprocess.run")
    def test_custom_params_applied(self, mock_run, tmp_path):
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # Default (organic)
                return MagicMock(
                    returncode=0,
                    stdout=json.dumps({"estimatedCost": 100000}),
                    stderr=""
                )
            else:
                # Embedded (higher)
                return MagicMock(
                    returncode=0,
                    stdout=json.dumps({"estimatedCost": 200000}),
                    stderr=""
                )

        mock_run.side_effect = side_effect
        result = check_custom_params_applied(tmp_path)
        assert result.passed is True
        assert result.check_id == "CO-2"

    @patch("scripts.checks.cocomo.subprocess.run")
    def test_run_cocomo_checks_count(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "estimatedCost": 500000,
                "estimatedScheduleMonths": 10,
                "estimatedPeople": 3,
            }),
            stderr=""
        )
        results = run_cocomo_checks(tmp_path)
        assert len(results) == 3


# ---------------------------------------------------------------------------
# Tests: Per-file checks (PF-1 to PF-6) - via mock
# ---------------------------------------------------------------------------

class TestPerFileChecks:
    @patch("scripts.checks.per_file.subprocess.run")
    def test_per_file_json_valid(self, mock_run, tmp_path):
        per_file_data = [
            {
                "Name": "Python",
                "Files": [
                    {
                        "Location": "src/main.py",
                        "Complexity": 5,
                        "Uloc": 30,
                        "Minified": False,
                        "Generated": False,
                    }
                ]
            }
        ]
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(per_file_data),
            stderr=""
        )
        result = check_per_file_json_valid(tmp_path)
        assert result.passed is True
        assert result.check_id == "PF-1"

    @patch("scripts.checks.per_file.subprocess.run")
    def test_per_file_exit_code_failure(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="error"
        )
        result = check_per_file_json_valid(tmp_path)
        assert result.passed is False

    @patch("scripts.checks.per_file.subprocess.run")
    def test_run_per_file_checks_count(self, mock_run, tmp_path):
        per_file_data = [
            {
                "Name": "Python",
                "Files": [
                    {
                        "Location": "src/main.py",
                        "Complexity": 5,
                        "Uloc": 30,
                        "Minified": False,
                        "Generated": False,
                    }
                ]
            }
        ]
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(per_file_data),
            stderr=""
        )
        results = run_per_file_checks(tmp_path)
        assert len(results) == 6
