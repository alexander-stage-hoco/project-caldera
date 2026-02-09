"""Unit tests for LCOV parser."""
from __future__ import annotations

import pytest

from parsers.lcov import LcovParser


class TestLcovParserDetection:
    """Tests for LCOV format detection."""

    def test_detect_valid_lcov(self, sample_lcov_content: str) -> None:
        """Should detect valid LCOV content."""
        parser = LcovParser()
        assert parser.detect(sample_lcov_content) is True

    def test_detect_lcov_bytes(self, sample_lcov_content: str) -> None:
        """Should detect LCOV content from bytes."""
        parser = LcovParser()
        assert parser.detect(sample_lcov_content.encode()) is True

    def test_detect_not_lcov_xml(self) -> None:
        """Should not detect XML as LCOV."""
        parser = LcovParser()
        xml_content = '<?xml version="1.0"?><coverage/>'
        assert parser.detect(xml_content) is False

    def test_detect_not_lcov_json(self) -> None:
        """Should not detect JSON as LCOV."""
        parser = LcovParser()
        json_content = '{"path": "test.js", "s": {}}'
        assert parser.detect(json_content) is False

    def test_detect_minimal_lcov(self) -> None:
        """Should detect minimal LCOV with just SF and LF/LH."""
        parser = LcovParser()
        minimal = "SF:test.py\nLF:10\nLH:5\n"
        assert parser.detect(minimal) is True


class TestLcovParserParsing:
    """Tests for LCOV parsing."""

    def test_parse_basic(self, sample_lcov_content: str) -> None:
        """Should parse basic LCOV content."""
        parser = LcovParser()
        results = parser.parse(sample_lcov_content)

        assert len(results) == 2

        # First file: src/main.py
        main = results[0]
        assert main.relative_path == "src/main.py"
        assert main.lines_total == 4
        assert main.lines_covered == 3
        assert main.lines_missed == 1
        assert main.line_coverage_pct == 75.0
        assert main.branches_total == 2
        assert main.branches_covered == 1
        assert main.branch_coverage_pct == 50.0

        # Second file: src/utils.py
        utils = results[1]
        assert utils.relative_path == "src/utils.py"
        assert utils.lines_total == 2
        assert utils.lines_covered == 2
        assert utils.lines_missed == 0
        assert utils.line_coverage_pct == 100.0
        assert utils.branches_total is None
        assert utils.branches_covered is None

    def test_parse_bytes(self, sample_lcov_content: str) -> None:
        """Should parse LCOV from bytes."""
        parser = LcovParser()
        results = parser.parse(sample_lcov_content.encode())
        assert len(results) == 2

    def test_parse_absolute_path_normalized(self) -> None:
        """Should strip leading slash from absolute paths."""
        parser = LcovParser()
        content = "SF:/home/user/project/src/main.py\nLF:10\nLH:5\nend_of_record\n"
        results = parser.parse(content)

        assert len(results) == 1
        assert results[0].relative_path == "home/user/project/src/main.py"

    def test_parse_zero_coverage(self) -> None:
        """Should handle files with zero coverage."""
        parser = LcovParser()
        content = "SF:src/empty.py\nLF:10\nLH:0\nend_of_record\n"
        results = parser.parse(content)

        assert len(results) == 1
        assert results[0].lines_total == 10
        assert results[0].lines_covered == 0
        assert results[0].lines_missed == 10
        assert results[0].line_coverage_pct == 0.0

    def test_parse_full_coverage(self) -> None:
        """Should handle files with 100% coverage."""
        parser = LcovParser()
        content = "SF:src/perfect.py\nLF:10\nLH:10\nend_of_record\n"
        results = parser.parse(content)

        assert len(results) == 1
        assert results[0].line_coverage_pct == 100.0

    def test_parse_no_end_of_record(self) -> None:
        """Should handle files without end_of_record marker."""
        parser = LcovParser()
        content = "SF:src/main.py\nLF:5\nLH:3\n"
        results = parser.parse(content)

        assert len(results) == 1
        assert results[0].lines_total == 5

    def test_parse_empty_file(self) -> None:
        """Should handle empty content."""
        parser = LcovParser()
        results = parser.parse("")
        assert results == []

    def test_parse_windows_paths(self) -> None:
        """Should normalize Windows-style paths."""
        parser = LcovParser()
        content = "SF:src\\main.py\nLF:5\nLH:3\nend_of_record\n"
        results = parser.parse(content)

        assert len(results) == 1
        assert results[0].relative_path == "src/main.py"


class TestLcovParserFormatName:
    """Tests for format name property."""

    def test_format_name(self) -> None:
        """Should return 'lcov' as format name."""
        parser = LcovParser()
        assert parser.format_name == "lcov"
