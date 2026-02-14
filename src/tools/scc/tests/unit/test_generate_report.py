"""Tests for scripts/generate_report.py - scorecard report generation."""
from __future__ import annotations

import pytest
from scripts.generate_report import generate_scorecard


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def evidence():
    """Sample evidence dict."""
    return {
        "run_id": "test-run-001",
        "items": [
            {"data": {"language": "Python"}},
            {"data": {"language": "Python"}},
            {"data": {"language": "C#"}},
            {"data": {"language": "JavaScript"}},
        ],
        "summary": {
            "languages": 3,
            "total_files": 10,
            "total_loc": 500,
            "total_lines": 700,
            "total_comments": 100,
            "total_complexity": 25,
            "comment_ratio": 0.143,
        },
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGenerateScorecard:
    def test_basic_structure(self, evidence, tmp_path):
        timing_path = tmp_path / "timing.md"
        result = generate_scorecard(evidence, timing_path)
        assert "scc Evaluation Scorecard" in result
        assert "STRONG PASS" in result

    def test_contains_run_id(self, evidence, tmp_path):
        result = generate_scorecard(evidence, tmp_path / "timing.md")
        assert "test-run-001" in result

    def test_contains_language_counts(self, evidence, tmp_path):
        result = generate_scorecard(evidence, tmp_path / "timing.md")
        # Should have counted 2 Python, 1 C#, 1 JavaScript
        assert "2 file(s)" in result  # Python
        assert "1 file(s)" in result  # C# or JavaScript

    def test_contains_evidence_summary(self, evidence, tmp_path):
        result = generate_scorecard(evidence, tmp_path / "timing.md")
        assert "500" in result  # total_loc
        assert "10" in result  # total_files
        assert "25" in result  # total_complexity

    def test_includes_timing_if_available(self, evidence, tmp_path):
        timing_path = tmp_path / "timing.md"
        timing_path.write_text("Execution time: 0.5s")
        result = generate_scorecard(evidence, timing_path)
        assert "Execution time: 0.5s" in result

    def test_no_timing_file(self, evidence, tmp_path):
        result = generate_scorecard(evidence, tmp_path / "nonexistent.md")
        # Should still generate without error
        assert "scc Evaluation Scorecard" in result

    def test_score_table(self, evidence, tmp_path):
        result = generate_scorecard(evidence, tmp_path / "timing.md")
        assert "Output Quality" in result
        assert "Integration Fit" in result
        assert "Reliability" in result
        assert "Performance" in result
        assert "Installation" in result
        assert "4.80" in result
