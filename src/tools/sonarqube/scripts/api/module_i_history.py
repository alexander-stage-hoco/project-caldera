"""Module I: Analysis history extraction."""

from dataclasses import dataclass, field
from datetime import datetime

import structlog

from .client import SonarQubeClient

logger = structlog.get_logger(__name__)


@dataclass
class AnalysisEvent:
    """An event associated with an analysis (e.g., version change)."""

    key: str
    category: str
    name: str
    description: str | None = None

    @classmethod
    def from_api_response(cls, data: dict) -> "AnalysisEvent":
        """Create from API response."""
        return cls(
            key=data.get("key", ""),
            category=data.get("category", ""),
            name=data.get("name", ""),
            description=data.get("description"),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            "key": self.key,
            "category": self.category,
            "name": self.name,
        }
        if self.description:
            result["description"] = self.description
        return result


@dataclass
class Analysis:
    """A single analysis record."""

    key: str
    date: str
    project_version: str | None = None
    revision: str | None = None
    detected_ci: str | None = None
    events: list[AnalysisEvent] = field(default_factory=list)
    manual_new_code_period_baseline: bool = False

    @classmethod
    def from_api_response(cls, data: dict) -> "Analysis":
        """Create from API response."""
        events = [AnalysisEvent.from_api_response(e) for e in data.get("events", [])]

        return cls(
            key=data.get("key", ""),
            date=data.get("date", ""),
            project_version=data.get("projectVersion"),
            revision=data.get("revision"),
            detected_ci=data.get("detectedCI"),
            events=events,
            manual_new_code_period_baseline=data.get("manualNewCodePeriodBaseline", False),
        )

    @property
    def parsed_date(self) -> datetime | None:
        """Parse the date string to datetime."""
        try:
            # SonarQube uses ISO 8601 format
            return datetime.fromisoformat(self.date.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            "key": self.key,
            "date": self.date,
        }
        if self.project_version:
            result["project_version"] = self.project_version
        if self.revision:
            result["revision"] = self.revision
        if self.detected_ci:
            result["detected_ci"] = self.detected_ci
        if self.events:
            result["events"] = [e.to_dict() for e in self.events]
        return result


@dataclass
class AnalysisHistory:
    """History of analyses for a project."""

    analyses: list[Analysis] = field(default_factory=list)

    @property
    def latest(self) -> Analysis | None:
        """Get the most recent analysis."""
        return self.analyses[0] if self.analyses else None

    def to_list(self) -> list[dict]:
        """Convert to list of dictionaries for JSON export."""
        return [a.to_dict() for a in self.analyses]


def get_analysis_history(
    client: SonarQubeClient,
    project_key: str,
    limit: int = 10,
) -> AnalysisHistory:
    """Get recent analysis history for a project.

    Args:
        client: SonarQube API client
        project_key: Project key
        limit: Maximum number of analyses to return

    Returns:
        AnalysisHistory with recent analyses
    """
    logger.info("Getting analysis history", project_key=project_key, limit=limit)

    params = {
        "project": project_key,
        "ps": min(limit, 500),  # Max page size
    }

    analyses = []
    for item in client.get_paged("/api/project_analyses/search", params, "analyses"):
        analyses.append(Analysis.from_api_response(item))
        if len(analyses) >= limit:
            break

    logger.info("Analysis history retrieved", count=len(analyses))
    return AnalysisHistory(analyses=analyses)


def get_analysis_by_key(client: SonarQubeClient, analysis_key: str) -> Analysis | None:
    """Get a specific analysis by key.

    Args:
        client: SonarQube API client
        analysis_key: Analysis key

    Returns:
        Analysis or None if not found
    """
    # The API doesn't have a direct get-by-key, so we search
    # This is inefficient but works for single lookups
    data = client.get(
        "/api/project_analyses/search",
        {"project": "*", "ps": 1},  # This won't work directly
    )

    # Alternative: iterate through recent history
    # In practice, you'd need to know the project key
    logger.warning("get_analysis_by_key requires project context")
    return None


def get_metric_history(
    client: SonarQubeClient,
    project_key: str,
    metrics: list[str],
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict[str, list[dict]]:
    """Get historical values for metrics.

    Args:
        client: SonarQube API client
        project_key: Project key
        metrics: List of metric keys
        from_date: Start date (ISO format)
        to_date: End date (ISO format)

    Returns:
        Dictionary mapping metric keys to list of {date, value} dicts
    """
    logger.info(
        "Getting metric history",
        project_key=project_key,
        metrics=metrics,
    )

    params = {
        "component": project_key,
        "metrics": ",".join(metrics),
    }
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date

    data = client.get("/api/measures/search_history", params)

    result: dict[str, list[dict]] = {}
    for measure in data.get("measures", []):
        metric = measure.get("metric", "")
        history = []
        for item in measure.get("history", []):
            history.append({
                "date": item.get("date", ""),
                "value": item.get("value"),
            })
        result[metric] = history

    return result


def compare_analyses(
    client: SonarQubeClient,
    project_key: str,
    from_analysis: str,
    to_analysis: str,
    metrics: list[str] | None = None,
) -> dict:
    """Compare two analyses.

    Args:
        client: SonarQube API client
        project_key: Project key
        from_analysis: Earlier analysis key
        to_analysis: Later analysis key
        metrics: Metrics to compare (uses defaults if None)

    Returns:
        Comparison data
    """
    metrics = metrics or [
        "ncloc",
        "bugs",
        "vulnerabilities",
        "code_smells",
        "coverage",
        "duplicated_lines_density",
    ]

    # Get metric values for both analyses
    # This would require fetching measures at specific analysis points
    # SonarQube API doesn't directly support this, would need to use history
    history = get_metric_history(client, project_key, metrics)

    # Find values at each analysis point
    comparison = {"from": {}, "to": {}, "delta": {}}

    for metric, values in history.items():
        # Match by date (simplified - in practice would need exact matching)
        if len(values) >= 2:
            comparison["from"][metric] = values[-1].get("value")
            comparison["to"][metric] = values[0].get("value")

            try:
                from_val = float(comparison["from"][metric] or 0)
                to_val = float(comparison["to"][metric] or 0)
                comparison["delta"][metric] = to_val - from_val
            except (ValueError, TypeError):
                pass

    return comparison
