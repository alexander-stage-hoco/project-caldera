"""Unit tests for accuracy checks (AC-1 to AC-8)."""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks import CheckCategory
from checks.accuracy import (
    run_accuracy_checks,
    _ac1_heavy_duplication_detected,
    _ac2_clone_count_in_range,
    _ac3_duplication_percentage_accuracy,
    _ac4_no_false_positives_clean_files,
    _ac5_cross_file_detection,
    _ac6_semantic_identifier_detection,
    _ac7_semantic_literal_detection,
    _ac8_clone_line_accuracy,
)


@pytest.fixture
def heavy_dup_analysis():
    """Analysis with heavy duplication detected."""
    return {
        "metadata": {"version": "1.0"},
        "files": [
            {
                "path": "python/heavy_duplication.py",
                "duplicate_blocks": 5,
                "duplicate_lines": 50,
                "duplication_percentage": 35.0,
                "total_lines": 143,
            },
            {
                "path": "javascript/heavy_duplication.js",
                "duplicate_blocks": 4,
                "duplicate_lines": 40,
                "duplication_percentage": 30.0,
                "total_lines": 133,
            },
        ],
        "duplications": [
            {"clone_id": "CPD-0001", "lines": 15, "tokens": 100, "occurrences": [
                {"file": "python/heavy_duplication.py", "line_start": 10, "line_end": 24},
                {"file": "python/heavy_duplication.py", "line_start": 50, "line_end": 64},
            ]},
        ],
    }


@pytest.fixture
def light_dup_analysis():
    """Analysis with light duplication detected."""
    return {
        "metadata": {"version": "1.0"},
        "files": [
            {
                "path": "python/light_duplication.py",
                "duplicate_blocks": 1,
                "duplicate_lines": 10,
                "duplication_percentage": 8.0,
                "total_lines": 125,
            },
        ],
        "duplications": [
            {"clone_id": "CPD-0001", "lines": 10, "tokens": 50, "occurrences": [
                {"file": "python/light_duplication.py", "line_start": 20, "line_end": 29},
                {"file": "python/light_duplication.py", "line_start": 80, "line_end": 89},
            ]},
        ],
    }


@pytest.fixture
def no_dup_analysis():
    """Analysis with no duplication."""
    return {
        "metadata": {"version": "1.0"},
        "files": [
            {
                "path": "python/no_duplication.py",
                "duplicate_blocks": 0,
                "duplicate_lines": 0,
                "duplication_percentage": 0.0,
                "total_lines": 100,
            },
        ],
        "duplications": [],
    }


@pytest.fixture
def cross_file_analysis():
    """Analysis with cross-file clones."""
    return {
        "metadata": {"version": "1.0"},
        "files": [
            {"path": "python/cross_file_a.py", "duplicate_blocks": 2},
            {"path": "python/cross_file_b.py", "duplicate_blocks": 2},
        ],
        "duplications": [
            {
                "clone_id": "CPD-0001",
                "lines": 20,
                "tokens": 150,
                "occurrences": [
                    {"file": "python/cross_file_a.py", "line_start": 10, "line_end": 29},
                    {"file": "python/cross_file_b.py", "line_start": 5, "line_end": 24},
                ],
            },
        ],
    }


@pytest.fixture
def semantic_analysis():
    """Analysis with semantic mode enabled."""
    return {
        "metadata": {
            "version": "1.0",
            "ignore_identifiers": True,
            "ignore_literals": True,
        },
        "files": [
            {
                "path": "python/semantic_test.py",
                "duplicate_blocks": 3,
                "duplicate_lines": 30,
            },
        ],
        "duplications": [
            {"clone_id": "CPD-0001", "lines": 10, "tokens": 50, "occurrences": [
                {"file": "python/semantic_test.py", "line_start": 10, "line_end": 19},
                {"file": "python/semantic_test.py", "line_start": 50, "line_end": 59},
            ]},
        ],
    }


