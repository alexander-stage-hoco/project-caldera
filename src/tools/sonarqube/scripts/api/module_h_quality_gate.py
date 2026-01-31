"""Module H: Quality gate status extraction."""

from dataclasses import dataclass, field
from enum import Enum

import structlog

from .client import SonarQubeClient

logger = structlog.get_logger(__name__)


class QualityGateStatus(Enum):
    """Quality gate overall status."""

    OK = "OK"
    WARN = "WARN"  # Deprecated but may still appear
    ERROR = "ERROR"
    NONE = "NONE"


class ConditionStatus(Enum):
    """Status of an individual condition."""

    OK = "OK"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass
class QualityGateCondition:
    """A single quality gate condition."""

    metric: str
    comparator: str  # LT, GT, EQ
    threshold: str
    status: ConditionStatus
    actual_value: str | None = None
    error_threshold: str | None = None
    warning_threshold: str | None = None

    @classmethod
    def from_api_response(cls, data: dict) -> "QualityGateCondition":
        """Create from API response."""
        return cls(
            metric=data.get("metricKey", data.get("metric", "")),
            comparator=data.get("comparator", data.get("op", "")),
            threshold=data.get("errorThreshold", data.get("error", "")),
            status=ConditionStatus(data.get("status", "OK")),
            actual_value=data.get("actualValue", data.get("actual")),
            error_threshold=data.get("errorThreshold", data.get("error")),
            warning_threshold=data.get("warningThreshold", data.get("warning")),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            "metric": self.metric,
            "comparator": self.comparator,
            "threshold": self.threshold,
            "status": self.status.value,
        }
        if self.actual_value:
            result["actual_value"] = self.actual_value
        if self.error_threshold:
            result["error_threshold"] = self.error_threshold
        return result


@dataclass
class QualityGateResult:
    """Quality gate evaluation result."""

    status: QualityGateStatus
    name: str = ""
    conditions: list[QualityGateCondition] = field(default_factory=list)
    ignored_conditions: bool = False
    period_index: int | None = None

    @classmethod
    def from_api_response(cls, data: dict) -> "QualityGateResult":
        """Create from API response."""
        project_status = data.get("projectStatus", data)

        conditions = []
        for cond in project_status.get("conditions", []):
            conditions.append(QualityGateCondition.from_api_response(cond))

        return cls(
            status=QualityGateStatus(project_status.get("status", "NONE")),
            name=project_status.get("name", ""),
            conditions=conditions,
            ignored_conditions=project_status.get("ignoredConditions", False),
            period_index=project_status.get("periodIndex"),
        )

    @property
    def failed_conditions(self) -> list[QualityGateCondition]:
        """Get conditions that failed (ERROR status)."""
        return [c for c in self.conditions if c.status == ConditionStatus.ERROR]

    @property
    def warning_conditions(self) -> list[QualityGateCondition]:
        """Get conditions with warnings."""
        return [c for c in self.conditions if c.status == ConditionStatus.WARN]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "status": self.status.value,
            "name": self.name,
            "conditions": [c.to_dict() for c in self.conditions],
            "ignored_conditions": self.ignored_conditions,
            "failed_count": len(self.failed_conditions),
            "warning_count": len(self.warning_conditions),
        }


def _conditions_from_definition(definition: dict) -> list[QualityGateCondition]:
    """Convert quality gate definition conditions into result conditions."""
    conditions = []
    for cond in definition.get("conditions", []):
        metric = cond.get("metric") or cond.get("metricKey") or ""
        comparator = cond.get("op") or cond.get("comparator") or ""
        threshold = cond.get("error") or cond.get("errorThreshold") or ""
        conditions.append(
            QualityGateCondition(
                metric=metric,
                comparator=comparator,
                threshold=str(threshold),
                status=ConditionStatus.OK,
                actual_value=None,
                error_threshold=cond.get("error") or cond.get("errorThreshold"),
                warning_threshold=cond.get("warning") or cond.get("warningThreshold"),
            )
        )
    return conditions


