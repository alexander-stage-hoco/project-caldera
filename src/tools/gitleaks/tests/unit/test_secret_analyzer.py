"""Unit tests for secret_analyzer module."""

from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from secret_analyzer import (
    DirectoryMetrics,
    FileSummary,
    SecretAnalysis,
    SecretFinding,
    get_gitleaks_version,
    get_head_commit,
    get_head_files,
    mask_secret,
    to_output_format,
)


class TestMaskSecret:
    """Tests for mask_secret function."""

    def test_mask_short_secret_fully_masked(self) -> None:
        """Short secrets (<=8 chars) should be fully masked."""
        result = mask_secret("abc")
        assert result == "***"
        assert "*" in result
        assert "a" not in result

    def test_mask_exactly_8_chars_fully_masked(self) -> None:
        """Exactly 8 char secrets should be fully masked."""
        result = mask_secret("12345678")
        assert result == "********"
        assert len(result) == 8

    def test_mask_long_secret_partial_mask(self) -> None:
        """Long secrets should show first 8 chars, mask rest."""
        secret = "ghp_1234567890abcdefghij"
        result = mask_secret(secret)
        assert result.startswith("ghp_1234")
        assert result.endswith("*" * (len(secret) - 8))
        assert len(result) == len(secret)

    def test_mask_empty_string(self) -> None:
        """Empty string should return empty string."""
        result = mask_secret("")
        assert result == ""

    def test_mask_single_char(self) -> None:
        """Single char should be masked."""
        result = mask_secret("x")
        assert result == "*"

    def test_mask_custom_visible_chars(self) -> None:
        """Custom visible chars parameter."""
        result = mask_secret("1234567890", visible_chars=4)
        assert result == "1234******"
        assert len(result) == 10

    def test_mask_preserves_length(self) -> None:
        """Masked output should preserve original length."""
        secrets = ["a", "ab", "abc123456789", "ghp_1234567890abcdefghijklmnop"]
        for secret in secrets:
            result = mask_secret(secret)
            assert len(result) == len(secret)


class TestSecretFindingDataclass:
    """Tests for SecretFinding dataclass."""

    def test_create_minimal_finding(self) -> None:
        """Create a finding with required fields."""
        finding = SecretFinding(
            file_path="config/.env",
            line_number=10,
            rule_id="generic-api-key",
            secret_type="generic-api-key",
            description="Generic API Key",
            secret_preview="abc*****",
            entropy=4.5,
            commit_hash="abc123",
            commit_author="test@example.com",
            commit_date="2026-01-01",
            fingerprint="fp123",
        )
        assert finding.file_path == "config/.env"
        assert finding.line_number == 10
        assert finding.in_current_head is True  # default

    def test_finding_in_history(self) -> None:
        """Finding marked as historical."""
        finding = SecretFinding(
            file_path=".env",
            line_number=1,
            rule_id="aws-access-key",
            secret_type="aws-access-key",
            description="AWS Access Key",
            secret_preview="AKIA****",
            entropy=3.2,
            commit_hash="old123",
            commit_author="dev@example.com",
            commit_date="2025-01-01",
            fingerprint="fp456",
            in_current_head=False,
        )
        assert finding.in_current_head is False

    def test_finding_to_dict(self) -> None:
        """Convert finding to dict."""
        finding = SecretFinding(
            file_path="secrets.txt",
            line_number=5,
            rule_id="private-key",
            secret_type="private-key",
            description="Private Key",
            secret_preview="-----BEGIN****",
            entropy=5.0,
            commit_hash="def456",
            commit_author="author@test.com",
            commit_date="2026-01-15",
            fingerprint="fp789",
        )
        d = asdict(finding)
        assert d["file_path"] == "secrets.txt"
        assert d["line_number"] == 5
        assert "in_current_head" in d


