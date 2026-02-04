"""Unit tests for edge case checks (EC-1 to EC-8)."""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks import CheckCategory
from checks.edge_cases import (
    run_edge_case_checks,
    _ec1_empty_files,
    _ec2_single_line_files,
    _ec3_large_files,
    _ec4_unicode_content,
    _ec5_mixed_line_endings,
    _ec6_deeply_nested_code,
    _ec7_special_characters_paths,
    _ec8_no_duplicates_repository,
)


@pytest.fixture
def clean_analysis():
    """Analysis with no errors or issues."""
    return {
        "metadata": {"version": "1.0", "elapsed_seconds": 15.0},
        "summary": {"total_clones": 5, "duplication_percentage": 15.0},
        "files": [
            {"path": "main.py", "total_lines": 100, "duplicate_lines": 15},
            {"path": "utils.py", "total_lines": 50, "duplicate_lines": 5},
        ],
        "duplications": [
            {"clone_id": "CPD-0001", "lines": 10, "tokens": 50, "occurrences": [
                {"file": "main.py"},
                {"file": "utils.py"},
            ]},
        ],
        "errors": [],
    }


@pytest.fixture
def analysis_with_errors():
    """Analysis with various errors."""
    return {
        "metadata": {"version": "1.0", "elapsed_seconds": 30.0},
        "summary": {"total_clones": 0, "duplication_percentage": 0.0},
        "files": [],
        "duplications": [],
        "errors": [
            "Error processing empty file: empty.py",
            "Unicode decode error in unicode_file.py",
            "Path not found: path/with/issues",
            "CRLF line ending issue detected",
        ],
    }


@pytest.fixture
def large_file_analysis():
    """Analysis with large files."""
    return {
        "metadata": {"version": "1.0", "elapsed_seconds": 120.0},
        "summary": {"total_clones": 10, "duplication_percentage": 20.0},
        "files": [
            {"path": "small.py", "total_lines": 50, "duplicate_lines": 5},
            {"path": "medium.py", "total_lines": 500, "duplicate_lines": 50},
            {"path": "large.py", "total_lines": 2000, "duplicate_lines": 200},
            {"path": "huge.py", "total_lines": 5000, "duplicate_lines": 500},
        ],
        "duplications": [],
        "errors": [],
    }


@pytest.fixture
def single_line_file_analysis():
    """Analysis with single-line files."""
    return {
        "metadata": {"version": "1.0"},
        "files": [
            {"path": "normal.py", "total_lines": 100, "duplicate_lines": 10},
            {"path": "single.py", "total_lines": 1, "duplicate_lines": 0},
            {"path": "empty.py", "total_lines": 0, "duplicate_lines": 0},
        ],
        "duplications": [],
        "errors": [],
    }


@pytest.fixture
def no_dup_ground_truth():
    """Ground truth with clean files."""
    return {
        "python": {
            "language": "python",
            "files": {
                "no_dup.py": {"expected_clone_count": 0},
                "clean.py": {"expected_clone_count": 0},
            },
        },
    }


class TestEC1EmptyFiles:
    """Tests for EC-1: Empty file handling."""

    def test_no_empty_file_errors(self, clean_analysis):
        """Test when no empty file errors occur."""
        result = _ec1_empty_files(clean_analysis)

        assert result.check_id == "EC-1"
        assert result.name == "Empty file handling"
        assert result.category == CheckCategory.EDGE_CASES
        assert result.passed is True
        assert result.score == 1.0

    def test_empty_file_errors_present(self, analysis_with_errors):
        """Test when empty file errors occur."""
        result = _ec1_empty_files(analysis_with_errors)

        assert result.passed is False
        assert result.score == 0.0
        assert len(result.evidence.get("errors", [])) > 0

    def test_missing_errors_key(self):
        """Test when errors key is missing."""
        analysis = {"metadata": {}, "files": []}
        result = _ec1_empty_files(analysis)

        assert result.passed is True


