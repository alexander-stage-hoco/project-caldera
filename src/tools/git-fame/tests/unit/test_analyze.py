"""Unit tests for git-fame analyze script pure functions.

Tests compute_hhi, compute_bus_factor, extract_author_metric,
transform_output, and fallback_commit_hash from scripts/analyze.py.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from scripts.analyze import (
    compute_bus_factor,
    compute_hhi,
    extract_author_metric,
    fallback_commit_hash,
    transform_output,
)


# =============================================================================
# compute_hhi
# =============================================================================


class TestComputeHhi:
    def test_empty_list_returns_zero(self):
        assert compute_hhi([]) == 0.0

    def test_single_author_full_ownership(self):
        assert compute_hhi([100.0]) == pytest.approx(1.0)

    def test_two_equal_authors(self):
        # Each 50% → (0.5)^2 + (0.5)^2 = 0.5
        assert compute_hhi([50.0, 50.0]) == pytest.approx(0.5)

    def test_realistic_distribution(self):
        # 60/30/10 → 0.36 + 0.09 + 0.01 = 0.46
        assert compute_hhi([60.0, 30.0, 10.0]) == pytest.approx(0.46)


# =============================================================================
# compute_bus_factor
# =============================================================================


class TestComputeBusFactor:
    def test_empty_returns_zero(self):
        assert compute_bus_factor([]) == 0

    def test_single_author(self):
        assert compute_bus_factor([100.0]) == 1

    def test_two_equal_authors(self):
        # 50+50=100 → need both to reach 50% threshold? No — first author hits 50.
        assert compute_bus_factor([50.0, 50.0]) == 1

    def test_needs_two_for_threshold(self):
        # 40+35+25 → need 2 authors (40+35=75 >= 50)
        assert compute_bus_factor([40.0, 35.0, 25.0]) == 2

    def test_custom_threshold(self):
        # 30/30/20/20 with threshold=80 → need 3 (30+30+20=80)
        assert compute_bus_factor([30.0, 30.0, 20.0, 20.0], threshold=80.0) == 3

    def test_sorts_descending_internally(self):
        # Pass unsorted — function should sort
        assert compute_bus_factor([10.0, 60.0, 30.0]) == 1

    def test_exact_threshold_boundary_50_50(self):
        """Two authors at exactly 50/50 — first author hits threshold exactly."""
        # cumulative after first: 50.0 >= 50.0 → bus_factor = 1
        assert compute_bus_factor([50.0, 50.0]) == 1

    def test_just_below_threshold(self):
        """First author at 49.9 should need second author to cross threshold."""
        assert compute_bus_factor([49.9, 49.9, 0.2]) == 2

    def test_exact_threshold_with_custom_value(self):
        """Exact boundary with custom threshold=70 and [35, 35, 30]."""
        # 35 < 70, 35+35=70 >= 70 → 2
        assert compute_bus_factor([35.0, 35.0, 30.0], threshold=70.0) == 2

    def test_all_authors_needed(self):
        """Very high threshold that requires all authors."""
        # threshold=100, need all: 40+30+20+10=100
        assert compute_bus_factor([40.0, 30.0, 20.0, 10.0], threshold=100.0) == 4


# =============================================================================
# extract_author_metric
# =============================================================================


class TestExtractAuthorMetric:
    def test_normal_output(self):
        raw = {
            "columns": ["Author", "loc", "coms", "fils"],
            "data": [
                ["Alice", 500, 20, 10],
                ["Bob", 300, 15, 8],
            ],
        }
        result = extract_author_metric(raw, "loc")
        assert result == {"Alice": 500, "Bob": 300}

    def test_empty_data(self):
        raw = {"columns": ["Author", "loc"], "data": []}
        result = extract_author_metric(raw)
        assert result == {}

    def test_missing_column_falls_back(self):
        raw = {
            "columns": ["Author", "loc"],
            "data": [["Alice", 100]],
        }
        # Request a column that doesn't exist — falls back to "loc" index
        result = extract_author_metric(raw, "nonexistent")
        assert result == {"Alice": 100}


# =============================================================================
# transform_output
# =============================================================================


class TestTransformOutput:
    def test_normal_multi_author(self, tmp_path: Path):
        raw = {
            "columns": ["Author", "loc", "coms", "fils"],
            "data": [
                ["Alice", 600, 20, 10],
                ["Bob", 400, 15, 8],
            ],
        }
        ins = {"Alice": 700, "Bob": 450}
        dels = {"Alice": 100, "Bob": 50}

        result = transform_output(
            raw, ins, dels, tmp_path,
            run_id="test-run", repo_id="test-repo",
            branch="main", commit="a" * 40,
        )

        assert "metadata" in result
        assert "data" in result
        assert result["metadata"]["tool_name"] == "git-fame"

        data = result["data"]
        assert data["summary"]["author_count"] == 2
        assert data["summary"]["total_loc"] == 1000
        assert data["summary"]["bus_factor"] >= 1
        assert len(data["authors"]) == 2

        # Authors sorted by ownership descending
        assert data["authors"][0]["name"] == "Alice"
        assert data["authors"][0]["ownership_pct"] == 60.0
        assert data["authors"][0]["insertions_total"] == 700
        assert data["authors"][0]["deletions_total"] == 100

    def test_empty_data_returns_error_envelope(self, tmp_path: Path):
        raw = {"columns": [], "data": []}
        result = transform_output(
            raw, {}, {}, tmp_path,
            run_id="test-run", repo_id="test-repo",
            branch="main", commit="a" * 40,
        )

        assert result["metadata"]["tool_name"] == "git-fame"
        data = result["data"]
        assert data["summary"]["author_count"] == 0
        assert data["summary"]["total_loc"] == 0
        assert data["authors"] == []

    def test_single_author(self, tmp_path: Path):
        raw = {
            "columns": ["Author", "loc", "coms", "fils"],
            "data": [["Solo", 500, 30, 15]],
        }
        result = transform_output(
            raw, {"Solo": 600}, {"Solo": 100}, tmp_path,
            run_id="test-run", repo_id="test-repo",
            branch="main", commit="b" * 40,
        )

        data = result["data"]
        assert data["summary"]["author_count"] == 1
        assert data["summary"]["hhi_index"] == pytest.approx(1.0)
        assert data["summary"]["bus_factor"] == 1
        assert data["authors"][0]["ownership_pct"] == 100.0


# =============================================================================
# fallback_commit_hash
# =============================================================================


class TestFallbackCommitHash:
    def test_returns_40_char_hex(self, tmp_path: Path):
        (tmp_path / "file.txt").write_text("hello")
        result = fallback_commit_hash(tmp_path)
        assert len(result) == 40
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic_for_same_content(self, tmp_path: Path):
        (tmp_path / "file.txt").write_text("hello")
        hash1 = fallback_commit_hash(tmp_path)

        # Create identical content in a different directory
        with tempfile.TemporaryDirectory() as other:
            other_path = Path(other)
            (other_path / "file.txt").write_text("hello")
            hash2 = fallback_commit_hash(other_path)

        assert hash1 == hash2
