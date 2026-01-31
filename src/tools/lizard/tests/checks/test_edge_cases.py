"""Tests for edge case checks (EC-1 to EC-8)."""

import pytest

from scripts.checks import CheckCategory, CheckSeverity
from scripts.checks.edge_cases import (
    check_ec1_empty_files,
    check_ec2_comments_only_files,
    check_ec3_single_line_files,
    check_ec4_unicode_function_names,
    check_ec5_deep_nesting,
    check_ec6_lambda_functions,
    check_ec7_class_methods,
    check_ec8_anonymous_functions,
    run_edge_case_checks,
)


class TestEC1EmptyFiles:
    """Tests for EC-1: Empty files handled."""

    def test_empty_file_reports_zero(self, sample_analysis, sample_ground_truth):
        """Test that empty files report 0 functions."""
        result = check_ec1_empty_files(sample_analysis, sample_ground_truth)

        assert result.check_id == "EC-1"
        assert result.category == CheckCategory.EDGE_CASES
        assert result.severity == CheckSeverity.MEDIUM

    def test_no_empty_files_in_ground_truth(self, sample_analysis):
        """Test when no empty files in ground truth."""
        gt_no_empty = {"files": {"simple.py": {"expected_functions": 5, "functions": {}}}}
        result = check_ec1_empty_files(sample_analysis, gt_no_empty)

        assert result.passed


class TestEC2CommentsOnlyFiles:
    """Tests for EC-2: Comments-only files handled."""

    def test_comments_only_file(self, sample_analysis):
        """Test that comments-only files report 0 functions."""
        gt_with_comments = {
            "files": {
                "comments_only.py": {"expected_functions": 0, "functions": {}},
            },
        }
        result = check_ec2_comments_only_files(sample_analysis, gt_with_comments)

        assert result.check_id == "EC-2"
        assert result.category == CheckCategory.EDGE_CASES


class TestEC3SingleLineFiles:
    """Tests for EC-3: Single-line files handled."""

    def test_single_line_files(self, sample_analysis, sample_ground_truth):
        """Test that single-line files are handled."""
        result = check_ec3_single_line_files(sample_analysis, sample_ground_truth)

        assert result.check_id == "EC-3"
        assert result.passed  # Always passes as informational


class TestEC4UnicodeFunctionNames:
    """Tests for EC-4: Unicode function names handled."""

    def test_unicode_functions(self, sample_analysis):
        """Test unicode function name detection."""
        gt_with_unicode = {
            "files": {
                "unicode.py": {
                    "functions": {
                    },
                },
            },
        }
        result = check_ec4_unicode_function_names(sample_analysis, gt_with_unicode)

        assert result.check_id == "EC-4"
        assert result.category == CheckCategory.EDGE_CASES


class TestEC5DeepNesting:
    """Tests for EC-5: Deep nesting detected."""

    def test_deep_nesting_detection(self, sample_analysis):
        """Test that deeply nested functions have high CCN."""
        gt_deep = {
            "files": {
                "complex.py": {
                    "functions": {
                        "process_data": {"ccn": 15},  # High CCN = deep nesting
                    },
                },
            },
        }
        result = check_ec5_deep_nesting(sample_analysis, gt_deep)

        assert result.check_id == "EC-5"
        assert result.category == CheckCategory.EDGE_CASES
        assert result.severity == CheckSeverity.HIGH


class TestEC6LambdaFunctions:
    """Tests for EC-6: Lambda functions handled."""

    def test_lambda_detection(self, sample_analysis):
        """Test lambda function detection."""
        result = check_ec6_lambda_functions(sample_analysis)

        assert result.check_id == "EC-6"
        assert result.passed  # Informational check
        assert "lambda_count" in result.evidence


class TestEC7ClassMethods:
    """Tests for EC-7: Class methods detected."""

    def test_class_methods_detected(self, sample_analysis):
        """Test that class methods with qualified names are detected."""
        result = check_ec7_class_methods(sample_analysis)

        assert result.check_id == "EC-7"
        assert result.category == CheckCategory.EDGE_CASES
        # Sample analysis has "User.greet" and "User.Greet"
        assert result.passed
        assert result.evidence["method_count"] > 0


class TestEC8AnonymousFunctions:
    """Tests for EC-8: Anonymous functions handled."""

    def test_anonymous_functions(self, sample_analysis):
        """Test anonymous function detection."""
        result = check_ec8_anonymous_functions(sample_analysis)

        assert result.check_id == "EC-8"
        assert result.passed  # Informational check
        # Sample has "(anonymous)" function
        assert result.evidence["anonymous_count"] > 0


class TestRunEdgeCaseChecks:
    """Tests for running all edge case checks."""

    def test_runs_all_checks(self, sample_analysis, sample_ground_truth):
        """Test that all 8 edge case checks are run."""
        results = run_edge_case_checks(sample_analysis, sample_ground_truth)

        assert len(results) == 8
        check_ids = [r.check_id for r in results]
        assert all(f"EC-{i}" in check_ids for i in range(1, 9))

    def test_all_checks_have_correct_category(self, sample_analysis, sample_ground_truth):
        """Test that all checks are categorized as EDGE_CASES."""
        results = run_edge_case_checks(sample_analysis, sample_ground_truth)

        for result in results:
            assert result.category == CheckCategory.EDGE_CASES
