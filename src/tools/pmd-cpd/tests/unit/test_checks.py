"""Unit tests for PMD CPD evaluation checks."""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks import (
    CheckResult,
    CheckCategory,
    EvaluationReport,
    normalize_path,
    get_language_from_path,
    get_file_from_analysis,
)


class TestCheckResult:
    """Test CheckResult dataclass."""

    def test_check_result_creation(self):
        """Test basic CheckResult creation."""
        result = CheckResult(
            check_id="AC-1",
            name="Heavy duplication detection",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=0.85,
            message="Test passed",
            evidence={"detected": 5}
        )

        assert result.check_id == "AC-1"
        assert result.name == "Heavy duplication detection"
        assert result.category == CheckCategory.ACCURACY
        assert result.passed is True
        assert result.score == 0.85
        assert result.evidence == {"detected": 5}

    def test_check_result_to_dict(self):
        """Test CheckResult serialization."""
        result = CheckResult(
            check_id="AC-1",
            name="Test Check",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0,
            message="All good",
        )

        d = result.to_dict()
        assert d["check_id"] == "AC-1"
        assert d["category"] == "accuracy"
        assert d["passed"] is True


class TestEvaluationReport:
    """Test EvaluationReport dataclass."""

    def test_report_score_calculation(self):
        """Test overall score calculation."""
        checks = [
            CheckResult("AC-1", "Test 1", CheckCategory.ACCURACY, True, 1.0, ""),
            CheckResult("AC-2", "Test 2", CheckCategory.ACCURACY, False, 0.5, ""),
            CheckResult("CV-1", "Test 3", CheckCategory.COVERAGE, True, 0.75, ""),
        ]

        report = EvaluationReport(
            timestamp="2025-01-20T10:00:00",
            analysis_path="test.json",
            ground_truth_dir="gt/",
            checks=checks,
        )

        assert report.passed == 2
        assert report.failed == 1
        assert report.total == 3
        assert report.score == pytest.approx(0.75, rel=0.01)

    def test_report_score_by_category(self):
        """Test score breakdown by category."""
        checks = [
            CheckResult("AC-1", "Test 1", CheckCategory.ACCURACY, True, 1.0, ""),
            CheckResult("AC-2", "Test 2", CheckCategory.ACCURACY, False, 0.5, ""),
            CheckResult("CV-1", "Test 3", CheckCategory.COVERAGE, True, 1.0, ""),
        ]

        report = EvaluationReport(
            timestamp="2025-01-20T10:00:00",
            analysis_path="test.json",
            ground_truth_dir="gt/",
            checks=checks,
        )

        scores = report.score_by_category
        assert scores["accuracy"] == pytest.approx(0.75, rel=0.01)
        assert scores["coverage"] == pytest.approx(1.0, rel=0.01)

    def test_empty_report(self):
        """Test report with no checks."""
        report = EvaluationReport(
            timestamp="2025-01-20T10:00:00",
            analysis_path="test.json",
            ground_truth_dir="gt/",
            checks=[],
        )

        assert report.score == 0.0
        assert report.passed == 0


class TestNormalizePath:
    """Test path normalization utilities."""

    def test_normalize_path_with_leading_dot_slash(self):
        """Test removing leading ./ from paths."""
        assert normalize_path("./src/file.py") == "src/file.py"

    def test_normalize_path_with_leading_slash(self):
        """Test removing leading / from paths."""
        assert normalize_path("/src/file.py") == "src/file.py"

    def test_normalize_path_backslash(self):
        """Test converting backslashes to forward slashes."""
        assert normalize_path("src\\file.py") == "src/file.py"

    def test_normalize_path_clean(self):
        """Test path that doesn't need normalization."""
        assert normalize_path("src/file.py") == "src/file.py"


class TestGetLanguageFromPath:
    """Test language detection from file paths."""

    def test_python_detection(self):
        """Test Python file detection."""
        assert get_language_from_path("src/main.py") == "python"

    def test_javascript_detection(self):
        """Test JavaScript file detection."""
        assert get_language_from_path("src/app.js") == "javascript"
        assert get_language_from_path("src/component.jsx") == "javascript"

    def test_typescript_detection(self):
        """Test TypeScript file detection."""
        assert get_language_from_path("src/app.ts") == "typescript"
        assert get_language_from_path("src/component.tsx") == "typescript"

    def test_csharp_detection(self):
        """Test C# file detection."""
        assert get_language_from_path("src/Program.cs") == "csharp"

    def test_java_detection(self):
        """Test Java file detection."""
        assert get_language_from_path("src/Main.java") == "java"

    def test_go_detection(self):
        """Test Go file detection."""
        assert get_language_from_path("src/main.go") == "go"

    def test_rust_detection(self):
        """Test Rust file detection."""
        assert get_language_from_path("src/main.rs") == "rust"

    def test_unknown_extension(self):
        """Test unknown file extension."""
        assert get_language_from_path("src/file.xyz") == "unknown"


class TestGetFileFromAnalysis:
    """Test file lookup in analysis data."""

    def test_find_file_exact_match(self):
        """Test finding file with exact path match."""
        analysis = {
            "files": [
                {"path": "src/main.py", "duplicate_lines": 10},
                {"path": "src/utils.py", "duplicate_lines": 5},
            ]
        }

        result = get_file_from_analysis(analysis, "src/main.py")
        assert result is not None
        assert result["duplicate_lines"] == 10

    def test_find_file_suffix_match(self):
        """Test finding file with path suffix match."""
        analysis = {
            "files": [
                {"path": "project/src/main.py", "duplicate_lines": 10},
            ]
        }

        result = get_file_from_analysis(analysis, "src/main.py")
        assert result is not None
        assert result["duplicate_lines"] == 10

    def test_file_not_found(self):
        """Test file not found returns None."""
        analysis = {
            "files": [
                {"path": "src/main.py", "duplicate_lines": 10},
            ]
        }

        result = get_file_from_analysis(analysis, "src/other.py")
        assert result is None

    def test_empty_files_list(self):
        """Test empty files list returns None."""
        analysis = {"files": []}
        result = get_file_from_analysis(analysis, "src/main.py")
        assert result is None
