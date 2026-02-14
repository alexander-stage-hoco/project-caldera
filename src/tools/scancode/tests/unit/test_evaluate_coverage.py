"""Tests targeting uncovered paths in evaluate.py for coverage improvement."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.evaluate import (
    determine_decision,
    find_analysis_files,
    generate_scorecard_json,
    generate_scorecard_md,
    normalize_analysis,
    evaluate_repository,
)
from scripts.checks import CheckResult, EvaluationReport


class TestDetermineDecision:
    """Tests for all 4 decision branches."""

    def test_strong_pass(self) -> None:
        assert determine_decision(0.85) == "STRONG_PASS"

    def test_pass(self) -> None:
        assert determine_decision(0.72) == "PASS"

    def test_weak_pass(self) -> None:
        assert determine_decision(0.62) == "WEAK_PASS"

    def test_fail(self) -> None:
        assert determine_decision(0.50) == "FAIL"


class TestNormalizeAnalysis:
    """Tests for analysis format normalization."""

    def test_caldera_envelope_format(self) -> None:
        analysis = {
            "metadata": {
                "schema_version": "1.0.0",
                "repo_name": "test-repo",
                "repo_path": "/tmp/repo",
                "timestamp": "2025-01-01T00:00:00Z",
                "tool_name": "scancode",
                "tool_version": "1.0.0",
            },
            "data": {
                "summary": {"total_files": 5},
                "findings": [],
            },
        }
        result = normalize_analysis(analysis)
        assert result["summary"]["total_files"] == 5
        assert result["schema_version"] == "1.0.0"
        assert result["repository"] == "test-repo"

    def test_legacy_vulcan_format(self) -> None:
        analysis = {
            "schema_version": "0.9",
            "repo_name": "legacy-repo",
            "repo_path": "/tmp/legacy",
            "generated_at": "2025-01-01T00:00:00Z",
            "results": {
                "tool": "scancode",
                "tool_version": "0.9",
                "findings": [],
            },
        }
        result = normalize_analysis(analysis)
        assert result["findings"] == []
        assert result["schema_version"] == "0.9"

    def test_already_normalized(self) -> None:
        analysis = {"findings": [], "summary": {}}
        result = normalize_analysis(analysis)
        assert result is analysis


class TestGenerateScorecardJson:
    """Tests for scorecard JSON generation."""

    def test_scorecard_with_categories(self) -> None:
        report = EvaluationReport(repository="test-repo")
        report.add_result(CheckResult(
            check_id="AC-1", category="accuracy",
            passed=True, message="OK",
        ))
        report.add_result(CheckResult(
            check_id="CV-1", category="coverage",
            passed=False, message="Missing",
        ))
        scorecard = generate_scorecard_json([report], 2, 1)

        assert scorecard["tool"] == "scancode"
        assert scorecard["summary"]["total_checks"] == 2
        assert scorecard["summary"]["passed"] == 1
        assert len(scorecard["dimensions"]) == 2
        assert scorecard["summary"]["decision"] in (
            "STRONG_PASS", "PASS", "WEAK_PASS", "FAIL",
        )

    def test_empty_reports(self) -> None:
        scorecard = generate_scorecard_json([], 0, 0)
        assert scorecard["summary"]["total_checks"] == 0
        assert scorecard["dimensions"] == []


class TestGenerateScorecardMd:
    """Tests for markdown scorecard generation."""

    def test_generates_markdown(self, tmp_path: Path) -> None:
        scorecard = {
            "generated_at": "2025-01-01T00:00:00Z",
            "summary": {
                "total_checks": 10,
                "passed": 8,
                "failed": 2,
                "normalized_score": 4.0,
                "decision": "STRONG_PASS",
                "score_percent": 80.0,
            },
            "dimensions": [
                {
                    "name": "Accuracy",
                    "total_checks": 5,
                    "passed": 4,
                    "score": 4.0,
                    "weight": 0.5,
                },
            ],
            "critical_failures": [],
            "thresholds": {
                "STRONG_PASS": ">= 4.0",
                "FAIL": "< 3.0",
            },
        }
        out = tmp_path / "scorecard.md"
        generate_scorecard_md(scorecard, out)
        content = out.read_text()
        assert "# Scancode License Analysis Evaluation Scorecard" in content
        assert "STRONG_PASS" in content
        assert "Accuracy" in content


class TestFindAnalysisFiles:
    """Tests for analysis file discovery."""

    def test_direct_json_pattern(self, tmp_path: Path) -> None:
        analysis_dir = tmp_path / "analysis"
        analysis_dir.mkdir()
        gt_dir = tmp_path / "gt"
        gt_dir.mkdir()

        (analysis_dir / "my-repo.json").write_text("{}")
        (gt_dir / "my-repo.json").write_text("{}")
        (analysis_dir / "no-match.json").write_text("{}")

        pairs = find_analysis_files(analysis_dir, gt_dir)
        assert len(pairs) == 1
        assert pairs[0][0].name == "my-repo.json"

    def test_subdirectory_output_pattern(self, tmp_path: Path) -> None:
        analysis_dir = tmp_path / "analysis"
        gt_dir = tmp_path / "gt"
        analysis_dir.mkdir()
        gt_dir.mkdir()

        subdir = analysis_dir / "run-001"
        subdir.mkdir()
        output = {
            "metadata": {"repo_path": "/tmp/test-repo"},
        }
        (subdir / "output.json").write_text(json.dumps(output))
        (gt_dir / "test-repo.json").write_text("{}")

        pairs = find_analysis_files(analysis_dir, gt_dir)
        assert len(pairs) == 1

    def test_no_matches(self, tmp_path: Path) -> None:
        analysis_dir = tmp_path / "analysis"
        analysis_dir.mkdir()
        gt_dir = tmp_path / "gt"
        gt_dir.mkdir()

        pairs = find_analysis_files(analysis_dir, gt_dir)
        assert pairs == []


class TestEvaluateRepository:
    """Tests for full repository evaluation."""

    def test_evaluates_with_all_check_categories(self, tmp_path: Path) -> None:
        analysis = {
            "metadata": {"tool_name": "scancode", "tool_version": "1.0.0"},
            "data": {
                "summary": {
                    "total_files": 3,
                    "files_with_licenses": 2,
                    "license_coverage": 66.7,
                    "overall_risk": "low",
                    "licenses_found": ["MIT"],
                },
                "findings": [
                    {
                        "file_path": "LICENSE",
                        "spdx_id": "MIT",
                        "category": "permissive",
                        "confidence": 1.0,
                        "match_type": "file",
                    },
                ],
                "files": {
                    "LICENSE": {
                        "licenses": ["MIT"],
                        "categories": ["permissive"],
                        "risk_level": "low",
                    },
                },
                "directories": [],
                "elapsed_seconds": 1.0,
            },
        }
        gt = {
            "repository": "test-repo",
            "expected_licenses": ["MIT"],
            "expected_license_count": 1,
            "risk_level": "low",
            "files": {
                "LICENSE": {"licenses": ["MIT"]},
            },
        }
        analysis_path = tmp_path / "analysis.json"
        analysis_path.write_text(json.dumps(analysis))
        gt_path = tmp_path / "gt.json"
        gt_path.write_text(json.dumps(gt))

        report = evaluate_repository(analysis_path, gt_path)
        assert report.total_checks > 0
        categories = {r.category for r in report.results}
        assert len(categories) >= 2  # At least accuracy + something else
