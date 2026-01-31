"""Tests for accuracy checks (AC-1 to AC-8)."""

import pytest

from scripts.checks import CheckCategory, CheckSeverity
from scripts.checks.accuracy import (
    check_ac1_simple_functions,
    check_ac2_complex_functions,
    check_ac3_massive_functions,
    check_ac4_function_count,
    check_ac5_nloc_accuracy,
    check_ac6_parameter_count,
    check_ac7_line_range,
    check_ac8_nested_functions,
    run_accuracy_checks,
)


class TestAC1SimpleFunctions:
    """Tests for AC-1: Simple functions CCN=1."""

    def test_all_simple_functions_match(self, sample_analysis, sample_ground_truth):
        """Test that simple functions with CCN=1 are correctly identified."""
        result = check_ac1_simple_functions(sample_analysis, sample_ground_truth)

        assert result.check_id == "AC-1"
        assert result.category == CheckCategory.ACCURACY
        assert result.severity == CheckSeverity.CRITICAL
        # Should have some matches since we have CCN=1 functions
        assert result.score > 0

    def test_no_simple_functions_in_ground_truth(self, sample_analysis):
        """Test handling when no simple functions exist."""
        empty_gt = {"files": {}}
        result = check_ac1_simple_functions(sample_analysis, empty_gt)

        assert result.passed
        assert result.score == 1.0


class TestAC2ComplexFunctions:
    """Tests for AC-2: Complex functions CCN 10-20."""

    def test_complex_functions_detected(self, sample_analysis, sample_ground_truth):
        """Test that complex functions (CCN 10-20) are validated."""
        result = check_ac2_complex_functions(sample_analysis, sample_ground_truth)

        assert result.check_id == "AC-2"
        assert result.category == CheckCategory.ACCURACY
        assert result.severity == CheckSeverity.HIGH

    def test_no_complex_functions(self, sample_analysis):
        """Test handling when no complex functions exist."""
        simple_gt = {
            "files": {
                "simple.py": {
                    "functions": {"add": {"ccn": 1}},
                },
            },
        }
        result = check_ac2_complex_functions(sample_analysis, simple_gt)

        assert result.passed
        assert result.score == 1.0


class TestAC3MassiveFunctions:
    """Tests for AC-3: Massive functions CCN >= 20."""

    def test_massive_functions_detected(self, sample_analysis):
        """Test that massive functions (CCN >= 20) are validated."""
        massive_gt = {
            "files": {
                "complex.py": {
                    "functions": {"mega_function": {"ccn": 25}},
                },
            },
        }
        result = check_ac3_massive_functions(sample_analysis, massive_gt)

        assert result.check_id == "AC-3"
        assert result.category == CheckCategory.ACCURACY


class TestAC4FunctionCount:
    """Tests for AC-4: Function count matches expected."""

    def test_function_count_matches(self, sample_analysis, sample_ground_truth):
        """Test that function counts are validated."""
        result = check_ac4_function_count(sample_analysis, sample_ground_truth)

        assert result.check_id == "AC-4"
        assert result.category == CheckCategory.ACCURACY
        assert result.severity == CheckSeverity.CRITICAL
        assert "total_expected" in result.evidence
        assert "total_actual" in result.evidence


class TestAC5NlocAccuracy:
    """Tests for AC-5: NLOC accuracy within 10%."""

    def test_nloc_within_tolerance(self, sample_analysis, sample_ground_truth):
        """Test NLOC accuracy check."""
        result = check_ac5_nloc_accuracy(sample_analysis, sample_ground_truth)

        assert result.check_id == "AC-5"
        assert result.category == CheckCategory.ACCURACY
        assert result.severity == CheckSeverity.MEDIUM


class TestAC6ParameterCount:
    """Tests for AC-6: Parameter count accuracy."""

    def test_parameter_count_matches(self, sample_analysis, sample_ground_truth):
        """Test parameter count accuracy."""
        result = check_ac6_parameter_count(sample_analysis, sample_ground_truth)

        assert result.check_id == "AC-6"
        assert result.category == CheckCategory.ACCURACY


