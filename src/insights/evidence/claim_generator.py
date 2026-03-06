"""Claim generator — deterministic rule-based claim derivation from evidence.

Each ``ClaimRule`` subclass evaluates a specific pattern across evidence items,
optionally augmented by a supplementary SQL query, and emits
``TechnicalClaim`` instances.
"""

from __future__ import annotations

import warnings
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from ..data_fetcher import DataFetcher
from .entities import (
    ConfidenceLevel,
    EvidenceItem,
    TechnicalClaim,
)

if TYPE_CHECKING:
    from ..narrative.enricher import NarrativeEnricher


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

        # Map evidence by directory prefix for linking
        complexity_evidence = [
            e for e in evidence if e.category == "complexity"
        ]

        for i, row in enumerate(rows, start=1):
            dir_path = row.get("directory_path", "")
            gini = row.get("gini_ccn", 0)

            # Link evidence items whose location is within this directory
            if dir_path in (".", ""):
                linked = [e.evidence_id for e in complexity_evidence]
            else:
                linked = [
                    e.evidence_id
                    for e in complexity_evidence
                    if e.location.startswith(dir_path + "/") or e.location == dir_path
                ]

            if not linked:
                # Synthetic fallback: use first 3 complexity evidence items
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
    """Fires when fan_out > fan_in * N (high outbound coupling)."""

    category = "coupling"
    abbr = "COUP"

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        p = params or {}
        self._fan_out_multiplier = p.get("fan_out_multiplier", 3)
        self._min_fan_out = p.get("min_fan_out", 5)

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
            # Parse fan_in/fan_out from metadata or excerpt
            fan_in = ev.metadata.get("fan_in") if ev.metadata else None
            fan_out = ev.metadata.get("fan_out") if ev.metadata else None
            if fan_in is None or fan_out is None:
                fan_in, fan_out = _parse_fan(ev.excerpt)
            if fan_out > fan_in * self._fan_out_multiplier and fan_out > self._min_fan_out:
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
    """Fires when unique_authors <= max_authors AND total_lines > min_lines."""

    category = "ownership"
    abbr = "SILO"

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        p = params or {}
        self._max_authors = p.get("max_authors", 1)
        self._min_lines = p.get("min_lines", 500)

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
            authors = ev.metadata.get("unique_authors") if ev.metadata else None
            lines = ev.metadata.get("total_lines") if ev.metadata else None
            if authors is None:
                authors = _parse_int_from_excerpt(ev.excerpt, "authors=")
            if lines is None:
                lines = _parse_int_from_excerpt(ev.excerpt, "lines=")
            if authors <= self._max_authors and lines > self._min_lines:
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
    """Fires when coverage < max_coverage AND ccn > min_ccn."""

    category = "coverage"
    abbr = "COVG"

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        p = params or {}
        self._max_coverage = p.get("max_coverage", 50)
        self._min_ccn = p.get("min_ccn", 15)

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

        seq = 0
        for ev in coverage_evidence:
            coverage = ev.metadata.get("coverage_line_pct") if ev.metadata else None
            ccn = ev.metadata.get("complexity_max") if ev.metadata else None
            if coverage is None:
                coverage = _parse_float_from_excerpt(ev.excerpt, "coverage=")
            if ccn is None:
                ccn = _parse_int_from_excerpt(ev.excerpt, "complexity_max=")
            if coverage >= self._max_coverage or ccn <= self._min_ccn:
                continue
            seq += 1
            claims.append(
                TechnicalClaim(
                    claim_id=f"CLM-{self.abbr}-{seq:03d}",
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
                    severity="critical",
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
                    severity="high",
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
# LLM Synthesis Rule — cross-signal compound-risk detection
# ---------------------------------------------------------------------------


class LLMSynthesisRule(ClaimRule):
    """Finds files appearing in 3+ evidence categories, generates compound-risk claims via LLM."""

    category = "quality"
    abbr = "SYNT"

    def __init__(self, enricher: NarrativeEnricher) -> None:
        self._enricher = enricher

    def evaluate(
        self,
        evidence: list[EvidenceItem],
        fetcher: DataFetcher,
        run_pk: int,
    ) -> list[TechnicalClaim]:
        # Group evidence by location
        by_location: dict[str, list[EvidenceItem]] = defaultdict(list)
        for e in evidence:
            if e.location:
                by_location[e.location].append(e)

        # Find hotspots: locations with evidence in 3+ distinct categories
        hotspots: list[tuple[str, set[str], list[EvidenceItem]]] = []
        for loc, items in by_location.items():
            categories = {e.category for e in items}
            if len(categories) >= 3:
                hotspots.append((loc, categories, items))

        if not hotspots:
            return []

        # Sort by number of categories descending, take top 10
        hotspots.sort(key=lambda x: len(x[1]), reverse=True)
        hotspots = hotspots[:10]

        # Build data for LLM
        hotspot_data = [
            {
                "file": loc,
                "categories": sorted(cats),
                "excerpts": [e.excerpt[:500] for e in items[:3]],
            }
            for loc, cats, items in hotspots
        ]

        result = self._enricher.enrich(
            task=(
                "For each file listed below, write one sentence describing the "
                "compound risk from overlapping analysis signals. Each line should "
                "start with the file path followed by a colon. Be specific about "
                "the risk combination."
            ),
            data={"hotspot_files": hotspot_data},
            max_tokens=400,
        )

        if not result:
            return []

        # Parse response lines into claims
        claims: list[TechnicalClaim] = []
        seq = 0
        for line in result.strip().splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue

            # Find matching hotspot for this line
            matched_hotspot = None
            for loc, cats, items in hotspots:
                if loc in line:
                    matched_hotspot = (loc, cats, items)
                    break

            if not matched_hotspot:
                continue

            loc, cats, items = matched_hotspot
            seq += 1
            claims.append(
                TechnicalClaim(
                    claim_id=f"CLM-{self.abbr}-{seq:03d}",
                    category=self.category,
                    statement=line,
                    evidence_ids=tuple(e.evidence_id for e in items[:10]),
                    implication="Multiple independent analysis signals converge "
                    "on this location, indicating compound risk.",
                    confidence="high" if len(cats) >= 4 else "medium",
                    triggered_by="LLMSynthesisRule",
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

# Rules that accept a params dict in __init__
_PARAMETERIZED_RULES: frozenset[type[ClaimRule]] = frozenset({
    HighCouplingRule,
    KnowledgeSiloRule,
    CoverageGapRule,
})


class ClaimGenerator:
    """Evaluates all claim rules against collected evidence."""

    def __init__(
        self,
        rules: tuple[type[ClaimRule], ...] | None = None,
        enricher: NarrativeEnricher | None = None,
        claim_params: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        cp = claim_params or {}
        rule_classes = rules or DEFAULT_RULES
        self._rules: list[ClaimRule] = []
        for cls in rule_classes:
            if cls in _PARAMETERIZED_RULES:
                params = cp.get(cls.__name__, {})
                self._rules.append(cls(params=params))  # type: ignore[call-arg]
            else:
                self._rules.append(cls())
        if enricher is not None:
            self._rules.append(LLMSynthesisRule(enricher))

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
