from scripts.evaluate import generate_scorecard_md


def test_generate_scorecard_md_includes_summary() -> None:
    scorecard = {
        "generated_at": "2026-01-01T00:00:00Z",
        "summary": {
            "decision": "PASS",
            "score_percent": 82.0,
            "total_checks": 14,
            "passed": 12,
            "failed": 2,
            "normalized_score": 4.1,
            "overall": {
                "total": 14,
                "passed": 12,
                "pass_rate": 12 / 14,
            },
        },
    }
    output = generate_scorecard_md(scorecard)
    assert "Trivy Evaluation Scorecard" in output
    assert "Decision" in output
    assert "PASS" in output
