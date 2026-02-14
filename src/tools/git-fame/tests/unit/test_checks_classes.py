"""Unit tests for git-fame check classes.

Covers OutputQualityChecks, AuthorshipAccuracyChecks, IntegrationFitChecks,
InstallationChecks, PerformanceChecks, and ReliabilityChecks.

Tests exercise the actual check class methods using mock data written
to temporary directories, rather than asserting on pre-built fixture data.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from checks.authorship_accuracy import AuthorshipAccuracyChecks
from checks.installation import InstallationChecks
from checks.integration_fit import IntegrationFitChecks
from checks.output_quality import OutputQualityChecks
from checks.performance import PerformanceChecks
from checks.reliability import ReliabilityChecks


# =============================================================================
# Helpers
# =============================================================================


def _make_envelope_analysis(
    authors: list[dict[str, Any]] | None = None,
    summary: dict[str, Any] | None = None,
    files: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create a valid Caldera envelope analysis dict."""
    if authors is None:
        authors = [
            {"name": "Alice", "surviving_loc": 700, "ownership_pct": 70.0},
            {"name": "Bob", "surviving_loc": 300, "ownership_pct": 30.0},
        ]
    if summary is None:
        summary = {
            "author_count": len(authors),
            "total_loc": sum(a.get("surviving_loc", 0) for a in authors),
            "hhi_index": 0.58,
            "bus_factor": 1,
            "top_author_pct": 70.0,
            "top_two_pct": 100.0,
        }
    data: dict[str, Any] = {
        "tool": "git-fame",
        "tool_version": "3.1.1",
        "summary": summary,
        "authors": authors,
    }
    if files is not None:
        data["files"] = files
    return {
        "metadata": {
            "tool_name": "git-fame",
            "tool_version": "3.1.1",
            "run_id": "test-run",
            "repo_id": "test-repo",
            "branch": "main",
            "commit": "a" * 40,
            "timestamp": "2026-02-14T12:00:00+00:00",
            "schema_version": "1.0.0",
        },
        "data": data,
    }


