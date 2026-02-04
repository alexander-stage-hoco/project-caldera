"""Unit tests for directory rollup computation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))

from license_analyzer import (
    FileSummary,
    DirectoryStats,
    DirectoryEntry,
    compute_directory_rollups,
    _build_directory_stats,
)


class TestBuildDirectoryStats:
    """Tests for _build_directory_stats helper function."""

    def test_empty_files_list(self):
        """Empty files list should return default DirectoryStats."""
        stats = _build_directory_stats([])
        assert stats.file_count == 0
        assert stats.files_with_licenses == 0
        assert stats.license_counts == {}
        assert stats.category_counts == {}
        assert stats.has_copyleft is False
        assert stats.worst_risk == "unknown"

    def test_single_permissive_file(self):
        """Single file with permissive license should compute correctly."""
        files = [
            FileSummary(
                file_path="LICENSE",
                licenses=["MIT"],
                category="permissive",
                has_spdx_header=False,
            )
        ]
        stats = _build_directory_stats(files)

        assert stats.file_count == 1
        assert stats.files_with_licenses == 1
        assert stats.license_counts == {"MIT": 1}
        assert stats.category_counts == {"permissive": 1}
        assert stats.has_permissive is True
        assert stats.has_copyleft is False
        assert stats.worst_risk == "low"

    def test_multiple_files_same_license(self):
        """Multiple files with same license should aggregate counts."""
        files = [
            FileSummary(file_path="LICENSE", licenses=["MIT"], category="permissive", has_spdx_header=False),
            FileSummary(file_path="src/main.py", licenses=["MIT"], category="permissive", has_spdx_header=True),
            FileSummary(file_path="src/lib.py", licenses=["MIT"], category="permissive", has_spdx_header=True),
        ]
        stats = _build_directory_stats(files)

        assert stats.file_count == 3
        assert stats.files_with_licenses == 3
        assert stats.license_counts == {"MIT": 3}
        assert stats.category_counts == {"permissive": 3}

    def test_multiple_licenses_per_file(self):
        """File with multiple licenses should count each license."""
        files = [
            FileSummary(
                file_path="LICENSE",
                licenses=["MIT", "Apache-2.0"],
                category="permissive",
                has_spdx_header=False,
            )
        ]
        stats = _build_directory_stats(files)

        assert stats.license_counts == {"MIT": 1, "Apache-2.0": 1}
        assert stats.file_count == 1
        assert stats.files_with_licenses == 1

    def test_copyleft_detection(self):
        """Copyleft category should set has_copyleft and worst_risk."""
        files = [
            FileSummary(file_path="COPYING", licenses=["GPL-3.0-only"], category="copyleft", has_spdx_header=False),
        ]
        stats = _build_directory_stats(files)

        assert stats.has_copyleft is True
        assert stats.has_permissive is False
        assert stats.worst_risk == "critical"

    def test_weak_copyleft_detection(self):
        """Weak-copyleft category should set has_weak_copyleft and worst_risk."""
        files = [
            FileSummary(file_path="LICENSE", licenses=["LGPL-3.0-only"], category="weak-copyleft", has_spdx_header=False),
        ]
        stats = _build_directory_stats(files)

        assert stats.has_weak_copyleft is True
        assert stats.has_copyleft is False
        assert stats.worst_risk == "medium"

    def test_mixed_categories_worst_risk(self):
        """Mixed categories should return worst (copyleft > weak-copyleft > permissive)."""
        files = [
            FileSummary(file_path="MIT-LICENSE", licenses=["MIT"], category="permissive", has_spdx_header=False),
            FileSummary(file_path="GPL-LICENSE", licenses=["GPL-3.0-only"], category="copyleft", has_spdx_header=False),
        ]
        stats = _build_directory_stats(files)

        assert stats.has_permissive is True
        assert stats.has_copyleft is True
        assert stats.worst_risk == "critical"

    def test_weak_copyleft_vs_permissive_risk(self):
        """Weak-copyleft should take precedence over permissive."""
        files = [
            FileSummary(file_path="MIT-LICENSE", licenses=["MIT"], category="permissive", has_spdx_header=False),
            FileSummary(file_path="LGPL-LICENSE", licenses=["LGPL-2.1-only"], category="weak-copyleft", has_spdx_header=False),
        ]
        stats = _build_directory_stats(files)

        assert stats.has_permissive is True
        assert stats.has_weak_copyleft is True
        assert stats.worst_risk == "medium"

    def test_file_without_licenses_not_counted(self):
        """File with empty licenses list should not count in files_with_licenses."""
        files = [
            FileSummary(file_path="README.md", licenses=[], category="unknown", has_spdx_header=False),
            FileSummary(file_path="LICENSE", licenses=["MIT"], category="permissive", has_spdx_header=False),
        ]
        stats = _build_directory_stats(files)

        assert stats.file_count == 2
        assert stats.files_with_licenses == 1

    def test_unknown_category_worst_risk(self):
        """Only unknown category should return 'unknown' worst_risk."""
        files = [
            FileSummary(file_path="PROPRIETARY", licenses=["Custom-1.0"], category="unknown", has_spdx_header=False),
        ]
        stats = _build_directory_stats(files)

        # Unknown category doesn't set any has_* flags, so worst_risk stays "unknown"
        assert stats.has_permissive is False
        assert stats.has_copyleft is False
        assert stats.has_weak_copyleft is False
        assert stats.worst_risk == "unknown"


class TestComputeDirectoryRollups:
    """Tests for compute_directory_rollups function."""

    def test_empty_files_dict(self):
        """Empty files dict should return empty directories list."""
        directories = compute_directory_rollups({})
        assert directories == []

    def test_single_root_file(self):
        """Single file in root should create root directory entry."""
        files = {
            "LICENSE": FileSummary(
                file_path="LICENSE",
                licenses=["MIT"],
                category="permissive",
                has_spdx_header=False,
            )
        }
        directories = compute_directory_rollups(files)

        assert len(directories) == 1
        root_entry = directories[0]
        assert root_entry.path == "/"
        assert root_entry.direct.file_count == 1
        assert root_entry.recursive.file_count == 1
        assert root_entry.direct.license_counts == {"MIT": 1}

    def test_nested_directory_structure(self):
        """Nested directories should compute direct and recursive stats separately."""
        files = {
            "LICENSE": FileSummary(file_path="LICENSE", licenses=["MIT"], category="permissive", has_spdx_header=False),
            "src/main.py": FileSummary(file_path="src/main.py", licenses=["MIT"], category="permissive", has_spdx_header=True),
            "src/lib/util.py": FileSummary(file_path="src/lib/util.py", licenses=["MIT"], category="permissive", has_spdx_header=True),
        }
        directories = compute_directory_rollups(files)

        # Should have /, src, src/lib directories
        dir_paths = {d.path for d in directories}
        assert "/" in dir_paths
        assert "src" in dir_paths
        assert "src/lib" in dir_paths

    def test_direct_vs_recursive_counts(self):
        """Direct stats should only count immediate children, recursive should count all descendants."""
        files = {
            "LICENSE": FileSummary(file_path="LICENSE", licenses=["MIT"], category="permissive", has_spdx_header=False),
            "src/main.py": FileSummary(file_path="src/main.py", licenses=["Apache-2.0"], category="permissive", has_spdx_header=True),
        }
        directories = compute_directory_rollups(files)

        # Find root entry
        root_entry = next(d for d in directories if d.path == "/")

        # Root direct should only have LICENSE
        assert root_entry.direct.file_count == 1
        assert root_entry.direct.license_counts == {"MIT": 1}

        # Root recursive should have both files
        assert root_entry.recursive.file_count == 2
        assert "MIT" in root_entry.recursive.license_counts
        assert "Apache-2.0" in root_entry.recursive.license_counts

    def test_deep_nesting(self):
        """Deeply nested files should propagate to all ancestor directories."""
        files = {
            "a/b/c/d/deep.py": FileSummary(
                file_path="a/b/c/d/deep.py",
                licenses=["GPL-3.0-only"],
                category="copyleft",
                has_spdx_header=True,
            )
        }
        directories = compute_directory_rollups(files)

        dir_paths = {d.path for d in directories}
        assert "a" in dir_paths
        assert "a/b" in dir_paths
        assert "a/b/c" in dir_paths
        assert "a/b/c/d" in dir_paths

        # All ancestor directories should have copyleft in recursive stats
        for d in directories:
            if d.path in ["a", "a/b", "a/b/c", "a/b/c/d"]:
                assert d.recursive.has_copyleft is True
                assert d.recursive.worst_risk == "critical"

    def test_sibling_directories(self):
        """Sibling directories should not affect each other's direct stats."""
        files = {
            "frontend/app.js": FileSummary(file_path="frontend/app.js", licenses=["MIT"], category="permissive", has_spdx_header=True),
            "backend/server.py": FileSummary(file_path="backend/server.py", licenses=["GPL-3.0-only"], category="copyleft", has_spdx_header=True),
        }
        directories = compute_directory_rollups(files)

        frontend = next(d for d in directories if d.path == "frontend")
        backend = next(d for d in directories if d.path == "backend")

        # frontend should only have MIT
        assert frontend.direct.license_counts == {"MIT": 1}
        assert frontend.direct.has_copyleft is False

        # backend should only have GPL
        assert backend.direct.license_counts == {"GPL-3.0-only": 1}
        assert backend.direct.has_copyleft is True

        # Root recursive should have both
        root = next(d for d in directories if d.path == "/")
        assert root.recursive.has_permissive is True
        assert root.recursive.has_copyleft is True

    def test_directories_sorted_by_path(self):
        """Directory entries should be sorted by path."""
        files = {
            "z/file.py": FileSummary(file_path="z/file.py", licenses=["MIT"], category="permissive", has_spdx_header=False),
            "a/file.py": FileSummary(file_path="a/file.py", licenses=["MIT"], category="permissive", has_spdx_header=False),
            "m/file.py": FileSummary(file_path="m/file.py", licenses=["MIT"], category="permissive", has_spdx_header=False),
        }
        directories = compute_directory_rollups(files)

        paths = [d.path for d in directories]
        assert paths == sorted(paths)

    def test_mixed_licenses_recursive_aggregation(self):
        """Recursive stats should aggregate all licenses from subtree."""
        files = {
            "LICENSE": FileSummary(file_path="LICENSE", licenses=["MIT"], category="permissive", has_spdx_header=False),
            "src/main.py": FileSummary(file_path="src/main.py", licenses=["Apache-2.0"], category="permissive", has_spdx_header=True),
            "src/vendor/lib.py": FileSummary(file_path="src/vendor/lib.py", licenses=["LGPL-3.0-only"], category="weak-copyleft", has_spdx_header=True),
        }
        directories = compute_directory_rollups(files)

        root = next(d for d in directories if d.path == "/")
        src = next(d for d in directories if d.path == "src")

        # Root recursive should have all licenses
        assert set(root.recursive.license_counts.keys()) == {"MIT", "Apache-2.0", "LGPL-3.0-only"}
        assert root.recursive.has_permissive is True
        assert root.recursive.has_weak_copyleft is True
        assert root.recursive.worst_risk == "medium"

        # src recursive should have Apache-2.0 and LGPL
        assert "Apache-2.0" in src.recursive.license_counts
        assert "LGPL-3.0-only" in src.recursive.license_counts
        # MIT is in root, not in src subtree
        assert "MIT" not in src.recursive.license_counts


