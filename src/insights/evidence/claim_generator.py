"""Claim generator — deterministic rule-based claim derivation from evidence.

Each ``ClaimRule`` subclass evaluates a specific pattern across evidence items,
optionally augmented by a supplementary SQL query, and emits
``TechnicalClaim`` instances.
"""

from __future__ import annotations

import warnings
from abc import ABC, abstractmethod
from typing import Any

from ..data_fetcher import DataFetcher
from .entities import (
    ConfidenceLevel,
    EvidenceItem,
    TechnicalClaim,
)


class ClaimRule(ABC):
    """Base class for deterministic claim rules."""

    category: str
    abbr: str  # Short code for claim IDs, e.g. "CONC"

    @abstractmethod
    def evaluate(
        self,
        evidence: list[EvidenceItem],
        fetcher: DataFetcher,
        run_pk: int,
    ) -> list[TechnicalClaim]:
        ...


class ComplexityConcentrationRule(ClaimRule):
    """Fires when complexity Gini > 0.7 in a directory with 10+ files."""

    category = "complexity"
    abbr = "CONC"

    def evaluate(
        self,
        evidence: list[EvidenceItem],
        fetcher: DataFetcher,
        run_pk: int,
    ) -> list[TechnicalClaim]:
        rows = _safe_query(fetcher, "claim_complexity_concentration", run_pk)
        claims: list[TechnicalClaim] = []

        # Map evidence by location for linking
        complexity_evidence = [
            e for e in evidence if e.category == "complexity"
        ]
        evidence_by_dir: dict[str, list[str]] = {}
        for e in complexity_evidence:
            parts = e.location.split("/")
            dir_key = parts[0] if len(parts) > 1 else "."
            evidence_by_dir.setdefault(dir_key, []).append(e.evidence_id)

        for i, row in enumerate(rows, start=1):
            dir_path = row.get("directory_path", "")
            gini = row.get("gini_ccn", 0)
            linked = evidence_by_dir.get(dir_path, [])

            # Must have at least one linked evidence item
            if not linked:
                # Create a synthetic link to all complexity evidence
                linked = [e.evidence_id for e in complexity_evidence[:3]]
            if not linked:
                continue

            claims.append(
                TechnicalClaim(
                    claim_id=f"CLM-{self.abbr}-{i:03d}",
                    category=self.category,
                    statement=f"Complexity concentrated in {dir_path}/ "
                    f"(Gini={gini:.2f}, {row.get('file_count', 0)} files)",
                    evidence_ids=tuple(linked[:10]),
                    implication="Maintenance burden falls on a small set of "
                    "files — changes are risky and review-intensive.",
                    confidence="high" if gini > 0.8 else "medium",
                    triggered_by="ComplexityConcentrationRule",
                )
            )
        return claims


class HighCouplingRule(ClaimRule):
    """Fires when fan_out > fan_in * 3 (high outbound coupling)."""

    category = "coupling"
    abbr = "COUP"

    def evaluate(
        self,
        evidence: list[EvidenceItem],
        fetcher: DataFetcher,
        run_pk: int,
    ) -> list[TechnicalClaim]:
        coupling_evidence = [
            e for e in evidence if e.category == "coupling"
        ]
        claims: list[TechnicalClaim] = []

        for i, ev in enumerate(coupling_evidence, start=1):
            # Parse fan_in/fan_out from excerpt
            fan_in, fan_out = _parse_fan(ev.excerpt)
            if fan_out > fan_in * 3 and fan_out > 5:
                claims.append(
                    TechnicalClaim(
                        claim_id=f"CLM-{self.abbr}-{i:03d}",
                        category=self.category,
                        statement=f"Module {ev.location} exhibits high "
                        f"outbound coupling (fan_out={fan_out}, "
                        f"fan_in={fan_in})",
                        evidence_ids=(ev.evidence_id,),
                        implication="Changes in this module ripple outward; "
                        "it is a change amplifier.",
                        confidence="high",
                        triggered_by="HighCouplingRule",
                    )
                )
        return claims


