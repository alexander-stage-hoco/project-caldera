"""Tests targeting uncovered paths in analyze.py for coverage improvement."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.analyze import (
    AnalysisResult,
    Duplication,
    DuplicationOccurrence,
    FileMetrics,
    calculate_file_metrics,
    calculate_statistics,
    collect_files,
    detect_language,
    find_java,
    parse_cpd_xml,
)


class TestParseCpdXml:
    """Tests for parse_cpd_xml with realistic CPD output."""

    def test_parse_multi_language_xml(self, tmp_path: Path) -> None:
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<pmd-cpd>
  <duplication lines="10" tokens="55">
    <file path="{repo}/src/utils.py" line="5" column="1" endline="14" endcolumn="20"/>
    <file path="{repo}/src/helpers.py" line="20" column="1" endline="29" endcolumn="20"/>
    <codefragment>def process(data): pass</codefragment>
  </duplication>
  <duplication lines="8" tokens="42">
    <file path="{repo}/src/main.ts" line="1" column="1" endline="8" endcolumn="30"/>
    <file path="{repo}/src/app.ts" line="50" column="1" endline="57" endcolumn="30"/>
  </duplication>
</pmd-cpd>""".format(repo=tmp_path)

        dups = parse_cpd_xml(xml, tmp_path, start_id=0)
        assert len(dups) == 2
        assert dups[0].clone_id == "CPD-0000"
        assert dups[0].lines == 10
        assert dups[0].tokens == 55
        assert len(dups[0].occurrences) == 2
        assert dups[0].code_fragment == "def process(data): pass"
        assert dups[1].clone_id == "CPD-0001"
        assert dups[1].lines == 8

    def test_parse_empty_xml(self, tmp_path: Path) -> None:
        assert parse_cpd_xml("", tmp_path) == []

    def test_parse_invalid_xml(self, tmp_path: Path) -> None:
        assert parse_cpd_xml("<bad xml>", tmp_path) == []

    def test_parse_start_id_offset(self, tmp_path: Path) -> None:
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<pmd-cpd>
  <duplication lines="5" tokens="30">
    <file path="{repo}/a.py" line="1" column="0" endline="5" endcolumn="0"/>
    <file path="{repo}/b.py" line="1" column="0" endline="5" endcolumn="0"/>
  </duplication>
