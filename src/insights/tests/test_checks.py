"""
Tests for programmatic evaluation checks.
"""

from __future__ import annotations

import pytest

from insights.scripts.checks import (
    CheckResult,
    CheckOutput,
    get_all_checks,
    get_checks_by_dimension,
    run_check,
    run_all_checks,
    CHECK_REGISTRY,
)


class TestCheckRegistry:
    """Tests for check registry functionality."""

    def test_all_checks_registered(self) -> None:
        """Verify all checks are properly registered."""
        checks = get_all_checks()
        assert len(checks) == 21, f"Expected 21 checks, got {len(checks)}"

    def test_accuracy_checks_registered(self) -> None:
        """Verify accuracy dimension checks."""
        checks = get_checks_by_dimension("accuracy")
        assert len(checks) == 6
        check_ids = {c.check_id for c in checks}
        assert check_ids == {"IN-AC-1", "IN-AC-2", "IN-AC-3", "IN-AC-4", "IN-AC-5", "IN-AC-6"}

    def test_completeness_checks_registered(self) -> None:
        """Verify completeness dimension checks."""
        checks = get_checks_by_dimension("completeness")
        assert len(checks) == 5
        check_ids = {c.check_id for c in checks}
        assert check_ids == {"IN-CM-1", "IN-CM-2", "IN-CM-3", "IN-CM-4", "IN-CM-5"}

    def test_format_quality_checks_registered(self) -> None:
        """Verify format quality dimension checks."""
        checks = get_checks_by_dimension("format_quality")
        assert len(checks) == 5
        check_ids = {c.check_id for c in checks}
        assert check_ids == {"IN-FQ-1", "IN-FQ-2", "IN-FQ-3", "IN-FQ-4", "IN-FQ-5"}

    def test_data_integrity_checks_registered(self) -> None:
        """Verify data integrity dimension checks."""
        checks = get_checks_by_dimension("data_integrity")
        assert len(checks) == 5
        check_ids = {c.check_id for c in checks}
        assert check_ids == {"IN-DI-1", "IN-DI-2", "IN-DI-3", "IN-DI-4", "IN-DI-5"}


class TestAccuracyChecks:
    """Tests for accuracy checks (IN-AC-*)."""

    def test_total_files_accuracy_match(self) -> None:
        """Test IN-AC-1 with matching file counts."""
        result = run_check(
            "IN-AC-1",
            report_data={"repo_health": {"total_files": 100}},
            db_data={"total_files": 100},
        )
        assert result.result == CheckResult.PASS
        assert result.score == 1.0

    def test_total_files_accuracy_mismatch(self) -> None:
        """Test IN-AC-1 with mismatched file counts."""
        result = run_check(
            "IN-AC-1",
            report_data={"repo_health": {"total_files": 90}},
            db_data={"total_files": 100},
        )
        assert result.result == CheckResult.FAIL
        assert result.score < 1.0

    def test_total_files_accuracy_no_db_data(self) -> None:
        """Test IN-AC-1 skips when no database data."""
        result = run_check(
            "IN-AC-1",
            report_data={"repo_health": {"total_files": 100}},
            db_data={"total_files": 0},
        )
        assert result.result == CheckResult.SKIP

    def test_total_loc_accuracy_match(self) -> None:
        """Test IN-AC-2 with matching LOC."""
        result = run_check(
            "IN-AC-2",
            report_data={"repo_health": {"total_loc": 50000}},
            db_data={"total_loc": 50000},
        )
        assert result.result == CheckResult.PASS
        assert result.score == 1.0

    def test_avg_complexity_accuracy_match(self) -> None:
        """Test IN-AC-5 with matching average complexity."""
        result = run_check(
            "IN-AC-5",
            report_data={"repo_health": {"avg_ccn": 5.5}},
            db_data={"avg_ccn": 5.5},
        )
        assert result.result == CheckResult.PASS
        assert result.score == 1.0


