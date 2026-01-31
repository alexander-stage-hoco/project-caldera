"""Module E: Issues extraction with streaming support."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Iterator

import structlog

from .client import SonarQubeClient

logger = structlog.get_logger(__name__)


class IssueSeverity(Enum):
    """SonarQube issue severities."""

    BLOCKER = "BLOCKER"
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    INFO = "INFO"


class IssueType(Enum):
    """SonarQube issue types."""

    BUG = "BUG"
    VULNERABILITY = "VULNERABILITY"
    CODE_SMELL = "CODE_SMELL"
    SECURITY_HOTSPOT = "SECURITY_HOTSPOT"


class IssueStatus(Enum):
    """SonarQube issue statuses."""

    OPEN = "OPEN"
    CONFIRMED = "CONFIRMED"
    REOPENED = "REOPENED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    TO_REVIEW = "TO_REVIEW"
    IN_REVIEW = "IN_REVIEW"
    REVIEWED = "REVIEWED"


@dataclass
class TextRange:
    """Source code location for an issue."""

    start_line: int
    end_line: int
    start_offset: int = 0
    end_offset: int = 0

    @classmethod
    def from_api_response(cls, data: dict) -> "TextRange":
        """Create TextRange from API response."""
        return cls(
            start_line=data.get("startLine", 0),
            end_line=data.get("endLine", 0),
            start_offset=data.get("startOffset", 0),
            end_offset=data.get("endOffset", 0),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
        }


@dataclass
class Issue:
    """Represents a SonarQube issue."""

    key: str
    rule: str
    severity: IssueSeverity
    type: IssueType
    status: IssueStatus
    message: str
    component: str
    project: str
    line: int | None = None
    text_range: TextRange | None = None
    effort: str | None = None  # Remediation effort
    debt: str | None = None  # Technical debt
    tags: list[str] = field(default_factory=list)
    creation_date: str | None = None
    update_date: str | None = None
    flows: list[dict] = field(default_factory=list)  # Data flow for taint analysis

    @classmethod
    def from_api_response(cls, data: dict) -> "Issue":
        """Create Issue from API response."""
        text_range = None
        if tr := data.get("textRange"):
            text_range = TextRange.from_api_response(tr)

        return cls(
            key=data.get("key", ""),
            rule=data.get("rule", ""),
            severity=IssueSeverity(data.get("severity", "INFO")),
            type=IssueType(data.get("type", "CODE_SMELL")),
            status=IssueStatus(data.get("status", "OPEN")),
            message=data.get("message", ""),
            component=data.get("component", ""),
            project=data.get("project", ""),
            line=data.get("line"),
            text_range=text_range,
            effort=data.get("effort"),
            debt=data.get("debt"),
            tags=data.get("tags", []),
            creation_date=data.get("creationDate"),
            update_date=data.get("updateDate"),
            flows=data.get("flows", []),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        result = {
            "key": self.key,
            "rule": self.rule,
            "severity": self.severity.value,
            "type": self.type.value,
            "status": self.status.value,
            "message": self.message,
            "component": self.component,
            "project": self.project,
        }
        if self.line is not None:
            result["line"] = self.line
        if self.text_range:
            result["text_range"] = self.text_range.to_dict()
        if self.effort:
            result["effort"] = self.effort
        if self.debt:
            result["debt"] = self.debt
        if self.tags:
            result["tags"] = self.tags
        if self.creation_date:
            result["creation_date"] = self.creation_date
        if self.update_date:
            result["update_date"] = self.update_date
        if self.flows:
            result["flows"] = self.flows
        return result


@dataclass
class IssueRollups:
    """Aggregated issue statistics."""

    total: int = 0
    by_severity: dict[str, int] = field(default_factory=dict)
    by_type: dict[str, int] = field(default_factory=dict)
    by_rule: dict[str, int] = field(default_factory=dict)
    by_file: dict[str, int] = field(default_factory=dict)
    by_directory: dict[str, int] = field(default_factory=dict)

    def add_issue(self, issue: Issue) -> None:
        """Update rollups with an issue."""
        self.total += 1

        # By severity
        sev = issue.severity.value
        self.by_severity[sev] = self.by_severity.get(sev, 0) + 1

        # By type
        typ = issue.type.value
        self.by_type[typ] = self.by_type.get(typ, 0) + 1

        # By rule
        self.by_rule[issue.rule] = self.by_rule.get(issue.rule, 0) + 1

        # By file
        self.by_file[issue.component] = self.by_file.get(issue.component, 0) + 1

        # By directory
        if ":" in issue.component:
            path = issue.component.split(":", 1)[1]
            if "/" in path:
                dir_path = "/".join(path.split("/")[:-1])
                self.by_directory[dir_path] = self.by_directory.get(dir_path, 0) + 1

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total": self.total,
            "by_severity": self.by_severity,
            "by_type": self.by_type,
            "by_rule": self.by_rule,
            "by_file": self.by_file,
            "by_directory": self.by_directory,
        }


@dataclass
class IssuesResult:
    """Result of issues extraction."""

    items: list[Issue] = field(default_factory=list)
    rollups: IssueRollups = field(default_factory=IssueRollups)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "items": [i.to_dict() for i in self.items],
            "rollups": self.rollups.to_dict(),
        }


def stream_issues(
    client: SonarQubeClient,
    project_key: str,
    types: list[IssueType] | None = None,
    severities: list[IssueSeverity] | None = None,
    resolved: bool = False,
) -> Iterator[Issue]:
    """Stream issues for a project without loading all into memory.

    Args:
        client: SonarQube API client
        project_key: Project key
        types: Issue types to include (default: all)
        severities: Severities to include (default: all)
        resolved: Whether to include resolved issues

    Yields:
        Issue objects
    """
    params: dict[str, Any] = {
        "componentKeys": project_key,
        "resolved": str(resolved).lower(),
    }

    if types:
        params["types"] = ",".join(t.value for t in types)
    if severities:
        params["severities"] = ",".join(s.value for s in severities)

    for item in client.get_paged("/api/issues/search", params, "issues"):
        yield Issue.from_api_response(item)


def extract_issues(
    client: SonarQubeClient,
    project_key: str,
    types: list[IssueType] | None = None,
    severities: list[IssueSeverity] | None = None,
    resolved: bool = False,
) -> IssuesResult:
    """Extract all issues for a project with rollup statistics.

    Args:
        client: SonarQube API client
        project_key: Project key
        types: Issue types to include (default: all)
        severities: Severities to include (default: all)
        resolved: Whether to include resolved issues

    Returns:
        IssuesResult with all issues and rollups
    """
    logger.info("Extracting issues", project_key=project_key)

    result = IssuesResult()

    for issue in stream_issues(client, project_key, types, severities, resolved):
        result.items.append(issue)
        result.rollups.add_issue(issue)

    logger.info(
        "Issues extraction complete",
        total=result.rollups.total,
        by_type=result.rollups.by_type,
        by_severity=result.rollups.by_severity,
    )

    return result


def stream_issues_to_jsonl(
    client: SonarQubeClient,
    project_key: str,
    output_path: Path,
    types: list[IssueType] | None = None,
    severities: list[IssueSeverity] | None = None,
) -> IssueRollups:
    """Stream issues directly to JSONL file to minimize memory usage.

    Args:
        client: SonarQube API client
        project_key: Project key
        output_path: Path to write JSONL file
        types: Issue types to include (default: all)
        severities: Severities to include (default: all)

    Returns:
        IssueRollups computed while streaming
    """
    logger.info("Streaming issues to JSONL", project_key=project_key, output=str(output_path))

    rollups = IssueRollups()

    with open(output_path, "w") as f:
        for issue in stream_issues(client, project_key, types, severities):
            f.write(json.dumps(issue.to_dict()) + "\n")
            rollups.add_issue(issue)

    logger.info(
        "Issues streaming complete",
        total=rollups.total,
        output=str(output_path),
    )

    return rollups


def get_issue_facets(
    client: SonarQubeClient,
    project_key: str,
    facets: list[str] | None = None,
) -> dict[str, list[dict]]:
    """Get issue facets (aggregations) without fetching all issues.

    Args:
        client: SonarQube API client
        project_key: Project key
        facets: Facets to request (default: common facets)

    Returns:
        Dictionary mapping facet names to their values
    """
    facets = facets or ["types", "severities", "rules", "languages", "tags"]

    data = client.get(
        "/api/issues/search",
        {
            "componentKeys": project_key,
            "ps": 1,  # Minimal page size, we only want facets
            "facets": ",".join(facets),
        },
    )

    result = {}
    for facet in data.get("facets", []):
        result[facet.get("property", "")] = facet.get("values", [])

    return result
