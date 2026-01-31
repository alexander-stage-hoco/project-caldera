"""Tests for SCC reliability checks (RL-1 to RL-9).

Tests the reliability checks including RL-9 (cross-run semantic consistency).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks import CheckResult
from checks.reliability import (
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
    run_scc_by_file,
)


class DummyResult:
    """Mock subprocess result."""
    def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class TestRL1EmptyFileHandled:
    """Tests for RL-1: Empty files handled correctly."""

    @pytest.fixture
    def mock_empty_files(self):
        """Mock scc output with empty files."""
        return [
            {"Location": "eval-repos/synthetic/python/empty.py", "Language": "Python", "Code": 0, "Lines": 0},
            {"Location": "eval-repos/synthetic/csharp/Empty.cs", "Language": "C#", "Code": 0, "Lines": 0},
            {"Location": "eval-repos/synthetic/javascript/empty.js", "Language": "JavaScript", "Code": 0, "Lines": 0},
            {"Location": "eval-repos/synthetic/typescript/empty.ts", "Language": "TypeScript", "Code": 0, "Lines": 0},
            {"Location": "eval-repos/synthetic/go/empty.go", "Language": "Go", "Code": 0, "Lines": 0},
            {"Location": "eval-repos/synthetic/rust/empty.rs", "Language": "Rust", "Code": 0, "Lines": 0},
            {"Location": "eval-repos/synthetic/java/Empty.java", "Language": "Java", "Code": 0, "Lines": 0},
        ]

    def test_rl1_passes_with_all_empty_files(self, mock_empty_files, tmp_path):
        """RL-1 should pass when all 7 empty files have Code=0."""
        with patch("checks.reliability.run_scc_by_file", return_value=(mock_empty_files, 0, "")):
            result = check_empty_file_handled(tmp_path)

            assert result.check_id == "RL-1"
            assert result.passed is True
            assert len(result.evidence["files"]) >= 7

    def test_rl1_fails_when_missing_empty_files(self, tmp_path):
        """RL-1 should fail when fewer than 7 empty files found."""
        partial_files = [
            {"Location": "eval-repos/synthetic/python/empty.py", "Language": "Python", "Code": 0},
            {"Location": "eval-repos/synthetic/csharp/Empty.cs", "Language": "C#", "Code": 0},
        ]
        with patch("checks.reliability.run_scc_by_file", return_value=(partial_files, 0, "")):
            result = check_empty_file_handled(tmp_path)

            assert result.check_id == "RL-1"
            assert result.passed is False

    def test_rl1_fails_when_empty_file_has_nonzero_code(self, mock_empty_files, tmp_path):
        """RL-1 should fail when an empty file has Code > 0."""
        mock_empty_files[0]["Code"] = 5
        with patch("checks.reliability.run_scc_by_file", return_value=(mock_empty_files, 0, "")):
            result = check_empty_file_handled(tmp_path)

            assert result.check_id == "RL-1"
            assert result.passed is False

    def test_rl1_handles_exception(self, tmp_path):
        """RL-1 should handle exceptions gracefully."""
        with patch("checks.reliability.run_scc_by_file", side_effect=Exception("Test error")):
            result = check_empty_file_handled(tmp_path)

            assert result.check_id == "RL-1"
            assert result.passed is False
            assert "error" in result.message.lower()


class TestRL2CommentsOnlyHandled:
    """Tests for RL-2: Comments-only files handled correctly."""

    @pytest.fixture
    def mock_comment_files(self):
        """Mock scc output with comments-only files."""
        return [
            {"Location": "eval-repos/synthetic/python/comments_only.py", "Language": "Python", "Code": 0, "Comment": 10},
            {"Location": "eval-repos/synthetic/csharp/CommentsOnly.cs", "Language": "C#", "Code": 0, "Comment": 8},
            {"Location": "eval-repos/synthetic/javascript/comments_only.js", "Language": "JavaScript", "Code": 0, "Comment": 12},
            {"Location": "eval-repos/synthetic/typescript/comments_only.ts", "Language": "TypeScript", "Code": 0, "Comment": 5},
            {"Location": "eval-repos/synthetic/go/comments_only.go", "Language": "Go", "Code": 0, "Comment": 7},
            {"Location": "eval-repos/synthetic/rust/comments_only.rs", "Language": "Rust", "Code": 0, "Comment": 6},
            {"Location": "eval-repos/synthetic/java/CommentsOnly.java", "Language": "Java", "Code": 0, "Comment": 9},
        ]

    def test_rl2_passes_when_comment_files_valid(self, mock_comment_files, tmp_path):
        """RL-2 should pass when comment-only files have Code=0 and Comment>0."""
        with patch("checks.reliability.run_scc_by_file", return_value=(mock_comment_files, 0, "")):
            result = check_comments_only_handled(tmp_path)

            assert result.check_id == "RL-2"
            assert result.passed is True

    def test_rl2_fails_when_comment_file_has_code(self, mock_comment_files, tmp_path):
        """RL-2 should fail when comment-only file has Code > 0."""
        mock_comment_files[0]["Code"] = 3
        with patch("checks.reliability.run_scc_by_file", return_value=(mock_comment_files, 0, "")):
            result = check_comments_only_handled(tmp_path)

            assert result.check_id == "RL-2"
            assert result.passed is False

    def test_rl2_fails_when_comment_file_has_zero_comments(self, mock_comment_files, tmp_path):
        """RL-2 should fail when comment-only file has Comment=0."""
        mock_comment_files[0]["Comment"] = 0
        with patch("checks.reliability.run_scc_by_file", return_value=(mock_comment_files, 0, "")):
            result = check_comments_only_handled(tmp_path)

            assert result.check_id == "RL-2"
            assert result.passed is False


class TestRL3SingleLineHandled:
    """Tests for RL-3: Single-line files handled correctly."""

    @pytest.fixture
    def mock_single_line_files(self):
        """Mock scc output with single-line files."""
        return [
            {"Location": "eval-repos/synthetic/python/single_line.py", "Language": "Python", "Code": 1},
            {"Location": "eval-repos/synthetic/csharp/SingleLine.cs", "Language": "C#", "Code": 1},
            {"Location": "eval-repos/synthetic/javascript/single_line.js", "Language": "JavaScript", "Code": 1},
            {"Location": "eval-repos/synthetic/typescript/single_line.ts", "Language": "TypeScript", "Code": 1},
            {"Location": "eval-repos/synthetic/go/single_line.go", "Language": "Go", "Code": 1},
            {"Location": "eval-repos/synthetic/rust/single_line.rs", "Language": "Rust", "Code": 1},
            {"Location": "eval-repos/synthetic/java/SingleLine.java", "Language": "Java", "Code": 1},
        ]

    def test_rl3_passes_when_single_line_files_have_code_1(self, mock_single_line_files, tmp_path):
        """RL-3 should pass when single-line files have Code=1."""
        with patch("checks.reliability.run_scc_by_file", return_value=(mock_single_line_files, 0, "")):
            result = check_single_line_handled(tmp_path)

            assert result.check_id == "RL-3"
            assert result.passed is True

    def test_rl3_fails_when_single_line_file_has_wrong_code_count(self, mock_single_line_files, tmp_path):
        """RL-3 should fail when single-line file has Code != 1."""
        mock_single_line_files[0]["Code"] = 2
        with patch("checks.reliability.run_scc_by_file", return_value=(mock_single_line_files, 0, "")):
            result = check_single_line_handled(tmp_path)

            assert result.check_id == "RL-3"
            assert result.passed is False


class TestRL4UnicodeHandled:
    """Tests for RL-4: Unicode files parsed successfully."""

    @pytest.fixture
    def mock_unicode_files(self):
        """Mock scc output with unicode files."""
        return [
            {"Location": "eval-repos/synthetic/python/unicode.py", "Language": "Python", "Lines": 50},
            {"Location": "eval-repos/synthetic/csharp/Unicode.cs", "Language": "C#", "Lines": 45},
            {"Location": "eval-repos/synthetic/javascript/unicode.js", "Language": "JavaScript", "Lines": 30},
            {"Location": "eval-repos/synthetic/typescript/unicode.ts", "Language": "TypeScript", "Lines": 35},
            {"Location": "eval-repos/synthetic/go/unicode.go", "Language": "Go", "Lines": 40},
            {"Location": "eval-repos/synthetic/rust/unicode.rs", "Language": "Rust", "Lines": 25},
            {"Location": "eval-repos/synthetic/java/Unicode.java", "Language": "Java", "Lines": 55},
        ]

    def test_rl4_passes_when_unicode_files_have_lines(self, mock_unicode_files, tmp_path):
        """RL-4 should pass when unicode files have Lines > 0."""
        with patch("checks.reliability.run_scc_by_file", return_value=(mock_unicode_files, 0, "")):
            result = check_unicode_handled(tmp_path)

            assert result.check_id == "RL-4"
            assert result.passed is True

    def test_rl4_fails_when_unicode_file_has_zero_lines(self, mock_unicode_files, tmp_path):
        """RL-4 should fail when unicode file has Lines=0 (parsing failed)."""
        mock_unicode_files[0]["Lines"] = 0
        with patch("checks.reliability.run_scc_by_file", return_value=(mock_unicode_files, 0, "")):
            result = check_unicode_handled(tmp_path)

            assert result.check_id == "RL-4"
            assert result.passed is False


class TestRL5DeepNestingHandled:
    """Tests for RL-5: Deep nesting files report complexity."""

    @pytest.fixture
    def mock_deep_nesting_files(self):
        """Mock scc output with deep nesting files."""
        return [
            {"Location": "eval-repos/synthetic/python/deep_nesting.py", "Language": "Python", "Complexity": 15},
            {"Location": "eval-repos/synthetic/csharp/DeepNesting.cs", "Language": "C#", "Complexity": 20},
            {"Location": "eval-repos/synthetic/javascript/deep_nesting.js", "Language": "JavaScript", "Complexity": 12},
            {"Location": "eval-repos/synthetic/typescript/deep_nesting.ts", "Language": "TypeScript", "Complexity": 18},
            {"Location": "eval-repos/synthetic/go/deep_nesting.go", "Language": "Go", "Complexity": 10},
            {"Location": "eval-repos/synthetic/rust/deep_nesting.rs", "Language": "Rust", "Complexity": 14},
            {"Location": "eval-repos/synthetic/java/DeepNesting.java", "Language": "Java", "Complexity": 22},
        ]

    def test_rl5_passes_when_deep_nesting_files_have_complexity(self, mock_deep_nesting_files, tmp_path):
        """RL-5 should pass when deep nesting files have Complexity > 0."""
        with patch("checks.reliability.run_scc_by_file", return_value=(mock_deep_nesting_files, 0, "")):
            result = check_deep_nesting_handled(tmp_path)

            assert result.check_id == "RL-5"
            assert result.passed is True

    def test_rl5_fails_when_deep_nesting_file_has_zero_complexity(self, mock_deep_nesting_files, tmp_path):
        """RL-5 should fail when deep nesting file has Complexity=0."""
        mock_deep_nesting_files[0]["Complexity"] = 0
        with patch("checks.reliability.run_scc_by_file", return_value=(mock_deep_nesting_files, 0, "")):
            result = check_deep_nesting_handled(tmp_path)

            assert result.check_id == "RL-5"
            assert result.passed is False


class TestRL6DeterministicOutput:
    """Tests for RL-6: Output is deterministic across runs."""

    def test_rl6_passes_when_three_runs_identical(self, tmp_path):
        """RL-6 should pass when 3 runs produce identical output."""
        with patch("checks.reliability.subprocess.run") as mock_run:
            mock_run.return_value = DummyResult(
                returncode=0,
                stdout=json.dumps([{"Name": "Python", "Code": 500}])
            )

            result = check_deterministic_output(tmp_path)

            assert result.check_id == "RL-6"
            assert result.passed is True
            assert len(set(result.evidence["hashes"])) == 1

    def test_rl6_fails_when_runs_differ(self, tmp_path):
        """RL-6 should fail when runs produce different output."""
        call_count = [0]

        def varying_run(*args, **kwargs):
            call_count[0] += 1
            return DummyResult(
                returncode=0,
                stdout=json.dumps([{"Name": "Python", "Code": 500 + call_count[0]}])
            )

        with patch("checks.reliability.subprocess.run", side_effect=varying_run):
            result = check_deterministic_output(tmp_path)

            assert result.check_id == "RL-6"
            assert result.passed is False
            assert len(set(result.evidence["hashes"])) > 1


class TestRL7AllFilesDetected:
    """Tests for RL-7: All expected files detected."""

    def test_rl7_passes_when_all_files_found(self, tmp_path):
        """RL-7 should pass when file count >= expected."""
        mock_files = [{"Location": f"file{i}.py"} for i in range(70)]
        with patch("checks.reliability.run_scc_by_file", return_value=(mock_files, 0, "")):
            result = check_all_files_detected(tmp_path, expected_total=63)

            assert result.check_id == "RL-7"
            assert result.passed is True
            assert result.actual == 70

    def test_rl7_fails_when_files_missing(self, tmp_path):
        """RL-7 should fail when file count < expected."""
        mock_files = [{"Location": f"file{i}.py"} for i in range(50)]
        with patch("checks.reliability.run_scc_by_file", return_value=(mock_files, 0, "")):
            result = check_all_files_detected(tmp_path, expected_total=63)

            assert result.check_id == "RL-7"
            assert result.passed is False


class TestRL8NoCrashes:
    """Tests for RL-8: SCC exits with code 0."""

    def test_rl8_passes_when_exit_code_zero(self, tmp_path):
        """RL-8 should pass when scc exits with code 0."""
        with patch("checks.reliability.subprocess.run") as mock_run:
            mock_run.return_value = DummyResult(returncode=0, stdout="[]", stderr="")

            result = check_no_crashes(tmp_path)

            assert result.check_id == "RL-8"
            assert result.passed is True

    def test_rl8_fails_when_exit_code_nonzero(self, tmp_path):
        """RL-8 should fail when scc exits with non-zero code."""
        with patch("checks.reliability.subprocess.run") as mock_run:
            mock_run.return_value = DummyResult(returncode=1, stderr="Error occurred")

            result = check_no_crashes(tmp_path)

            assert result.check_id == "RL-8"
            assert result.passed is False


class TestRL9SemanticConsistency:
    """Tests for RL-9: Cross-run semantic consistency."""

    @pytest.fixture
    def sample_scc_output(self):
        """Sample scc JSON output for testing."""
        return [
            {"Name": "Python", "Code": 500, "Comment": 100, "Blank": 50, "Lines": 650, "Complexity": 25, "Count": 10},
            {"Name": "JavaScript", "Code": 300, "Comment": 50, "Blank": 30, "Lines": 380, "Complexity": 15, "Count": 5},
        ]

    @pytest.fixture
    def sample_scc_output_changed(self):
        """Sample scc output with changed metrics."""
        return [
            {"Name": "Python", "Code": 510, "Comment": 100, "Blank": 50, "Lines": 660, "Complexity": 26, "Count": 10},  # Code changed
            {"Name": "JavaScript", "Code": 300, "Comment": 50, "Blank": 30, "Lines": 380, "Complexity": 15, "Count": 5},
        ]

    @pytest.fixture
    def sample_scc_output_new_language(self):
        """Sample scc output with a new language added."""
        return [
            {"Name": "Python", "Code": 500, "Comment": 100, "Blank": 50, "Lines": 650, "Complexity": 25, "Count": 10},
            {"Name": "JavaScript", "Code": 300, "Comment": 50, "Blank": 30, "Lines": 380, "Complexity": 15, "Count": 5},
            {"Name": "Go", "Code": 200, "Comment": 30, "Blank": 20, "Lines": 250, "Complexity": 10, "Count": 3},
        ]

    def test_rl9_passes_when_runs_are_identical(self, sample_scc_output, tmp_path):
        """RL-9 should pass when two runs produce identical metrics."""
        with patch("checks.reliability.subprocess.run") as mock_run:
            # Both runs return identical output
            mock_run.return_value = DummyResult(
                returncode=0,
                stdout=json.dumps(sample_scc_output)
            )

            result = check_semantic_consistency(tmp_path)

            assert result.check_id == "RL-9"
            assert result.passed is True
            assert "0 differences" in result.message

    def test_rl9_detects_metric_changes(self, sample_scc_output, sample_scc_output_changed, tmp_path):
        """RL-9 should detect when metrics change between runs."""
        with patch("checks.reliability.subprocess.run") as mock_run:
            # First call returns original, second returns changed
            mock_run.side_effect = [
                DummyResult(returncode=0, stdout=json.dumps(sample_scc_output_changed)),
                DummyResult(returncode=0, stdout=json.dumps(sample_scc_output)),
            ]

            result = check_semantic_consistency(tmp_path)

            assert result.check_id == "RL-9"
            assert result.passed is False
            assert "differences" in result.message
            # Check that changes are recorded
            assert result.evidence.get("total_changes", 0) > 0

    def test_rl9_detects_new_languages(self, sample_scc_output, sample_scc_output_new_language, tmp_path):
        """RL-9 should detect when languages are added."""
        with patch("checks.reliability.subprocess.run") as mock_run:
            mock_run.side_effect = [
                DummyResult(returncode=0, stdout=json.dumps(sample_scc_output_new_language)),
                DummyResult(returncode=0, stdout=json.dumps(sample_scc_output)),
            ]

            result = check_semantic_consistency(tmp_path)

            assert result.check_id == "RL-9"
            assert result.passed is False
            # Check for language addition in changes
            changes = result.evidence.get("changes", [])
            lang_changes = [c for c in changes if c.get("type") in ("languages_added", "languages_removed")]
            assert len(lang_changes) > 0

    def test_rl9_handles_run_failure(self, tmp_path):
        """RL-9 should handle scc run failures gracefully."""
        with patch("checks.reliability.subprocess.run") as mock_run:
            mock_run.return_value = DummyResult(
                returncode=1,
                stderr="scc: command not found"
            )

            result = check_semantic_consistency(tmp_path)

            assert result.check_id == "RL-9"
            assert result.passed is False
            assert "failed" in result.message.lower()

    def test_rl9_uses_previous_run_path_when_provided(self, sample_scc_output, tmp_path):
        """RL-9 should use previous run file when path is provided."""
        # Create previous run file
        previous_run = tmp_path / "previous_run.json"
        previous_run.write_text(json.dumps(sample_scc_output))

        with patch("checks.reliability.subprocess.run") as mock_run:
            mock_run.return_value = DummyResult(
                returncode=0,
                stdout=json.dumps(sample_scc_output)
            )

            result = check_semantic_consistency(tmp_path, previous_run)

            assert result.check_id == "RL-9"
            assert result.passed is True
            # Should only have called subprocess once (not twice)
            assert mock_run.call_count == 1

    def test_rl9_handles_empty_previous_run(self, sample_scc_output, tmp_path):
        """RL-9 should handle missing previous run gracefully."""
        nonexistent_path = tmp_path / "does_not_exist.json"

        with patch("checks.reliability.subprocess.run") as mock_run:
            mock_run.return_value = DummyResult(
                returncode=0,
                stdout=json.dumps(sample_scc_output)
            )

            result = check_semantic_consistency(tmp_path, nonexistent_path)

            assert result.check_id == "RL-9"
            # Should fall back to running twice
            assert mock_run.call_count == 2

    def test_rl9_reports_specific_metric_changes(self, tmp_path):
        """RL-9 should report specific metric changes in evidence."""
        original = [{"Name": "Python", "Code": 100, "Comment": 20, "Blank": 10, "Lines": 130, "Complexity": 5, "Count": 2}]
        changed = [{"Name": "Python", "Code": 110, "Comment": 20, "Blank": 10, "Lines": 140, "Complexity": 6, "Count": 2}]

        with patch("checks.reliability.subprocess.run") as mock_run:
            mock_run.side_effect = [
                DummyResult(returncode=0, stdout=json.dumps(changed)),
                DummyResult(returncode=0, stdout=json.dumps(original)),
            ]

            result = check_semantic_consistency(tmp_path)

            assert result.passed is False
            changes = result.evidence.get("changes", [])
            metric_changes = [c for c in changes if c.get("type") == "metric_changed"]
            assert len(metric_changes) > 0
            # Check that specific metrics are reported
            changed_metrics = {c.get("metric") for c in metric_changes}
            assert "Code" in changed_metrics or "Lines" in changed_metrics or "Complexity" in changed_metrics

    def test_rl9_handles_exception(self, tmp_path):
        """RL-9 should handle unexpected exceptions gracefully."""
        with patch("checks.reliability.subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Unexpected error")

            result = check_semantic_consistency(tmp_path)

            assert result.check_id == "RL-9"
            assert result.passed is False
            assert "error" in result.message.lower()


class TestRunReliabilityChecks:
    """Tests for the run_reliability_checks orchestrator function."""

    def test_run_reliability_checks_includes_all_checks(self, tmp_path):
        """run_reliability_checks should include all 9 reliability checks."""
        with patch("checks.reliability.subprocess.run") as mock_run:
            # Return valid output for all checks
            mock_run.return_value = DummyResult(
                returncode=0,
                stdout=json.dumps([{"Name": "Python", "Code": 100, "Comment": 10, "Blank": 5}])
            )

            with patch("checks.reliability.run_scc_by_file") as mock_by_file:
                mock_by_file.return_value = (
                    [
                        {"Location": "eval-repos/synthetic/python/empty.py", "Code": 0, "Comment": 0, "Lines": 0},
                        {"Location": "eval-repos/synthetic/python/comments_only.py", "Code": 0, "Comment": 10, "Lines": 10},
                        {"Location": "eval-repos/synthetic/python/single_line.py", "Code": 1, "Lines": 1},
                        {"Location": "eval-repos/synthetic/python/unicode.py", "Code": 10, "Lines": 15},
                        {"Location": "eval-repos/synthetic/python/deep_nesting.py", "Code": 50, "Complexity": 10, "Lines": 60},
                    ] * 7 + [  # 7 copies to match expected 7 per edge case
                        {"Location": f"eval-repos/synthetic/python/file{i}.py", "Code": 10, "Lines": 15}
                        for i in range(28)  # Extra files to reach 63 total
                    ],
                    0,
                    ""
                )

                results = run_reliability_checks(tmp_path)

                check_ids = [r.check_id for r in results]
                assert len(results) == 9, "Should include all 9 reliability checks"
                for i in range(1, 10):
                    assert f"RL-{i}" in check_ids, f"RL-{i} should be included in reliability checks"

    def test_run_reliability_checks_accepts_previous_run_path(self, tmp_path):
        """run_reliability_checks should accept previous_run_path parameter."""
        previous_run = tmp_path / "previous.json"
        previous_run.write_text(json.dumps([{"Name": "Python", "Code": 100}]))

        with patch("checks.reliability.subprocess.run") as mock_run:
            mock_run.return_value = DummyResult(
                returncode=0,
                stdout=json.dumps([{"Name": "Python", "Code": 100}])
            )

            with patch("checks.reliability.run_scc_by_file") as mock_by_file:
                mock_by_file.return_value = ([], 0, "")

                # Should not raise an error
                results = run_reliability_checks(tmp_path, previous_run)

                assert isinstance(results, list)
                assert all(isinstance(r, CheckResult) for r in results)
