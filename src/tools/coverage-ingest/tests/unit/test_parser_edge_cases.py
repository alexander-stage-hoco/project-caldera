"""Unit tests targeting uncovered lines in parsers (base.py validation,
parser-specific edge cases for lcov, cobertura, jacoco, istanbul)."""
from __future__ import annotations

import pytest

from parsers.base import FileCoverage, compute_coverage_pct
from parsers.lcov import LcovParser
from parsers.cobertura import CoberturaParser
from parsers.jacoco import JacocoParser
from parsers.istanbul import IstanbulParser


# ===========================================================================
# FileCoverage __post_init__ validation (base.py lines 44-80)
# ===========================================================================
class TestFileCoverageValidation:
    """Test __post_init__ validation paths in FileCoverage."""

    def test_lines_covered_exceeds_total_raises(self) -> None:
        with pytest.raises(ValueError, match="lines_covered.*>.*lines_total"):
            FileCoverage(
                relative_path="t.py",
                line_coverage_pct=50.0,
                branch_coverage_pct=None,
                lines_total=5,
                lines_covered=6,
                lines_missed=-1,
                branches_total=None,
                branches_covered=None,
            )

    def test_lines_missed_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="lines_missed"):
            FileCoverage(
                relative_path="t.py",
                line_coverage_pct=50.0,
                branch_coverage_pct=None,
                lines_total=10,
                lines_covered=5,
                lines_missed=3,  # Should be 5
                branches_total=None,
                branches_covered=None,
            )

    def test_branches_covered_exceeds_total_raises(self) -> None:
        with pytest.raises(ValueError, match="branches_covered.*>.*branches_total"):
            FileCoverage(
                relative_path="t.py",
                line_coverage_pct=50.0,
                branch_coverage_pct=None,
                lines_total=10,
                lines_covered=5,
                lines_missed=5,
                branches_total=4,
                branches_covered=5,
            )

    def test_line_coverage_pct_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="line_coverage_pct.*must be 0-100"):
            FileCoverage(
                relative_path="t.py",
                line_coverage_pct=-1.0,
                branch_coverage_pct=None,
                lines_total=10,
                lines_covered=5,
                lines_missed=5,
                branches_total=None,
                branches_covered=None,
            )

    def test_line_coverage_pct_over_100_raises(self) -> None:
        with pytest.raises(ValueError, match="line_coverage_pct.*must be 0-100"):
            FileCoverage(
                relative_path="t.py",
                line_coverage_pct=101.0,
                branch_coverage_pct=None,
                lines_total=10,
                lines_covered=5,
                lines_missed=5,
                branches_total=None,
                branches_covered=None,
            )

    def test_branch_coverage_pct_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="branch_coverage_pct.*must be 0-100"):
            FileCoverage(
                relative_path="t.py",
                line_coverage_pct=50.0,
                branch_coverage_pct=-5.0,
                lines_total=10,
                lines_covered=5,
                lines_missed=5,
                branches_total=4,
                branches_covered=2,
            )

    def test_branch_coverage_pct_over_100_raises(self) -> None:
        with pytest.raises(ValueError, match="branch_coverage_pct.*must be 0-100"):
            FileCoverage(
                relative_path="t.py",
                line_coverage_pct=50.0,
                branch_coverage_pct=200.0,
                lines_total=10,
                lines_covered=5,
                lines_missed=5,
                branches_total=4,
                branches_covered=2,
            )

    def test_uncovered_lines_exceeds_missed_raises(self) -> None:
        with pytest.raises(ValueError, match="uncovered_lines length.*>.*lines_missed"):
            FileCoverage(
                relative_path="t.py",
                line_coverage_pct=50.0,
                branch_coverage_pct=None,
                lines_total=10,
                lines_covered=8,
                lines_missed=2,
                branches_total=None,
                branches_covered=None,
                uncovered_lines=[1, 2, 3],  # 3 > lines_missed(2)
            )

    def test_uncovered_lines_zero_indexed_raises(self) -> None:
        with pytest.raises(ValueError, match="uncovered_lines must be 1-indexed"):
            FileCoverage(
                relative_path="t.py",
                line_coverage_pct=50.0,
                branch_coverage_pct=None,
                lines_total=10,
                lines_covered=8,
                lines_missed=2,
                branches_total=None,
                branches_covered=None,
                uncovered_lines=[0, 5],  # 0 is invalid
            )

    def test_valid_uncovered_lines(self) -> None:
        fc = FileCoverage(
            relative_path="t.py",
            line_coverage_pct=80.0,
            branch_coverage_pct=None,
            lines_total=10,
            lines_covered=8,
            lines_missed=2,
            branches_total=None,
            branches_covered=None,
            uncovered_lines=[3, 7],
        )
        assert fc.uncovered_lines == [3, 7]


