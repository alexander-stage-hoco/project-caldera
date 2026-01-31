"""
Content Metadata Checks (CT-1 to CT-6).

Validates content metadata enrichment when the content pass is enabled.
These checks are optional and only run when passes_completed includes "content".
"""

import re
from typing import Any, Dict, List

from . import CheckCategory, CheckResult, register_check


def run_content_metadata_checks(output: Dict[str, Any]) -> List[CheckResult]:
    """
    Run all content metadata checks.

    Only runs if "content" is in passes_completed.
    """
    passes = output.get("passes_completed", [])
    if "content" not in passes:
        # Content pass not enabled, return empty list
        return []

    checks = []
    checks.append(check_content_pass_recorded(output))
    checks.append(check_hashes_valid_hex(output))
    checks.append(check_line_counts_valid(output))
    checks.append(check_binary_files_no_line_count(output))
    checks.append(check_text_file_coverage(output))
    checks.append(check_hash_consistency(output))

    return checks


def has_content_pass(output: Dict[str, Any]) -> bool:
    """Check if content pass was completed."""
    return "content" in output.get("passes_completed", [])


# SHA-256 hex pattern (64 lowercase hex characters)
SHA256_HEX_PATTERN = re.compile(r"^[a-f0-9]{64}$")

# SHA-1 hex pattern (40 lowercase hex characters)
SHA1_HEX_PATTERN = re.compile(r"^[a-f0-9]{40}$")

# MD5 hex pattern (32 lowercase hex characters)
MD5_HEX_PATTERN = re.compile(r"^[a-f0-9]{32}$")


def is_valid_hash_hex(hash_str: str) -> bool:
    """Check if string is valid hex hash (SHA-256, SHA-1, or MD5)."""
    if not hash_str:
        return False
    return bool(
        SHA256_HEX_PATTERN.match(hash_str)
        or SHA1_HEX_PATTERN.match(hash_str)
        or MD5_HEX_PATTERN.match(hash_str)
    )


@register_check("CT-1")
def check_content_pass_recorded(output: Dict[str, Any]) -> CheckResult:
    """CT-1: Content pass is recorded in passes_completed."""
    passes = output.get("passes_completed", [])

    if "content" in passes:
        return CheckResult(
            check_id="CT-1",
            name="Content Pass Recorded",
            category=CheckCategory.CONTENT_METADATA,
            passed=True,
            score=1.0,
            message="'content' pass recorded in passes_completed",
            evidence={"passes_completed": passes},
        )

    return CheckResult(
        check_id="CT-1",
        name="Content Pass Recorded",
        category=CheckCategory.CONTENT_METADATA,
        passed=False,
        score=0.0,
        message="'content' pass not found in passes_completed",
        evidence={"passes_completed": passes},
    )


@register_check("CT-2")
def check_hashes_valid_hex(output: Dict[str, Any]) -> CheckResult:
    """CT-2: All content_hash values are valid hex strings."""
    files = output.get("files", {})

    invalid_hashes = []

    for path, file_obj in files.items():
        content_hash = file_obj.get("content_hash")

        # Only check non-null hashes
        if content_hash is not None and not is_valid_hash_hex(content_hash):
            invalid_hashes.append({
                "path": path,
                "content_hash": content_hash,
            })

    if invalid_hashes:
        return CheckResult(
            check_id="CT-2",
            name="Hashes Valid Hex",
            category=CheckCategory.CONTENT_METADATA,
            passed=False,
            score=0.0,
            message=f"{len(invalid_hashes)} invalid hash values found",
            evidence={"invalid_hashes": invalid_hashes[:10]},
        )

    return CheckResult(
        check_id="CT-2",
        name="Hashes Valid Hex",
        category=CheckCategory.CONTENT_METADATA,
        passed=True,
        score=1.0,
        message="All content_hash values are valid hex strings",
    )


@register_check("CT-3")
def check_line_counts_valid(output: Dict[str, Any]) -> CheckResult:
    """CT-3: line_count is non-negative integer or null."""
    files = output.get("files", {})

    invalid_counts = []

    for path, file_obj in files.items():
        line_count = file_obj.get("line_count")

        # Null is valid (binary file or not enriched)
        if line_count is None:
            continue

        # Must be non-negative integer
        if not isinstance(line_count, int) or line_count < 0:
            invalid_counts.append({
                "path": path,
                "line_count": line_count,
            })

    if invalid_counts:
        return CheckResult(
            check_id="CT-3",
            name="Line Counts Valid",
            category=CheckCategory.CONTENT_METADATA,
            passed=False,
            score=0.0,
            message=f"{len(invalid_counts)} files have invalid line_count",
            evidence={"invalid_counts": invalid_counts[:10]},
        )

    return CheckResult(
        check_id="CT-3",
        name="Line Counts Valid",
        category=CheckCategory.CONTENT_METADATA,
        passed=True,
        score=1.0,
        message="All line_count values are valid (non-negative integer or null)",
    )


