"""Unit tests for coverage checks (CV-1 to CV-8)."""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks import CheckCategory
from checks.coverage import (
    run_coverage_checks,
    _check_language_coverage,
    _cv1_python_coverage,
    _cv2_javascript_coverage,
    _cv3_typescript_coverage,
    _cv4_csharp_coverage,
    _cv5_java_coverage,
    _cv6_go_coverage,
    _cv7_rust_coverage,
    _cv8_multi_language_detection,
)


@pytest.fixture
def multi_language_analysis():
    """Analysis with multiple languages."""
    return {
        "metadata": {"version": "1.0"},
        "files": [
            {"path": "python/main.py", "language": "python", "duplicate_blocks": 2},
            {"path": "python/utils.py", "language": "python", "duplicate_blocks": 1},
            {"path": "javascript/app.js", "language": "ecmascript", "duplicate_blocks": 3},
            {"path": "typescript/index.ts", "language": "typescript", "duplicate_blocks": 1},
            {"path": "csharp/Program.cs", "language": "cs", "duplicate_blocks": 2},
            {"path": "java/Main.java", "language": "java", "duplicate_blocks": 1},
            {"path": "go/main.go", "language": "go", "duplicate_blocks": 0},
            {"path": "rust/main.rs", "language": "rust", "duplicate_blocks": 1},
        ],
        "duplications": [],
    }


@pytest.fixture
def python_only_analysis():
    """Analysis with only Python files."""
    return {
        "metadata": {"version": "1.0"},
        "files": [
            {"path": "python/main.py", "language": "python", "duplicate_blocks": 2},
            {"path": "python/utils.py", "language": "python", "duplicate_blocks": 1},
            {"path": "python/test.py", "language": "python", "duplicate_blocks": 0},
        ],
        "duplications": [],
    }


@pytest.fixture
def multi_language_ground_truth():
    """Ground truth with multiple languages."""
    return {
        "python": {
            "language": "python",
            "files": {
                "python/main.py": {"expected_clone_range": [1, 5]},
                "python/utils.py": {"expected_clone_range": [0, 3]},
            },
        },
        "javascript": {
            "language": "javascript",
            "files": {
                "javascript/app.js": {"expected_clone_range": [2, 5]},
            },
        },
        "typescript": {
            "language": "typescript",
            "files": {
                "typescript/index.ts": {"expected_clone_range": [0, 3]},
            },
        },
        "csharp": {
            "language": "csharp",
            "files": {
                "csharp/Program.cs": {"expected_clone_range": [1, 4]},
            },
        },
        "java": {
            "language": "java",
            "files": {
                "java/Main.java": {"expected_clone_range": [0, 3]},
            },
        },
        "go": {
            "language": "go",
            "files": {
                "go/main.go": {"expected_clone_range": [0, 2]},
            },
        },
        "rust": {
            "language": "rust",
            "files": {
                "rust/main.rs": {"expected_clone_range": [0, 3]},
            },
        },
    }


class TestCheckLanguageCoverage:
    """Tests for the generic language coverage check function."""

    def test_full_coverage(self, multi_language_analysis, multi_language_ground_truth):
        """Test when all expected files are found."""
        result = _check_language_coverage(
            multi_language_analysis,
            multi_language_ground_truth,
            "python",
            "TEST-1",
            "Test coverage",
        )

        assert result.check_id == "TEST-1"
        assert result.category == CheckCategory.COVERAGE
        assert result.passed is True
        assert result.score == 1.0

    def test_partial_coverage(self, multi_language_ground_truth):
        """Test when only some expected files are found."""
        analysis = {
            "files": [
                {"path": "python/main.py", "language": "python"},
                # Missing python/utils.py
            ],
        }
        result = _check_language_coverage(
            analysis,
            multi_language_ground_truth,
            "python",
            "TEST-1",
            "Test coverage",
        )

        assert result.score == 0.5  # 1 of 2 files found
        assert result.passed is False  # Below 80% threshold

    def test_no_files_in_ground_truth(self, multi_language_analysis):
        """Test when language has no files in ground truth."""
        gt = {"python": {"files": {}}}
        result = _check_language_coverage(
            multi_language_analysis,
            gt,
            "python",
            "TEST-1",
            "Test coverage",
        )

        assert result.passed is True
        assert result.score == 1.0

    def test_language_not_in_ground_truth(self, multi_language_analysis):
        """Test when language is not in ground truth at all."""
        gt = {}
        result = _check_language_coverage(
            multi_language_analysis,
            gt,
            "python",
            "TEST-1",
            "Test coverage",
        )

        assert result.passed is True
        assert result.score == 1.0


class TestCV1PythonCoverage:
    """Tests for CV-1: Python file coverage."""

    def test_python_files_covered(self, multi_language_analysis, multi_language_ground_truth):
        """Test Python files are found."""
        result = _cv1_python_coverage(multi_language_analysis, multi_language_ground_truth)

        assert result.check_id == "CV-1"
        assert result.name == "Python file coverage"
        assert result.category == CheckCategory.COVERAGE
        assert result.passed is True

    def test_missing_python_files(self, multi_language_ground_truth):
        """Test when Python files are missing."""
        analysis = {"files": []}
        result = _cv1_python_coverage(analysis, multi_language_ground_truth)

        assert result.passed is False
        assert result.score == 0.0


