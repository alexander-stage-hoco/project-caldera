"""
Unit tests for report_formatter.py
"""

import json
from typing import Any, Dict

import pytest

from scripts.checks import CheckCategory, CheckResult, DimensionResult
from scripts.report_formatter import (
    Colors,
    CATEGORY_NAMES,
    RECOMMENDATIONS,
    EvaluationResult,
    ReportFormatter,
    get_recommendations,
)


class TestColors:
    """Tests for Colors class."""

    def test_reset_code(self):
        """RESET should be a valid ANSI code."""
        assert Colors.RESET == "\033[0m"

    def test_color_codes_exist(self):
        """Common color codes should exist."""
        assert hasattr(Colors, "RED")
        assert hasattr(Colors, "GREEN")
        assert hasattr(Colors, "YELLOW")
        assert hasattr(Colors, "BLUE")
        assert hasattr(Colors, "CYAN")


class TestCategoryNames:
    """Tests for CATEGORY_NAMES mapping."""

    def test_all_categories_have_names(self):
        """All check categories should have display names."""
        for category in CheckCategory:
            assert category in CATEGORY_NAMES

    def test_names_are_human_readable(self):
        """Display names should be human readable."""
        assert CATEGORY_NAMES[CheckCategory.OUTPUT_QUALITY] == "Output Quality"
        assert CATEGORY_NAMES[CheckCategory.GIT_METADATA] == "Git Metadata"
        assert CATEGORY_NAMES[CheckCategory.CONTENT_METADATA] == "Content Metadata"


class TestRecommendations:
    """Tests for RECOMMENDATIONS mapping."""

    def test_recommendations_exist(self):
        """Recommendations should exist for common prefixes."""
        assert "OQ" in RECOMMENDATIONS
        assert "AC" in RECOMMENDATIONS
        assert "CL" in RECOMMENDATIONS
        assert "PF" in RECOMMENDATIONS
        assert "GT" in RECOMMENDATIONS
        assert "CT" in RECOMMENDATIONS


class TestEvaluationResult:
    """Tests for EvaluationResult dataclass."""

    def test_from_dict_basic(self):
        """Should create result from basic dict."""
        data = {
            "repository": "test-repo",
            "timestamp": "2026-01-10T12:00:00Z",
            "overall_score": 4.5,
            "decision": "STRONG_PASS",
            "dimensions": [],
            "summary": {
                "total_checks": 10,
                "passed_checks": 9,
            },
        }

        result = EvaluationResult.from_dict(data)

        assert result.repository == "test-repo"
        assert result.timestamp == "2026-01-10T12:00:00Z"
        assert result.overall_score == 4.5
        assert result.decision == "STRONG_PASS"
        assert result.total_checks == 10
        assert result.passed_checks == 9

    def test_from_dict_with_dimensions(self):
        """Should parse dimensions correctly."""
        data = {
            "repository": "test-repo",
            "timestamp": "",
            "overall_score": 4.0,
            "decision": "STRONG_PASS",
            "dimensions": [
                {
                    "category": "output_quality",
                    "score": 5.0,
                    "passed_count": 8,
                    "total_count": 8,
                    "checks": [
                        {
                            "check_id": "OQ-1",
                            "name": "JSON Valid",
                            "category": "output_quality",
                            "passed": True,
                            "score": 1.0,
                            "message": "All good",
                            "evidence": {},
                        }
                    ],
                }
            ],
            "summary": {"total_checks": 8, "passed_checks": 8},
        }

        result = EvaluationResult.from_dict(data)

        assert len(result.dimensions) == 1
        assert result.dimensions[0].category == CheckCategory.OUTPUT_QUALITY
        assert result.dimensions[0].score == 5.0
        assert len(result.dimensions[0].checks) == 1
        assert result.dimensions[0].checks[0].check_id == "OQ-1"


class TestReportFormatterInit:
    """Tests for ReportFormatter initialization."""

    def test_default_color_enabled(self):
        """Colors should be enabled by default."""
        formatter = ReportFormatter()
        assert formatter.use_color is True

    def test_color_disabled(self):
        """Colors can be disabled."""
        formatter = ReportFormatter(use_color=False)
        assert formatter.use_color is False