class TestEC2SingleLineFiles:
    """Tests for EC-2: Single-line file handling."""

    def test_no_single_line_issues(self, clean_analysis):
        """Test when single-line files are handled correctly."""
        result = _ec2_single_line_files(clean_analysis)

        assert result.check_id == "EC-2"
        assert result.name == "Single-line file handling"
        assert result.category == CheckCategory.EDGE_CASES
        assert result.passed is True
        assert result.score == 1.0

    def test_single_line_files_no_duplicates(self, single_line_file_analysis):
        """Test single-line files without false duplicates."""
        result = _ec2_single_line_files(single_line_file_analysis)

        assert result.passed is True

    def test_single_line_file_with_duplicates(self):
        """Test single-line file reporting duplicates (false positive)."""
        analysis = {
            "files": [
                {"path": "single.py", "total_lines": 1, "duplicate_lines": 1},
            ],
        }
        result = _ec2_single_line_files(analysis)

        assert result.passed is False
        assert len(result.evidence.get("issues", [])) > 0

    def test_empty_files_list(self):
        """Test with empty files list."""
        analysis = {"files": []}
        result = _ec2_single_line_files(analysis)

        assert result.passed is True


class TestEC3LargeFiles:
    """Tests for EC-3: Large file handling."""

    def test_large_files_processed_quickly(self, large_file_analysis):
        """Test large files processed within timeout."""
        result = _ec3_large_files(large_file_analysis)

        assert result.check_id == "EC-3"
        assert result.name == "Large file handling"
        assert result.category == CheckCategory.EDGE_CASES
        assert result.passed is True  # 120s < 600s timeout

    def test_analysis_timed_out(self):
        """Test analysis exceeding timeout."""
        analysis = {
            "metadata": {"elapsed_seconds": 700.0},  # > 600s timeout
            "files": [{"path": "huge.py", "total_lines": 10000}],
        }
        result = _ec3_large_files(analysis)

        assert result.passed is False
        assert result.score == 0.5

    def test_large_file_detection(self, large_file_analysis):
        """Test that large files are detected in evidence."""
        result = _ec3_large_files(large_file_analysis)

        # Files > 1000 lines are considered large
        assert result.evidence.get("large_file_count", 0) >= 2

    def test_no_metadata_elapsed(self):
        """Test when elapsed_seconds is missing."""
        analysis = {"metadata": {}, "files": []}
        result = _ec3_large_files(analysis)

        assert result.passed is True  # 0 < 600s


class TestEC4UnicodeContent:
    """Tests for EC-4: Unicode content handling."""

    def test_no_unicode_errors(self, clean_analysis):
        """Test when no unicode errors occur."""
        result = _ec4_unicode_content(clean_analysis)

        assert result.check_id == "EC-4"
        assert result.name == "Unicode content handling"
        assert result.category == CheckCategory.EDGE_CASES
        assert result.passed is True
        assert result.score == 1.0

    def test_unicode_errors_present(self, analysis_with_errors):
        """Test when unicode errors occur."""
        result = _ec4_unicode_content(analysis_with_errors)

        assert result.passed is False
        assert result.score == 0.5
        assert len(result.evidence.get("encoding_errors", [])) > 0

    def test_various_encoding_error_keywords(self):
        """Test detection of various encoding-related errors."""
        analysis = {
            "errors": [
                "UTF-8 decoding failed",
                "Codec error in file.py",
                "Encoding issue detected",
            ],
        }
        result = _ec4_unicode_content(analysis)

        assert result.passed is False
        assert len(result.evidence.get("encoding_errors", [])) == 3


class TestEC5MixedLineEndings:
    """Tests for EC-5: Mixed line endings handling."""

    def test_no_line_ending_errors(self, clean_analysis):
        """Test when no line ending errors occur."""
        result = _ec5_mixed_line_endings(clean_analysis)

        assert result.check_id == "EC-5"
        assert result.name == "Mixed line endings handling"
        assert result.category == CheckCategory.EDGE_CASES
        assert result.passed is True

    def test_line_ending_errors_present(self, analysis_with_errors):
        """Test when line ending errors occur."""
        result = _ec5_mixed_line_endings(analysis_with_errors)

        assert result.passed is False
        assert len(result.evidence.get("errors", [])) > 0

    def test_crlf_detection(self):
        """Test CRLF-related error detection."""
        analysis = {
            "errors": ["CRLF to LF conversion failed"],
        }
        result = _ec5_mixed_line_endings(analysis)

        assert result.passed is False


class TestEC6DeeplyNestedCode:
    """Tests for EC-6: Deeply nested code handling."""

    def test_analysis_completed(self, clean_analysis):
        """Test that analysis completed without crashes."""
        result = _ec6_deeply_nested_code(clean_analysis)

        assert result.check_id == "EC-6"
        assert result.name == "Deeply nested code handling"
        assert result.category == CheckCategory.EDGE_CASES
        assert result.passed is True
        assert result.score == 1.0

    def test_clone_count_in_evidence(self, clean_analysis):
        """Test that clone count is in evidence."""
        result = _ec6_deeply_nested_code(clean_analysis)

        assert "total_clones" in result.evidence

    def test_no_duplications(self):
        """Test with no duplications."""
        analysis = {"duplications": []}
        result = _ec6_deeply_nested_code(analysis)

        assert result.passed is True
        assert result.evidence.get("total_clones") == 0


