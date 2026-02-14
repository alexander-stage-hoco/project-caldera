"""Unit tests for analyze module (_resolve_gitleaks_path, _compute_content_hash, build_analysis_data)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from analyze import (
    SCHEMA_VERSION,
    TOOL_NAME,
    _compute_content_hash,
    _resolve_gitleaks_path,
    build_analysis_data,
)
from secret_analyzer import (
    DirectoryMetrics,
    FileSummary,
    SecretAnalysis,
    SecretFinding,
)


# ---------------------------------------------------------------------------
# _resolve_gitleaks_path
# ---------------------------------------------------------------------------
class TestResolveGitleaksPath:
    """Tests for _resolve_gitleaks_path."""

    def test_explicit_path_returned(self) -> None:
        """When an explicit path is given, it should be returned as-is."""
        result = _resolve_gitleaks_path("/usr/local/bin/gitleaks")
        assert result == Path("/usr/local/bin/gitleaks")

    def test_none_uses_default_bin(self) -> None:
        """When None, should return scripts/../bin/gitleaks."""
        result = _resolve_gitleaks_path(None)
        # The default path is relative to analyze.py's parent / "bin" / "gitleaks"
        assert result.name == "gitleaks"
        assert result.parent.name == "bin"

    def test_empty_string_uses_default(self) -> None:
        """Empty string is falsy, should fall through to default."""
        result = _resolve_gitleaks_path("")
        assert result.name == "gitleaks"
        assert result.parent.name == "bin"


# ---------------------------------------------------------------------------
# _compute_content_hash
# ---------------------------------------------------------------------------
class TestComputeContentHash:
    """Tests for _compute_content_hash."""

    def test_deterministic_hash(self, tmp_path: Path) -> None:
        """Same content should produce the same hash."""
        (tmp_path / "a.txt").write_text("hello")
        (tmp_path / "b.txt").write_text("world")

        h1 = _compute_content_hash(tmp_path)
        h2 = _compute_content_hash(tmp_path)
        assert h1 == h2
        assert len(h1) == 40  # SHA-1 hex digest

    def test_different_content_different_hash(self, tmp_path: Path) -> None:
        """Different content produces different hashes."""
        (tmp_path / "a.txt").write_text("hello")
        h1 = _compute_content_hash(tmp_path)

        (tmp_path / "a.txt").write_text("goodbye")
        h2 = _compute_content_hash(tmp_path)
        assert h1 != h2

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Empty directory should still produce a valid hash."""
        h = _compute_content_hash(tmp_path)
        assert len(h) == 40

    def test_ignores_git_directory(self, tmp_path: Path) -> None:
        """Files inside .git/ should be excluded from the hash."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hi')")
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("gitconfig")

        h_with_git = _compute_content_hash(tmp_path)

        # Remove .git and recompute - should be the same
        import shutil
        shutil.rmtree(tmp_path / ".git")
        h_without_git = _compute_content_hash(tmp_path)

        assert h_with_git == h_without_git

    def test_nested_files(self, tmp_path: Path) -> None:
        """Should walk nested directories."""
        (tmp_path / "a" / "b").mkdir(parents=True)
        (tmp_path / "a" / "b" / "deep.txt").write_text("deep content")
        h = _compute_content_hash(tmp_path)
        assert len(h) == 40


# ---------------------------------------------------------------------------
# build_analysis_data
# ---------------------------------------------------------------------------
class TestBuildAnalysisData:
    """Tests for build_analysis_data."""

    def _make_analysis(self) -> SecretAnalysis:
        finding = SecretFinding(
            file_path="config/.env",
            line_number=5,
            rule_id="generic-api-key",
            secret_type="generic-api-key",
            description="Generic API Key",
            secret_preview="sk_live****",
            entropy=4.5,
            commit_hash="abc123",
            commit_author="dev@test.com",
            commit_date="2026-01-01",
            fingerprint="fp123",
            in_current_head=True,
            severity="HIGH",
        )
        file_summary = FileSummary(
            file_path="config/.env",
            secret_count=1,
            rule_ids=["generic-api-key"],
            earliest_commit="abc123",
            latest_commit="abc123",
        )
        dir_metrics = DirectoryMetrics(
            direct_secret_count=1,
            recursive_secret_count=1,
            direct_file_count=1,
            recursive_file_count=1,
            rule_id_counts={"generic-api-key": 1},
        )
        return SecretAnalysis(
            repo_name="test-repo",
            repo_path="/tmp/test-repo",
            tool_version="8.18.4",
            total_secrets=1,
            unique_secrets=1,
            secrets_in_head=1,
            secrets_in_history=0,
            files_with_secrets=1,
            commits_with_secrets=1,
            secrets_by_rule={"generic-api-key": 1},
            secrets_by_severity={"HIGH": 1},
            findings=[finding],
            files={"config/.env": file_summary},
            directories={"config": dir_metrics},
            scan_time_ms=150.0,
        )

    def test_basic_structure(self) -> None:
        """Should produce correct top-level structure."""
        analysis = self._make_analysis()
        data = build_analysis_data(analysis, "8.18.4")

        assert data["tool"] == TOOL_NAME
        assert data["tool_version"] == "8.18.4"
        assert data["total_secrets"] == 1
        assert data["unique_secrets"] == 1
        assert data["secrets_in_head"] == 1
        assert data["secrets_in_history"] == 0

    def test_findings_list(self) -> None:
        """Findings should be serialized as list of dicts."""
        analysis = self._make_analysis()
        data = build_analysis_data(analysis, "8.18.4")

        assert len(data["findings"]) == 1
        f = data["findings"][0]
        assert f["rule_id"] == "generic-api-key"
        assert f["line_number"] == 5
        assert f["severity"] == "HIGH"
        assert f["in_current_head"] is True

    def test_files_dict(self) -> None:
        """Files should be serialized as dict."""
        analysis = self._make_analysis()
        data = build_analysis_data(analysis, "8.18.4")

        assert len(data["files"]) == 1
        # File path gets normalized - just check a value exists
        file_data = list(data["files"].values())[0]
        assert file_data["secret_count"] == 1

    def test_directories_dict(self) -> None:
        """Directories should be serialized as dict."""
        analysis = self._make_analysis()
        data = build_analysis_data(analysis, "8.18.4")

        assert len(data["directories"]) == 1
        dir_data = list(data["directories"].values())[0]
        assert dir_data["direct_secret_count"] == 1
        assert dir_data["recursive_secret_count"] == 1

    def test_scan_time(self) -> None:
        """Scan time should be included."""
        analysis = self._make_analysis()
        data = build_analysis_data(analysis, "8.18.4")
        assert data["scan_time_ms"] == 150.0

    def test_empty_analysis(self) -> None:
        """Empty analysis should produce valid data with zeros."""
        analysis = SecretAnalysis(
            repo_name="empty",
            repo_path="/tmp/empty",
            tool_version="8.18.4",
        )
        data = build_analysis_data(analysis, "8.18.4")

        assert data["total_secrets"] == 0
        assert data["findings"] == []
        assert data["files"] == {}
        assert data["directories"] == {}

    def test_with_repo_root_normalizes_paths(self, tmp_path: Path) -> None:
        """Passing repo_root should normalize file paths."""
        finding = SecretFinding(
            file_path="src/config.env",
            line_number=1,
            rule_id="test",
            secret_type="test",
            description="test",
            secret_preview="***",
            entropy=0.0,
            commit_hash="abc",
            commit_author="dev",
            commit_date="2026-01-01",
            fingerprint="fp1",
        )
        file_summary = FileSummary(
            file_path="src/config.env",
            secret_count=1,
            rule_ids=["test"],
            earliest_commit="abc",
            latest_commit="abc",
        )
        analysis = SecretAnalysis(
            repo_name="test",
            repo_path=str(tmp_path),
            tool_version="8.18.4",
            total_secrets=1,
            findings=[finding],
            files={"src/config.env": file_summary},
            directories={},
        )
        data = build_analysis_data(analysis, "8.18.4", repo_root=tmp_path)
        # Should not crash; paths should be present
        assert len(data["findings"]) == 1
        assert len(data["files"]) == 1
