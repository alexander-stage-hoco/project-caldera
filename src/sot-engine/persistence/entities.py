from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


def _validate_identifier(value: str, field_name: str) -> None:
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty identifier")


def _validate_relative_path(value: str, field_name: str) -> None:
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value.startswith(("/", "\\", "./", "~")):
        raise ValueError(f"{field_name} must be repo-relative")
    if ".." in value.split("/"):
        raise ValueError(f"{field_name} must not contain '..'")
    if "\\" in value:
        raise ValueError(f"{field_name} must use '/' separators")


def _validate_non_negative(value: Optional[float], field_name: str) -> None:
    if value is None:
        return
    if value < 0:
        raise ValueError(f"{field_name} must be >= 0")


def _validate_line_range(
    line_start: int | None,
    line_end: int | None,
    field_prefix: str = "",
) -> None:
    """Validate line number range fields.

    Args:
        line_start: Starting line number (must be >= 1 if provided)
        line_end: Ending line number (must be >= 1 if provided)
        field_prefix: Prefix for error messages (e.g., "function" -> "function.line_start")
    """
    prefix = f"{field_prefix}." if field_prefix else ""
    if line_start is not None and line_start < 1:
        raise ValueError(f"{prefix}line_start must be >= 1")
    if line_end is not None and line_end < 1:
        raise ValueError(f"{prefix}line_end must be >= 1")


def _validate_required_string(value: str | None, field_name: str) -> None:
    """Validate that a string field is non-empty."""
    if not value:
        raise ValueError(f"{field_name} must be non-empty")


def _validate_positive_pk(value: int, field_name: str = "run_pk") -> None:
    """Validate that a primary key is positive."""
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _validate_fields_non_negative(fields: dict[str, int | float | None]) -> None:
    """Validate that multiple fields are non-negative."""
    for field_name, value in fields.items():
        _validate_non_negative(value, field_name)


@dataclass(frozen=True)
class ToolRun:
    collection_run_id: str
    repo_id: str
    run_id: str
    tool_name: str
    tool_version: str
    schema_version: str
    branch: str
    commit: str
    timestamp: datetime

    def __post_init__(self) -> None:
        _validate_identifier(self.collection_run_id, "collection_run_id")
        _validate_identifier(self.repo_id, "repo_id")
        _validate_identifier(self.run_id, "run_id")
        if not self.tool_name:
            raise ValueError("tool_name must be non-empty")
        if not self.tool_version:
            raise ValueError("tool_version must be non-empty")
        if not self.schema_version:
            raise ValueError("schema_version must be non-empty")
        if not self.branch:
            raise ValueError("branch must be non-empty")
        if not self.commit or len(self.commit) != 40:
            raise ValueError("commit must be a 40-hex string")


@dataclass(frozen=True)
class CollectionRun:
    collection_run_id: str
    repo_id: str
    run_id: str
    branch: str
    commit: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: str

    def __post_init__(self) -> None:
        _validate_identifier(self.collection_run_id, "collection_run_id")
        _validate_identifier(self.repo_id, "repo_id")
        _validate_identifier(self.run_id, "run_id")
        if not self.branch:
            raise ValueError("branch must be non-empty")
        if not self.commit or len(self.commit) != 40:
            raise ValueError("commit must be a 40-hex string")
        if not self.status:
            raise ValueError("status must be non-empty")


@dataclass(frozen=True)
class LayoutFile:
    run_pk: int
    file_id: str
    relative_path: str
    directory_id: str
    filename: str
    extension: Optional[str]
    language: Optional[str]
    category: Optional[str]
    size_bytes: Optional[int]
    line_count: Optional[int]
    is_binary: Optional[bool]

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.relative_path, "relative_path")


@dataclass(frozen=True)
class LayoutDirectory:
    run_pk: int
    directory_id: str
    relative_path: str
    parent_id: Optional[str]
    depth: int
    file_count: Optional[int]
    total_size_bytes: Optional[int]

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.relative_path, "relative_path")
        _validate_non_negative(self.depth, "depth")