def _write_combined(output_dir: Path, analyses: dict[str, dict]) -> Path:
    """Write a combined_analysis.json file and return output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "combined_analysis.json").write_text(json.dumps(analyses, indent=2))
    return output_dir


def _write_ground_truth(gt_file: Path, repos: dict[str, dict]) -> Path:
    """Write a ground truth JSON file and return its path."""
    gt_file.parent.mkdir(parents=True, exist_ok=True)
    gt_file.write_text(json.dumps(repos, indent=2))
    return gt_file


# =============================================================================
# OutputQualityChecks Tests
# =============================================================================


class TestOutputQualityChecksClass:
    """Test OutputQualityChecks methods against real data on disk."""

    def test_all_checks_pass_with_valid_data(self, tmp_path: Path):
        """All OQ checks should pass for valid envelope data."""
        analysis = _make_envelope_analysis()
        output_dir = _write_combined(tmp_path / "out", {"test-repo": analysis})

        # Also write the combined file as valid JSON for OQ-6
        checker = OutputQualityChecks(output_dir)
        results = checker.run_all()

        assert len(results) == 6
        # OQ-1 through OQ-4 should pass
        for r in results[:4]:
            assert r["passed"], f"{r['check']} failed: {r['message']}"

    def test_oq1_fails_missing_schema_version(self, tmp_path: Path):
        """OQ-1 should fail when schema_version is missing."""
        analysis = _make_envelope_analysis()
        del analysis["metadata"]["schema_version"]
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = OutputQualityChecks(output_dir)
        results = checker.run_all()
        oq1 = next(r for r in results if r["check"] == "OQ-1")
        assert not oq1["passed"]

    def test_oq2_fails_invalid_timestamp(self, tmp_path: Path):
        """OQ-2 should fail when timestamp is not ISO8601."""
        analysis = _make_envelope_analysis()
        analysis["metadata"]["timestamp"] = "not-a-timestamp"
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = OutputQualityChecks(output_dir)
        results = checker.run_all()
        oq2 = next(r for r in results if r["check"] == "OQ-2")
        assert not oq2["passed"]

    def test_oq3_fails_missing_summary_field(self, tmp_path: Path):
        """OQ-3 should fail when a required summary field is missing."""
        analysis = _make_envelope_analysis()
        del analysis["data"]["summary"]["hhi_index"]
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = OutputQualityChecks(output_dir)
        results = checker.run_all()
        oq3 = next(r for r in results if r["check"] == "OQ-3")
        assert not oq3["passed"]

    def test_oq4_fails_missing_author_field(self, tmp_path: Path):
        """OQ-4 should fail when a required author field is missing."""
        analysis = _make_envelope_analysis()
        del analysis["data"]["authors"][0]["name"]
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = OutputQualityChecks(output_dir)
        results = checker.run_all()
        oq4 = next(r for r in results if r["check"] == "OQ-4")
        assert not oq4["passed"]

    def test_oq5_passes_no_files(self, tmp_path: Path):
        """OQ-5 should pass when no file-level data is present."""
        analysis = _make_envelope_analysis()
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = OutputQualityChecks(output_dir)
        results = checker.run_all()
        oq5 = next(r for r in results if r["check"] == "OQ-5")
        assert oq5["passed"]

    def test_oq5_fails_missing_file_field(self, tmp_path: Path):
        """OQ-5 should fail when file records miss required fields."""
        analysis = _make_envelope_analysis(files=[{"path": "a.py"}])  # missing 'author' and 'loc'
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = OutputQualityChecks(output_dir)
        results = checker.run_all()
        oq5 = next(r for r in results if r["check"] == "OQ-5")
        assert not oq5["passed"]

    def test_oq6_fails_invalid_json_file(self, tmp_path: Path):
        """OQ-6 should fail when a JSON file is malformed."""
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        (output_dir / "bad.json").write_text("{not valid")
        # Need at least one analysis for earlier checks
        analysis = _make_envelope_analysis()
        (output_dir / "combined_analysis.json").write_text(json.dumps({"repo": analysis}))

        checker = OutputQualityChecks(output_dir)
        results = checker.run_all()
        oq6 = next(r for r in results if r["check"] == "OQ-6")
        assert not oq6["passed"]

    def test_oq6_passes_valid_json_files(self, tmp_path: Path):
        """OQ-6 should pass when all JSON files are valid."""
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        analysis = _make_envelope_analysis()
        (output_dir / "combined_analysis.json").write_text(json.dumps({"repo": analysis}))
        (output_dir / "extra.json").write_text("{}")

        checker = OutputQualityChecks(output_dir)
        results = checker.run_all()
        oq6 = next(r for r in results if r["check"] == "OQ-6")
        assert oq6["passed"]

    def test_all_checks_fail_no_analyses(self, tmp_path: Path):
        """All checks should fail or handle gracefully when no analysis data."""
        output_dir = tmp_path / "empty"
        output_dir.mkdir()

        checker = OutputQualityChecks(output_dir)
        results = checker.run_all()

        # OQ-1 to OQ-5 should fail (no analyses), OQ-6 depends on file presence
        for r in results[:5]:
            assert not r["passed"]


# =============================================================================
# AuthorshipAccuracyChecks Tests
# =============================================================================


class TestAuthorshipAccuracyChecksClass:
    """Test AuthorshipAccuracyChecks methods with mock data on disk."""

    def _make_ground_truth(self, tmp_path: Path) -> Path:
        """Create ground truth matching the default envelope data."""
        gt = {
            "test-repo": {
                "expected_total_loc": 1000,
                "expected_author_count": 2,
                "expected_top_author_loc": 700,
                "expected_bus_factor": 1,
                "expected_hhi": 0.58,
                "expected_top_two_pct": 100.0,
                "expected_authors": {"Alice": 70.0, "Bob": 30.0},
            }
        }
        gt_file = tmp_path / "gt.json"
        gt_file.write_text(json.dumps(gt))
        return gt_file

    def test_all_checks_pass_matching_data(self, tmp_path: Path):
        """All AA checks should pass when data matches ground truth."""
        analysis = _make_envelope_analysis()
        output_dir = _write_combined(tmp_path / "out", {"test-repo": analysis})
        gt_file = self._make_ground_truth(tmp_path)

        checker = AuthorshipAccuracyChecks(output_dir, gt_file)
        results = checker.run_all()

        assert len(results) == 8
        for r in results:
            assert r["passed"], f"{r['check']} failed: {r['message']}"

    def test_aa1_fails_loc_mismatch(self, tmp_path: Path):
        """AA-1 should fail when total LOC doesn't match."""
        analysis = _make_envelope_analysis(
            summary={"author_count": 2, "total_loc": 500, "hhi_index": 0.5, "bus_factor": 1, "top_author_pct": 70.0, "top_two_pct": 100.0}
        )
        output_dir = _write_combined(tmp_path / "out", {"test-repo": analysis})
        gt_file = self._make_ground_truth(tmp_path)

        checker = AuthorshipAccuracyChecks(output_dir, gt_file)
        results = checker.run_all()
        aa1 = next(r for r in results if r["check"] == "AA-1")
        assert not aa1["passed"]

    def test_aa2_fails_author_count_mismatch(self, tmp_path: Path):
        """AA-2 should fail when author count doesn't match."""
        analysis = _make_envelope_analysis(
            authors=[{"name": "Alice", "surviving_loc": 1000, "ownership_pct": 100.0}],
            summary={"author_count": 1, "total_loc": 1000, "hhi_index": 1.0, "bus_factor": 1, "top_author_pct": 100.0, "top_two_pct": 100.0}
        )
        output_dir = _write_combined(tmp_path / "out", {"test-repo": analysis})
        gt_file = self._make_ground_truth(tmp_path)

        checker = AuthorshipAccuracyChecks(output_dir, gt_file)
        results = checker.run_all()
        aa2 = next(r for r in results if r["check"] == "AA-2")
        assert not aa2["passed"]

    def test_aa5_fails_bus_factor_mismatch(self, tmp_path: Path):
        """AA-5 should fail when bus factor doesn't match."""
        analysis = _make_envelope_analysis(
            summary={"author_count": 2, "total_loc": 1000, "hhi_index": 0.58, "bus_factor": 2, "top_author_pct": 70.0, "top_two_pct": 100.0}
        )
        output_dir = _write_combined(tmp_path / "out", {"test-repo": analysis})
        gt_file = self._make_ground_truth(tmp_path)

        checker = AuthorshipAccuracyChecks(output_dir, gt_file)
        results = checker.run_all()
        aa5 = next(r for r in results if r["check"] == "AA-5")
        assert not aa5["passed"]

    def test_aa6_fails_hhi_out_of_tolerance(self, tmp_path: Path):
        """AA-6 should fail when HHI is more than 0.1 from expected."""
        analysis = _make_envelope_analysis(
            summary={"author_count": 2, "total_loc": 1000, "hhi_index": 0.9, "bus_factor": 1, "top_author_pct": 70.0, "top_two_pct": 100.0}
        )
        output_dir = _write_combined(tmp_path / "out", {"test-repo": analysis})
        gt_file = self._make_ground_truth(tmp_path)

        checker = AuthorshipAccuracyChecks(output_dir, gt_file)
        results = checker.run_all()
        aa6 = next(r for r in results if r["check"] == "AA-6")
        assert not aa6["passed"]

    def test_checks_skip_when_no_ground_truth(self, tmp_path: Path):
        """Checks should pass (skip) when ground truth file doesn't exist."""
        analysis = _make_envelope_analysis()
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})
        gt_file = tmp_path / "nonexistent.json"

        checker = AuthorshipAccuracyChecks(output_dir, gt_file)
        results = checker.run_all()

        # All should pass as "skipped"
        for r in results:
            assert r["passed"], f"{r['check']} should skip: {r['message']}"

    def test_checks_fail_no_analyses(self, tmp_path: Path):
        """All checks should fail when no analysis data."""
        output_dir = tmp_path / "empty"
        output_dir.mkdir()
        gt_file = self._make_ground_truth(tmp_path)

        checker = AuthorshipAccuracyChecks(output_dir, gt_file)
        results = checker.run_all()

        for r in results:
            assert not r["passed"]

    def test_aa8_passes_with_authors(self, tmp_path: Path):
        """AA-8 should pass when author-level attribution exists."""
        analysis = _make_envelope_analysis()
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})
        gt_file = tmp_path / "nonexistent.json"

        checker = AuthorshipAccuracyChecks(output_dir, gt_file)
        results = checker.run_all()
        aa8 = next(r for r in results if r["check"] == "AA-8")
        assert aa8["passed"]

    def test_aa4_fails_ownership_mismatch(self, tmp_path: Path):
        """AA-4 should fail when ownership pct is >5% off expected."""
        analysis = _make_envelope_analysis(
            authors=[
                {"name": "Alice", "surviving_loc": 500, "ownership_pct": 50.0},
                {"name": "Bob", "surviving_loc": 500, "ownership_pct": 50.0},
            ],
            summary={"author_count": 2, "total_loc": 1000, "hhi_index": 0.5, "bus_factor": 1, "top_author_pct": 50.0, "top_two_pct": 100.0}
        )
        output_dir = _write_combined(tmp_path / "out", {"test-repo": analysis})
        gt_file = self._make_ground_truth(tmp_path)

        checker = AuthorshipAccuracyChecks(output_dir, gt_file)
        results = checker.run_all()
        aa4 = next(r for r in results if r["check"] == "AA-4")
        assert not aa4["passed"]  # Alice expected 70%, got 50%

    def test_aa7_fails_top_two_pct_mismatch(self, tmp_path: Path):
        """AA-7 should fail when top two percentage differs by >5%."""
        analysis = _make_envelope_analysis(
            summary={"author_count": 2, "total_loc": 1000, "hhi_index": 0.58, "bus_factor": 1, "top_author_pct": 70.0, "top_two_pct": 80.0}
        )
        output_dir = _write_combined(tmp_path / "out", {"test-repo": analysis})
        gt_file = self._make_ground_truth(tmp_path)

        checker = AuthorshipAccuracyChecks(output_dir, gt_file)
        results = checker.run_all()
        aa7 = next(r for r in results if r["check"] == "AA-7")
        assert not aa7["passed"]  # Expected 100%, got 80% -> diff > 5%

    def test_nested_ground_truth_format(self, tmp_path: Path):
        """Should handle nested ground truth with 'expected' key."""
        analysis = _make_envelope_analysis()
        output_dir = _write_combined(tmp_path / "out", {"test-repo": analysis})

        gt = {
            "test-repo": {
                "expected": {
                    "expected_total_loc": 1000,
                    "expected_author_count": 2,
                },
                "description": "Nested format",
            }
        }
        gt_file = tmp_path / "gt.json"
        gt_file.write_text(json.dumps(gt))

        checker = AuthorshipAccuracyChecks(output_dir, gt_file)
        results = checker.run_all()
        aa1 = next(r for r in results if r["check"] == "AA-1")
        assert aa1["passed"]

    def test_ground_truth_skips_underscore_repos(self, tmp_path: Path):
        """Ground truth entries starting with _ should be skipped."""
        analysis = _make_envelope_analysis()
        output_dir = _write_combined(tmp_path / "out", {"test-repo": analysis})

        gt = {
            "_metadata": {"format_version": "1.0"},
            "test-repo": {
                "expected_total_loc": 1000,
                "expected_author_count": 2,
            },
        }
        gt_file = tmp_path / "gt.json"
        gt_file.write_text(json.dumps(gt))

        checker = AuthorshipAccuracyChecks(output_dir, gt_file)
        results = checker.run_all()
        # Should not crash and should still check test-repo
        aa1 = next(r for r in results if r["check"] == "AA-1")
        assert aa1["passed"]


