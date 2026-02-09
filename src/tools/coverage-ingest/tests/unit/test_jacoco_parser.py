"""Unit tests for JaCoCo parser."""
from __future__ import annotations

import pytest

from parsers.jacoco import JacocoParser


class TestJacocoParserDetection:
    """Tests for JaCoCo format detection."""

    def test_detect_valid_jacoco(self, sample_jacoco_content: str) -> None:
        """Should detect valid JaCoCo content."""
        parser = JacocoParser()
        assert parser.detect(sample_jacoco_content) is True

    def test_detect_jacoco_bytes(self, sample_jacoco_content: str) -> None:
        """Should detect JaCoCo content from bytes."""
        parser = JacocoParser()
        assert parser.detect(sample_jacoco_content.encode()) is True

    def test_detect_not_jacoco_lcov(self) -> None:
        """Should not detect LCOV as JaCoCo."""
        parser = JacocoParser()
        lcov_content = "SF:test.py\nLF:10\nLH:5\nend_of_record\n"
        assert parser.detect(lcov_content) is False

    def test_detect_not_jacoco_cobertura(self) -> None:
        """Should not detect Cobertura as JaCoCo."""
        parser = JacocoParser()
        cobertura_content = '<coverage line-rate="0.5"><packages/></coverage>'
        assert parser.detect(cobertura_content) is False

    def test_detect_minimal_jacoco(self) -> None:
        """Should detect minimal JaCoCo with report and counter."""
        parser = JacocoParser()
        minimal = '<report name="test"><counter type="LINE" missed="0" covered="10"/></report>'
        assert parser.detect(minimal) is True


class TestJacocoParserParsing:
    """Tests for JaCoCo parsing."""

    def test_parse_basic(self, sample_jacoco_content: str) -> None:
        """Should parse basic JaCoCo content."""
        parser = JacocoParser()
        results = parser.parse(sample_jacoco_content)

        assert len(results) == 2

        # First file: com/example/Main.java
        main = next(r for r in results if "Main" in r.relative_path)
        assert main.relative_path == "com/example/Main.java"
        assert main.lines_total == 10
        assert main.lines_covered == 8
        assert main.lines_missed == 2
        assert main.line_coverage_pct == 80.0
        assert main.branches_total == 4
        assert main.branches_covered == 3
        assert main.branch_coverage_pct == 75.0

        # Second file: com/example/Utils.java
        utils = next(r for r in results if "Utils" in r.relative_path)
        assert utils.relative_path == "com/example/Utils.java"
        assert utils.lines_total == 5
        assert utils.lines_covered == 5
        assert utils.lines_missed == 0
        assert utils.line_coverage_pct == 100.0
        assert utils.branches_total is None  # No branch counter

    def test_parse_bytes(self, sample_jacoco_content: str) -> None:
        """Should parse JaCoCo from bytes."""
        parser = JacocoParser()
        results = parser.parse(sample_jacoco_content.encode())
        assert len(results) == 2

    def test_parse_zero_coverage(self) -> None:
        """Should handle files with zero coverage."""
        parser = JacocoParser()
        content = """<?xml version="1.0"?>
<report name="test">
    <package name="com/example">
        <sourcefile name="Empty.java">
            <counter type="LINE" missed="10" covered="0"/>
        </sourcefile>
    </package>
</report>
"""
        results = parser.parse(content)
        assert len(results) == 1
        assert results[0].lines_covered == 0
        assert results[0].line_coverage_pct == 0.0

    def test_parse_invalid_xml(self) -> None:
        """Should raise ValueError for invalid XML."""
        parser = JacocoParser()
        with pytest.raises(ValueError, match="Invalid XML"):
            parser.parse("<report><unclosed>")

    def test_parse_wrong_root_element(self) -> None:
        """Should raise ValueError for wrong root element."""
        parser = JacocoParser()
        with pytest.raises(ValueError, match="Expected <report>"):
            parser.parse("<coverage><packages/></coverage>")

    def test_parse_empty_packages(self) -> None:
        """Should handle empty packages."""
        parser = JacocoParser()
        content = '<report name="test"></report>'
        results = parser.parse(content)
        assert results == []

    def test_parse_package_path_construction(self) -> None:
        """Should construct path from package name and filename."""
        parser = JacocoParser()
        content = """<?xml version="1.0"?>
<report name="test">
    <package name="org/example/service">
        <sourcefile name="UserService.java">
            <counter type="LINE" missed="0" covered="10"/>
        </sourcefile>
    </package>
</report>
"""
        results = parser.parse(content)
        assert len(results) == 1
        assert results[0].relative_path == "org/example/service/UserService.java"


class TestJacocoParserFormatName:
    """Tests for format name property."""

    def test_format_name(self) -> None:
        """Should return 'jacoco' as format name."""
        parser = JacocoParser()
        assert parser.format_name == "jacoco"