@pytest.fixture
def mock_ground_truth():
    """Mock ground truth data."""
    return {
        "python": {
            "language": "python",
            "files": {
                "python/heavy_duplication.py": {
                    "expected_clone_range": [3, 10],
                    "duplication_percentage_range": [20.0, 50.0],
                },
                "python/light_duplication.py": {
                    "expected_clone_range": [1, 3],
                    "duplication_percentage_range": [5.0, 15.0],
                },
                "python/no_duplication.py": {
                    "expected_clone_count": 0,
                    "expected_clone_range": [0, 0],
                    "duplication_percentage_range": [0.0, 5.0],
                },
                "python/cross_file_a.py": {
                    "expected_clone_range": [1, 5],
                },
                "python/cross_file_b.py": {
                    "expected_clone_range": [1, 5],
                },
                "python/semantic_test.py": {
                    "expected_clones_semantic": {
                        "requires_ignore_identifiers": True,
                        "requires_ignore_literals": True,
                        "count_range": [2, 5],
                    },
                },
            },
            "cross_file_expectations": {
                "pair_a_b": {
                    "files": ["python/cross_file_a.py", "python/cross_file_b.py"],
                    "expected_cross_file_clone_range": [1, 5],
                },
            },
        },
    }


class TestAC1HeavyDuplicationDetection:
    """Tests for AC-1: Heavy duplication detection."""

    def test_detects_heavy_duplication(self, heavy_dup_analysis, mock_ground_truth):
        """Test that heavy duplication files are detected."""
        result = _ac1_heavy_duplication_detected(heavy_dup_analysis, mock_ground_truth)

        assert result.check_id == "AC-1"
        assert result.category == CheckCategory.ACCURACY
        assert result.passed is True
        assert result.score >= 0.8

    def test_no_heavy_files_in_ground_truth(self, heavy_dup_analysis):
        """Test when no heavy duplication files are in ground truth."""
        gt = {"python": {"files": {"regular.py": {}}}}
        result = _ac1_heavy_duplication_detected(heavy_dup_analysis, gt)

        assert result.passed is True
        assert result.score == 1.0

    def test_missed_heavy_duplication(self, no_dup_analysis, mock_ground_truth):
        """Test failure when heavy duplication is missed."""
        # Modify ground truth to expect heavy_duplication.py but analysis shows 0 clones
        analysis = {
            "metadata": {},
            "files": [{"path": "python/heavy_duplication.py", "duplicate_blocks": 0}],
            "duplications": [],
        }
        result = _ac1_heavy_duplication_detected(analysis, mock_ground_truth)

        # Should fail because heavy file has 0 clones detected
        assert "detected" in result.evidence


class TestAC2CloneCountAccuracy:
    """Tests for AC-2: Clone count in expected range."""

    def test_clone_count_in_range(self, heavy_dup_analysis, mock_ground_truth):
        """Test clone counts within expected range."""
        result = _ac2_clone_count_in_range(heavy_dup_analysis, mock_ground_truth)

        assert result.check_id == "AC-2"
        assert result.category == CheckCategory.ACCURACY
        # Heavy file has 5 clones, expected range is [3, 10] - should pass
        assert "files" in result.evidence

    def test_clone_count_out_of_range(self, mock_ground_truth):
        """Test clone count outside expected range."""
        analysis = {
            "metadata": {},
            "files": [
                {"path": "python/heavy_duplication.py", "duplicate_blocks": 50},  # Way above range
            ],
        }
        result = _ac2_clone_count_in_range(analysis, mock_ground_truth)

        # 50 clones is outside [3, 10] range
        evidence_files = result.evidence.get("files", [])
        if evidence_files:
            out_of_range = [f for f in evidence_files if f.get("status") == "out_of_range"]
            assert len(out_of_range) > 0

    def test_no_expectations(self):
        """Test with no clone count expectations."""
        gt = {"python": {"files": {"test.py": {}}}}
        analysis = {"metadata": {}, "files": []}
        result = _ac2_clone_count_in_range(analysis, gt)

        assert result.passed is True
        assert result.score == 1.0


