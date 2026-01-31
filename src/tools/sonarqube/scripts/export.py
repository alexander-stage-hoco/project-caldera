"""Export SonarQube data to unified JSON format."""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

from .api.module_b_components import ComponentTree, ComponentQualifier
from .api.module_c_catalog import MetricCatalog
from .api.module_d_measures import MeasuresResult
from .api.module_e_issues import IssuesResult, IssueType, IssueSeverity
from .api.module_f_rules import RulesCache
from .api.module_g_duplications import DuplicationsResult
from .api.module_h_quality_gate import QualityGateResult
from .api.module_i_history import AnalysisHistory

logger = structlog.get_logger(__name__)

SCHEMA_VERSION = "1.2.0"


def normalize_path(path: str, repo_root: str = "") -> str:
    """Normalize file path to repo-relative with forward slashes.

    Args:
        path: File path to normalize
        repo_root: Optional repository root to strip from path

    Returns:
        Normalized path with forward slashes
    """
    path = path.replace("\\", "/")
    if repo_root:
        repo_root = repo_root.replace("\\", "/").rstrip("/")
        if path.startswith(repo_root + "/"):
            path = path[len(repo_root) + 1:]
    if path.startswith("./"):
        path = path[2:]
    if path.startswith("/"):
        path = path[1:]
    return path


@dataclass
class DerivedInsights:
    """Derived insights computed from raw data."""

    hotspots: list[dict]
    directory_rollups: dict[str, dict]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "hotspots": self.hotspots,
            "directory_rollups": self.directory_rollups,
        }


def compute_hotspots(
    components: ComponentTree,
    measures: MeasuresResult,
    issues: IssuesResult,
    top_n: int = 50,
) -> list[dict]:
    """Compute file hotspots based on complexity, issues, and size.

    Args:
        components: Component tree
        measures: Component measures
        issues: Issue data
        top_n: Number of hotspots to return

    Returns:
        List of hotspot dictionaries
    """
    file_scores = []

    for file_comp in components.files:
        comp_measures = measures.get_component(file_comp.key)
        if not comp_measures:
            continue

        # Get metrics
        ncloc = comp_measures.get_value("ncloc")
        if not ncloc:
            ncloc = comp_measures.get_value("lines") or 0
        complexity = comp_measures.get_value("complexity") or 0
        cognitive_complexity = comp_measures.get_value("cognitive_complexity") or 0
        issues_count = issues.rollups.by_file.get(file_comp.key, 0)

        # Skip tiny files unless there are issues to surface
        if ncloc < 10 and issues_count == 0:
            continue

        # Compute hotspot score (weighted combination)
        score = (
            complexity * 0.3
            + cognitive_complexity * 0.3
            + issues_count * 10  # Issues are weighted heavily
            + ncloc * 0.01  # Size has small weight
        )

        file_scores.append({
            "key": file_comp.key,
            "path": file_comp.path,
            "language": file_comp.language,
            "score": score,
            "ncloc": ncloc,
            "complexity": complexity,
            "cognitive_complexity": cognitive_complexity,
            "issues": issues_count,
        })

    # Sort by score descending
    file_scores.sort(key=lambda x: x["score"], reverse=True)

    return file_scores[:top_n]


def compute_directory_rollups(
    components: ComponentTree,
    measures: MeasuresResult,
    issues: IssuesResult,
) -> dict[str, dict]:
    """Compute aggregated metrics for directories.

    Args:
        components: Component tree
        measures: Component measures
        issues: Issue data

    Returns:
        Dictionary mapping directory paths to rollup metrics
    """
    rollups: dict[str, dict] = {}

    for file_comp in components.files:
        if not file_comp.path:
            continue

        # Get directory path (root-level files roll up under "/")
        parts = file_comp.path.split("/")
        dir_path = "/" if len(parts) < 2 else "/".join(parts[:-1])

        if dir_path not in rollups:
            rollups[dir_path] = {
                "files": 0,
                "ncloc": 0,
                "complexity": 0,
                "issues": 0,
                "bugs": 0,
                "vulnerabilities": 0,
                "code_smells": 0,
            }

        rollups[dir_path]["files"] += 1

        # Add measures
        comp_measures = measures.get_component(file_comp.key)
        if comp_measures:
            ncloc_val = comp_measures.get_value("ncloc")
            if not ncloc_val:
                ncloc_val = comp_measures.get_value("lines")
            if ncloc_val:
                rollups[dir_path]["ncloc"] = rollups[dir_path].get("ncloc", 0) + ncloc_val
            complexity_val = comp_measures.get_value("complexity")
            if complexity_val:
                rollups[dir_path]["complexity"] = rollups[dir_path].get("complexity", 0) + complexity_val

        # Add issues
        rollups[dir_path]["issues"] += issues.rollups.by_file.get(file_comp.key, 0)

    # Add issue type breakdowns from directory rollups
    for issue in issues.items:
        if ":" in issue.component:
            path = issue.component.split(":", 1)[1]
            if "/" in path:
                dir_path = "/".join(path.split("/")[:-1])
                if dir_path in rollups:
                    if issue.type == IssueType.BUG:
                        rollups[dir_path]["bugs"] += 1
                    elif issue.type == IssueType.VULNERABILITY:
                        rollups[dir_path]["vulnerabilities"] += 1
                    elif issue.type == IssueType.CODE_SMELL:
                        rollups[dir_path]["code_smells"] += 1

    return rollups


