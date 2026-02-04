"""Integration tests for PMD CPD evaluation pipeline."""

import pytest
import sys
import json
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks import (
    load_analysis,
    load_all_ground_truth,
    get_cross_file_clones,
    SUPPORTED_LANGUAGES,
)


# Paths relative to the test file
TOOL_ROOT = Path(__file__).parent.parent.parent
GROUND_TRUTH_DIR = TOOL_ROOT / "evaluation" / "ground-truth"
SYNTHETIC_REPOS_DIR = TOOL_ROOT / "eval-repos" / "synthetic"


class TestGroundTruthFiles:
    """Test that ground truth files are valid."""

    def test_all_languages_have_ground_truth(self):
        """Test that each supported language has a ground truth file."""
        for lang in SUPPORTED_LANGUAGES:
            gt_file = GROUND_TRUTH_DIR / f"{lang}.json"
            assert gt_file.exists(), f"Missing ground truth file for {lang}"

    def test_ground_truth_files_are_valid_json(self):
        """Test that all ground truth files are valid JSON."""
        gt = load_all_ground_truth(GROUND_TRUTH_DIR)
        assert len(gt) == len(SUPPORTED_LANGUAGES)

        for lang, data in gt.items():
            assert "language" in data
            assert "files" in data
            assert isinstance(data["files"], dict)

    def test_ground_truth_has_required_test_files(self):
        """Test that ground truth references expected test file types."""
        # Patterns match both underscore and no-underscore naming
        required_patterns = [
            ("nodup", "no_dup"),  # NoDuplication, no_duplication
            ("lightdup", "light_dup"),
            ("heavydup", "heavy_dup"),
            ("crossfile", "cross_file"),
            ("semantic",),
        ]

        gt = load_all_ground_truth(GROUND_TRUTH_DIR)
        for lang, data in gt.items():
            files = data.get("files", {})
            # Remove underscores and spaces for matching
            filenames_normalized = " ".join(files.keys()).lower().replace("_", "")

            for patterns in required_patterns:
                found = any(p in filenames_normalized for p in patterns)
                assert found, (
                    f"Missing {patterns[0]} file in {lang} ground truth"
                )


class TestSyntheticTestFiles:
    """Test that synthetic test files exist and are properly structured."""

    def test_all_languages_have_synthetic_repos(self):
        """Test that each supported language has a synthetic test directory."""
        for lang in SUPPORTED_LANGUAGES:
            lang_dir = SYNTHETIC_REPOS_DIR / lang
            assert lang_dir.exists(), f"Missing synthetic repo for {lang}"
            assert lang_dir.is_dir()

    def test_synthetic_repos_have_test_files(self):
        """Test that each language has the expected test files."""
        for lang in SUPPORTED_LANGUAGES:
            lang_dir = SYNTHETIC_REPOS_DIR / lang
            files = list(lang_dir.iterdir())

            # Should have at least 5 test files
            assert len(files) >= 5, f"Insufficient test files for {lang}"

            # Check for key file patterns (normalize by removing underscores)
            file_names_normalized = [f.stem.lower().replace("_", "") for f in files]
            assert any("nodup" in name for name in file_names_normalized), (
                f"Missing no_duplication file for {lang}"
            )
            assert any("heavy" in name for name in file_names_normalized), (
                f"Missing heavy_duplication file for {lang}"
            )


class TestCrossFileCloneDetection:
    """Test cross-file clone detection utilities."""

    def test_get_cross_file_clones_empty(self):
        """Test with analysis containing no duplications."""
        analysis = {"duplications": []}
        clones = get_cross_file_clones(analysis)
        assert clones == []

    def test_get_cross_file_clones_single_file(self):
        """Test clone within single file is not cross-file."""
        analysis = {
            "duplications": [
                {
                    "clone_id": "CPD-0001",
                    "occurrences": [
                        {"file": "src/main.py", "line_start": 10, "line_end": 20},
                        {"file": "src/main.py", "line_start": 50, "line_end": 60},
                    ]
                }
            ]
        }
        clones = get_cross_file_clones(analysis)
        assert len(clones) == 0

    def test_get_cross_file_clones_multiple_files(self):
        """Test clone spanning multiple files is detected."""
        analysis = {
            "duplications": [
                {
                    "clone_id": "CPD-0001",
                    "occurrences": [
                        {"file": "src/a.py", "line_start": 10, "line_end": 20},
                        {"file": "src/b.py", "line_start": 5, "line_end": 15},
                    ]
                }
            ]
        }
        clones = get_cross_file_clones(analysis)
        assert len(clones) == 1
        assert clones[0]["clone_id"] == "CPD-0001"


@pytest.mark.skipif(
    not (TOOL_ROOT / "output" / "runs" / "synthetic.json").exists(),
    reason="Analysis output not available (run 'make analyze' first)"
)
class TestAnalysisOutput:
    """Test the analysis output structure."""

    @pytest.fixture
    def analysis(self):
        """Load the synthetic analysis output."""
        output_path = TOOL_ROOT / "output" / "runs" / "synthetic.json"
        return load_analysis(output_path)

    def test_analysis_has_required_sections(self, analysis):
        """Test that analysis output has all required sections."""
        assert "metadata" in analysis
        assert "summary" in analysis
        assert "files" in analysis
        assert "duplications" in analysis
        assert "statistics" in analysis

    def test_analysis_metadata_is_valid(self, analysis):
        """Test that metadata contains expected fields."""
        metadata = analysis["metadata"]
        assert "version" in metadata
        assert "cpd_version" in metadata
        assert "min_tokens" in metadata

    def test_analysis_summary_is_valid(self, analysis):
        """Test that summary contains expected metrics."""
        summary = analysis["summary"]
        assert "total_files" in summary
        assert "total_clones" in summary
        assert "duplication_percentage" in summary

    def test_analysis_files_have_metrics(self, analysis):
        """Test that file entries have required metrics."""
        files = analysis["files"]
        if files:
            first_file = files[0]
            assert "path" in first_file
            assert "duplicate_lines" in first_file
            assert "duplication_percentage" in first_file
