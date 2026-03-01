"""
Stakeholder report profiles for Caldera Insights.

Defines curated section subsets for different audiences (CTO, Investor, CEO).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StakeholderProfile:
    """A named report profile targeting a specific stakeholder audience."""

    name: str
    display_name: str
    description: str
    sections: tuple[str, ...]
    title_template: str
    gaps: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Profile name must not be empty.")
        if not self.sections:
            raise ValueError("Profile must include at least one section.")


# ── Built-in profiles ───────────────────────────────────────────────────────

CTO_PROFILE = StakeholderProfile(
    name="cto",
    display_name="CTO / VP Engineering",
    description="Full technical due diligence — all sections included.",
    sections=tuple(
        [
            "tool_readiness",
            "tool_coverage_dashboard",
            "executive_summary",
            "delta_summary",
            "technical_debt_summary",
            "coupling_debt",
            "composite_risk",
            "dependency_health",
            "function_complexity",
            "coverage_gap",
            "dotcover_coverage",
            "component_inventory",
            "import_dependencies",
            "circular_dependencies",
            "blast_radius",
            "code_size_hotspots",
            "git_sizer",
            "repo_health",
            "directory_structure",
            "file_hotspots",
            "directory_analysis",
            "vulnerabilities",
            "secrets",
            "cross_tool",
            "code_quality_rules",
            "sonarqube_deep_dive",
            "coupling_analysis",
            "authorship_risk",
            "knowledge_risk",
            "language_coverage",
            "code_duplication",
            "distribution_insights",
            "roslyn_violations",
            "iac_misconfigs",
            "devskim_security",
            "module_health",
            "code_inequality",
            "license_compliance",
            "risk_register",
            "rewrite_risk",
            "sampling_rationale",
            "evidence_pack",
            "claim_register",
        ]
    ),
    title_template="Technical Due Diligence: {repository}",
)

INVESTOR_PROFILE = StakeholderProfile(
    name="investor",
    display_name="Investor / Acquirer",
    description="Risk and financial signals for investment due diligence.",
    sections=(
        "executive_summary",
        "composite_risk",
        "risk_register",
        "vulnerabilities",
        "secrets",
        "technical_debt_summary",
        "rewrite_risk",
        "code_inequality",
        "coverage_gap",
        "coupling_debt",
        "evidence_pack",
        "claim_register",
        "sampling_rationale",
    ),
    title_template="Investment Risk Assessment: {repository}",
    gaps=("deal_considerations", "financial_implications"),
)

CEO_PROFILE = StakeholderProfile(
    name="ceo",
    display_name="CEO / Board",
    description="High-level technology assessment for decision-makers.",
    sections=(
        "executive_summary",
        "composite_risk",
        "rewrite_risk",
        "technical_debt_summary",
        "risk_register",
    ),
    title_template="Technology Assessment: {repository}",
    gaps=(
        "bottom_line",
        "business_impact_translation",
        "investment_summary",
        "questions_for_tech_team",
    ),
)

BUILTIN_PROFILES: tuple[StakeholderProfile, ...] = (
    CTO_PROFILE,
    INVESTOR_PROFILE,
    CEO_PROFILE,
)

_PROFILE_INDEX: dict[str, StakeholderProfile] = {p.name: p for p in BUILTIN_PROFILES}


def get_profile(name: str) -> StakeholderProfile:
    """Look up a built-in profile by name (case-insensitive).

    Raises ValueError if the name is not recognized.
    """
    profile = _PROFILE_INDEX.get(name.lower())
    if profile is None:
        available = ", ".join(sorted(_PROFILE_INDEX))
        raise ValueError(f"Unknown profile: {name!r}. Available profiles: {available}")
    return profile


def list_profiles() -> list[StakeholderProfile]:
    """Return all built-in profiles."""
    return list(BUILTIN_PROFILES)
