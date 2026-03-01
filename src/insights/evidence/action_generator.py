"""Action generator — enriches execution risks with default remediation actions.

Maps ``triggered_by`` patterns to default actions and SLA offsets so the
risk register is immediately actionable without manual triage.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone

from .entities import ExecutionRisk, RiskSeverity


@dataclass(frozen=True)
class ActionRule:
    """Maps a risk pattern to a default remediation action and SLA."""

    triggered_by: str
    action: str
    sla_days: dict[RiskSeverity, int]


DEFAULT_ACTION_RULES: tuple[ActionRule, ...] = (
    ActionRule(
        triggered_by="Security exposure",
        action="Triage and remediate security findings",
        sla_days={"critical": 7, "high": 14, "medium": 30, "low": 90},
    ),
    ActionRule(
        triggered_by="Change amplification",
        action="Reduce coupling through interface extraction",
        sla_days={"critical": 7, "high": 14, "medium": 30, "low": 90},
    ),
    ActionRule(
        triggered_by="Knowledge concentration",
        action="Cross-train or document concentrated modules",
        sla_days={"critical": 7, "high": 14, "medium": 30, "low": 90},
    ),
    ActionRule(
        triggered_by="Untested complexity",
        action="Add tests for high-complexity untested code",
        sla_days={"critical": 7, "high": 14, "medium": 30, "low": 90},
    ),
    ActionRule(
        triggered_by="Systemic debt",
        action="Schedule technical debt reduction sprint",
        sla_days={"critical": 14, "high": 30, "medium": 60, "low": 90},
    ),
)


class ActionGenerator:
    """Enriches ``ExecutionRisk`` instances with default actions and SLA dates.

    Enrichment is idempotent: risks that already have an ``action`` set are
    returned unchanged.
    """

    def __init__(
        self,
        rules: tuple[ActionRule, ...] | None = None,
        *,
        now: datetime | None = None,
    ) -> None:
        self._rules = rules or DEFAULT_ACTION_RULES
        self._rules_by_pattern: dict[str, ActionRule] = {
            r.triggered_by: r for r in self._rules
        }
        self._now = now or datetime.now(timezone.utc)

    def enrich(self, risks: list[ExecutionRisk]) -> list[ExecutionRisk]:
        """Return a new list of risks with action/sla_date populated."""
        return [self._enrich_one(r) for r in risks]

    def _enrich_one(self, risk: ExecutionRisk) -> ExecutionRisk:
        # Idempotent: skip if action already assigned
        if risk.action is not None:
            return risk

        rule = self._rules_by_pattern.get(risk.triggered_by)
        if rule is None:
            return risk

        sla_offset = rule.sla_days.get(risk.severity, 30)
        sla_date = (self._now + timedelta(days=sla_offset)).strftime("%Y-%m-%d")

        return replace(risk, action=rule.action, sla_date=sla_date)