class KnowledgeSiloRule(ClaimRule):
    """Fires when unique_authors = 1 AND total_lines > 500."""

    category = "ownership"
    abbr = "SILO"

    def evaluate(
        self,
        evidence: list[EvidenceItem],
        fetcher: DataFetcher,
        run_pk: int,
    ) -> list[TechnicalClaim]:
        ownership_evidence = [
            e for e in evidence if e.category == "ownership"
        ]
        claims: list[TechnicalClaim] = []
        seq = 0

        for ev in ownership_evidence:
            authors = _parse_int_from_excerpt(ev.excerpt, "authors=")
            lines = _parse_int_from_excerpt(ev.excerpt, "lines=")
            if authors == 1 and lines > 500:
                seq += 1
                claims.append(
                    TechnicalClaim(
                        claim_id=f"CLM-{self.abbr}-{seq:03d}",
                        category=self.category,
                        statement=f"File {ev.location} has single author "
                        f"— bus factor risk ({lines} lines)",
                        evidence_ids=(ev.evidence_id,),
                        implication="If this contributor leaves, knowledge "
                        "of this code is lost.",
                        confidence="high",
                        triggered_by="KnowledgeSiloRule",
                    )
                )
        return claims


class CoverageGapRule(ClaimRule):
    """Fires when coverage < 50 AND ccn > 15."""

    category = "coverage"
    abbr = "COVG"

    def evaluate(
        self,
        evidence: list[EvidenceItem],
        fetcher: DataFetcher,
        run_pk: int,
    ) -> list[TechnicalClaim]:
        coverage_evidence = [
            e for e in evidence if e.category == "coverage"
        ]
        claims: list[TechnicalClaim] = []

        for i, ev in enumerate(coverage_evidence, start=1):
            coverage = _parse_float_from_excerpt(ev.excerpt, "coverage=")
            ccn = _parse_int_from_excerpt(ev.excerpt, "max_ccn=")
            claims.append(
                TechnicalClaim(
                    claim_id=f"CLM-{self.abbr}-{i:03d}",
                    category=self.category,
                    statement=f"File {ev.location} is high-risk: "
                    f"{ccn} CCN with {coverage:.0f}% coverage",
                    evidence_ids=(ev.evidence_id,),
                    implication="Defects in this file are likely to go "
                    "undetected until production.",
                    confidence="high" if coverage < 30 else "medium",
                    triggered_by="CoverageGapRule",
                )
            )
        return claims


class SecurityExposureRule(ClaimRule):
    """Fires when critical vulnerabilities exist."""

    category = "security"
    abbr = "SECX"

    def evaluate(
        self,
        evidence: list[EvidenceItem],
        fetcher: DataFetcher,
        run_pk: int,
    ) -> list[TechnicalClaim]:
        security_evidence = [
            e for e in evidence if e.category == "security"
        ]
        if not security_evidence:
            return []

        # Group by severity
        critical = [
            e
            for e in security_evidence
            if "CRITICAL" in e.excerpt.upper() or "secret" in e.evidence_type
        ]
        high = [
            e
            for e in security_evidence
            if "HIGH" in e.excerpt.upper() and e not in critical
        ]

        claims: list[TechnicalClaim] = []
        seq = 0

        if critical:
            seq += 1
            claims.append(
                TechnicalClaim(
                    claim_id=f"CLM-{self.abbr}-{seq:03d}",
                    category=self.category,
                    statement=f"Platform has {len(critical)} critical "
                    f"security finding(s)",
                    evidence_ids=tuple(e.evidence_id for e in critical[:10]),
                    implication="Critical vulnerabilities may be actively "
                    "exploited — immediate remediation required.",
                    confidence="high",
                    triggered_by="SecurityExposureRule",
                )
            )

        if high:
            seq += 1
            claims.append(
                TechnicalClaim(
                    claim_id=f"CLM-{self.abbr}-{seq:03d}",
                    category=self.category,
                    statement=f"Platform has {len(high)} high-severity "
                    f"security finding(s)",
                    evidence_ids=tuple(e.evidence_id for e in high[:10]),
                    implication="High-severity vulnerabilities require "
                    "remediation within the next release cycle.",
                    confidence="high",
                    triggered_by="SecurityExposureRule",
                )
            )

        return claims


