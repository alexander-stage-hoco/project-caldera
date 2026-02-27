"""Rewrite risk memo — identifies where incremental evolution breaks down."""

from __future__ import annotations

from typing import Any

from ..data_fetcher import DataFetcher
from .base import EvidenceAwareSection, SectionConfig


# ---------------------------------------------------------------------------
# Assumption text per signal type
# ---------------------------------------------------------------------------

_ASSUMPTIONS: dict[str, str] = {
    "monolith": "We can incrementally extract services from this module",
    "bidirectional_coupling": "We can evolve the data model incrementally",
    "unidirectional_coupling": "We can refactor dependencies without cascading changes",
    "knowledge_silo": "The team can maintain velocity if a key contributor leaves",
    "untested_core": "We can safely modify this module without regressions",
}

_EXPLANATIONS: dict[str, str] = {
    "monolith": (
        "High LOC concentration (Gini > 0.7) with elevated complexity and top-10% "
        "files doing >60% of the work leaves no natural seams for decomposition."
    ),
    "bidirectional_coupling": (
        "Bidirectional coupling makes it impossible to change one side without "
        "affecting the other, creating a change-amplification loop."
    ),
    "unidirectional_coupling": (
        "High fan-out relative to fan-in means this module depends on many others; "
        "refactoring is feasible but requires careful dependency inversion."
    ),
    "knowledge_silo": (
        "Single-author files account for the majority of complexity in this module. "
        "Knowledge transfer has not occurred on the critical path."
    ),
    "untested_core": (
        "High complexity with near-zero test coverage means any change risks "
        "silent regressions. For large modules the cost approaches a rewrite."
    ),
}

_TRIGGERS: dict[str, str] = {
    "monolith": "Attempt to split this module into independently deployable units",
    "bidirectional_coupling": "Change to shared data model or interface contract",
    "unidirectional_coupling": "Refactor of any upstream dependency",
    "knowledge_silo": "Key contributor becomes unavailable or changes teams",
    "untested_core": "Feature change or bug fix touching this module",
}


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------


def _classify_constraint(signals: list[str], loc_total: int) -> tuple[str, str]:
    """Return (constraint_type, risk_level) for a set of signals on one directory.

    Rules:
    - Monolith + coupling + knowledge silo → structural / high
    - Monolith + coupling → structural / high
    - Monolith alone → structural / medium
    - Bidirectional coupling without monolith → structural / medium
    - Unidirectional coupling without monolith → addressable / medium
    - Knowledge silo alone → addressable / low
    - Untested core → addressable / medium  (high if >3000 LOC)
    """
    has_monolith = "monolith" in signals
    has_bidir = "bidirectional_coupling" in signals
    has_unidir = "unidirectional_coupling" in signals
    has_silo = "knowledge_silo" in signals
    has_untested = "untested_core" in signals

    if has_monolith and (has_bidir or has_unidir) and has_silo:
        return ("structural", "high")
    if has_monolith and (has_bidir or has_unidir):
        return ("structural", "high")
    if has_monolith:
        return ("structural", "medium")
    if has_bidir:
        return ("structural", "medium")
    if has_unidir:
        return ("addressable", "medium")
    if has_untested:
        if loc_total > 3000:
            return ("addressable", "high")
        return ("addressable", "medium")
    if has_silo:
        return ("addressable", "low")

    # Fallback (shouldn't be reached with valid input)
    return ("addressable", "low")


def _generate_assumption(signal: str) -> str:
    """Return the assumption that fails for a given signal type."""
    return _ASSUMPTIONS.get(signal, "Incremental modernisation is feasible")


def _generate_explanation(signal: str) -> str:
    """Return the explanation of why the assumption fails."""
    return _EXPLANATIONS.get(signal, "Multiple risk signals converge on this module.")


def _generate_trigger(signal: str) -> str:
    """Return the trigger condition for the constraint."""
    return _TRIGGERS.get(signal, "Significant modification to this module")


# ---------------------------------------------------------------------------
# Section
# ---------------------------------------------------------------------------