def build_export_data(
    source: dict,
    metric_catalog: MetricCatalog,
    components: ComponentTree,
    measures: MeasuresResult,
    issues: IssuesResult,
    rules: RulesCache,
    duplications: DuplicationsResult,
    quality_gate: QualityGateResult,
    analyses: AnalysisHistory,
    metadata: dict | None = None,
    tool_version: str = "unknown",
) -> dict:
    """Build the complete export data structure.

    Args:
        source: Source metadata
        metric_catalog: Available metrics
        components: Component tree
        measures: Component measures
        issues: Issue data
        rules: Rule metadata
        duplications: Duplication data
        quality_gate: Quality gate status
        analyses: Analysis history

    Returns:
        Complete export data dictionary
    """
    # Compute derived insights
    hotspots = compute_hotspots(components, measures, issues)
    directory_rollups = compute_directory_rollups(components, measures, issues)

    derived = DerivedInsights(
        hotspots=hotspots,
        directory_rollups=directory_rollups,
    )

    # Extract repo_name and repo_path from source for root level (per TOOL_REQUIREMENTS.md)
    repo_name = source.get("repo_name", "")
    repo_path = source.get("repo_path", "")

    data = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_name": repo_name,
        "repo_path": repo_path,
        "results": {
            "tool": "sonarqube",
            "tool_version": tool_version,
            "source": source,
            "metric_catalog": metric_catalog.to_list(),
            "components": components.to_dict(),
            "measures": measures.to_dict(),
            "issues": issues.to_dict(),
            "rules": rules.to_dict(),
            "duplications": duplications.to_dict(),
            "quality_gate": quality_gate.to_dict(),
            "analyses": analyses.to_list(),
            "derived_insights": derived.to_dict(),
            "limitations": {
                "no_symbol_graph": True,
                "no_call_graph": True,
                "no_data_flow": True,
                "issues_may_be_truncated": len(issues.items) >= 10000,
            },
        },
    }

    if metadata is not None:
        data["metadata"] = metadata

    return data


def export_unified_json(
    output_path: Path,
    source: dict,
    metric_catalog: MetricCatalog,
    components: ComponentTree,
    measures: MeasuresResult,
    issues: IssuesResult,
    rules: RulesCache,
    duplications: DuplicationsResult,
    quality_gate: QualityGateResult,
    analyses: AnalysisHistory,
    tool_version: str = "unknown",
    metadata: dict | None = None,
    indent: int = 2,
) -> dict:
    """Export all data to unified JSON file.

    Args:
        output_path: Path to write JSON file
        source: Source metadata
        metric_catalog: Available metrics
        components: Component tree
        measures: Component measures
        issues: Issue data
        rules: Rule metadata
        duplications: Duplication data
        quality_gate: Quality gate status
        analyses: Analysis history
        indent: JSON indentation level

    Returns:
        The exported data dictionary
    """
    data = build_export_data(
        source=source,
        metric_catalog=metric_catalog,
        components=components,
        measures=measures,
        issues=issues,
        rules=rules,
        duplications=duplications,
        quality_gate=quality_gate,
        analyses=analyses,
        tool_version=tool_version,
        metadata=metadata,
    )

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    with open(output_path, "w") as f:
        json.dump(data, f, indent=indent, default=str)

    logger.info(
        "Exported unified JSON",
        path=str(output_path),
        size_bytes=output_path.stat().st_size,
    )

    return data


def validate_export(output_path: Path, schema_path: Path | None = None) -> bool:
    """Validate exported JSON against schema.

    Args:
        output_path: Path to exported JSON
        schema_path: Path to JSON schema (uses default if None)

    Returns:
        True if valid, False otherwise
    """
    if not HAS_JSONSCHEMA:
        logger.warning("jsonschema not installed, skipping validation")
        return True

    if schema_path is None:
        schema_path = Path(__file__).parent.parent / "schemas" / "sonar_export.schema.json"

    if not schema_path.exists():
        logger.warning("Schema file not found", path=str(schema_path))
        return True

    try:
        with open(output_path) as f:
            data = json.load(f)
        with open(schema_path) as f:
            schema = json.load(f)

        jsonschema.validate(data, schema)
        logger.info("Export validation passed")
        return True

    except jsonschema.ValidationError as e:
        logger.error("Export validation failed", error=str(e.message), path=str(e.path))
        return False
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON", error=str(e))
        return False


def export_summary(data: dict) -> dict:
    """Create a summary of the exported data.

    Args:
        data: Full export data

    Returns:
        Summary dictionary
    """
    # Get results wrapper (tool-specific data)
    results = data.get("results", {})
    issues = results.get("issues", {})
    rollups = issues.get("rollups", {})

    return {
        "schema_version": data.get("schema_version"),
        "generated_at": data.get("generated_at"),
        "project_key": results.get("source", {}).get("project_key"),
        "quality_gate_status": results.get("quality_gate", {}).get("status"),
        "total_issues": rollups.get("total", 0),
        "bugs": rollups.get("by_type", {}).get("BUG", 0),
        "vulnerabilities": rollups.get("by_type", {}).get("VULNERABILITY", 0),
        "code_smells": rollups.get("by_type", {}).get("CODE_SMELL", 0),
        "components": len(results.get("components", {}).get("by_key", {})),
        "files": sum(
            1 for c in results.get("components", {}).get("by_key", {}).values()
            if c.get("qualifier") == "FIL"
        ),
        "hotspots_count": len(results.get("derived_insights", {}).get("hotspots", [])),
    }
