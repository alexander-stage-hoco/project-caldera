"""Unit tests for checks/rollup.py (RV-1 through RV-4)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.rollup import run_rollup_checks


class TestRV1RecursiveGteDirectSecrets:
    """RV-1: Recursive secret count >= Direct secret count for all directories."""

    def test_valid_rollup_passes(self) -> None:
        analysis = {
            "total_secrets": 3,
            "directories": {
                ".": {"direct_secret_count": 1, "recursive_secret_count": 3,
                      "direct_file_count": 1, "recursive_file_count": 3,
                      "rule_id_counts": {}},
                "src": {"direct_secret_count": 2, "recursive_secret_count": 2,
                        "direct_file_count": 2, "recursive_file_count": 2,
                        "rule_id_counts": {}},
            },
        }
        results = run_rollup_checks(analysis, {})
        rv1 = next(r for r in results if r.check_id == "RV-1")
        assert rv1.passed is True

    def test_recursive_less_than_direct_fails(self) -> None:
        analysis = {
            "total_secrets": 2,
            "directories": {
                ".": {"direct_secret_count": 5, "recursive_secret_count": 2,
                      "direct_file_count": 1, "recursive_file_count": 1,
                      "rule_id_counts": {}},
            },
        }
        results = run_rollup_checks(analysis, {})
        rv1 = next(r for r in results if r.check_id == "RV-1")
        assert rv1.passed is False


class TestRV2RecursiveGteDirectFiles:
    """RV-2: Recursive file count >= Direct file count."""

    def test_valid_file_counts_pass(self) -> None:
        analysis = {
            "total_secrets": 1,
            "directories": {
                ".": {"direct_secret_count": 1, "recursive_secret_count": 1,
                      "direct_file_count": 1, "recursive_file_count": 3,
                      "rule_id_counts": {}},
            },
        }
        results = run_rollup_checks(analysis, {})
        rv2 = next(r for r in results if r.check_id == "RV-2")
        assert rv2.passed is True

    def test_recursive_files_less_than_direct_fails(self) -> None:
        analysis = {
            "total_secrets": 1,
            "directories": {
                "src": {"direct_secret_count": 0, "recursive_secret_count": 0,
                        "direct_file_count": 10, "recursive_file_count": 3,
                        "rule_id_counts": {}},
            },
        }
        results = run_rollup_checks(analysis, {})
        rv2 = next(r for r in results if r.check_id == "RV-2")
        assert rv2.passed is False


class TestRV3NonNegativeCounts:
    """RV-3: All counts must be non-negative."""

    def test_all_non_negative_passes(self) -> None:
        analysis = {
            "total_secrets": 0,
            "directories": {
                ".": {"direct_secret_count": 0, "recursive_secret_count": 0,
                      "direct_file_count": 0, "recursive_file_count": 0,
                      "rule_id_counts": {}},
            },
        }
        results = run_rollup_checks(analysis, {})
        rv3 = next(r for r in results if r.check_id == "RV-3")
        assert rv3.passed is True

    def test_negative_count_fails(self) -> None:
        analysis = {
            "total_secrets": 0,
            "directories": {
                "src": {"direct_secret_count": -1, "recursive_secret_count": 0,
                        "direct_file_count": 0, "recursive_file_count": 0,
                        "rule_id_counts": {}},
            },
        }
        results = run_rollup_checks(analysis, {})
        rv3 = next(r for r in results if r.check_id == "RV-3")
        assert rv3.passed is False

    def test_multiple_negative_fields(self) -> None:
        analysis = {
            "total_secrets": 0,
            "directories": {
                "a": {"direct_secret_count": -1, "recursive_secret_count": -2,
                      "direct_file_count": -3, "recursive_file_count": -4,
                      "rule_id_counts": {}},
            },
        }
        results = run_rollup_checks(analysis, {})
        rv3 = next(r for r in results if r.check_id == "RV-3")
        assert rv3.passed is False


class TestRV4RootRecursiveEqualsTotal:
    """RV-4: Root recursive_secret_count == total_secrets."""

    def test_matching_total_passes(self) -> None:
        analysis = {
            "total_secrets": 5,
            "directories": {
                ".": {"direct_secret_count": 2, "recursive_secret_count": 5,
                      "direct_file_count": 2, "recursive_file_count": 5,
                      "rule_id_counts": {}},
                "src": {"direct_secret_count": 3, "recursive_secret_count": 3,
                        "direct_file_count": 3, "recursive_file_count": 3,
                        "rule_id_counts": {}},
            },
        }
        results = run_rollup_checks(analysis, {})
        rv4 = next(r for r in results if r.check_id == "RV-4")
        assert rv4.passed is True

    def test_mismatching_total_fails(self) -> None:
        analysis = {
            "total_secrets": 10,
            "directories": {
                ".": {"direct_secret_count": 2, "recursive_secret_count": 5,
                      "direct_file_count": 2, "recursive_file_count": 5,
                      "rule_id_counts": {}},
            },
        }
        results = run_rollup_checks(analysis, {})
        rv4 = next(r for r in results if r.check_id == "RV-4")
        assert rv4.passed is False

    def test_root_not_dot_uses_shortest_path(self) -> None:
        """When '.' is not present, the shortest path is used as root."""
        analysis = {
            "total_secrets": 3,
            "directories": {
                "a": {"direct_secret_count": 1, "recursive_secret_count": 3,
                      "direct_file_count": 1, "recursive_file_count": 3,
                      "rule_id_counts": {}},
                "a/b": {"direct_secret_count": 2, "recursive_secret_count": 2,
                        "direct_file_count": 2, "recursive_file_count": 2,
                        "rule_id_counts": {}},
            },
        }
        results = run_rollup_checks(analysis, {})
        rv4 = next(r for r in results if r.check_id == "RV-4")
        assert rv4.passed is True


class TestNoDirectories:
    """Edge case: No directories present in analysis."""

    def test_empty_directories_all_pass(self) -> None:
        """All checks should pass with N/A when no directories."""
        analysis = {"total_secrets": 0, "directories": {}}
        results = run_rollup_checks(analysis, {})

        assert len(results) == 4
        for r in results:
            assert r.passed is True
            assert "N/A" in r.message

    def test_missing_directories_key(self) -> None:
        """Missing directories key entirely."""
        analysis = {"total_secrets": 0}
        results = run_rollup_checks(analysis, {})

        assert len(results) == 4
        for r in results:
            assert r.passed is True
