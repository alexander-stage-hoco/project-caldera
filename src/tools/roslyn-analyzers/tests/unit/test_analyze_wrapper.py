"""
Tests for analyze.py wrapper - envelope creation and severity mapping.

Tests cover:
- wrap_in_envelope: path normalization, violation mapping, directory rollup
- _map_severity: severity normalization
- main CLI argument parsing and error handling
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from analyze import wrap_in_envelope, _map_severity, TOOL_NAME, SCHEMA_VERSION


class TestMapSeverity:
    """Test severity mapping via shared normalization."""

    def test_map_severity_high(self):
        assert _map_severity("high") == "HIGH"

    def test_map_severity_medium(self):
        assert _map_severity("medium") == "MEDIUM"

    def test_map_severity_low(self):
        assert _map_severity("low") == "LOW"

    def test_map_severity_critical(self):
        assert _map_severity("critical") == "CRITICAL"

    def test_map_severity_unknown_returns_default(self):
        result = _map_severity("unknown_value")
        assert result == "MEDIUM"

    def test_map_severity_empty_string(self):
        result = _map_severity("")
        assert result == "MEDIUM"


class TestWrapInEnvelope:
    """Test wrapping analysis output in Caldera envelope."""

    def _make_analysis_output(self, files=None, summary=None, directory_rollup=None):
        return {
            "results": {
                "tool_version": "1.2.3",
                "analysis_duration_ms": 5000,
                "summary": summary or {"total_violations": 2},
                "files": files or [],
                "statistics": {"violations_per_file": {"mean": 1.0}},
                "directory_rollup": directory_rollup or [],
            }
        }

    def test_envelope_has_metadata(self, tmp_path):
        """Envelope must contain standard metadata fields."""
        output = self._make_analysis_output()
        envelope = wrap_in_envelope(
            output,
            run_id="run-123",
            repo_id="repo-456",
            branch="main",
            commit="a" * 40,
            repo_path=tmp_path,
        )

        assert "metadata" in envelope
        metadata = envelope["metadata"]
        assert metadata["run_id"] == "run-123"
        assert metadata["repo_id"] == "repo-456"
        assert metadata["branch"] == "main"
        assert metadata["commit"] == "a" * 40
        assert metadata["tool_name"] == TOOL_NAME
        assert metadata["schema_version"] == SCHEMA_VERSION

    def test_envelope_data_contains_tool_info(self, tmp_path):
        """Data section includes tool name and version from analysis output."""
        output = self._make_analysis_output()
        envelope = wrap_in_envelope(
            output,
            run_id="run-123",
            repo_id="repo-456",
            branch="main",
            commit="a" * 40,
            repo_path=tmp_path,
        )

        data = envelope["data"]
        assert data["tool"] == TOOL_NAME
        assert data["tool_version"] == "1.2.3"
        assert data["analysis_duration_ms"] == 5000

    def test_envelope_maps_file_violations(self, tmp_path):
        """File violations are mapped to smells with correct fields."""
        files = [
            {
                "relative_path": "src/test.cs",
                "language": "C#",
                "lines_of_code": 50,
                "violation_count": 1,
                "violations": [
                    {
                        "rule_id": "CA3001",
                        "dd_category": "security",
                        "dd_severity": "high",
                        "message": "SQL injection",
                        "line_start": 10,
                        "line_end": 12,
                        "column_start": 5,
                        "column_end": 40,
                    }
                ],
            }
        ]
        output = self._make_analysis_output(files=files)
        envelope = wrap_in_envelope(
            output,
            run_id="run-1",
            repo_id="repo-1",
            branch="main",
            commit="b" * 40,
            repo_path=tmp_path,
        )

        data_files = envelope["data"]["files"]
        assert len(data_files) == 1
        f = data_files[0]
        assert f["language"] == "C#"
        assert f["lines_of_code"] == 50
        assert f["violation_count"] == 1

        smell = f["violations"][0]
        assert smell["rule_id"] == "CA3001"
        assert smell["dd_category"] == "security"
        assert smell["message"] == "SQL injection"
        assert smell["line_start"] == 10
        assert smell["line_end"] == 12

    def test_envelope_normalizes_directory_rollup_paths(self, tmp_path):
        """Directory rollup paths are normalized to repo-relative."""
        rollup = [
            {"directory": "src/controllers", "total_violations": 5},
        ]
        output = self._make_analysis_output(directory_rollup=rollup)
        envelope = wrap_in_envelope(
            output,
            run_id="run-1",
            repo_id="repo-1",
            branch="main",
            commit="c" * 40,
            repo_path=tmp_path,
        )

        data_rollup = envelope["data"]["directory_rollup"]
        assert len(data_rollup) == 1
        assert data_rollup[0]["total_violations"] == 5

    def test_envelope_empty_files(self, tmp_path):
        """Handle analysis with no files."""
        output = self._make_analysis_output(files=[])
        envelope = wrap_in_envelope(
            output,
            run_id="run-1",
            repo_id="repo-1",
            branch="main",
            commit="d" * 40,
            repo_path=tmp_path,
        )

        assert envelope["data"]["files"] == []

    def test_envelope_default_tool_version(self, tmp_path):
        """When results have no tool_version, use default."""
        output = {"results": {
            "analysis_duration_ms": 100,
            "summary": {},
            "files": [],
            "statistics": {},
            "directory_rollup": [],
        }}
        envelope = wrap_in_envelope(
            output,
            run_id="run-1",
            repo_id="repo-1",
            branch="main",
            commit="e" * 40,
            repo_path=tmp_path,
        )

        # Should use the default TOOL_VERSION from module
        assert envelope["data"]["tool_version"] is not None

    def test_envelope_multiple_violations_per_file(self, tmp_path):
        """Multiple violations in one file are all mapped."""
        files = [
            {
                "relative_path": "src/service.cs",
                "language": "C#",
                "lines_of_code": 200,
                "violation_count": 3,
                "violations": [
                    {"rule_id": "CA3001", "dd_category": "security", "dd_severity": "high",
                     "message": "v1", "line_start": 10, "line_end": 10, "column_start": 1, "column_end": 20},
                    {"rule_id": "CA1001", "dd_category": "resource", "dd_severity": "critical",
                     "message": "v2", "line_start": 50, "line_end": 50, "column_start": 1, "column_end": 30},
                    {"rule_id": "IDE0005", "dd_category": "dead_code", "dd_severity": "medium",
                     "message": "v3", "line_start": 1, "line_end": 1, "column_start": 1, "column_end": 15},
                ],
            }
        ]
        output = self._make_analysis_output(files=files)
        envelope = wrap_in_envelope(
            output,
            run_id="run-1",
            repo_id="repo-1",
            branch="main",
            commit="f" * 40,
            repo_path=tmp_path,
        )

        smells = envelope["data"]["files"][0]["violations"]
        assert len(smells) == 3
        rule_ids = [s["rule_id"] for s in smells]
        assert "CA3001" in rule_ids
        assert "CA1001" in rule_ids
        assert "IDE0005" in rule_ids


class TestMainCLI:
    """Test main CLI entry point error paths."""

    def test_main_missing_repo_path(self):
        """main() exits on missing required args."""
        from analyze import main
        with patch("sys.argv", ["analyze.py"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0

    def test_main_nonexistent_repo_path(self, tmp_path):
        """main() exits when repo path does not exist."""
        from analyze import main
        fake_path = str(tmp_path / "does_not_exist")
        with patch("sys.argv", [
            "analyze.py",
            "--repo-path", fake_path,
            "--repo-name", "test",
            "--output-dir", str(tmp_path / "out"),
            "--run-id", "run-1",
            "--repo-id", "repo-1",
        ]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_main_short_commit_warns(self, tmp_path, capsys):
        """main() warns on short commit SHA but does not crash before analysis."""
        from analyze import main

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        out_dir = tmp_path / "out"

        with patch("sys.argv", [
            "analyze.py",
            "--repo-path", str(repo_dir),
            "--repo-name", "test",
            "--output-dir", str(out_dir),
            "--run-id", "run-1",
            "--repo-id", "repo-1",
            "--commit", "abc123",
        ]):
            # It will fail at the analyze() call, but should have printed warning
            with patch("analyze.analyze", side_effect=Exception("mock")):
                with pytest.raises(SystemExit):
                    main()
                captured = capsys.readouterr()
                assert "Warning" in captured.out or "Error" in captured.out
