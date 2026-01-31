from scripts.evaluate import generate_scorecard_md


def test_generate_scorecard_md_includes_summary() -> None:
    scorecard = {
        "generated_at": "2026-01-01T00:00:00Z",
        "summary": {
            "decision": "PASS",
            "score_percent": 78.5,
            "total_checks": 12,
            "passed": 10,
            "failed": 2,
            "normalized_score": 3.9,
        },
    }
    output = generate_scorecard_md(scorecard)
    assert "Git-Sizer Evaluation Scorecard" in output
    assert "Decision" in output
    assert "PASS" in output
