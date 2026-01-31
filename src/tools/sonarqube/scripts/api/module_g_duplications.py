"""Module G: Duplications extraction."""

from dataclasses import dataclass, field

import structlog

from .client import SonarQubeClient
from .module_d_measures import get_component_measures

logger = structlog.get_logger(__name__)


@dataclass
class DuplicatedBlock:
    """A block of duplicated code."""

    from_line: int
    size: int  # Number of lines

    @classmethod
    def from_api_response(cls, data: dict) -> "DuplicatedBlock":
        """Create from API response."""
        return cls(
            from_line=data.get("from", 0),
            size=data.get("size", 0),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "from_line": self.from_line,
            "size": self.size,
        }


@dataclass
class Duplication:
    """A duplication instance (original + copies)."""

    blocks: list[dict] = field(default_factory=list)  # List of {file_key, from_line, size}

    @classmethod
    def from_api_response(cls, data: dict) -> "Duplication":
        """Create from API response."""
        blocks = []
        for block in data.get("blocks", []):
            blocks.append({
                "file_key": block.get("_ref", block.get("key", "")),
                "from_line": block.get("from", 0),
                "size": block.get("size", 0),
            })
        return cls(blocks=blocks)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {"blocks": self.blocks}


@dataclass
class FileDuplicationInfo:
    """Duplication information for a single file."""

    key: str
    duplicated_lines: int = 0
    duplicated_lines_density: float = 0.0
    duplicated_blocks: int = 0
    duplications: list[Duplication] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "duplicated_lines": self.duplicated_lines,
            "duplicated_lines_density": self.duplicated_lines_density,
            "duplicated_blocks": self.duplicated_blocks,
            "duplications": [d.to_dict() for d in self.duplications],
        }


@dataclass
class DuplicationPolicy:
    """Policy for duplication extraction."""

    top_n: int = 200  # Number of files to extract detailed duplications for
    min_density: float = 0.0  # Minimum duplication density to include

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "top_n": self.top_n,
            "min_density": self.min_density,
        }


@dataclass
class DuplicationsResult:
    """Result of duplication extraction."""

    policy: DuplicationPolicy
    by_file_key: dict[str, FileDuplicationInfo] = field(default_factory=dict)
    project_summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "policy": self.policy.to_dict(),
            "by_file_key": {k: v.to_dict() for k, v in self.by_file_key.items()},
            "project_summary": self.project_summary,
        }


def get_file_duplications(client: SonarQubeClient, file_key: str) -> FileDuplicationInfo:
    """Get detailed duplication information for a file.

    Args:
        client: SonarQube API client
        file_key: File component key

    Returns:
        FileDuplicationInfo with duplication details
    """
    data = client.get("/api/duplications/show", {"key": file_key})

    info = FileDuplicationInfo(key=file_key)

    # Parse duplications
    duplications = data.get("duplications", [])
    for dup in duplications:
        info.duplications.append(Duplication.from_api_response(dup))

    # Get measures for summary stats
    try:
        measures = get_component_measures(
            client,
            file_key,
            ["duplicated_lines", "duplicated_lines_density", "duplicated_blocks"],
        )
        for m in measures.measures:
            val = m.parsed_value()
            if m.metric == "duplicated_lines" and val:
                info.duplicated_lines = int(val)
            elif m.metric == "duplicated_lines_density" and val:
                info.duplicated_lines_density = float(val)
            elif m.metric == "duplicated_blocks" and val:
                info.duplicated_blocks = int(val)
    except Exception as e:
        logger.debug("Could not get duplication measures", file_key=file_key, error=str(e))

    return info


def get_files_by_duplication_density(
    client: SonarQubeClient,
    project_key: str,
    top_n: int = 200,
    min_density: float = 0.0,
) -> list[tuple[str, float]]:
    """Get files sorted by duplication density.

    Args:
        client: SonarQube API client
        project_key: Project key
        top_n: Maximum number of files to return
        min_density: Minimum density threshold

    Returns:
        List of (file_key, density) tuples sorted by density descending
    """
    params = {
        "component": project_key,
        "metricKeys": "duplicated_lines_density",
        "metricSort": "duplicated_lines_density",
        "metricSortFilter": "withMeasuresOnly",
        "asc": "false",
        "s": "metric",
        "qualifiers": "FIL",
    }

    files = []
    count = 0

    for item in client.get_paged("/api/measures/component_tree", params, "components"):
        if count >= top_n:
            break

        measures = item.get("measures", [])
        density = 0.0
        for m in measures:
            if m.get("metric") == "duplicated_lines_density":
                try:
                    density = float(m.get("value", 0))
                except ValueError:
                    pass
                break

        if density >= min_density:
            files.append((item.get("key", ""), density))
            count += 1

    return files


def extract_duplications(
    client: SonarQubeClient,
    project_key: str,
    policy: DuplicationPolicy | None = None,
) -> DuplicationsResult:
    """Extract duplication data for a project.

    Fetches detailed duplication information for the top-N files
    by duplication density.

    Args:
        client: SonarQube API client
        project_key: Project key
        policy: Extraction policy (default: top 200 files)

    Returns:
        DuplicationsResult with duplication data
    """
    policy = policy or DuplicationPolicy()

    logger.info(
        "Extracting duplications",
        project_key=project_key,
        top_n=policy.top_n,
        min_density=policy.min_density,
    )

    result = DuplicationsResult(policy=policy)

    # Get project-level duplication summary
    try:
        project_measures = get_component_measures(
            client,
            project_key,
            [
                "duplicated_lines",
                "duplicated_lines_density",
                "duplicated_blocks",
                "duplicated_files",
            ],
        )
        for m in project_measures.measures:
            val = m.parsed_value()
            if val is not None:
                result.project_summary[m.metric] = val
    except Exception as e:
        logger.warning("Could not get project duplication summary", error=str(e))

    # Get top files by duplication
    top_files = get_files_by_duplication_density(
        client, project_key, policy.top_n, policy.min_density
    )

    logger.info("Found files with duplications", count=len(top_files))

    # Fetch detailed duplications for each
    for file_key, density in top_files:
        try:
            info = get_file_duplications(client, file_key)
            info.duplicated_lines_density = density
            result.by_file_key[file_key] = info
        except Exception as e:
            logger.debug("Could not get duplications for file", file_key=file_key, error=str(e))

    logger.info(
        "Duplications extraction complete",
        files_with_dups=len(result.by_file_key),
        project_dup_density=result.project_summary.get("duplicated_lines_density", 0),
    )

    return result
