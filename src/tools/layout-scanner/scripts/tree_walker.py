"""
Tree Walker for Layout Scanner.

Fast filesystem traversal using os.scandir for efficient directory walking.
Collects file and directory metadata without reading file contents.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Iterator

from .id_generator import generate_id, generate_root_id
from .ignore_filter import IgnoreFilter, load_ignore_filter


@dataclass
class FileInfo:
    """Information about a file collected during traversal."""
    id: str
    path: str  # Relative path from repo root
    name: str
    extension: str
    size_bytes: int
    modified_time: str  # ISO 8601 format
    is_symlink: bool
    parent_directory_id: str
    depth: int


@dataclass
class DirectoryInfo:
    """Information about a directory collected during traversal."""
    id: str
    path: str  # Relative path from repo root (empty string for root)
    name: str
    modified_time: str  # ISO 8601 format
    is_symlink: bool
    parent_directory_id: str | None  # None for root
    depth: int
    child_file_ids: list[str] = field(default_factory=list)
    child_directory_ids: list[str] = field(default_factory=list)


@dataclass
class WalkResult:
    """Result of walking a repository."""
    files: dict[str, FileInfo]  # path -> FileInfo
    directories: dict[str, DirectoryInfo]  # path -> DirectoryInfo
    root_path: str
    max_depth: int = 0
    total_size_bytes: int = 0
    skipped_paths: list[str] = field(default_factory=list)  # Paths that couldn't be accessed
    skipped_reasons: dict[str, str] = field(default_factory=dict)  # path -> reason


def get_extension(filename: str) -> str:
    """Extract file extension including the dot."""
    if "." not in filename:
        return ""
    # Handle cases like .gitignore (hidden files with no real extension)
    if filename.startswith(".") and filename.count(".") == 1:
        return ""
    return "." + filename.rsplit(".", 1)[-1]


def format_mtime(stat_result: os.stat_result) -> str:
    """Format modification time as ISO 8601."""
    dt = datetime.fromtimestamp(stat_result.st_mtime, tz=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def walk_repository(
    repo_path: Path,
    ignore_filter: IgnoreFilter | None = None,
    additional_ignores: list[str] | None = None,
    respect_gitignore: bool = True
) -> WalkResult:
    """
    Walk a repository and collect file/directory information.

    Uses os.scandir for efficient traversal. Does not read file contents.

    Args:
        repo_path: Path to repository root
        ignore_filter: Pre-configured ignore filter (optional)
        additional_ignores: Additional patterns to ignore
        respect_gitignore: Whether to respect .gitignore

    Returns:
        WalkResult containing all files and directories
    """
    repo_path = Path(repo_path).resolve()

    if not repo_path.is_dir():
        raise ValueError(f"Repository path does not exist or is not a directory: {repo_path}")

    # Load or use provided ignore filter
    if ignore_filter is None:
        ignore_filter = load_ignore_filter(
            repo_path,
            additional_patterns=additional_ignores,
            respect_gitignore=respect_gitignore
        )
    elif additional_ignores:
        for pattern in additional_ignores:
            ignore_filter.add_pattern(pattern)

    files: dict[str, FileInfo] = {}
    directories: dict[str, DirectoryInfo] = {}
    max_depth = 0
    total_size = 0
    skipped_paths: list[str] = []
    skipped_reasons: dict[str, str] = {}

    # Create root directory entry
    root_stat = repo_path.stat()
    root_id = generate_root_id()
    root_info = DirectoryInfo(
        id=root_id,
        path="",
        name=repo_path.name,
        modified_time=format_mtime(root_stat),
        is_symlink=repo_path.is_symlink(),
        parent_directory_id=None,
        depth=0
    )
    directories[""] = root_info

    # Walk the tree using iterative approach with stack
    # Stack contains: (dir_path, relative_path, depth, parent_id)
    stack: list[tuple[Path, str, int, str]] = [(repo_path, "", 0, root_id)]

    while stack:
        current_path, rel_path, depth, parent_id = stack.pop()

        try:
            entries = list(os.scandir(current_path))
        except PermissionError:
            skipped_paths.append(rel_path or ".")
            skipped_reasons[rel_path or "."] = "permission denied"
            continue
        except OSError as e:
            skipped_paths.append(rel_path or ".")
            skipped_reasons[rel_path or "."] = str(e)
            continue

        # Filter entries
        entries = ignore_filter.filter_entries(entries, rel_path)

        # Sort entries for deterministic ordering
        entries.sort(key=lambda e: e.name)

        for entry in entries:
            entry_rel_path = f"{rel_path}/{entry.name}" if rel_path else entry.name
            is_symlink = entry.is_symlink()

            try:
                stat = entry.stat(follow_symlinks=False)
                mtime = format_mtime(stat)
            except OSError:
                continue

            if entry.is_dir(follow_symlinks=False):
                # Directory entry
                dir_id = generate_id(entry_rel_path, "directory")
                # Use path-based depth calculation (count of path separators)
                dir_depth = entry_rel_path.count('/') if entry_rel_path else 0
                dir_info = DirectoryInfo(
                    id=dir_id,
                    path=entry_rel_path,
                    name=entry.name,
                    modified_time=mtime,
                    is_symlink=is_symlink,
                    parent_directory_id=parent_id,
                    depth=dir_depth
                )
                directories[entry_rel_path] = dir_info

                # Update parent's child list
                if rel_path in directories:
                    directories[rel_path].child_directory_ids.append(dir_id)

                # Add to stack for traversal (skip symlinks to avoid cycles)
                if not is_symlink:
                    stack.append((entry.path, entry_rel_path, depth + 1, dir_id))

                max_depth = max(max_depth, dir_depth)

            elif entry.is_file(follow_symlinks=False):
                # File entry
                file_id = generate_id(entry_rel_path, "file")
                size = stat.st_size
                total_size += size

                # Use path-based depth calculation (count of path separators)
                file_depth = entry_rel_path.count('/')
                file_info = FileInfo(
                    id=file_id,
                    path=entry_rel_path,
                    name=entry.name,
                    extension=get_extension(entry.name),
                    size_bytes=size,
                    modified_time=mtime,
                    is_symlink=is_symlink,
                    parent_directory_id=parent_id,
                    depth=file_depth
                )
                files[entry_rel_path] = file_info

                # Update parent's child list
                if rel_path in directories:
                    directories[rel_path].child_file_ids.append(file_id)

                max_depth = max(max_depth, file_depth)

    return WalkResult(
        files=files,
        directories=directories,
        root_path=str(repo_path),
        max_depth=max_depth,
        total_size_bytes=total_size,
        skipped_paths=skipped_paths,
        skipped_reasons=skipped_reasons
    )


def iter_files(walk_result: WalkResult) -> Iterator[FileInfo]:
    """Iterate over all files in the walk result."""
    return iter(walk_result.files.values())


def iter_directories(walk_result: WalkResult) -> Iterator[DirectoryInfo]:
    """Iterate over all directories in the walk result."""
    return iter(walk_result.directories.values())