class TestReportFormatterColor:
    """Tests for color formatting."""

    def test_color_applied_when_enabled(self):
        """Color codes should be applied when enabled."""
        formatter = ReportFormatter(use_color=True)
        result = formatter._color("test", Colors.GREEN)
        assert Colors.GREEN in result
        assert Colors.RESET in result
        assert "test" in result

    def test_color_not_applied_when_disabled(self):
        """Color codes should not be applied when disabled."""
        formatter = ReportFormatter(use_color=False)
        result = formatter._color("test", Colors.GREEN)
        assert result == "test"
        assert Colors.GREEN not in result


class TestReportFormatterStatusIcon:
    """Tests for status icon formatting."""

    def test_passed_icon(self):
        """Passed checks should show checkmark."""
        formatter = ReportFormatter(use_color=False)
        icon = formatter._status_icon(True)
        assert "✓" in icon

    def test_failed_icon(self):
        """Failed checks should show X."""
        formatter = ReportFormatter(use_color=False)
        icon = formatter._status_icon(False)
        assert "✗" in icon


class TestReportFormatterScoreColor:
    """Tests for score color selection."""

    def test_high_score_green(self):
        """High scores should be green."""
        formatter = ReportFormatter()
        color = formatter._score_color(4.5)
        assert color == Colors.GREEN

    def test_medium_score_yellow(self):
        """Medium scores should be yellow."""
        formatter = ReportFormatter()
        color = formatter._score_color(3.5)
        assert color == Colors.YELLOW

    def test_low_score_red(self):
        """Low scores should be red."""
        formatter = ReportFormatter()
        color = formatter._score_color(2.5)
        assert color == Colors.RED


def _create_sample_result() -> EvaluationResult:
    """Create a sample evaluation result for testing."""
    checks = [
        CheckResult(
            check_id="OQ-1",
            name="JSON Valid",
            category=CheckCategory.OUTPUT_QUALITY,
            passed=True,
            score=1.0,
            message="All good",
            evidence={},
        ),
        CheckResult(
            check_id="OQ-2",
            name="Schema Compliant",
            category=CheckCategory.OUTPUT_QUALITY,
            passed=False,
            score=0.0,
            message="Schema validation failed",
            evidence={"error": "Missing field 'files'"},
        ),
    ]

    dim = DimensionResult(
        category=CheckCategory.OUTPUT_QUALITY,
        checks=checks,
        passed_count=1,
        total_count=2,
        score=3.0,
    )

    return EvaluationResult(
        repository="test-repo",
        timestamp="2026-01-10T12:00:00Z",
        overall_score=3.5,
        decision="PASS",
        dimensions=[dim],
        total_checks=2,
        passed_checks=1,
    )


class TestReportFormatterTable:
    """Tests for table format output."""

    def test_table_contains_repository(self):
        """Table should contain repository name."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter._format_table(result, verbose=False)
        assert "test-repo" in output

    def test_table_contains_score(self):
        """Table should contain overall score."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter._format_table(result, verbose=False)
        assert "3.5" in output

    def test_table_contains_decision(self):
        """Table should contain decision."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter._format_table(result, verbose=False)
        assert "PASS" in output

    def test_table_contains_check_ids(self):
        """Table should contain check IDs."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter._format_table(result, verbose=False)
        assert "OQ-1" in output
        assert "OQ-2" in output

    def test_table_contains_box_characters(self):
        """Table should contain box-drawing characters."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter._format_table(result, verbose=False)
        assert "╔" in output
        assert "╚" in output
        assert "┌" in output
        assert "└" in output


class TestReportFormatterSummary:
    """Tests for summary format output."""

    def test_summary_contains_repository(self):
        """Summary should contain repository name."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter._format_summary(result, verbose=False)
        assert "test-repo" in output

    def test_summary_contains_score(self):
        """Summary should contain overall score."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter._format_summary(result, verbose=False)
        assert "3.5/5.0" in output

    def test_summary_contains_dimension_scores(self):
        """Summary should contain dimension scores."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter._format_summary(result, verbose=False)
        assert "Output Quality" in output
        assert "(1/2 checks)" in output

    def test_summary_contains_failed_checks(self):
        """Summary should list failed checks."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter._format_summary(result, verbose=False)
        assert "Failed Checks:" in output
        assert "OQ-2" in output


class TestReportFormatterMarkdown:
    """Tests for markdown format output."""

    def test_markdown_contains_header(self):
        """Markdown should contain H1 header."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter._format_markdown(result, verbose=False)
        assert "# Evaluation Report: test-repo" in output

    def test_markdown_contains_table(self):
        """Markdown should contain summary table."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter._format_markdown(result, verbose=False)
        assert "| Dimension | Score |" in output
        assert "|-----------|-------|" in output

    def test_markdown_contains_failed_section(self):
        """Markdown should contain failed checks section."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter._format_markdown(result, verbose=False)
        assert "## Failed Checks" in output
        assert "### OQ-2:" in output