def get_quality_gate_status(
    client: SonarQubeClient,
    project_key: str,
    analysis_id: str | None = None,
) -> QualityGateResult:
    """Get quality gate status for a project.

    Args:
        client: SonarQube API client
        project_key: Project key
        analysis_id: Specific analysis ID (uses latest if None)

    Returns:
        QualityGateResult with status and conditions
    """
    logger.info("Getting quality gate status", project_key=project_key)

    if analysis_id:
        params = {"analysisId": analysis_id}
    else:
        params = {"projectKey": project_key}

    data = client.get("/api/qualitygates/project_status", params)
    result = QualityGateResult.from_api_response(data)

    if not result.conditions and result.status != QualityGateStatus.NONE:
        definition = get_quality_gate_definition(client, project_key)
        fallback_conditions = _conditions_from_definition(definition)
        if fallback_conditions:
            result.conditions = fallback_conditions
            if not result.name:
                result.name = definition.get("name", "")

    logger.info(
        "Quality gate status retrieved",
        status=result.status.value,
        failed_conditions=len(result.failed_conditions),
    )

    return result


def get_quality_gate_definition(
    client: SonarQubeClient,
    project_key: str | None = None,
) -> dict:
    """Get the quality gate definition for a project or default.

    Args:
        client: SonarQube API client
        project_key: Project key (uses default gate if None)

    Returns:
        Quality gate definition
    """
    if project_key:
        # Get the gate assigned to the project
        data = client.get("/api/qualitygates/get_by_project", {"project": project_key})
        gate = data.get("qualityGate", {})
        gate_id = gate.get("id")
        gate_name = gate.get("name")
        if gate_id:
            data = client.get("/api/qualitygates/show", {"id": gate_id})
        elif gate_name:
            data = client.get("/api/qualitygates/show", {"name": gate_name})
        else:
            # Fall back to default gate if project gate is missing
            data = client.get("/api/qualitygates/list")
            gates = data.get("qualitygates", [])
            default_gate = next((g for g in gates if g.get("isDefault")), gates[0] if gates else {})
            default_id = default_gate.get("id") if default_gate else None
            default_name = default_gate.get("name") if default_gate else None
            if default_id:
                data = client.get("/api/qualitygates/show", {"id": default_id})
            elif default_name:
                data = client.get("/api/qualitygates/show", {"name": default_name})
    else:
        # Get the default gate
        data = client.get("/api/qualitygates/list")
        gates = data.get("qualitygates", [])
        default_gate = next((g for g in gates if g.get("isDefault")), gates[0] if gates else {})
        default_id = default_gate.get("id") if default_gate else None
        default_name = default_gate.get("name") if default_gate else None
        if default_id:
            data = client.get("/api/qualitygates/show", {"id": default_id})
        elif default_name:
            data = client.get("/api/qualitygates/show", {"name": default_name})

    return data.get("qualityGate", data)


def evaluate_custom_gate(
    measures: dict[str, float],
    conditions: list[dict],
) -> QualityGateResult:
    """Evaluate measures against custom conditions.

    Useful for testing or simulating quality gates.

    Args:
        measures: Dictionary of metric -> value
        conditions: List of condition definitions

    Returns:
        QualityGateResult with evaluation
    """
    result_conditions = []
    overall_status = QualityGateStatus.OK

    for cond in conditions:
        metric = cond.get("metric", "")
        comparator = cond.get("comparator", "GT")
        threshold = float(cond.get("threshold", 0))
        actual = measures.get(metric)

        status = ConditionStatus.OK
        if actual is not None:
            if comparator == "GT" and actual > threshold:
                status = ConditionStatus.ERROR
            elif comparator == "LT" and actual < threshold:
                status = ConditionStatus.ERROR
            elif comparator == "EQ" and actual == threshold:
                status = ConditionStatus.ERROR

        if status == ConditionStatus.ERROR:
            overall_status = QualityGateStatus.ERROR

        result_conditions.append(
            QualityGateCondition(
                metric=metric,
                comparator=comparator,
                threshold=str(threshold),
                status=status,
                actual_value=str(actual) if actual is not None else None,
            )
        )

    return QualityGateResult(
        status=overall_status,
        name="Custom Gate",
        conditions=result_conditions,
    )
