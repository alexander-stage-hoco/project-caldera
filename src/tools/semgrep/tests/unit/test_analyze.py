"""Tests for scripts/analyze.py - CLI entry point for Semgrep smell analysis.

Covers:
- result_to_data_dict conversion logic
- _directory_stats_to_dict helper
- to_envelope_format wrapper
- TOOL_VERSION / SCHEMA_VERSION constants
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

# analyze.py uses relative imports (from .smell_analyzer import ...) so we must
# import it through the scripts package, not by adding scripts/ to sys.path.
_tool_root = str(Path(__file__).parent.parent.parent)
if _tool_root not in sys.path:
    sys.path.insert(0, _tool_root)

from scripts.analyze import (
    result_to_data_dict,
    _directory_stats_to_dict,
    to_envelope_format,
    TOOL_VERSION,
    SCHEMA_VERSION,
)
from scripts.smell_analyzer import (
    AnalysisResult,
    FileStats,
    SmellInstance,
    DirectoryEntry,
    DirectoryStats,
    LanguageStats,
)


# ===========================================================================
# result_to_data_dict
# ===========================================================================

class TestResultToDataDict:
    def _make_result(self) -> AnalysisResult:
        smell = SmellInstance(
            rule_id="DD-D1-EMPTY-CATCH-python",
            dd_smell_id="D1_EMPTY_CATCH",
            dd_category="error_handling",
            file_path="src/main.py",
            line_start=10,
            line_end=12,
            column_start=5,
            column_end=10,
            severity="HIGH",
            message="Empty catch block",
            code_snippet="except: pass",
        )
        file_stat = FileStats(
            path="src/main.py",
            language="python",
            lines=100,
            smell_count=1,
            smell_density=1.0,
            by_category={"error_handling": 1},
            by_severity={"HIGH": 1},
            by_smell_type={"D1_EMPTY_CATCH": 1},
            smells=[smell],
        )
        dir_entry = DirectoryEntry(
            path="src",
            name="src",
            depth=1,
            is_leaf=True,
            child_count=0,
            subdirectories=[],
            direct=DirectoryStats(file_count=1, lines_code=100, smell_count=1,
                                  by_category={"error_handling": 1}, by_severity={"HIGH": 1},
                                  by_smell_type={"D1_EMPTY_CATCH": 1}, smell_density=1.0),
            recursive=DirectoryStats(file_count=1, lines_code=100, smell_count=1,
                                     by_category={"error_handling": 1}, by_severity={"HIGH": 1},
                                     by_smell_type={"D1_EMPTY_CATCH": 1}, smell_density=1.0),
        )
        lang_stats = LanguageStats(files=1, lines=100, smell_count=1, categories_covered={"error_handling"})
        return AnalysisResult(
            semgrep_version="1.50.0",
            files=[file_stat],
            smells=[smell],
            directories=[dir_entry],
            by_language={"python": lang_stats},
            by_category={"error_handling": 1},
            by_smell_type={"D1_EMPTY_CATCH": 1},
            by_severity={"HIGH": 1},
            analysis_duration_ms=3000,
            rules_used=["DD-D1-EMPTY-CATCH-python"],
        )

    def test_basic_structure(self):
        result = self._make_result()
        data = result_to_data_dict(result)
        assert data["tool"] == "semgrep"
        assert data["tool_version"] == "1.50.0"
        assert "summary" in data
        assert "files" in data
        assert "directories" in data
        assert "by_language" in data

    def test_summary_counts(self):
        result = self._make_result()
        data = result_to_data_dict(result)
        summary = data["summary"]
        assert summary["total_files"] == 1
        assert summary["total_smells"] == 1
        assert summary["files_with_smells"] == 1
        assert summary["total_lines"] == 100

    def test_file_serialization(self):
        result = self._make_result()
        data = result_to_data_dict(result)
        files = data["files"]
        assert len(files) == 1
        f = files[0]
        assert f["language"] == "python"
        assert f["lines"] == 100
        assert f["smell_count"] == 1
        assert len(f["smells"]) == 1
        smell = f["smells"][0]
        assert smell["rule_id"] == "DD-D1-EMPTY-CATCH-python"
        assert smell["dd_smell_id"] == "D1_EMPTY_CATCH"
        assert smell["line_start"] == 10
        assert smell["severity"] == "HIGH"

    def test_directory_serialization(self):
        result = self._make_result()
        data = result_to_data_dict(result)
        dirs = data["directories"]
        assert len(dirs) == 1
        d = dirs[0]
        assert d["name"] == "src"
        assert d["depth"] == 1
        assert d["is_leaf"] is True
        assert "direct" in d
        assert "recursive" in d

    def test_language_stats_serialization(self):
        result = self._make_result()
        data = result_to_data_dict(result)
        by_lang = data["by_language"]
        assert "python" in by_lang
        py = by_lang["python"]
        assert py["files"] == 1
        assert py["lines"] == 100
        assert "error_handling" in py["categories_covered"]

    def test_empty_result(self):
        result = AnalysisResult(semgrep_version="1.50.0")
        data = result_to_data_dict(result)
        assert data["summary"]["total_files"] == 0
        assert data["summary"]["total_smells"] == 0
        assert data["files"] == []
        assert data["directories"] == []

    def test_with_repo_root(self, tmp_path: Path):
        result = self._make_result()
        data = result_to_data_dict(result, repo_root=tmp_path)
        # Path normalization should be applied
        assert isinstance(data["files"][0]["path"], str)


# ===========================================================================
# _directory_stats_to_dict
# ===========================================================================

class TestDirectoryStatsToDict:
    def test_basic_conversion(self):
        stats = DirectoryStats(
            file_count=5,
            lines_code=500,
            smell_count=10,
            by_category={"security": 5, "error_handling": 5},
            by_severity={"HIGH": 10},
            by_smell_type={"SQL_INJECTION": 5, "D1_EMPTY_CATCH": 5},
            smell_density=2.0,
        )
        d = _directory_stats_to_dict(stats)
        assert d["file_count"] == 5
        assert d["lines_code"] == 500
        assert d["smell_count"] == 10
        assert d["smell_density"] == 2.0
        assert d["by_category"]["security"] == 5

    def test_none_density(self):
        stats = DirectoryStats(smell_density=None)
        d = _directory_stats_to_dict(stats)
        assert d["smell_density"] == 0


# ===========================================================================
# to_envelope_format
# ===========================================================================

class TestToEnvelopeFormat:
    def test_creates_envelope(self):
        data = {"tool": "semgrep", "summary": {"total_files": 1}}
        envelope = to_envelope_format(
            data,
            run_id="run-123",
            repo_id="my-repo",
            branch="main",
            commit="abc123de" * 5,
            timestamp="2026-01-01T00:00:00Z",
            semgrep_version="1.50.0",
        )
        assert "metadata" in envelope
        assert "data" in envelope
        assert envelope["metadata"]["tool_name"] == "semgrep"
        assert envelope["metadata"]["run_id"] == "run-123"


# ===========================================================================
# Constants
# ===========================================================================

class TestConstants:
    def test_tool_version(self):
        assert TOOL_VERSION == "1.0.0"

    def test_schema_version(self):
        assert SCHEMA_VERSION == "1.0.0"
