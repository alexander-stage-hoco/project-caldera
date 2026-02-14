"""Tests for exclusion checks (EX-1 through EX-6) covering both passing
and failing paths, including edge cases for validation logic."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from scripts.checks.exclusion import (
    check_ex1_excluded_files_present,
    check_ex2_exclusion_reasons_valid,
    check_ex3_excluded_paths_normalized,
    check_ex4_exclusion_counts_consistent,
    check_ex5_vendor_patterns_detected,
    check_ex6_minified_detection_works,
    run_exclusion_checks,
)


# =============================================================================
# EX-1: excluded_files array present
# =============================================================================

class TestEX1ExcludedFilesPresent:
    """Tests for EX-1: excluded_files array existence."""

    def test_missing_excluded_files_fails(self):
        """Missing excluded_files key produces failure."""
        result = check_ex1_excluded_files_present({})
        assert result.passed is False
        assert result.check_id == "EX-1"

    def test_empty_excluded_files_passes(self):
        """Empty excluded_files array passes."""
        result = check_ex1_excluded_files_present({"excluded_files": []})
        assert result.passed is True
        assert result.evidence["count"] == 0

    def test_populated_excluded_files_passes(self):
        """Non-empty excluded_files passes with correct count."""
        analysis = {"excluded_files": [{"path": "a.js", "reason": "pattern"}]}
        result = check_ex1_excluded_files_present(analysis)
        assert result.passed is True
        assert result.evidence["count"] == 1


# =============================================================================
# EX-2: exclusion reasons valid
# =============================================================================

class TestEX2ExclusionReasonsValid:
    """Tests for EX-2: reason enum validation."""

    def test_no_excluded_files_passes(self):
        """No excluded files -> pass."""
        result = check_ex2_exclusion_reasons_valid({"excluded_files": []})
        assert result.passed is True

    def test_all_valid_reasons_pass(self):
        """All four valid reasons pass."""
        analysis = {"excluded_files": [
            {"path": "a.min.js", "reason": "pattern"},
            {"path": "b.js", "reason": "minified"},
            {"path": "c.dat", "reason": "large"},
            {"path": "d.py", "reason": "language"},
        ]}
        result = check_ex2_exclusion_reasons_valid(analysis)
        assert result.passed is True
        assert result.evidence["valid"] == 4

    def test_invalid_reason_fails(self):
        """Invalid reason like 'unknown' causes failure."""
        analysis = {"excluded_files": [
            {"path": "a.js", "reason": "pattern"},
            {"path": "b.js", "reason": "unknown_reason"},
        ]}
        result = check_ex2_exclusion_reasons_valid(analysis)
        assert result.passed is False
        assert len(result.evidence["invalid"]) == 1
        assert result.evidence["invalid"][0]["reason"] == "unknown_reason"

    def test_missing_reason_field_fails(self):
        """Entry without 'reason' field is treated as invalid."""
        analysis = {"excluded_files": [
            {"path": "a.js"},  # No reason field
        ]}
        result = check_ex2_exclusion_reasons_valid(analysis)
        assert result.passed is False


# =============================================================================
# EX-3: excluded paths normalized
# =============================================================================

class TestEX3ExcludedPathsNormalized:
    """Tests for EX-3: path normalization validation."""

    def test_no_excluded_files_passes(self):
        """No excluded files -> pass."""
        result = check_ex3_excluded_paths_normalized({"excluded_files": []})
        assert result.passed is True

    def test_normalized_paths_pass(self):
        """Properly normalized repo-relative paths pass."""
        analysis = {"excluded_files": [
            {"path": "src/vendor/jquery.min.js"},
            {"path": "dist/bundle.js"},
        ]}
        result = check_ex3_excluded_paths_normalized(analysis)
        assert result.passed is True

    def test_leading_slash_fails(self):
        """Absolute paths (leading /) fail."""
        analysis = {"excluded_files": [
            {"path": "/usr/src/file.js"},
        ]}
        result = check_ex3_excluded_paths_normalized(analysis)
        assert result.passed is False
        assert result.evidence["invalid"][0]["issues"] == ["leading slash"]

    def test_relative_prefix_fails(self):
        """Paths with ./ prefix fail."""
        analysis = {"excluded_files": [
            {"path": "./src/file.js"},
        ]}
        result = check_ex3_excluded_paths_normalized(analysis)
        assert result.passed is False
        assert "relative prefix" in result.evidence["invalid"][0]["issues"]

    def test_parent_reference_fails(self):
        """Paths with .. parent references fail."""
        analysis = {"excluded_files": [
            {"path": "src/../vendor/file.js"},
        ]}
        result = check_ex3_excluded_paths_normalized(analysis)
        assert result.passed is False
        assert "parent reference" in result.evidence["invalid"][0]["issues"]

    def test_windows_separator_fails(self):
        """Paths with backslash separators fail."""
        analysis = {"excluded_files": [
            {"path": "src\\vendor\\file.js"},
        ]}
        result = check_ex3_excluded_paths_normalized(analysis)
        assert result.passed is False
        assert "Windows separator" in result.evidence["invalid"][0]["issues"]

    def test_windows_drive_letter_fails(self):
        """Windows drive letter paths fail."""
        analysis = {"excluded_files": [
            {"path": "C:\\src\\file.js"},
        ]}
        result = check_ex3_excluded_paths_normalized(analysis)
        assert result.passed is False
        issues = result.evidence["invalid"][0]["issues"]
        assert "Windows drive letter" in issues

    def test_multiple_issues_reported(self):
        """A path can have multiple normalization issues."""
        analysis = {"excluded_files": [
            {"path": "/src/../file.js"},  # Leading slash AND parent reference
        ]}
        result = check_ex3_excluded_paths_normalized(analysis)
        assert result.passed is False
        issues = result.evidence["invalid"][0]["issues"]
        assert len(issues) >= 2


# =============================================================================
# EX-4: exclusion counts consistent
# =============================================================================

class TestEX4ExclusionCountsConsistent:
    """Tests for EX-4: summary counts match excluded_files array."""

    def test_consistent_counts_pass(self):
        """When all counts match, check passes."""
        analysis = {
            "excluded_files": [
                {"path": "a.min.js", "reason": "pattern"},
                {"path": "b.js", "reason": "minified"},
                {"path": "c.dat", "reason": "large"},
            ],
            "summary": {
                "excluded_count": 3,
                "excluded_by_pattern": 1,
                "excluded_by_minified": 1,
                "excluded_by_size": 1,
                "excluded_by_language": 0,
            },
        }
        result = check_ex4_exclusion_counts_consistent(analysis)
        assert result.passed is True

    def test_mismatched_total_count_fails(self):
        """Total count mismatch causes failure."""
        analysis = {
            "excluded_files": [
                {"path": "a.min.js", "reason": "pattern"},
            ],
            "summary": {
                "excluded_count": 5,  # Wrong!
                "excluded_by_pattern": 1,
                "excluded_by_minified": 0,
                "excluded_by_size": 0,
                "excluded_by_language": 0,
            },
        }
        result = check_ex4_exclusion_counts_consistent(analysis)
        assert result.passed is False
        assert any("excluded_count" in i for i in result.evidence["issues"])

    def test_mismatched_by_reason_fails(self):
        """Per-reason count mismatch causes failure."""
        analysis = {
            "excluded_files": [
                {"path": "a.min.js", "reason": "pattern"},
                {"path": "b.min.js", "reason": "pattern"},
            ],
            "summary": {
                "excluded_count": 2,
                "excluded_by_pattern": 1,  # Wrong: should be 2
                "excluded_by_minified": 0,
                "excluded_by_size": 0,
                "excluded_by_language": 1,  # Wrong: should be 0
            },
        }
        result = check_ex4_exclusion_counts_consistent(analysis)
        assert result.passed is False

    def test_sum_by_reason_mismatch_fails(self):
        """Sum of by_* counts not matching excluded_count is flagged."""
        analysis = {
            "excluded_files": [
                {"path": "a.min.js", "reason": "pattern"},
            ],
            "summary": {
                "excluded_count": 1,
                "excluded_by_pattern": 1,
                "excluded_by_minified": 1,  # Extra, sum won't match
                "excluded_by_size": 0,
                "excluded_by_language": 0,
            },
        }
        result = check_ex4_exclusion_counts_consistent(analysis)
        assert result.passed is False

    def test_empty_excluded_files_with_zero_summary_passes(self):
        """No excluded files with zero counts is consistent."""
        analysis = {
            "excluded_files": [],
            "summary": {
                "excluded_count": 0,
                "excluded_by_pattern": 0,
                "excluded_by_minified": 0,
                "excluded_by_size": 0,
                "excluded_by_language": 0,
            },
        }
        result = check_ex4_exclusion_counts_consistent(analysis)
        assert result.passed is True


# =============================================================================
# EX-5: vendor patterns detected
# =============================================================================

class TestEX5VendorPatternsDetected:
    """Tests for EX-5: vendor pattern matching validation."""

    def test_no_excluded_files_passes(self):
        """Empty excluded_files passes (nothing to exclude)."""
        result = check_ex5_vendor_patterns_detected({"excluded_files": []})
        assert result.passed is True

    def test_pattern_excluded_files_pass(self):
        """Files excluded by pattern cause pass."""
        analysis = {"excluded_files": [
            {"path": "vendor/jquery.min.js", "reason": "pattern", "details": "*.min.js"},
        ]}
        result = check_ex5_vendor_patterns_detected(analysis)
        assert result.passed is True
        assert result.evidence["pattern_excluded_count"] == 1

    def test_only_non_pattern_exclusions(self):
        """Having excluded files but none by pattern fails."""
        analysis = {"excluded_files": [
            {"path": "big.js", "reason": "large"},
            {"path": "dense.js", "reason": "minified"},
        ]}
        result = check_ex5_vendor_patterns_detected(analysis)
        assert result.passed is False


# =============================================================================
# EX-6: minified detection works
# =============================================================================

class TestEX6MinifiedDetectionWorks:
    """Tests for EX-6: content-based minification detection."""

    def test_no_excluded_files_passes(self):
        """Empty excluded_files passes."""
        result = check_ex6_minified_detection_works({"excluded_files": []})
        assert result.passed is True

    def test_minified_files_detected(self):
        """Minified JS files produce correct evidence."""
        analysis = {"excluded_files": [
            {"path": "dist/app.js", "reason": "minified", "language": "JavaScript"},
        ]}
        result = check_ex6_minified_detection_works(analysis)
        assert result.passed is True
        assert result.evidence["minified_excluded_count"] == 1
        assert result.evidence["js_ts_minified_count"] == 1

    def test_non_js_minified(self):
        """Minified non-JS/TS files are counted but not in js_ts count."""
        analysis = {"excluded_files": [
            {"path": "style.css", "reason": "minified", "language": "CSS"},
        ]}
        result = check_ex6_minified_detection_works(analysis)
        assert result.passed is True
        assert result.evidence["minified_excluded_count"] == 1
        assert result.evidence["js_ts_minified_count"] == 0

    def test_no_minified_with_other_exclusions(self):
        """Having exclusions but no minified still passes (best-effort)."""
        analysis = {"excluded_files": [
            {"path": "a.min.js", "reason": "pattern"},
        ]}
        result = check_ex6_minified_detection_works(analysis)
        assert result.passed is True
        assert "No content-based" in result.message


# =============================================================================
# run_exclusion_checks (integration)
# =============================================================================

class TestRunExclusionChecks:
    """Integration tests for running all exclusion checks together."""

    def test_returns_six_checks(self):
        """run_exclusion_checks returns exactly 6 check results."""
        analysis = {"excluded_files": [], "summary": {
            "excluded_count": 0,
            "excluded_by_pattern": 0,
            "excluded_by_minified": 0,
            "excluded_by_size": 0,
            "excluded_by_language": 0,
        }}
        results = run_exclusion_checks(analysis)
        assert len(results) == 6
        check_ids = {r.check_id for r in results}
        assert check_ids == {"EX-1", "EX-2", "EX-3", "EX-4", "EX-5", "EX-6"}

    def test_all_pass_with_clean_data(self):
        """All checks pass with consistent, clean data."""
        analysis = {
            "excluded_files": [
                {"path": "vendor/react.min.js", "reason": "pattern",
                 "language": "JavaScript", "details": "*.min.js"},
                {"path": "dist/bundle.js", "reason": "minified",
                 "language": "JavaScript", "details": "content-based detection"},
            ],
            "summary": {
                "excluded_count": 2,
                "excluded_by_pattern": 1,
                "excluded_by_minified": 1,
                "excluded_by_size": 0,
                "excluded_by_language": 0,
            },
        }
        results = run_exclusion_checks(analysis)
        for r in results:
            assert r.passed is True, f"{r.check_id} failed: {r.message}"
