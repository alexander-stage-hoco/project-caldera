"""Tests for ActionGenerator — risk-to-action mapping."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from insights.evidence.action_generator import ActionGenerator, ActionRule
from insights.evidence.entities import ExecutionRisk


def _risk(
    risk_id: str = "RISK-001",
    triggered_by: str = "Security exposure",
    severity: str = "high",
    action: str | None = None,
    sla_date: str | None = None,
) -> ExecutionRisk:
    """
    Create an ExecutionRisk test instance with sensible defaults to simplify tests.
    
    Parameters:
        risk_id (str): Unique identifier for the risk. Defaults to "RISK-001".
        triggered_by (str): Root cause or pattern that triggered the risk (e.g., "Security exposure").
        severity (str): Severity level of the risk (e.g., "low", "medium", "high", "critical").
        action (str | None): Optional pre-set action text; if provided, it will be assigned to the risk.
        sla_date (str | None): Optional SLA due date as an ISO date string (YYYY-MM-DD); if provided, it will be assigned to the risk.
    
    Returns:
        ExecutionRisk: An ExecutionRisk populated with the supplied values and fixed test defaults for description, technical_cause, claim_ids, and manifests_in.
    """
    return ExecutionRisk(
        risk_id=risk_id,
        description="Test risk",
        technical_cause="Test cause",
        claim_ids=("CLM-SEC-001",),
        manifests_in=("src/file.py",),
        triggered_by=triggered_by,
        severity=severity,
        action=action,
        sla_date=sla_date,
    )


class TestActionGenerator:
    """Unit tests for ActionGenerator.enrich()."""

    def _generator(self, now: datetime | None = None) -> ActionGenerator:
        """
        Create an ActionGenerator configured with a fixed current time for tests.
        
        Parameters:
            now (datetime | None): Optional current time to use for the generator; if omitted, uses 2026-03-01 UTC.
        
        Returns:
            ActionGenerator: An ActionGenerator instance whose `now` is set to `now` or the default test date.
        """
        return ActionGenerator(now=now or datetime(2026, 3, 1, tzinfo=timezone.utc))

    def test_enriches_security_exposure_high(self):
        gen = self._generator()
        result = gen.enrich([_risk(severity="high")])
        assert len(result) == 1
        assert result[0].action == "Triage and remediate security findings"
        assert result[0].sla_date == "2026-03-15"  # +14 days

    def test_enriches_security_exposure_critical(self):
        gen = self._generator()
        result = gen.enrich([_risk(severity="critical")])
        assert result[0].sla_date == "2026-03-08"  # +7 days

    def test_enriches_change_amplification(self):
        gen = self._generator()
        result = gen.enrich([_risk(triggered_by="Change amplification", severity="medium")])
        assert result[0].action == "Reduce coupling through interface extraction"
        assert result[0].sla_date == "2026-03-31"  # +30 days

    def test_enriches_knowledge_concentration(self):
        gen = self._generator()
        result = gen.enrich([_risk(triggered_by="Knowledge concentration", severity="medium")])
        assert result[0].action == "Cross-train or document concentrated modules"

    def test_enriches_untested_complexity(self):
        gen = self._generator()
        result = gen.enrich([_risk(triggered_by="Untested complexity", severity="high")])
        assert result[0].action == "Add tests for high-complexity untested code"
        assert result[0].sla_date == "2026-03-15"

    def test_enriches_systemic_debt(self):
        gen = self._generator()
        result = gen.enrich([_risk(triggered_by="Systemic debt", severity="low")])
        assert result[0].action == "Schedule technical debt reduction sprint"
        assert result[0].sla_date == "2026-05-30"  # +90 days

    def test_idempotent_skips_already_set(self):
        gen = self._generator()
        risk = _risk(action="Custom action", sla_date="2026-12-31")
        result = gen.enrich([risk])
        assert result[0].action == "Custom action"
        assert result[0].sla_date == "2026-12-31"

    def test_unknown_pattern_unchanged(self):
        gen = self._generator()
        risk = _risk(triggered_by="Unknown pattern")
        result = gen.enrich([risk])
        assert result[0].action is None
        assert result[0].sla_date is None

    def test_multiple_risks(self):
        gen = self._generator()
        risks = [
            _risk("RISK-001", triggered_by="Security exposure", severity="critical"),
            _risk("RISK-002", triggered_by="Systemic debt", severity="medium"),
        ]
        result = gen.enrich(risks)
        assert len(result) == 2
        assert result[0].action == "Triage and remediate security findings"
        assert result[1].action == "Schedule technical debt reduction sprint"

    def test_empty_list(self):
        gen = self._generator()
        assert gen.enrich([]) == []

    def test_status_preserved(self):
        gen = self._generator()
        result = gen.enrich([_risk()])
        assert result[0].status == "open"

    def test_custom_rules(self):
        rule = ActionRule(
            triggered_by="Custom pattern",
            action="Do custom thing",
            sla_days={"critical": 1, "high": 2, "medium": 3, "low": 4},
        )
        gen = ActionGenerator(
            rules=(rule,),
            now=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        result = gen.enrich([_risk(triggered_by="Custom pattern", severity="high")])
        assert result[0].action == "Do custom thing"
        assert result[0].sla_date == "2026-03-03"  # +2 days
