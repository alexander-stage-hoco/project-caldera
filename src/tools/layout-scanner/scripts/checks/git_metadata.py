"""
Git Metadata Checks (GT-1 to GT-6).

Validates git metadata enrichment when the git pass is enabled.
These checks are optional and only run when passes_completed includes "git".
"""

import re
from typing import Any, Dict, List

from . import CheckCategory, CheckResult, register_check


def run_git_metadata_checks(output: Dict[str, Any]) -> List[CheckResult]:
    """
    Run all git metadata checks.

    Only runs if "git" is in passes_completed.
    """
    passes = output.get("passes_completed", [])
    if "git" not in passes:
        # Git pass not enabled, return empty list
        return []

    checks = []
    checks.append(check_git_pass_recorded(output))
    checks.append(check_dates_valid_iso8601(output))
    checks.append(check_date_ordering(output))
    checks.append(check_commit_count_valid(output))
    checks.append(check_author_count_valid(output))
    checks.append(check_git_coverage(output))

    return checks


def has_git_pass(output: Dict[str, Any]) -> bool:
    """Check if git pass was completed."""
    return "git" in output.get("passes_completed", [])


# ISO 8601 date pattern (with timezone)
ISO8601_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}([+-]\d{2}:\d{2}|Z)?$"
)


def is_valid_iso8601(date_str: str) -> bool:
    """Check if string is valid ISO 8601 datetime."""
    if not date_str:
        return False
    return bool(ISO8601_PATTERN.match(date_str))


@register_check("GT-1")
def check_git_pass_recorded(output: Dict[str, Any]) -> CheckResult:
    """GT-1: Git pass is recorded in passes_completed."""
    passes = output.get("passes_completed", [])

    if "git" in passes:
        return CheckResult(
            check_id="GT-1",
            name="Git Pass Recorded",
            category=CheckCategory.GIT_METADATA,
            passed=True,
            score=1.0,
            message="'git' pass recorded in passes_completed",
            evidence={"passes_completed": passes},
        )

    return CheckResult(
        check_id="GT-1",
        name="Git Pass Recorded",
        category=CheckCategory.GIT_METADATA,
        passed=False,
        score=0.0,
        message="'git' pass not found in passes_completed",
        evidence={"passes_completed": passes},
    )


@register_check("GT-2")
def check_dates_valid_iso8601(output: Dict[str, Any]) -> CheckResult:
    """GT-2: All git dates are valid ISO 8601 format."""
    files = output.get("files", {})

    invalid_dates = []

    for path, file_obj in files.items():
        first_date = file_obj.get("first_commit_date")
        last_date = file_obj.get("last_commit_date")

        # Only check non-null dates
        if first_date is not None and not is_valid_iso8601(first_date):
            invalid_dates.append({
                "path": path,
                "field": "first_commit_date",
                "value": first_date,
            })

        if last_date is not None and not is_valid_iso8601(last_date):
            invalid_dates.append({
                "path": path,
                "field": "last_commit_date",
                "value": last_date,
            })

    if invalid_dates:
        return CheckResult(
            check_id="GT-2",
            name="Dates Valid ISO 8601",
            category=CheckCategory.GIT_METADATA,
            passed=False,
            score=0.0,
            message=f"{len(invalid_dates)} invalid ISO 8601 dates found",
            evidence={"invalid_dates": invalid_dates[:10]},
        )

    return CheckResult(
        check_id="GT-2",
        name="Dates Valid ISO 8601",
        category=CheckCategory.GIT_METADATA,
        passed=True,
        score=1.0,
        message="All git dates are valid ISO 8601",
    )


@register_check("GT-3")
def check_date_ordering(output: Dict[str, Any]) -> CheckResult:
    """GT-3: first_commit_date <= last_commit_date for all files."""
    files = output.get("files", {})

    ordering_errors = []

    for path, file_obj in files.items():
        first_date = file_obj.get("first_commit_date")
        last_date = file_obj.get("last_commit_date")

        # Skip if either is null
        if first_date is None or last_date is None:
            continue

        # Compare dates as strings (ISO 8601 sorts correctly)
        if first_date > last_date:
            ordering_errors.append({
                "path": path,
                "first_commit_date": first_date,
                "last_commit_date": last_date,
            })

    if ordering_errors:
        return CheckResult(
            check_id="GT-3",
            name="Date Ordering",
            category=CheckCategory.GIT_METADATA,
            passed=False,
            score=0.0,
            message=f"{len(ordering_errors)} files have first_commit_date > last_commit_date",
            evidence={"ordering_errors": ordering_errors[:10]},
        )

    return CheckResult(
        check_id="GT-3",
        name="Date Ordering",
        category=CheckCategory.GIT_METADATA,
        passed=True,
        score=1.0,
        message="All file date orderings are valid",
    )