@dataclass(frozen=True)
class SccFileMetric:
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    filename: Optional[str]
    extension: Optional[str]
    language: Optional[str]
    lines_total: Optional[int]
    code_lines: Optional[int]
    comment_lines: Optional[int]
    blank_lines: Optional[int]
    bytes: Optional[int]
    complexity: Optional[int]
    uloc: Optional[int]
    comment_ratio: Optional[float]
    blank_ratio: Optional[float]
    code_ratio: Optional[float]
    complexity_density: Optional[float]
    dryness: Optional[float]
    bytes_per_loc: Optional[float]
    is_minified: Optional[bool]
    is_generated: Optional[bool]
    is_binary: Optional[bool]
    classification: Optional[str]

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.relative_path, "relative_path")
        _validate_fields_non_negative({
            "lines_total": self.lines_total,
            "code_lines": self.code_lines,
            "comment_lines": self.comment_lines,
            "blank_lines": self.blank_lines,
            "bytes": self.bytes,
            "complexity": self.complexity,
            "uloc": self.uloc,
            "comment_ratio": self.comment_ratio,
            "blank_ratio": self.blank_ratio,
            "code_ratio": self.code_ratio,
            "complexity_density": self.complexity_density,
            "dryness": self.dryness,
            "bytes_per_loc": self.bytes_per_loc,
        })


@dataclass(frozen=True)
class LizardFileMetric:
    run_pk: int
    file_id: str
    relative_path: str
    language: Optional[str]
    nloc: Optional[int]
    function_count: Optional[int]
    total_ccn: Optional[int]
    avg_ccn: Optional[float]
    max_ccn: Optional[int]

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.relative_path, "relative_path")
        _validate_fields_non_negative({
            "nloc": self.nloc,
            "function_count": self.function_count,
            "total_ccn": self.total_ccn,
            "avg_ccn": self.avg_ccn,
            "max_ccn": self.max_ccn,
        })


@dataclass(frozen=True)
class LizardFunctionMetric:
    run_pk: int
    file_id: str
    function_name: str
    long_name: Optional[str]
    ccn: Optional[int]
    nloc: Optional[int]
    params: Optional[int]
    token_count: Optional[int]
    line_start: Optional[int]
    line_end: Optional[int]

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_required_string(self.function_name, "function_name")
        _validate_fields_non_negative({
            "ccn": self.ccn,
            "nloc": self.nloc,
            "params": self.params,
            "token_count": self.token_count,
        })
        _validate_line_range(self.line_start, self.line_end)


@dataclass(frozen=True)
class SemgrepSmell:
    """Individual code smell instance from semgrep analysis."""
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    rule_id: str
    dd_smell_id: Optional[str]
    dd_category: Optional[str]
    severity: Optional[str]
    line_start: Optional[int]
    line_end: Optional[int]
    column_start: Optional[int]
    column_end: Optional[int]
    message: Optional[str]
    code_snippet: Optional[str]

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.relative_path, "relative_path")
        _validate_required_string(self.rule_id, "rule_id")
        _validate_line_range(self.line_start, self.line_end)


@dataclass(frozen=True)
class GitleaksSecret:
    """Individual secret finding from gitleaks analysis."""
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    rule_id: str
    secret_type: Optional[str]
    severity: Optional[str]
    line_number: Optional[int]
    commit_hash: Optional[str]
    commit_author: Optional[str]
    commit_date: Optional[str]
    fingerprint: Optional[str]
    in_current_head: Optional[bool]
    entropy: Optional[float]
    description: Optional[str]

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.relative_path, "relative_path")
        _validate_required_string(self.rule_id, "rule_id")
        if self.line_number is not None and self.line_number < 0:
            raise ValueError("line_number must be >= 0")
        if self.entropy is not None and (self.entropy < 0 or self.entropy > 8):
            raise ValueError("entropy must be between 0 and 8")
        if self.severity is not None:
            valid_severities = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
            if self.severity not in valid_severities:
                raise ValueError(f"severity must be one of {valid_severities}")


@dataclass(frozen=True)
class RoslynViolation:
    """Individual violation instance from roslyn-analyzers analysis."""
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    rule_id: str
    dd_category: str
    severity: str
    message: Optional[str]
    line_start: Optional[int]
    line_end: Optional[int]
    column_start: Optional[int]
    column_end: Optional[int]

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.relative_path, "relative_path")
        _validate_required_string(self.rule_id, "rule_id")
        _validate_required_string(self.dd_category, "dd_category")
        _validate_required_string(self.severity, "severity")
        _validate_line_range(self.line_start, self.line_end)


