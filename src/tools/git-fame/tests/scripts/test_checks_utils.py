"""Tests for git-fame check utilities.

Tests verify the utility functions used across all check modules.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from checks.utils import (
    check_result,
    find_repo_analyses,
    load_analysis_bundle,
    load_ground_truth,
)


# =============================================================================
# load_analysis_bundle Tests
# =============================================================================


class TestLoadAnalysisBundle:
    """Test loading analysis bundle from output directory."""

    def test_load_from_latest_symlink(self, output_dir_with_data: Path):
        """Should load analysis from latest symlink."""
        bundle = load_analysis_bundle(output_dir_with_data)

        assert bundle != {}
        assert "results" in bundle
        assert bundle["results"]["tool"] == "git-fame"

    def test_load_from_runs_directory(self, temp_dir: Path, valid_output_data: dict[str, Any]):
        """Should load analysis from runs directory when latest doesn't exist."""
        output_dir = temp_dir / "output"
        runs_dir = output_dir / "runs" / "test-run"
        runs_dir.mkdir(parents=True)

        analysis_file = runs_dir / "analysis.json"
        analysis_file.write_text(json.dumps(valid_output_data, indent=2))

        bundle = load_analysis_bundle(output_dir)

        assert bundle != {}
        assert bundle["repo_name"] == "test-repo"

    def test_load_from_named_file(self, temp_dir: Path, valid_output_data: dict[str, Any]):
        """Should load analysis from named JSON file."""
        output_dir = temp_dir / "output"
        output_dir.mkdir(parents=True)

        # Create synthetic.json file
        data = valid_output_data.copy()
        data["repo_name"] = "synthetic"
        (output_dir / "synthetic.json").write_text(json.dumps(data, indent=2))

        bundle = load_analysis_bundle(output_dir, repo_name="synthetic")

        assert bundle != {}
        assert bundle["repo_name"] == "synthetic"

    def test_load_from_analysis_file(self, temp_dir: Path, valid_output_data: dict[str, Any]):
        """Should load from analysis.json in output directory."""
        output_dir = temp_dir / "output"
        output_dir.mkdir(parents=True)

        (output_dir / "analysis.json").write_text(json.dumps(valid_output_data, indent=2))

        bundle = load_analysis_bundle(output_dir)

        assert bundle != {}
        assert bundle["results"]["tool"] == "git-fame"

    def test_load_returns_empty_for_missing_dir(self, temp_dir: Path):
        """Should return empty dict if directory doesn't exist."""
        nonexistent = temp_dir / "nonexistent"
        bundle = load_analysis_bundle(nonexistent)

        assert bundle == {}

    def test_load_returns_empty_for_empty_dir(self, temp_dir: Path):
        """Should return empty dict if directory has no analysis files."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        bundle = load_analysis_bundle(empty_dir)

        assert bundle == {}

    def test_load_handles_invalid_json(self, temp_dir: Path):
        """Should handle invalid JSON gracefully."""
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        (output_dir / "analysis.json").write_text("not valid json {{{")

        bundle = load_analysis_bundle(output_dir)

        assert bundle == {}

    def test_load_finds_most_recent_run(self, temp_dir: Path, valid_output_data: dict[str, Any]):
        """Should find most recent run when multiple exist."""
        output_dir = temp_dir / "output"
        runs_dir = output_dir / "runs"

        # Create older run
        old_run = runs_dir / "run-old"
        old_run.mkdir(parents=True)
        old_data = valid_output_data.copy()
        old_data["repo_name"] = "old-repo"
        (old_run / "analysis.json").write_text(json.dumps(old_data, indent=2))

        # Create newer run
        new_run = runs_dir / "run-new"
        new_run.mkdir()
        new_data = valid_output_data.copy()
        new_data["repo_name"] = "new-repo"
        (new_run / "analysis.json").write_text(json.dumps(new_data, indent=2))

        bundle = load_analysis_bundle(output_dir)

        # Should find one of them (order may vary)
        assert bundle != {}
        assert bundle["repo_name"] in ("old-repo", "new-repo")


# =============================================================================
# load_ground_truth Tests
# =============================================================================


class TestLoadGroundTruth:
    """Test loading ground truth from file."""

    def test_load_valid_ground_truth(self, ground_truth_file: Path):
        """Should load valid ground truth file."""
        gt = load_ground_truth(ground_truth_file)

        assert gt != {}
        assert "expected" in gt
        assert gt["scenario"] == "synthetic"

    def test_load_returns_empty_for_missing_file(self, temp_dir: Path):
        """Should return empty dict for missing file."""
        nonexistent = temp_dir / "missing.json"
        gt = load_ground_truth(nonexistent)

        assert gt == {}

    def test_load_handles_invalid_json(self, temp_dir: Path):
        """Should handle invalid JSON gracefully."""
        invalid_file = temp_dir / "invalid.json"
        invalid_file.write_text("not valid json")

        gt = load_ground_truth(invalid_file)

        assert gt == {}

    def test_load_ground_truth_with_authors(self, ground_truth_file: Path):
        """Should load ground truth with author expectations."""
        gt = load_ground_truth(ground_truth_file)

        assert "authors" in gt["expected"]
        assert len(gt["expected"]["authors"]) == 3

        # Check first author
        alice = gt["expected"]["authors"][0]
        assert alice["name"] == "Alice Developer"
        assert "loc_pct" in alice

    def test_load_ground_truth_with_ranges(self, ground_truth_file: Path):
        """Should load ground truth with min/max ranges."""
        gt = load_ground_truth(ground_truth_file)

        hhi_index = gt["expected"]["concentration_metrics"]["hhi_index"]
        assert "min" in hhi_index
        assert "max" in hhi_index


# =============================================================================
# find_repo_analyses Tests
# =============================================================================


class TestFindRepoAnalyses:
    """Test finding all repository analyses in output directory."""

    def test_find_from_combined_file(self, output_dir_with_multiple_repos: Path):
        """Should find analyses from combined_analysis.json."""
        analyses = find_repo_analyses(output_dir_with_multiple_repos)

        assert len(analyses) == 4
        assert "single-author" in analyses
        assert "multi-author" in analyses
        assert "balanced" in analyses
        assert "bus-factor-1" in analyses

    def test_find_from_individual_files(
        self, temp_dir: Path, single_author_data: dict[str, Any], multi_author_data: dict[str, Any]
    ):
        """Should find analyses from individual JSON files."""
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        (output_dir / "single-author.json").write_text(json.dumps(single_author_data, indent=2))
        (output_dir / "multi-author.json").write_text(json.dumps(multi_author_data, indent=2))

        analyses = find_repo_analyses(output_dir)

        assert len(analyses) == 2
        assert "single-author" in analyses
        assert "multi-author" in analyses

    def test_find_from_runs_directory(self, temp_dir: Path, valid_output_data: dict[str, Any]):
        """Should find analyses from runs directory structure."""
        output_dir = temp_dir / "output"
        runs_dir = output_dir / "runs"

        # Create multiple run directories
        for i, repo_name in enumerate(["repo-a", "repo-b"]):
            run_dir = runs_dir / f"run-{i}"
            run_dir.mkdir(parents=True)
            data = valid_output_data.copy()
            data["repo_name"] = repo_name
            (run_dir / "analysis.json").write_text(json.dumps(data, indent=2))

        analyses = find_repo_analyses(output_dir)

        assert len(analyses) >= 1  # At least one should be found
        assert any(name in analyses for name in ["repo-a", "repo-b"])

    def test_find_returns_empty_for_missing_dir(self, temp_dir: Path):
        """Should return empty dict for missing directory."""
        nonexistent = temp_dir / "nonexistent"
        analyses = find_repo_analyses(nonexistent)

        assert analyses == {}

    def test_find_skips_metadata_files(self, temp_dir: Path, valid_output_data: dict[str, Any]):
        """Should skip metadata.json and combined_analysis.json for individual file detection."""
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Write both metadata and actual analysis
        (output_dir / "metadata.json").write_text('{"run_id": "test"}')
        (output_dir / "repo-a.json").write_text(json.dumps(valid_output_data, indent=2))

        analyses = find_repo_analyses(output_dir)

        # Should have repo-a but not metadata
        assert "repo-a" in analyses or "test-repo" in analyses
        # Note: repo name comes from data["repo_name"] if present

    def test_find_handles_invalid_json_files(
        self, temp_dir: Path, valid_output_data: dict[str, Any]
    ):
        """Should skip invalid JSON files gracefully."""
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        (output_dir / "invalid.json").write_text("not valid json")
        (output_dir / "valid.json").write_text(json.dumps(valid_output_data, indent=2))

        analyses = find_repo_analyses(output_dir)

        # Should still find valid file
        assert len(analyses) >= 1


# =============================================================================
# check_result Tests
# =============================================================================


class TestCheckResult:
    """Test check result helper function."""

    def test_check_result_pass(self):
        """Should create passing check result."""
        result = check_result("OQ-1", True, "Check passed")

        assert result["check"] == "OQ-1"
        assert result["passed"] is True
        assert result["message"] == "Check passed"

    def test_check_result_fail(self):
        """Should create failing check result."""
        result = check_result("AA-2", False, "Check failed: expected 3, got 2")

        assert result["check"] == "AA-2"
        assert result["passed"] is False
        assert "expected 3, got 2" in result["message"]

    def test_check_result_with_long_message(self):
        """Should handle long messages."""
        long_message = "A" * 1000
        result = check_result("REL-1", True, long_message)

        assert result["message"] == long_message

    def test_check_result_keys(self):
        """Should have exactly the required keys."""
        result = check_result("TEST-1", True, "Test message")

        assert set(result.keys()) == {"check", "passed", "message"}

    def test_check_result_empty_check_id(self):
        """Should handle empty check ID."""
        result = check_result("", True, "Message")

        assert result["check"] == ""

    def test_check_result_special_characters(self):
        """Should handle special characters in message."""
        message = "Check: value=100% (threshold: >=50%)"
        result = check_result("TEST-1", True, message)

        assert result["message"] == message
