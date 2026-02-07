"""
Tests for the ToolReadinessSection.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from insights.sections.tool_readiness import ToolReadinessSection


class TestToolReadinessSection:
    """Tests for ToolReadinessSection."""

    def test_config(self) -> None:
        """Test section configuration."""
        section = ToolReadinessSection()
        assert section.config.name == "tool_readiness"
        assert section.config.priority == 0  # First section

    def test_fetch_data_with_real_tools_dir(self) -> None:
        """Test fetch_data with the real tools directory."""
        section = ToolReadinessSection()
        data = section.fetch_data(None, 0)  # run_pk is ignored

        assert "tools" in data
        assert "summary" in data
        assert "ready_for_reports" in data
        assert "needs_investigation" in data
        assert "not_ready" in data
        assert "no_scorecard" in data
        assert data["has_tools"] is True

        # Should find at least some tools
        assert data["summary"]["total"] > 0

    def test_fetch_data_with_empty_tools_dir(self) -> None:
        """Test fetch_data with an empty tools directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            section = ToolReadinessSection(tools_dir=Path(tmpdir))
            data = section.fetch_data(None, 0)

            assert data["has_tools"] is False
            assert data["summary"]["total"] == 0

    def test_fetch_data_with_nonexistent_tools_dir(self) -> None:
        """Test fetch_data with a nonexistent tools directory."""
        section = ToolReadinessSection(tools_dir=Path("/nonexistent/path"))
        data = section.fetch_data(None, 0)

        assert data["has_tools"] is False
        assert data["summary"]["total"] == 0

    def test_parse_scorecard_strong_pass(self) -> None:
        """Test parsing a STRONG_PASS scorecard."""
        section = ToolReadinessSection()
        scorecard = {
            "summary": {
                "decision": "STRONG_PASS",
                "score_percent": 98.5,
                "total_checks": 100,
                "passed": 98,
                "failed": 2,
            },
            "dimensions": [
                {
                    "id": "D1",
                    "name": "Accuracy",
                    "total_checks": 50,
                    "passed": 49,
                    "failed": 1,
                    "score": 0.98,
                }
            ],
            "critical_failures": [],
        }

        result = section._parse_scorecard(scorecard)

        assert result["category"] == "ready"
        assert result["decision"] == "STRONG_PASS"
        assert result["score_percent"] == 98.5
        assert result["total_checks"] == 100
        assert result["passed_checks"] == 98
        assert result["failed_checks"] == 2

    def test_parse_scorecard_weak_pass(self) -> None:
        """Test parsing a WEAK_PASS scorecard."""
        section = ToolReadinessSection()
        scorecard = {
            "summary": {
                "decision": "WEAK_PASS",
                "score_percent": 65.0,
                "total_checks": 10,
                "passed": 6,
                "failed": 4,
            },
        }

        result = section._parse_scorecard(scorecard)

        assert result["category"] == "not_ready"
        assert result["decision"] == "WEAK_PASS"

    def test_parse_scorecard_empty(self) -> None:
        """Test parsing an empty scorecard."""
        section = ToolReadinessSection()
        scorecard = {"summary": {}}

        result = section._parse_scorecard(scorecard)

        assert result["category"] == "no_scorecard"
        assert result["decision"] == "EMPTY"

    def test_parse_evaluation_report(self) -> None:
        """Test parsing an evaluation_report.json."""
        section = ToolReadinessSection()
        report = {
            "decision": "STRONG_PASS",
            "score": 0.91,
            "summary": {
                "passed": 29,
                "failed": 1,
                "total": 30,
                "score_by_category": {
                    "accuracy": 1.0,
                    "coverage": 0.93,
                },
                "passed_by_category": {
                    "accuracy": [8, 8],
                    "coverage": [7, 8],
                },
            },
            "checks": [
                {
                    "check_id": "EC-6",
                    "category": "edge_cases",
                    "passed": False,
                    "message": "Found potential false positives",
                }
            ],
        }

        result = section._parse_evaluation_report(report)

        assert result["category"] == "ready"
        assert result["decision"] == "STRONG_PASS"
        assert result["score_percent"] == 91.0
        assert result["total_checks"] == 30
        assert result["passed_checks"] == 29
        assert result["failed_checks"] == 1
        assert len(result["dimensions"]) == 2
        assert len(result["failed_check_details"]) == 1

    def test_get_template_name(self) -> None:
        """Test template name generation."""
        section = ToolReadinessSection()
        assert section.get_template_name() == "tool_readiness.html.j2"
        assert section.get_markdown_template_name() == "tool_readiness.md.j2"

    def test_fallback_data(self) -> None:
        """Test fallback data structure."""
        section = ToolReadinessSection()
        fallback = section.get_fallback_data()

        assert fallback["tools"] == []
        assert fallback["has_tools"] is False
        assert fallback["summary"]["total"] == 0

    def test_fetch_data_with_synthetic_tools(self) -> None:
        """Test fetch_data with synthetic tool directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tools_dir = Path(tmpdir)

            # Create a tool with a valid scorecard
            tool1_dir = tools_dir / "good-tool" / "evaluation"
            tool1_dir.mkdir(parents=True)
            (tool1_dir / "scorecard.json").write_text(json.dumps({
                "summary": {
                    "decision": "STRONG_PASS",
                    "score_percent": 100.0,
                    "total_checks": 10,
                    "passed": 10,
                    "failed": 0,
                },
            }))

            # Create a tool with only scorecard.md
            tool2_dir = tools_dir / "needs-eval" / "evaluation"
            tool2_dir.mkdir(parents=True)
            (tool2_dir / "scorecard.md").write_text("# Scorecard")

            # Create a tool with no evaluation
            tool3_dir = tools_dir / "no-eval"
            tool3_dir.mkdir(parents=True)

            section = ToolReadinessSection(tools_dir=tools_dir)
            data = section.fetch_data(None, 0)

            assert data["summary"]["total"] == 3
            assert data["summary"]["ready"] == 1
            assert data["summary"]["investigate"] == 1
            assert data["summary"]["no_scorecard"] == 1