# =============================================================================
# IntegrationFitChecks Tests
# =============================================================================


class TestIntegrationFitChecksClass:
    """Test IntegrationFitChecks methods."""

    def test_all_checks_pass_valid_envelope(self, tmp_path: Path):
        """All IF checks should pass for valid envelope data."""
        analysis = _make_envelope_analysis()
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = IntegrationFitChecks(output_dir)
        results = checker.run_all()

        assert len(results) == 4
        for r in results:
            assert r["passed"], f"{r['check']} failed: {r['message']}"

    def test_if1_passes_no_files(self, tmp_path: Path):
        """IF-1 should pass when there are no file entries (author-level only)."""
        analysis = _make_envelope_analysis()
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = IntegrationFitChecks(output_dir)
        results = checker.run_all()
        if1 = next(r for r in results if r["check"] == "IF-1")
        assert if1["passed"]

    def test_if1_fails_absolute_path(self, tmp_path: Path):
        """IF-1 should fail when a file path is absolute."""
        analysis = _make_envelope_analysis(
            files=[{"path": "/absolute/path.py", "author": "Alice", "loc": 100}]
        )
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = IntegrationFitChecks(output_dir)
        results = checker.run_all()
        if1 = next(r for r in results if r["check"] == "IF-1")
        assert not if1["passed"]

    def test_if1_fails_dotslash_path(self, tmp_path: Path):
        """IF-1 should fail when a file path starts with ./."""
        analysis = _make_envelope_analysis(
            files=[{"path": "./relative/path.py", "author": "Alice", "loc": 100}]
        )
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = IntegrationFitChecks(output_dir)
        results = checker.run_all()
        if1 = next(r for r in results if r["check"] == "IF-1")
        assert not if1["passed"]

    def test_if1_fails_backslash_path(self, tmp_path: Path):
        """IF-1 should fail when a file path contains backslashes."""
        analysis = _make_envelope_analysis(
            files=[{"path": "src\\main.py", "author": "Alice", "loc": 100}]
        )
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = IntegrationFitChecks(output_dir)
        results = checker.run_all()
        if1 = next(r for r in results if r["check"] == "IF-1")
        assert not if1["passed"]

    def test_if1_fails_dotdot_in_path(self, tmp_path: Path):
        """IF-1 should fail when a path contains .. segments."""
        analysis = _make_envelope_analysis(
            files=[{"path": "src/../etc/passwd", "author": "Alice", "loc": 100}]
        )
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = IntegrationFitChecks(output_dir)
        results = checker.run_all()
        if1 = next(r for r in results if r["check"] == "IF-1")
        assert not if1["passed"]

    def test_if1_fails_drive_letter(self, tmp_path: Path):
        """IF-1 should fail when a path has a Windows drive letter."""
        analysis = _make_envelope_analysis(
            files=[{"path": "C:Users\\file.py", "author": "Alice", "loc": 100}]
        )
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = IntegrationFitChecks(output_dir)
        results = checker.run_all()
        if1 = next(r for r in results if r["check"] == "IF-1")
        assert not if1["passed"]

    def test_if2_fails_missing_metrics(self, tmp_path: Path):
        """IF-2 should fail when required metrics are missing."""
        analysis = _make_envelope_analysis(
            summary={"author_count": 2, "total_loc": 1000}  # missing hhi_index, bus_factor
        )
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = IntegrationFitChecks(output_dir)
        results = checker.run_all()
        if2 = next(r for r in results if r["check"] == "IF-2")
        assert not if2["passed"]

    def test_if3_passes_author_level_tool(self, tmp_path: Path):
        """IF-3 should pass for author-level tool (no directory rollups)."""
        analysis = _make_envelope_analysis()
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = IntegrationFitChecks(output_dir)
        results = checker.run_all()
        if3 = next(r for r in results if r["check"] == "IF-3")
        assert if3["passed"]

    def test_if4_passes_valid_envelope(self, tmp_path: Path):
        """IF-4 should pass for valid Caldera envelope format."""
        analysis = _make_envelope_analysis()
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = IntegrationFitChecks(output_dir)
        results = checker.run_all()
        if4 = next(r for r in results if r["check"] == "IF-4")
        assert if4["passed"]

    def test_if4_fails_missing_metadata_fields(self, tmp_path: Path):
        """IF-4 should fail when required metadata fields are missing."""
        analysis = _make_envelope_analysis()
        del analysis["metadata"]["run_id"]
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = IntegrationFitChecks(output_dir)
        results = checker.run_all()
        if4 = next(r for r in results if r["check"] == "IF-4")
        assert not if4["passed"]

    def test_if4_fails_missing_data_fields(self, tmp_path: Path):
        """IF-4 should fail when required data fields are missing."""
        analysis = _make_envelope_analysis()
        del analysis["data"]["authors"]
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = IntegrationFitChecks(output_dir)
        results = checker.run_all()
        if4 = next(r for r in results if r["check"] == "IF-4")
        assert not if4["passed"]

    def test_all_checks_fail_no_analyses(self, tmp_path: Path):
        """All checks should fail when no analysis data."""
        output_dir = tmp_path / "empty"
        output_dir.mkdir()

        checker = IntegrationFitChecks(output_dir)
        results = checker.run_all()

        for r in results:
            assert not r["passed"]


