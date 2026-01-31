"""Module D: Measures extraction with metric chunking."""

from dataclasses import dataclass, field
from typing import Any

import structlog

from .client import SonarQubeClient
from .module_c_catalog import CORE_METRICS, filter_available_metrics, get_available_metric_keys

logger = structlog.get_logger(__name__)

PROJECT_ONLY_METRICS = {"quality_gate_details", "alert_status"}


@dataclass
class Measure:
    """A single metric measurement for a component."""

    metric: str
    value: str | None = None
    best_value: bool = False
    period_value: str | None = None  # Value change in leak period

    @classmethod
    def from_api_response(cls, data: dict) -> "Measure":
        """Create Measure from API response."""
        return cls(
            metric=data.get("metric", ""),
            value=data.get("value"),
            best_value=data.get("bestValue", False),
            period_value=data.get("period", {}).get("value") if data.get("period") else None,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        result = {"metric": self.metric}
        if self.value is not None:
            result["value"] = self.value
        if self.best_value:
            result["best_value"] = True
        if self.period_value is not None:
            result["period_value"] = self.period_value
        return result

    def parsed_value(self) -> Any:
        """Get parsed numeric value if applicable."""
        if self.value is None:
            return None
        try:
            if "." in self.value:
                return float(self.value)
            return int(self.value)
        except ValueError:
            return self.value


@dataclass
class ComponentMeasures:
    """Measures for a single component."""

    key: str
    name: str
    qualifier: str
    path: str | None
    language: str | None
    measures: list[Measure] = field(default_factory=list)

    @classmethod
    def from_api_response(cls, data: dict) -> "ComponentMeasures":
        """Create ComponentMeasures from API response."""
        return cls(
            key=data.get("key", ""),
            name=data.get("name", ""),
            qualifier=data.get("qualifier", ""),
            path=data.get("path"),
            language=data.get("language"),
            measures=[Measure.from_api_response(m) for m in data.get("measures", [])],
        )

    def get_measure(self, metric: str) -> Measure | None:
        """Get measure by metric key."""
        for m in self.measures:
            if m.metric == metric:
                return m
        return None

    def get_value(self, metric: str) -> Any:
        """Get parsed value for a metric."""
        measure = self.get_measure(metric)
        return measure.parsed_value() if measure else None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        result = {
            "key": self.key,
            "name": self.name,
            "qualifier": self.qualifier,
            "measures": [m.to_dict() for m in self.measures],
        }
        if self.path:
            result["path"] = self.path
        if self.language:
            result["language"] = self.language
        return result


@dataclass
class MeasuresResult:
    """Collection of measures for all components."""

    by_component_key: dict[str, ComponentMeasures] = field(default_factory=dict)
    metrics_requested: list[str] = field(default_factory=list)

    def get_component(self, key: str) -> ComponentMeasures | None:
        """Get measures for a specific component."""
        return self.by_component_key.get(key)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "by_component_key": {k: v.to_dict() for k, v in self.by_component_key.items()},
            "metrics_requested": self.metrics_requested,
        }


def get_component_measures(
    client: SonarQubeClient,
    component_key: str,
    metric_keys: list[str],
) -> ComponentMeasures:
    """Get measures for a single component.

    Args:
        client: SonarQube API client
        component_key: Component key
        metric_keys: Metrics to fetch

    Returns:
        ComponentMeasures with all requested metrics
    """
    data = client.get(
        "/api/measures/component",
        {
            "component": component_key,
            "metricKeys": ",".join(metric_keys),
        },
    )

    return ComponentMeasures.from_api_response(data.get("component", {}))


