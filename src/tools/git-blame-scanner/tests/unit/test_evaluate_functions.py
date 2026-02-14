"""Unit tests for git-blame-scanner evaluate.py functions.

Tests cover the uncovered logic in evaluate.py:
- run_checks: dispatching check functions and collecting results
- main: CLI entry point with file I/O
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.evaluate import load_checks, run_checks, compute_summary, main


# ---------------------------------------------------------------------------
# run_checks
# ---------------------------------------------------------------------------

class TestRunChecks:
    """Tests for run_checks dispatcher."""

    def _make_output(self, files: list[dict] | None = None) -> dict:
        """Build a minimal valid output envelope."""
        return {
            "metadata": {
                "tool_name": "git-blame-scanner",
                "tool_version": "1.0.0",
                "run_id": "r1",
                "repo_id": "test",
                "branch": "main",
                "commit": "a" * 40,
                "timestamp": "2025-01-01T00:00:00Z",
                "schema_version": "1.0.0",
            },
            "data": {
                "files": files or [
                    {
                        "path": "src/main.py",
                        "total_lines": 100,
                        "unique_authors": 2,
                        "top_author": "alice@ex.com",
                        "top_author_lines": 80,
                        "top_author_pct": 80.0,
                        "last_modified": "2025-01-01",
                        "churn_30d": 1,
                        "churn_90d": 3,
                    },
                ],
                "authors": [
                    {
                        "author_email": "alice@ex.com",
                        "total_files": 1,
                        "total_lines": 80,
                        "exclusive_files": 0,
                        "avg_ownership_pct": 80.0,
                    },
                ],
                "summary": {
                    "total_files_analyzed": 1,
                    "total_authors": 1,
                    "single_author_files": 0,
                    "single_author_pct": 0.0,
                    "high_concentration_files": 1,
                    "high_concentration_pct": 100.0,
                    "stale_files_90d": 0,
                    "knowledge_silo_count": 0,
                    "avg_authors_per_file": 2.0,
                },
                "knowledge_silos": [],
            },
        }

    def test_run_checks_returns_list_of_dicts(self):
        """run_checks should return a list of dict results."""
        output = self._make_output()
        results = run_checks(output, None)
        assert isinstance(results, list)
        assert len(results) > 0
        for r in results:
            assert isinstance(r, dict)
            assert "check_id" in r
            assert "status" in r

    def test_run_checks_all_pass_for_valid_output(self):
        """With valid output all standard checks should pass."""
        output = self._make_output()
        results = run_checks(output, None)
        statuses = {r["status"] for r in results}
        # Should not have any failures for clean data
        assert "fail" not in statuses

    def test_run_checks_handles_exception_in_check(self):
        """If a check function raises, it should produce an error result."""
        def bad_check(output, gt):
            raise ValueError("kaboom")

        fake_module = MagicMock()
        fake_module.__dir__ = MagicMock(return_value=["check_broken"])
        fake_module.check_broken = bad_check

        with patch("scripts.evaluate.load_checks", return_value=[("bad", fake_module)]):
            results = run_checks({}, None)

        assert len(results) == 1
        assert results[0]["status"] == "error"
        assert "kaboom" in results[0]["message"]

    def test_run_checks_handles_list_returning_check(self):
        """Checks that return a list get extended into results."""
        def list_check(output, gt):
            return [
                {"check_id": "x.a", "status": "pass", "message": "ok"},
                {"check_id": "x.b", "status": "warn", "message": "meh"},
            ]

        fake_module = MagicMock()
        fake_module.__dir__ = MagicMock(return_value=["check_multi"])
        fake_module.check_multi = list_check

        with patch("scripts.evaluate.load_checks", return_value=[("multi", fake_module)]):
            results = run_checks({}, None)

        assert len(results) == 2
        assert results[0]["check_id"] == "x.a"
        assert results[1]["check_id"] == "x.b"

    def test_run_checks_handles_dict_returning_check(self):
        """Checks that return a single dict get appended."""
        def dict_check(output, gt):
            return {"check_id": "y.a", "status": "pass", "message": "single"}

        fake_module = MagicMock()
        fake_module.__dir__ = MagicMock(return_value=["check_single"])
        fake_module.check_single = dict_check

        with patch("scripts.evaluate.load_checks", return_value=[("single", fake_module)]):
            results = run_checks({}, None)

        assert len(results) == 1
        assert results[0]["check_id"] == "y.a"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

class TestEvaluateMain:
    """Tests for the evaluate CLI entry point."""

    def test_no_output_json_returns_1(self, tmp_path: Path):
        """If no output.json is found, main returns 1."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        gt_dir = tmp_path / "gt"
        gt_dir.mkdir()
        out_file = tmp_path / "eval.json"

        args = [
            "--results-dir", str(results_dir),
            "--ground-truth-dir", str(gt_dir),
            "--output", str(out_file),
        ]
        with patch("sys.argv", ["evaluate.py"] + args):
            rc = main()
        assert rc == 1

    def test_finds_output_in_subdirectory(self, tmp_path: Path):
        """output.json in a subdirectory is found and processed."""
        results_dir = tmp_path / "results"
        sub_dir = results_dir / "run-abc"
        sub_dir.mkdir(parents=True)

        output_data = {
            "metadata": {
                "tool_name": "git-blame-scanner",
                "tool_version": "1.0.0",
                "run_id": "r1",
                "repo_id": "test",
                "branch": "main",
                "commit": "a" * 40,
                "timestamp": "2025-01-01T00:00:00Z",
                "schema_version": "1.0.0",
            },
            "data": {
                "files": [
                    {
                        "path": "f.py",
                        "total_lines": 10,
                        "unique_authors": 1,
                        "top_author": "a@b.com",
                        "top_author_lines": 10,
                        "top_author_pct": 100.0,
                        "last_modified": "2025-01-01",
                        "churn_30d": 0,
                        "churn_90d": 0,
                    },
                ],
                "authors": [
                    {
                        "author_email": "a@b.com",
                        "total_files": 1,
                        "total_lines": 10,
                        "exclusive_files": 1,
                        "avg_ownership_pct": 100.0,
                    },
                ],
                "summary": {
                    "total_files_analyzed": 1,
                    "total_authors": 1,
                    "single_author_files": 1,
                    "single_author_pct": 100.0,
                    "high_concentration_files": 1,
                    "high_concentration_pct": 100.0,
                    "stale_files_90d": 1,
                    "knowledge_silo_count": 0,
                    "avg_authors_per_file": 1.0,
                },
                "knowledge_silos": [],
            },
        }
        (sub_dir / "output.json").write_text(json.dumps(output_data))

        gt_dir = tmp_path / "gt"
        gt_dir.mkdir()
        out_file = tmp_path / "eval.json"

        args = [
            "--results-dir", str(results_dir),
            "--ground-truth-dir", str(gt_dir),
            "--output", str(out_file),
        ]
        with patch("sys.argv", ["evaluate.py"] + args):
            rc = main()

        assert out_file.exists()
        report = json.loads(out_file.read_text())
        assert "decision" in report
        assert "score" in report
        assert "checks" in report

    def test_ground_truth_loaded_when_present(self, tmp_path: Path):
        """Ground truth file is loaded and passed to checks."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        output_data = {
            "metadata": {
                "tool_name": "git-blame-scanner",
                "tool_version": "1.0.0",
                "run_id": "r1",
                "repo_id": "test",
                "branch": "main",
                "commit": "a" * 40,
                "timestamp": "2025-01-01T00:00:00Z",
                "schema_version": "1.0.0",
            },
            "data": {
                "files": [],
                "authors": [],
                "summary": {
                    "total_files_analyzed": 0,
                    "total_authors": 0,
                    "single_author_files": 0,
                    "single_author_pct": 0,
                    "high_concentration_files": 0,
                    "high_concentration_pct": 0,
                    "stale_files_90d": 0,
                    "knowledge_silo_count": 0,
                    "avg_authors_per_file": 0,
                },
                "knowledge_silos": [],
            },
        }
        (results_dir / "output.json").write_text(json.dumps(output_data))

        gt_dir = tmp_path / "gt"
        gt_dir.mkdir()
        gt_data = {"expected_files": 5}
        (gt_dir / "synthetic.json").write_text(json.dumps(gt_data))

        out_file = tmp_path / "eval.json"

        args = [
            "--results-dir", str(results_dir),
            "--ground-truth-dir", str(gt_dir),
            "--output", str(out_file),
        ]

        captured_gt = {}

        original_run_checks = run_checks

        def spy_run_checks(output, ground_truth):
            captured_gt["gt"] = ground_truth
            return original_run_checks(output, ground_truth)

        with patch("sys.argv", ["evaluate.py"] + args), \
             patch("scripts.evaluate.run_checks", side_effect=spy_run_checks):
            main()

        assert captured_gt["gt"] == {"expected_files": 5}
