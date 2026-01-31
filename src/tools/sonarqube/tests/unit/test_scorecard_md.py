from scripts.evaluate import generate_scorecard_md


def test_generate_scorecard_md_includes_summary() -> None:
    scorecard = {
        "generated_at": "2026-01-01T00:00:00Z",
        "summary": {
            "decision": "PASS",
            "score_percent": 77.0,
            "total_checks": 18,
            "passed": 14,
            "failed": 4,
            "normalized_score": 3.85,
        },
    }
    output = generate_scorecard_md(scorecard)
    assert "SonarQube Evaluation Scorecard" in output
    assert "Decision" in output
    assert "PASS" in output
