"""
Output Writer for Layout Scanner.

Serializes scan results to JSON format matching the defined schema.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .classifier import ClassificationResult, LanguageResult
from .hierarchy_builder import DirectoryMetrics, HierarchyInfo
from .statistics import (
    compute_depth_distribution_stats,
    compute_files_per_directory_stats,
    compute_file_size_stats,
)
from .tree_walker import DirectoryInfo, FileInfo, WalkResult

# Import ecosystem detection from common module
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from common.ecosystem_detector import (
    EcosystemDetectionResult,
    detect_ecosystems,
    get_ecosystem_summary,
)


SCHEMA_VERSION = "1.0.0"
TOOL_VERSION = "1.0.0"


def generate_run_id(repo_name: str) -> str:
    """Generate a unique run ID."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"layout-{timestamp}-{repo_name}"


def format_file_object(
    file_info: FileInfo,
    classification: ClassificationResult,
    language: LanguageResult,
    git_metadata: Any | None = None,
    content_metadata: Any | None = None,
) -> dict[str, Any]:
    """
    Format a file object for JSON output.

    Args:
        file_info: File information from tree walker
        classification: Classification result
        language: Language detection result
        git_metadata: Optional git metadata (GitFileMetadata from git_enricher)
        content_metadata: Optional content metadata (ContentFileMetadata from content_enricher)
    """
    return {
        "id": file_info.id,
        "path": file_info.path,
        "name": file_info.name,
        "extension": file_info.extension,
        "size_bytes": file_info.size_bytes,
        "modified_time": file_info.modified_time,
        "is_symlink": file_info.is_symlink,
        "language": language.language,
        "classification": classification.category,
        "classification_reason": classification.reason,
        "classification_confidence": classification.confidence,
        "parent_directory_id": file_info.parent_directory_id,
        "depth": file_info.depth,
        # Git metadata fields (populated when --git is used)
        "first_commit_date": git_metadata.first_commit_date if git_metadata else None,
        "last_commit_date": git_metadata.last_commit_date if git_metadata else None,
        "commit_count": git_metadata.commit_count if git_metadata else None,
        "author_count": git_metadata.author_count if git_metadata else None,
        # Content metadata fields (populated when --content is used)
        "content_hash": content_metadata.content_hash if content_metadata else None,
        "is_binary": content_metadata.is_binary if content_metadata else None,
        "line_count": content_metadata.line_count if content_metadata else None,
    }


def format_directory_object(
    dir_info: DirectoryInfo,
    metrics: DirectoryMetrics,
    classification: str,
    classification_reason: str,
) -> dict[str, Any]:
    """Format a directory object for JSON output."""
    return {
        "id": dir_info.id,
        "path": dir_info.path,
        "name": dir_info.name,
        "modified_time": dir_info.modified_time,
        "is_symlink": dir_info.is_symlink,
        "classification": classification,
        "classification_reason": classification_reason,
        "parent_directory_id": dir_info.parent_directory_id,
        "depth": dir_info.depth,
        "child_directory_ids": dir_info.child_directory_ids,
        "child_file_ids": dir_info.child_file_ids,
        "direct_file_count": metrics.direct_file_count,
        "direct_directory_count": metrics.direct_directory_count,
        "recursive_file_count": metrics.recursive_file_count,
        "recursive_directory_count": metrics.recursive_directory_count,
        "direct_size_bytes": metrics.direct_size_bytes,
        "recursive_size_bytes": metrics.recursive_size_bytes,
        "classification_distribution": metrics.classification_distribution,
        "language_distribution": metrics.language_distribution,
    }


def format_hierarchy_section(hierarchy: HierarchyInfo) -> dict[str, Any]:
    """Format the hierarchy section for JSON output."""
    return {
        "root_id": hierarchy.root_id,
        "max_depth": hierarchy.max_depth,
        "total_files": hierarchy.total_files,
        "total_directories": hierarchy.total_directories,
        "total_size_bytes": hierarchy.total_size_bytes,
        "children": hierarchy.children,
        "parents": hierarchy.parents,
        "depth_distribution": {
            str(k): v for k, v in hierarchy.depth_distribution.items()
        },
    }


