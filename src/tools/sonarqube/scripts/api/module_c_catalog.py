"""Module C: Metric catalog discovery."""

from dataclasses import dataclass
from enum import Enum

import structlog

from .client import SonarQubeClient

logger = structlog.get_logger(__name__)


class MetricType(Enum):
    """SonarQube metric value types."""

    INT = "INT"
    FLOAT = "FLOAT"
    PERCENT = "PERCENT"
    BOOL = "BOOL"
    STRING = "STRING"
    MILLISEC = "MILLISEC"
    DATA = "DATA"
    LEVEL = "LEVEL"
    DISTRIB = "DISTRIB"
    RATING = "RATING"
    WORK_DUR = "WORK_DUR"


class MetricDomain(Enum):
    """SonarQube metric domains."""

    RELIABILITY = "Reliability"
    SECURITY = "Security"
    SECURITY_REVIEW = "SecurityReview"
    MAINTAINABILITY = "Maintainability"
    COVERAGE = "Coverage"
    DUPLICATIONS = "Duplications"
    SIZE = "Size"
    COMPLEXITY = "Complexity"
    DOCUMENTATION = "Documentation"
    ISSUES = "Issues"
    GENERAL = "General"
    RELEASABILITY = "Releasability"


@dataclass
class Metric:
    """Represents a SonarQube metric definition."""

    key: str
    name: str
    description: str
    domain: str
    type: MetricType
    direction: int  # -1 (lower is better), 0 (neutral), 1 (higher is better)
    qualitative: bool  # True if metric has quality threshold
    hidden: bool

    @classmethod
    def from_api_response(cls, data: dict) -> "Metric":
        """Create Metric from API response."""
        return cls(
            key=data.get("key", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            domain=data.get("domain", ""),
            type=MetricType(data.get("type", "INT")),
            direction=data.get("direction", 0),
            qualitative=data.get("qualitative", False),
            hidden=data.get("hidden", False),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "domain": self.domain,
            "type": self.type.value,
            "direction": self.direction,
            "qualitative": self.qualitative,
            "hidden": self.hidden,
        }


@dataclass
class MetricCatalog:
    """Collection of all available metrics."""

    metrics: dict[str, Metric]

    @property
    def visible_metrics(self) -> list[Metric]:
        """Get non-hidden metrics."""
        return [m for m in self.metrics.values() if not m.hidden]

    @property
    def metric_keys(self) -> list[str]:
        """Get all metric keys."""
        return list(self.metrics.keys())

    def get_by_domain(self, domain: str) -> list[Metric]:
        """Get metrics by domain."""
        return [m for m in self.metrics.values() if m.domain == domain]

    def to_list(self) -> list[dict]:
        """Convert to list of dictionaries for JSON export."""
        return [m.to_dict() for m in self.metrics.values()]


# Core metrics we always want to extract
CORE_METRICS = [
    # Size
    "ncloc",
    "lines",
    "statements",
    "functions",
    "classes",
    "files",
    "directories",
    "comment_lines",
    "comment_lines_density",
    # Complexity
    "complexity",
    "cognitive_complexity",
    "file_complexity",
    "function_complexity",
    # Duplications
    "duplicated_lines",
    "duplicated_lines_density",
    "duplicated_blocks",
    "duplicated_files",
    # Issues
    "violations",
    "blocker_violations",
    "critical_violations",
    "major_violations",
    "minor_violations",
    "info_violations",
    "bugs",
    "vulnerabilities",
    "code_smells",
    "security_hotspots",
    # Reliability
    "reliability_rating",
    "reliability_remediation_effort",
    # Security
    "security_rating",
    "security_remediation_effort",
    "security_review_rating",
    "security_hotspots_reviewed",
    # Maintainability
    "sqale_rating",  # Maintainability rating
    "sqale_index",  # Technical debt in minutes
    "sqale_debt_ratio",
    # Coverage
    "coverage",
    "line_coverage",
    "branch_coverage",
    "lines_to_cover",
    "uncovered_lines",
    "conditions_to_cover",
    "uncovered_conditions",
    # Quality Gate
    "alert_status",
    "quality_gate_details",
]


def discover_all_metrics(client: SonarQubeClient) -> MetricCatalog:
    """Discover all available metrics from SonarQube.

    Args:
        client: SonarQube API client

    Returns:
        MetricCatalog with all available metrics
    """
    logger.info("Discovering available metrics")

    metrics: dict[str, Metric] = {}

    for item in client.get_paged("/api/metrics/search", {}, "metrics"):
        metric = Metric.from_api_response(item)
        metrics[metric.key] = metric

    logger.info(
        "Metrics discovered",
        total=len(metrics),
        visible=sum(1 for m in metrics.values() if not m.hidden),
    )

    return MetricCatalog(metrics=metrics)


def get_available_metric_keys(client: SonarQubeClient, include_hidden: bool = False) -> list[str]:
    """Get list of available metric keys.

    Args:
        client: SonarQube API client
        include_hidden: Whether to include hidden metrics

    Returns:
        List of metric keys
    """
    catalog = discover_all_metrics(client)
    if include_hidden:
        return catalog.metric_keys
    return [m.key for m in catalog.visible_metrics]


def filter_available_metrics(
    available: list[str],
    requested: list[str] | None = None,
) -> list[str]:
    """Filter requested metrics to only those available.

    Args:
        available: List of available metric keys
        requested: Requested metrics (uses CORE_METRICS if None)

    Returns:
        Filtered list of metric keys
    """
    requested = requested or CORE_METRICS
    available_set = set(available)
    filtered = [m for m in requested if m in available_set]

    if len(filtered) < len(requested):
        missing = set(requested) - available_set
        logger.warning("Some requested metrics not available", missing=list(missing))

    return filtered
