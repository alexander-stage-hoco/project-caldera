"""Unit tests for Cobertura parser."""
from __future__ import annotations

import pytest

from parsers.cobertura import CoberturaParser


class TestCoberturaParserDetection:
    """Tests for Cobertura format detection."""

    def test_detect_valid_cobertura(self, sample_cobertura_content: str) -> None:
        """Should detect valid Cobertura content."""
        parser = CoberturaParser()
        assert parser.detect(sample_cobertura_content) is True

    def test_detect_cobertura_bytes(self, sample_cobertura_content: str) -> None:
        """Should detect Cobertura content from bytes."""
        parser = CoberturaParser()
        assert parser.detect(sample_cobertura_content.encode()) is True

    def test_detect_not_cobertura_lcov(self) -> None:
        """Should not detect LCOV as Cobertura."""
        parser = CoberturaParser()
        lcov_content = "SF:test.py\nLF:10\nLH:5\nend_of_record\n"
        assert parser.detect(lcov_content) is False

    def test_detect_not_cobertura_jacoco(self) -> None:
        """Should not detect JaCoCo as Cobertura."""
        parser = CoberturaParser()
        jacoco_content = '<report name="test"><counter type="LINE"/></report>'
        assert parser.detect(jacoco_content) is False

    def test_detect_minimal_cobertura(self) -> None:
        """Should detect minimal Cobertura with coverage and line-rate."""
        parser = CoberturaParser()
        minimal = '<coverage line-rate="0.5"><packages><package/></packages></coverage>'
        assert parser.detect(minimal) is True


class TestCoberturaParserParsing:
    """Tests for Cobertura parsing."""

    def test_parse_basic(self, sample_cobertura_content: str) -> None:
        """Should parse basic Cobertura content."""
        parser = CoberturaParser()
        results = parser.parse(sample_cobertura_content)

        assert len(results) == 2

        # First file: src/main.py
        main = next(r for r in results if "main" in r.relative_path)
        assert main.relative_path == "src/main.py"
        assert main.lines_total == 4
        assert main.lines_covered == 3
        assert main.lines_missed == 1
        assert main.line_coverage_pct == 75.0
        # Branch coverage is None when we only have rate but no actual counts
        assert main.branch_coverage_pct is None

        # Second file: src/utils.py
        utils = next(r for r in results if "utils" in r.relative_path)
        assert utils.relative_path == "src/utils.py"
        assert utils.lines_total == 2
        assert utils.lines_covered == 2
        assert utils.lines_missed == 0
        assert utils.line_coverage_pct == 100.0

    def test_parse_bytes(self, sample_cobertura_content: str) -> None:
        """Should parse Cobertura from bytes."""
        parser = CoberturaParser()
        results = parser.parse(sample_cobertura_content.encode())
        assert len(results) == 2

    def test_parse_absolute_path_normalized(self) -> None:
        """Should strip leading slash from absolute paths."""
        parser = CoberturaParser()
        content = """<?xml version="1.0"?>
<coverage line-rate="0.5">
    <packages>
        <package name="src">
            <classes>
                <class filename="/home/user/src/main.py" line-rate="0.5">
                    <lines>
                        <line number="1" hits="1"/>
                        <line number="2" hits="0"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>
"""
        results = parser.parse(content)
        assert len(results) == 1
        assert results[0].relative_path == "home/user/src/main.py"

    def test_parse_zero_coverage(self) -> None:
        """Should handle files with zero coverage."""
        parser = CoberturaParser()
        content = """<?xml version="1.0"?>
<coverage line-rate="0.0">
    <packages>
        <package name="src">
            <classes>
                <class filename="src/empty.py" line-rate="0.0">
                    <lines>
                        <line number="1" hits="0"/>
                        <line number="2" hits="0"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>
"""
        results = parser.parse(content)
        assert len(results) == 1
        assert results[0].lines_covered == 0
        assert results[0].line_coverage_pct == 0.0

    def test_parse_invalid_xml(self) -> None:
        """Should raise ValueError for invalid XML."""
        parser = CoberturaParser()
        with pytest.raises(ValueError, match="Invalid XML"):
            parser.parse("<coverage><unclosed>")

    def test_parse_wrong_root_element(self) -> None:
        """Should raise ValueError for wrong root element."""
        parser = CoberturaParser()
        with pytest.raises(ValueError, match="Expected <coverage>"):
            parser.parse("<report><packages/></report>")

    def test_parse_empty_packages(self) -> None:
        """Should handle empty packages."""
        parser = CoberturaParser()
        content = '<coverage line-rate="0"><packages></packages></coverage>'
        results = parser.parse(content)
        assert results == []


class TestCoberturaParserFormatName:
    """Tests for format name property."""

    def test_format_name(self) -> None:
        """Should return 'cobertura' as format name."""
        parser = CoberturaParser()
        assert parser.format_name == "cobertura"
