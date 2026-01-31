"""Tests for coverage checks (CV-1 to CV-8)."""

import pytest

from scripts.checks import CheckCategory, CheckSeverity
from scripts.checks.coverage import (
    check_cv1_python_detected,
    check_cv2_csharp_detected,
    check_cv3_java_detected,
    check_cv4_javascript_detected,
    check_cv5_typescript_detected,
    check_cv6_go_detected,
    check_cv7_rust_detected,
    check_cv8_all_languages_in_summary,
    run_coverage_checks,
)


class TestLanguageDetection:
    """Tests for individual language detection checks."""

    def test_python_detected(self, sample_analysis):
        """CV-1: Python should be detected."""
        result = check_cv1_python_detected(sample_analysis)

        assert result.check_id == "CV-1"
        assert result.category == CheckCategory.COVERAGE
        assert result.passed
        assert result.evidence["files_found"] > 0

    def test_csharp_detected(self, sample_analysis):
        """CV-2: C# should be detected."""
        result = check_cv2_csharp_detected(sample_analysis)

        assert result.check_id == "CV-2"
        assert result.passed

    def test_java_not_in_sample(self, sample_analysis):
        """CV-3: Java not in minimal sample analysis."""
        result = check_cv3_java_detected(sample_analysis)

        assert result.check_id == "CV-3"
        # Java not in our minimal sample
        assert not result.passed

    def test_java_detected_in_full_analysis(self, multi_language_analysis):
        """CV-3: Java detected in full analysis."""
        result = check_cv3_java_detected(multi_language_analysis)

        assert result.passed
        assert result.evidence["functions_found"] > 0

    def test_javascript_detected(self, multi_language_analysis):
        """CV-4: JavaScript detected in full analysis."""
        result = check_cv4_javascript_detected(multi_language_analysis)

        assert result.check_id == "CV-4"
        assert result.passed

    def test_typescript_detected(self, multi_language_analysis):
        """CV-5: TypeScript detected in full analysis."""
        result = check_cv5_typescript_detected(multi_language_analysis)

        assert result.check_id == "CV-5"
        assert result.passed

    def test_go_detected(self, multi_language_analysis):
        """CV-6: Go detected in full analysis."""
        result = check_cv6_go_detected(multi_language_analysis)

        assert result.check_id == "CV-6"
        assert result.passed

    def test_rust_detected(self, multi_language_analysis):
        """CV-7: Rust detected in full analysis."""
        result = check_cv7_rust_detected(multi_language_analysis)

        assert result.check_id == "CV-7"
        assert result.passed


class TestAllLanguagesCheck:
    """Tests for CV-8: All languages in summary."""

    def test_partial_languages(self, sample_analysis):
        """Test with only some languages present."""
        result = check_cv8_all_languages_in_summary(sample_analysis)

        assert result.check_id == "CV-8"
        assert result.category == CheckCategory.COVERAGE
        assert result.severity == CheckSeverity.CRITICAL
        # Only Python and C# in minimal sample
        assert result.score < 1.0
        assert len(result.evidence["missing_languages"]) > 0

    def test_all_languages_present(self, multi_language_analysis):
        """Test with all 7 languages present."""
        result = check_cv8_all_languages_in_summary(multi_language_analysis)

        assert result.score == 1.0
        assert len(result.evidence["missing_languages"]) == 0
        assert len(result.evidence["detected_languages"]) == 7


class TestRunCoverageChecks:
    """Tests for running all coverage checks."""

    def test_runs_all_checks(self, sample_analysis):
        """Test that all 8 coverage checks are run."""
        results = run_coverage_checks(sample_analysis)

        assert len(results) == 8
        check_ids = [r.check_id for r in results]
        assert all(f"CV-{i}" in check_ids for i in range(1, 9))

    def test_all_checks_have_correct_category(self, sample_analysis):
        """Test that all checks are categorized as COVERAGE."""
        results = run_coverage_checks(sample_analysis)

        for result in results:
            assert result.category == CheckCategory.COVERAGE
