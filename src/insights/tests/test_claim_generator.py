"""Tests for ClaimGenerator and individual claim rules."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from insights.evidence.claim_generator import (
    ClaimGenerator,
    ComplexityConcentrationRule,
    CoverageGapRule,
    HighCouplingRule,
    KnowledgeSiloRule,
    PervasiveDebtRule,
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
        ev = _evidence("E-COV-001", "coverage", excerpt="coverage=20%, complexity_max=25, loc=500")
        claims = rule.evaluate([ev], _mock_fetcher(), 1)
        assert len(claims) == 1
        assert "high-risk" in claims[0].statement.lower()
        assert claims[0].confidence == "high"  # coverage < 30

    def test_medium_confidence_for_moderate_coverage(self):
        rule = CoverageGapRule()
        ev = _evidence("E-COV-001", "coverage", excerpt="coverage=40%, complexity_max=20, loc=300")
        claims = rule.evaluate([ev], _mock_fetcher(), 1)
        assert len(claims) == 1
        assert claims[0].confidence == "medium"

    def test_does_not_fire_for_high_coverage(self):
        rule = CoverageGapRule()
        ev = _evidence("E-COV-001", "coverage", excerpt="coverage=80%, complexity_max=5, loc=200")
        claims = rule.evaluate([ev], _mock_fetcher(), 1)
        assert len(claims) == 0

    def test_does_not_fire_for_low_ccn(self):
        rule = CoverageGapRule()
        ev = _evidence("E-COV-001", "coverage", excerpt="coverage=30%, complexity_max=10, loc=300")
        claims = rule.evaluate([ev], _mock_fetcher(), 1)
        assert len(claims) == 0


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


class TestComplexityConcentrationRule:
    def test_fires_when_gini_above_threshold(self):
        """Gini > 0.7 with matching complexity evidence → claim generated."""
        rule = ComplexityConcentrationRule()
        ev = _evidence("E-CCN-001", "complexity", location="src/heavy.py", excerpt="complexity_max=25")
        fetcher = _mock_fetcher({
            "claim_complexity_concentration": [
                {"directory_path": "src", "gini_ccn": 0.85, "file_count": 15},
            ],
        })
        claims = rule.evaluate([ev], fetcher, 1)
        assert len(claims) == 1
        assert "src/" in claims[0].statement
        assert "Gini=0.85" in claims[0].statement
        assert claims[0].evidence_ids == ("E-CCN-001",)

    def test_does_not_fire_on_empty_query(self):
        """Fetcher returns empty → no claims."""
        rule = ComplexityConcentrationRule()
        ev = _evidence("E-CCN-001", "complexity")
        claims = rule.evaluate([ev], _mock_fetcher(), 1)
        assert len(claims) == 0

    def test_synthetic_linking_fallback(self):
        """When no evidence matches directory, falls back to first 3 complexity items."""
        rule = ComplexityConcentrationRule()
        # Evidence at different directory than query result
        ev1 = _evidence("E-CCN-001", "complexity", location="other/a.py")
        ev2 = _evidence("E-CCN-002", "complexity", location="other/b.py")
        ev3 = _evidence("E-CCN-003", "complexity", location="other/c.py")
        ev4 = _evidence("E-CCN-004", "complexity", location="other/d.py")
        fetcher = _mock_fetcher({
            "claim_complexity_concentration": [
                {"directory_path": "src", "gini_ccn": 0.75, "file_count": 20},
            ],
        })
        claims = rule.evaluate([ev1, ev2, ev3, ev4], fetcher, 1)
        assert len(claims) == 1
        # Synthetic fallback takes first 3
        assert len(claims[0].evidence_ids) == 3
        assert claims[0].evidence_ids == ("E-CCN-001", "E-CCN-002", "E-CCN-003")

    def test_high_confidence_above_0_8(self):
        """Gini > 0.8 → high confidence."""
        rule = ComplexityConcentrationRule()
        ev = _evidence("E-CCN-001", "complexity", location="src/file.py")
        fetcher = _mock_fetcher({
            "claim_complexity_concentration": [
                {"directory_path": "src", "gini_ccn": 0.9, "file_count": 12},
            ],
        })
        claims = rule.evaluate([ev], fetcher, 1)
        assert claims[0].confidence == "high"

    def test_medium_confidence_at_0_8(self):
        """Gini == 0.8 → medium confidence (not > 0.8)."""
        rule = ComplexityConcentrationRule()
        ev = _evidence("E-CCN-001", "complexity", location="src/file.py")
        fetcher = _mock_fetcher({
            "claim_complexity_concentration": [
                {"directory_path": "src", "gini_ccn": 0.8, "file_count": 12},
            ],
        })
        claims = rule.evaluate([ev], fetcher, 1)
        assert claims[0].confidence == "medium"

    def test_skips_when_no_complexity_evidence(self):
        """If query returns rows but no complexity evidence exists, no claims."""
        rule = ComplexityConcentrationRule()
        fetcher = _mock_fetcher({
            "claim_complexity_concentration": [
                {"directory_path": "src", "gini_ccn": 0.9, "file_count": 12},
            ],
        })
        claims = rule.evaluate([], fetcher, 1)
        assert len(claims) == 0


class TestPervasiveDebtRule:
    def test_fires_for_pervasive_smells(self):
        """Query returns rows with quality evidence → claim generated."""
        rule = PervasiveDebtRule()
        ev = _evidence("E-QUAL-001", "quality", location="src/messy.py")
        fetcher = _mock_fetcher({
            "claim_pervasive_smells": [
                {"smell_type": "long_method", "affected_pct": 65},
            ],
        })
        claims = rule.evaluate([ev], fetcher, 1)
        assert len(claims) == 1
        assert "long_method" in claims[0].statement
        assert "65%" in claims[0].statement
        assert claims[0].evidence_ids == ("E-QUAL-001",)

    def test_does_not_fire_without_quality_evidence(self):
        """Even if query returns rows, no quality evidence → no claims."""
        rule = PervasiveDebtRule()
        # Only complexity evidence, no quality
        ev = _evidence("E-CCN-001", "complexity")
        fetcher = _mock_fetcher({
            "claim_pervasive_smells": [
                {"smell_type": "long_method", "affected_pct": 80},
            ],
        })
        claims = rule.evaluate([ev], fetcher, 1)
        assert len(claims) == 0

    def test_high_confidence_above_70(self):
        """affected_pct > 70 → high confidence."""
        rule = PervasiveDebtRule()
        ev = _evidence("E-QUAL-001", "quality")
        fetcher = _mock_fetcher({
            "claim_pervasive_smells": [
                {"smell_type": "god_class", "affected_pct": 75},
            ],
        })
        claims = rule.evaluate([ev], fetcher, 1)
        assert claims[0].confidence == "high"

    def test_medium_confidence_at_70(self):
        """affected_pct == 70 → medium confidence (not > 70)."""
        rule = PervasiveDebtRule()
        ev = _evidence("E-QUAL-001", "quality")
        fetcher = _mock_fetcher({
            "claim_pervasive_smells": [
                {"smell_type": "long_method", "affected_pct": 70},
            ],
        })
        claims = rule.evaluate([ev], fetcher, 1)
        assert claims[0].confidence == "medium"

    def test_empty_query_no_claims(self):
        """Fetcher returns empty → no claims."""
        rule = PervasiveDebtRule()
        ev = _evidence("E-QUAL-001", "quality")
        claims = rule.evaluate([ev], _mock_fetcher(), 1)
        assert len(claims) == 0

    def test_multiple_smells_produce_multiple_claims(self):
        """Multiple rows → multiple claims with sequential IDs."""
        rule = PervasiveDebtRule()
        ev = _evidence("E-QUAL-001", "quality")
        fetcher = _mock_fetcher({
            "claim_pervasive_smells": [
                {"smell_type": "long_method", "affected_pct": 60},
                {"smell_type": "god_class", "affected_pct": 55},
            ],
        })
        claims = rule.evaluate([ev], fetcher, 1)
        assert len(claims) == 2
        assert claims[0].claim_id == "CLM-DEBT-001"
        assert claims[1].claim_id == "CLM-DEBT-002"


class TestHighCouplingRuleBoundary:
    def test_does_not_fire_when_fan_out_equals_fan_in_times_three(self):
        """fan_out == fan_in * 3 exactly should NOT fire (condition is >)."""
        rule = HighCouplingRule()
        # fan_out=9 == fan_in=3 * 3, and fan_out > 5, but NOT fan_out > fan_in * 3
        ev = _evidence("E-COUP-001", "coupling", excerpt="fan_in=3, fan_out=9, coupling=12")
        claims = rule.evaluate([ev], _mock_fetcher(), 1)
        assert len(claims) == 0

    def test_does_not_fire_when_ratio_exceeds_but_fan_out_not_above_five(self):
        """fan_out=5, fan_in=1 — ratio > 3x but fan_out is not > 5 → should NOT fire."""
        rule = HighCouplingRule()
        ev = _evidence("E-COUP-001", "coupling", excerpt="fan_in=1, fan_out=5, coupling=6")
        claims = rule.evaluate([ev], _mock_fetcher(), 1)
        assert len(claims) == 0


class TestSecurityExposureRuleBoth:
    def test_fires_two_claims_for_critical_and_high(self):
        """Both critical AND high evidence present → 2 claims with sequential IDs."""
        rule = SecurityExposureRule()
        ev_critical = _evidence(
            "E-SEC-001", "security",
            excerpt="CVE-2024-9999 (CRITICAL) in pkg 2.0",
        )
        ev_high = _evidence(
            "E-SEC-002", "security",
            excerpt="CVE-2024-8888 (HIGH) in pkg 3.0",
        )
        claims = rule.evaluate([ev_critical, ev_high], _mock_fetcher(), 1)
        assert len(claims) == 2
        assert claims[0].claim_id == "CLM-SECX-001"
        assert claims[1].claim_id == "CLM-SECX-002"
        assert "critical" in claims[0].statement.lower()
        assert "high" in claims[1].statement.lower()


class TestClaimGeneratorGracefulFailureWithEvidence:
    def test_graceful_on_rule_failure_with_real_evidence(self):
        """Generator continues when a rule raises, even with non-empty evidence.

        Unlike the existing test which passes empty evidence (so rules like
        HighCouplingRule never call fetcher.fetch), this test passes coupling
        evidence that triggers the parsing path, and makes the
        ComplexityConcentrationRule fail via a broken fetcher while
        HighCouplingRule still succeeds locally (it doesn't call fetcher).
        """
        gen = ClaimGenerator()
        fetcher = MagicMock()
        # fetch raises — will break ComplexityConcentrationRule and PervasiveDebtRule
        fetcher.fetch.side_effect = Exception("boom")
        evidence = [
            _evidence("E-COUP-001", "coupling", excerpt="fan_in=1, fan_out=20, coupling=21"),
        ]
        import warnings
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            claims = gen.generate(evidence, fetcher, 1)
        # HighCouplingRule should still succeed (it doesn't call fetcher.fetch)
        assert any("high outbound coupling" in c.statement.lower() for c in claims)
        # At least one warning should be emitted for the broken rules
        warning_messages = [str(w.message) for w in caught]
        assert any("failed" in m.lower() for m in warning_messages)


class TestExcerptParsing:
    def test_parse_int(self):
        assert _parse_int_from_excerpt("authors=3, lines=500", "authors=") == 3
        assert _parse_int_from_excerpt("authors=3, lines=500", "lines=") == 500

    def test_parse_int_missing(self):
        assert _parse_int_from_excerpt("nothing here", "authors=") == 0

    def test_parse_float(self):
        assert _parse_float_from_excerpt("coverage=45.5%, complexity_max=10", "coverage=") == 45.5

    def test_parse_float_missing(self):
        assert _parse_float_from_excerpt("nothing", "coverage=") == 0.0