def extract_measures_chunked(
    client: SonarQubeClient,
    project_key: str,
    metric_keys: list[str] | None = None,
    qualifiers: str = "FIL,DIR",
    chunk_size: int = 15,
) -> MeasuresResult:
    """Extract measures for all components with metric chunking.

    SonarQube limits the number of metrics per request (typically 15).
    This function chunks the metrics and merges results.

    Args:
        client: SonarQube API client
        project_key: Project key
        metric_keys: Metrics to fetch (uses CORE_METRICS if None)
        qualifiers: Component qualifiers to include
        chunk_size: Number of metrics per request

    Returns:
        MeasuresResult with measures for all components
    """
    metric_keys = metric_keys or CORE_METRICS

    # Filter to only available metrics
    available = get_available_metric_keys(client, include_hidden=True)
    metric_keys = filter_available_metrics(available, metric_keys)
    skipped = sorted(PROJECT_ONLY_METRICS & set(metric_keys))
    if skipped:
        metric_keys = [m for m in metric_keys if m not in PROJECT_ONLY_METRICS]
        logger.warning(
            "Skipping project-only metrics for component_tree extraction",
            skipped=skipped,
        )

    logger.info(
        "Extracting measures",
        project_key=project_key,
        metric_count=len(metric_keys),
        chunk_size=chunk_size,
    )

    result = MeasuresResult(metrics_requested=metric_keys)

    # Chunk metrics and fetch
    for i in range(0, len(metric_keys), chunk_size):
        chunk = metric_keys[i : i + chunk_size]
        logger.debug("Processing metric chunk", chunk_index=i // chunk_size, metrics=chunk)

        params = {
            "component": project_key,
            "metricKeys": ",".join(chunk),
            "qualifiers": qualifiers,
        }

        for item in client.get_paged("/api/measures/component_tree", params, "components"):
            comp = ComponentMeasures.from_api_response(item)

            if comp.key not in result.by_component_key:
                result.by_component_key[comp.key] = comp
            else:
                # Merge measures from this chunk
                result.by_component_key[comp.key].measures.extend(comp.measures)

    logger.info(
        "Measures extraction complete",
        components=len(result.by_component_key),
        metrics=len(metric_keys),
    )

    return result


def get_project_measures(
    client: SonarQubeClient,
    project_key: str,
    metric_keys: list[str] | None = None,
) -> ComponentMeasures:
    """Get measures for the project root component only.

    Args:
        client: SonarQube API client
        project_key: Project key
        metric_keys: Metrics to fetch (uses CORE_METRICS if None)

    Returns:
        ComponentMeasures for the project
    """
    metric_keys = metric_keys or CORE_METRICS

    # Chunk and merge for project level too
    all_measures: list[Measure] = []
    chunk_size = 15

    for i in range(0, len(metric_keys), chunk_size):
        chunk = metric_keys[i : i + chunk_size]
        result = get_component_measures(client, project_key, chunk)
        all_measures.extend(result.measures)

    # Create final result with all measures
    result = get_component_measures(client, project_key, metric_keys[:chunk_size])
    result.measures = all_measures

    return result


def aggregate_directory_measures(measures: MeasuresResult) -> dict[str, dict]:
    """Compute aggregate measures for directories from file measures.

    Args:
        measures: MeasuresResult with file-level measures

    Returns:
        Dictionary mapping directory keys to aggregated measures
    """
    dir_aggregates: dict[str, dict[str, float]] = {}

    for key, comp in measures.by_component_key.items():
        if comp.qualifier != "FIL":
            continue

        # Get parent directory from path
        if not comp.path:
            continue

        parts = comp.path.split("/")
        if len(parts) > 1:
            dir_path = "/".join(parts[:-1])
            # Build synthetic directory key
            project_key = key.rsplit(":", 1)[0] if ":" in key else key
            dir_key = f"{project_key}:{dir_path}"

            if dir_key not in dir_aggregates:
                dir_aggregates[dir_key] = {}

            # Sum numeric measures
            for measure in comp.measures:
                val = measure.parsed_value()
                if isinstance(val, (int, float)):
                    dir_aggregates[dir_key][measure.metric] = (
                        dir_aggregates[dir_key].get(measure.metric, 0) + val
                    )

    return dir_aggregates
