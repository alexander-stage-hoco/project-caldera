"""Unit tests for Istanbul parser."""
from __future__ import annotations

import pytest

from parsers.istanbul import IstanbulParser


class TestIstanbulParserDetection:
    """Tests for Istanbul format detection."""

    def test_detect_valid_istanbul(self, sample_istanbul_content: str) -> None:
        """Should detect valid Istanbul content."""
        parser = IstanbulParser()
        assert parser.detect(sample_istanbul_content) is True

    def test_detect_istanbul_bytes(self, sample_istanbul_content: str) -> None:
        """Should detect Istanbul content from bytes."""
        parser = IstanbulParser()
        assert parser.detect(sample_istanbul_content.encode()) is True

    def test_detect_not_istanbul_lcov(self) -> None:
        """Should not detect LCOV as Istanbul."""
        parser = IstanbulParser()
        lcov_content = "SF:test.py\nLF:10\nLH:5\nend_of_record\n"
        assert parser.detect(lcov_content) is False

    def test_detect_not_istanbul_xml(self) -> None:
        """Should not detect XML as Istanbul."""
        parser = IstanbulParser()
        xml_content = '<?xml version="1.0"?><coverage/>'
        assert parser.detect(xml_content) is False

    def test_detect_minimal_istanbul(self) -> None:
        """Should detect minimal Istanbul with s (statements) key."""
        parser = IstanbulParser()
        minimal = '{"test.js": {"path": "test.js", "s": {"0": 5}}}'
        assert parser.detect(minimal) is True

    def test_detect_not_random_json(self) -> None:
        """Should not detect random JSON as Istanbul."""
        parser = IstanbulParser()
        random_json = '{"name": "test", "version": "1.0"}'
        assert parser.detect(random_json) is False


class TestIstanbulParserParsing:
    """Tests for Istanbul parsing."""

    def test_parse_basic(self, sample_istanbul_content: str) -> None:
        """Should parse basic Istanbul content."""
        parser = IstanbulParser()
        results = parser.parse(sample_istanbul_content)

        assert len(results) == 2

        # First file: src/main.js
        main = next(r for r in results if "main" in r.relative_path)
        assert main.relative_path == "src/main.js"
        assert main.lines_total == 4
        assert main.lines_covered == 3
        assert main.lines_missed == 1
        assert main.line_coverage_pct == 75.0
        assert main.branches_total == 2
        assert main.branches_covered == 2
        assert main.branch_coverage_pct == 100.0

        # Second file: src/utils.js
        utils = next(r for r in results if "utils" in r.relative_path)
        assert utils.relative_path == "src/utils.js"
        assert utils.lines_total == 2
        assert utils.lines_covered == 2
        assert utils.lines_missed == 0
        assert utils.line_coverage_pct == 100.0
        assert utils.branches_total is None  # Empty branch map
        assert utils.branches_covered is None

    def test_parse_bytes(self, sample_istanbul_content: str) -> None:
        """Should parse Istanbul from bytes."""
        parser = IstanbulParser()
        results = parser.parse(sample_istanbul_content.encode())
        assert len(results) == 2

    def test_parse_absolute_path_normalized(self) -> None:
        """Should strip leading slash from absolute paths."""
        parser = IstanbulParser()
        content = '{"//home/user/src/main.js": {"path": "/home/user/src/main.js", "s": {"0": 1}}}'
        results = parser.parse(content)
        assert len(results) == 1
        assert results[0].relative_path == "home/user/src/main.js"

    def test_parse_zero_coverage(self) -> None:
        """Should handle files with zero coverage."""
        parser = IstanbulParser()
        content = '{"src/empty.js": {"path": "src/empty.js", "s": {"0": 0, "1": 0}, "b": {}}}'
        results = parser.parse(content)
        assert len(results) == 1
        assert results[0].lines_covered == 0
        assert results[0].line_coverage_pct == 0.0

    def test_parse_full_coverage(self) -> None:
        """Should handle files with 100% coverage."""
        parser = IstanbulParser()
        content = '{"src/perfect.js": {"path": "src/perfect.js", "s": {"0": 5, "1": 3}, "b": {}}}'
        results = parser.parse(content)
        assert len(results) == 1
        assert results[0].line_coverage_pct == 100.0

    def test_parse_invalid_json(self) -> None:
        """Should raise ValueError for invalid JSON."""
        parser = IstanbulParser()
        with pytest.raises(ValueError, match="Invalid JSON"):
            parser.parse('{"unclosed": ')

    def test_parse_wrong_root_type(self) -> None:
        """Should raise ValueError for non-object root."""
        parser = IstanbulParser()
        with pytest.raises(ValueError, match="Expected JSON object"):
            parser.parse('[{"path": "test.js"}]')

    def test_parse_empty_object(self) -> None:
        """Should handle empty object."""
        parser = IstanbulParser()
        results = parser.parse("{}")
        assert results == []

    def test_parse_branch_coverage(self) -> None:
        """Should correctly count branch coverage."""
        parser = IstanbulParser()
        # Two branches: one fully covered [2, 2], one partially [1, 0]
        content = """{
            "test.js": {
                "path": "test.js",
                "s": {"0": 1},
                "b": {"0": [2, 2], "1": [1, 0]}
            }
        }"""
        results = parser.parse(content)
        assert len(results) == 1
        assert results[0].branches_total == 4
        assert results[0].branches_covered == 3
        assert results[0].branch_coverage_pct == 75.0


class TestIstanbulParserFormatName:
    """Tests for format name property."""

    def test_format_name(self) -> None:
        """Should return 'istanbul' as format name."""
        parser = IstanbulParser()
        assert parser.format_name == "istanbul"
