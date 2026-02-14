"""Unit tests for checks/edge_cases.py (EC-1 through EC-4)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.edge_cases import run_edge_case_checks


class TestEC1EmptyRepoHandling:
    """EC-1: Empty repo should return valid zero-secret output."""

    def test_empty_repo_valid_output(self) -> None:
        """Empty repo with total_secrets=0 and findings=[] -> PASS."""
        analysis = {
            "total_secrets": 0,
            "findings": [],
            "scan_time_ms": 50,
        }
        ground_truth = {"expected": {"is_empty_repo": True}}

        results = run_edge_case_checks(analysis, ground_truth)

        ec1 = next(r for r in results if r.check_id == "EC-1")
        assert ec1.passed is True
        assert "valid zero-secret" in ec1.message

    def test_empty_repo_nonzero_secrets_fails(self) -> None:
        """Empty repo with total_secrets > 0 -> FAIL."""
        analysis = {
            "total_secrets": 3,
            "findings": [],
            "scan_time_ms": 50,
        }
        ground_truth = {"expected": {"is_empty_repo": True}}

        results = run_edge_case_checks(analysis, ground_truth)

        ec1 = next(r for r in results if r.check_id == "EC-1")
        assert ec1.passed is False

    def test_empty_repo_missing_findings_fails(self) -> None:
        """Empty repo missing 'findings' key -> FAIL."""
        analysis = {
            "total_secrets": 0,
            "scan_time_ms": 50,
        }
        ground_truth = {"expected": {"is_empty_repo": True}}

        results = run_edge_case_checks(analysis, ground_truth)

        ec1 = next(r for r in results if r.check_id == "EC-1")
        assert ec1.passed is False

    def test_not_empty_repo_skipped(self) -> None:
        """Non-empty repo scenario -> N/A pass."""
        analysis = {
            "total_secrets": 5,
            "findings": [{"file_path": "config.env"}],
            "scan_time_ms": 100,
        }
        ground_truth = {"expected": {"is_empty_repo": False}}

        results = run_edge_case_checks(analysis, ground_truth)

        ec1 = next(r for r in results if r.check_id == "EC-1")
        assert ec1.passed is True
        assert "N/A" in ec1.message


class TestEC2UnicodeFilePaths:
    """EC-2: All file paths should be valid UTF-8."""

    def test_all_valid_utf8(self) -> None:
        """All string paths -> PASS."""
        analysis = {
            "total_secrets": 2,
            "findings": [
                {"file_path": "src/main.py"},
                {"file_path": "config/日本語.env"},
            ],
            "scan_time_ms": 100,
        }
        ground_truth = {"expected": {}}

        results = run_edge_case_checks(analysis, ground_truth)

        ec2 = next(r for r in results if r.check_id == "EC-2")
        assert ec2.passed is True

    def test_bytes_path_fails(self) -> None:
        """Bytes path (not string) -> FAIL."""
        analysis = {
            "total_secrets": 1,
            "findings": [
                {"file_path": b"raw/bytes/path.txt"},
            ],
            "scan_time_ms": 50,
        }
        ground_truth = {"expected": {}}

        results = run_edge_case_checks(analysis, ground_truth)

        ec2 = next(r for r in results if r.check_id == "EC-2")
        assert ec2.passed is False

    def test_empty_findings_passes(self) -> None:
        """No findings -> no unicode issues -> PASS."""
        analysis = {
            "total_secrets": 0,
            "findings": [],
            "scan_time_ms": 10,
        }
        ground_truth = {"expected": {}}

        results = run_edge_case_checks(analysis, ground_truth)

        ec2 = next(r for r in results if r.check_id == "EC-2")
        assert ec2.passed is True


class TestEC3LargeFileHandling:
    """EC-3: Large file scan should complete within time limit."""

    def test_large_file_scan_passes(self) -> None:
        """Scan completes within max time -> PASS."""
        analysis = {
            "total_secrets": 0,
            "findings": [],
            "scan_time_ms": 5000,
        }
        ground_truth = {"expected": {"has_large_files": True, "max_scan_time_ms": 60000}}

        results = run_edge_case_checks(analysis, ground_truth)

        ec3 = next(r for r in results if r.check_id == "EC-3")
        assert ec3.passed is True

    def test_large_file_scan_timeout(self) -> None:
        """Scan exceeds max time -> FAIL."""
        analysis = {
            "total_secrets": 0,
            "findings": [],
            "scan_time_ms": 120000,
        }
        ground_truth = {"expected": {"has_large_files": True, "max_scan_time_ms": 60000}}

        results = run_edge_case_checks(analysis, ground_truth)

        ec3 = next(r for r in results if r.check_id == "EC-3")
        assert ec3.passed is False

    def test_zero_scan_time_fails(self) -> None:
        """scan_time_ms=0 with large files -> FAIL (suspicious)."""
        analysis = {
            "total_secrets": 0,
            "findings": [],
            "scan_time_ms": 0,
        }
        ground_truth = {"expected": {"has_large_files": True}}

        results = run_edge_case_checks(analysis, ground_truth)

        ec3 = next(r for r in results if r.check_id == "EC-3")
        assert ec3.passed is False

    def test_no_large_files_skipped(self) -> None:
        """No large file scenario -> N/A pass."""
        analysis = {
            "total_secrets": 0,
            "findings": [],
            "scan_time_ms": 100,
        }
        ground_truth = {"expected": {"has_large_files": False}}

        results = run_edge_case_checks(analysis, ground_truth)

        ec3 = next(r for r in results if r.check_id == "EC-3")
        assert ec3.passed is True
        assert "N/A" in ec3.message


class TestEC4BinaryFileHandling:
    """EC-4: Binary files should be skipped or handled gracefully."""

    def test_no_binary_findings_passes(self) -> None:
        """Findings not in binary files -> PASS."""
        analysis = {
            "total_secrets": 1,
            "findings": [{"file_path": "config/api_key.txt"}],
            "scan_time_ms": 100,
        }
        ground_truth = {"expected": {"has_binary_files": True}}

        results = run_edge_case_checks(analysis, ground_truth)

        ec4 = next(r for r in results if r.check_id == "EC-4")
        assert ec4.passed is True

    def test_binary_file_findings_fails(self) -> None:
        """Findings in binary files -> FAIL."""
        analysis = {
            "total_secrets": 2,
            "findings": [
                {"file_path": "images/logo.png"},
                {"file_path": "lib/native.dll"},
            ],
            "scan_time_ms": 100,
        }
        ground_truth = {"expected": {"has_binary_files": True}}

        results = run_edge_case_checks(analysis, ground_truth)

        ec4 = next(r for r in results if r.check_id == "EC-4")
        assert ec4.passed is False

    def test_no_binary_files_skipped(self) -> None:
        """No binary file scenario -> N/A pass."""
        analysis = {
            "total_secrets": 0,
            "findings": [],
            "scan_time_ms": 50,
        }
        ground_truth = {"expected": {"has_binary_files": False}}

        results = run_edge_case_checks(analysis, ground_truth)

        ec4 = next(r for r in results if r.check_id == "EC-4")
        assert ec4.passed is True
        assert "N/A" in ec4.message

    def test_mixed_binary_extensions(self) -> None:
        """Only binary-extension findings should be flagged."""
        analysis = {
            "total_secrets": 3,
            "findings": [
                {"file_path": "src/main.py"},
                {"file_path": "build/app.exe"},
                {"file_path": "docs/readme.md"},
            ],
            "scan_time_ms": 100,
        }
        ground_truth = {"expected": {"has_binary_files": True}}

        results = run_edge_case_checks(analysis, ground_truth)

        ec4 = next(r for r in results if r.check_id == "EC-4")
        assert ec4.passed is False  # app.exe is binary


class TestAllEdgeCasesReturned:
    """Verify that all 4 checks are always returned."""

    def test_always_returns_four_checks(self) -> None:
        """Should always return exactly 4 CheckResult objects."""
        analysis = {"total_secrets": 0, "findings": [], "scan_time_ms": 10}
        ground_truth = {"expected": {}}

        results = run_edge_case_checks(analysis, ground_truth)

        assert len(results) == 4
        check_ids = {r.check_id for r in results}
        assert check_ids == {"EC-1", "EC-2", "EC-3", "EC-4"}
