from scripts.evaluate import generate_scorecard_md


def test_generate_scorecard_md_includes_summary() -> None:
    scorecard = {
        "generated_at": "2026-01-01T00:00:00Z",
        "summary": {
            "decision": "PASS",
            "score_percent": 75.0,
            "total_checks": 20,
            "passed": 15,
            "failed": 5,
            "normalized_score": 3.75,
        },
    }
    output = generate_scorecard_md(scorecard)
    assert "Roslyn Analyzers Evaluation Scorecard" in output
    assert "Decision" in output
    assert "PASS" in output
