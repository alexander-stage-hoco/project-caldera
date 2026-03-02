"""Tests for EvidenceItem text field size caps (P1)."""

from __future__ import annotations

import pytest

from insights.evidence.entities import (
    EvidenceItem,
    MAX_EXCERPT_CHARS,
    MAX_OBSERVATION_CHARS,
    MAX_WHY_IT_MATTERS_CHARS,
)


def _make_evidence(**overrides) -> EvidenceItem:
    defaults = dict(
        evidence_id="E-CCN-001",
        evidence_type="test",
        category="complexity",
        location="src/file.py",
        excerpt="short excerpt",
        observation="short observation",
        why_it_matters="short reason",
        tool_source="test-tool",
        run_pk=1,
    )
    defaults.update(overrides)
    return EvidenceItem(**defaults)


class TestExcerptCap:
    def test_excerpt_capped_at_limit(self):
        long_text = "x" * (MAX_EXCERPT_CHARS + 100)
        ev = _make_evidence(excerpt=long_text)
        assert len(ev.excerpt) == MAX_EXCERPT_CHARS
        assert ev.excerpt.endswith("\u2026")

    def test_observation_capped(self):
        long_text = "y" * (MAX_OBSERVATION_CHARS + 200)
        ev = _make_evidence(observation=long_text)
        assert len(ev.observation) == MAX_OBSERVATION_CHARS
        assert ev.observation.endswith("\u2026")

    def test_why_it_matters_capped(self):
        long_text = "z" * (MAX_WHY_IT_MATTERS_CHARS + 300)
        ev = _make_evidence(why_it_matters=long_text)
        assert len(ev.why_it_matters) == MAX_WHY_IT_MATTERS_CHARS
        assert ev.why_it_matters.endswith("\u2026")

    def test_short_text_unchanged(self):
        ev = _make_evidence(
            excerpt="hello",
            observation="world",
            why_it_matters="ok",
        )
        assert ev.excerpt == "hello"
        assert ev.observation == "world"
        assert ev.why_it_matters == "ok"

    def test_exact_limit_unchanged(self):
        text = "a" * MAX_EXCERPT_CHARS
        ev = _make_evidence(excerpt=text)
        assert ev.excerpt == text
        assert len(ev.excerpt) == MAX_EXCERPT_CHARS