class TestDirectoryEntryDataclass:
    """Tests for DirectoryEntry dataclass."""

    def test_directory_entry_creation(self):
        """DirectoryEntry should store path and both stats."""
        direct = DirectoryStats(file_count=2, worst_risk="low")
        recursive = DirectoryStats(file_count=5, worst_risk="medium")
        entry = DirectoryEntry(path="src", direct=direct, recursive=recursive)

        assert entry.path == "src"
        assert entry.direct.file_count == 2
        assert entry.recursive.file_count == 5

    def test_directory_entry_with_empty_stats(self):
        """DirectoryEntry can have empty stats for directories with no direct files."""
        entry = DirectoryEntry(
            path="empty",
            direct=DirectoryStats(),
            recursive=DirectoryStats(file_count=3),
        )

        assert entry.direct.file_count == 0
        assert entry.recursive.file_count == 3


class TestEdgeCases:
    """Edge case tests for directory rollup computation."""

    def test_file_at_root_level(self):
        """File with no directory component should use root."""
        files = {
            "package.json": FileSummary(
                file_path="package.json",
                licenses=["MIT"],
                category="permissive",
                has_spdx_header=False,
            )
        }
        directories = compute_directory_rollups(files)

        # Should only have root directory
        assert len(directories) == 1
        assert directories[0].path == "/"

    def test_multiple_files_same_directory(self):
        """Multiple files in same directory should be counted together."""
        files = {
            "src/a.py": FileSummary(file_path="src/a.py", licenses=["MIT"], category="permissive", has_spdx_header=True),
            "src/b.py": FileSummary(file_path="src/b.py", licenses=["MIT"], category="permissive", has_spdx_header=True),
            "src/c.py": FileSummary(file_path="src/c.py", licenses=["MIT"], category="permissive", has_spdx_header=True),
        }
        directories = compute_directory_rollups(files)

        src = next(d for d in directories if d.path == "src")
        assert src.direct.file_count == 3
        assert src.direct.license_counts == {"MIT": 3}

    def test_windows_style_paths_not_expected(self):
        """Test confirms we expect forward slashes (POSIX-style) paths."""
        files = {
            "src/lib/module.py": FileSummary(
                file_path="src/lib/module.py",
                licenses=["MIT"],
                category="permissive",
                has_spdx_header=True,
            )
        }
        directories = compute_directory_rollups(files)

        # Should have forward-slash paths
        paths = {d.path for d in directories}
        assert "src" in paths
        assert "src/lib" in paths
        assert "src\\lib" not in paths

    def test_dotted_directory_names(self):
        """Directories with dots should be handled correctly."""
        files = {
            ".github/workflows/ci.yml": FileSummary(
                file_path=".github/workflows/ci.yml",
                licenses=["MIT"],
                category="permissive",
                has_spdx_header=True,
            )
        }
        directories = compute_directory_rollups(files)

        paths = {d.path for d in directories}
        assert ".github" in paths
        assert ".github/workflows" in paths
