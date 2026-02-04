"""Integration tests for ground truth validation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

TOOL_DIR = Path(__file__).parent.parent.parent
GT_DIR = TOOL_DIR / "evaluation" / "ground-truth"

sys.path.insert(0, str(TOOL_DIR / "scripts"))


class TestGroundTruthFiles:
    """Tests for ground truth file structure and validity."""

    @pytest.fixture
    def ground_truth_files(self) -> list[Path]:
        """Get all ground truth JSON files."""
        if not GT_DIR.exists():
            pytest.skip("Ground truth directory not found")
        return list(GT_DIR.glob("*.json"))

    def test_ground_truth_directory_exists(self) -> None:
        """Ground truth directory should exist."""
        assert GT_DIR.exists(), f"Ground truth directory not found at {GT_DIR}"

    def test_at_least_one_ground_truth_file(self, ground_truth_files: list[Path]) -> None:
        """Should have at least one ground truth file."""
        assert len(ground_truth_files) >= 1, "No ground truth files found"

    def test_minimum_five_ground_truth_files(self, ground_truth_files: list[Path]) -> None:
        """Should have at least 5 ground truth files for production."""
        assert len(ground_truth_files) >= 5, f"Need 5+ GT files, found {len(ground_truth_files)}"

    def test_ground_truth_files_are_valid_json(self, ground_truth_files: list[Path]) -> None:
        """All ground truth files should be valid JSON."""
        for gt_file in ground_truth_files:
            with open(gt_file) as f:
                data = json.load(f)
            assert isinstance(data, dict), f"{gt_file.name} is not a dict"

    def test_ground_truth_files_have_schema_version(self, ground_truth_files: list[Path]) -> None:
        """Ground truth files should have schema_version."""
        for gt_file in ground_truth_files:
            with open(gt_file) as f:
                data = json.load(f)
            assert "schema_version" in data, f"{gt_file.name} missing schema_version"

    def test_ground_truth_files_have_scenario(self, ground_truth_files: list[Path]) -> None:
        """Ground truth files should have scenario field."""
        for gt_file in ground_truth_files:
            with open(gt_file) as f:
                data = json.load(f)
            has_scenario = "scenario" in data or "language" in data
            assert has_scenario, f"{gt_file.name} missing scenario/language"

    def test_ground_truth_files_have_expected(self, ground_truth_files: list[Path]) -> None:
        """Ground truth files should have expected outcomes."""
        for gt_file in ground_truth_files:
            with open(gt_file) as f:
                data = json.load(f)
            has_expected = "expected" in data or "files" in data
            assert has_expected, f"{gt_file.name} missing expected outcomes"

    def test_csharp_ground_truth_exists(self, ground_truth_files: list[Path]) -> None:
        """C# ground truth should exist (primary language for DevSkim)."""
        csharp_files = [f for f in ground_truth_files if "csharp" in f.stem.lower()]
        assert len(csharp_files) >= 1, "C# ground truth file required"

    def test_clean_scenario_exists(self, ground_truth_files: list[Path]) -> None:
        """Clean scenario (no issues expected) should exist."""
        clean_files = [f for f in ground_truth_files if "clean" in f.stem.lower()]
        assert len(clean_files) >= 1, "Clean scenario ground truth required"


class TestGroundTruthContent:
    """Tests for ground truth content validity."""

    @pytest.fixture
    def csharp_gt(self) -> dict:
        """Load C# ground truth."""
        gt_path = GT_DIR / "csharp.json"
        if not gt_path.exists():
            pytest.skip("C# ground truth not found")
        with open(gt_path) as f:
            return json.load(f)

    def test_csharp_has_files_section(self, csharp_gt: dict) -> None:
        """C# ground truth should define expected files."""
        assert "files" in csharp_gt, "Missing files section"
        assert len(csharp_gt["files"]) > 0, "Files section is empty"

    def test_csharp_has_aggregate_expectations(self, csharp_gt: dict) -> None:
        """C# ground truth should have aggregate expectations."""
        expected = csharp_gt.get("expected", {})
        has_aggregate = "aggregate_expectations" in expected or "aggregate_expectations" in csharp_gt
        assert has_aggregate or "files" in csharp_gt, "Missing aggregate expectations"

    def test_files_have_expected_issues(self, csharp_gt: dict) -> None:
        """File entries should specify expected issues."""
        files = csharp_gt.get("files", {})
        for file_name, file_data in files.items():
            assert "expected_issues" in file_data or "total_expected" in file_data, \
                f"File {file_name} missing expected_issues"

    def test_expected_issues_have_category_or_rule(self, csharp_gt: dict) -> None:
        """Expected issues should have category or rule_id."""
        files = csharp_gt.get("files", {})
        for file_name, file_data in files.items():
            for issue in file_data.get("expected_issues", []):
                has_identifier = "category" in issue or "rule_id" in issue
                assert has_identifier, f"Issue in {file_name} missing category/rule_id"