class TestFileSummaryDataclass:
    """Tests for FileSummary dataclass."""

    def test_create_file_summary(self) -> None:
        """Create a file summary."""
        summary = FileSummary(
            file_path="config/api.py",
            secret_count=3,
            rule_ids=["stripe-access-token", "github-pat"],
            earliest_commit="abc123",
            latest_commit="def456",
        )
        assert summary.file_path == "config/api.py"
        assert summary.secret_count == 3
        assert len(summary.rule_ids) == 2

    def test_file_summary_single_secret(self) -> None:
        """File with single secret."""
        summary = FileSummary(
            file_path=".env",
            secret_count=1,
            rule_ids=["generic-api-key"],
            earliest_commit="abc",
            latest_commit="abc",
        )
        assert summary.secret_count == 1
        assert summary.earliest_commit == summary.latest_commit


class TestDirectoryMetricsDataclass:
    """Tests for DirectoryMetrics dataclass."""

    def test_create_directory_metrics(self) -> None:
        """Create directory metrics."""
        metrics = DirectoryMetrics(
            direct_secret_count=2,
            recursive_secret_count=5,
            direct_file_count=1,
            recursive_file_count=3,
            rule_id_counts={"github-pat": 2, "aws-access-key": 3},
        )
        assert metrics.direct_secret_count == 2
        assert metrics.recursive_secret_count == 5
        assert metrics.rule_id_counts["github-pat"] == 2

    def test_empty_directory_metrics(self) -> None:
        """Directory with no secrets."""
        metrics = DirectoryMetrics(
            direct_secret_count=0,
            recursive_secret_count=0,
            direct_file_count=0,
            recursive_file_count=0,
            rule_id_counts={},
        )
        assert metrics.direct_secret_count == 0
        assert len(metrics.rule_id_counts) == 0


class TestSecretAnalysisDataclass:
    """Tests for SecretAnalysis dataclass."""

    def test_create_empty_analysis(self) -> None:
        """Create analysis with defaults."""
        analysis = SecretAnalysis()
        assert analysis.schema_version == "1.0.0"
        assert analysis.total_secrets == 0
        assert analysis.findings == []
        assert analysis.files == {}
        assert analysis.directories == {}

    def test_create_analysis_with_findings(self) -> None:
        """Create analysis with findings."""
        finding = SecretFinding(
            file_path=".env",
            line_number=1,
            rule_id="github-pat",
            secret_type="github-pat",
            description="GitHub PAT",
            secret_preview="ghp_****",
            entropy=4.0,
            commit_hash="abc123",
            commit_author="dev@test.com",
            commit_date="2026-01-01",
            fingerprint="fp123",
        )
        analysis = SecretAnalysis(
            repo_name="test-repo",
            repo_path="/tmp/test-repo",
            total_secrets=1,
            unique_secrets=1,
            secrets_in_head=1,
            findings=[finding],
        )
        assert analysis.total_secrets == 1
        assert len(analysis.findings) == 1
        assert analysis.repo_name == "test-repo"


