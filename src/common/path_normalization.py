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
