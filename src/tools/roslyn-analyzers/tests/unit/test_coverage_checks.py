"""
Tests for coverage checks (CV-1 to CV-8).

Tests cover:
- Security rule coverage (CV-1)
- Design rule coverage with RCS prefix detection (CV-2)
- Resource rule coverage (CV-3)
- Performance rule coverage (CV-4)
- Dead code rule coverage (CV-5)
- DD category coverage (CV-6)
- File coverage (CV-7)
- Line-level precision (CV-8)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.coverage import (
    cv1_security_rule_coverage,
    cv2_design_rule_coverage,
    cv3_resource_rule_coverage,
    cv4_performance_rule_coverage,
    cv5_dead_code_rule_coverage,
    cv6_dd_category_coverage,
    cv7_file_coverage,
    cv8_line_level_precision,
    run_all_coverage_checks,
)


def _make_analysis(violations_by_rule=None, violations_by_category=None, files=None):
    return {
        "summary": {
            "violations_by_rule": violations_by_rule or {},
            "violations_by_category": violations_by_category or {},
        },
        "files": files or [],
    }


def _make_gt(files=None):
    return {"files": files or {}}


class TestCV1SecurityRuleCoverage:
    """CV-1: Security rule coverage."""

    def test_passes_with_8_rules(self):
        rules = {
            "CA2100": 1, "CA5350": 2, "CA5351": 1, "CA5364": 1,
            "CA5386": 1, "CA2300": 1, "SCS0006": 1, "SCS0010": 1,
        }
        result = cv1_security_rule_coverage(_make_analysis(violations_by_rule=rules), {})
        assert result.passed is True
        assert result.check_id == "CV-1"

    def test_fails_with_few_rules(self):
        rules = {"CA2100": 1, "CA5350": 2}
        result = cv1_security_rule_coverage(_make_analysis(violations_by_rule=rules), {})
        assert result.passed is False
        assert result.evidence["triggered_rules"] == ["CA2100", "CA5350"]

    def test_zero_rules(self):
        result = cv1_security_rule_coverage(_make_analysis(), {})
        assert result.passed is False
        assert result.score == pytest.approx(0.0)


class TestCV2DesignRuleCoverage:
    """CV-2: Design rule coverage with Roslynator prefix detection."""

    def test_passes_with_design_and_rcs_rules(self):
        rules = {
            "CA1051": 1, "CA1040": 1, "CA1000": 1, "CA1061": 1,
            "CA1502": 1, "IDE0040": 1,
            "RCS1001": 1, "RCS1002": 1, "RCS1003": 1,
        }
        result = cv2_design_rule_coverage(_make_analysis(violations_by_rule=rules), {})
        # 6 base + up to 4 RCS = 10 >= 8
        assert result.passed is True

    def test_fails_without_enough_rules(self):
        rules = {"CA1051": 1, "CA1040": 1}
        result = cv2_design_rule_coverage(_make_analysis(violations_by_rule=rules), {})
        assert result.passed is False


class TestCV3ResourceRuleCoverage:
    """CV-3: Resource rule coverage."""

    def test_passes_with_6_rules(self):
        rules = {
            "CA2000": 1, "CA1001": 1, "CA1063": 1,
            "CA2016": 1, "IDISP001": 1, "IDISP006": 1,
        }
        result = cv3_resource_rule_coverage(_make_analysis(violations_by_rule=rules), {})
        assert result.passed is True

    def test_fails_with_few_rules(self):
        rules = {"CA2000": 1}
        result = cv3_resource_rule_coverage(_make_analysis(violations_by_rule=rules), {})
        assert result.passed is False


class TestCV4PerformanceRuleCoverage:
    """CV-4: Performance rule coverage."""

    def test_passes_with_3_rules(self):
        rules = {"CA1826": 1, "CA1829": 1, "CA1825": 1}
        result = cv4_performance_rule_coverage(_make_analysis(violations_by_rule=rules), {})
        assert result.passed is True

    def test_fails_below_threshold(self):
        rules = {"CA1826": 1}
        result = cv4_performance_rule_coverage(_make_analysis(violations_by_rule=rules), {})
        assert result.passed is False
        assert result.score == pytest.approx(0.2)


class TestCV5DeadCodeRuleCoverage:
    """CV-5: Dead code rule coverage."""

    def test_passes_with_4_rules(self):
        rules = {"IDE0005": 3, "IDE0060": 1, "IDE0052": 2, "IDE0059": 1}
        result = cv5_dead_code_rule_coverage(_make_analysis(violations_by_rule=rules), {})
        assert result.passed is True
        assert result.score == pytest.approx(0.8)

    def test_fails_with_few_rules(self):
        rules = {"IDE0005": 1}
        result = cv5_dead_code_rule_coverage(_make_analysis(violations_by_rule=rules), {})
        assert result.passed is False


class TestCV6DDCategoryCoverage:
    """CV-6: DD category coverage."""

    def test_all_5_categories_covered(self):
        cats = {
            "security": 5, "design": 3, "resource": 2,
            "performance": 1, "dead_code": 4,
        }
        result = cv6_dd_category_coverage(
            _make_analysis(violations_by_category=cats), {}
        )
        assert result.passed is True
        assert result.score == pytest.approx(1.0)

    def test_missing_category(self):
        cats = {"security": 5, "design": 3, "resource": 2, "performance": 1}
        result = cv6_dd_category_coverage(
            _make_analysis(violations_by_category=cats), {}
        )
        assert result.passed is False
        assert "dead_code" in result.evidence["missing_categories"]

    def test_zero_count_not_covered(self):
        """A category with 0 count is not considered covered."""
        cats = {
            "security": 5, "design": 3, "resource": 2,
            "performance": 1, "dead_code": 0,
        }
        result = cv6_dd_category_coverage(
            _make_analysis(violations_by_category=cats), {}
        )
        assert result.passed is False


class TestCV7FileCoverage:
    """CV-7: File coverage."""

    def test_all_expected_files_analyzed(self):
        gt_files = {
            "security/sql_injection.cs": {},
            "design/empty_interfaces.cs": {},
        }
        analysis_files = [
            {"path": "security/sql_injection.cs", "relative_path": "security/sql_injection.cs"},
            {"path": "design/empty_interfaces.cs", "relative_path": "design/empty_interfaces.cs"},
        ]
        result = cv7_file_coverage(
            _make_analysis(files=analysis_files), _make_gt(files=gt_files)
        )
        assert result.passed is True
        assert result.score == pytest.approx(1.0)

    def test_missing_expected_files(self):
        gt_files = {
            "security/sql_injection.cs": {},
            "design/empty_interfaces.cs": {},
            "resource/undisposed.cs": {},
        }
        analysis_files = [
            {"path": "security/sql_injection.cs", "relative_path": "security/sql_injection.cs"},
        ]
        result = cv7_file_coverage(
            _make_analysis(files=analysis_files), _make_gt(files=gt_files)
        )
        assert result.passed is False
        assert result.evidence["covered_count"] == 1
        assert result.evidence["expected_count"] == 3

    def test_no_expected_files(self):
        result = cv7_file_coverage(_make_analysis(), _make_gt())
        # 0/0 = 0, but does not pass (coverage < 1.0 treated differently)
        assert result.score == 0


class TestCV8LineLevelPrecision:
    """CV-8: Line-level precision."""

    def test_all_violations_have_lines(self):
        files = [
            {"violations": [
                {"line_start": 10},
                {"line_start": 20},
                {"line_start": 30},
            ]}
        ]
        result = cv8_line_level_precision(_make_analysis(files=files), {})
        assert result.passed is True
        assert result.score == pytest.approx(1.0)

    def test_some_violations_missing_lines(self):
        files = [
            {"violations": [
                {"line_start": 10},
                {"line_start": 0},
                {"line_start": 30},
            ]}
        ]
        result = cv8_line_level_precision(_make_analysis(files=files), {})
        # 2/3 = 66.7% < 70%
        assert result.passed is False
        assert result.score == pytest.approx(2 / 3)

    def test_no_violations(self):
        files = [{"violations": []}]
        result = cv8_line_level_precision(_make_analysis(files=files), {})
        # 0 violations -> precision 1.0
        assert result.passed is True
        assert result.score == pytest.approx(1.0)


class TestRunAllCoverageChecks:
    """Test run_all_coverage_checks returns all 8 checks."""

    def test_returns_8_checks(self):
        analysis = _make_analysis()
        gt = _make_gt()
        results = run_all_coverage_checks(analysis, gt)
        assert len(results) == 8
        check_ids = [r.check_id for r in results]
        for i in range(1, 9):
            assert f"CV-{i}" in check_ids