class TestToOutputFormat:
    """Tests for to_output_format function."""

    def test_empty_analysis_output_format(self) -> None:
        """Convert empty analysis to output format."""
        analysis = SecretAnalysis(
            generated_at="2026-01-21T00:00:00Z",
            repo_name="test",
            repo_path="/tmp/test",
            tool_version="8.18.4",
        )
        output = to_output_format(analysis)

        # Check metadata
        assert "metadata" in output
        assert output["metadata"]["schema_version"] == "1.0.0"
        assert output["metadata"]["tool_name"] == "gitleaks"
        assert output["metadata"]["tool_version"] == "8.18.4"

        # Check data
        assert "data" in output
        assert output["data"]["tool"] == "gitleaks"
        assert output["data"]["tool_version"] == "8.18.4"

    def test_output_format_with_findings(self) -> None:
        """Convert analysis with findings to output format."""
        finding = SecretFinding(
            file_path=".env",
            line_number=5,
            rule_id="stripe-access-token",
            secret_type="stripe-access-token",
            description="Stripe Key",
            secret_preview="sk_live****",
            entropy=4.5,
            commit_hash="abc123",
            commit_author="dev@test.com",
            commit_date="2026-01-01",
            fingerprint="fp123",
        )
        file_summary = FileSummary(
            file_path=".env",
            secret_count=1,
            rule_ids=["stripe-access-token"],
            earliest_commit="abc123",
            latest_commit="abc123",
        )
        analysis = SecretAnalysis(
            generated_at="2026-01-21T00:00:00Z",
            repo_name="test",
            repo_path="/tmp/test",
            tool_version="8.18.4",
            total_secrets=1,
            unique_secrets=1,
            secrets_in_head=1,
            findings=[finding],
            files={".env": file_summary},
            secrets_by_rule={"stripe-access-token": 1},
        )
        output = to_output_format(analysis)

        data = output["data"]
        assert data["total_secrets"] == 1
        assert len(data["findings"]) == 1
        assert data["findings"][0]["file_path"] == ".env"
        assert ".env" in data["files"]
        assert data["secrets_by_rule"]["stripe-access-token"] == 1

    def test_output_format_files_converted_to_dict(self) -> None:
        """File summaries should be converted to dicts."""
        file_summary = FileSummary(
            file_path="config/api.py",
            secret_count=2,
            rule_ids=["github-pat"],
            earliest_commit="abc",
            latest_commit="def",
        )
        analysis = SecretAnalysis(
            generated_at="2026-01-21T00:00:00Z",
            repo_name="test",
            repo_path="/tmp/test",
            tool_version="8.18.4",
            files={"config/api.py": file_summary},
        )
        output = to_output_format(analysis)

        file_data = output["data"]["files"]["config/api.py"]
        assert isinstance(file_data, dict)
        assert file_data["secret_count"] == 2


class TestGetGitleaksVersion:
    """Tests for get_gitleaks_version function."""

    def test_get_version_success(self) -> None:
        """Get gitleaks version with mocked subprocess."""
        mock_result = MagicMock()
        mock_result.stdout = "8.18.4\n"

        with patch("secret_analyzer.subprocess.run", return_value=mock_result):
            version = get_gitleaks_version(Path("/usr/bin/gitleaks"))

        assert version == "8.18.4"

    def test_get_version_strips_whitespace(self) -> None:
        """Version string should be stripped."""
        mock_result = MagicMock()
        mock_result.stdout = "  v8.18.4  \n"

        with patch("secret_analyzer.subprocess.run", return_value=mock_result):
            version = get_gitleaks_version(Path("/usr/bin/gitleaks"))

        assert version == "v8.18.4"


class TestGetHeadCommit:
    """Tests for get_head_commit function."""

    def test_get_head_commit_success(self) -> None:
        """Get HEAD commit hash."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "abc123def456789\n"

        with patch("secret_analyzer.subprocess.run", return_value=mock_result):
            commit = get_head_commit(Path("/tmp/repo"))

        assert commit == "abc123def456789"

    def test_get_head_commit_failure(self) -> None:
        """Return empty string on failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch("secret_analyzer.subprocess.run", return_value=mock_result):
            commit = get_head_commit(Path("/tmp/nonexistent"))

        assert commit == ""


class TestGetHeadFiles:
    """Tests for get_head_files function."""

    def test_get_head_files_success(self) -> None:
        """Get list of files in HEAD."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "README.md\nsrc/main.py\nconfig/.env\n"

        with patch("secret_analyzer.subprocess.run", return_value=mock_result):
            files = get_head_files(Path("/tmp/repo"))

        assert files == {"README.md", "src/main.py", "config/.env"}

    def test_get_head_files_failure(self) -> None:
        """Return empty set on failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch("secret_analyzer.subprocess.run", return_value=mock_result):
            files = get_head_files(Path("/tmp/nonexistent"))

        assert files == set()
