"""Unit tests for scripts/checks/coverage.py (FC-1 to FC-6 format coverage checks)."""
from __future__ import annotations

import pytest

from scripts.checks.coverage import (
    CheckResult,
    LCOV_CONTENT,
    COBERTURA_CONTENT,
    JACOCO_CONTENT,
    ISTANBUL_CONTENT,
    check_fc1_lcov_detection,
    check_fc2_cobertura_detection,
    check_fc3_jacoco_detection,
    check_fc4_istanbul_detection,
    check_fc5_format_override,
    check_fc6_invalid_format_rejection,
    run_all_coverage_checks,
)


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------
class TestModuleConstants:
    def test_lcov_content_is_string(self) -> None:
        assert isinstance(LCOV_CONTENT, str)
        assert "SF:" in LCOV_CONTENT

    def test_cobertura_content_is_xml(self) -> None:
        assert "<coverage" in COBERTURA_CONTENT

    def test_jacoco_content_is_xml(self) -> None:
        assert "<report" in JACOCO_CONTENT

    def test_istanbul_content_is_json(self) -> None:
        assert ISTANBUL_CONTENT.strip().startswith("{")


# ---------------------------------------------------------------------------
# Individual FC check functions
# ---------------------------------------------------------------------------
class TestFCChecks:
    def test_fc1_lcov_detection_passes(self) -> None:
        r = check_fc1_lcov_detection()
        assert isinstance(r, CheckResult)
        assert r.check_id == "FC-1"
        assert r.passed is True

    def test_fc2_cobertura_detection_passes(self) -> None:
        r = check_fc2_cobertura_detection()
        assert isinstance(r, CheckResult)
        assert r.check_id == "FC-2"
        assert r.passed is True

    def test_fc3_jacoco_detection_passes(self) -> None:
        r = check_fc3_jacoco_detection()
        assert isinstance(r, CheckResult)
        assert r.check_id == "FC-3"
        assert r.passed is True

    def test_fc4_istanbul_detection_passes(self) -> None:
        r = check_fc4_istanbul_detection()
        assert isinstance(r, CheckResult)
        assert r.check_id == "FC-4"
        assert r.passed is True

    def test_fc5_format_override_passes(self) -> None:
        r = check_fc5_format_override()
        assert isinstance(r, CheckResult)
        assert r.check_id == "FC-5"
        assert r.passed is True

    def test_fc6_invalid_format_rejection_passes(self) -> None:
        r = check_fc6_invalid_format_rejection()
        assert isinstance(r, CheckResult)
        assert r.check_id == "FC-6"
        assert r.passed is True


# ---------------------------------------------------------------------------
# run_all_coverage_checks
# ---------------------------------------------------------------------------
class TestRunAllCoverageChecks:
    def test_returns_six_results(self) -> None:
        results = run_all_coverage_checks()
        assert len(results) == 6

    def test_ids_are_fc1_to_fc6(self) -> None:
        results = run_all_coverage_checks()
        ids = [r.check_id for r in results]
        assert ids == ["FC-1", "FC-2", "FC-3", "FC-4", "FC-5", "FC-6"]

    def test_all_pass(self) -> None:
        results = run_all_coverage_checks()
        for r in results:
            assert r.passed is True, f"{r.check_id} failed: {r.message}"