# ===========================================================================
# compute_coverage_pct (base.py line 94)
# ===========================================================================
class TestComputeCoveragePct:
    def test_zero_total_returns_none(self) -> None:
        assert compute_coverage_pct(0, 0) is None

    def test_normal_computation(self) -> None:
        assert compute_coverage_pct(7, 10) == 70.0

    def test_full_coverage(self) -> None:
        assert compute_coverage_pct(10, 10) == 100.0

    def test_zero_covered(self) -> None:
        assert compute_coverage_pct(0, 10) == 0.0

    def test_rounding(self) -> None:
        assert compute_coverage_pct(1, 3) == 33.33


# ===========================================================================
# LCOV parser edge cases (uncovered lines: 79, 126, 131, 138-172)
# ===========================================================================
class TestLcovEdgeCases:
    def test_malformed_lf_value_ignored(self) -> None:
        """Non-integer LF: should be silently ignored."""
        parser = LcovParser()
        content = "SF:t.py\nLF:abc\nLH:0\nend_of_record\n"
        results = parser.parse(content)
        assert len(results) == 1
        # LF parse failed, so lines_found stays 0
        assert results[0].lines_total == 0

    def test_malformed_lh_value_ignored(self) -> None:
        parser = LcovParser()
        content = "SF:t.py\nLF:10\nLH:xyz\nend_of_record\n"
        results = parser.parse(content)
        assert len(results) == 1
        # LH parse failed, lines_hit stays 0
        assert results[0].lines_covered == 0

    def test_malformed_brf_value_ignored(self) -> None:
        parser = LcovParser()
        content = "SF:t.py\nLF:5\nLH:3\nBRF:abc\nBRH:2\nend_of_record\n"
        results = parser.parse(content)
        assert len(results) == 1
        # BRF parse failed => branches_found stays None
        assert results[0].branches_total is None

    def test_malformed_brh_value_ignored(self) -> None:
        parser = LcovParser()
        content = "SF:t.py\nLF:5\nLH:3\nBRF:4\nBRH:xyz\nend_of_record\n"
        results = parser.parse(content)
        assert len(results) == 1
        # BRH parse failed => branches_hit stays None
        assert results[0].branches_covered is None

    def test_da_records_track_uncovered(self) -> None:
        parser = LcovParser()
        content = "SF:t.py\nDA:1,5\nDA:2,0\nDA:3,0\nLF:3\nLH:1\nend_of_record\n"
        results = parser.parse(content)
        assert results[0].uncovered_lines == [2, 3]

    def test_malformed_da_ignored(self) -> None:
        parser = LcovParser()
        content = "SF:t.py\nDA:bad\nLF:1\nLH:0\nend_of_record\n"
        results = parser.parse(content)
        assert len(results) == 1
        assert results[0].uncovered_lines is None

    def test_consecutive_sf_emits_previous(self) -> None:
        """Two SF: lines without end_of_record between them."""
        parser = LcovParser()
        content = "SF:a.py\nLF:10\nLH:5\nSF:b.py\nLF:3\nLH:3\nend_of_record\n"
        results = parser.parse(content)
        assert len(results) == 2
        assert results[0].relative_path == "a.py"
        assert results[1].relative_path == "b.py"

    def test_trailing_file_without_end_of_record(self) -> None:
        parser = LcovParser()
        content = "SF:orphan.py\nLF:4\nLH:2"
        results = parser.parse(content)
        assert len(results) == 1
        assert results[0].relative_path == "orphan.py"

    def test_blank_lines_skipped(self) -> None:
        parser = LcovParser()
        content = "\n\nSF:t.py\n\nLF:5\n\nLH:3\n\nend_of_record\n\n"
        results = parser.parse(content)
        assert len(results) == 1
        assert results[0].lines_total == 5