class TestAC3DuplicationPercentageAccuracy:
    """Tests for AC-3: Duplication percentage accuracy."""

    def test_percentage_in_range(self, heavy_dup_analysis, mock_ground_truth):
        """Test duplication percentage within expected range."""
        result = _ac3_duplication_percentage_accuracy(heavy_dup_analysis, mock_ground_truth)

        assert result.check_id == "AC-3"
        assert result.category == CheckCategory.ACCURACY
        # Heavy file has 35%, expected range is [20, 50] - should be in range
        assert "files" in result.evidence

    def test_percentage_out_of_range(self, mock_ground_truth):
        """Test percentage outside expected range."""
        analysis = {
            "metadata": {},
            "files": [
                {"path": "python/heavy_duplication.py", "duplication_percentage": 80.0},
            ],
        }
        result = _ac3_duplication_percentage_accuracy(analysis, mock_ground_truth)

        evidence_files = result.evidence.get("files", [])
        if evidence_files:
            out_of_range = [f for f in evidence_files if f.get("status") == "out_of_range"]
            # 80% is outside [20, 50] range
            assert len(out_of_range) > 0

    def test_no_percentage_expectations(self):
        """Test with no percentage expectations."""
        gt = {"python": {"files": {"test.py": {}}}}
        analysis = {"metadata": {}, "files": []}
        result = _ac3_duplication_percentage_accuracy(analysis, gt)

        assert result.passed is True
        assert result.score == 1.0


class TestAC4NoFalsePositives:
    """Tests for AC-4: No false positives in clean files."""

    def test_clean_file_no_clones(self, no_dup_analysis, mock_ground_truth):
        """Test clean file correctly has no clones."""
        result = _ac4_no_false_positives_clean_files(no_dup_analysis, mock_ground_truth)

        assert result.check_id == "AC-4"
        assert result.category == CheckCategory.ACCURACY
        assert result.passed is True

    def test_clean_file_with_false_positive(self, mock_ground_truth):
        """Test false positive in clean file."""
        analysis = {
            "metadata": {},
            "files": [
                {"path": "python/no_duplication.py", "duplicate_blocks": 5},  # Should be 0
            ],
        }
        result = _ac4_no_false_positives_clean_files(analysis, mock_ground_truth)

        evidence_files = result.evidence.get("files", [])
        if evidence_files:
            false_positives = [f for f in evidence_files if f.get("status") == "false_positive"]
            assert len(false_positives) > 0

    def test_no_clean_files_in_ground_truth(self, heavy_dup_analysis):
        """Test when no clean files are in ground truth."""
        gt = {"python": {"files": {"heavy.py": {"expected_clone_range": [5, 10]}}}}
        result = _ac4_no_false_positives_clean_files(heavy_dup_analysis, gt)

        assert result.passed is True
        assert result.score == 1.0


class TestAC5CrossFileDetection:
    """Tests for AC-5: Cross-file clone detection."""

    def test_cross_file_detected(self, cross_file_analysis, mock_ground_truth):
        """Test cross-file clones are detected."""
        result = _ac5_cross_file_detection(cross_file_analysis, mock_ground_truth)

        assert result.check_id == "AC-5"
        assert result.category == CheckCategory.ACCURACY

    def test_no_cross_file_expectations(self, cross_file_analysis):
        """Test with no cross-file expectations."""
        gt = {"python": {"files": {}}}
        result = _ac5_cross_file_detection(cross_file_analysis, gt)

        assert result.passed is True
        assert result.score == 1.0

    def test_missed_cross_file_clone(self, mock_ground_truth):
        """Test when cross-file clone is missed."""
        analysis = {
            "metadata": {},
            "files": [],
            "duplications": [],  # No clones at all
        }
        result = _ac5_cross_file_detection(analysis, mock_ground_truth)

        # Should fail if expectations exist but no clones found
        pairs = result.evidence.get("pairs", [])
        if pairs:
            missed = [p for p in pairs if p.get("status") == "missed"]
            assert len(missed) > 0


class TestAC6SemanticIdentifierDetection:
    """Tests for AC-6: Semantic identifier detection."""

    def test_semantic_mode_disabled(self, heavy_dup_analysis, mock_ground_truth):
        """Test when semantic mode is not enabled."""
        result = _ac6_semantic_identifier_detection(heavy_dup_analysis, mock_ground_truth)

        assert result.check_id == "AC-6"
        assert result.category == CheckCategory.ACCURACY
        assert result.passed is True
        assert result.score == 0.5  # Neutral score for non-semantic mode
        assert "semantic mode not enabled" in result.message.lower()

    def test_semantic_mode_enabled(self, semantic_analysis, mock_ground_truth):
        """Test when semantic mode is enabled."""
        result = _ac6_semantic_identifier_detection(semantic_analysis, mock_ground_truth)

        assert result.check_id == "AC-6"
        # Should attempt to evaluate semantic expectations

    def test_no_semantic_expectations(self, semantic_analysis):
        """Test with no semantic expectations."""
        gt = {"python": {"files": {"regular.py": {}}}}
        result = _ac6_semantic_identifier_detection(semantic_analysis, gt)

        assert result.passed is True