@dataclass(frozen=True)
class DevskimFinding:
    """Individual security finding from DevSkim analysis."""
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    rule_id: str
    dd_category: Optional[str]
    severity: Optional[str]
    line_start: Optional[int]
    line_end: Optional[int]
    column_start: Optional[int]
    column_end: Optional[int]
    message: Optional[str]
    code_snippet: Optional[str]

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.relative_path, "relative_path")
        _validate_required_string(self.rule_id, "rule_id")
        _validate_line_range(self.line_start, self.line_end)
        if self.severity is not None:
            valid_severities = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
            if self.severity not in valid_severities:
                raise ValueError(f"severity must be one of {valid_severities}")



@dataclass(frozen=True)
class SonarqubeIssue:
    """Individual issue instance from SonarQube analysis."""
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    issue_key: str
    rule_id: str
    issue_type: Optional[str]      # BUG, VULNERABILITY, CODE_SMELL, SECURITY_HOTSPOT
    severity: Optional[str]        # BLOCKER, CRITICAL, MAJOR, MINOR, INFO
    message: Optional[str]
    line_start: Optional[int]
    line_end: Optional[int]
    effort: Optional[str]
    status: Optional[str]
    tags: Optional[str]

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.relative_path, "relative_path")
        _validate_required_string(self.issue_key, "issue_key")
        _validate_required_string(self.rule_id, "rule_id")
        _validate_line_range(self.line_start, self.line_end)


@dataclass(frozen=True)
class SonarqubeMetric:
    """Per-file metrics from SonarQube analysis."""
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    ncloc: Optional[int]
    complexity: Optional[int]
    cognitive_complexity: Optional[int]
    duplicated_lines: Optional[int]
    duplicated_lines_density: Optional[float]
    code_smells: Optional[int]
    bugs: Optional[int]
    vulnerabilities: Optional[int]

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.relative_path, "relative_path")
        _validate_fields_non_negative({
            "ncloc": self.ncloc,
            "complexity": self.complexity,
            "cognitive_complexity": self.cognitive_complexity,
            "duplicated_lines": self.duplicated_lines,
            "code_smells": self.code_smells,
            "bugs": self.bugs,
            "vulnerabilities": self.vulnerabilities,
        })
        if self.duplicated_lines_density is not None:
            if self.duplicated_lines_density < 0 or self.duplicated_lines_density > 100:
                raise ValueError("duplicated_lines_density must be between 0 and 100")


@dataclass(frozen=True)
class TrivyVulnerability:
    """Individual vulnerability finding from Trivy analysis."""
    run_pk: int
    target_key: str
    vulnerability_id: str
    package_name: str
    installed_version: Optional[str]
    fixed_version: Optional[str]
    severity: Optional[str]
    cvss_score: Optional[float]
    title: Optional[str]
    published_date: Optional[str]
    age_days: Optional[int]
    fix_available: Optional[bool]

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_required_string(self.target_key, "target_key")
        _validate_required_string(self.vulnerability_id, "vulnerability_id")
        _validate_required_string(self.package_name, "package_name")
        if self.severity is not None:
            valid_severities = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"}
            if self.severity not in valid_severities:
                raise ValueError(f"severity must be one of {valid_severities}")
        if self.cvss_score is not None:
            if self.cvss_score < 0 or self.cvss_score > 10:
                raise ValueError("cvss_score must be between 0 and 10")
        _validate_non_negative(self.age_days, "age_days")


@dataclass(frozen=True)
class TrivyTarget:
    """Scan target (lockfile, Dockerfile, etc.) from Trivy analysis."""
    run_pk: int
    target_key: str
    file_id: Optional[str]
    directory_id: Optional[str]
    relative_path: str
    target_type: Optional[str]
    vulnerability_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_required_string(self.target_key, "target_key")
        _validate_relative_path(self.relative_path, "relative_path")
        _validate_fields_non_negative({
            "vulnerability_count": self.vulnerability_count,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
        })