# ===========================================================================
# Cobertura parser edge cases (uncovered lines: 83, 96-97, 103-104, 124-125, 131-132)
# ===========================================================================
class TestCoberturaEdgeCases:
    def test_class_without_filename_skipped(self) -> None:
        """A <class> element with no filename attribute should be skipped."""
        parser = CoberturaParser()
        content = """<?xml version="1.0"?>
<coverage line-rate="0.5">
    <packages>
        <package>
            <classes>
                <class line-rate="0.5">
                    <lines><line number="1" hits="1"/></lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>"""
        results = parser.parse(content)
        assert results == []

    def test_invalid_line_rate_defaults_to_zero(self) -> None:
        """Non-numeric line-rate should default to 0.0."""
        parser = CoberturaParser()
        content = """<?xml version="1.0"?>
<coverage line-rate="bad">
    <packages>
        <package>
            <classes>
                <class filename="t.py" line-rate="bad">
                    <lines><line number="1" hits="1"/></lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>"""
        results = parser.parse(content)
        assert len(results) == 1
        # line_rate parsing fails => defaults to 0.0, but line count is valid
        assert results[0].lines_covered == 1

    def test_invalid_branch_rate_ignored(self) -> None:
        parser = CoberturaParser()
        content = """<?xml version="1.0"?>
<coverage line-rate="0.5">
    <packages>
        <package>
            <classes>
                <class filename="t.py" line-rate="0.5" branch-rate="bad">
                    <lines><line number="1" hits="1"/></lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>"""
        results = parser.parse(content)
        assert len(results) == 1
        assert results[0].branch_coverage_pct is None

    def test_malformed_line_hits_ignored(self) -> None:
        """Malformed hits/number still increments lines_total (counted as
        a line element) but the bad line is not counted as covered."""
        parser = CoberturaParser()
        content = """<?xml version="1.0"?>
<coverage line-rate="0.5">
    <packages>
        <package>
            <classes>
                <class filename="t.py" line-rate="0.5">
                    <lines>
                        <line number="1" hits="1"/>
                        <line number="bad" hits="bad"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>"""
        results = parser.parse(content)
        assert len(results) == 1
        # Both <line> elements count toward total
        assert results[0].lines_total == 2
        # Only the valid line with hits=1 is counted as covered
        assert results[0].lines_covered == 1

    def test_no_lines_element_uses_line_rate(self) -> None:
        """When there are no <line> elements, fall back to line-rate."""
        parser = CoberturaParser()
        content = """<?xml version="1.0"?>
<coverage line-rate="0.7">
    <packages>
        <package>
            <classes>
                <class filename="t.py" line-rate="0.7">
                </class>
            </classes>
        </package>
    </packages>
</coverage>"""
        results = parser.parse(content)
        assert len(results) == 1
        assert results[0].lines_total == 0
        assert results[0].line_coverage_pct == 70.0

    def test_uncovered_lines_tracked(self) -> None:
        parser = CoberturaParser()
        content = """<?xml version="1.0"?>
<coverage line-rate="0.5">
    <packages>
        <package>
            <classes>
                <class filename="t.py" line-rate="0.5">
                    <lines>
                        <line number="1" hits="1"/>
                        <line number="2" hits="0"/>
                        <line number="3" hits="0"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>"""
        results = parser.parse(content)
        assert results[0].uncovered_lines == [2, 3]


# ===========================================================================
# JaCoCo parser edge cases (uncovered lines: 89, 97, 102, 127-134, 149)
# ===========================================================================
class TestJacocoEdgeCases:
    def test_sourcefile_without_name_skipped(self) -> None:
        parser = JacocoParser()
        content = """<?xml version="1.0"?>
<report name="test">
    <package name="com/example">
        <sourcefile>
            <counter type="LINE" missed="0" covered="5"/>
        </sourcefile>
    </package>
</report>"""
        results = parser.parse(content)
        assert results == []

    def test_empty_package_name(self) -> None:
        parser = JacocoParser()
        content = """<?xml version="1.0"?>
<report name="test">
    <package name="">
        <sourcefile name="Root.java">
            <counter type="LINE" missed="1" covered="9"/>
        </sourcefile>
    </package>
</report>"""
        results = parser.parse(content)
        assert len(results) == 1
        # Empty package name => path is just filename
        assert results[0].relative_path == "Root.java"

    def test_absolute_path_normalised(self) -> None:
        parser = JacocoParser()
        content = """<?xml version="1.0"?>
<report name="test">
    <package name="/com/example">
        <sourcefile name="Test.java">
            <counter type="LINE" missed="0" covered="5"/>
        </sourcefile>
    </package>
</report>"""
        results = parser.parse(content)
        assert len(results) == 1
        assert not results[0].relative_path.startswith("/")

    def test_uncovered_lines_from_line_elements(self) -> None:
        """<line> elements with mi>0 and ci==0 should produce uncovered_lines."""
        parser = JacocoParser()
        content = """<?xml version="1.0"?>
<report name="test">
    <package name="com/example">
        <sourcefile name="Test.java">
            <line nr="1" mi="0" ci="5"/>
            <line nr="2" mi="3" ci="0"/>
            <line nr="3" mi="2" ci="0"/>
            <counter type="LINE" missed="2" covered="1"/>
        </sourcefile>
    </package>
</report>"""
        results = parser.parse(content)
        assert results[0].uncovered_lines == [2, 3]

    def test_malformed_line_element_ignored(self) -> None:
        parser = JacocoParser()
        content = """<?xml version="1.0"?>
<report name="test">
    <package name="com/example">
        <sourcefile name="Test.java">
            <line nr="bad" mi="bad" ci="bad"/>
            <counter type="LINE" missed="0" covered="5"/>
        </sourcefile>
    </package>
</report>"""
        results = parser.parse(content)
        assert len(results) == 1
        assert results[0].uncovered_lines is None

    def test_nested_packages(self) -> None:
        parser = JacocoParser()
        content = """<?xml version="1.0"?>
<report name="test">
    <package name="com/example/core">
        <sourcefile name="Service.java">
            <counter type="LINE" missed="3" covered="7"/>
            <counter type="BRANCH" missed="1" covered="5"/>
        </sourcefile>
    </package>
    <package name="com/example/util">
        <sourcefile name="Helper.java">
            <counter type="LINE" missed="0" covered="10"/>
        </sourcefile>
    </package>
</report>"""
        results = parser.parse(content)
        assert len(results) == 2
        paths = {r.relative_path for r in results}
        assert "com/example/core/Service.java" in paths
        assert "com/example/util/Helper.java" in paths

    def test_no_line_counter(self) -> None:
        """Sourcefile with no LINE counter should produce zeros."""
        parser = JacocoParser()
        content = """<?xml version="1.0"?>
<report name="test">
    <package name="com/example">
        <sourcefile name="NoLines.java">
            <counter type="INSTRUCTION" missed="10" covered="90"/>
        </sourcefile>
    </package>
</report>"""
        results = parser.parse(content)
        assert len(results) == 1
        assert results[0].lines_total == 0
        assert results[0].line_coverage_pct is None