class TestReportFormatterJson:
    """Tests for JSON format output."""

    def test_json_is_valid(self):
        """JSON output should be valid JSON."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter._format_json(result)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_json_contains_fields(self):
        """JSON should contain required fields."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter._format_json(result)
        parsed = json.loads(output)
        assert "repository" in parsed
        assert "overall_score" in parsed
        assert "decision" in parsed
        assert "dimensions" in parsed

    def test_json_score_value(self):
        """JSON score should match result."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter._format_json(result)
        parsed = json.loads(output)
        assert parsed["overall_score"] == 3.5


class TestReportFormatterFormat:
    """Tests for main format() method."""

    def test_format_table(self):
        """format() should handle table format."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter.format(result, format_type="table")
        assert "╔" in output

    def test_format_summary(self):
        """format() should handle summary format."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter.format(result, format_type="summary")
        assert "Layout Scanner Evaluation Summary" in output

    def test_format_markdown(self):
        """format() should handle markdown format."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter.format(result, format_type="markdown")
        assert "# Evaluation Report:" in output

    def test_format_json(self):
        """format() should handle json format."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter.format(result, format_type="json")
        parsed = json.loads(output)
        assert "repository" in parsed


class TestReportFormatterFiltering:
    """Tests for filtering in format() method."""

    def test_status_filter_passed(self):
        """Status filter should only show passed checks."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        # Use table format which shows individual checks
        output = formatter.format(result, format_type="table", status_filter="passed")
        assert "OQ-1" in output
        # OQ-2 is failed, should not appear with passed filter
        assert "OQ-2" not in output

    def test_status_filter_failed(self):
        """Status filter should only show failed checks."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        output = formatter.format(result, format_type="table", status_filter="failed")
        assert "OQ-2" in output

    def test_category_filter(self):
        """Category filter should only show specified category."""
        formatter = ReportFormatter(use_color=False)
        result = _create_sample_result()
        # Add another dimension
        result.dimensions.append(
            DimensionResult(
                category=CheckCategory.ACCURACY,
                checks=[],
                passed_count=0,
                total_count=0,
                score=5.0,
            )
        )
        output = formatter.format(
            result, format_type="table", category_filter="output_quality"
        )
        assert "Output Quality" in output
        # Accuracy should not appear when filtering
        assert "Accuracy" not in output


class TestGetRecommendations:
    """Tests for get_recommendations function."""

    def test_empty_list(self):
        """Empty check list should return empty recommendations."""
        recs = get_recommendations([])
        assert recs == []

    def test_single_failed_check(self):
        """Single failed check should return one recommendation."""
        check = CheckResult(
            check_id="CL-1",
            name="Test",
            category=CheckCategory.CLASSIFICATION,
            passed=False,
            score=0.0,
            message="Failed",
            evidence={},
        )
        recs = get_recommendations([check])
        assert len(recs) == 1
        assert "classification" in recs[0].lower()

    def test_multiple_same_prefix(self):
        """Multiple checks with same prefix should return one recommendation."""
        checks = [
            CheckResult(
                check_id="CL-1",
                name="Test 1",
                category=CheckCategory.CLASSIFICATION,
                passed=False,
                score=0.0,
                message="Failed",
                evidence={},
            ),
            CheckResult(
                check_id="CL-2",
                name="Test 2",
                category=CheckCategory.CLASSIFICATION,
                passed=False,
                score=0.0,
                message="Failed",
                evidence={},
            ),
        ]
        recs = get_recommendations(checks)
        assert len(recs) == 1

    def test_multiple_different_prefixes(self):
        """Multiple checks with different prefixes should return multiple recommendations."""
        checks = [
            CheckResult(
                check_id="CL-1",
                name="Test 1",
                category=CheckCategory.CLASSIFICATION,
                passed=False,
                score=0.0,
                message="Failed",
                evidence={},
            ),
            CheckResult(
                check_id="PF-1",
                name="Test 2",
                category=CheckCategory.PERFORMANCE,
                passed=False,
                score=0.0,
                message="Failed",
                evidence={},
            ),
        ]
        recs = get_recommendations(checks)
        assert len(recs) == 2
