"""
Hierarchy Builder for Layout Scanner.

Computes tree relationships, recursive counts, and aggregated metrics
for directories based on their contents.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .tree_walker import DirectoryInfo, FileInfo, WalkResult


@dataclass
class DirectoryMetrics:
    """Aggregated metrics for a directory."""
    direct_file_count: int = 0
    direct_directory_count: int = 0
    recursive_file_count: int = 0
    recursive_directory_count: int = 0
    direct_size_bytes: int = 0
    recursive_size_bytes: int = 0
    classification_distribution: Dict[str, int] = field(default_factory=dict)
    language_distribution: Dict[str, int] = field(default_factory=dict)


@dataclass
class HierarchyInfo:
    """Complete hierarchy information for the repository."""
    root_id: str
    max_depth: int
    total_files: int
    total_directories: int
    total_size_bytes: int
    children: Dict[str, List[str]]  # parent_id -> list of child IDs
    parents: Dict[str, str]  # child_id -> parent_id
    depth_distribution: Dict[int, int]  # depth -> count


def build_hierarchy(
    walk_result: WalkResult,
    file_classifications: Dict[str, str],  # path -> classification
    file_languages: Dict[str, str],  # path -> language
) -> tuple[HierarchyInfo, Dict[str, DirectoryMetrics]]:
    """
    Build complete hierarchy information from walk result.

    Args:
        walk_result: Result from tree_walker
        file_classifications: Classification for each file path
        file_languages: Language for each file path

    Returns:
        Tuple of (HierarchyInfo, dict of path -> DirectoryMetrics)
    """
    # Build children and parents maps
    children: Dict[str, List[str]] = defaultdict(list)
    parents: Dict[str, str] = {}
    depth_distribution: Dict[int, int] = defaultdict(int)

    root_id = None

    # Process directories
    for path, dir_info in walk_result.directories.items():
        if dir_info.parent_directory_id is None:
            root_id = dir_info.id
        else:
            children[dir_info.parent_directory_id].append(dir_info.id)
            parents[dir_info.id] = dir_info.parent_directory_id

        depth_distribution[dir_info.depth] += 1

    # Process files
    for path, file_info in walk_result.files.items():
        children[file_info.parent_directory_id].append(file_info.id)
        parents[file_info.id] = file_info.parent_directory_id
        depth_distribution[file_info.depth] += 1

    # Compute directory metrics
    dir_metrics = compute_directory_metrics(
        walk_result, file_classifications, file_languages
    )

    hierarchy = HierarchyInfo(
        root_id=root_id or "d-000000000000",
        max_depth=walk_result.max_depth,
        total_files=len(walk_result.files),
        total_directories=len(walk_result.directories),
        total_size_bytes=walk_result.total_size_bytes,
        children=dict(children),
        parents=parents,
        depth_distribution=dict(depth_distribution),
    )

    return hierarchy, dir_metrics


def compute_directory_metrics(
    walk_result: WalkResult,
    file_classifications: Dict[str, str],
    file_languages: Dict[str, str],
) -> Dict[str, DirectoryMetrics]:
    """
    Compute direct and recursive metrics for all directories.

    Uses bottom-up aggregation for efficiency.

    Args:
        walk_result: Result from tree_walker
        file_classifications: Classification for each file path
        file_languages: Language for each file path

    Returns:
        Dict mapping directory path to its metrics
    """
    metrics: Dict[str, DirectoryMetrics] = {}

    # Initialize metrics for all directories
    for path in walk_result.directories:
        metrics[path] = DirectoryMetrics()

    # First pass: compute direct metrics
    for path, file_info in walk_result.files.items():
        # Find parent directory path
        parent_path = "/".join(path.split("/")[:-1]) if "/" in path else ""

        if parent_path in metrics:
            m = metrics[parent_path]
            m.direct_file_count += 1
            m.direct_size_bytes += file_info.size_bytes

            # Classification distribution
            classification = file_classifications.get(path, "other")
            m.classification_distribution[classification] = (
                m.classification_distribution.get(classification, 0) + 1
            )

            # Language distribution
            language = file_languages.get(path, "unknown")
            if language != "unknown":
                m.language_distribution[language] = (
                    m.language_distribution.get(language, 0) + 1
                )

    # Count direct subdirectories
    for path, dir_info in walk_result.directories.items():
        if path:  # Skip root
            parent_path = "/".join(path.split("/")[:-1]) if "/" in path else ""
            if parent_path in metrics:
                metrics[parent_path].direct_directory_count += 1

    # Second pass: compute recursive metrics (bottom-up)
    # Sort directories by depth (deepest first), then by path length (longer first)
    # This ensures children are always processed before their parents
    sorted_dirs = sorted(
        walk_result.directories.items(),
        key=lambda x: (x[1].depth, len(x[0])),
        reverse=True
    )

    for path, dir_info in sorted_dirs:
        m = metrics[path]

        # Start with direct counts
        m.recursive_file_count = m.direct_file_count
        m.recursive_directory_count = m.direct_directory_count
        m.recursive_size_bytes = m.direct_size_bytes

        # Create copies for recursive distributions
        recursive_classifications = dict(m.classification_distribution)
        recursive_languages = dict(m.language_distribution)

        # Add metrics from child directories
        for child_path, child_dir in walk_result.directories.items():
            if not child_path:
                continue
            # For root (empty path), match any direct child; otherwise use prefix match
            is_child = (path == "" and "/" not in child_path) or \
                       (path != "" and child_path.startswith(path + "/"))
            if is_child:
                # Check if immediate child
                remaining = child_path[len(path) + 1:] if path else child_path
                if "/" not in remaining:
                    # This is an immediate child directory
                    child_metrics = metrics.get(child_path)
                    if child_metrics:
                        m.recursive_file_count += child_metrics.recursive_file_count
                        m.recursive_directory_count += child_metrics.recursive_directory_count
                        m.recursive_size_bytes += child_metrics.recursive_size_bytes

                        # Merge classification distributions
                        for cat, count in child_metrics.classification_distribution.items():
                            recursive_classifications[cat] = (
                                recursive_classifications.get(cat, 0) + count
                            )

                        # Merge language distributions
                        for lang, count in child_metrics.language_distribution.items():
                            recursive_languages[lang] = (
                                recursive_languages.get(lang, 0) + count
                            )

        # Update with recursive distributions
        m.classification_distribution = recursive_classifications
        m.language_distribution = recursive_languages

    return metrics


def get_path_ancestors(path: str) -> List[str]:
    """Get all ancestor paths for a given path."""
    if not path:
        return []

    parts = path.split("/")
    ancestors = []

    for i in range(len(parts)):
        ancestor = "/".join(parts[:i])
        if ancestor or i == 0:
            ancestors.append(ancestor if ancestor else "")

    return ancestors


def get_files_in_directory(
    walk_result: WalkResult,
    dir_path: str,
    recursive: bool = False
) -> List[FileInfo]:
    """
    Get all files in a directory.

    Args:
        walk_result: Result from tree_walker
        dir_path: Directory path
        recursive: If True, include files in subdirectories

    Returns:
        List of FileInfo objects
    """
    files = []

    for path, file_info in walk_result.files.items():
        if recursive:
            if path.startswith(dir_path + "/") or (dir_path == "" and "/" not in path):
                files.append(file_info)
            elif dir_path == "" and "/" in path:
                files.append(file_info)
        else:
            parent = "/".join(path.split("/")[:-1]) if "/" in path else ""
            if parent == dir_path:
                files.append(file_info)

    return files


def get_subdirectories(
    walk_result: WalkResult,
    dir_path: str,
    recursive: bool = False
) -> List[DirectoryInfo]:
    """
    Get subdirectories of a directory.

    Args:
        walk_result: Result from tree_walker
        dir_path: Directory path
        recursive: If True, include all descendant directories

    Returns:
        List of DirectoryInfo objects
    """
    subdirs = []

    for path, dir_info in walk_result.directories.items():
        if not path:
            continue

        if recursive:
            if path.startswith(dir_path + "/") or (dir_path == "" and path):
                subdirs.append(dir_info)
        else:
            parent = "/".join(path.split("/")[:-1]) if "/" in path else ""
            if parent == dir_path:
                subdirs.append(dir_info)

    return subdirs
