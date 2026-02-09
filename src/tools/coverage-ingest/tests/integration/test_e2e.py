"""End-to-end integration tests for coverage-ingest."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


class TestEndToEnd:
    """End-to-end tests for the coverage ingestion pipeline."""

    def test_lcov_to_output(self, sample_lcov_content: str) -> None:
        """Should produce valid output from LCOV input."""
        from parsers import LcovParser
        from parsers.base import FileCoverage

        parser = LcovParser()
        results = parser.parse(sample_lcov_content)

        assert len(results) == 2
        assert all(isinstance(r, FileCoverage) for r in results)

        # Verify invariants
        for r in results:
            assert r.lines_covered <= r.lines_total
            assert r.lines_missed == r.lines_total - r.lines_covered
            if r.line_coverage_pct is not None:
                assert 0 <= r.line_coverage_pct <= 100

    def test_cobertura_to_output(self, sample_cobertura_content: str) -> None:
        """Should produce valid output from Cobertura input."""
        from parsers import CoberturaParser
        from parsers.base import FileCoverage

        parser = CoberturaParser()
        results = parser.parse(sample_cobertura_content)

        assert len(results) == 2
        assert all(isinstance(r, FileCoverage) for r in results)

    def test_jacoco_to_output(self, sample_jacoco_content: str) -> None:
        """Should produce valid output from JaCoCo input."""
        from parsers import JacocoParser
        from parsers.base import FileCoverage

        parser = JacocoParser()
        results = parser.parse(sample_jacoco_content)

        assert len(results) == 2
        assert all(isinstance(r, FileCoverage) for r in results)

    def test_istanbul_to_output(self, sample_istanbul_content: str) -> None:
        """Should produce valid output from Istanbul input."""
        from parsers import IstanbulParser
        from parsers.base import FileCoverage

        parser = IstanbulParser()
        results = parser.parse(sample_istanbul_content)

        assert len(results) == 2
        assert all(isinstance(r, FileCoverage) for r in results)

    def test_format_auto_detection(
        self,
        sample_lcov_content: str,
        sample_cobertura_content: str,
        sample_jacoco_content: str,
        sample_istanbul_content: str,
    ) -> None:
        """Should auto-detect format correctly for all types."""
        from parsers import LcovParser, CoberturaParser, JacocoParser, IstanbulParser

        lcov = LcovParser()
        cobertura = CoberturaParser()
        jacoco = JacocoParser()
        istanbul = IstanbulParser()

        # Each parser should only detect its own format
        assert lcov.detect(sample_lcov_content) is True
        assert lcov.detect(sample_cobertura_content) is False
        assert lcov.detect(sample_jacoco_content) is False
        assert lcov.detect(sample_istanbul_content) is False

        assert cobertura.detect(sample_cobertura_content) is True
        assert cobertura.detect(sample_lcov_content) is False
        assert cobertura.detect(sample_istanbul_content) is False

        assert jacoco.detect(sample_jacoco_content) is True
        assert jacoco.detect(sample_lcov_content) is False
        assert jacoco.detect(sample_istanbul_content) is False

        assert istanbul.detect(sample_istanbul_content) is True
        assert istanbul.detect(sample_lcov_content) is False
        assert istanbul.detect(sample_cobertura_content) is False

    def test_cross_format_path_normalization(self) -> None:
        """All formats should normalize paths consistently."""
        from parsers import LcovParser, CoberturaParser, JacocoParser, IstanbulParser

        # Same logical file in different formats with different path representations
        lcov_content = "SF:/home/user/project/src/main.py\nLF:10\nLH:5\nend_of_record\n"
        cobertura_content = """<?xml version="1.0"?>
<coverage line-rate="0.5">
    <packages>
        <package name="src">
            <classes>
                <class filename="/home/user/project/src/main.py" line-rate="0.5">
                    <lines><line number="1" hits="1"/></lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>"""
        istanbul_content = '{"/home/user/project/src/main.py": {"path": "/home/user/project/src/main.py", "s": {"0": 1}}}'

        lcov_result = LcovParser().parse(lcov_content)[0]
        cobertura_result = CoberturaParser().parse(cobertura_content)[0]
        istanbul_result = IstanbulParser().parse(istanbul_content)[0]

        # All should produce paths without leading slash
        assert not lcov_result.relative_path.startswith("/")
        assert not cobertura_result.relative_path.startswith("/")
        assert not istanbul_result.relative_path.startswith("/")

        # All should use POSIX separators
        assert "\\" not in lcov_result.relative_path
        assert "\\" not in cobertura_result.relative_path
        assert "\\" not in istanbul_result.relative_path
