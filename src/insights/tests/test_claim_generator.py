"""Tests for ClaimGenerator and individual claim rules."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from insights.evidence.claim_generator import (
    ClaimGenerator,
    CoverageGapRule,
    HighCouplingRule,
    KnowledgeSiloRule,
    SecurityExposureRule,
    _parse_float_from_excerpt,
    _parse_int_from_excerpt,
)
from insights.evidence.entities import EvidenceItem


def _evidence(eid: str, cat: str, location: str = "src/file.py", excerpt: str = "") -> EvidenceItem:
    return EvidenceItem(
        evidence_id=eid,
        evidence_type="test",
        category=cat,  # type: ignore[arg-type]
        location=location,
        excerpt=excerpt or f"test excerpt for {eid}",
        observation="test",
        why_it_matters="test",
        tool_source="test-tool",
        run_pk=1,
    )


def _mock_fetcher(results: dict[str, list[dict]] | None = None) -> MagicMock:
    fetcher = MagicMock()
    data = results or {}
    fetcher.fetch.side_effect = lambda name, pk, **kw: data.get(name, [])
    return fetcher


class TestHighCouplingRule:
    def test_fires_when_fan_out_exceeds_threshold(self):
        rule = HighCouplingRule()
        ev = _evidence("E-COUP-001", "coupling", excerpt="fan_in=2, fan_out=20, coupling=22")
        claims = rule.evaluate([ev], _mock_fetcher(), 1)
        assert len(claims) == 1
        assert "high outbound coupling" in claims[0].statement.lower()

    def test_does_not_fire_when_balanced(self):
        rule = HighCouplingRule()
        ev = _evidence("E-COUP-001", "coupling", excerpt="fan_in=10, fan_out=10, coupling=20")
        claims = rule.evaluate([ev], _mock_fetcher(), 1)
        assert len(claims) == 0

    def test_does_not_fire_when_fan_out_low(self):
        rule = HighCouplingRule()
        ev = _evidence("E-COUP-001", "coupling", excerpt="fan_in=1, fan_out=4, coupling=5")
        claims = rule.evaluate([ev], _mock_fetcher(), 1)
        assert len(claims) == 0


class TestKnowledgeSiloRule:
    def test_fires_for_single_author_large_file(self):
        rule = KnowledgeSiloRule()
        ev = _evidence("E-OWN-001", "ownership", excerpt="authors=1, top_author=dev (100%), lines=800")
        claims = rule.evaluate([ev], _mock_fetcher(), 1)
        assert len(claims) == 1
        assert "bus factor" in claims[0].statement.lower()

    def test_does_not_fire_for_multiple_authors(self):
        rule = KnowledgeSiloRule()
        ev = _evidence("E-OWN-001", "ownership", excerpt="authors=3, top_author=dev (60%), lines=800")
        claims = rule.evaluate([ev], _mock_fetcher(), 1)
        assert len(claims) == 0

    def test_does_not_fire_for_small_file(self):
        rule = KnowledgeSiloRule()
        ev = _evidence("E-OWN-001", "ownership", excerpt="authors=1, top_author=dev (100%), lines=100")
        claims = rule.evaluate([ev], _mock_fetcher(), 1)
        assert len(claims) == 0


class TestCoverageGapRule:
    def test_fires_for_low_coverage_high_ccn(self):
        rule = CoverageGapRule()
        ev = _evidence("E-COV-001", "coverage", excerpt="coverage=20%, max_ccn=25, loc=500")
        claims = rule.evaluate([ev], _mock_fetcher(), 1)
        assert len(claims) == 1
        assert "high-risk" in claims[0].statement.lower()
        assert claims[0].confidence == "high"  # coverage < 30

    def test_medium_confidence_for_moderate_coverage(self):
        rule = CoverageGapRule()
        ev = _evidence("E-COV-001", "coverage", excerpt="coverage=40%, max_ccn=20, loc=300")
        claims = rule.evaluate([ev], _mock_fetcher(), 1)
        assert len(claims) == 1
        assert claims[0].confidence == "medium"


class TestSecurityExposureRule:
    def test_fires_for_critical_vulns(self):
        rule = SecurityExposureRule()
        ev = _evidence("E-SEC-001", "security", excerpt="CVE-2024-1234 (CRITICAL) in pkg 1.0")
        claims = rule.evaluate([ev], _mock_fetcher(), 1)
        assert len(claims) == 1
        assert "critical" in claims[0].statement.lower()

    def test_fires_for_secrets(self):
        rule = SecurityExposureRule()
        ev = EvidenceItem(
            evidence_id="E-SEC-001",
            evidence_type="secret_detection",
            category="security",
            location="config.py",
            excerpt="rule=api-key",
            observation="Secret detected",
            why_it_matters="Access risk",
            tool_source="gitleaks",
            run_pk=1,
        )
        claims = rule.evaluate([ev], _mock_fetcher(), 1)
        assert len(claims) >= 1

    def test_empty_when_no_security_evidence(self):
        rule = SecurityExposureRule()
        claims = rule.evaluate([], _mock_fetcher(), 1)
        assert len(claims) == 0


class TestClaimGenerator:
    def test_generates_from_mixed_evidence(self):
        gen = ClaimGenerator()
        evidence = [
            _evidence("E-COUP-001", "coupling", excerpt="fan_in=1, fan_out=20, coupling=21"),
            _evidence("E-SEC-001", "security", excerpt="CVE-X (CRITICAL) in pkg 1"),
        ]
        claims = gen.generate(evidence, _mock_fetcher(), 1)
        assert len(claims) >= 2

    def test_graceful_on_rule_failure(self):
        """Generator should continue even if one rule raises."""
        gen = ClaimGenerator()
        fetcher = MagicMock()
        fetcher.fetch.side_effect = Exception("boom")
        # Should not raise
        claims = gen.generate([], fetcher, 1)
        assert isinstance(claims, list)


class TestExcerptParsing:
    def test_parse_int(self):
        assert _parse_int_from_excerpt("authors=3, lines=500", "authors=") == 3
        assert _parse_int_from_excerpt("authors=3, lines=500", "lines=") == 500

    def test_parse_int_missing(self):
        assert _parse_int_from_excerpt("nothing here", "authors=") == 0

    def test_parse_float(self):
        assert _parse_float_from_excerpt("coverage=45.5%, max_ccn=10", "coverage=") == 45.5

    def test_parse_float_missing(self):
        assert _parse_float_from_excerpt("nothing", "coverage=") == 0.0
