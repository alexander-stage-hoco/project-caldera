"""Tests for entity __post_init__ validation across all entity types in entities.py."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from persistence.entities import (
    CodeSymbol,
    CollectionRun,
    CoverageSummary,
    DotcoverAssemblyCoverage,
    GitBlameAuthorStats,
    GitBlameFileSummary,
    GitSizerMetric,
    GitSizerViolation,
    PmdCpdDuplication,
    ScancodeFileLicense,
    ScancodeSummary,
    ToolRun,
    TrivyVulnerability,
    _validate_identifier,
    _validate_line_range,
    _validate_positive_pk,
    _validate_relative_path,
)


# ── Internal validators ─────────────────────────────────────────────────────

class TestValidateIdentifier:
    def test_valid(self) -> None:
        _validate_identifier("my-repo", "repo_id")  # no exception

    def test_empty_string(self) -> None:
        with pytest.raises(ValueError, match="non-empty identifier"):
            _validate_identifier("", "repo_id")

    def test_leading_whitespace(self) -> None:
        with pytest.raises(ValueError, match="non-empty identifier"):
            _validate_identifier(" padded", "name")

    def test_trailing_whitespace(self) -> None:
        with pytest.raises(ValueError, match="non-empty identifier"):
            _validate_identifier("padded ", "name")


class TestValidateRelativePath:
    def test_valid_path(self) -> None:
        _validate_relative_path("src/main.py", "path")

    def test_empty_path(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            _validate_relative_path("", "path")

    def test_absolute_path(self) -> None:
        with pytest.raises(ValueError, match="repo-relative"):
            _validate_relative_path("/usr/bin/file", "path")

    def test_dotdot_component(self) -> None:
        with pytest.raises(ValueError, match="must not contain"):
            _validate_relative_path("src/../escape.py", "path")

    def test_backslash_rejected(self) -> None:
        with pytest.raises(ValueError, match="separators"):
            _validate_relative_path("src\\main.py", "path")

    def test_dot_slash_prefix(self) -> None:
        with pytest.raises(ValueError, match="repo-relative"):
            _validate_relative_path("./src/main.py", "path")


class TestValidatePositivePk:
    def test_valid(self) -> None:
        _validate_positive_pk(1)

    def test_zero_rejected(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            _validate_positive_pk(0)

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            _validate_positive_pk(-1)


class TestValidateLineRange:
    def test_valid_range(self) -> None:
        _validate_line_range(1, 10)

    def test_none_values(self) -> None:
        _validate_line_range(None, None)

    def test_start_below_one(self) -> None:
        with pytest.raises(ValueError, match="line_start must be >= 1"):
            _validate_line_range(0, 10)

    def test_end_below_one(self) -> None:
        with pytest.raises(ValueError, match="line_end must be >= 1"):
            _validate_line_range(1, 0)


# ── ToolRun ─────────────────────────────────────────────────────────────────

class TestToolRun:
    def _make(self, **overrides) -> ToolRun:
        defaults = dict(
            collection_run_id="run-1",
            repo_id="repo-1",
            run_id="run-1",
            tool_name="scc",
            tool_version="1.0.0",
            schema_version="1.0.0",
            branch="main",
            commit="a" * 40,
            timestamp=datetime.now(timezone.utc),
        )
        defaults.update(overrides)
        return ToolRun(**defaults)

    def test_valid(self) -> None:
        run = self._make()
        assert run.tool_name == "scc"

    def test_invalid_commit_length(self) -> None:
        with pytest.raises(ValueError, match="40-hex string"):
            self._make(commit="short")

    def test_empty_tool_name(self) -> None:
        with pytest.raises(ValueError, match="tool_name must be non-empty"):
            self._make(tool_name="")


# ── CollectionRun ───────────────────────────────────────────────────────────

class TestCollectionRun:
    def _make(self, **overrides) -> CollectionRun:
        defaults = dict(
            collection_run_id="run-1",
            repo_id="repo-1",
            run_id="run-1",
            branch="main",
            commit="a" * 40,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            status="running",
        )
        defaults.update(overrides)
        return CollectionRun(**defaults)

    def test_valid(self) -> None:
        run = self._make()
        assert run.status == "running"

    def test_empty_status(self) -> None:
        with pytest.raises(ValueError, match="status must be non-empty"):
            self._make(status="")

    def test_invalid_commit(self) -> None:
        with pytest.raises(ValueError, match="40-hex string"):
            self._make(commit="abc")


# ── GitleaksSecret ──────────────────────────────────────────────────────────

class TestGitleaksSecret:
    def _make(self, **overrides):
        from persistence.entities import GitleaksSecret
        defaults = dict(
            run_pk=1, file_id="f1", directory_id="d1",
            relative_path="src/config.py", rule_id="aws-key",
            secret_type="AWS", severity="HIGH", line_number=10,
            commit_hash=None, commit_author=None, commit_date=None,
            fingerprint="fp1", in_current_head=True, entropy=4.5,
            description=None,
        )
        defaults.update(overrides)
        return GitleaksSecret(**defaults)

    def test_valid(self) -> None:
        s = self._make()
        assert s.entropy == 4.5

    def test_entropy_below_zero(self) -> None:
        with pytest.raises(ValueError, match="entropy must be between 0 and 8"):
            self._make(entropy=-0.1)

    def test_entropy_above_eight(self) -> None:
        with pytest.raises(ValueError, match="entropy must be between 0 and 8"):
            self._make(entropy=8.1)

    def test_invalid_severity(self) -> None:
        with pytest.raises(ValueError, match="severity must be one of"):
            self._make(severity="UNKNOWN")


# ── TrivyVulnerability ─────────────────────────────────────────────────────

class TestTrivyVulnerability:
    def _make(self, **overrides):
        defaults = dict(
            run_pk=1, target_key="requirements.txt:pip",
            vulnerability_id="CVE-2024-1234", package_name="flask",
            installed_version="2.0.0", fixed_version="2.0.1",
            severity="HIGH", cvss_score=7.5, title="Vuln",
            published_date=None, age_days=30, fix_available=True,
        )
        defaults.update(overrides)
        return TrivyVulnerability(**defaults)

    def test_valid(self) -> None:
        v = self._make()
        assert v.cvss_score == 7.5

    def test_cvss_below_zero(self) -> None:
        with pytest.raises(ValueError, match="cvss_score must be between 0 and 10"):
            self._make(cvss_score=-0.1)

    def test_cvss_above_ten(self) -> None:
        with pytest.raises(ValueError, match="cvss_score must be between 0 and 10"):
            self._make(cvss_score=10.1)

    def test_invalid_severity(self) -> None:
        with pytest.raises(ValueError, match="severity must be one of"):
            self._make(severity="NONE")


# ── DotcoverAssemblyCoverage ───────────────────────────────────────────────

class TestDotcoverAssemblyCoverage:
    def _make(self, **overrides):
        defaults = dict(
            run_pk=1, assembly_name="MyLib",
            covered_statements=80, total_statements=100,
            statement_coverage_pct=80.0,
        )
        defaults.update(overrides)
        return DotcoverAssemblyCoverage(**defaults)

    def test_valid(self) -> None:
        c = self._make()
        assert c.statement_coverage_pct == 80.0

    def test_coverage_pct_above_100(self) -> None:
        with pytest.raises(ValueError, match="statement_coverage_pct must be between 0 and 100"):
            self._make(statement_coverage_pct=101.0)

    def test_covered_exceeds_total(self) -> None:
        with pytest.raises(ValueError, match="covered_statements cannot exceed total_statements"):
            self._make(covered_statements=101, total_statements=100)


# ── GitBlameFileSummary ────────────────────────────────────────────────────

class TestGitBlameFileSummary:
    def _make(self, **overrides):
        defaults = dict(
            run_pk=1, file_id="f1", directory_id="d1",
            relative_path="src/main.py", total_lines=100,
            unique_authors=3, top_author="alice",
            top_author_lines=60, top_author_pct=60.0,
            last_modified="2026-01-01", churn_30d=5, churn_90d=15,
        )
        defaults.update(overrides)
        return GitBlameFileSummary(**defaults)

    def test_valid(self) -> None:
        s = self._make()
        assert s.unique_authors == 3

    def test_unique_authors_below_one(self) -> None:
        with pytest.raises(ValueError, match="unique_authors must be >= 1"):
            self._make(unique_authors=0)

    def test_churn_invariant(self) -> None:
        with pytest.raises(ValueError, match="churn_30d cannot exceed churn_90d"):
            self._make(churn_30d=20, churn_90d=10)

    def test_top_author_pct_above_100(self) -> None:
        with pytest.raises(ValueError, match="top_author_pct must be between 0 and 100"):
            self._make(top_author_pct=101.0)

    def test_top_author_pct_below_zero(self) -> None:
        with pytest.raises(ValueError, match="top_author_pct must be between 0 and 100"):
            self._make(top_author_pct=-1.0)


# ── GitBlameAuthorStats ────────────────────────────────────────────────────

class TestGitBlameAuthorStats:
    def _make(self, **overrides):
        defaults = dict(
            run_pk=1, author_email="alice@example.com",
            total_files=10, total_lines=500,
            exclusive_files=3, avg_ownership_pct=50.0,
        )
        defaults.update(overrides)
        return GitBlameAuthorStats(**defaults)

    def test_valid(self) -> None:
        s = self._make()
        assert s.total_files == 10

    def test_exclusive_exceeds_total(self) -> None:
        with pytest.raises(ValueError, match="exclusive_files cannot exceed total_files"):
            self._make(exclusive_files=11, total_files=10)

    def test_ownership_pct_above_100(self) -> None:
        with pytest.raises(ValueError, match="avg_ownership_pct must be between 0 and 100"):
            self._make(avg_ownership_pct=101.0)

    def test_ownership_pct_below_zero(self) -> None:
        with pytest.raises(ValueError, match="avg_ownership_pct must be between 0 and 100"):
            self._make(avg_ownership_pct=-1.0)


# ── CoverageSummary ────────────────────────────────────────────────────────

class TestCoverageSummary:
    def _make(self, **overrides):
        defaults = dict(
            run_pk=1, file_id="f1", directory_id="d1",
            relative_path="src/main.py",
            line_coverage_pct=80.0, branch_coverage_pct=60.0,
            lines_total=100, lines_covered=80, lines_missed=20,
            branches_total=10, branches_covered=6,
            source_format="lcov",
        )
        defaults.update(overrides)
        return CoverageSummary(**defaults)

    def test_valid(self) -> None:
        c = self._make()
        assert c.lines_covered == 80

    def test_covered_exceeds_total(self) -> None:
        # lines_missed must still be non-negative, so use 0 to bypass that check
        with pytest.raises(ValueError, match="lines_covered cannot exceed lines_total"):
            self._make(lines_covered=101, lines_total=100, lines_missed=0)

    def test_missed_invariant(self) -> None:
        with pytest.raises(ValueError, match="lines_missed must equal lines_total - lines_covered"):
            self._make(lines_total=100, lines_covered=80, lines_missed=10)

    def test_branch_coverage_above_100(self) -> None:
        with pytest.raises(ValueError, match="branch_coverage_pct must be between 0 and 100"):
            self._make(branch_coverage_pct=101.0)

    def test_branches_covered_exceeds_total(self) -> None:
        with pytest.raises(ValueError, match="branches_covered cannot exceed branches_total"):
            self._make(branches_total=5, branches_covered=10)


# ── CodeSymbol ──────────────────────────────────────────────────────────────

class TestCodeSymbol:
    def _make(self, **overrides):
        defaults = dict(
            run_pk=1, file_id="f1", directory_id="d1",
            relative_path="src/main.py", symbol_name="my_func",
            symbol_type="function", line_start=10, line_end=20,
            is_exported=True, parameters=2, parent_symbol=None,
            docstring=None,
        )
        defaults.update(overrides)
        return CodeSymbol(**defaults)

    def test_valid(self) -> None:
        s = self._make()
        assert s.symbol_name == "my_func"

    def test_invalid_symbol_type(self) -> None:
        with pytest.raises(ValueError, match="symbol_type must be"):
            self._make(symbol_type="module")

    def test_negative_parameters(self) -> None:
        with pytest.raises(ValueError, match="parameters must be >= 0"):
            self._make(parameters=-1)


# ── ScancodeFileLicense ─────────────────────────────────────────────────────

class TestScancodeFileLicense:
    def _make(self, **overrides):
        defaults = dict(
            run_pk=1, file_id="f1", directory_id="d1",
            relative_path="src/main.py", spdx_id="MIT",
            category="permissive", confidence=0.95,
            match_type="file", line_number=1,
        )
        defaults.update(overrides)
        return ScancodeFileLicense(**defaults)

    def test_valid(self) -> None:
        lic = self._make()
        assert lic.spdx_id == "MIT"

    def test_invalid_category(self) -> None:
        with pytest.raises(ValueError, match="category must be"):
            self._make(category="proprietary")

    def test_confidence_above_one(self) -> None:
        with pytest.raises(ValueError, match="confidence must be between 0 and 1"):
            self._make(confidence=1.5)

    def test_invalid_match_type(self) -> None:
        with pytest.raises(ValueError, match="match_type must be"):
            self._make(match_type="body")


# ── GitSizerMetric ──────────────────────────────────────────────────────────

class TestGitSizerMetric:
    def _make(self, **overrides):
        defaults = dict(
            run_pk=1, repo_id="repo-1", health_grade="B",
            duration_ms=100, commit_count=50, commit_total_size=1000,
            max_commit_size=200, max_history_depth=10, max_parent_count=2,
            tree_count=100, tree_total_size=5000, tree_total_entries=300,
            max_tree_entries=50, blob_count=200, blob_total_size=10000,
            max_blob_size=5000, tag_count=5, max_tag_depth=1,
            reference_count=10, branch_count=3,
            max_path_depth=8, max_path_length=100,
            expanded_tree_count=150, expanded_blob_count=250,
            expanded_blob_size=15000,
        )
        defaults.update(overrides)
        return GitSizerMetric(**defaults)

    def test_valid(self) -> None:
        m = self._make()
        assert m.health_grade == "B"

    def test_invalid_health_grade(self) -> None:
        with pytest.raises(ValueError, match="Invalid health_grade"):
            self._make(health_grade="E")


# ── GitSizerViolation ──────────────────────────────────────────────────────

class TestGitSizerViolation:
    def _make(self, **overrides):
        defaults = dict(
            run_pk=1, metric="max_blob_size",
            value_display="5 MiB", raw_value=5242880,
            level=2, object_ref=None,
        )
        defaults.update(overrides)
        return GitSizerViolation(**defaults)

    def test_valid(self) -> None:
        v = self._make()
        assert v.level == 2

    def test_level_below_one(self) -> None:
        with pytest.raises(ValueError, match="level must be 1-4"):
            self._make(level=0)

    def test_level_above_four(self) -> None:
        with pytest.raises(ValueError, match="level must be 1-4"):
            self._make(level=5)


# ── PmdCpdDuplication ──────────────────────────────────────────────────────

class TestPmdCpdDuplication:
    def _make(self, **overrides):
        defaults = dict(
            run_pk=1, clone_id="clone-1",
            lines=10, tokens=50, occurrence_count=3,
            is_cross_file=False, code_fragment=None,
        )
        defaults.update(overrides)
        return PmdCpdDuplication(**defaults)

    def test_valid(self) -> None:
        d = self._make()
        assert d.occurrence_count == 3

    def test_occurrence_count_below_two(self) -> None:
        with pytest.raises(ValueError, match="occurrence_count must be >= 2"):
            self._make(occurrence_count=1)


# ── ScancodeSummary ────────────────────────────────────────────────────────

class TestScancodeSummary:
    def _make(self, **overrides):
        defaults = dict(
            run_pk=1, total_files_scanned=100,
            files_with_licenses=50, overall_risk="low",
            has_permissive=True, has_weak_copyleft=False,
            has_copyleft=False, has_unknown=False,
        )
        defaults.update(overrides)
        return ScancodeSummary(**defaults)

    def test_valid(self) -> None:
        s = self._make()
        assert s.overall_risk == "low"

    def test_invalid_overall_risk(self) -> None:
        with pytest.raises(ValueError, match="overall_risk must be"):
            self._make(overall_risk="extreme")
