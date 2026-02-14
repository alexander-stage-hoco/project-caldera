"""Unit tests for dependensee evaluate script.

Covers: check loading, check dispatching, summary computation,
scorecard generation, and the main() entry point.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.evaluate import (
    compute_summary,
    generate_scorecard,
    load_checks,
    run_checks,
)


# ---------------------------------------------------------------------------
# load_checks
# ---------------------------------------------------------------------------

class TestLoadChecks:
    def test_loads_at_least_four_modules(self) -> None:
        checks = load_checks()
        names = [name for name, _mod in checks]
        assert len(checks) >= 4
        assert "accuracy" in names
        assert "coverage" in names
        assert "output_quality" in names
        assert "performance" in names

    def test_skips_dunder_files(self) -> None:
        checks = load_checks()
        names = [name for name, _mod in checks]
        assert "__init__" not in names

    def test_modules_have_check_functions(self) -> None:
        checks = load_checks()
        for name, module in checks:
            funcs = [a for a in dir(module) if a.startswith("check_")]
            assert len(funcs) > 0, f"{name} has no check_* functions"


# ---------------------------------------------------------------------------
# run_checks
# ---------------------------------------------------------------------------

SAMPLE_OUTPUT = {
    "metadata": {
        "tool_name": "dependensee",
        "tool_version": "1.0.0",
        "run_id": "test-run",
        "repo_id": "test-repo",
        "branch": "main",
        "commit": "a" * 40,
        "timestamp": "2025-01-01T00:00:00Z",
        "schema_version": "1.0.0",
    },
    "data": {
        "tool": "dependensee",
        "tool_version": "1.0.0",
        "projects": [
            {
                "name": "App",
                "path": "src/App/App.csproj",
                "target_framework": "net8.0",
                "project_references": ["src/Core/Core.csproj"],
                "package_references": [{"name": "Newtonsoft.Json", "version": "13.0.3"}],
            },
            {
                "name": "Core",
                "path": "src/Core/Core.csproj",
                "target_framework": "net8.0",
                "project_references": [],
                "package_references": [],
            },
        ],
        "dependency_graph": {
            "nodes": [
                {"id": "src/App/App.csproj", "name": "App", "type": "project", "target_framework": "net8.0"},
                {"id": "src/Core/Core.csproj", "name": "Core", "type": "project", "target_framework": "net8.0"},
                {"id": "nuget:Newtonsoft.Json", "name": "Newtonsoft.Json", "type": "package", "version": "13.0.3"},
            ],
            "edges": [
                {"source": "src/App/App.csproj", "target": "src/Core/Core.csproj", "type": "project_reference"},
                {"source": "src/App/App.csproj", "target": "nuget:Newtonsoft.Json", "type": "package_reference"},
            ],
        },
        "circular_dependencies": [],
        "summary": {
            "project_count": 2,
            "package_count": 1,
            "reference_count": 1,
            "circular_dependency_count": 0,
        },
    },
}


class TestRunChecks:
    def test_returns_list(self) -> None:
        results = run_checks(SAMPLE_OUTPUT, None)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_all_results_have_check_id(self) -> None:
        results = run_checks(SAMPLE_OUTPUT, None)
        for r in results:
            assert "check_id" in r
            assert "status" in r

    def test_no_ground_truth_still_passes(self) -> None:
        results = run_checks(SAMPLE_OUTPUT, None)
        statuses = {r["status"] for r in results}
        # Without ground truth accuracy checks skip (pass), everything else should pass
        assert "fail" not in statuses

    def test_with_matching_ground_truth(self) -> None:
        gt = {
            "expected": {
                "project_count": 2,
                "projects": [
                    {
                        "path": "src/App/App.csproj",
                        "target_framework": "net8.0",
                        "project_references": ["src/Core/Core.csproj"],
                        "package_references": [{"name": "Newtonsoft.Json"}],
                    },
                    {
                        "path": "src/Core/Core.csproj",
                        "target_framework": "net8.0",
                        "project_references": [],
                        "package_references": [],
                    },
                ],
                "circular_dependency_count": 0,
            },
        }
        results = run_checks(SAMPLE_OUTPUT, gt)
        statuses = {r["status"] for r in results}
        assert "fail" not in statuses

    def test_exception_in_check_produces_error_result(self) -> None:
        """If a check_* function raises, run_checks captures it as 'error'."""
        bad_module = MagicMock()
        bad_module.__name__ = "bad"

        def bad_check(output, gt):
            raise ValueError("boom")

        # Mock load_checks to return a module with a failing check
        bad_module.check_explode = bad_check
        # dir() needs to return the attr name
        bad_module.__dir__ = lambda self=None: ["check_explode"]

        with patch("scripts.evaluate.load_checks", return_value=[("bad", bad_module)]):
            with patch("builtins.dir", return_value=["check_explode"]):
                # Can't easily patch dir() per-object; use the real run_checks logic
                pass

        # Simpler approach: directly test the exception path via a real module mock
        import types
        mod = types.ModuleType("fake_checks")
        mod.check_kaboom = lambda o, g: (_ for _ in ()).throw(RuntimeError("kaboom"))
        # Actually create a proper raising function
        def raising_check(output, gt):
            raise RuntimeError("kaboom")
        mod.check_kaboom = raising_check

        with patch("scripts.evaluate.load_checks", return_value=[("fake", mod)]):
            results = run_checks(SAMPLE_OUTPUT, None)

        error_results = [r for r in results if r["status"] == "error"]
        assert len(error_results) == 1
        assert "kaboom" in error_results[0]["message"]

    def test_check_returning_list_is_extended(self) -> None:
        """If a check returns a list of dicts, they are all collected."""
        import types
        mod = types.ModuleType("multi_checks")

        def check_multi(output, gt):
            return [
                {"check_id": "multi.a", "status": "pass", "message": "ok"},
                {"check_id": "multi.b", "status": "warn", "message": "meh"},
            ]
        mod.check_multi = check_multi

        with patch("scripts.evaluate.load_checks", return_value=[("multi", mod)]):
            results = run_checks(SAMPLE_OUTPUT, None)
        ids = [r["check_id"] for r in results]
        assert "multi.a" in ids
        assert "multi.b" in ids


# ---------------------------------------------------------------------------
# compute_summary
# ---------------------------------------------------------------------------

class TestComputeSummary:
    def test_all_pass(self) -> None:
        results = [
            {"check_id": "a", "status": "pass"},
            {"check_id": "b", "status": "pass"},
        ]
        s = compute_summary(results)
        assert s["total"] == 2
        assert s["passed"] == 2
        assert s["failed"] == 0
        assert s["score"] == 1.0
        assert s["decision"] == "PASS"

    def test_one_fail(self) -> None:
        results = [
            {"check_id": "a", "status": "pass"},
            {"check_id": "b", "status": "fail"},
        ]
        s = compute_summary(results)
        assert s["decision"] == "FAIL"
        assert s["score"] == 0.5

    def test_one_error(self) -> None:
        results = [
            {"check_id": "a", "status": "pass"},
            {"check_id": "b", "status": "error"},
        ]
        s = compute_summary(results)
        assert s["decision"] == "FAIL"
        assert s["errored"] == 1

    def test_warn_only_passes(self) -> None:
        results = [
            {"check_id": "a", "status": "pass"},
            {"check_id": "b", "status": "warn"},
        ]
        s = compute_summary(results)
        assert s["decision"] == "PASS"
        assert s["warned"] == 1

    def test_empty_results(self) -> None:
        s = compute_summary([])
        assert s["total"] == 0
        assert s["score"] == 0.0
        assert s["decision"] == "PASS"  # 0 fails → PASS


# ---------------------------------------------------------------------------
# generate_scorecard
# ---------------------------------------------------------------------------

class TestGenerateScorecard:
    def test_writes_markdown_file(self, tmp_path: Path) -> None:
        summary = {"score": 0.75, "decision": "FAIL", "passed": 3, "total": 4}
        results = [
            {"check_id": "a.one", "status": "pass", "message": "good"},
            {"check_id": "b.two", "status": "fail", "message": "bad"},
        ]
        generate_scorecard(summary, results, tmp_path)
        scorecard = tmp_path / "scorecard.md"
        assert scorecard.exists()

        content = scorecard.read_text()
        assert "75.0%" in content
        assert "FAIL" in content
        assert "a.one" in content
        assert "b.two" in content
        assert "| a.one |" in content

    def test_scorecard_contains_header(self, tmp_path: Path) -> None:
        summary = {"score": 1.0, "decision": "PASS", "passed": 2, "total": 2}
        results = [{"check_id": "x", "status": "pass", "message": "ok"}]
        generate_scorecard(summary, results, tmp_path)
        content = (tmp_path / "scorecard.md").read_text()
        assert "# dependensee Evaluation Scorecard" in content
        assert "## Check Details" in content


# ---------------------------------------------------------------------------
# main() entry point
# ---------------------------------------------------------------------------

class TestMain:
    def test_main_with_valid_output(self, tmp_path: Path) -> None:
        from scripts.evaluate import main

        results_dir = tmp_path / "results"
        results_dir.mkdir()
        (results_dir / "output.json").write_text(json.dumps(SAMPLE_OUTPUT))

        gt_dir = tmp_path / "ground_truth"
        gt_dir.mkdir()

        output_file = tmp_path / "eval" / "scorecard.json"

        with patch(
            "sys.argv",
            [
                "evaluate.py",
                "--results-dir", str(results_dir),
                "--ground-truth-dir", str(gt_dir),
                "--output", str(output_file),
            ],
        ):
            ret = main()

        assert ret == 0
        assert output_file.exists()
        report = json.loads(output_file.read_text())
        assert "decision" in report
        assert "score" in report
        assert "checks" in report
        assert "summary" in report
        assert "timestamp" in report
        # Scorecard should also be written
        assert (tmp_path / "eval" / "scorecard.md").exists()

    def test_main_finds_output_in_subdir(self, tmp_path: Path) -> None:
        from scripts.evaluate import main

        results_dir = tmp_path / "results"
        sub = results_dir / "run-001"
        sub.mkdir(parents=True)
        (sub / "output.json").write_text(json.dumps(SAMPLE_OUTPUT))

        gt_dir = tmp_path / "ground_truth"
        gt_dir.mkdir()

        output_file = tmp_path / "eval" / "scorecard.json"

        with patch(
            "sys.argv",
            [
                "evaluate.py",
                "--results-dir", str(results_dir),
                "--ground-truth-dir", str(gt_dir),
                "--output", str(output_file),
            ],
        ):
            ret = main()

        assert ret == 0

    def test_main_missing_output_returns_1(self, tmp_path: Path) -> None:
        from scripts.evaluate import main

        results_dir = tmp_path / "results"
        results_dir.mkdir()
        gt_dir = tmp_path / "ground_truth"
        gt_dir.mkdir()
        output_file = tmp_path / "eval" / "scorecard.json"

        with patch(
            "sys.argv",
            [
                "evaluate.py",
                "--results-dir", str(results_dir),
                "--ground-truth-dir", str(gt_dir),
                "--output", str(output_file),
            ],
        ):
            ret = main()

        assert ret == 1

    def test_main_loads_ground_truth_by_scenario(self, tmp_path: Path) -> None:
        """Ground truth is loaded based on repo_path in metadata."""
        from scripts.evaluate import main

        output_with_scenario = dict(SAMPLE_OUTPUT)
        output_with_scenario["metadata"] = dict(SAMPLE_OUTPUT["metadata"])
        output_with_scenario["metadata"]["repo_path"] = "eval-repos/synthetic"

        results_dir = tmp_path / "results"
        results_dir.mkdir()
        (results_dir / "output.json").write_text(json.dumps(output_with_scenario))

        gt_dir = tmp_path / "ground_truth"
        gt_dir.mkdir()
        gt = {
            "expected": {
                "project_count": 2,
                "projects": [
                    {
                        "path": "src/App/App.csproj",
                        "target_framework": "net8.0",
                        "project_references": ["src/Core/Core.csproj"],
                        "package_references": [{"name": "Newtonsoft.Json"}],
                    },
                    {
                        "path": "src/Core/Core.csproj",
                        "target_framework": "net8.0",
                        "project_references": [],
                        "package_references": [],
                    },
                ],
                "circular_dependency_count": 0,
            },
        }
        (gt_dir / "synthetic.json").write_text(json.dumps(gt))

        output_file = tmp_path / "eval" / "scorecard.json"

        with patch(
            "sys.argv",
            [
                "evaluate.py",
                "--results-dir", str(results_dir),
                "--ground-truth-dir", str(gt_dir),
                "--output", str(output_file),
            ],
        ):
            ret = main()

        assert ret == 0
