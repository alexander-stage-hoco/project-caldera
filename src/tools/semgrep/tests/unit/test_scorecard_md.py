from scripts.evaluate import generate_scorecard_md


def test_generate_scorecard_md_includes_summary() -> None:
    scorecard = {
        "generated_at": "2026-01-01T00:00:00Z",
        "summary": {
            "decision": "PASS",
            "score_percent": 80.0,
            "total_checks": 10,
            "passed": 8,
            "failed": 2,
            "normalized_score": 4.0,
        },
    }
    output = generate_scorecard_md(scorecard)
    assert "Semgrep Evaluation Scorecard" in output
    assert "Decision" in output
    assert "PASS" in output