class TestAC7LineRange:
    """Tests for AC-7: Line range accuracy.

    AC-7 validates that Lizard correctly identifies function boundaries.
    Start lines should match exactly, end lines should match exactly.
    """

    def test_line_range_accuracy(self, sample_analysis, sample_ground_truth):
        """Test start/end line accuracy."""
        result = check_ac7_line_range(sample_analysis, sample_ground_truth)

        assert result.check_id == "AC-7"
        assert result.category == CheckCategory.ACCURACY
        assert "correct_start" in result.evidence
        assert "correct_end" in result.evidence

    def test_ac7_exact_start_line_match(self):
        """AC-7 should require exact start line matches."""
        analysis = {
            "files": [
                {
                    "path": "test.py",
                    "functions": [
                        {"name": "func1", "ccn": 1, "start_line": 10, "end_line": 20},
                    ],
                },
            ],
        }
        ground_truth = {
            "files": {
                "test.py": {
                    "functions": {
                        "func1": {"ccn": 1, "start_line": 10, "end_line": 20},
                    },
                },
            },
        }

        result = check_ac7_line_range(analysis, ground_truth)

        assert result.check_id == "AC-7"
        assert result.evidence["correct_start"] == 1
        assert result.score == 1.0

    def test_ac7_start_line_mismatch_fails(self):
        """AC-7 should fail when start line doesn't match exactly."""
        analysis = {
            "files": [
                {
                    "path": "test.py",
                    "functions": [
                        {"name": "func1", "ccn": 1, "start_line": 11, "end_line": 20},  # Off by 1
                    ],
                },
            ],
        }
        ground_truth = {
            "files": {
                "test.py": {
                    "functions": {
                        "func1": {"ccn": 1, "start_line": 10, "end_line": 20},
                    },
                },
            },
        }

        result = check_ac7_line_range(analysis, ground_truth)

        assert result.evidence["correct_start"] == 0
        assert result.score < 1.0

    def test_ac7_exact_end_line_match(self):
        """AC-7 should require exact end line matches."""
        analysis = {
            "files": [
                {
                    "path": "test.py",
                    "functions": [
                        {"name": "func1", "ccn": 1, "start_line": 10, "end_line": 20},
                    ],
                },
            ],
        }
        ground_truth = {
            "files": {
                "test.py": {
                    "functions": {
                        "func1": {"ccn": 1, "start_line": 10, "end_line": 20},
                    },
                },
            },
        }

        result = check_ac7_line_range(analysis, ground_truth)

        assert result.evidence["correct_end"] == 1

    def test_ac7_end_line_mismatch_fails(self):
        """AC-7 should fail when end line doesn't match exactly."""
        analysis = {
            "files": [
                {
                    "path": "test.py",
                    "functions": [
                        {"name": "func1", "ccn": 1, "start_line": 10, "end_line": 21},  # Off by 1
                    ],
                },
            ],
        }
        ground_truth = {
            "files": {
                "test.py": {
                    "functions": {
                        "func1": {"ccn": 1, "start_line": 10, "end_line": 20},
                    },
                },
            },
        }

        result = check_ac7_line_range(analysis, ground_truth)

        assert result.evidence["correct_end"] == 0
        assert result.score < 1.0

    def test_ac7_partial_match_scores_correctly(self):
        """AC-7 should score partial matches (start correct, end incorrect)."""
        analysis = {
            "files": [
                {
                    "path": "test.py",
                    "functions": [
                        {"name": "func1", "ccn": 1, "start_line": 10, "end_line": 25},  # End wrong
                    ],
                },
            ],
        }
        ground_truth = {
            "files": {
                "test.py": {
                    "functions": {
                        "func1": {"ccn": 1, "start_line": 10, "end_line": 20},
                    },
                },
            },
        }

        result = check_ac7_line_range(analysis, ground_truth)

        # Score should be 50% - correct start but incorrect end
        assert result.evidence["correct_start"] == 1
        assert result.evidence["correct_end"] == 0
        assert result.score == 0.5

    def test_ac7_multiple_functions_scoring(self):
        """AC-7 should correctly score multiple functions."""
        analysis = {
            "files": [
                {
                    "path": "test.py",
                    "functions": [
                        {"name": "func1", "ccn": 1, "start_line": 10, "end_line": 20},  # Both correct
                        {"name": "func2", "ccn": 2, "start_line": 30, "end_line": 45},  # Both wrong
                    ],
                },
            ],
        }
        ground_truth = {
            "files": {
                "test.py": {
                    "functions": {
                        "func1": {"ccn": 1, "start_line": 10, "end_line": 20},
                        "func2": {"ccn": 2, "start_line": 25, "end_line": 40},
                    },
                },
            },
        }

        result = check_ac7_line_range(analysis, ground_truth)

        # 1/2 starts correct, 1/2 ends correct = 2/4 = 0.5
        assert result.evidence["total"] == 2
        assert result.evidence["correct_start"] == 1
        assert result.evidence["correct_end"] == 1
        assert result.score == 0.5

    def test_ac7_function_not_found_in_analysis(self):
        """AC-7 should handle when function is not found in analysis."""
        analysis = {
            "files": [
                {
                    "path": "test.py",
                    "functions": [],  # No functions
                },
            ],
        }
        ground_truth = {
            "files": {
                "test.py": {
                    "functions": {
                        "func1": {"ccn": 1, "start_line": 10, "end_line": 20},
                    },
                },
            },
        }

        result = check_ac7_line_range(analysis, ground_truth)

        # Function not found, so no correct lines
        assert result.evidence["correct_start"] == 0
        assert result.evidence["correct_end"] == 0

    def test_ac7_no_line_info_in_ground_truth(self):
        """AC-7 should skip functions without line info in ground truth."""
        analysis = {
            "files": [
                {
                    "path": "test.py",
                    "functions": [
                        {"name": "func1", "ccn": 1, "start_line": 10, "end_line": 20},
                    ],
                },
            ],
        }
        ground_truth = {
            "files": {
                "test.py": {
                    "functions": {
                        "func1": {"ccn": 1},  # No start_line or end_line
                    },
                },
            },
        }

        result = check_ac7_line_range(analysis, ground_truth)

        # No functions to validate
        assert result.evidence["total"] == 0
        assert result.score == 1.0  # Default when nothing to check

    def test_ac7_records_incorrect_ranges(self):
        """AC-7 should record details of incorrect ranges."""
        analysis = {
            "files": [
                {
                    "path": "test.py",
                    "functions": [
                        {"name": "func1", "ccn": 1, "start_line": 15, "end_line": 25},
                    ],
                },
            ],
        }
        ground_truth = {
            "files": {
                "test.py": {
                    "functions": {
                        "func1": {"ccn": 1, "start_line": 10, "end_line": 20},
                    },
                },
            },
        }

        result = check_ac7_line_range(analysis, ground_truth)

        assert "incorrect_ranges" in result.evidence
        incorrect = result.evidence["incorrect_ranges"]
        assert len(incorrect) > 0
        assert incorrect[0]["function"] == "func1"
        assert incorrect[0]["expected_start"] == 10
        assert incorrect[0]["actual_start"] == 15


class TestAC8NestedFunctions:
    """Tests for AC-8: Nested function detection."""

    def test_nested_functions_detected(self, sample_analysis, sample_ground_truth):
        """Test that nested/qualified functions are detected."""
        result = check_ac8_nested_functions(sample_analysis, sample_ground_truth)

        assert result.check_id == "AC-8"
        assert result.category == CheckCategory.ACCURACY
        # Sample analysis has "User.greet" which is a qualified name
        assert result.evidence["qualified_functions_count"] > 0


class TestRunAccuracyChecks:
    """Tests for running all accuracy checks."""

    def test_runs_all_checks(self, sample_analysis, sample_ground_truth):
        """Test that all 8 accuracy checks are run."""
        results = run_accuracy_checks(sample_analysis, sample_ground_truth)

        assert len(results) == 8
        check_ids = [r.check_id for r in results]
        assert "AC-1" in check_ids
        assert "AC-2" in check_ids
        assert "AC-3" in check_ids
        assert "AC-4" in check_ids
        assert "AC-5" in check_ids
        assert "AC-6" in check_ids
        assert "AC-7" in check_ids
        assert "AC-8" in check_ids