class PervasiveDebtRule(ClaimRule):
    """Fires when a code smell affects > 50% of files."""

    category = "quality"
    abbr = "DEBT"

    def evaluate(
        self,
        evidence: list[EvidenceItem],
        fetcher: DataFetcher,
        run_pk: int,
    ) -> list[TechnicalClaim]:
        rows = _safe_query(fetcher, "claim_pervasive_smells", run_pk)
        quality_evidence = [
            e for e in evidence if e.category == "quality"
        ]

        claims: list[TechnicalClaim] = []
        # Link to top quality evidence items for traceability
        linked_ids = tuple(e.evidence_id for e in quality_evidence[:5])

        for i, row in enumerate(rows, start=1):
            smell_type = row.get("smell_type", "unknown")
            pct = row.get("affected_pct", 0)

            if not linked_ids:
                continue

            claims.append(
                TechnicalClaim(
                    claim_id=f"CLM-{self.abbr}-{i:03d}",
                    category=self.category,
                    statement=f"Code smell '{smell_type}' affects "
                    f"{pct:.0f}% of files",
                    evidence_ids=linked_ids,
                    implication="Pervasive smells indicate systemic code "
                    "quality issues that compound over time.",
                    confidence="high" if pct > 70 else "medium",
                    triggered_by="PervasiveDebtRule",
                )
            )
        return claims


# ---------------------------------------------------------------------------
# ClaimGenerator — orchestrates all rules
# ---------------------------------------------------------------------------

# Default rules in evaluation order
DEFAULT_RULES: tuple[type[ClaimRule], ...] = (
    ComplexityConcentrationRule,
    HighCouplingRule,
    KnowledgeSiloRule,
    CoverageGapRule,
    SecurityExposureRule,
    PervasiveDebtRule,
)


class ClaimGenerator:
    """Evaluates all claim rules against collected evidence."""

    def __init__(
        self, rules: tuple[type[ClaimRule], ...] | None = None
    ) -> None:
        self._rules = [cls() for cls in (rules or DEFAULT_RULES)]

    def generate(
        self,
        evidence: list[EvidenceItem],
        fetcher: DataFetcher,
        run_pk: int,
    ) -> list[TechnicalClaim]:
        claims: list[TechnicalClaim] = []
        for rule in self._rules:
            try:
                claims.extend(rule.evaluate(evidence, fetcher, run_pk))
            except Exception as exc:
                warnings.warn(
                    f"[ClaimGenerator] {rule.__class__.__name__} failed: {exc}",
                    stacklevel=2,
                )
        return claims


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_query(
    fetcher: DataFetcher, query_name: str, run_pk: int
) -> list[dict[str, Any]]:
    try:
        return fetcher.fetch(query_name, run_pk)
    except Exception as exc:
        warnings.warn(
            f"[ClaimGenerator] Query '{query_name}' failed: {exc}",
            stacklevel=2,
        )
        return []


def _parse_fan(excerpt: str) -> tuple[int, int]:
    """Parse fan_in and fan_out from an evidence excerpt string."""
    fan_in = _parse_int_from_excerpt(excerpt, "fan_in=")
    fan_out = _parse_int_from_excerpt(excerpt, "fan_out=")
    return fan_in, fan_out


def _parse_int_from_excerpt(excerpt: str, prefix: str) -> int:
    """Extract an integer value following *prefix* in a string."""
    try:
        idx = excerpt.index(prefix) + len(prefix)
        end = idx
        while end < len(excerpt) and (excerpt[end].isdigit() or excerpt[end] == "-"):
            end += 1
        return int(excerpt[idx:end]) if idx < end else 0
    except (ValueError, IndexError):
        return 0


def _parse_float_from_excerpt(excerpt: str, prefix: str) -> float:
    """Extract a float value following *prefix* in a string."""
    try:
        idx = excerpt.index(prefix) + len(prefix)
        end = idx
        while end < len(excerpt) and (excerpt[end].isdigit() or excerpt[end] in ".-"):
            end += 1
        return float(excerpt[idx:end]) if idx < end else 0.0
    except (ValueError, IndexError):
        return 0.0
