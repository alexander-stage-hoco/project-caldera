"""Tests for architecture reviewer data models."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from models import (
    DimensionResult,
    Finding,
    ReviewResult,
    ReviewSummary,
)


class TestFinding:
    def test_valid_construction(self) -> None:
        f = Finding(severity="error", rule_id="TEST_RULE", message="test message")
        assert f.severity == "error"
        assert f.rule_id == "TEST_RULE"
        assert f.message == "test message"

    def test_rejects_invalid_severity(self) -> None:
        with pytest.raises(ValueError, match="severity"):
            Finding(severity="critical", rule_id="TEST", message="msg")

    def test_rejects_empty_rule_id(self) -> None:
        with pytest.raises(ValueError, match="rule_id"):
            Finding(severity="info", rule_id="", message="msg")

    def test_rejects_empty_message(self) -> None:
        with pytest.raises(ValueError, match="message"):
            Finding(severity="info", rule_id="TEST", message="")

    def test_rejects_invalid_category(self) -> None:
        with pytest.raises(ValueError, match="category"):
            Finding(severity="info", rule_id="TEST", message="msg", category="bad")

    def test_rejects_negative_line(self) -> None:
        with pytest.raises(ValueError, match="line"):
            Finding(severity="info", rule_id="TEST", message="msg", line=0)

    def test_optional_fields_default_none(self) -> None:
        f = Finding(severity="info", rule_id="TEST", message="msg")
        assert f.category is None
        assert f.file is None
        assert f.line is None
        assert f.evidence is None
        assert f.recommendation is None

    def test_to_dict_minimal(self) -> None:
        f = Finding(severity="info", rule_id="TEST", message="msg")
        d = f.to_dict()
        assert d == {"severity": "info", "rule_id": "TEST", "message": "msg"}

    def test_to_dict_full(self, sample_finding: Finding) -> None:
        d = sample_finding.to_dict()
        assert "category" in d
        assert "file" in d
        assert "line" in d
        assert "evidence" in d
        assert "recommendation" in d


class TestDimensionResult:
    def test_valid_construction(self) -> None:
        dr = DimensionResult(
            dimension="test_dim", weight=0.15, status="pass", score=5
        )
        assert dr.dimension == "test_dim"
        assert dr.findings == []

    def test_rejects_score_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="score"):
            DimensionResult(dimension="d", weight=0.1, status="pass", score=6)
        with pytest.raises(ValueError, match="score"):
            DimensionResult(dimension="d", weight=0.1, status="pass", score=0)

    def test_rejects_invalid_status(self) -> None:
        with pytest.raises(ValueError, match="status"):
            DimensionResult(dimension="d", weight=0.1, status="bad", score=3)

    def test_rejects_weight_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="weight"):
            DimensionResult(dimension="d", weight=1.5, status="pass", score=5)

    def test_to_dict(self, sample_dimension_result: DimensionResult) -> None:
        d = sample_dimension_result.to_dict()
        assert d["dimension"] == "entity_persistence_pattern"
        assert len(d["findings"]) == 1


class TestReviewSummary:
    def test_valid_construction(self) -> None:
        rs = ReviewSummary(
            total_findings=5,
            by_severity={"error": 1, "warning": 3, "info": 1},
            overall_status="WEAK_PASS",
            overall_score=3.2,
            dimensions_reviewed=5,
        )
        assert rs.total_findings == 5

    def test_rejects_missing_severity_key(self) -> None:
        with pytest.raises(ValueError, match="by_severity"):
            ReviewSummary(
                total_findings=0,
                by_severity={"error": 0, "warning": 0},
                overall_status="STRONG_PASS",
                overall_score=5.0,
                dimensions_reviewed=1,
            )

    def test_rejects_invalid_overall_status(self) -> None:
        with pytest.raises(ValueError, match="overall_status"):
            ReviewSummary(
                total_findings=0,
                by_severity={"error": 0, "warning": 0, "info": 0},
                overall_status="EXCELLENT",
                overall_score=5.0,
                dimensions_reviewed=1,
            )


class TestReviewResult:
    def _make_result(self) -> ReviewResult:
        dim = DimensionResult(
            dimension="test", weight=1.0, status="pass", score=5
        )
        summary = ReviewSummary(
            total_findings=0,
            by_severity={"error": 0, "warning": 0, "info": 0},
            overall_status="STRONG_PASS",
            overall_score=5.0,
            dimensions_reviewed=1,
        )
        return ReviewResult(
            review_id=ReviewResult.create_id(),
            timestamp=ReviewResult.create_timestamp(),
            target="test-tool",
            review_type="tool_implementation",
            dimensions=[dim],
            summary=summary,
        )

    def test_to_dict_matches_schema(self) -> None:
        result = self._make_result()
        d = result.to_dict()
        schema_path = Path(__file__).parent.parent / "schemas" / "review_result.schema.json"
        schema = json.loads(schema_path.read_text())
        jsonschema.validate(d, schema)

    def test_roundtrip(self) -> None:
        result = self._make_result()
        d = result.to_dict()
        json_str = json.dumps(d)
        loaded = json.loads(json_str)
        assert loaded["target"] == "test-tool"
        assert loaded["review_type"] == "tool_implementation"
        assert len(loaded["dimensions"]) == 1
        assert loaded["summary"]["overall_status"] == "STRONG_PASS"

    def test_rejects_invalid_review_type(self) -> None:
        with pytest.raises(ValueError, match="review_type"):
            ReviewResult(
                review_id="id",
                timestamp="ts",
                target="t",
                review_type="invalid",
                dimensions=[],
                summary=ReviewSummary(
                    total_findings=0,
                    by_severity={"error": 0, "warning": 0, "info": 0},
                    overall_status="PASS",
                    overall_score=4.0,
                    dimensions_reviewed=1,
                ),
            )