def format_statistics(
    walk_result: WalkResult,
    file_classifications: dict[str, str],
    file_languages: dict[str, str],
    scan_duration_ms: int,
    hierarchy: HierarchyInfo | None = None,
    dir_metrics: dict[str, DirectoryMetrics] | None = None,
    ecosystem_result: EcosystemDetectionResult | None = None,
) -> dict[str, Any]:
    """Format the statistics section for JSON output.

    Args:
        walk_result: Result from tree walking.
        file_classifications: Classification for each file path.
        file_languages: Language for each file path.
        scan_duration_ms: Scan duration in milliseconds.
        hierarchy: Optional hierarchy info for depth statistics.
        dir_metrics: Optional directory metrics for files-per-directory stats.
        ecosystem_result: Optional ecosystem detection result.

    Returns:
        Statistics dictionary for JSON output.
    """
    # Count by classification
    by_classification: dict[str, int] = {}
    for path, classification in file_classifications.items():
        by_classification[classification] = by_classification.get(classification, 0) + 1

    # Count by language (include "unknown" for consistency with total count)
    by_language: dict[str, int] = {}
    for path, language in file_languages.items():
        by_language[language] = by_language.get(language, 0) + 1

    total_files = len(walk_result.files)
    files_per_second = (
        round(total_files / (scan_duration_ms / 1000), 1)
        if scan_duration_ms > 0
        else 0
    )

    stats = {
        "total_files": total_files,
        "total_directories": len(walk_result.directories),
        "total_size_bytes": walk_result.total_size_bytes,
        "max_depth": walk_result.max_depth,
        "scan_duration_ms": scan_duration_ms,
        "files_per_second": files_per_second,
        "by_classification": by_classification,
        "by_language": by_language,
    }

    # Add skipped count if any paths were skipped
    if walk_result.skipped_paths:
        stats["skipped_count"] = len(walk_result.skipped_paths)

    # Add directory depth distribution statistics
    if hierarchy and hierarchy.depth_distribution:
        depth_stats = compute_depth_distribution_stats(hierarchy.depth_distribution)
        stats["directory_depth_stats"] = depth_stats.to_dict()

    # Add files per directory distribution statistics
    if dir_metrics:
        dir_file_counts = [
            dm.direct_file_count for dm in dir_metrics.values()
        ]
        if dir_file_counts:
            files_per_dir_stats = compute_files_per_directory_stats(dir_file_counts)
            stats["files_per_directory_stats"] = files_per_dir_stats.to_dict()

    # Add file size distribution statistics
    file_sizes = [
        f.size_bytes for f in walk_result.files.values()
        if f is not None and hasattr(f, "size_bytes")
    ]
    if file_sizes:
        size_stats = compute_file_size_stats(file_sizes)
        stats["size_per_file_stats"] = size_stats.to_dict()

    # Add ecosystem detection statistics
    if ecosystem_result:
        stats["detected_ecosystems"] = get_ecosystem_summary(ecosystem_result)
        stats["dependency_files"] = {
            "total": len(ecosystem_result.dependency_files),
            "by_type": {
                "manifest": sum(
                    1 for df in ecosystem_result.dependency_files
                    if df.file_type == "manifest"
                ),
                "lockfile": sum(
                    1 for df in ecosystem_result.dependency_files
                    if df.file_type == "lockfile"
                ),
            },
        }
        if ecosystem_result.incomplete_ecosystems:
            stats["incomplete_ecosystems"] = ecosystem_result.incomplete_ecosystems

    return stats


def build_output(
    walk_result: WalkResult,
    file_classifications: dict[str, ClassificationResult],
    file_languages: dict[str, LanguageResult],
    dir_classifications: dict[str, tuple[str, str]],  # path -> (category, reason)
    dir_metrics: dict[str, DirectoryMetrics],
    hierarchy: HierarchyInfo,
    repo_name: str,
    repo_path: str,
    scan_duration_ms: int,
    git_metadata: dict[str, Any] | None = None,
    content_metadata: dict[str, Any] | None = None,
    ecosystem_result: EcosystemDetectionResult | None = None,
) -> dict[str, Any]:
    """
    Build the complete output structure.

    Args:
        walk_result: Result from tree walking
        file_classifications: Classification results for each file
        file_languages: Language detection results for each file
        dir_classifications: Classification for each directory
        dir_metrics: Metrics for each directory
        hierarchy: Hierarchy information
        repo_name: Name of the repository
        repo_path: Absolute path to the repository
        scan_duration_ms: Scan duration in milliseconds
        git_metadata: Optional dict mapping file paths to GitFileMetadata
        content_metadata: Optional dict mapping file paths to ContentFileMetadata
        ecosystem_result: Optional ecosystem detection result

    Returns:
        Complete output dictionary ready for JSON serialization
    """
    # Build files section
    files: dict[str, Any] = {}
    for path, file_info in walk_result.files.items():
        classification = file_classifications.get(
            path,
            ClassificationResult(category="other", confidence=0.0, reason="unknown")
        )
        language = file_languages.get(
            path,
            LanguageResult(language="unknown", confidence=0.0)
        )
        file_git = git_metadata.get(path) if git_metadata else None
        file_content = content_metadata.get(path) if content_metadata else None
        files[path] = format_file_object(
            file_info, classification, language, file_git, file_content
        )

    # Build directories section
    directories: dict[str, Any] = {}
    for path, dir_info in walk_result.directories.items():
        metrics = dir_metrics.get(path, DirectoryMetrics())
        classification, reason = dir_classifications.get(path, ("other", "unknown"))
        directories[path] = format_directory_object(
            dir_info, metrics, classification, reason
        )

    # Build classification and language maps for statistics
    file_class_map = {p: c.category for p, c in file_classifications.items()}
    file_lang_map = {p: l.language for p, l in file_languages.items()}

    # Determine passes completed
    passes = ["filesystem"]
    if git_metadata is not None:
        passes.append("git")
    if content_metadata is not None:
        passes.append("content")

    return {
        "schema_version": SCHEMA_VERSION,
        "tool": "layout-scanner",
        "tool_version": TOOL_VERSION,
        "run_id": generate_run_id(repo_name),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "repository": repo_name,
        "repository_path": repo_path,
        "passes_completed": passes,
        "statistics": format_statistics(
            walk_result,
            file_class_map,
            file_lang_map,
            scan_duration_ms,
            hierarchy=hierarchy,
            dir_metrics=dir_metrics,
            ecosystem_result=ecosystem_result,
        ),
        "files": files,
        "directories": directories,
        "hierarchy": format_hierarchy_section(hierarchy),
    }


def write_output(
    output: dict[str, Any],
    output_path: Path,
    indent: int = 2,
) -> None:
    """
    Write output to a JSON file.

    Args:
        output: Output dictionary
        output_path: Path to write to
        indent: JSON indentation level
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=indent, ensure_ascii=False)


def output_to_json(output: dict[str, Any], indent: int = 2) -> str:
    """Convert output to JSON string."""
    return json.dumps(output, indent=indent, ensure_ascii=False)