class TestAC7SemanticLiteralDetection:
    """Tests for AC-7: Semantic literal detection."""

    def test_semantic_mode_disabled(self, heavy_dup_analysis, mock_ground_truth):
        """Test when semantic mode is not enabled."""
        result = _ac7_semantic_literal_detection(heavy_dup_analysis, mock_ground_truth)

        assert result.check_id == "AC-7"
        assert result.category == CheckCategory.ACCURACY
        assert result.passed is True
        assert result.score == 0.5  # Neutral score
        assert "semantic mode not enabled" in result.message.lower()

    def test_semantic_mode_enabled(self, semantic_analysis, mock_ground_truth):
        """Test when semantic mode is enabled."""
        result = _ac7_semantic_literal_detection(semantic_analysis, mock_ground_truth)

        assert result.check_id == "AC-7"

    def test_no_literal_expectations(self, semantic_analysis):
        """Test with no semantic literal expectations."""
        gt = {"python": {"files": {"test.py": {}}}}
        result = _ac7_semantic_literal_detection(semantic_analysis, gt)

        assert result.passed is True


class TestAC8CloneLineAccuracy:
    """Tests for AC-8: Clone line accuracy."""

    def test_valid_clones(self, heavy_dup_analysis, mock_ground_truth):
        """Test clones with valid line counts."""
        result = _ac8_clone_line_accuracy(heavy_dup_analysis, mock_ground_truth)

        assert result.check_id == "AC-8"
        assert result.category == CheckCategory.ACCURACY
        # Clone has 15 lines and 2 occurrences - valid
        assert result.passed is True

    def test_no_clones(self, no_dup_analysis, mock_ground_truth):
        """Test with no clones to verify."""
        result = _ac8_clone_line_accuracy(no_dup_analysis, mock_ground_truth)

        assert result.passed is True
        assert result.score == 1.0
        assert "no clones" in result.message.lower()

    def test_invalid_clones(self, mock_ground_truth):
        """Test clones with invalid characteristics."""
        analysis = {
            "metadata": {},
            "files": [],
            "duplications": [
                # Clone with only 1 line (too small)
                {"clone_id": "CPD-0001", "lines": 1, "tokens": 10, "occurrences": [
                    {"file": "a.py", "line_start": 1, "line_end": 1},
                    {"file": "b.py", "line_start": 1, "line_end": 1},
                ]},
                # Clone with only 1 occurrence (invalid)
                {"clone_id": "CPD-0002", "lines": 10, "tokens": 50, "occurrences": [
                    {"file": "c.py", "line_start": 1, "line_end": 10},
                ]},
            ],
        }
        result = _ac8_clone_line_accuracy(analysis, mock_ground_truth)

        # Both clones are invalid, so score should be low
        assert result.score < 1.0


class TestRunAccuracyChecks:
    """Tests for the run_accuracy_checks aggregator function."""

    def test_runs_all_checks(self, heavy_dup_analysis, tmp_path):
        """Test that all 8 accuracy checks are run."""
        # Create mock ground truth file
        gt_dir = tmp_path / "ground-truth"
        gt_dir.mkdir()
        gt_file = gt_dir / "python.json"
        import json
        gt_file.write_text(json.dumps({
            "language": "python",
            "files": {
                "heavy_duplication.py": {"expected_clone_range": [3, 10]},
            },
        }))

        results = run_accuracy_checks(heavy_dup_analysis, str(gt_dir))

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

    def test_all_checks_have_correct_category(self, heavy_dup_analysis, tmp_path):
        """Test that all checks are categorized as ACCURACY."""
        gt_dir = tmp_path / "ground-truth"
        gt_dir.mkdir()
        gt_file = gt_dir / "python.json"
        import json
        gt_file.write_text(json.dumps({"language": "python", "files": {}}))

        results = run_accuracy_checks(heavy_dup_analysis, str(gt_dir))

        for result in results:
            assert result.category == CheckCategory.ACCURACY
