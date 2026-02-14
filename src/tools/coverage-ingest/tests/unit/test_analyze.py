"""Unit tests for analyze.py: format detection, path normalization, summary computation, main."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from parsers.base import FileCoverage
from scripts.analyze import (
    detect_format,
    normalize_coverage_paths,
    compute_summary,
    FORMAT_TO_PARSER,
    PARSERS,
    TOOL_VERSION,
    main,
)


# ---------------------------------------------------------------------------
# detect_format
# ---------------------------------------------------------------------------
class TestDetectFormat:
    """Tests for auto-detecting coverage format from file content."""

    def test_detects_lcov(self) -> None:
        content = "SF:test.py\nLF:10\nLH:5\nend_of_record\n"
        parser = detect_format(content)
        assert parser is not None
        assert parser.format_name == "lcov"

    def test_detects_cobertura(self) -> None:
        content = '<coverage line-rate="0.5"><packages><package><classes></classes></package></packages></coverage>'
        parser = detect_format(content)
        assert parser is not None
        assert parser.format_name == "cobertura"

    def test_detects_jacoco(self) -> None:
        content = '<report name="test"><counter type="LINE" missed="1" covered="9"/></report>'
        parser = detect_format(content)
        assert parser is not None
        assert parser.format_name == "jacoco"

    def test_detects_istanbul(self) -> None:
        content = '{"test.js": {"path": "test.js", "s": {"0": 1}}}'
        parser = detect_format(content)
        assert parser is not None
        assert parser.format_name == "istanbul"

    def test_returns_none_for_unrecognised(self) -> None:
        content = "this is just plain text"
        assert detect_format(content) is None

    def test_returns_none_for_empty_string(self) -> None:
        assert detect_format("") is None

    def test_accepts_bytes(self) -> None:
        content = b"SF:test.py\nLF:10\nLH:5\nend_of_record\n"
        parser = detect_format(content)
        assert parser is not None
        assert parser.format_name == "lcov"

    def test_jacoco_detected_before_cobertura_for_report_xml(self) -> None:
        """JaCoCo comes before Cobertura in detection order, so a
        <report>-based XML should match JaCoCo first."""
        content = '<report name="p"><counter type="LINE" missed="0" covered="5"/></report>'
        parser = detect_format(content)
        assert parser is not None
        assert parser.format_name == "jacoco"


# ---------------------------------------------------------------------------
# FORMAT_TO_PARSER / PARSERS module-level constants
# ---------------------------------------------------------------------------
class TestModuleConstants:

    def test_format_to_parser_has_four_formats(self) -> None:
        assert set(FORMAT_TO_PARSER.keys()) == {"lcov", "cobertura", "jacoco", "istanbul"}

    def test_parsers_list_has_four_entries(self) -> None:
        assert len(PARSERS) == 4

    def test_tool_version_is_string(self) -> None:
        assert isinstance(TOOL_VERSION, str)
        assert "." in TOOL_VERSION


# ---------------------------------------------------------------------------
# normalize_coverage_paths
# ---------------------------------------------------------------------------
class TestNormalizeCoveragePaths:
    """Tests for normalize_coverage_paths (relies on shared path_utils)."""

    def test_basic_normalization(self, tmp_path: Path) -> None:
        coverages = [
            FileCoverage(
                relative_path="src/main.py",
                line_coverage_pct=75.0,
                branch_coverage_pct=None,
                lines_total=4,
                lines_covered=3,
                lines_missed=1,
                branches_total=None,
                branches_covered=None,
                uncovered_lines=None,
            )
        ]
        with patch("scripts.analyze.normalize_file_path", return_value="src/main.py"):
            results = normalize_coverage_paths(coverages, tmp_path)

        assert len(results) == 1
        assert results[0]["relative_path"] == "src/main.py"
        assert results[0]["line_coverage_pct"] == 75.0
        assert results[0]["branch_coverage_pct"] is None
        assert results[0]["lines_total"] == 4
        assert results[0]["lines_covered"] == 3
        assert results[0]["lines_missed"] == 1
        assert results[0]["branches_total"] is None
        assert results[0]["branches_covered"] is None
        assert results[0]["uncovered_lines"] is None

    def test_multiple_files(self, tmp_path: Path) -> None:
        coverages = [
            FileCoverage(
                relative_path="a.py",
                line_coverage_pct=100.0,
                branch_coverage_pct=None,
                lines_total=2,
                lines_covered=2,
                lines_missed=0,
                branches_total=None,
                branches_covered=None,
            ),
            FileCoverage(
                relative_path="b.py",
                line_coverage_pct=0.0,
                branch_coverage_pct=None,
                lines_total=3,
                lines_covered=0,
                lines_missed=3,
                branches_total=None,
                branches_covered=None,
            ),
        ]
        with patch("scripts.analyze.normalize_file_path", side_effect=lambda p, r: p):
            results = normalize_coverage_paths(coverages, tmp_path)

        assert len(results) == 2
        assert results[0]["relative_path"] == "a.py"
        assert results[1]["relative_path"] == "b.py"

    def test_preserves_uncovered_lines(self, tmp_path: Path) -> None:
        coverages = [
            FileCoverage(
                relative_path="src/x.py",
                line_coverage_pct=50.0,
                branch_coverage_pct=None,
                lines_total=4,
                lines_covered=2,
                lines_missed=2,
                branches_total=None,
                branches_covered=None,
                uncovered_lines=[3, 4],
            )
        ]
        with patch("scripts.analyze.normalize_file_path", side_effect=lambda p, r: p):
            results = normalize_coverage_paths(coverages, tmp_path)

        assert results[0]["uncovered_lines"] == [3, 4]

    def test_preserves_branch_data(self, tmp_path: Path) -> None:
        coverages = [
            FileCoverage(
                relative_path="src/y.py",
                line_coverage_pct=80.0,
                branch_coverage_pct=50.0,
                lines_total=5,
                lines_covered=4,
                lines_missed=1,
                branches_total=4,
                branches_covered=2,
            )
        ]
        with patch("scripts.analyze.normalize_file_path", side_effect=lambda p, r: p):
            results = normalize_coverage_paths(coverages, tmp_path)

        assert results[0]["branches_total"] == 4
        assert results[0]["branches_covered"] == 2
        assert results[0]["branch_coverage_pct"] == 50.0


# ---------------------------------------------------------------------------
# compute_summary
# ---------------------------------------------------------------------------
class TestComputeSummary:
    """Tests for summary computation from coverage dicts."""

    def test_basic_summary(self) -> None:
        coverages = [
            {"lines_total": 10, "lines_covered": 7, "branches_total": 4, "branches_covered": 2},
            {"lines_total": 5, "lines_covered": 5, "branches_total": None, "branches_covered": None},
        ]
        summary = compute_summary(coverages)
        assert summary["total_files"] == 2
        assert summary["files_with_coverage"] == 2
        assert summary["total_lines"] == 15
        assert summary["total_lines_covered"] == 12
        assert summary["overall_line_coverage_pct"] == 80.0
        assert summary["total_branches"] == 4
        assert summary["total_branches_covered"] == 2
        assert summary["overall_branch_coverage_pct"] == 50.0

    def test_empty_coverages(self) -> None:
        summary = compute_summary([])
        assert summary["total_files"] == 0
        assert summary["files_with_coverage"] == 0
        assert summary["overall_line_coverage_pct"] is None
        assert summary["overall_branch_coverage_pct"] is None
        assert summary["total_lines"] == 0
        assert summary["total_branches"] is None

    def test_zero_total_lines(self) -> None:
        coverages = [{"lines_total": 0, "lines_covered": 0, "branches_total": 0, "branches_covered": 0}]
        summary = compute_summary(coverages)
        assert summary["overall_line_coverage_pct"] is None
        assert summary["overall_branch_coverage_pct"] is None
        assert summary["total_branches"] is None

    def test_no_branches(self) -> None:
        coverages = [
            {"lines_total": 10, "lines_covered": 5, "branches_total": None, "branches_covered": None},
        ]
        summary = compute_summary(coverages)
        assert summary["overall_branch_coverage_pct"] is None
        assert summary["total_branches"] is None
        assert summary["total_branches_covered"] is None

    def test_all_files_with_coverage(self) -> None:
        coverages = [
            {"lines_total": 10, "lines_covered": 10, "branches_total": None, "branches_covered": None},
            {"lines_total": 5, "lines_covered": 5, "branches_total": None, "branches_covered": None},
        ]
        summary = compute_summary(coverages)
        assert summary["files_with_coverage"] == 2
        assert summary["overall_line_coverage_pct"] == 100.0

    def test_file_without_coverable_lines(self) -> None:
        coverages = [
            {"lines_total": 0, "lines_covered": 0, "branches_total": None, "branches_covered": None},
            {"lines_total": 10, "lines_covered": 8, "branches_total": None, "branches_covered": None},
        ]
        summary = compute_summary(coverages)
        # Only the second file has coverage
        assert summary["files_with_coverage"] == 1
        assert summary["total_files"] == 2
        assert summary["overall_line_coverage_pct"] == 80.0

    def test_missing_keys_use_defaults(self) -> None:
        """compute_summary uses .get() with default 0 so missing keys are safe."""
        coverages = [{}]
        summary = compute_summary(coverages)
        assert summary["total_files"] == 1
        assert summary["total_lines"] == 0
        assert summary["files_with_coverage"] == 0

    def test_rounding_precision(self) -> None:
        coverages = [
            {"lines_total": 3, "lines_covered": 1, "branches_total": None, "branches_covered": None},
        ]
        summary = compute_summary(coverages)
        assert summary["overall_line_coverage_pct"] == 33.33


# ---------------------------------------------------------------------------
# main() CLI entry point
# ---------------------------------------------------------------------------
class TestMain:
    """Tests for the main() CLI entry point (mock heavy external deps)."""

    def _make_common(self, tmp_path: Path) -> MagicMock:
        """Create a mock 'common' namespace returned by validate_common_args."""
        common = MagicMock()
        common.run_id = "test-run-id"
        common.repo_id = "test-repo"
        common.branch = "main"
        common.commit = "a" * 40
        common.output_path = tmp_path / "output.json"
        # repo_path must be a MagicMock so we can set resolve().return_value
        repo_path_mock = MagicMock()
        repo_path_mock.resolve.return_value = tmp_path
        common.repo_path = repo_path_mock
        return common

    def test_main_auto_detect_lcov(self, tmp_path: Path) -> None:
        """main() with --format auto should auto-detect LCOV and produce output."""
        coverage_file = tmp_path / "coverage.lcov"
        coverage_file.write_text("SF:src/main.py\nLF:10\nLH:7\nend_of_record\n")
        output_file = tmp_path / "output.json"
        common = self._make_common(tmp_path)
        common.output_path = output_file

        with (
            patch("sys.argv", ["analyze", "--coverage-file", str(coverage_file),
                                "--format", "auto"]),
            patch("scripts.analyze.validate_common_args", return_value=common),
            patch("scripts.analyze.CommitResolutionConfig"),
            patch("scripts.analyze.add_common_args"),
            patch("scripts.analyze.normalize_file_path", side_effect=lambda p, r: p),
            patch("scripts.analyze.create_envelope", side_effect=lambda data, **kw: {"envelope": data}),
            patch("scripts.analyze.get_current_timestamp", return_value="2026-01-01T00:00:00Z"),
        ):
            main()

        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert "envelope" in data
        assert data["envelope"]["source_format"] == "lcov"

    def test_main_explicit_format(self, tmp_path: Path) -> None:
        """main() with --format lcov should use the specified parser."""
        coverage_file = tmp_path / "coverage.lcov"
        coverage_file.write_text("SF:src/main.py\nLF:5\nLH:5\nend_of_record\n")
        output_file = tmp_path / "output.json"
        common = self._make_common(tmp_path)
        common.output_path = output_file

        with (
            patch("sys.argv", ["analyze", "--coverage-file", str(coverage_file),
                                "--format", "lcov"]),
            patch("scripts.analyze.validate_common_args", return_value=common),
            patch("scripts.analyze.CommitResolutionConfig"),
            patch("scripts.analyze.add_common_args"),
            patch("scripts.analyze.normalize_file_path", side_effect=lambda p, r: p),
            patch("scripts.analyze.create_envelope", side_effect=lambda data, **kw: {"envelope": data}),
            patch("scripts.analyze.get_current_timestamp", return_value="2026-01-01T00:00:00Z"),
        ):
            main()

        data = json.loads(output_file.read_text())
        assert data["envelope"]["source_format"] == "lcov"

    def test_main_coverage_file_not_found(self, tmp_path: Path) -> None:
        """main() should exit(1) when coverage file doesn't exist."""
        common = self._make_common(tmp_path)
        with (
            patch("sys.argv", ["analyze", "--coverage-file", "/nonexistent/file.lcov",
                                "--format", "auto"]),
            patch("scripts.analyze.validate_common_args", return_value=common),
            patch("scripts.analyze.CommitResolutionConfig"),
            patch("scripts.analyze.add_common_args"),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()
        assert exc_info.value.code == 1

    def test_main_auto_detect_fails(self, tmp_path: Path) -> None:
        """main() should exit(1) when auto-detect can't identify the format."""
        coverage_file = tmp_path / "mystery.txt"
        coverage_file.write_text("this is not a valid coverage file")
        common = self._make_common(tmp_path)

        with (
            patch("sys.argv", ["analyze", "--coverage-file", str(coverage_file),
                                "--format", "auto"]),
            patch("scripts.analyze.validate_common_args", return_value=common),
            patch("scripts.analyze.CommitResolutionConfig"),
            patch("scripts.analyze.add_common_args"),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()
        assert exc_info.value.code == 1

    def test_main_parse_error(self, tmp_path: Path) -> None:
        """main() should exit(1) when the parser raises ValueError."""
        coverage_file = tmp_path / "bad.xml"
        # Write content that Cobertura detects but then fails to parse properly
        coverage_file.write_text("<coverage><broken")
        common = self._make_common(tmp_path)
        common.output_path = tmp_path / "output.json"

        with (
            patch("sys.argv", ["analyze", "--coverage-file", str(coverage_file),
                                "--format", "cobertura"]),
            patch("scripts.analyze.validate_common_args", return_value=common),
            patch("scripts.analyze.CommitResolutionConfig"),
            patch("scripts.analyze.add_common_args"),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()
        assert exc_info.value.code == 1

    def test_main_with_branch_coverage(self, tmp_path: Path) -> None:
        """main() output includes branch coverage when present."""
        coverage_file = tmp_path / "coverage.lcov"
        coverage_file.write_text(
            "SF:src/main.py\nLF:10\nLH:7\nBRF:4\nBRH:2\nend_of_record\n"
        )
        output_file = tmp_path / "output.json"
        common = self._make_common(tmp_path)
        common.output_path = output_file

        with (
            patch("sys.argv", ["analyze", "--coverage-file", str(coverage_file),
                                "--format", "auto"]),
            patch("scripts.analyze.validate_common_args", return_value=common),
            patch("scripts.analyze.CommitResolutionConfig"),
            patch("scripts.analyze.add_common_args"),
            patch("scripts.analyze.normalize_file_path", side_effect=lambda p, r: p),
            patch("scripts.analyze.create_envelope", side_effect=lambda data, **kw: {"envelope": data}),
            patch("scripts.analyze.get_current_timestamp", return_value="2026-01-01T00:00:00Z"),
        ):
            main()

        data = json.loads(output_file.read_text())
        summary = data["envelope"]["summary"]
        assert summary["overall_branch_coverage_pct"] == 50.0
