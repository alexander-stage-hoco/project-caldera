"""Extended tests for secret_analyzer: calculate_severity, analyze_all_repos, run_gitleaks."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from secret_analyzer import (
    SecretAnalysis,
    SecretFinding,
    analyze_all_repos,
    calculate_severity,
    run_gitleaks,
    to_output_format,
)


# ---------------------------------------------------------------------------
# calculate_severity
# ---------------------------------------------------------------------------
class TestCalculateSeverity:
    """Tests for the calculate_severity decision logic."""

    def test_known_critical_rule(self) -> None:
        """Known critical rule should return CRITICAL."""
        assert calculate_severity("aws-access-token", "config/aws.py", True) == "CRITICAL"

    def test_known_high_rule(self) -> None:
        """Known high rule should return HIGH."""
        assert calculate_severity("github-pat", "src/.env", True) == "HIGH"

    def test_known_medium_rule(self) -> None:
        """Known medium rule should return MEDIUM."""
        assert calculate_severity("generic-api-key", "src/config.py", True) == "MEDIUM"

    def test_known_low_rule(self) -> None:
        """Known low rule should return LOW."""
        assert calculate_severity("sendgrid-api-token", "src/mail.py", True) == "LOW"

    def test_unknown_rule_defaults_medium(self) -> None:
        """Unknown rule_id should default to MEDIUM."""
        assert calculate_severity("unknown-rule-xyz", "src/file.py", True) == "MEDIUM"

    def test_historical_medium_downgraded_to_low(self) -> None:
        """Medium severity + historical (not in HEAD) -> LOW."""
        assert calculate_severity("generic-api-key", "src/config.py", False) == "LOW"

    def test_historical_low_stays_low(self) -> None:
        """Low severity + historical -> LOW."""
        assert calculate_severity("sendgrid-api-token", "src/mail.py", False) == "LOW"

    def test_historical_high_stays_high(self) -> None:
        """High severity + historical -> remains HIGH (no downgrade for HIGH/CRITICAL)."""
        assert calculate_severity("github-pat", "src/.env", False) == "HIGH"

    def test_historical_critical_stays_critical(self) -> None:
        """Critical severity + historical -> remains CRITICAL."""
        assert calculate_severity("aws-access-token", "config/aws.py", False) == "CRITICAL"

    def test_production_path_escalation(self) -> None:
        """Production path patterns should escalate severity."""
        # A production/ path with a LOW rule should escalate by one level
        result = calculate_severity("sendgrid-api-token", "production/config.py", True)
        # LOW escalated one level -> MEDIUM
        assert result == "MEDIUM"

    def test_private_key_rules(self) -> None:
        """Multiple private key rule IDs should all be HIGH."""
        for rule in ["private-key", "rsa-private-key", "dsa-private-key",
                      "openssh-private-key", "pgp-private-key"]:
            assert calculate_severity(rule, "keys/key.pem", True) == "HIGH"


# ---------------------------------------------------------------------------
# run_gitleaks
# ---------------------------------------------------------------------------
class TestRunGitleaks:
    """Tests for run_gitleaks function."""

    def test_successful_scan_with_findings(self, tmp_path: Path) -> None:
        """Successful scan (exit code 1 = leaks found) should parse results."""
        report_data = [
            {"File": "config/.env", "RuleID": "generic-api-key", "Secret": "abc123"},
        ]

        def mock_run(cmd, **kwargs):
            mock_result = MagicMock()
            mock_result.returncode = 1  # leaks found
            mock_result.stderr = ""
            # Write the report to the temp file specified in cmd
            report_path = cmd[cmd.index("--report-path") + 1]
            Path(report_path).write_text(json.dumps(report_data))
            return mock_result

        with patch("secret_analyzer.subprocess.run", side_effect=mock_run):
            findings, elapsed = run_gitleaks(
                Path("/usr/bin/gitleaks"), tmp_path
            )

        assert len(findings) == 1
        assert findings[0]["File"] == "config/.env"
        assert elapsed > 0

    def test_clean_scan_no_findings(self, tmp_path: Path) -> None:
        """Clean scan (exit code 0) should return empty findings."""
        def mock_run(cmd, **kwargs):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            # No report written (or empty)
            return mock_result

        with patch("secret_analyzer.subprocess.run", side_effect=mock_run):
            findings, elapsed = run_gitleaks(
                Path("/usr/bin/gitleaks"), tmp_path
            )

        assert findings == []

    def test_error_exit_code_raises(self, tmp_path: Path) -> None:
        """Exit code other than 0 or 1 should raise RuntimeError."""
        mock_result = MagicMock()
        mock_result.returncode = 2
        mock_result.stderr = "gitleaks binary error"

        with patch("secret_analyzer.subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="gitleaks failed"):
                run_gitleaks(Path("/usr/bin/gitleaks"), tmp_path)

    def test_with_config_and_baseline(self, tmp_path: Path) -> None:
        """Config and baseline paths should be included in command."""
        calls_received = []

        def mock_run(cmd, **kwargs):
            calls_received.append(cmd)
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            return mock_result

        config = tmp_path / "config.toml"
        baseline = tmp_path / "baseline.json"

        with patch("secret_analyzer.subprocess.run", side_effect=mock_run):
            run_gitleaks(
                Path("/usr/bin/gitleaks"),
                tmp_path,
                config_path=config,
                baseline_path=baseline,
            )

        cmd = calls_received[0]
        assert "--config" in cmd
        assert str(config) in cmd
        assert "--baseline-path" in cmd
        assert str(baseline) in cmd


# ---------------------------------------------------------------------------
# analyze_all_repos
# ---------------------------------------------------------------------------
class TestAnalyzeAllRepos:
    """Tests for analyze_all_repos function."""

    def test_scans_git_repos_only(self, tmp_path: Path) -> None:
        """Only directories with .git should be analyzed."""
        repos_dir = tmp_path / "repos"
        output_dir = tmp_path / "output"
        repos_dir.mkdir()
        output_dir.mkdir()

        # Create repo with .git
        repo1 = repos_dir / "has-git"
        repo1.mkdir()
        (repo1 / ".git").mkdir()

        # Create dir without .git
        no_git = repos_dir / "no-git"
        no_git.mkdir()

        # Create a file (not a directory)
        (repos_dir / "not-a-dir.txt").write_text("file")

        # Mock analyze_repository to return empty analysis
        mock_analysis = SecretAnalysis(
            repo_name="has-git",
            tool_version="8.18.4",
        )

        with patch("secret_analyzer.analyze_repository", return_value=mock_analysis) as mock_analyze:
            with patch("secret_analyzer.get_gitleaks_version", return_value="8.18.4"):
                results = analyze_all_repos(
                    Path("/usr/bin/gitleaks"),
                    repos_dir,
                    output_dir,
                )

        assert len(results) == 1
        assert "has-git" in results
        mock_analyze.assert_called_once()

    def test_saves_output_files(self, tmp_path: Path) -> None:
        """Each analyzed repo should have an output JSON file."""
        repos_dir = tmp_path / "repos"
        output_dir = tmp_path / "output"
        repos_dir.mkdir()
        output_dir.mkdir()

        repo = repos_dir / "test-repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        mock_analysis = SecretAnalysis(
            repo_name="test-repo",
            tool_version="8.18.4",
            total_secrets=0,
        )

        with patch("secret_analyzer.analyze_repository", return_value=mock_analysis):
            with patch("secret_analyzer.get_gitleaks_version", return_value="8.18.4"):
                results = analyze_all_repos(
                    Path("/usr/bin/gitleaks"),
                    repos_dir,
                    output_dir,
                )

        output_file = output_dir / "test-repo.json"
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert "metadata" in data
        assert "data" in data

    def test_empty_repos_directory(self, tmp_path: Path) -> None:
        """Empty repos directory should return empty dict."""
        repos_dir = tmp_path / "repos"
        output_dir = tmp_path / "output"
        repos_dir.mkdir()
        output_dir.mkdir()

        results = analyze_all_repos(
            Path("/usr/bin/gitleaks"),
            repos_dir,
            output_dir,
        )

        assert results == {}
