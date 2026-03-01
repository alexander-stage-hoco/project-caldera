"""Core entities for the Evidence & Claim framework.

All entities are frozen dataclasses with ``__post_init__`` validation,
following the project convention for immutable value objects.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal


# ---------------------------------------------------------------------------
# Text field size caps (P1 — upstream data limits)
# ---------------------------------------------------------------------------

MAX_EXCERPT_CHARS = 500
MAX_OBSERVATION_CHARS = 500
MAX_WHY_IT_MATTERS_CHARS = 500


def _cap(value: str, max_len: int) -> str:
    """Truncate *value* to *max_len* chars, appending ``…`` when trimmed."""
    if len(value) <= max_len:
        return value
    return value[: max_len - 1] + "\u2026"


# ---------------------------------------------------------------------------
# ID format constants
# ---------------------------------------------------------------------------

_EVIDENCE_ID_RE = re.compile(r"^E-[A-Z]+-\d{3,}$")
_CLAIM_ID_RE = re.compile(r"^CLM-[A-Z]+-\d{3,}$")
_RISK_ID_RE = re.compile(r"^RISK-\d{3,}$")

EvidenceCategory = Literal[
    "complexity",
    "security",
    "coupling",
    "coverage",
    "ownership",
    "quality",
]

EVIDENCE_CATEGORIES: tuple[EvidenceCategory, ...] = (
    "complexity",
    "security",
    "coupling",
    "coverage",
    "ownership",
    "quality",
)

ClaimCategory = Literal[
    "complexity",
    "coupling",
    "ownership",
    "coverage",
    "security",
    "quality",
]

RiskSeverity = Literal["critical", "high", "medium", "low"]

ConfidenceLevel = Literal["high", "medium", "low"]


# ---------------------------------------------------------------------------
# EvidenceItem
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvidenceItem:
    """A single piece of auditable evidence extracted from tool data.

    ``evidence_id`` follows the pattern ``E-{CATEGORY_ABBR}-{SEQ}``,
    e.g. ``E-CCN-001``, ``E-SEC-002``.
    """

    evidence_id: str
    evidence_type: str
    category: EvidenceCategory
    location: str
    excerpt: str
    observation: str
    why_it_matters: str
    tool_source: str
    run_pk: int
    confidence: ConfidenceLevel = "high"

    def __post_init__(self) -> None:
        if not _EVIDENCE_ID_RE.match(self.evidence_id):
            raise ValueError(
                f"evidence_id must match E-XXX-NNN, got: {self.evidence_id!r}"
            )
        if self.category not in EVIDENCE_CATEGORIES:
            raise ValueError(f"Invalid evidence category: {self.category!r}")
        if not self.location:
            raise ValueError("location must not be empty")
        if not self.tool_source:
            raise ValueError("tool_source must not be empty")

        # Upstream text field size caps (frozen → object.__setattr__)
        object.__setattr__(self, "excerpt", _cap(self.excerpt, MAX_EXCERPT_CHARS))
        object.__setattr__(self, "observation", _cap(self.observation, MAX_OBSERVATION_CHARS))
        object.__setattr__(self, "why_it_matters", _cap(self.why_it_matters, MAX_WHY_IT_MATTERS_CHARS))


# ---------------------------------------------------------------------------
# TechnicalClaim
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TechnicalClaim:
    """A deterministic claim derived from evidence via pattern rules.

    ``claim_id`` follows ``CLM-{CATEGORY_ABBR}-{SEQ}``,
    e.g. ``CLM-COUP-001``.
    """

    claim_id: str
    category: ClaimCategory
    statement: str
    evidence_ids: tuple[str, ...]
    implication: str
    confidence: ConfidenceLevel
    triggered_by: str
    severity: RiskSeverity | None = None

    def __post_init__(self) -> None:
        if not _CLAIM_ID_RE.match(self.claim_id):
            raise ValueError(
                f"claim_id must match CLM-XXX-NNN, got: {self.claim_id!r}"
            )
        if not self.evidence_ids:
            raise ValueError("A claim must reference at least one evidence_id")
        if not self.statement:
            raise ValueError("statement must not be empty")
        if not self.triggered_by:
            raise ValueError("triggered_by must not be empty")
        if self.severity is not None and self.severity not in (
            "critical", "high", "medium", "low",
        ):
            raise ValueError(f"Invalid claim severity: {self.severity!r}")


# ---------------------------------------------------------------------------
# ExecutionRisk
# ---------------------------------------------------------------------------


RiskStatus = Literal["open", "mitigating", "accepted", "resolved"]


@dataclass(frozen=True)
class ExecutionRisk:
    """An aggregated execution risk derived from one or more claims.

    ``risk_id`` follows ``RISK-{SEQ}``, e.g. ``RISK-001``.
    """

    risk_id: str
    description: str
    technical_cause: str
    claim_ids: tuple[str, ...]
    manifests_in: tuple[str, ...]
    triggered_by: str
    severity: RiskSeverity
    owner: str | None = None
    action: str | None = None
    sla_date: str | None = None
    status: RiskStatus = "open"

    def __post_init__(self) -> None:
        if not _RISK_ID_RE.match(self.risk_id):
            raise ValueError(
                f"risk_id must match RISK-NNN, got: {self.risk_id!r}"
            )
        if not self.claim_ids:
            raise ValueError("A risk must reference at least one claim_id")
        if not self.description:
            raise ValueError("description must not be empty")
        if self.status not in ("open", "mitigating", "accepted", "resolved"):
            raise ValueError(f"Invalid risk status: {self.status!r}")


# ---------------------------------------------------------------------------
# EvidenceRegistry — mutable container with lookup helpers
# ---------------------------------------------------------------------------


class EvidenceRegistry:
    """Mutable container holding all evidence, claims, and risks for a run.

    Provides O(1) lookups by ID and category-based filtering.
    """

    def __init__(
        self,
        evidence: list[EvidenceItem] | None = None,
        claims: list[TechnicalClaim] | None = None,
        risks: list[ExecutionRisk] | None = None,
        warning_count: int = 0,
        warning_details: dict[str, Any] | None = None,
    ) -> None:
        self._evidence: list[EvidenceItem] = list(evidence or [])
        self._claims: list[TechnicalClaim] = list(claims or [])
        self._risks: list[ExecutionRisk] = list(risks or [])
        self.warning_count: int = warning_count
        self.warning_details: dict[str, Any] = warning_details or {}

        # Build lookup indices
        self._evidence_by_id: dict[str, EvidenceItem] = {
            e.evidence_id: e for e in self._evidence
        }
        self._claims_by_id: dict[str, TechnicalClaim] = {
            c.claim_id: c for c in self._claims
        }
        self._risks_by_id: dict[str, ExecutionRisk] = {
            r.risk_id: r for r in self._risks
        }

    # -- Read helpers -------------------------------------------------------

    @property
    def evidence(self) -> list[EvidenceItem]:
        return list(self._evidence)

    @property
    def claims(self) -> list[TechnicalClaim]:
        return list(self._claims)

    @property
    def risks(self) -> list[ExecutionRisk]:
        return list(self._risks)

    def evidence_by_id(self, evidence_id: str) -> EvidenceItem | None:
        return self._evidence_by_id.get(evidence_id)

    def claim_by_id(self, claim_id: str) -> TechnicalClaim | None:
        return self._claims_by_id.get(claim_id)

    def risk_by_id(self, risk_id: str) -> ExecutionRisk | None:
        return self._risks_by_id.get(risk_id)

    def evidence_by_category(
        self, category: EvidenceCategory
    ) -> list[EvidenceItem]:
        return [e for e in self._evidence if e.category == category]

    def claims_by_category(
        self, category: ClaimCategory
    ) -> list[TechnicalClaim]:
        return [c for c in self._claims if c.category == category]

    def evidence_for_claim(self, claim: TechnicalClaim) -> list[EvidenceItem]:
        return [
            self._evidence_by_id[eid]
            for eid in claim.evidence_ids
            if eid in self._evidence_by_id
        ]

    def claims_for_risk(self, risk: ExecutionRisk) -> list[TechnicalClaim]:
        return [
            self._claims_by_id[cid]
            for cid in risk.claim_ids
            if cid in self._claims_by_id
        ]

    def risks_by_severity(
        self, severity: RiskSeverity
    ) -> list[ExecutionRisk]:
        return [r for r in self._risks if r.severity == severity]

    # -- Write helpers ------------------------------------------------------

    def add_evidence(self, item: EvidenceItem) -> None:
        self._evidence.append(item)
        self._evidence_by_id[item.evidence_id] = item

    def add_claim(self, claim: TechnicalClaim) -> None:
        self._claims.append(claim)
        self._claims_by_id[claim.claim_id] = claim

    def add_risk(self, risk: ExecutionRisk) -> None:
        self._risks.append(risk)
        self._risks_by_id[risk.risk_id] = risk

    # -- Summary ------------------------------------------------------------

    def summary(self) -> dict[str, Any]:
        """Return a summary dict suitable for template rendering."""
        return {
            "total_evidence": len(self._evidence),
            "total_claims": len(self._claims),
            "total_risks": len(self._risks),
            "evidence_by_category": {
                cat: len(self.evidence_by_category(cat))
                for cat in EVIDENCE_CATEGORIES
            },
            "claims_by_category": {
                cat: len(self.claims_by_category(cat))
                for cat in EVIDENCE_CATEGORIES
            },
            "risks_by_severity": {
                sev: len(self.risks_by_severity(sev))
                for sev in ("critical", "high", "medium", "low")
            },
        }

    def __repr__(self) -> str:
        return (
            f"EvidenceRegistry("
            f"evidence={len(self._evidence)}, "
            f"claims={len(self._claims)}, "
            f"risks={len(self._risks)})"
        )