@dataclass(frozen=True)
class TrivyIacMisconfig:
    """Infrastructure as Code misconfiguration from Trivy analysis."""
    run_pk: int
    file_id: Optional[str]
    directory_id: Optional[str]
    relative_path: str
    misconfig_id: str
    severity: Optional[str]
    title: Optional[str]
    description: Optional[str]
    resolution: Optional[str]
    target_type: Optional[str]
    start_line: Optional[int]
    end_line: Optional[int]

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.relative_path, "relative_path")
        _validate_required_string(self.misconfig_id, "misconfig_id")
        if self.severity is not None:
            valid_severities = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
            if self.severity not in valid_severities:
                raise ValueError(f"severity must be one of {valid_severities}")
        # Allow -1 as sentinel value for file-level issues (no specific line)
        if self.start_line is not None and self.start_line < -1:
            raise ValueError("start_line must be >= -1 (-1 indicates file-level issue)")
        if self.start_line is not None and self.start_line == 0:
            raise ValueError("start_line cannot be 0; use -1 for file-level issues")
        if self.end_line is not None and self.end_line < -1:
            raise ValueError("end_line must be >= -1 (-1 indicates file-level issue)")
        if self.end_line is not None and self.end_line == 0:
            raise ValueError("end_line cannot be 0; use -1 for file-level issues")


# =============================================================================
# git-sizer Entities
# =============================================================================

@dataclass(frozen=True)
class GitSizerMetric:
    """Repository-level metrics from git-sizer analysis."""
    run_pk: int
    repo_id: str
    health_grade: str
    duration_ms: int
    # Commit metrics
    commit_count: int
    commit_total_size: int
    max_commit_size: int
    max_history_depth: int
    max_parent_count: int
    # Tree metrics
    tree_count: int
    tree_total_size: int
    tree_total_entries: int
    max_tree_entries: int
    # Blob metrics
    blob_count: int
    blob_total_size: int
    max_blob_size: int
    # Tag metrics
    tag_count: int
    max_tag_depth: int
    # Reference metrics
    reference_count: int
    branch_count: int
    # Path metrics
    max_path_depth: int
    max_path_length: int
    # Expanded checkout metrics
    expanded_tree_count: int
    expanded_blob_count: int
    expanded_blob_size: int

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_identifier(self.repo_id, "repo_id")
        if self.health_grade not in ("A", "A+", "B", "B+", "C", "C+", "D", "D+", "F"):
            raise ValueError(f"Invalid health_grade: {self.health_grade}")
        _validate_fields_non_negative({
            "duration_ms": self.duration_ms,
            "commit_count": self.commit_count,
            "commit_total_size": self.commit_total_size,
            "max_commit_size": self.max_commit_size,
            "max_history_depth": self.max_history_depth,
            "max_parent_count": self.max_parent_count,
            "tree_count": self.tree_count,
            "tree_total_size": self.tree_total_size,
            "tree_total_entries": self.tree_total_entries,
            "max_tree_entries": self.max_tree_entries,
            "blob_count": self.blob_count,
            "blob_total_size": self.blob_total_size,
            "max_blob_size": self.max_blob_size,
            "tag_count": self.tag_count,
            "max_tag_depth": self.max_tag_depth,
            "reference_count": self.reference_count,
            "branch_count": self.branch_count,
            "max_path_depth": self.max_path_depth,
            "max_path_length": self.max_path_length,
            "expanded_tree_count": self.expanded_tree_count,
            "expanded_blob_count": self.expanded_blob_count,
            "expanded_blob_size": self.expanded_blob_size,
        })


@dataclass(frozen=True)
class GitSizerViolation:
    """Threshold violation from git-sizer analysis."""
    run_pk: int
    metric: str
    value_display: str
    raw_value: int
    level: int
    object_ref: Optional[str]

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_required_string(self.metric, "metric")
        if not 1 <= self.level <= 4:
            raise ValueError(f"level must be 1-4, got {self.level}")


@dataclass(frozen=True)
class GitSizerLfsCandidate:
    """LFS migration candidate from git-sizer analysis."""
    run_pk: int
    file_path: str  # repo-relative

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.file_path, "file_path")


# =============================================================================
# symbol-scanner Entities
# =============================================================================

@dataclass(frozen=True)
class CodeSymbol:
    """Function, class, or method definition from symbol-scanner analysis."""
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    symbol_name: str
    symbol_type: str  # function, class, method, variable
    line_start: int | None
    line_end: int | None
    is_exported: bool
    parameters: int | None
    parent_symbol: str | None
    docstring: str | None

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.relative_path, "relative_path")
        _validate_required_string(self.symbol_name, "symbol_name")
        if self.symbol_type not in ("function", "class", "method", "variable"):
            raise ValueError(f"symbol_type must be function, class, method, or variable, got {self.symbol_type}")
        _validate_line_range(self.line_start, self.line_end)
        if self.parameters is not None and self.parameters < 0:
            raise ValueError("parameters must be >= 0")


