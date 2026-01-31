"""Unit tests for trivy analyze module."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestTransformTrivyOutput:
    """Tests for transform_trivy_output function."""

    def test_empty_results(self):
        """Test handling of empty trivy results."""
        from scripts.analyze import transform_trivy_output, AnalysisConfig

        config = AnalysisConfig(
            repo_path=Path("/tmp/test"),
            repo_name="test",
            output_dir=Path("/tmp/output"),
            run_id="test-run-id",
            repo_id="test-repo-id",
            branch="main",
            commit="0" * 40,
        )

        raw_output = {"Results": []}
        result = transform_trivy_output(raw_output, config)

        assert result["metadata"]["tool_name"] == "trivy"
        assert result["data"]["vulnerabilities"] == []
        assert result["data"]["targets"] == []

    def test_vulnerability_extraction(self):
        """Test extraction of vulnerability data."""
        from scripts.analyze import transform_trivy_output, AnalysisConfig

        config = AnalysisConfig(
            repo_path=Path("/tmp/test"),
            repo_name="test",
            output_dir=Path("/tmp/output"),
            run_id="test-run-id",
            repo_id="test-repo-id",
            branch="main",
            commit="0" * 40,
        )

        raw_output = {
            "Results": [
                {
                    "Target": "package-lock.json",
                    "Type": "npm",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2021-23337",
                            "PkgName": "lodash",
                            "InstalledVersion": "4.17.15",
                            "FixedVersion": "4.17.21",
                            "Severity": "HIGH",
                        }
                    ],
                }
            ]
        }

        result = transform_trivy_output(raw_output, config)

        assert len(result["data"]["vulnerabilities"]) == 1
        vuln = result["data"]["vulnerabilities"][0]
        assert vuln["id"] == "CVE-2021-23337"
        assert vuln["package"] == "lodash"
        assert vuln["severity"] == "HIGH"
        assert vuln["fix_available"] is True


class TestGetTrivyVersion:
    """Tests for get_trivy_version function."""

    @patch("subprocess.run")
    def test_version_parsing(self, mock_run):
        """Test parsing of trivy version output."""
        from scripts.analyze import get_trivy_version

        mock_run.return_value = MagicMock(
            returncode=0, stdout="Version: 0.58.0\n"
        )

        version = get_trivy_version()
        assert version == "0.58.0"

    @patch("subprocess.run")
    def test_version_not_found(self, mock_run):
        """Test handling when trivy is not installed."""
        from scripts.analyze import get_trivy_version

        mock_run.side_effect = FileNotFoundError()

        version = get_trivy_version()
        assert version == "unknown"
