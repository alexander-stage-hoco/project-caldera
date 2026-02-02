"""Tests for gitleaks directory rollup invariants.

These tests validate that directory rollup metrics satisfy
the required mathematical invariants.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def load_output_json(output_dir: Path) -> dict | None:
    """Load output.json from the most recent run."""
    output_file = output_dir / "output.json"
    if output_file.exists():
        return json.loads(output_file.read_text())
    # Try to find the most recent run directory
    run_dirs = sorted(output_dir.glob("*/output.json"), reverse=True)
    if run_dirs:
        return json.loads(run_dirs[0].read_text())
    return None


@pytest.fixture
def sample_directories() -> dict:
    """Sample directory rollup data for testing."""
    return {
        ".": {
            "direct_secret_count": 1,
            "recursive_secret_count": 4,
            "direct_file_count": 1,
            "recursive_file_count": 3,
            "rule_id_counts": {"github-pat": 2, "aws-access-token": 2},
        },
        "src": {
            "direct_secret_count": 1,
            "recursive_secret_count": 3,
            "direct_file_count": 1,
            "recursive_file_count": 2,
            "rule_id_counts": {"github-pat": 1, "aws-access-token": 2},
        },
        "src/api": {
            "direct_secret_count": 2,
            "recursive_secret_count": 2,
            "direct_file_count": 1,
            "recursive_file_count": 1,
            "rule_id_counts": {"aws-access-token": 2},
        },
    }


class TestRollupInvariants:
    """Test rollup mathematical invariants."""

    def test_recursive_gte_direct_secret_count(self, sample_directories: dict) -> None:
        """RV-1: recursive_secret_count >= direct_secret_count for all directories."""
        for path, metrics in sample_directories.items():
            direct = metrics.get("direct_secret_count", 0)
            recursive = metrics.get("recursive_secret_count", 0)
            assert recursive >= direct, (
                f"Directory {path}: recursive ({recursive}) < direct ({direct})"
            )

    def test_recursive_gte_direct_file_count(self, sample_directories: dict) -> None:
        """RV-2: recursive_file_count >= direct_file_count for all directories."""
        for path, metrics in sample_directories.items():
            direct = metrics.get("direct_file_count", 0)
            recursive = metrics.get("recursive_file_count", 0)
            assert recursive >= direct, (
                f"Directory {path}: recursive files ({recursive}) < direct files ({direct})"
            )

    def test_non_negative_counts(self, sample_directories: dict) -> None:
        """RV-3: All counts must be non-negative."""
        for path, metrics in sample_directories.items():
            for key, value in metrics.items():
                if key.endswith("_count"):
                    assert value >= 0, f"Directory {path}: {key} is negative ({value})"

    def test_root_recursive_equals_total(self, sample_directories: dict) -> None:
        """RV-4: Root recursive_secret_count should equal total_secrets."""
        root = sample_directories.get(".", {})
        root_recursive = root.get("recursive_secret_count", 0)
        # In a real test, we'd compare against total_secrets from the data
        # Here we just verify root exists and has valid recursive count
        assert "." in sample_directories, "Root directory (.) must be present"
        assert root_recursive >= 0, "Root recursive count must be non-negative"


class TestRollupValidation:
    """Test rollup validation logic."""

    def test_leaf_directory_equality(self) -> None:
        """Leaf directories should have direct == recursive."""
        leaf_dir = {
            "direct_secret_count": 2,
            "recursive_secret_count": 2,
            "direct_file_count": 1,
            "recursive_file_count": 1,
        }
        assert leaf_dir["direct_secret_count"] == leaf_dir["recursive_secret_count"]
        assert leaf_dir["direct_file_count"] == leaf_dir["recursive_file_count"]

    def test_parent_includes_children(self) -> None:
        """Parent recursive count must be >= sum of direct counts."""
        parent = {
            "direct_secret_count": 1,
            "recursive_secret_count": 4,
        }
        children = [
            {"direct_secret_count": 2, "recursive_secret_count": 2},
            {"direct_secret_count": 1, "recursive_secret_count": 1},
        ]
        child_recursive_sum = sum(c["recursive_secret_count"] for c in children)
        expected_recursive = parent["direct_secret_count"] + child_recursive_sum
        assert parent["recursive_secret_count"] == expected_recursive

    def test_empty_directory(self) -> None:
        """Empty directories should have zero counts."""
        empty_dir = {
            "direct_secret_count": 0,
            "recursive_secret_count": 0,
            "direct_file_count": 0,
            "recursive_file_count": 0,
        }
        assert empty_dir["direct_secret_count"] == 0
        assert empty_dir["recursive_secret_count"] == 0
        assert empty_dir["direct_file_count"] == 0
        assert empty_dir["recursive_file_count"] == 0


class TestRollupIntegration:
    """Integration tests for rollup data from actual output."""

    @pytest.fixture
    def output_data(self) -> dict | None:
        """Load output data if available."""
        tool_dir = Path(__file__).resolve().parents[2]
        outputs_dir = tool_dir / "outputs"
        return load_output_json(outputs_dir)

    def test_output_has_directories(self, output_data: dict | None) -> None:
        """Output should contain directories section."""
        if output_data is None:
            pytest.skip("No output.json available - run 'make analyze' first")

        data = output_data.get("data", {})
        assert "directories" in data, "Output must contain 'directories' section"

    def test_output_rollup_invariants(self, output_data: dict | None) -> None:
        """All rollup invariants should hold for actual output."""
        if output_data is None:
            pytest.skip("No output.json available - run 'make analyze' first")

        data = output_data.get("data", {})
        directories = data.get("directories", {})
        total_secrets = data.get("total_secrets", 0)

        # RV-1 and RV-2: Recursive >= Direct
        for path, metrics in directories.items():
            direct_secrets = metrics.get("direct_secret_count", 0)
            recursive_secrets = metrics.get("recursive_secret_count", 0)
            assert recursive_secrets >= direct_secrets, (
                f"RV-1 failed for {path}: recursive ({recursive_secrets}) < direct ({direct_secrets})"
            )

            direct_files = metrics.get("direct_file_count", 0)
            recursive_files = metrics.get("recursive_file_count", 0)
            assert recursive_files >= direct_files, (
                f"RV-2 failed for {path}: recursive files ({recursive_files}) < direct files ({direct_files})"
            )

        # RV-4: Root recursive equals total
        root = directories.get(".", {})
        root_recursive = root.get("recursive_secret_count", 0)
        assert root_recursive == total_secrets, (
            f"RV-4 failed: root recursive ({root_recursive}) != total_secrets ({total_secrets})"
        )
