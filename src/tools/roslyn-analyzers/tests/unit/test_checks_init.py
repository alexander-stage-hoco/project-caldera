"""
Tests for checks/__init__.py utility functions.

Tests cover:
- compute_recall: edge cases
- compute_precision: edge cases
- compute_f1: harmonic mean computation
- match_violations: line tolerance matching, grouping by rule
- load_analysis_results: both envelope formats
- load_ground_truth: file and directory loading
- get_violations_for_file: path matching
- count_violations_by_rule: counting
- count_violations_by_category: counting
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks import (
    compute_recall,
    compute_precision,
    compute_f1,
    match_violations,
    load_analysis_results,
    load_ground_truth,
    get_violations_for_file,
    count_violations_by_rule,
    count_violations_by_category,
)


class TestComputeRecall:
    """Test recall computation."""

    def test_perfect_recall(self):
        assert compute_recall(10, 10) == pytest.approx(1.0)

    def test_partial_recall(self):
        assert compute_recall(5, 10) == pytest.approx(0.5)

    def test_zero_detected(self):
        assert compute_recall(0, 10) == pytest.approx(0.0)

    def test_zero_expected(self):
        """Zero expected -> recall 1.0 (nothing to miss)."""
        assert compute_recall(0, 0) == pytest.approx(1.0)


class TestComputePrecision:
    """Test precision computation."""

    def test_perfect_precision(self):
        assert compute_precision(10, 10) == pytest.approx(1.0)

    def test_partial_precision(self):
        assert compute_precision(8, 10) == pytest.approx(0.8)

    def test_zero_total(self):
        """Zero total -> precision 1.0 (nothing reported wrong)."""
        assert compute_precision(0, 0) == pytest.approx(1.0)


class TestComputeF1:
    """Test F1 score computation."""

    def test_perfect_f1(self):
        assert compute_f1(1.0, 1.0) == pytest.approx(1.0)

    def test_balanced_f1(self):
        # F1 = 2 * (0.8 * 0.8) / (0.8 + 0.8) = 0.8
        assert compute_f1(0.8, 0.8) == pytest.approx(0.8)

    def test_zero_precision_and_recall(self):
        assert compute_f1(0.0, 0.0) == pytest.approx(0.0)

    def test_asymmetric_f1(self):
        # F1 = 2 * (1.0 * 0.5) / (1.0 + 0.5) = 2/3
        assert compute_f1(1.0, 0.5) == pytest.approx(2 / 3)


class TestMatchViolations:
    """Test violation matching with line tolerance."""

    def test_exact_line_match(self):
        detected = [
            {"rule_id": "CA3001", "line_start": 15},
        ]
        expected = [
            {"rule_id": "CA3001", "count": 1, "lines": [15]},
        ]
        tp, fp, fn = match_violations(detected, expected, "test.cs", tolerance_lines=5)
        assert tp == 1
        assert fp == 0
        assert fn == 0

    def test_within_tolerance(self):
        detected = [
            {"rule_id": "CA3001", "line_start": 18},  # Within 5 lines of 15
        ]
        expected = [
            {"rule_id": "CA3001", "count": 1, "lines": [15]},
        ]
        tp, fp, fn = match_violations(detected, expected, "test.cs", tolerance_lines=5)
        assert tp == 1
        assert fp == 0
        assert fn == 0

    def test_outside_tolerance(self):
        detected = [
            {"rule_id": "CA3001", "line_start": 50},  # Far from expected line 15
        ]
        expected = [
            {"rule_id": "CA3001", "count": 1, "lines": [15]},
        ]
        tp, fp, fn = match_violations(detected, expected, "test.cs", tolerance_lines=5)
        assert tp == 0
        assert fp == 1
        assert fn == 1

    def test_different_rules_not_matched(self):
        detected = [
            {"rule_id": "CA1040", "line_start": 15},
        ]
        expected = [
            {"rule_id": "CA3001", "count": 1, "lines": [15]},
        ]
        tp, fp, fn = match_violations(detected, expected, "test.cs")
        assert tp == 0
        assert fp == 1
        assert fn == 1

    def test_multiple_expected_entries(self):
        """Two separate expected entries each match one detected violation."""
        detected = [
            {"rule_id": "CA3001", "line_start": 15},
            {"rule_id": "CA3001", "line_start": 28},
        ]
        expected = [
            {"rule_id": "CA3001", "count": 1, "lines": [15]},
            {"rule_id": "CA3001", "count": 1, "lines": [28]},
        ]
        tp, fp, fn = match_violations(detected, expected, "test.cs")
        assert tp == 2
        assert fp == 0
        assert fn == 0

    def test_single_expected_multi_line_matches_once(self):
        """One expected entry with multiple lines matches at most once."""
        detected = [
            {"rule_id": "CA3001", "line_start": 15},
            {"rule_id": "CA3001", "line_start": 28},
        ]
        expected = [
            {"rule_id": "CA3001", "count": 2, "lines": [15, 28]},
        ]
        tp, fp, fn = match_violations(detected, expected, "test.cs")
        # Algorithm matches one expected entry to one detected, so tp=1
        assert tp == 1
        assert fp == 1  # Second detected unmatched
        assert fn == 1  # count=2 minus 1 matched

    def test_empty_detected(self):
        expected = [
            {"rule_id": "CA3001", "count": 2, "lines": [10, 20]},
        ]
        tp, fp, fn = match_violations([], expected, "test.cs")
        assert tp == 0
        assert fp == 0
        assert fn == 2

    def test_empty_expected(self):
        detected = [
            {"rule_id": "CA3001", "line_start": 15},
        ]
        tp, fp, fn = match_violations(detected, [], "test.cs")
        assert tp == 0
        assert fp == 1
        assert fn == 0

    def test_both_empty(self):
        tp, fp, fn = match_violations([], [], "test.cs")
        assert tp == 0
        assert fp == 0
        assert fn == 0


class TestLoadAnalysisResults:
    """Test loading analysis results from different envelope formats."""

    def test_results_envelope(self, tmp_path):
        """Standard { results: {...} } envelope."""
        data = {
            "schema_version": "1.0.0",
            "generated_at": "2026-01-22T10:00:00Z",
            "repo_name": "test",
            "repo_path": "/tmp/test",
            "results": {
                "tool": "roslyn-analyzers",
                "tool_version": "1.0.0",
                "analysis_duration_ms": 100,
                "summary": {"total": 5},
                "files": [{"path": "a.cs"}],
            },
        }
        path = tmp_path / "analysis.json"
        path.write_text(json.dumps(data))

        loaded = load_analysis_results(str(path))
        assert loaded["summary"]["total"] == 5
        assert loaded["files"] == [{"path": "a.cs"}]
        assert loaded["metadata"]["tool"] == "roslyn-analyzers"
        assert loaded["metadata"]["analysis_duration_ms"] == 100

    def test_data_envelope(self, tmp_path):
        """Alternative { data: {...}, metadata: {...} } envelope."""
        data = {
            "metadata": {
                "timestamp": "2026-01-22T10:00:00Z",
                "repo_id": "test-repo",
                "repo_path": "/tmp/test",
            },
            "data": {
                "tool": "roslyn-analyzers",
                "tool_version": "1.0.0",
                "analysis_duration_ms": 200,
                "summary": {"total": 3},
                "files": [],
            },
        }
        path = tmp_path / "analysis.json"
        path.write_text(json.dumps(data))

        loaded = load_analysis_results(str(path))
        assert loaded["summary"]["total"] == 3
        assert loaded["metadata"]["tool"] == "roslyn-analyzers"

    def test_plain_dict(self, tmp_path):
        """Plain dict without results or data wrapper."""
        data = {
            "summary": {"total": 1},
            "files": [],
        }
        path = tmp_path / "analysis.json"
        path.write_text(json.dumps(data))

        loaded = load_analysis_results(str(path))
        assert loaded["summary"]["total"] == 1

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_analysis_results(str(tmp_path / "missing.json"))


class TestLoadGroundTruth:
    """Test loading ground truth."""

    def test_load_from_file(self, tmp_path):
        gt = {"files": {"test.cs": {"expected_violations": []}}}
        path = tmp_path / "gt.json"
        path.write_text(json.dumps(gt))

        loaded = load_ground_truth(str(path))
        assert "files" in loaded

    def test_load_from_directory(self, tmp_path):
        """When given a directory, should load csharp.json from it."""
        gt = {"files": {"test.cs": {}}}
        (tmp_path / "csharp.json").write_text(json.dumps(gt))

        loaded = load_ground_truth(str(tmp_path))
        assert "files" in loaded

    def test_missing_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_ground_truth(str(tmp_path / "nonexistent"))


class TestGetViolationsForFile:
    """Test get_violations_for_file path matching."""

    def test_exact_path_match(self):
        analysis = {
            "files": [
                {"path": "src/test.cs", "violations": [{"rule_id": "CA3001"}]},
                {"path": "src/other.cs", "violations": [{"rule_id": "CA1040"}]},
            ]
        }
        violations = get_violations_for_file(analysis, "src/test.cs")
        assert len(violations) == 1
        assert violations[0]["rule_id"] == "CA3001"

    def test_partial_path_match(self):
        analysis = {
            "files": [
                {"path": "full/path/security/sql_injection.cs", "violations": [
                    {"rule_id": "CA3001"},
                ]},
            ]
        }
        violations = get_violations_for_file(analysis, "security/sql_injection.cs")
        assert len(violations) == 1

    def test_no_match_returns_empty(self):
        analysis = {
            "files": [
                {"path": "src/test.cs", "violations": [{"rule_id": "CA3001"}]},
            ]
        }
        violations = get_violations_for_file(analysis, "nonexistent.cs")
        assert violations == []

    def test_matches_relative_path_field(self):
        analysis = {
            "files": [
                {"path": "full/path/test.cs", "relative_path": "test.cs",
                 "violations": [{"rule_id": "CA3001"}]},
            ]
        }
        violations = get_violations_for_file(analysis, "test.cs")
        assert len(violations) == 1


class TestCountViolationsByRule:
    """Test counting violations by rule."""

    def test_counts_across_files(self):
        analysis = {
            "files": [
                {"violations": [
                    {"rule_id": "CA3001"},
                    {"rule_id": "CA3001"},
                    {"rule_id": "CA1040"},
                ]},
                {"violations": [
                    {"rule_id": "CA3001"},
                ]},
            ]
        }
        assert count_violations_by_rule(analysis, "CA3001") == 3
        assert count_violations_by_rule(analysis, "CA1040") == 1
        assert count_violations_by_rule(analysis, "UNKNOWN") == 0


class TestCountViolationsByCategory:
    """Test counting violations by category."""

    def test_returns_category_count(self):
        analysis = {
            "summary": {
                "violations_by_category": {
                    "security": 10,
                    "design": 5,
                }
            }
        }
        assert count_violations_by_category(analysis, "security") == 10
        assert count_violations_by_category(analysis, "design") == 5
        assert count_violations_by_category(analysis, "other") == 0

    def test_missing_summary_returns_zero(self):
        assert count_violations_by_category({}, "security") == 0
