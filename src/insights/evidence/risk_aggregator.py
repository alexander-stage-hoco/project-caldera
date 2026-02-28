"""Risk aggregator — groups claims into execution risks by theme.

Each ``RiskPattern`` defines a theme, the claim categories it matches,
the minimum number of claims required to trigger, and a default severity.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .entities import (
    EvidenceItem,
    EvidenceRegistry,
    ExecutionRisk,
    RiskSeverity,
    TechnicalClaim,
)


@dataclass(frozen=True)
class RiskPattern:
    """Defines how claims are grouped into an execution risk."""

    name: str
    description: str
    technical_cause: str
    categories: tuple[str, ...]
    min_claims: int
    default_severity: RiskSeverity


DEFAULT_PATTERNS: tuple[RiskPattern, ...] = (
    RiskPattern(
        name="Security exposure",
        description="Active security vulnerabilities or leaked secrets "
        "that may be exploited.",
        technical_cause="Unpatched dependencies or committed secrets.",
        categories=("security",),
        min_claims=1,
        default_severity="high",
    ),
    RiskPattern(
        name="Change amplification",
        description="High coupling amplifies the blast radius of changes, "
        "increasing defect introduction rate.",
        technical_cause="Excessive outbound coupling between modules.",
        categories=("coupling",),
        min_claims=2,
        default_severity="high",
    ),
    RiskPattern(
        name="Knowledge concentration",
        description="Critical code owned by a single contributor — "
        "bus factor and onboarding risk.",
        technical_cause="Single-author files with no knowledge transfer.",
        categories=("ownership",),
        min_claims=2,
        default_severity="high",
    ),
    RiskPattern(
        name="Untested complexity",
        description="Complex code lacks adequate test coverage, "
        "creating latent defect risk.",
        technical_cause="Low coverage in high-CCN files.",
        categories=("coverage", "complexity"),
        min_claims=2,
        default_severity="high",
    ),
    RiskPattern(
        name="Systemic debt",
        description="Pervasive code quality issues that compound over time, "
        "reducing velocity.",
        technical_cause="Code smells and quality issues affecting a large "
        "proportion of the codebase.",
        categories=("quality",),
        min_claims=3,
        default_severity="medium",
    ),
)


class RiskAggregator:
    """Groups claims by theme and creates ``ExecutionRisk`` entries."""

    def __init__(
        self,
        patterns: tuple[RiskPattern, ...] | None = None,
    ) -> None:
        self._patterns = patterns or DEFAULT_PATTERNS

    def aggregate(
        self,
        claims: list[TechnicalClaim],
        evidence: list[EvidenceItem] | None = None,
    ) -> list[ExecutionRisk]:
        """Match claims against risk patterns and emit risks."""
        risks: list[ExecutionRisk] = []
        evidence_by_id: dict[str, EvidenceItem] = {}
        if evidence:
            evidence_by_id = {e.evidence_id: e for e in evidence}

        for seq, pattern in enumerate(self._patterns, start=1):
            matching_claims = [
                c for c in claims if c.category in pattern.categories
            ]

            # Multi-category patterns require at least one claim from each category
            if len(pattern.categories) > 1:
                represented = {c.category for c in matching_claims}
                if not represented >= set(pattern.categories):
                    continue

            if len(matching_claims) < pattern.min_claims:
                continue

            # Collect locations from linked evidence
            manifests_in: list[str] = []
            seen_locations: set[str] = set()
            for claim in matching_claims:
                for eid in claim.evidence_ids:
                    ev = evidence_by_id.get(eid)
                    if ev and ev.location not in seen_locations:
                        manifests_in.append(ev.location)
                        seen_locations.add(ev.location)

            # Determine severity: escalate if any claim indicates critical-level findings
            severity = pattern.default_severity
            if any(c.severity == "critical" for c in matching_claims):
                severity = "critical"
            if len(matching_claims) >= pattern.min_claims * 3:
                severity = _escalate(severity)

            risks.append(
                ExecutionRisk(
                    risk_id=f"RISK-{seq:03d}",
                    description=pattern.description,
                    technical_cause=pattern.technical_cause,
                    claim_ids=tuple(
                        c.claim_id for c in matching_claims[:20]
                    ),
                    manifests_in=tuple(manifests_in[:20]),
                    triggered_by=pattern.name,
                    severity=severity,
                )
            )

        return risks


def _escalate(severity: RiskSeverity) -> RiskSeverity:
    """Bump severity one level up."""
    order: dict[RiskSeverity, RiskSeverity] = {
        "low": "medium",
        "medium": "high",
        "high": "critical",
        "critical": "critical",
    }
    return order[severity]
