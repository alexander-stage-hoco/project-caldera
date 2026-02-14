"""Unit tests for dotcover evaluate script.

Tests cover:
- load_checks: dynamic module loading
- run_checks: dispatching check_* functions, error handling
- compute_summary: counting pass/fail/warn/error, score, decision
- determine_decision: threshold-based decision strings
- generate_scorecard_json: category grouping, dimensions, critical failures
- generate_scorecard_md: markdown rendering
- save_scorecards: file I/O
- main: CLI argument parsing, end-to-end flow
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# load_checks
# ---------------------------------------------------------------------------

class TestLoadChecks:
    """Test dynamic check module loading."""

    def test_loads_at_least_one_module(self):
        from scripts.evaluate import load_checks
        checks = load_checks()
        assert len(checks) > 0

    def test_each_entry_is_name_module_tuple(self):
        from scripts.evaluate import load_checks
        checks = load_checks()
        for name, module in checks:
            assert isinstance(name, str)
            assert hasattr(module, "__name__")

    def test_skips_dunder_files(self):
        from scripts.evaluate import load_checks
        checks = load_checks()
        names = [name for name, _ in checks]
        assert "__init__" not in names

    def test_known_modules_loaded(self):
        from scripts.evaluate import load_checks
        checks = load_checks()
        names = [name for name, _ in checks]
        assert "accuracy" in names
        assert "coverage" in names
        assert "invariants" in names
        assert "performance" in names


# ---------------------------------------------------------------------------
# run_checks
# ---------------------------------------------------------------------------

class TestRunChecks:
    """Test check dispatching and error handling."""

    def test_collects_dict_results(self):
        from scripts.evaluate import run_checks
        output = {
            "data": {
                "summary": {"covered_statements": 5, "total_statements": 10, "statement_coverage_pct": 50.0},
                "assemblies": [],
                "types": [],
                "methods": [],
            },
        }
        results = run_checks(output, None)
        assert len(results) > 0
        for r in results:
            assert "check_id" in r
            assert "status" in r

    def test_handles_check_returning_list(self):
        """Invariant checks return lists; verify they are flattened."""
        from scripts.evaluate import run_checks
        output = {
            "data": {
                "summary": {"covered_statements": 5, "total_statements": 10, "statement_coverage_pct": 50.0},
                "assemblies": [],
                "types": [],
                "methods": [],
            },
        }
        results = run_checks(output, None)
        # invariants module returns lists, which get extended into results
        invariant_results = [r for r in results if r["check_id"].startswith("invariants.")]
        assert len(invariant_results) > 0

    def test_exception_in_check_produces_error_result(self):
        from scripts.evaluate import run_checks

        # Create a module with a failing check
        fake_module = MagicMock()
        failing_fn = MagicMock(side_effect=RuntimeError("boom"))
        failing_fn.__name__ = "check_broken"
        fake_module.__dir__ = lambda self: ["check_broken"]
        # Make getattr work
        type(fake_module).check_broken = failing_fn

        with patch("scripts.evaluate.load_checks", return_value=[("fake", fake_module)]):
            # Need dir() to return check_broken
            fake_module.__dir__ = MagicMock(return_value=["check_broken"])
            with patch("scripts.evaluate.dir", return_value=["check_broken"]):
                results = run_checks({}, None)

        error_results = [r for r in results if r["status"] == "error"]
        assert len(error_results) >= 1
        assert "boom" in error_results[0]["message"]


# ---------------------------------------------------------------------------
# compute_summary
# ---------------------------------------------------------------------------

class TestComputeSummary:
    """Test summary statistics computation."""

    def test_all_pass(self):
        from scripts.evaluate import compute_summary
        results = [
            {"check_id": "a", "status": "pass"},
            {"check_id": "b", "status": "pass"},
        ]
        summary = compute_summary(results)
        assert summary["total"] == 2
        assert summary["passed"] == 2
        assert summary["failed"] == 0
        assert summary["score"] == 1.0
        assert summary["decision"] == "PASS"

    def test_mixed_results(self):
        from scripts.evaluate import compute_summary
        results = [
            {"check_id": "a", "status": "pass"},
            {"check_id": "b", "status": "fail"},
            {"check_id": "c", "status": "warn"},
            {"check_id": "d", "status": "error"},
        ]
        summary = compute_summary(results)
        assert summary["total"] == 4
        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert summary["warned"] == 1
        assert summary["errored"] == 1
        assert summary["score"] == 0.25
        assert summary["decision"] == "FAIL"

    def test_empty_results(self):
        from scripts.evaluate import compute_summary
        summary = compute_summary([])
        assert summary["total"] == 0
        assert summary["score"] == 0.0
        assert summary["decision"] == "PASS"  # 0 failed, 0 errored -> PASS

    def test_only_warnings(self):
        from scripts.evaluate import compute_summary
        results = [
            {"check_id": "a", "status": "warn"},
            {"check_id": "b", "status": "warn"},
        ]
        summary = compute_summary(results)
        assert summary["passed"] == 0
        assert summary["warned"] == 2
        assert summary["decision"] == "PASS"  # no failures or errors


# ---------------------------------------------------------------------------
# determine_decision
# ---------------------------------------------------------------------------

class TestDetermineDecision:
    """Test threshold-based decision strings."""

    def test_strong_pass(self):
        from scripts.evaluate import determine_decision
        assert determine_decision(1.0) == "STRONG_PASS"
        assert determine_decision(0.9) == "STRONG_PASS"
        assert determine_decision(0.8) == "STRONG_PASS"

    def test_pass(self):
        from scripts.evaluate import determine_decision
        assert determine_decision(0.75) == "PASS"
        assert determine_decision(0.7) == "PASS"

    def test_weak_pass(self):
        from scripts.evaluate import determine_decision
        assert determine_decision(0.65) == "WEAK_PASS"
        assert determine_decision(0.6) == "WEAK_PASS"

    def test_fail(self):
        from scripts.evaluate import determine_decision
        assert determine_decision(0.5) == "FAIL"
        assert determine_decision(0.0) == "FAIL"

    def test_boundary_values(self):
        from scripts.evaluate import determine_decision
        # 0.8 * 5 = 4.0 -> STRONG_PASS
        assert determine_decision(0.8) == "STRONG_PASS"
        # 0.7 * 5 = 3.5 -> PASS
        assert determine_decision(0.7) == "PASS"
        # 0.6 * 5 = 3.0 -> WEAK_PASS
        assert determine_decision(0.6) == "WEAK_PASS"
        # 0.59 * 5 = 2.95 -> FAIL
        assert determine_decision(0.59) == "FAIL"


# ---------------------------------------------------------------------------
# generate_scorecard_json
# ---------------------------------------------------------------------------

class TestGenerateScorecardJson:
    """Test structured scorecard JSON generation."""

    @pytest.fixture
    def results_and_summary(self):
        results = [
            {"check_id": "accuracy.check_overall", "status": "pass", "message": "OK"},
            {"check_id": "accuracy.check_assembly", "status": "fail", "message": "Missing"},
            {"check_id": "coverage.check_files", "status": "pass", "message": "5 files"},
            {"check_id": "invariants.check_bounds", "status": "pass", "message": "In range"},
        ]
        summary = {
            "total": 4,
            "passed": 3,
            "failed": 1,
            "warned": 0,
            "errored": 0,
            "score": 0.75,
        }
        return results, summary

    def test_basic_structure(self, results_and_summary):
        from scripts.evaluate import generate_scorecard_json
        results, summary = results_and_summary
        scorecard = generate_scorecard_json(results, summary)
        assert scorecard["tool"] == "dotcover"
        assert "summary" in scorecard
        assert "dimensions" in scorecard
        assert "thresholds" in scorecard

    def test_dimensions_grouped_by_category(self, results_and_summary):
        from scripts.evaluate import generate_scorecard_json
        results, summary = results_and_summary
        scorecard = generate_scorecard_json(results, summary)
        dim_names = [d["name"] for d in scorecard["dimensions"]]
        assert "Accuracy" in dim_names
        assert "Coverage" in dim_names
        assert "Invariants" in dim_names

    def test_summary_score(self, results_and_summary):
        from scripts.evaluate import generate_scorecard_json
        results, summary = results_and_summary
        scorecard = generate_scorecard_json(results, summary)
        assert scorecard["summary"]["score"] == 0.75
        assert scorecard["summary"]["score_percent"] == 75.0
        assert scorecard["summary"]["normalized_score"] == 3.75

    def test_critical_failures_extracted(self):
        from scripts.evaluate import generate_scorecard_json
        results = [
            {"check_id": "accuracy.check_critical_assembly", "status": "fail", "message": "bad"},
        ]
        summary = {"total": 1, "passed": 0, "failed": 1, "warned": 0, "errored": 0, "score": 0.0}
        scorecard = generate_scorecard_json(results, summary)
        assert len(scorecard["critical_failures"]) == 1
        assert "critical" in scorecard["critical_failures"][0]["check_id"].lower()

    def test_no_critical_failures_when_all_pass(self, results_and_summary):
        from scripts.evaluate import generate_scorecard_json
        results = [
            {"check_id": "accuracy.check_overall", "status": "pass", "message": "OK"},
        ]
        summary = {"total": 1, "passed": 1, "failed": 0, "warned": 0, "errored": 0, "score": 1.0}
        scorecard = generate_scorecard_json(results, summary)
        assert len(scorecard["critical_failures"]) == 0

    def test_check_with_no_dot_gets_general_category(self):
        from scripts.evaluate import generate_scorecard_json
        results = [{"check_id": "standalone", "status": "pass", "message": "ok"}]
        summary = {"total": 1, "passed": 1, "failed": 0, "warned": 0, "errored": 0, "score": 1.0}
        scorecard = generate_scorecard_json(results, summary)
        dim_names = [d["name"] for d in scorecard["dimensions"]]
        assert "General" in dim_names


# ---------------------------------------------------------------------------
# generate_scorecard_md
# ---------------------------------------------------------------------------

class TestGenerateScorecardMd:
    """Test markdown scorecard rendering."""

    @pytest.fixture
    def sample_scorecard(self):
        return {
            "tool": "dotcover",
            "generated_at": "2025-01-01T00:00:00Z",
            "summary": {
                "total_checks": 4,
                "passed": 3,
                "failed": 1,
                "score": 0.75,
                "score_percent": 75.0,
                "normalized_score": 3.75,
                "decision": "PASS",
            },
            "dimensions": [
                {
                    "id": "D1",
                    "name": "Accuracy",
                    "weight": 0.5,
                    "total_checks": 2,
                    "passed": 1,
                    "failed": 1,
                    "score": 2.5,
                    "weighted_score": 1.25,
                    "checks": [
                        {"check_id": "accuracy.check_overall", "name": "accuracy.check_overall",
                         "passed": True, "message": "OK"},
                        {"check_id": "accuracy.check_asm", "name": "accuracy.check_asm",
                         "passed": False, "message": "Missing assembly"},
                    ],
                },
            ],
            "critical_failures": [
                {"check_id": "accuracy.check_critical_x", "name": "accuracy.check_critical_x", "message": "bad"},
            ],
            "thresholds": {
                "STRONG_PASS": ">= 4.0",
                "PASS": ">= 3.5",
                "WEAK_PASS": ">= 3.0",
                "FAIL": "< 3.0",
            },
        }

    def test_contains_header(self, sample_scorecard):
        from scripts.evaluate import generate_scorecard_md
        md = generate_scorecard_md(sample_scorecard)
        assert "# dotCover Evaluation Scorecard" in md

    def test_contains_decision(self, sample_scorecard):
        from scripts.evaluate import generate_scorecard_md
        md = generate_scorecard_md(sample_scorecard)
        assert "PASS" in md

    def test_contains_dimensions_table(self, sample_scorecard):
        from scripts.evaluate import generate_scorecard_md
        md = generate_scorecard_md(sample_scorecard)
        assert "## Dimensions" in md
        assert "Accuracy" in md

    def test_contains_critical_failures(self, sample_scorecard):
        from scripts.evaluate import generate_scorecard_md
        md = generate_scorecard_md(sample_scorecard)
        assert "## Critical Failures" in md

    def test_contains_detailed_results(self, sample_scorecard):
        from scripts.evaluate import generate_scorecard_md
        md = generate_scorecard_md(sample_scorecard)
        assert "## Detailed Results" in md
        assert "accuracy.check_overall" in md

    def test_contains_thresholds(self, sample_scorecard):
        from scripts.evaluate import generate_scorecard_md
        md = generate_scorecard_md(sample_scorecard)
        assert "## Decision Thresholds" in md
        assert "STRONG_PASS" in md

    def test_long_messages_truncated(self, sample_scorecard):
        from scripts.evaluate import generate_scorecard_md
        # Add a check with a very long message
        sample_scorecard["dimensions"][0]["checks"].append({
            "check_id": "test.long",
            "name": "test.long",
            "passed": True,
            "message": "x" * 100,
        })
        md = generate_scorecard_md(sample_scorecard)
        assert "..." in md  # truncation indicator

    def test_no_critical_failures_section_when_empty(self):
        from scripts.evaluate import generate_scorecard_md
        scorecard = {
            "summary": {"total_checks": 1, "passed": 1, "failed": 0, "score": 1.0,
                         "score_percent": 100.0, "normalized_score": 5.0, "decision": "STRONG_PASS"},
            "dimensions": [],
            "critical_failures": [],
            "thresholds": {},
            "generated_at": "2025-01-01",
        }
        md = generate_scorecard_md(scorecard)
        assert "## Critical Failures" not in md


# ---------------------------------------------------------------------------
# save_scorecards
# ---------------------------------------------------------------------------

class TestSaveScorecards:
    """Test scorecard file I/O."""

    def test_creates_json_and_md_files(self, tmp_path: Path):
        from scripts.evaluate import save_scorecards
        results = [
            {"check_id": "accuracy.check_a", "status": "pass", "message": "ok"},
        ]
        summary = {"total": 1, "passed": 1, "failed": 0, "warned": 0, "errored": 0, "score": 1.0}
        save_scorecards(results, summary, tmp_path)
        assert (tmp_path / "scorecard.json").exists()
        assert (tmp_path / "scorecard.md").exists()

    def test_json_is_valid(self, tmp_path: Path):
        from scripts.evaluate import save_scorecards
        results = [
            {"check_id": "accuracy.check_a", "status": "pass", "message": "ok"},
        ]
        summary = {"total": 1, "passed": 1, "failed": 0, "warned": 0, "errored": 0, "score": 1.0}
        save_scorecards(results, summary, tmp_path)
        data = json.loads((tmp_path / "scorecard.json").read_text())
        assert data["tool"] == "dotcover"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

class TestEvaluateMain:
    """Test the main() CLI entry point."""

    def test_main_with_valid_output(self, tmp_path: Path):
        from scripts.evaluate import main

        # Create results dir with output.json
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        output_data = {
            "data": {
                "summary": {"covered_statements": 5, "total_statements": 10, "statement_coverage_pct": 50.0},
                "assemblies": [{"name": "A", "covered_statements": 5, "total_statements": 10, "statement_coverage_pct": 50.0}],
                "types": [{"assembly": "A", "namespace": None, "name": "Foo", "file_path": None,
                            "covered_statements": 5, "total_statements": 10, "statement_coverage_pct": 50.0}],
                "methods": [{"assembly": "A", "type_name": "Foo", "name": "Bar",
                              "covered_statements": 5, "total_statements": 10, "statement_coverage_pct": 50.0}],
            },
        }
        (results_dir / "output.json").write_text(json.dumps(output_data))

        # Create ground truth dir (no synthetic.json)
        gt_dir = tmp_path / "ground_truth"
        gt_dir.mkdir()

        # Create output path
        eval_output = tmp_path / "eval" / "results.json"

        # Create evaluation dir for scorecards
        eval_dir = Path(__file__).parent.parent.parent / "evaluation"
        eval_dir.mkdir(parents=True, exist_ok=True)

        with patch("sys.argv", [
            "evaluate.py",
            "--results-dir", str(results_dir),
            "--ground-truth-dir", str(gt_dir),
            "--output", str(eval_output),
        ]):
            exit_code = main()

        assert eval_output.exists()
        report = json.loads(eval_output.read_text())
        assert "decision" in report
        assert "score" in report
        assert "checks" in report

    def test_main_finds_output_in_subdirectory(self, tmp_path: Path):
        from scripts.evaluate import main

        results_dir = tmp_path / "results"
        sub = results_dir / "run-abc"
        sub.mkdir(parents=True)
        output_data = {
            "data": {
                "summary": {"covered_statements": 0, "total_statements": 0, "statement_coverage_pct": 0},
                "assemblies": [], "types": [], "methods": [],
            },
        }
        (sub / "output.json").write_text(json.dumps(output_data))

        gt_dir = tmp_path / "gt"
        gt_dir.mkdir()
        eval_output = tmp_path / "eval.json"

        eval_dir = Path(__file__).parent.parent.parent / "evaluation"
        eval_dir.mkdir(parents=True, exist_ok=True)

        with patch("sys.argv", [
            "evaluate.py",
            "--results-dir", str(results_dir),
            "--ground-truth-dir", str(gt_dir),
            "--output", str(eval_output),
        ]):
            exit_code = main()

        assert eval_output.exists()

    def test_main_loads_ground_truth_when_present(self, tmp_path: Path):
        from scripts.evaluate import main

        results_dir = tmp_path / "results"
        results_dir.mkdir()
        (results_dir / "output.json").write_text(json.dumps({
            "data": {
                "summary": {"covered_statements": 15, "total_statements": 20, "statement_coverage_pct": 75.0},
                "assemblies": [{"name": "Demo", "covered_statements": 15, "total_statements": 20, "statement_coverage_pct": 75.0}],
                "types": [{"assembly": "Demo", "name": "Calc", "namespace": None, "file_path": None,
                            "covered_statements": 15, "total_statements": 20, "statement_coverage_pct": 75.0}],
                "methods": [{"assembly": "Demo", "type_name": "Calc", "name": "Add",
                              "covered_statements": 15, "total_statements": 20, "statement_coverage_pct": 75.0}],
            },
        }))

        gt_dir = tmp_path / "gt"
        gt_dir.mkdir()
        gt_data = {
            "expected_coverage": {"overall_min": 50, "overall_max": 90},
            "expected_assemblies": [{"name": "Demo"}],
        }
        (gt_dir / "synthetic.json").write_text(json.dumps(gt_data))

        eval_output = tmp_path / "eval.json"

        eval_dir = Path(__file__).parent.parent.parent / "evaluation"
        eval_dir.mkdir(parents=True, exist_ok=True)

        with patch("sys.argv", [
            "evaluate.py",
            "--results-dir", str(results_dir),
            "--ground-truth-dir", str(gt_dir),
            "--output", str(eval_output),
        ]):
            exit_code = main()

        report = json.loads(eval_output.read_text())
        # With ground truth loaded, accuracy checks should reference it
        accuracy_checks = [c for c in report["checks"] if c["check_id"].startswith("accuracy.")]
        assert len(accuracy_checks) >= 2

    def test_main_returns_1_when_no_output_found(self, tmp_path: Path):
        from scripts.evaluate import main

        results_dir = tmp_path / "empty_results"
        results_dir.mkdir()
        gt_dir = tmp_path / "gt"
        gt_dir.mkdir()
        eval_output = tmp_path / "eval.json"

        with patch("sys.argv", [
            "evaluate.py",
            "--results-dir", str(results_dir),
            "--ground-truth-dir", str(gt_dir),
            "--output", str(eval_output),
        ]):
            exit_code = main()

        assert exit_code == 1