# =============================================================================
# InstallationChecks Tests
# =============================================================================


class TestInstallationChecksClass:
    """Test InstallationChecks methods."""

    def test_in1_passes_when_gitfame_installed(self):
        """IN-1 should pass when gitfame imports successfully."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "3.1.1\n"

        with patch("checks.installation.subprocess.run", return_value=mock_result):
            checker = InstallationChecks()
            results = checker.run_all()

        in1 = next(r for r in results if r["check"] == "IN-1")
        assert in1["passed"]
        assert "3.1.1" in in1["message"]

    def test_in1_tries_alternate_import(self):
        """IN-1 should try alternate import when direct import fails."""
        call_count = 0

        def mock_run(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.returncode = 1
                result.stderr = "ImportError"
            else:
                result.returncode = 0
                result.stdout = "gitfame 3.1.1"
                result.stderr = ""
            return result

        with patch("checks.installation.subprocess.run", side_effect=mock_run):
            checker = InstallationChecks()
            results = checker.run_all()

        in1 = next(r for r in results if r["check"] == "IN-1")
        assert in1["passed"]

    def test_in1_fails_both_methods(self):
        """IN-1 should fail when both import methods fail."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "ModuleNotFoundError"
        mock_result.stdout = ""

        with patch("checks.installation.subprocess.run", return_value=mock_result):
            checker = InstallationChecks()
            results = checker.run_all()

        in1 = next(r for r in results if r["check"] == "IN-1")
        assert not in1["passed"]

    def test_in1_handles_timeout(self):
        """IN-1 should handle timeout."""
        with patch("checks.installation.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="test", timeout=10)):
            checker = InstallationChecks()
            results = checker.run_all()

        in1 = next(r for r in results if r["check"] == "IN-1")
        assert not in1["passed"]
        assert "timed out" in in1["message"].lower()

    def test_in1_handles_file_not_found(self):
        """IN-1 should handle missing Python interpreter."""
        with patch("checks.installation.subprocess.run", side_effect=FileNotFoundError):
            checker = InstallationChecks()
            results = checker.run_all()

        in1 = next(r for r in results if r["check"] == "IN-1")
        assert not in1["passed"]

    def test_in2_passes_valid_help(self):
        """IN-2 should pass when --help returns valid help text."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "usage: gitfame [-h] [--format FORMAT] [--branch BRANCH]"

        with patch("checks.installation.subprocess.run", return_value=mock_result):
            checker = InstallationChecks()
            results = checker.run_all()

        in2 = next(r for r in results if r["check"] == "IN-2")
        assert in2["passed"]

    def test_in2_fails_nonzero_exit(self):
        """IN-2 should fail when --help returns non-zero."""

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            # Check which command is being run by looking at args
            cmd_str = " ".join(str(c) for c in cmd)
            if "--help" in cmd_str:
                # IN-2 call
                result.returncode = 1
                result.stderr = "error"
                result.stdout = ""
            else:
                # IN-1 calls (import check or --version)
                result.returncode = 0
                result.stdout = "3.1.1"
                result.stderr = ""
            return result

        with patch("checks.installation.subprocess.run", side_effect=mock_run):
            checker = InstallationChecks()
            results = checker.run_all()

        in2 = next(r for r in results if r["check"] == "IN-2")
        assert not in2["passed"]

    def test_in2_handles_timeout(self):
        """IN-2 should handle timeout."""

        def mock_run(cmd, **kwargs):
            cmd_str = " ".join(str(c) for c in cmd)
            if "--help" in cmd_str:
                raise subprocess.TimeoutExpired(cmd="test", timeout=10)
            result = MagicMock()
            result.returncode = 0
            result.stdout = "3.1.1"
            result.stderr = ""
            return result

        with patch("checks.installation.subprocess.run", side_effect=mock_run):
            checker = InstallationChecks()
            results = checker.run_all()

        in2 = next(r for r in results if r["check"] == "IN-2")
        assert not in2["passed"]


# =============================================================================
# PerformanceChecks Tests
# =============================================================================


class TestPerformanceChecksClass:
    """Test PerformanceChecks methods."""

    def test_pf1_passes_fast_repo(self, tmp_path: Path):
        """PF-1 should pass when analysis completes under 5s."""
        # Create a test repo
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "test-repo"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"data": []}'
        mock_result.stderr = ""

        with patch("checks.performance.subprocess.run", return_value=mock_result), \
             patch("checks.performance.time.perf_counter", side_effect=[0.0, 1.5]):
            checker = PerformanceChecks(tmp_path / "output", tmp_path / "eval-repos")
            results = checker.run_all()

        pf1 = next(r for r in results if r["check"] == "PF-1")
        assert pf1["passed"]

    def test_pf1_fails_slow_repo(self, tmp_path: Path):
        """PF-1 should fail when analysis takes > 5s."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "test-repo"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"data": []}'
        mock_result.stderr = ""

        with patch("checks.performance.subprocess.run", return_value=mock_result), \
             patch("checks.performance.time.perf_counter", side_effect=[0.0, 6.0]):
            checker = PerformanceChecks(tmp_path / "output", tmp_path / "eval-repos")
            results = checker.run_all()

        pf1 = next(r for r in results if r["check"] == "PF-1")
        assert not pf1["passed"]

    def test_pf1_fails_no_test_repo(self, tmp_path: Path):
        """PF-1 should fail when no test repository is found."""
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()

        checker = PerformanceChecks(tmp_path / "output", eval_repos)
        results = checker.run_all()
        pf1 = next(r for r in results if r["check"] == "PF-1")
        assert not pf1["passed"]

    def test_pf4_passes_consistent_runs(self, tmp_path: Path):
        """PF-4 should pass when second run is not significantly slower."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "repo"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        checker = PerformanceChecks(tmp_path / "output", tmp_path / "eval-repos")

        # Mock _run_git_fame_timed to return consistent times
        run_count = 0
        original_timed = checker._run_git_fame_timed

        def mock_timed(repo_path, timeout=120):
            nonlocal run_count
            run_count += 1
            if run_count <= 1:
                return (1.0, 0, "")
            else:
                return (1.2, 0, "")

        checker._run_git_fame_timed = mock_timed
        result = checker._check_incremental_speed()
        assert result["passed"]

    def test_find_test_repo_tries_multiple_locations(self, tmp_path: Path):
        """_find_test_repo should check synthetic, real, and root dirs."""
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()
        # Create a repo in the root
        repo = eval_repos / "my-repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        checker = PerformanceChecks(tmp_path / "output", eval_repos)
        found = checker._find_test_repo()
        assert found is not None
        assert found.name == "my-repo"


# =============================================================================
# ReliabilityChecks Tests
# =============================================================================


class TestReliabilityChecksClass:
    """Test ReliabilityChecks methods."""

    def test_rl1_passes_deterministic(self, tmp_path: Path):
        """RL-1 should pass when two runs produce identical output."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "repo"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        output = json.dumps({"data": [["Alice", 100]], "columns": ["Author", "loc"]})
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = output
        mock_result.stderr = ""

        with patch("checks.reliability.subprocess.run", return_value=mock_result):
            checker = ReliabilityChecks(tmp_path / "out", tmp_path / "eval-repos")
            results = checker.run_all()

        rl1 = next(r for r in results if r["check"] == "RL-1")
        assert rl1["passed"]

    def test_rl1_fails_no_repos(self, tmp_path: Path):
        """RL-1 should fail when no test repositories found."""
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()

        checker = ReliabilityChecks(tmp_path / "out", eval_repos)
        results = checker.run_all()
        rl1 = next(r for r in results if r["check"] == "RL-1")
        assert not rl1["passed"]

    def test_rl2_skips_no_empty_repo(self, tmp_path: Path):
        """RL-2 should skip (pass) when no empty repo exists."""
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()
        (eval_repos / "synthetic").mkdir()

        output_dir = tmp_path / "out"
        output_dir.mkdir()

        checker = ReliabilityChecks(output_dir, eval_repos)
        results = checker.run_all()
        rl2 = next(r for r in results if r["check"] == "RL-2")
        assert rl2["passed"]  # Skipped

    def test_rl2_passes_empty_repo_graceful(self, tmp_path: Path):
        """RL-2 should pass when empty repo returns no data."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "empty"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"data": [], "columns": []}'
        mock_result.stderr = ""

        with patch("checks.reliability.subprocess.run", return_value=mock_result):
            checker = ReliabilityChecks(tmp_path / "out", tmp_path / "eval-repos")
            results = checker.run_all()

        rl2 = next(r for r in results if r["check"] == "RL-2")
        assert rl2["passed"]

    def test_rl3_skips_no_single_author_repo(self, tmp_path: Path):
        """RL-3 should skip (pass) when no single-author repo exists."""
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()
        (eval_repos / "synthetic").mkdir()

        output_dir = tmp_path / "out"
        output_dir.mkdir()

        checker = ReliabilityChecks(output_dir, eval_repos)
        results = checker.run_all()
        rl3 = next(r for r in results if r["check"] == "RL-3")
        assert rl3["passed"]

    def test_rl3_passes_single_author(self, tmp_path: Path):
        """RL-3 should pass when single-author repo returns 1 author."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "single-author"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "data": [["Alice", 500, 10, 5]],
            "columns": ["Author", "loc", "coms", "fils"],
        })
        mock_result.stderr = ""

        with patch("checks.reliability.subprocess.run", return_value=mock_result):
            checker = ReliabilityChecks(tmp_path / "out", tmp_path / "eval-repos")
            results = checker.run_all()

        rl3 = next(r for r in results if r["check"] == "RL-3")
        assert rl3["passed"]

    def test_rl3_fails_multiple_authors_from_single_author_repo(self, tmp_path: Path):
        """RL-3 should fail if single-author repo returns multiple authors."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "single-author"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "data": [["Alice", 300, 5, 3], ["Bob", 200, 3, 2]],
            "columns": ["Author", "loc", "coms", "fils"],
        })
        mock_result.stderr = ""

        with patch("checks.reliability.subprocess.run", return_value=mock_result):
            checker = ReliabilityChecks(tmp_path / "out", tmp_path / "eval-repos")
            results = checker.run_all()

        rl3 = next(r for r in results if r["check"] == "RL-3")
        assert not rl3["passed"]

    def test_rl4_skips_no_rename_repo(self, tmp_path: Path):
        """RL-4 should skip (pass) when no rename test repo exists."""
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()
        (eval_repos / "synthetic").mkdir()

        checker = ReliabilityChecks(tmp_path / "out", eval_repos)
        results = checker.run_all()
        rl4 = next(r for r in results if r["check"] == "RL-4")
        assert rl4["passed"]

    def test_rl4_passes_with_rename_repo(self, tmp_path: Path):
        """RL-4 should pass when rename repo produces data."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "rename-test"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "data": [["Alice", 200, 5, 3]],
            "columns": ["Author", "loc", "coms", "fils"],
        })
        mock_result.stderr = ""

        with patch("checks.reliability.subprocess.run", return_value=mock_result):
            checker = ReliabilityChecks(tmp_path / "out", tmp_path / "eval-repos")
            results = checker.run_all()

        rl4 = next(r for r in results if r["check"] == "RL-4")
        assert rl4["passed"]