class RewriteRiskSection(EvidenceAwareSection):
    """Surfaces structural constraints that could force a rewrite.

    Classifies each directory-level constraint as *structural* (requires
    rewrite) or *addressable* (fixable incrementally), with evidence links
    and trigger conditions.
    """

    config = SectionConfig(
        name="rewrite_risk",
        title="Rewrite Risk Assessment",
        description=(
            "Identifies where incremental modernisation breaks down — "
            "distinguishing structural constraints from addressable ones."
        ),
        priority=3,  # After risk register, before deep-dive sections
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        raw_constraints = self._safe_fetch(
            fetcher, "rewrite_risk_constraints", run_pk, fallback=[]
        )

        if not raw_constraints:
            return self._build_result([], [])

        # Group by directory to merge multiple signals
        by_dir: dict[str, list[dict[str, Any]]] = {}
        for row in raw_constraints:
            dp = row["directory_path"]
            by_dir.setdefault(dp, []).append(row)

        # Collect evidence IDs from registry if available
        evidence_ids: dict[str, list[str]] = {}
        registry = self._evidence_registry
        if registry:
            for ev in registry.evidence:
                if ev.category in ("complexity", "coupling", "ownership", "coverage"):
                    evidence_ids.setdefault(ev.category, []).append(ev.evidence_id)

        constraints: list[dict[str, Any]] = []
        for directory_path, rows in by_dir.items():
            signals = list({r["signal"] for r in rows})
            first = rows[0]  # Metrics are the same across signals for a directory
            loc_total = first.get("loc_total", 0) or 0

            constraint_type, risk_level = _classify_constraint(signals, loc_total)

            # Pick the most severe signal for the primary assumption
            primary_signal = signals[0]
            for s in ("monolith", "bidirectional_coupling", "unidirectional_coupling", "untested_core", "knowledge_silo"):
                if s in signals:
                    primary_signal = s
                    break

            # Build linked evidence list
            linked: list[str] = []
            for s in signals:
                if s in ("monolith",) and "complexity" in evidence_ids:
                    linked.extend(evidence_ids["complexity"][:2])
                if s in ("bidirectional_coupling", "unidirectional_coupling") and "coupling" in evidence_ids:
                    linked.extend(evidence_ids["coupling"][:2])
                if s == "knowledge_silo" and "ownership" in evidence_ids:
                    linked.extend(evidence_ids["ownership"][:2])
                if s == "untested_core" and "coverage" in evidence_ids:
                    linked.extend(evidence_ids["coverage"][:2])
            linked = list(dict.fromkeys(linked))  # Dedupe preserving order

            constraints.append({
                "directory": directory_path,
                "constraint_type": constraint_type,
                "risk_level": risk_level,
                "signals": signals,
                "loc_total": loc_total,
                "file_count": first.get("file_count", 0) or 0,
                "loc_gini": first.get("loc_gini", 0) or 0,
                "loc_top_10_pct": first.get("loc_top_10_pct", 0) or 0,
                "avg_ccn": first.get("avg_ccn", 0) or 0,
                "coupling_fan_out": first.get("coupling_fan_out", 0) or 0,
                "coupling_fan_in": first.get("coupling_fan_in", 0) or 0,
                "coverage_line_pct": first.get("coverage_line_pct", 0) or 0,
                "assumption_that_fails": _generate_assumption(primary_signal),
                "why_it_fails": _generate_explanation(primary_signal),
                "trigger_condition": _generate_trigger(primary_signal),
                "linked_evidence": linked,
            })

        # Sort: high → medium → low, structural before addressable
        level_order = {"high": 0, "medium": 1, "low": 2}
        type_order = {"structural": 0, "addressable": 1}
        constraints.sort(
            key=lambda c: (level_order.get(c["risk_level"], 9), type_order.get(c["constraint_type"], 9))
        )

        return self._build_result(constraints, raw_constraints)

    def _build_result(
        self,
        constraints: list[dict[str, Any]],
        raw_constraints: list[dict[str, Any]],
    ) -> dict[str, Any]:
        structural_count = sum(1 for c in constraints if c["constraint_type"] == "structural")
        addressable_count = sum(1 for c in constraints if c["constraint_type"] == "addressable")
        high_count = sum(1 for c in constraints if c["risk_level"] == "high")
        medium_count = sum(1 for c in constraints if c["risk_level"] == "medium")
        low_count = sum(1 for c in constraints if c["risk_level"] == "low")

        # Overall assessment
        if structural_count > 0 and high_count > 0:
            assessment = "significant rewrite risk"
            recommendation = (
                "Multiple structural constraints detected at high risk. "
                "Incremental modernisation will likely stall in these areas. "
                "Consider targeted rewrite strategies for the affected modules."
            )
        elif structural_count > 0:
            assessment = "viable with constraints"
            recommendation = (
                "Structural constraints exist but are not at critical risk levels. "
                "Incremental evolution is possible if these modules are addressed early."
            )
        elif len(constraints) > 0:
            assessment = "incremental evolution viable"
            recommendation = (
                "All detected constraints are addressable through incremental refactoring. "
                "No structural blockers to modernisation were identified."
            )
        else:
            assessment = "incremental evolution viable"
            recommendation = (
                "No significant rewrite risk constraints detected. "
                "The codebase supports incremental modernisation."
            )

        # Type × level matrix
        matrix: dict[str, dict[str, int]] = {
            "structural": {"high": 0, "medium": 0, "low": 0},
            "addressable": {"high": 0, "medium": 0, "low": 0},
        }
        for c in constraints:
            ct = c["constraint_type"]
            rl = c["risk_level"]
            if ct in matrix and rl in matrix[ct]:
                matrix[ct][rl] += 1

        return {
            "constraints": constraints,
            "total_constraints": len(constraints),
            "structural_count": structural_count,
            "addressable_count": addressable_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "assessment": assessment,
            "recommendation": recommendation,
            "matrix": matrix,
            "has_data": len(constraints) > 0,
        }

    def get_template_name(self) -> str:
        return "rewrite_risk.html.j2"

    def get_fallback_data(self) -> dict[str, Any]:
        return {
            "constraints": [],
            "total_constraints": 0,
            "structural_count": 0,
            "addressable_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "assessment": "incremental evolution viable",
            "recommendation": "No data available to assess rewrite risk.",
            "matrix": {
                "structural": {"high": 0, "medium": 0, "low": 0},
                "addressable": {"high": 0, "medium": 0, "low": 0},
            },
            "has_data": False,
        }
