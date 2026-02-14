"""Tests targeting uncovered paths in analyze.py for coverage improvement."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.analyze import _normalize_analysis_paths, to_envelope_output
from scripts.license_analyzer import (
    LicenseAnalysis,
    LicenseFinding,
    FileSummary,
    DirectoryEntry,
    DirectoryStats,
)


class TestNormalizeAnalysisPaths:
    """Tests for path normalization of analysis results."""

    def test_normalizes_finding_paths(self, tmp_path: Path) -> None:
        analysis = LicenseAnalysis(
            findings=[
                LicenseFinding(
                    file_path=str(tmp_path / "src" / "main.py"),
                    spdx_id="MIT",
                    category="permissive",
                    confidence=1.0,
                    match_type="spdx",
                ),
            ],
            files={
                str(tmp_path / "src" / "main.py"): FileSummary(
                    file_path=str(tmp_path / "src" / "main.py"),
                    licenses=["MIT"],
                    category="permissive",
                    has_spdx_header=True,
                )
            },
            directories=[
                DirectoryEntry(
                    path=str(tmp_path / "src"),
                    direct=DirectoryStats(file_count=1, files_with_licenses=1),
                    recursive=DirectoryStats(file_count=1, files_with_licenses=1),
                )
            ],
        )

        _normalize_analysis_paths(analysis, tmp_path)

        assert analysis.findings[0].file_path == "src/main.py"
        assert "src/main.py" in analysis.files
        # Directory should also be normalized
        assert not analysis.directories[0].path.startswith("/")


class TestToEnvelopeOutput:
    """Tests for Caldera envelope wrapping."""

    def test_envelope_structure(self, tmp_path: Path) -> None:
        analysis = LicenseAnalysis(findings=[], files={}, directories=[])
        result = to_envelope_output(
            analysis,
            repo_name="test-repo",
            repo_path="/tmp/test-repo",
            run_id="run-123",
            repo_id="repo-456",
            branch="main",
            commit="a" * 40,
            timestamp="2025-01-01T00:00:00Z",
        )
        assert result["metadata"]["tool_name"] == "scancode"
        assert result["metadata"]["tool_version"] == "1.0.0"
        assert result["metadata"]["run_id"] == "run-123"
        assert result["metadata"]["repo_id"] == "repo-456"
        assert result["metadata"]["branch"] == "main"
        assert result["metadata"]["commit"] == "a" * 40
        assert "data" in result
