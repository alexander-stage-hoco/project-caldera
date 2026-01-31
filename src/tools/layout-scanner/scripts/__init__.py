"""
Layout Scanner - Fast filesystem-based repository layout scanner.

A tool for creating canonical file and directory registries with
sophisticated file classification.
"""

from .classifier import (
    ClassificationResult,
    LanguageResult,
    classify_directory,
    classify_file,
    detect_language,
)
from .config_loader import ScannerConfig, load_config
from .hierarchy_builder import DirectoryMetrics, HierarchyInfo, build_hierarchy
from .id_generator import generate_id, generate_root_id
from .ignore_filter import IgnoreFilter, load_ignore_filter
from .layout_scanner import main, scan_repository
from .output_writer import build_output, write_output
from .statistics import (
    DistributionStats,
    compute_stats,
    compute_depth_distribution_stats,
    compute_files_per_directory_stats,
    compute_file_size_stats,
)
from .tree_walker import DirectoryInfo, FileInfo, WalkResult, walk_repository

__version__ = "1.0.0"
__all__ = [
    # Main entry points
    "main",
    "scan_repository",
    # Core types
    "FileInfo",
    "DirectoryInfo",
    "WalkResult",
    "ClassificationResult",
    "LanguageResult",
    "DirectoryMetrics",
    "HierarchyInfo",
    "ScannerConfig",
    "IgnoreFilter",
    "DistributionStats",
    # Functions
    "walk_repository",
    "classify_file",
    "classify_directory",
    "detect_language",
    "build_hierarchy",
    "build_output",
    "write_output",
    "load_config",
    "load_ignore_filter",
    "generate_id",
    "generate_root_id",
    # Statistics functions
    "compute_stats",
    "compute_depth_distribution_stats",
    "compute_files_per_directory_stats",
    "compute_file_size_stats",
]