@dataclass(frozen=True)
class SymbolCall:
    """Function or method call relationship from symbol-scanner analysis."""
    run_pk: int
    caller_file_id: str
    caller_directory_id: str
    caller_file_path: str
    caller_symbol: str
    callee_symbol: str
    callee_file_id: str | None  # NULL if external/unresolved
    callee_file_path: str | None
    line_number: int | None
    call_type: str | None  # direct, dynamic, async

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.caller_file_path, "caller_file_path")
        _validate_required_string(self.caller_symbol, "caller_symbol")
        _validate_required_string(self.callee_symbol, "callee_symbol")
        if self.callee_file_path is not None:
            _validate_relative_path(self.callee_file_path, "callee_file_path")
        if self.line_number is not None and self.line_number < 1:
            raise ValueError("line_number must be >= 1")
        if self.call_type is not None and self.call_type not in ("direct", "dynamic", "async"):
            raise ValueError(f"call_type must be direct, dynamic, or async, got {self.call_type}")


@dataclass(frozen=True)
class FileImport:
    """Import statement from symbol-scanner analysis."""
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    imported_path: str
    imported_symbols: str | None  # comma-separated or NULL for module import
    import_type: str | None  # static, dynamic, side_effect
    line_number: int | None

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.relative_path, "relative_path")
        _validate_required_string(self.imported_path, "imported_path")
        if self.line_number is not None and self.line_number < 1:
            raise ValueError("line_number must be >= 1")
        if self.import_type is not None and self.import_type not in ("static", "dynamic", "side_effect"):
            raise ValueError(f"import_type must be static, dynamic, or side_effect, got {self.import_type}")


# =============================================================================
# scancode Entities
# =============================================================================

@dataclass(frozen=True)
class ScancodeFileLicense:
    """Individual license finding from scancode analysis."""
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    spdx_id: str
    category: str  # permissive, weak-copyleft, copyleft, unknown
    confidence: float
    match_type: str  # file, header, spdx
    line_number: int | None

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.relative_path, "relative_path")
        _validate_required_string(self.spdx_id, "spdx_id")
        if self.category not in ("permissive", "weak-copyleft", "copyleft", "unknown"):
            raise ValueError(f"category must be permissive, weak-copyleft, copyleft, or unknown, got {self.category}")
        if self.confidence < 0 or self.confidence > 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.match_type not in ("file", "header", "spdx"):
            raise ValueError(f"match_type must be file, header, or spdx, got {self.match_type}")
        if self.line_number is not None and self.line_number < 1:
            raise ValueError("line_number must be >= 1")


@dataclass(frozen=True)
class ScancodeSummary:
    """Repository-level license summary from scancode analysis."""
    run_pk: int
    total_files_scanned: int
    files_with_licenses: int
    overall_risk: str  # low, medium, high, critical, unknown
    has_permissive: bool
    has_weak_copyleft: bool
    has_copyleft: bool
    has_unknown: bool

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_fields_non_negative({
            "total_files_scanned": self.total_files_scanned,
            "files_with_licenses": self.files_with_licenses,
        })
        if self.overall_risk not in ("low", "medium", "high", "critical", "unknown"):
            raise ValueError(f"overall_risk must be low, medium, high, critical, or unknown, got {self.overall_risk}")


# =============================================================================
# pmd-cpd Entities
# =============================================================================

@dataclass(frozen=True)
class PmdCpdFileMetric:
    """Per-file duplication metrics from pmd-cpd analysis."""
    run_pk: int
    file_id: str
    directory_id: str
    relative_path: str
    language: str | None
    total_lines: int
    duplicate_lines: int
    duplicate_blocks: int
    duplication_percentage: float

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.relative_path, "relative_path")
        _validate_fields_non_negative({
            "total_lines": self.total_lines,
            "duplicate_lines": self.duplicate_lines,
            "duplicate_blocks": self.duplicate_blocks,
        })
        if self.duplication_percentage < 0 or self.duplication_percentage > 100:
            raise ValueError("duplication_percentage must be between 0 and 100")


@dataclass(frozen=True)
class PmdCpdDuplication:
    """Clone group record from pmd-cpd analysis."""
    run_pk: int
    clone_id: str
    lines: int
    tokens: int
    occurrence_count: int
    is_cross_file: bool
    code_fragment: str | None

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_required_string(self.clone_id, "clone_id")
        _validate_fields_non_negative({
            "lines": self.lines,
            "tokens": self.tokens,
            "occurrence_count": self.occurrence_count,
        })
        if self.occurrence_count < 2:
            raise ValueError("occurrence_count must be >= 2 for a valid duplication")


