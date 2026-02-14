"""Tests for scripts/llm_judge.py - LLM-as-Judge dimension evaluation."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from scripts.llm_judge import (
    judge_dimension,
    judge_output_richness,
    judge_transformation_elegance,
    judge_documentation_quality,
    run_llm_judgments,
    JUDGE_PROMPT_TEMPLATE,
)


# ---------------------------------------------------------------------------
# Tests: judge_dimension
# ---------------------------------------------------------------------------

class TestJudgeDimension:
    @patch("scripts.llm_judge.get_provider", return_value=None)
    def test_no_provider_returns_fallback(self, mock_provider):
        result = judge_dimension("Test Dimension", "context", {"key": "val"})
        assert result["score"] is None
        assert result["llm_available"] is False
        assert "skipped" in result["reasoning"].lower()

    @patch("scripts.llm_judge.get_provider")
    def test_successful_judgment(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "score": 4,
            "reasoning": "Good output",
            "evidence": ["test evidence"]
        })
        mock_provider.complete.return_value = mock_response
        mock_get_provider.return_value = mock_provider

        result = judge_dimension("Test", "ctx", {"k": "v"})
        assert result["score"] == 4
        assert result["llm_available"] is True

    @patch("scripts.llm_judge.get_provider")
    def test_unparseable_response(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "This is not JSON at all"
        mock_provider.complete.return_value = mock_response
        mock_get_provider.return_value = mock_provider

        result = judge_dimension("Test", "ctx", {"k": "v"})
        assert result["score"] is None
        assert result["llm_available"] is True

    @patch("scripts.llm_judge.get_provider")
    def test_provider_error(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.complete.side_effect = RuntimeError("API error")
        mock_get_provider.return_value = mock_provider

        result = judge_dimension("Test", "ctx", {"k": "v"})
        assert result["score"] is None
        assert "error" in result


# ---------------------------------------------------------------------------
# Tests: Specific judge functions
# ---------------------------------------------------------------------------

class TestJudgeOutputRichness:
    @patch("scripts.llm_judge.get_provider", return_value=None)
    def test_no_provider(self, _):
        result = judge_output_richness([
            {"Name": "Python", "Code": 100, "Complexity": 5, "Bytes": 2000}
        ])
        assert result["llm_available"] is False

    @patch("scripts.llm_judge.get_provider", return_value=None)
    def test_empty_output(self, _):
        result = judge_output_richness([])
        assert result["llm_available"] is False


class TestJudgeTransformationElegance:
    @patch("scripts.llm_judge.get_provider", return_value=None)
    def test_no_provider(self, _):
        result = judge_transformation_elegance("code = 1", {"items": [{"data": {"key": "val"}}], "summary": {}})
        assert result["llm_available"] is False

    @patch("scripts.llm_judge.get_provider", return_value=None)
    def test_empty_evidence(self, _):
        result = judge_transformation_elegance("", {})
        assert result["llm_available"] is False


class TestJudgeDocumentationQuality:
    @patch("scripts.llm_judge.get_provider", return_value=None)
    def test_readme_exists(self, _, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Install\n\nUsage example\n\n## License\nMIT")
        result = judge_documentation_quality(readme)
        assert result["llm_available"] is False

    @patch("scripts.llm_judge.get_provider", return_value=None)
    def test_readme_missing(self, _, tmp_path):
        result = judge_documentation_quality(tmp_path / "MISSING.md")
        assert result["llm_available"] is False


# ---------------------------------------------------------------------------
# Tests: run_llm_judgments
# ---------------------------------------------------------------------------

class TestRunLlmJudgments:
    @patch("scripts.llm_judge.get_provider", return_value=None)
    def test_runs_all_judgments(self, _, tmp_path):
        # Create minimal file structure
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "raw_scc_output.json").write_text(json.dumps([{"Name": "Python", "Code": 100}]))
        (output_dir / "evidence_output.json").write_text(json.dumps({"items": [], "summary": {}}))

        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "transform.py").write_text("# transform code")

        (tmp_path / "README.md").write_text("# README")

        results = run_llm_judgments(tmp_path)
        assert "output_richness" in results
        assert "transformation_elegance" in results
        assert "documentation_quality" in results

    @patch("scripts.llm_judge.get_provider", return_value=None)
    def test_handles_missing_files(self, _, tmp_path):
        results = run_llm_judgments(tmp_path)
        assert "output_richness" in results
        assert "transformation_elegance" in results
        assert "documentation_quality" in results
