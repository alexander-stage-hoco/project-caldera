"""Tests for SonarQube LLM judges.

Includes tests for M11 (Issue Accuracy Judge dual-mode evaluation):
- Heuristic fallback mode testing
- Evidence collection with ground truth
- Handling when no issues found
- Sub-score calculation validation
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from evaluation.llm.judges.actionability import ActionabilityJudge
from evaluation.llm.judges.coverage_completeness import CoverageCompletenessJudge
from evaluation.llm.judges.issue_accuracy import IssueAccuracyJudge


def _write_analysis(tmp_path: Path, data: dict) -> Path:
    """Write analysis data to a temporary file."""
    path = tmp_path / "analysis.json"
    path.write_text(json.dumps(data))
    return path


# ============================================
# Existing tests
# ============================================

def test_issue_accuracy_uses_results(sample_sonarqube_export, tmp_path, project_root):
    """IssueAccuracyJudge reads issues from results wrapper."""
    analysis_path = _write_analysis(tmp_path, sample_sonarqube_export)
    judge = IssueAccuracyJudge(analysis_path=analysis_path, working_dir=project_root)

    result = judge.evaluate()

    assert "No issues found" not in result.reasoning
    assert "Total issues: 2" in result.evidence_cited


def test_coverage_completeness_uses_results(sample_sonarqube_export, tmp_path, project_root):
    """CoverageCompletenessJudge reads metrics/components/rules from results wrapper."""
    analysis_path = _write_analysis(tmp_path, sample_sonarqube_export)
    judge = CoverageCompletenessJudge(analysis_path=analysis_path, working_dir=project_root)

    result = judge.evaluate()

    assert "Metrics in catalog: 2" in result.evidence_cited
    assert "Components extracted: 3" in result.evidence_cited
    assert "Rules hydrated: 2" in result.evidence_cited


def test_actionability_uses_results(sample_sonarqube_export, tmp_path, project_root):
    """ActionabilityJudge reads quality gate and insights from results wrapper."""
    analysis_path = _write_analysis(tmp_path, sample_sonarqube_export)
    judge = ActionabilityJudge(analysis_path=analysis_path, working_dir=project_root)

    result = judge.evaluate()

    assert "Quality gate status: OK" in result.evidence_cited
    assert "Hotspots identified: 1" in result.evidence_cited


# ============================================
# M11: IssueAccuracyJudge comprehensive tests
# ============================================

class TestIssueAccuracyJudgeHeuristics:
    """Tests for IssueAccuracyJudge heuristic evaluation (M11)."""

    def test_handles_empty_issues(self, tmp_path, project_root):
        """IssueAccuracyJudge should handle empty issue list gracefully."""
        data = {
            "results": {
                "issues": {
                    "items": [],
                    "rollups": {},
                },
            },
        }
        analysis_path = _write_analysis(tmp_path, data)
        judge = IssueAccuracyJudge(analysis_path=analysis_path, working_dir=project_root)

        result = judge.evaluate()

        assert result.score == 3  # Neutral score for no issues
        assert "No issues found" in result.reasoning
        assert result.confidence == 0.5

    def test_bug_classification_with_valid_keywords(self, tmp_path, project_root):
        """IssueAccuracyJudge should score high for bugs with valid keywords."""
        data = {
            "results": {
                "issues": {
                    "items": [
                        {"type": "BUG", "message": "Potential null pointer dereference", "rule": "S1234"},
                        {"type": "BUG", "message": "Integer overflow may occur", "rule": "S2345"},
                        {"type": "BUG", "message": "Memory leak detected", "rule": "S3456"},
                        {"type": "BUG", "message": "Uncaught exception possible", "rule": "S4567"},
                    ],
                    "rollups": {},
                },
            },
        }
        analysis_path = _write_analysis(tmp_path, data)
        judge = IssueAccuracyJudge(analysis_path=analysis_path, working_dir=project_root)

        result = judge.evaluate()

        assert result.sub_scores["bug_classification"] >= 4  # High score for keyword matches
        assert result.dimension == "issue_accuracy"

    def test_bug_classification_with_no_keywords(self, tmp_path, project_root):
        """IssueAccuracyJudge should score low for bugs without valid keywords."""
        data = {
            "results": {
                "issues": {
                    "items": [
                        {"type": "BUG", "message": "Consider refactoring this method", "rule": "S1234"},
                        {"type": "BUG", "message": "Use a different approach", "rule": "S2345"},
                    ],
                    "rollups": {},
                },
            },
        }
        analysis_path = _write_analysis(tmp_path, data)
        judge = IssueAccuracyJudge(analysis_path=analysis_path, working_dir=project_root)

        result = judge.evaluate()

        assert result.sub_scores["bug_classification"] < 3  # Low score for no keyword matches

    def test_vulnerability_classification_with_security_keywords(self, tmp_path, project_root):
        """IssueAccuracyJudge should score high for vulns with security keywords."""
        data = {
            "results": {
                "issues": {
                    "items": [
                        {"type": "VULNERABILITY", "message": "SQL injection vulnerability", "rule": "S3649"},
                        {"type": "VULNERABILITY", "message": "Hardcoded password detected", "rule": "S2068"},
                        {"type": "VULNERABILITY", "message": "Sensitive data exposure", "rule": "S5131"},
                    ],
                    "rollups": {},
                },
            },
        }
        analysis_path = _write_analysis(tmp_path, data)
        judge = IssueAccuracyJudge(analysis_path=analysis_path, working_dir=project_root)

        result = judge.evaluate()

        assert result.sub_scores["vulnerability_classification"] >= 4  # High score

    def test_vulnerability_classification_rule_based(self, tmp_path, project_root):
        """IssueAccuracyJudge should detect keywords in rule names too."""
        data = {
            "results": {
                "issues": {
                    "items": [
                        {"type": "VULNERABILITY", "message": "Issue found", "rule": "sql-injection"},
                        {"type": "VULNERABILITY", "message": "Issue detected", "rule": "auth-bypass"},
                    ],
                    "rollups": {},
                },
            },
        }
        analysis_path = _write_analysis(tmp_path, data)
        judge = IssueAccuracyJudge(analysis_path=analysis_path, working_dir=project_root)

        result = judge.evaluate()

        assert result.sub_scores["vulnerability_classification"] >= 4

    def test_code_smell_classification_with_maintainability_keywords(self, tmp_path, project_root):
        """IssueAccuracyJudge should score high for smells with maintainability keywords."""
        data = {
            "results": {
                "issues": {
                    "items": [
                        {"type": "CODE_SMELL", "message": "High cognitive complexity", "rule": "S3776"},
                        {"type": "CODE_SMELL", "message": "Duplicate code block", "rule": "S1192"},
                        {"type": "CODE_SMELL", "message": "Unused variable", "rule": "S1481"},
                        {"type": "CODE_SMELL", "message": "Method is too long", "rule": "S138"},
                    ],
                    "rollups": {},
                },
            },
        }
        analysis_path = _write_analysis(tmp_path, data)
        judge = IssueAccuracyJudge(analysis_path=analysis_path, working_dir=project_root)

        result = judge.evaluate()

        assert result.sub_scores["code_smell_classification"] >= 4

    def test_weighted_average_calculation(self, tmp_path, project_root):
        """IssueAccuracyJudge should calculate weighted average correctly."""
        data = {
            "results": {
                "issues": {
                    "items": [
                        # All bugs have valid keywords (score 5)
                        {"type": "BUG", "message": "Null pointer error", "rule": "S1234"},
                        # All vulns have valid keywords (score 5)
                        {"type": "VULNERABILITY", "message": "SQL injection", "rule": "S3649"},
                        # All smells have valid keywords (score 5)
                        {"type": "CODE_SMELL", "message": "High complexity", "rule": "S3776"},
                    ],
                    "rollups": {},
                },
            },
        }
        analysis_path = _write_analysis(tmp_path, data)
        judge = IssueAccuracyJudge(analysis_path=analysis_path, working_dir=project_root)

        result = judge.evaluate()

        # With all perfect sub-scores, overall should be high
        assert result.score >= 4
        assert "sub_scores" in result.to_dict()

    def test_neutral_score_when_no_issues_of_type(self, tmp_path, project_root):
        """IssueAccuracyJudge should give neutral score when issue type is missing."""
        data = {
            "results": {
                "issues": {
                    "items": [
                        # Only code smells, no bugs or vulnerabilities
                        {"type": "CODE_SMELL", "message": "Unused variable", "rule": "S1481"},
                        {"type": "CODE_SMELL", "message": "Duplicate code", "rule": "S1192"},
                    ],
                    "rollups": {},
                },
            },
        }
        analysis_path = _write_analysis(tmp_path, data)
        judge = IssueAccuracyJudge(analysis_path=analysis_path, working_dir=project_root)

        result = judge.evaluate()

        # Bug and vulnerability scores should be neutral (3)
        assert result.sub_scores["bug_classification"] == 3
        assert result.sub_scores["vulnerability_classification"] == 3
        # Code smell score should be based on actual evaluation
        assert result.sub_scores["code_smell_classification"] >= 1

    def test_evidence_collection_structure(self, tmp_path, project_root):
        """IssueAccuracyJudge.collect_evidence should return expected structure."""
        data = {
            "results": {
                "issues": {
                    "items": [
                        {"type": "BUG", "message": "Bug 1", "rule": "S1"},
                        {"type": "VULNERABILITY", "message": "Vuln 1", "rule": "S2"},
                        {"type": "CODE_SMELL", "message": "Smell 1", "rule": "S3"},
                    ],
                    "rollups": {"total": 3},
                },
            },
        }
        analysis_path = _write_analysis(tmp_path, data)
        judge = IssueAccuracyJudge(analysis_path=analysis_path, working_dir=project_root)

        evidence = judge.collect_evidence()

        assert "total_issues" in evidence
        assert "sampled_bugs" in evidence
        assert "sampled_vulnerabilities" in evidence
        assert "sampled_code_smells" in evidence
        assert "rollups" in evidence
        assert evidence["total_issues"] == 3

    def test_samples_limited_to_10(self, tmp_path, project_root):
        """IssueAccuracyJudge should sample at most 10 issues per type."""
        bugs = [{"type": "BUG", "message": f"Bug {i}", "rule": f"S{i}"} for i in range(15)]
        data = {
            "results": {
                "issues": {
                    "items": bugs,
                    "rollups": {},
                },
            },
        }
        analysis_path = _write_analysis(tmp_path, data)
        judge = IssueAccuracyJudge(analysis_path=analysis_path, working_dir=project_root)

        evidence = judge.collect_evidence()

        assert len(evidence["sampled_bugs"]) == 10


class TestIssueAccuracyJudgeProperties:
    """Tests for IssueAccuracyJudge properties."""

    def test_dimension_name(self, tmp_path, project_root):
        """IssueAccuracyJudge should have correct dimension name."""
        data = {"results": {"issues": {"items": [], "rollups": {}}}}
        analysis_path = _write_analysis(tmp_path, data)
        judge = IssueAccuracyJudge(analysis_path=analysis_path, working_dir=project_root)

        assert judge.dimension_name == "issue_accuracy"

    def test_weight(self, tmp_path, project_root):
        """IssueAccuracyJudge should have correct weight."""
        data = {"results": {"issues": {"items": [], "rollups": {}}}}
        analysis_path = _write_analysis(tmp_path, data)
        judge = IssueAccuracyJudge(analysis_path=analysis_path, working_dir=project_root)

        assert judge.weight == 0.35

    def test_default_prompt_contains_evidence_placeholder(self, tmp_path, project_root):
        """IssueAccuracyJudge default prompt should have {{ evidence }} placeholder."""
        data = {"results": {"issues": {"items": [], "rollups": {}}}}
        analysis_path = _write_analysis(tmp_path, data)
        judge = IssueAccuracyJudge(analysis_path=analysis_path, working_dir=project_root)

        prompt = judge.get_default_prompt()

        assert "{{ evidence }}" in prompt
        assert "Bug classification" in prompt
        assert "Vulnerability classification" in prompt
        assert "Code smell classification" in prompt


class TestIssueAccuracyJudgeLegacyFormat:
    """Tests for IssueAccuracyJudge with legacy data format."""

    def test_handles_caldera_envelope_format(self, tmp_path, project_root):
        """IssueAccuracyJudge should handle Caldera envelope format."""
        data = {
            "data": {
                "results": {
                    "issues": {
                        "items": [
                            {"type": "BUG", "message": "Null error", "rule": "S1234"},
                        ],
                        "rollups": {},
                    },
                },
            },
            "metadata": {"version": "1.0"},
        }
        analysis_path = _write_analysis(tmp_path, data)
        judge = IssueAccuracyJudge(analysis_path=analysis_path, working_dir=project_root)

        result = judge.evaluate()

        assert result.score >= 1
        assert "Total issues: 1" in result.evidence_cited

    def test_handles_flat_format(self, tmp_path, project_root):
        """IssueAccuracyJudge should handle flat data format."""
        data = {
            "issues": {
                "items": [
                    {"type": "CODE_SMELL", "message": "Cognitive complexity", "rule": "S3776"},
                ],
                "rollups": {},
            },
        }
        analysis_path = _write_analysis(tmp_path, data)
        judge = IssueAccuracyJudge(analysis_path=analysis_path, working_dir=project_root)

        result = judge.evaluate()

        assert result.score >= 1
