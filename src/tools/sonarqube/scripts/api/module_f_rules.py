"""Module F: Rule metadata extraction."""

from dataclasses import dataclass, field
from enum import Enum

import structlog

from .client import SonarQubeClient

logger = structlog.get_logger(__name__)


class RuleType(Enum):
    """SonarQube rule types."""

    BUG = "BUG"
    VULNERABILITY = "VULNERABILITY"
    CODE_SMELL = "CODE_SMELL"
    SECURITY_HOTSPOT = "SECURITY_HOTSPOT"


class RuleSeverity(Enum):
    """SonarQube rule severities."""

    BLOCKER = "BLOCKER"
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    INFO = "INFO"


class RuleStatus(Enum):
    """SonarQube rule statuses."""

    READY = "READY"
    BETA = "BETA"
    DEPRECATED = "DEPRECATED"
    REMOVED = "REMOVED"


@dataclass
class Rule:
    """Represents a SonarQube rule definition."""

    key: str
    name: str
    type: RuleType
    severity: RuleSeverity
    status: RuleStatus
    language: str
    html_desc: str = ""
    tags: list[str] = field(default_factory=list)
    security_standards: dict[str, list[str]] = field(default_factory=dict)
    remediation_function: str | None = None
    remediation_effort: str | None = None
    debt_time: str | None = None

    @classmethod
    def from_api_response(cls, data: dict) -> "Rule":
        """Create Rule from API response."""
        # Parse security standards
        security_standards = {}
        if cwe := data.get("cwe"):
            security_standards["cwe"] = cwe
        if owasp_top10 := data.get("owaspTop10"):
            security_standards["owaspTop10"] = owasp_top10
        if owasp_top10_2021 := data.get("owaspTop10-2021"):
            security_standards["owaspTop10-2021"] = owasp_top10_2021
        if sans_top25 := data.get("sansTop25"):
            security_standards["sansTop25"] = sans_top25

        return cls(
            key=data.get("key", ""),
            name=data.get("name", ""),
            type=RuleType(data.get("type", "CODE_SMELL")),
            severity=RuleSeverity(data.get("severity", "MAJOR")),
            status=RuleStatus(data.get("status", "READY")),
            language=data.get("lang", ""),
            html_desc=data.get("htmlDesc", ""),
            tags=data.get("sysTags", []) + data.get("tags", []),
            security_standards=security_standards,
            remediation_function=data.get("remFnType"),
            remediation_effort=data.get("remFnBaseEffort"),
            debt_time=data.get("defaultRemFnBaseEffort"),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        result = {
            "key": self.key,
            "name": self.name,
            "type": self.type.value,
            "severity": self.severity.value,
            "status": self.status.value,
            "language": self.language,
        }
        if self.html_desc:
            result["html_desc"] = self.html_desc
        if self.tags:
            result["tags"] = self.tags
        if self.security_standards:
            result["security_standards"] = self.security_standards
        if self.remediation_effort:
            result["remediation_effort"] = self.remediation_effort
        return result


@dataclass
class RulesCache:
    """Cache of rule definitions."""

    by_key: dict[str, Rule] = field(default_factory=dict)

    def get(self, key: str) -> Rule | None:
        """Get rule by key."""
        return self.by_key.get(key)

    def add(self, rule: Rule) -> None:
        """Add rule to cache."""
        self.by_key[rule.key] = rule

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {"by_key": {k: v.to_dict() for k, v in self.by_key.items()}}


def get_rule(client: SonarQubeClient, rule_key: str) -> Rule:
    """Get a single rule by key.

    Args:
        client: SonarQube API client
        rule_key: Rule key (e.g., "java:S1234")

    Returns:
        Rule object
    """
    data = client.get("/api/rules/show", {"key": rule_key})
    return Rule.from_api_response(data.get("rule", {}))


def get_rules_for_issues(
    client: SonarQubeClient,
    rule_keys: set[str],
    cache: RulesCache | None = None,
) -> RulesCache:
    """Fetch rule metadata for a set of rule keys.

    Uses caching to avoid redundant API calls.

    Args:
        client: SonarQube API client
        rule_keys: Set of rule keys to fetch
        cache: Optional existing cache to extend

    Returns:
        RulesCache with all requested rules
    """
    cache = cache or RulesCache()

    # Filter out already cached rules
    needed = [k for k in rule_keys if k not in cache.by_key]

    if not needed:
        logger.debug("All rules already cached", count=len(rule_keys))
        return cache

    logger.info("Fetching rule metadata", count=len(needed))

    for rule_key in needed:
        try:
            rule = get_rule(client, rule_key)
            cache.add(rule)
        except Exception as e:
            logger.warning("Failed to fetch rule", rule_key=rule_key, error=str(e))

    logger.info("Rules fetched", total=len(cache.by_key))
    return cache


def search_rules(
    client: SonarQubeClient,
    languages: list[str] | None = None,
    types: list[RuleType] | None = None,
    tags: list[str] | None = None,
    active_only: bool = True,
) -> list[Rule]:
    """Search for rules matching criteria.

    Args:
        client: SonarQube API client
        languages: Filter by languages
        types: Filter by rule types
        tags: Filter by tags
        active_only: Only return active rules

    Returns:
        List of matching rules
    """
    params = {}

    if languages:
        params["languages"] = ",".join(languages)
    if types:
        params["types"] = ",".join(t.value for t in types)
    if tags:
        params["tags"] = ",".join(tags)
    if active_only:
        params["activation"] = "true"

    rules = []
    for item in client.get_paged("/api/rules/search", params, "rules"):
        rules.append(Rule.from_api_response(item))

    logger.info("Rules search complete", count=len(rules))
    return rules


def get_security_rules(client: SonarQubeClient, language: str | None = None) -> list[Rule]:
    """Get security-related rules.

    Args:
        client: SonarQube API client
        language: Optional language filter

    Returns:
        List of security rules
    """
    params = {
        "types": "VULNERABILITY,SECURITY_HOTSPOT",
        "tags": "security,cwe,owasp",
    }
    if language:
        params["languages"] = language

    rules = []
    for item in client.get_paged("/api/rules/search", params, "rules"):
        rules.append(Rule.from_api_response(item))

    return rules


def hydrate_rules_for_project(
    client: SonarQubeClient,
    project_key: str,
) -> RulesCache:
    """Get all rules that have issues in a project.

    First queries for unique rule keys in issues, then fetches metadata.

    Args:
        client: SonarQube API client
        project_key: Project key

    Returns:
        RulesCache with rules that have issues
    """
    # Get facets to find unique rules
    data = client.get(
        "/api/issues/search",
        {
            "componentKeys": project_key,
            "ps": 1,
            "facets": "rules",
        },
    )

    rule_keys = set()
    for facet in data.get("facets", []):
        if facet.get("property") == "rules":
            for value in facet.get("values", []):
                rule_keys.add(value.get("val", ""))

    return get_rules_for_issues(client, rule_keys)