class TestEC7SpecialCharactersPaths:
    """Tests for EC-7: Special character paths handling."""

    def test_no_path_errors(self, clean_analysis):
        """Test when no path errors occur."""
        result = _ec7_special_characters_paths(clean_analysis)

        assert result.check_id == "EC-7"
        assert result.name == "Special character paths handling"
        assert result.category == CheckCategory.EDGE_CASES
        assert result.passed is True
        assert result.score == 1.0

    def test_path_errors_present(self, analysis_with_errors):
        """Test when path errors occur."""
        result = _ec7_special_characters_paths(analysis_with_errors)

        assert result.passed is False
        assert len(result.evidence.get("path_errors", [])) > 0

    def test_filename_error_detection(self):
        """Test filename-related error detection."""
        analysis = {
            "files": [],
            "errors": ["Invalid filename: test[1].py"],
        }
        result = _ec7_special_characters_paths(analysis)

        assert result.passed is False


class TestEC8NoDuplicatesRepository:
    """Tests for EC-8: Zero duplication handling."""

    def test_low_duplication(self, no_dup_ground_truth):
        """Test repository with low duplication."""
        analysis = {
            "summary": {"total_clones": 2, "duplication_percentage": 5.0},
        }
        result = _ec8_no_duplicates_repository(analysis, no_dup_ground_truth)

        assert result.check_id == "EC-8"
        assert result.name == "Zero duplication handling"
        assert result.category == CheckCategory.EDGE_CASES
        assert result.passed is True

    def test_high_duplication(self, no_dup_ground_truth):
        """Test repository with high duplication."""
        analysis = {
            "summary": {"total_clones": 50, "duplication_percentage": 60.0},
        }
        result = _ec8_no_duplicates_repository(analysis, no_dup_ground_truth)

        assert result.passed is False  # > 50% threshold

    def test_no_clean_files_in_ground_truth(self):
        """Test when no clean files in ground truth."""
        gt = {"python": {"files": {"heavy.py": {"expected_clone_range": [5, 10]}}}}
        analysis = {
            "summary": {"total_clones": 100, "duplication_percentage": 80.0},
        }
        result = _ec8_no_duplicates_repository(analysis, gt)

        assert result.passed is True  # No clean files to test
        assert result.score == 1.0

    def test_evidence_includes_stats(self, no_dup_ground_truth):
        """Test that evidence includes statistics."""
        analysis = {
            "summary": {"total_clones": 5, "duplication_percentage": 10.0},
        }
        result = _ec8_no_duplicates_repository(analysis, no_dup_ground_truth)

        assert "total_clones" in result.evidence
        assert "duplication_percentage" in result.evidence
        assert "clean_files_in_gt" in result.evidence


class TestRunEdgeCaseChecks:
    """Tests for the run_edge_case_checks aggregator function."""

    def test_runs_all_checks(self, clean_analysis, tmp_path):
        """Test that all 8 edge case checks are run."""
        # Create mock ground truth file
        gt_dir = tmp_path / "ground-truth"
        gt_dir.mkdir()
        gt_file = gt_dir / "python.json"
        import json
        gt_file.write_text(json.dumps({
            "language": "python",
            "files": {"test.py": {}},
        }))

        results = run_edge_case_checks(clean_analysis, str(gt_dir))

        assert len(results) == 8
        check_ids = [r.check_id for r in results]
        assert "EC-1" in check_ids
        assert "EC-2" in check_ids
        assert "EC-3" in check_ids
        assert "EC-4" in check_ids
        assert "EC-5" in check_ids
        assert "EC-6" in check_ids
        assert "EC-7" in check_ids
        assert "EC-8" in check_ids

    def test_all_checks_have_correct_category(self, clean_analysis, tmp_path):
        """Test that all checks are categorized as EDGE_CASES."""
        gt_dir = tmp_path / "ground-truth"
        gt_dir.mkdir()
        gt_file = gt_dir / "python.json"
        import json
        gt_file.write_text(json.dumps({"language": "python", "files": {}}))

        results = run_edge_case_checks(clean_analysis, str(gt_dir))

        for result in results:
            assert result.category == CheckCategory.EDGE_CASES