# ===========================================================================
# Istanbul parser edge case (uncovered line: 87)
# ===========================================================================
class TestIstanbulEdgeCases:
    def test_non_dict_file_data_skipped(self) -> None:
        """File entries that are not dicts should be skipped."""
        parser = IstanbulParser()
        content = '{"test.js": "not a dict", "ok.js": {"path": "ok.js", "s": {"0": 1}}}'
        results = parser.parse(content)
        assert len(results) == 1
        assert results[0].relative_path == "ok.js"

    def test_missing_path_uses_key(self) -> None:
        parser = IstanbulParser()
        content = '{"src/main.js": {"s": {"0": 5}}}'
        results = parser.parse(content)
        assert len(results) == 1
        assert results[0].relative_path == "src/main.js"

    def test_uncovered_lines_from_statement_map(self) -> None:
        parser = IstanbulParser()
        content = """{
            "test.js": {
                "path": "test.js",
                "statementMap": {
                    "0": {"start": {"line": 1}, "end": {"line": 1}},
                    "1": {"start": {"line": 2}, "end": {"line": 2}},
                    "2": {"start": {"line": 3}, "end": {"line": 3}}
                },
                "s": {"0": 5, "1": 0, "2": 0},
                "b": {}
            }
        }"""
        results = parser.parse(content)
        assert results[0].uncovered_lines == [2, 3]

    def test_empty_branches_treated_as_no_branch_data(self) -> None:
        parser = IstanbulParser()
        content = '{"t.js": {"path": "t.js", "s": {"0": 1}, "b": {}}}'
        results = parser.parse(content)
        assert results[0].branches_total is None
        assert results[0].branches_covered is None
        assert results[0].branch_coverage_pct is None

    def test_uncovered_statement_without_statementmap_line(self) -> None:
        """Uncovered statement with malformed or missing start.line is skipped."""
        parser = IstanbulParser()
        content = """{
            "test.js": {
                "path": "test.js",
                "statementMap": {
                    "0": {"start": {}, "end": {}},
                    "1": "not a dict"
                },
                "s": {"0": 0, "1": 0},
                "b": {}
            }
        }"""
        results = parser.parse(content)
        # Neither has a valid line number => uncovered_lines should be None
        assert results[0].uncovered_lines is None

    def test_deduplicates_uncovered_lines(self) -> None:
        """Multiple statements on same line should be deduplicated."""
        parser = IstanbulParser()
        content = """{
            "test.js": {
                "path": "test.js",
                "statementMap": {
                    "0": {"start": {"line": 5}, "end": {"line": 5}},
                    "1": {"start": {"line": 5}, "end": {"line": 5}}
                },
                "s": {"0": 0, "1": 0},
                "b": {}
            }
        }"""
        results = parser.parse(content)
        assert results[0].uncovered_lines == [5]  # Deduplicated