</pmd-cpd>""".format(repo=tmp_path)
        dups = parse_cpd_xml(xml, tmp_path, start_id=10)
        assert dups[0].clone_id == "CPD-0010"


class TestCollectFiles:
    """Tests for file collection with directory exclusions."""

    def test_excludes_hidden_dirs(self, tmp_path: Path) -> None:
        # Create source files
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("print('hello')")

        # Hidden dir should be excluded
        git = tmp_path / ".git"
        git.mkdir()
        (git / "config.py").write_text("x = 1")

        # node_modules should be excluded
        nm = tmp_path / "node_modules"
        nm.mkdir()
        (nm / "index.js").write_text("module.exports = {}")

        result = collect_files(tmp_path)
        all_files = [str(f) for files in result.values() for f in files]
        assert any("main.py" in f for f in all_files)
        assert not any(".git" in f for f in all_files)
        assert not any("node_modules" in f for f in all_files)

    def test_collects_multiple_languages(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("x = 1")
        (tmp_path / "app.js").write_text("const x = 1;")
        (tmp_path / "lib.ts").write_text("const y: number = 2;")
        (tmp_path / "readme.md").write_text("# Readme")  # non-source

        result = collect_files(tmp_path)
        assert "python" in result
        assert "ecmascript" in result
        assert "typescript" in result
        # .md is not in EXT_TO_LANGUAGE
        langs = set(result.keys())
        assert "markdown" not in langs


class TestCalculateFileMetrics:
    """Tests for file metrics calculation including overlap handling."""

    def test_overlapping_clones_capped_at_100(self, tmp_path: Path) -> None:
        # Create a small file
        f = tmp_path / "small.py"
        f.write_text("line1\nline2\nline3\nline4\nline5\n")

        files_by_lang = {"python": [f]}

        # Two overlapping clones covering the same lines
        dups = [
            Duplication(
                clone_id="CPD-0001", lines=5, tokens=30,
                occurrences=[DuplicationOccurrence(
                    file="small.py", line_start=1, line_end=5,
                )],
            ),
            Duplication(
                clone_id="CPD-0002", lines=5, tokens=30,
                occurrences=[DuplicationOccurrence(
                    file="small.py", line_start=1, line_end=5,
                )],
            ),
        ]

        metrics = calculate_file_metrics(tmp_path, dups, files_by_lang)
        # Should be capped at 100%
        assert metrics[0].duplication_percentage == 100.0
        # duplicate_blocks counts both occurrences
        assert metrics[0].duplicate_blocks == 2

    def test_no_duplications(self, tmp_path: Path) -> None:
        f = tmp_path / "clean.py"
        f.write_text("x = 1\ny = 2\n")
        files_by_lang = {"python": [f]}
        metrics = calculate_file_metrics(tmp_path, [], files_by_lang)
        assert metrics[0].duplicate_lines == 0
        assert metrics[0].duplication_percentage == 0.0


class TestCalculateStatistics:
    """Tests for overall statistics computation."""

    def test_cross_file_clone_counting(self) -> None:
        dups = [
            Duplication(
                clone_id="CPD-0001", lines=10, tokens=50,
                occurrences=[
                    DuplicationOccurrence(file="a.py", line_start=1, line_end=10),
                    DuplicationOccurrence(file="b.py", line_start=1, line_end=10),
                ],
            ),
            Duplication(
                clone_id="CPD-0002", lines=5, tokens=30,
                occurrences=[
                    DuplicationOccurrence(file="c.py", line_start=1, line_end=5),
                    DuplicationOccurrence(file="c.py", line_start=20, line_end=24),
                ],
            ),
        ]
        stats = calculate_statistics(dups)
        assert stats["cross_file_clones"] == 1  # only first is cross-file
        assert stats["total_tokens"] == 80
        assert stats["total_duplicate_lines"] == 15


class TestFindJava:
    """Tests for Java runtime detection."""

    @patch("scripts.analyze.shutil.which", return_value="/usr/bin/java")
    def test_finds_java_on_path(self, mock_which) -> None:
        result = find_java()
        assert result == "/usr/bin/java"

    @patch("scripts.analyze.shutil.which", return_value=None)
    @patch("scripts.analyze.Path.exists", return_value=False)
    def test_no_java_returns_none(self, mock_exists, mock_which) -> None:
        result = find_java()
        assert result is None


class TestDetectLanguage:
    """Tests for language detection from file extension."""

    def test_python(self) -> None:
        assert detect_language("src/main.py") == "python"

    def test_typescript(self) -> None:
        assert detect_language("app/index.tsx") == "typescript"

    def test_unknown_extension(self) -> None:
        assert detect_language("readme.md") == "unknown"


class TestAnalysisResultEnvelope:
    """Tests for the Caldera envelope output."""

    def test_to_caldera_envelope_structure(self) -> None:
        result = AnalysisResult(
            run_id="test-run",
            repo_id="test-repo",
            branch="main",
            commit="a" * 40,
            timestamp="2025-01-01T00:00:00Z",
            tool_version="7.0.0",
            min_tokens=50,
            ignore_identifiers=False,
            ignore_literals=False,
            elapsed_seconds=1.5,
            summary={"total_files": 0, "total_clones": 0, "duplication_percentage": 0.0},
            files=[],
            duplications=[],
            statistics={},
        )
        envelope = result.to_caldera_envelope()
        assert envelope["metadata"]["tool_name"] == "pmd-cpd"
        assert envelope["metadata"]["schema_version"] == "1.0.0"
        assert envelope["data"]["config"]["min_tokens"] == 50