@register_check("CT-4")
def check_binary_files_no_line_count(output: Dict[str, Any]) -> CheckResult:
    """CT-4: Binary files have null line_count, text files have counts."""
    files = output.get("files", {})

    violations = []

    for path, file_obj in files.items():
        is_binary = file_obj.get("is_binary")
        line_count = file_obj.get("line_count")

        # Skip if is_binary is not set
        if is_binary is None:
            continue

        if is_binary and line_count is not None:
            # Binary file should not have line count
            violations.append({
                "path": path,
                "is_binary": True,
                "line_count": line_count,
                "issue": "binary file has line_count",
            })
        elif not is_binary and line_count is None:
            # Text file should have line count
            violations.append({
                "path": path,
                "is_binary": False,
                "line_count": None,
                "issue": "text file missing line_count",
            })

    if violations:
        return CheckResult(
            check_id="CT-4",
            name="Binary/Text Consistency",
            category=CheckCategory.CONTENT_METADATA,
            passed=False,
            score=0.0,
            message=f"{len(violations)} files have inconsistent binary/line_count",
            evidence={"violations": violations[:10]},
        )

    return CheckResult(
        check_id="CT-4",
        name="Binary/Text Consistency",
        category=CheckCategory.CONTENT_METADATA,
        passed=True,
        score=1.0,
        message="Binary files have null line_count, text files have counts",
    )


@register_check("CT-5")
def check_text_file_coverage(output: Dict[str, Any]) -> CheckResult:
    """CT-5: >90% of text files have line counts."""
    files = output.get("files", {})

    total_text_files = 0
    text_files_with_counts = 0

    for file_obj in files.values():
        is_binary = file_obj.get("is_binary")

        # Only count text files (is_binary is explicitly False)
        if is_binary is False:
            total_text_files += 1
            if file_obj.get("line_count") is not None:
                text_files_with_counts += 1

    if total_text_files == 0:
        return CheckResult(
            check_id="CT-5",
            name="Text File Coverage",
            category=CheckCategory.CONTENT_METADATA,
            passed=True,
            score=1.0,
            message="No text files to check",
        )

    coverage = text_files_with_counts / total_text_files

    if coverage >= 0.9:
        return CheckResult(
            check_id="CT-5",
            name="Text File Coverage",
            category=CheckCategory.CONTENT_METADATA,
            passed=True,
            score=coverage,
            message=f"{text_files_with_counts}/{total_text_files} text files ({coverage:.0%}) have line counts",
            evidence={
                "text_files_with_counts": text_files_with_counts,
                "total_text_files": total_text_files,
                "coverage": round(coverage, 3),
            },
        )

    return CheckResult(
        check_id="CT-5",
        name="Text File Coverage",
        category=CheckCategory.CONTENT_METADATA,
        passed=False,
        score=coverage,
        message=f"Low coverage: {text_files_with_counts}/{total_text_files} text files ({coverage:.0%}) have line counts",
        evidence={
            "text_files_with_counts": text_files_with_counts,
            "total_text_files": total_text_files,
            "coverage": round(coverage, 3),
        },
    )


@register_check("CT-6")
def check_hash_consistency(output: Dict[str, Any]) -> CheckResult:
    """CT-6: Files with same size should be checked for duplicate hashes (sanity check)."""
    files = output.get("files", {})

    # Group files by content hash
    hash_to_files: Dict[str, List[str]] = {}
    for path, file_obj in files.items():
        content_hash = file_obj.get("content_hash")
        if content_hash:
            if content_hash not in hash_to_files:
                hash_to_files[content_hash] = []
            hash_to_files[content_hash].append(path)

    # Find duplicate hashes
    duplicates = {
        h: paths for h, paths in hash_to_files.items()
        if len(paths) > 1
    }

    # This is informational - duplicates are valid (identical files)
    files_with_hash = sum(1 for f in files.values() if f.get("content_hash"))

    return CheckResult(
        check_id="CT-6",
        name="Hash Consistency",
        category=CheckCategory.CONTENT_METADATA,
        passed=True,  # Duplicates are allowed, this is informational
        score=1.0,
        message=f"{files_with_hash} files have hashes, {len(duplicates)} unique hashes have duplicates",
        evidence={
            "files_with_hash": files_with_hash,
            "unique_hashes": len(hash_to_files),
            "duplicate_hash_count": len(duplicates),
            "example_duplicates": dict(list(duplicates.items())[:3]) if duplicates else {},
        },
    )