class TestCV2JavaScriptCoverage:
    """Tests for CV-2: JavaScript file coverage."""

    def test_javascript_files_covered(self, multi_language_analysis, multi_language_ground_truth):
        """Test JavaScript files are found."""
        result = _cv2_javascript_coverage(multi_language_analysis, multi_language_ground_truth)

        assert result.check_id == "CV-2"
        assert result.name == "JavaScript file coverage"
        assert result.passed is True

    def test_no_javascript_in_ground_truth(self, multi_language_analysis):
        """Test when no JavaScript in ground truth."""
        gt = {"python": {"files": {}}}
        result = _cv2_javascript_coverage(multi_language_analysis, gt)

        assert result.passed is True
        assert result.score == 1.0


class TestCV3TypeScriptCoverage:
    """Tests for CV-3: TypeScript file coverage."""

    def test_typescript_files_covered(self, multi_language_analysis, multi_language_ground_truth):
        """Test TypeScript files are found."""
        result = _cv3_typescript_coverage(multi_language_analysis, multi_language_ground_truth)

        assert result.check_id == "CV-3"
        assert result.name == "TypeScript file coverage"
        assert result.passed is True


class TestCV4CSharpCoverage:
    """Tests for CV-4: C# file coverage."""

    def test_csharp_files_covered(self, multi_language_analysis, multi_language_ground_truth):
        """Test C# files are found."""
        result = _cv4_csharp_coverage(multi_language_analysis, multi_language_ground_truth)

        assert result.check_id == "CV-4"
        assert result.name == "C# file coverage"
        assert result.passed is True


class TestCV5JavaCoverage:
    """Tests for CV-5: Java file coverage."""

    def test_java_files_covered(self, multi_language_analysis, multi_language_ground_truth):
        """Test Java files are found."""
        result = _cv5_java_coverage(multi_language_analysis, multi_language_ground_truth)

        assert result.check_id == "CV-5"
        assert result.name == "Java file coverage"
        assert result.passed is True


class TestCV6GoCoverage:
    """Tests for CV-6: Go file coverage."""

    def test_go_files_covered(self, multi_language_analysis, multi_language_ground_truth):
        """Test Go files are found."""
        result = _cv6_go_coverage(multi_language_analysis, multi_language_ground_truth)

        assert result.check_id == "CV-6"
        assert result.name == "Go file coverage"
        assert result.passed is True


class TestCV7RustCoverage:
    """Tests for CV-7: Rust file coverage."""

    def test_rust_files_covered(self, multi_language_analysis, multi_language_ground_truth):
        """Test Rust files are found."""
        result = _cv7_rust_coverage(multi_language_analysis, multi_language_ground_truth)

        assert result.check_id == "CV-7"
        assert result.name == "Rust file coverage"
        assert result.passed is True


class TestCV8MultiLanguageDetection:
    """Tests for CV-8: Multi-language detection."""

    def test_all_languages_detected(self, multi_language_analysis, multi_language_ground_truth):
        """Test all expected languages are detected."""
        result = _cv8_multi_language_detection(multi_language_analysis, multi_language_ground_truth)

        assert result.check_id == "CV-8"
        assert result.name == "Multi-language detection"
        assert result.category == CheckCategory.COVERAGE
        assert result.passed is True

    def test_partial_language_detection(self, python_only_analysis, multi_language_ground_truth):
        """Test when only some languages are detected."""
        result = _cv8_multi_language_detection(python_only_analysis, multi_language_ground_truth)

        # Only Python detected out of 7 expected languages
        assert result.score < 1.0
        assert "missing" in result.evidence

    def test_no_languages_in_ground_truth(self, multi_language_analysis):
        """Test when no languages in ground truth."""
        gt = {}
        result = _cv8_multi_language_detection(multi_language_analysis, gt)

        assert result.passed is True
        assert result.score == 1.0

    def test_language_name_mapping(self):
        """Test that CPD language names are mapped correctly."""
        analysis = {
            "files": [
                {"path": "app.js", "language": "ecmascript"},  # CPD uses ecmascript
                {"path": "Program.cs", "language": "cs"},  # CPD uses cs
            ],
        }
        gt = {
            "javascript": {"language": "javascript", "files": {}},
            "csharp": {"language": "csharp", "files": {}},
        }
        result = _cv8_multi_language_detection(analysis, gt)

        # ecmascript should map to javascript, cs should map to csharp
        assert result.passed is True
        assert "javascript" in result.evidence.get("covered", [])
        assert "csharp" in result.evidence.get("covered", [])


class TestRunCoverageChecks:
    """Tests for the run_coverage_checks aggregator function."""

    def test_runs_all_checks(self, multi_language_analysis, tmp_path):
        """Test that all 8 coverage checks are run."""
        # Create mock ground truth file
        gt_dir = tmp_path / "ground-truth"
        gt_dir.mkdir()
        gt_file = gt_dir / "python.json"
        import json
        gt_file.write_text(json.dumps({
            "language": "python",
            "files": {"main.py": {}},
        }))

        results = run_coverage_checks(multi_language_analysis, str(gt_dir))

        assert len(results) == 8
        check_ids = [r.check_id for r in results]
        assert "CV-1" in check_ids
        assert "CV-2" in check_ids
        assert "CV-3" in check_ids
        assert "CV-4" in check_ids
        assert "CV-5" in check_ids
        assert "CV-6" in check_ids
        assert "CV-7" in check_ids
        assert "CV-8" in check_ids

    def test_all_checks_have_correct_category(self, multi_language_analysis, tmp_path):
        """Test that all checks are categorized as COVERAGE."""
        gt_dir = tmp_path / "ground-truth"
        gt_dir.mkdir()
        gt_file = gt_dir / "python.json"
        import json
        gt_file.write_text(json.dumps({"language": "python", "files": {}}))

        results = run_coverage_checks(multi_language_analysis, str(gt_dir))

        for result in results:
            assert result.category == CheckCategory.COVERAGE
