"""Unit tests for analyze.py CLI module."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from analyze import AnalysisConfig, main, run_analysis, transform_trivy_output


class TestAnalysisConfig:
    """Tests for AnalysisConfig dataclass."""

    def test_config_creation(self, tmp_path: Path):
        """Test creating an AnalysisConfig."""
        config = AnalysisConfig(
            repo_path=tmp_path,
            repo_name="test-repo",
            output_dir=tmp_path / "output",
            run_id="test-run-id",
            repo_id="test-repo-id",
            branch="main",
            commit="abc123",
        )

        assert config.repo_path == tmp_path
        assert config.repo_name == "test-repo"
        assert config.timeout == 600  # Default


class TestTransformTrivyOutput:
    """Tests for transform_trivy_output function."""

    def test_empty_results(self, tmp_path: Path):
        """Test transforming empty trivy output."""
        config = AnalysisConfig(
            repo_path=tmp_path,
            repo_name="test-repo",
            output_dir=tmp_path / "output",
            run_id="test-run-id",
            repo_id="test-repo-id",
            branch="main",
            commit="abc123",
        )

        raw_output = {"Results": []}
        result = transform_trivy_output(raw_output, config)

        assert result["metadata"]["tool_name"] == "trivy"
        assert result["metadata"]["run_id"] == "test-run-id"
        assert result["data"]["targets"] == []
        assert result["data"]["vulnerabilities"] == []
        assert result["data"]["iac_misconfigurations"]["count"] == 0

    def test_transform_vulnerabilities(self, tmp_path: Path):
        """Test transforming trivy output with vulnerabilities."""
        config = AnalysisConfig(
            repo_path=tmp_path,
            repo_name="test-repo",
            output_dir=tmp_path / "output",
            run_id="test-run-id",
            repo_id="test-repo-id",
            branch="main",
            commit="abc123",
        )

        raw_output = {
            "Results": [
                {
                    "Target": "package.json",
                    "Type": "npm",
                    "Class": "lang-pkgs",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2021-0001",
                            "PkgName": "lodash",
                            "InstalledVersion": "4.17.20",
                            "FixedVersion": "4.17.21",
                            "Severity": "HIGH",
                            "Title": "Test vulnerability",
                        }
                    ],
                }
            ]
        }

        result = transform_trivy_output(raw_output, config)

        assert len(result["data"]["vulnerabilities"]) == 1
        vuln = result["data"]["vulnerabilities"][0]
        assert vuln["id"] == "CVE-2021-0001"
        assert vuln["package"] == "lodash"
        assert vuln["fix_available"] is True
        assert result["data"]["findings_summary"]["total_vulnerabilities"] == 1
        assert result["data"]["findings_summary"]["fixable_count"] == 1

    def test_transform_misconfigurations(self, tmp_path: Path):
        """Test transforming trivy output with misconfigurations."""
        config = AnalysisConfig(
            repo_path=tmp_path,
            repo_name="test-repo",
            output_dir=tmp_path / "output",
            run_id="test-run-id",
            repo_id="test-repo-id",
            branch="main",
            commit="abc123",
        )

        raw_output = {
            "Results": [
                {
                    "Target": "Dockerfile",
                    "Type": "dockerfile",
                    "Misconfigurations": [
                        {
                            "ID": "DS002",
                            "Severity": "HIGH",
                            "Title": "Root user",
                            "Description": "Running as root",
                            "Resolution": "Use non-root user",
                        }
                    ],
                }
            ]
        }

        result = transform_trivy_output(raw_output, config)

        assert result["data"]["iac_misconfigurations"]["count"] == 1
        misconfig = result["data"]["iac_misconfigurations"]["misconfigurations"][0]
        assert misconfig["id"] == "DS002"
        assert misconfig["severity"] == "HIGH"


class TestAnalyzeCLI:
    """Tests for the analyze CLI main function."""

    def test_cli_requires_repo_path(self, tmp_path: Path):
        """Test CLI requires --repo-path argument."""
        result = subprocess.run(
            [sys.executable, "-m", "analyze"],
            cwd=str(Path(__file__).parent.parent.parent / "scripts"),
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "required" in result.stderr.lower() or "--repo-path" in result.stderr

    def test_cli_help(self):
        """Test CLI --help shows usage."""
        result = subprocess.run(
            [sys.executable, "-m", "analyze", "--help"],
            cwd=str(Path(__file__).parent.parent.parent / "scripts"),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "--repo-path" in result.stdout
        assert "--output-dir" in result.stdout
        assert "--run-id" in result.stdout

    @patch("analyze.run_trivy_scan")
    @patch("analyze.get_trivy_version")
    @patch("analyze.discover_scannable_files")
    def test_main_success_mocked(
        self,
        mock_discover: MagicMock,
        mock_version: MagicMock,
        mock_scan: MagicMock,
        tmp_path: Path,
        monkeypatch,
    ):
        """Test successful main() execution with mocked trivy."""
        mock_version.return_value = "0.58.0"
        mock_scan.return_value = {"Results": []}
        mock_discover.return_value = {}

        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        output_dir = tmp_path / "output"

        # Simulate command line arguments
        test_args = [
            "analyze",
            "--repo-path", str(repo_path),
            "--repo-name", "test-repo",
            "--output-dir", str(output_dir),
            "--run-id", "test-run-id",
            "--repo-id", "test-repo-id",
            "--commit", "0" * 40,
        ]
        monkeypatch.setattr(sys, "argv", test_args)

        # Call main - it will exit with sys.exit on success or failure
        # For testing, we catch SystemExit
        try:
            main()
        except SystemExit as e:
            assert e.code == 0 or e.code is None, f"main() exited with code {e.code}"

        # Verify output file was created
        output_file = output_dir / "output.json"
        assert output_file.exists()


class TestRunAnalysis:
    """Tests for run_analysis function."""

    @patch("analyze.run_trivy_scan")
    @patch("analyze.get_trivy_version")
    @patch("analyze.discover_scannable_files")
    def test_run_analysis_writes_output(
        self,
        mock_discover: MagicMock,
        mock_version: MagicMock,
        mock_scan: MagicMock,
        tmp_path: Path,
    ):
        """Test run_analysis writes output file."""
        mock_version.return_value = "0.58.0"
        mock_scan.return_value = {"Results": []}
        mock_discover.return_value = {}

        config = AnalysisConfig(
            repo_path=tmp_path,
            repo_name="test-repo",
            output_dir=tmp_path / "output",
            run_id="test-run-id",
            repo_id="test-repo-id",
            branch="main",
            commit="abc123",
        )

        result = run_analysis(config)

        output_file = tmp_path / "output" / "output.json"
        assert output_file.exists()
        assert result["id"] == "test-repo"  # ID used for ground truth matching
        assert result["metadata"]["tool_name"] == "trivy"