@register_check("GT-4")
def check_commit_count_valid(output: Dict[str, Any]) -> CheckResult:
    """GT-4: commit_count is positive integer or null."""
    files = output.get("files", {})

    invalid_counts = []

    for path, file_obj in files.items():
        commit_count = file_obj.get("commit_count")

        # Null is valid (file not tracked)
        if commit_count is None:
            continue

        # Must be positive integer
        if not isinstance(commit_count, int) or commit_count < 0:
            invalid_counts.append({
                "path": path,
                "commit_count": commit_count,
            })

    if invalid_counts:
        return CheckResult(
            check_id="GT-4",
            name="Commit Count Valid",
            category=CheckCategory.GIT_METADATA,
            passed=False,
            score=0.0,
            message=f"{len(invalid_counts)} files have invalid commit_count",
            evidence={"invalid_counts": invalid_counts[:10]},
        )

    return CheckResult(
        check_id="GT-4",
        name="Commit Count Valid",
        category=CheckCategory.GIT_METADATA,
        passed=True,
        score=1.0,
        message="All commit_count values are valid",
    )


@register_check("GT-5")
def check_author_count_valid(output: Dict[str, Any]) -> CheckResult:
    """GT-5: author_count is positive integer or null."""
    files = output.get("files", {})

    invalid_counts = []

    for path, file_obj in files.items():
        author_count = file_obj.get("author_count")

        # Null is valid (file not tracked)
        if author_count is None:
            continue

        # Must be positive integer
        if not isinstance(author_count, int) or author_count < 0:
            invalid_counts.append({
                "path": path,
                "author_count": author_count,
            })

    if invalid_counts:
        return CheckResult(
            check_id="GT-5",
            name="Author Count Valid",
            category=CheckCategory.GIT_METADATA,
            passed=False,
            score=0.0,
            message=f"{len(invalid_counts)} files have invalid author_count",
            evidence={"invalid_counts": invalid_counts[:10]},
        )

    return CheckResult(
        check_id="GT-5",
        name="Author Count Valid",
        category=CheckCategory.GIT_METADATA,
        passed=True,
        score=1.0,
        message="All author_count values are valid",
    )


@register_check("GT-6")
def check_git_coverage(output: Dict[str, Any]) -> CheckResult:
    """GT-6: Reasonable coverage - >50% of files have git metadata."""
    files = output.get("files", {})

    total_files = len(files)
    if total_files == 0:
        return CheckResult(
            check_id="GT-6",
            name="Git Coverage",
            category=CheckCategory.GIT_METADATA,
            passed=True,
            score=1.0,
            message="No files to check",
        )

    files_with_git = 0
    for file_obj in files.values():
        if file_obj.get("commit_count") is not None:
            files_with_git += 1

    coverage = files_with_git / total_files

    if coverage >= 0.5:
        return CheckResult(
            check_id="GT-6",
            name="Git Coverage",
            category=CheckCategory.GIT_METADATA,
            passed=True,
            score=coverage,
            message=f"{files_with_git}/{total_files} files ({coverage:.0%}) have git metadata",
            evidence={
                "files_with_git": files_with_git,
                "total_files": total_files,
                "coverage": round(coverage, 3),
            },
        )

    return CheckResult(
        check_id="GT-6",
        name="Git Coverage",
        category=CheckCategory.GIT_METADATA,
        passed=False,
        score=coverage,
        message=f"Low coverage: {files_with_git}/{total_files} files ({coverage:.0%}) have git metadata",
        evidence={
            "files_with_git": files_with_git,
            "total_files": total_files,
            "coverage": round(coverage, 3),
        },
    )