class TestCompletenessChecks:
    """Tests for completeness checks (IN-CM-*)."""

    def test_required_sections_present(self) -> None:
        """Test IN-CM-1 with all required sections."""
        html_content = """
        <section id="repo_health">Repo Health</section>
        <section id="file_hotspots">Hotspots</section>
        <section id="vulnerabilities">Vulnerabilities</section>
        """
        result = run_check(
            "IN-CM-1",
            report_content=html_content,
            report_data={},
            db_data={},
            format="html",
        )
        assert result.result == CheckResult.PASS

    def test_required_sections_missing(self) -> None:
        """Test IN-CM-1 with missing sections."""
        html_content = """
        <section id="repo_health">Repo Health</section>
        """
        result = run_check(
            "IN-CM-1",
            report_content=html_content,
            report_data={},
            db_data={},
            format="html",
        )
        assert result.result == CheckResult.FAIL


class TestFormatQualityChecks:
    """Tests for format quality checks (IN-FQ-*)."""

    def test_html_well_formed(self) -> None:
        """Test IN-FQ-1 with valid HTML."""
        html_content = """
        <!DOCTYPE html>
        <html><head><title>Test</title></head><body><main>Content</main></body></html>
        """
        result = run_check(
            "IN-FQ-1",
            report_content=html_content,
            report_data={},
            db_data={},
            format="html",
        )
        assert result.result == CheckResult.PASS

    def test_html_missing_doctype(self) -> None:
        """Test IN-FQ-1 with missing DOCTYPE."""
        html_content = "<html><body>Content</body></html>"
        result = run_check(
            "IN-FQ-1",
            report_content=html_content,
            report_data={},
            db_data={},
            format="html",
        )
        # Should fail or have lower score
        assert result.score < 1.0


class TestDataIntegrityChecks:
    """Tests for data integrity checks (IN-DI-*)."""

    def test_file_counts_consistent(self) -> None:
        """Test IN-DI-1 with consistent counts."""
        result = run_check(
            "IN-DI-1",
            report_content="",
            report_data={
                "repo_health": {"total_files": 100},
                "file_hotspots": {"file_count": 100},
            },
            db_data={},
            format="html",
        )
        # Should pass or skip if data not comparable
        assert result.result in (CheckResult.PASS, CheckResult.SKIP)

    def test_loc_sums_consistent(self) -> None:
        """Test IN-DI-2 with consistent LOC sums."""
        result = run_check(
            "IN-DI-2",
            report_content="",
            report_data={
                "repo_health": {
                    "total_loc": 1000,
                    "total_code": 800,
                    "total_comment": 150,
                },
            },
            db_data={},
            format="html",
        )
        # Code + comments should be <= total_loc
        assert result.result in (CheckResult.PASS, CheckResult.SKIP)


class TestRunAllChecks:
    """Tests for running all checks together."""

    def test_run_all_checks_returns_results(self) -> None:
        """Verify run_all_checks returns results for all checks."""
        results = run_all_checks(
            report_content="",
            report_data={},
            db_data={},
            format="html",
        )
        assert len(results) == 21

    def test_run_all_checks_handles_missing_data(self) -> None:
        """Verify checks handle missing data gracefully."""
        results = run_all_checks(
            report_content="",
            report_data={},
            db_data={},
            format="html",
        )
        # Should not raise exceptions
        assert all(isinstance(r, CheckOutput) for r in results)


class TestCheckOutput:
    """Tests for CheckOutput data class."""

    def test_check_output_creation(self) -> None:
        """Verify CheckOutput can be created."""
        output = CheckOutput(
            check_id="TEST-1",
            name="Test Check",
            result=CheckResult.PASS,
            score=1.0,
            message="Test passed",
        )
        assert output.check_id == "TEST-1"
        assert output.result == CheckResult.PASS
        assert output.score == 1.0

    def test_check_output_with_details(self) -> None:
        """Verify CheckOutput with details."""
        output = CheckOutput(
            check_id="TEST-2",
            name="Test Check",
            result=CheckResult.FAIL,
            score=0.5,
            message="Test failed",
            details={"reason": "mismatch"},
        )
        assert output.details["reason"] == "mismatch"
