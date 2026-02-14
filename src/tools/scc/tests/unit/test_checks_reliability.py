"""Tests for scripts/checks/reliability.py - reliability checks (RL-1 to RL-9)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from scripts.checks import CheckResult
from scripts.checks.reliability import (
    _matches_edge_case,
    run_scc_by_file,
    check_empty_file_handled,
    check_comments_only_handled,
    check_single_line_handled,
    check_unicode_handled,
    check_deep_nesting_handled,
    check_deterministic_output,
    check_all_files_detected,
    check_no_crashes,
    check_semantic_consistency,
    run_reliability_checks,
)


# ---------------------------------------------------------------------------
# Tests: _matches_edge_case helper
# ---------------------------------------------------------------------------

class TestMatchesEdgeCase:
    def test_snake_case_match(self):
        assert _matches_edge_case("src/empty_file.py", "empty_file") is True

    def test_pascal_case_match(self):
        assert _matches_edge_case("src/EmptyFile.py", "empty_file") is True

    def test_case_insensitive(self):
        assert _matches_edge_case("src/COMMENTS_ONLY.py", "comments_only") is True

    def test_no_match(self):
        assert _matches_edge_case("src/main.py", "empty_file") is False

    def test_partial_match(self):
        assert _matches_edge_case("src/deep_nesting_test.py", "deep_nesting") is True


# ---------------------------------------------------------------------------
# Tests: run_scc_by_file
# ---------------------------------------------------------------------------

class TestRunSccByFile:
    @patch("scripts.checks.reliability.subprocess.run")
    def test_success(self, mock_run, tmp_path):
        per_file_data = [
            {
                "Name": "Python",
                "Files": [
                    {"Location": "src/main.py", "Code": 50, "Comment": 10, "Blank": 5, "Lines": 65, "Complexity": 3},
                    {"Location": "src/empty_file.py", "Code": 0, "Comment": 0, "Blank": 0, "Lines": 0, "Complexity": 0},
                ]
            }
        ]
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(per_file_data),
            stderr=""
        )
        files, rc, stderr = run_scc_by_file(tmp_path, "eval-repos/synthetic")
        assert rc == 0
        assert len(files) == 2
        assert files[0]["Location"] == "src/main.py"

    @patch("scripts.checks.reliability.subprocess.run")
    def test_failure(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        files, rc, stderr = run_scc_by_file(tmp_path, "eval-repos/synthetic")
        assert rc == 1
        assert files == []


# ---------------------------------------------------------------------------
# Tests: RL-1 to RL-5 (mock subprocess to avoid needing real scc binary)
# ---------------------------------------------------------------------------

class TestEmptyFileHandled:
    @patch("scripts.checks.reliability.run_scc_by_file")
    def test_pass(self, mock_by_file, tmp_path):
        files = [
            {"Location": f"lang/empty_file.{ext}", "Code": 0}
            for ext in ["py", "cs", "js", "ts", "go", "rs", "java"]
        ]
        mock_by_file.return_value = (files, 0, "")
        result = check_empty_file_handled(tmp_path)
        assert result.passed is True
        assert result.check_id == "RL-1"

    @patch("scripts.checks.reliability.run_scc_by_file")
    def test_fail_no_empty_files(self, mock_by_file, tmp_path):
        mock_by_file.return_value = ([], 0, "")
        result = check_empty_file_handled(tmp_path)
        assert result.passed is False


class TestCommentsOnlyHandled:
    @patch("scripts.checks.reliability.run_scc_by_file")
    def test_pass(self, mock_by_file, tmp_path):
        files = [
            {"Location": f"lang/comments_only.{ext}", "Code": 0, "Comment": 10}
            for ext in ["py", "cs", "js", "ts", "go", "rs", "java"]
        ]
        mock_by_file.return_value = (files, 0, "")
        result = check_comments_only_handled(tmp_path)
        assert result.passed is True
        assert result.check_id == "RL-2"

    @patch("scripts.checks.reliability.run_scc_by_file")
    def test_fail_has_code(self, mock_by_file, tmp_path):
        files = [
            {"Location": "lang/comments_only.py", "Code": 5, "Comment": 10},
        ]
        mock_by_file.return_value = (files, 0, "")
        result = check_comments_only_handled(tmp_path)
        assert result.passed is False


class TestSingleLineHandled:
    @patch("scripts.checks.reliability.run_scc_by_file")
    def test_pass(self, mock_by_file, tmp_path):
        files = [
            {"Location": f"lang/single_line.{ext}", "Code": 1}
            for ext in ["py", "cs", "js", "ts", "go", "rs", "java"]
        ]
        mock_by_file.return_value = (files, 0, "")
        result = check_single_line_handled(tmp_path)
        assert result.passed is True
        assert result.check_id == "RL-3"


class TestUnicodeHandled:
    @patch("scripts.checks.reliability.run_scc_by_file")
    def test_pass(self, mock_by_file, tmp_path):
        files = [
            {"Location": f"lang/unicode_test.{ext}", "Lines": 20}
            for ext in ["py", "cs", "js", "ts", "go", "rs", "java"]
        ]
        mock_by_file.return_value = (files, 0, "")
        result = check_unicode_handled(tmp_path)
        assert result.passed is True
        assert result.check_id == "RL-4"


class TestDeepNestingHandled:
    @patch("scripts.checks.reliability.run_scc_by_file")
    def test_pass(self, mock_by_file, tmp_path):
        files = [
            {"Location": f"lang/deep_nesting.{ext}", "Complexity": 15}
            for ext in ["py", "cs", "js", "ts", "go", "rs", "java"]
        ]
        mock_by_file.return_value = (files, 0, "")
        result = check_deep_nesting_handled(tmp_path)
        assert result.passed is True
        assert result.check_id == "RL-5"


# ---------------------------------------------------------------------------
# Tests: RL-6 to RL-9
# ---------------------------------------------------------------------------

class TestDeterministicOutput:
    @patch("scripts.checks.reliability.subprocess.run")
    def test_pass_identical_runs(self, mock_run, tmp_path):
        data = [{"Name": "Python", "Code": 100}]
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(data),
            stderr=""
        )
        result = check_deterministic_output(tmp_path)
        assert result.passed is True
        assert result.check_id == "RL-6"

    @patch("scripts.checks.reliability.subprocess.run")
    def test_fail_different_runs(self, mock_run, tmp_path):
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            data = [{"Name": "Python", "Code": 100 + call_count[0]}]
            return MagicMock(returncode=0, stdout=json.dumps(data), stderr="")
        mock_run.side_effect = side_effect
        result = check_deterministic_output(tmp_path)
        assert result.passed is False


class TestAllFilesDetected:
    @patch("scripts.checks.reliability.run_scc_by_file")
    def test_pass(self, mock_by_file, tmp_path):
        files = [{"Location": f"file{i}.py"} for i in range(63)]
        mock_by_file.return_value = (files, 0, "")
        result = check_all_files_detected(tmp_path, expected_total=63)
        assert result.passed is True
        assert result.check_id == "RL-7"

    @patch("scripts.checks.reliability.run_scc_by_file")
    def test_fail_missing(self, mock_by_file, tmp_path):
        files = [{"Location": f"file{i}.py"} for i in range(10)]
        mock_by_file.return_value = (files, 0, "")
        result = check_all_files_detected(tmp_path, expected_total=63)
        assert result.passed is False


class TestNoCrashes:
    @patch("scripts.checks.reliability.subprocess.run")
    def test_pass(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=0, stdout="[]", stderr="")
        result = check_no_crashes(tmp_path)
        assert result.passed is True
        assert result.check_id == "RL-8"

    @patch("scripts.checks.reliability.subprocess.run")
    def test_fail_nonzero_exit(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="segfault")
        result = check_no_crashes(tmp_path)
        assert result.passed is False


class TestSemanticConsistency:
    @patch("scripts.checks.reliability.subprocess.run")
    def test_pass_identical(self, mock_run, tmp_path):
        data = [{"Name": "Python", "Code": 100, "Comment": 10, "Blank": 5, "Lines": 115, "Complexity": 8, "Count": 3}]
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(data),
            stderr=""
        )
        result = check_semantic_consistency(tmp_path)
        assert result.passed is True
        assert result.check_id == "RL-9"

    @patch("scripts.checks.reliability.subprocess.run")
    def test_fail_different_metrics(self, mock_run, tmp_path):
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            code_val = 100 if call_count[0] <= 1 else 200
            data = [{"Name": "Python", "Code": code_val, "Comment": 10, "Blank": 5, "Lines": 115, "Complexity": 8, "Count": 3}]
            return MagicMock(returncode=0, stdout=json.dumps(data), stderr="")
        mock_run.side_effect = side_effect
        result = check_semantic_consistency(tmp_path)
        assert result.passed is False

    @patch("scripts.checks.reliability.subprocess.run")
    def test_fail_run_error(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        result = check_semantic_consistency(tmp_path)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: run_reliability_checks
# ---------------------------------------------------------------------------

class TestRunReliabilityChecks:
    @patch("scripts.checks.reliability.subprocess.run")
    def test_returns_9_checks(self, mock_run, tmp_path):
        data = [{"Name": "Python", "Code": 100, "Comment": 10, "Blank": 5, "Lines": 115, "Complexity": 8, "Count": 3}]
        per_file = [{"Name": "Python", "Files": [{"Location": "a.py", "Code": 100, "Comment": 10, "Blank": 5, "Lines": 115, "Complexity": 8}]}]
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(per_file),
            stderr=""
        )
        results = run_reliability_checks(tmp_path)
        assert len(results) == 9
        assert all(isinstance(r, CheckResult) for r in results)