@dataclass(frozen=True)
class PmdCpdOccurrence:
    """Individual clone location from pmd-cpd analysis."""
    run_pk: int
    clone_id: str
    file_id: str
    directory_id: str
    relative_path: str
    line_start: int
    line_end: int
    column_start: int | None
    column_end: int | None

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_required_string(self.clone_id, "clone_id")
        _validate_relative_path(self.relative_path, "relative_path")
        _validate_line_range(self.line_start, self.line_end)


# =============================================================================
# dotcover Entities
# =============================================================================

@dataclass(frozen=True)
class DotcoverAssemblyCoverage:
    """Assembly-level coverage metrics from dotCover analysis."""
    run_pk: int
    assembly_name: str
    covered_statements: int
    total_statements: int
    statement_coverage_pct: float

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_required_string(self.assembly_name, "assembly_name")
        _validate_fields_non_negative({
            "covered_statements": self.covered_statements,
            "total_statements": self.total_statements,
        })
        if self.statement_coverage_pct < 0 or self.statement_coverage_pct > 100:
            raise ValueError("statement_coverage_pct must be between 0 and 100")
        if self.covered_statements > self.total_statements:
            raise ValueError("covered_statements cannot exceed total_statements")


@dataclass(frozen=True)
class DotcoverTypeCoverage:
    """Type (class) level coverage metrics from dotCover analysis."""
    run_pk: int
    file_id: Optional[str]       # May be null if file mapping unavailable
    directory_id: Optional[str]
    relative_path: Optional[str]  # Source file path (from DetailedXML)
    assembly_name: str
    namespace: Optional[str]
    type_name: str
    covered_statements: int
    total_statements: int
    statement_coverage_pct: float

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_required_string(self.assembly_name, "assembly_name")
        _validate_required_string(self.type_name, "type_name")
        if self.relative_path:
            _validate_relative_path(self.relative_path, "relative_path")
        _validate_fields_non_negative({
            "covered_statements": self.covered_statements,
            "total_statements": self.total_statements,
        })
        if self.statement_coverage_pct < 0 or self.statement_coverage_pct > 100:
            raise ValueError("statement_coverage_pct must be between 0 and 100")
        if self.covered_statements > self.total_statements:
            raise ValueError("covered_statements cannot exceed total_statements")


@dataclass(frozen=True)
class DotcoverMethodCoverage:
    """Method-level coverage metrics from dotCover analysis."""
    run_pk: int
    assembly_name: str
    type_name: str
    method_name: str
    covered_statements: int
    total_statements: int
    statement_coverage_pct: float

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_required_string(self.assembly_name, "assembly_name")
        _validate_required_string(self.type_name, "type_name")
        _validate_required_string(self.method_name, "method_name")
        _validate_fields_non_negative({
            "covered_statements": self.covered_statements,
            "total_statements": self.total_statements,
        })
        if self.statement_coverage_pct < 0 or self.statement_coverage_pct > 100:
            raise ValueError("statement_coverage_pct must be between 0 and 100")
        if self.covered_statements > self.total_statements:
            raise ValueError("covered_statements cannot exceed total_statements")


# =============================================================================
# dependensee Entities
# =============================================================================

@dataclass(frozen=True)
class DependenseeProject:
    """Project dependency information from dependensee analysis."""
    run_pk: int
    project_path: str
    project_name: str
    target_framework: Optional[str]
    project_reference_count: int
    package_reference_count: int

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.project_path, "project_path")
        _validate_required_string(self.project_name, "project_name")
        _validate_fields_non_negative({
            "project_reference_count": self.project_reference_count,
            "package_reference_count": self.package_reference_count,
        })


@dataclass(frozen=True)
class DependenseeProjectReference:
    """Project-to-project reference from dependensee analysis."""
    run_pk: int
    source_project_path: str
    target_project_path: str

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.source_project_path, "source_project_path")
        _validate_relative_path(self.target_project_path, "target_project_path")


@dataclass(frozen=True)
class DependenseePackageReference:
    """NuGet package reference from dependensee analysis."""
    run_pk: int
    project_path: str
    package_name: str
    package_version: Optional[str]

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.project_path, "project_path")
        _validate_required_string(self.package_name, "package_name")
