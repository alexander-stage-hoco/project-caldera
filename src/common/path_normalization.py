"""Shared path normalization utilities."""
from __future__ import annotations

from pathlib import Path


def _strip_repo_prefix(normalized: str, repo_root: Path | None) -> str:
    if not repo_root:
        return normalized
    root = repo_root.resolve().as_posix().rstrip("/")
    root_trimmed = root.lstrip("/")
    alt_root = None
    if root.startswith("/private/"):
        alt_root = root.replace("/private", "", 1).lstrip("/")
    for prefix in (root, root_trimmed, alt_root):
        if prefix and normalized.startswith(prefix + "/"):
            return normalized[len(prefix) + 1 :]
    return normalized


def _to_posix(raw_path: str) -> str:
    normalized = raw_path.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized.startswith("/"):
        normalized = normalized.lstrip("/")
    return normalized


def normalize_file_path(raw_path: str, repo_root: Path | None) -> str:
    """Normalize file paths to repo-relative POSIX format."""
    if not raw_path:
        return raw_path
    normalized = _to_posix(raw_path)
    normalized = _strip_repo_prefix(normalized, repo_root)
    path_obj = Path(normalized)
    if path_obj.is_absolute():
        try:
            normalized = path_obj.relative_to(repo_root).as_posix() if repo_root else path_obj.as_posix().lstrip("/")
        except ValueError:
            normalized = path_obj.as_posix().lstrip("/")
    return normalized


def normalize_dir_path(raw_path: str, repo_root: Path | None) -> str:
    """Normalize directory paths to repo-relative POSIX format."""
    normalized = normalize_file_path(raw_path, repo_root)
    return normalized or "."


def is_repo_relative_path(raw_path: str) -> bool:
    """Return True if path complies with repo-relative rules."""
    if raw_path is None:
        return False
    if raw_path == "":
        return False
    if raw_path.startswith("/"):
        return False
    if raw_path.startswith("./"):
        return False
    if "\\" in raw_path:
        return False
    if raw_path.startswith("tmp/") or raw_path.startswith("private/"):
        return False
    return True


def validate_paths_consistent(paths: list[str]) -> tuple[bool, list[str]]:
    """Check if all paths in the list are consistently formatted.

    Returns a tuple of (is_consistent, issues) where issues is a list of
    inconsistency descriptions.
    """
    issues: list[str] = []
    if not paths:
        return True, issues

    # Check for mixed absolute/relative paths
    absolute_paths = [p for p in paths if p.startswith("/") or p.startswith("\\") or (len(p) > 1 and p[1] == ":")]
    relative_paths = [p for p in paths if not (p.startswith("/") or p.startswith("\\") or (len(p) > 1 and p[1] == ":"))]

    if absolute_paths and relative_paths:
        issues.append(f"Mixed absolute and relative paths: {len(absolute_paths)} absolute, {len(relative_paths)} relative")

    # Check for mixed path separators
    unix_style = [p for p in paths if "/" in p and "\\" not in p]
    win_style = [p for p in paths if "\\" in p]
    if unix_style and win_style:
        issues.append(f"Mixed path separators: {len(unix_style)} POSIX, {len(win_style)} Windows")

    # Check for case-sensitivity issues (same path with different casing)
    path_lower_map: dict[str, list[str]] = {}
    for p in paths:
        lower = p.lower()
        if lower not in path_lower_map:
            path_lower_map[lower] = []
        path_lower_map[lower].append(p)

    for lower_path, variants in path_lower_map.items():
        unique_variants = set(variants)
        if len(unique_variants) > 1:
            issues.append(f"Case inconsistency: {sorted(unique_variants)}")

    return len(issues) == 0, issues


def detect_path_root_pattern(paths: list[str]) -> str | None:
    """Detect common root pattern in paths (e.g., absolute path prefix).

    Returns the common prefix if detected, None otherwise.
    """
    if not paths:
        return None

    # Filter to non-empty paths
    non_empty = [p for p in paths if p]
    if not non_empty:
        return None

    # Look for common absolute prefix
    absolute_paths = [p for p in non_empty if p.startswith("/")]
    if not absolute_paths:
        return None

    # Find common prefix
    prefix = absolute_paths[0]
    for path in absolute_paths[1:]:
        while prefix and not path.startswith(prefix):
            # Remove last path segment
            if "/" in prefix[:-1]:
                prefix = prefix.rsplit("/", 1)[0] + "/"
            else:
                prefix = ""
                break

    # Only return if prefix is meaningful (more than just "/")
    if prefix and len(prefix) > 1 and prefix.count("/") >= 2:
        return prefix.rstrip("/")

    return None
