"""
Unit tests for hierarchy_builder.py
"""

import pytest
from pathlib import Path

from scripts.hierarchy_builder import (
    DirectoryMetrics,
    HierarchyInfo,
    build_hierarchy,
    compute_directory_metrics,
    get_path_ancestors,
    get_files_in_directory,
    get_subdirectories,
)
from scripts.tree_walker import walk_repository, WalkResult, FileInfo, DirectoryInfo
from scripts.id_generator import generate_root_id


class TestDirectoryMetricsDataclass:
    """Tests for DirectoryMetrics dataclass."""

    def test_directorymetrics_defaults(self):
        """DirectoryMetrics should have sensible defaults."""
        metrics = DirectoryMetrics()
        assert metrics.direct_file_count == 0
        assert metrics.direct_directory_count == 0
        assert metrics.recursive_file_count == 0
        assert metrics.recursive_directory_count == 0
        assert metrics.direct_size_bytes == 0
        assert metrics.recursive_size_bytes == 0
        assert metrics.classification_distribution == {}
        assert metrics.language_distribution == {}

    def test_directorymetrics_custom_values(self):
        """DirectoryMetrics should accept custom values."""
        metrics = DirectoryMetrics(
            direct_file_count=5,
            direct_directory_count=2,
            recursive_file_count=15,
            recursive_directory_count=8,
            direct_size_bytes=1000,
            recursive_size_bytes=5000,
            classification_distribution={"source": 10, "test": 5},
            language_distribution={"python": 8, "javascript": 7},
        )
        assert metrics.direct_file_count == 5
        assert metrics.recursive_file_count == 15
        assert metrics.classification_distribution["source"] == 10


class TestHierarchyInfoDataclass:
    """Tests for HierarchyInfo dataclass."""

    def test_hierarchyinfo_fields(self):
        """HierarchyInfo should have all required fields."""
        info = HierarchyInfo(
            root_id="d-000000000000",
            max_depth=5,
            total_files=100,
            total_directories=20,
            total_size_bytes=50000,
            children={"d-000": ["d-001", "f-001"]},
            parents={"d-001": "d-000", "f-001": "d-000"},
            depth_distribution={0: 1, 1: 5, 2: 10},
        )
        assert info.root_id == "d-000000000000"
        assert info.max_depth == 5
        assert info.total_files == 100
        assert info.total_directories == 20
        assert info.total_size_bytes == 50000


class TestBuildHierarchy:
    """Tests for build_hierarchy function."""

    def test_build_hierarchy_empty(self, tmp_path):
        """Building hierarchy for empty directory should work."""
        walk_result = walk_repository(tmp_path)
        hierarchy, metrics = build_hierarchy(walk_result, {}, {})

        assert hierarchy.root_id == generate_root_id()
        assert hierarchy.total_files == 0
        assert hierarchy.total_directories == 1  # root only
        assert hierarchy.total_size_bytes == 0

    def test_build_hierarchy_single_file(self, tmp_path):
        """Building hierarchy with single file should work."""
        (tmp_path / "main.py").write_text("x" * 100)
        walk_result = walk_repository(tmp_path)
        classifications = {"main.py": "source"}
        languages = {"main.py": "python"}

        hierarchy, metrics = build_hierarchy(walk_result, classifications, languages)

        assert hierarchy.total_files == 1
        assert hierarchy.total_directories == 1
        assert hierarchy.total_size_bytes == 100

    def test_build_hierarchy_nested(self, tmp_path):
        """Building hierarchy with nested structure should work."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "lib").mkdir()
        (tmp_path / "src" / "main.py").write_text("x" * 50)
        (tmp_path / "src" / "lib" / "utils.py").write_text("x" * 30)

        walk_result = walk_repository(tmp_path)
        classifications = {
            "src/main.py": "source",
            "src/lib/utils.py": "source",
        }
        languages = {
            "src/main.py": "python",
            "src/lib/utils.py": "python",
        }

        hierarchy, metrics = build_hierarchy(walk_result, classifications, languages)

        assert hierarchy.total_files == 2
        assert hierarchy.total_directories == 3  # root, src, src/lib
        # max_depth = path.count('/'): src/lib/utils.py has depth 2
        assert hierarchy.max_depth == 2

    def test_build_hierarchy_children_map(self, tmp_path):
        """Children map should contain correct relationships."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("code")

        walk_result = walk_repository(tmp_path)
        hierarchy, _ = build_hierarchy(walk_result, {}, {})

        # Root should have children
        root_id = generate_root_id()
        assert root_id in hierarchy.children
        # Check that src directory is a child
        src_dir = walk_result.directories["src"]
        assert src_dir.id in hierarchy.children[root_id]

    def test_build_hierarchy_parents_map(self, tmp_path):
        """Parents map should contain correct relationships."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("code")

        walk_result = walk_repository(tmp_path)
        hierarchy, _ = build_hierarchy(walk_result, {}, {})

        # src directory should have root as parent
        src_dir = walk_result.directories["src"]
        assert src_dir.id in hierarchy.parents
        assert hierarchy.parents[src_dir.id] == generate_root_id()

    def test_build_hierarchy_depth_distribution(self, tmp_path):
        """Depth distribution should be accurate."""
        (tmp_path / "a").mkdir()
        (tmp_path / "a" / "b").mkdir()
        (tmp_path / "a" / "b" / "c").mkdir()
        (tmp_path / "file1.txt").write_text("1")
        (tmp_path / "a" / "file2.txt").write_text("2")
        (tmp_path / "a" / "b" / "file3.txt").write_text("3")
        (tmp_path / "a" / "b" / "c" / "file4.txt").write_text("4")

        walk_result = walk_repository(tmp_path)
        hierarchy, _ = build_hierarchy(walk_result, {}, {})

        # Depth = path.count('/'):
        # Depth 0: root (path=""), 'a' (path="a"), file1.txt (path="file1.txt")
        # Depth 1: 'a/b' (path="a/b"), a/file2.txt (path="a/file2.txt")
        # Depth 2: 'a/b/c' (path="a/b/c"), a/b/file3.txt (path="a/b/file3.txt")
        # Depth 3: a/b/c/file4.txt (path="a/b/c/file4.txt")
        assert hierarchy.depth_distribution[0] == 3  # root + a + file1
        assert hierarchy.depth_distribution[1] == 2  # a/b + a/file2
        assert hierarchy.depth_distribution[2] == 2  # a/b/c + a/b/file3
        assert hierarchy.depth_distribution[3] == 1  # a/b/c/file4


class TestComputeDirectoryMetrics:
    """Tests for compute_directory_metrics function."""

    def test_compute_direct_file_count(self, tmp_path):
        """Direct file count should only count immediate children."""
        (tmp_path / "src").mkdir()
        (tmp_path / "file1.py").write_text("1")
        (tmp_path / "file2.py").write_text("2")
        (tmp_path / "src" / "nested.py").write_text("3")

        walk_result = walk_repository(tmp_path)
        metrics = compute_directory_metrics(walk_result, {}, {})

        # Root should have 2 direct files
        assert metrics[""].direct_file_count == 2
        # src should have 1 direct file
        assert metrics["src"].direct_file_count == 1

    def test_compute_recursive_file_count(self, tmp_path):
        """Recursive file count should include descendants for all directories."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "lib").mkdir()
        (tmp_path / "file1.py").write_text("1")
        (tmp_path / "src" / "file2.py").write_text("2")
        (tmp_path / "src" / "lib" / "file3.py").write_text("3")

        walk_result = walk_repository(tmp_path)
        metrics = compute_directory_metrics(walk_result, {}, {})

        # Root should have 3 files recursively (file1 + src/file2 + src/lib/file3)
        assert metrics[""].recursive_file_count == 3
        # src should have 2 files recursively (file2 + lib/file3)
        assert metrics["src"].recursive_file_count == 2
        # lib should have 1 file
        assert metrics["src/lib"].recursive_file_count == 1

    def test_compute_direct_size_bytes(self, tmp_path):
        """Direct size should sum immediate children only."""
        (tmp_path / "src").mkdir()
        (tmp_path / "file1.py").write_text("x" * 100)
        (tmp_path / "file2.py").write_text("x" * 200)
        (tmp_path / "src" / "nested.py").write_text("x" * 50)

        walk_result = walk_repository(tmp_path)
        metrics = compute_directory_metrics(walk_result, {}, {})

        # Root direct size = 100 + 200 = 300
        assert metrics[""].direct_size_bytes == 300
        # src direct size = 50
        assert metrics["src"].direct_size_bytes == 50

    def test_compute_recursive_size_bytes(self, tmp_path):
        """Recursive size should include descendants for all directories."""
        (tmp_path / "src").mkdir()
        (tmp_path / "file1.py").write_text("x" * 100)
        (tmp_path / "src" / "file2.py").write_text("x" * 50)

        walk_result = walk_repository(tmp_path)
        metrics = compute_directory_metrics(walk_result, {}, {})

        # Root recursive size = 100 + 50 = 150
        assert metrics[""].recursive_size_bytes == 150
        # src recursive = 50
        assert metrics["src"].recursive_size_bytes == 50

    def test_compute_direct_directory_count(self, tmp_path):
        """Direct directory count should only count immediate children."""
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "src" / "lib").mkdir()

        walk_result = walk_repository(tmp_path)
        metrics = compute_directory_metrics(walk_result, {}, {})

        # Root has 2 direct subdirs (src, tests)
        assert metrics[""].direct_directory_count == 2
        # src has 1 direct subdir (lib)
        assert metrics["src"].direct_directory_count == 1

    def test_compute_classification_distribution(self, tmp_path):
        """Classification distribution should be accurate."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("1")
        (tmp_path / "src" / "test_main.py").write_text("2")
        (tmp_path / "src" / "config.json").write_text("{}")

        walk_result = walk_repository(tmp_path)
        classifications = {
            "src/main.py": "source",
            "src/test_main.py": "test",
            "src/config.json": "config",
        }
        metrics = compute_directory_metrics(walk_result, classifications, {})

        dist = metrics["src"].classification_distribution
        assert dist.get("source", 0) == 1
        assert dist.get("test", 0) == 1
        assert dist.get("config", 0) == 1

    def test_compute_language_distribution(self, tmp_path):
        """Language distribution should be accurate."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("1")
        (tmp_path / "src" / "utils.py").write_text("2")
        (tmp_path / "src" / "app.js").write_text("3")

        walk_result = walk_repository(tmp_path)
        languages = {
            "src/main.py": "python",
            "src/utils.py": "python",
            "src/app.js": "javascript",
        }
        metrics = compute_directory_metrics(walk_result, {}, languages)

        dist = metrics["src"].language_distribution
        assert dist.get("python", 0) == 2
        assert dist.get("javascript", 0) == 1

    def test_compute_unknown_language_excluded(self, tmp_path):
        """Unknown language should not be in distribution."""
        (tmp_path / "data.xyz").write_text("data")

        walk_result = walk_repository(tmp_path)
        metrics = compute_directory_metrics(walk_result, {}, {"data.xyz": "unknown"})

        assert "unknown" not in metrics[""].language_distribution


class TestGetPathAncestors:
    """Tests for get_path_ancestors function."""

    def test_empty_path(self):
        """Empty path should return empty list."""
        assert get_path_ancestors("") == []

    def test_single_level_path(self):
        """Single level path should return root."""
        ancestors = get_path_ancestors("src")
        assert "" in ancestors

    def test_multi_level_path(self):
        """Multi-level path should return all ancestors."""
        ancestors = get_path_ancestors("src/lib/utils")
        assert "" in ancestors
        assert "src" in ancestors
        assert "src/lib" in ancestors

    def test_deep_path(self):
        """Deep path should return all ancestors."""
        ancestors = get_path_ancestors("a/b/c/d/e")
        assert len(ancestors) == 5  # "", "a", "a/b", "a/b/c", "a/b/c/d"


class TestGetFilesInDirectory:
    """Tests for get_files_in_directory function."""

    def test_get_direct_files(self, tmp_path):
        """Should get only direct children files."""
        (tmp_path / "src").mkdir()
        (tmp_path / "file1.py").write_text("1")
        (tmp_path / "file2.py").write_text("2")
        (tmp_path / "src" / "nested.py").write_text("3")

        walk_result = walk_repository(tmp_path)
        files = get_files_in_directory(walk_result, "", recursive=False)

        names = {f.name for f in files}
        assert "file1.py" in names
        assert "file2.py" in names
        assert "nested.py" not in names

    def test_get_recursive_files(self, tmp_path):
        """Should get all files recursively."""
        (tmp_path / "src").mkdir()
        (tmp_path / "file1.py").write_text("1")
        (tmp_path / "src" / "nested.py").write_text("2")

        walk_result = walk_repository(tmp_path)
        files = get_files_in_directory(walk_result, "", recursive=True)

        names = {f.name for f in files}
        assert "file1.py" in names
        assert "nested.py" in names

    def test_get_files_from_subdirectory(self, tmp_path):
        """Should get files from specific subdirectory."""
        (tmp_path / "src").mkdir()
        (tmp_path / "file1.py").write_text("1")
        (tmp_path / "src" / "main.py").write_text("2")
        (tmp_path / "src" / "utils.py").write_text("3")

        walk_result = walk_repository(tmp_path)
        files = get_files_in_directory(walk_result, "src", recursive=False)

        names = {f.name for f in files}
        assert "main.py" in names
        assert "utils.py" in names
        assert "file1.py" not in names

    def test_get_files_empty_directory(self, tmp_path):
        """Should return empty list for empty directory."""
        (tmp_path / "empty").mkdir()

        walk_result = walk_repository(tmp_path)
        files = get_files_in_directory(walk_result, "empty", recursive=False)

        assert files == []


class TestGetSubdirectories:
    """Tests for get_subdirectories function."""

    def test_get_direct_subdirs(self, tmp_path):
        """Should get only direct subdirectories."""
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "src" / "lib").mkdir()

        walk_result = walk_repository(tmp_path)
        subdirs = get_subdirectories(walk_result, "", recursive=False)

        names = {d.name for d in subdirs}
        assert "src" in names
        assert "tests" in names
        assert "lib" not in names

    def test_get_recursive_subdirs(self, tmp_path):
        """Should get all subdirectories recursively."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "lib").mkdir()
        (tmp_path / "src" / "lib" / "core").mkdir()

        walk_result = walk_repository(tmp_path)
        subdirs = get_subdirectories(walk_result, "", recursive=True)

        names = {d.name for d in subdirs}
        assert "src" in names
        assert "lib" in names
        assert "core" in names

    def test_get_subdirs_from_subdir(self, tmp_path):
        """Should get subdirectories from specific directory."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "lib").mkdir()
        (tmp_path / "src" / "utils").mkdir()
        (tmp_path / "tests").mkdir()

        walk_result = walk_repository(tmp_path)
        subdirs = get_subdirectories(walk_result, "src", recursive=False)

        names = {d.name for d in subdirs}
        assert "lib" in names
        assert "utils" in names
        assert "tests" not in names
        assert "src" not in names

    def test_get_subdirs_empty(self, tmp_path):
        """Should return empty list for directory with no subdirs."""
        (tmp_path / "leaf").mkdir()
        (tmp_path / "leaf" / "file.txt").write_text("content")

        walk_result = walk_repository(tmp_path)
        subdirs = get_subdirectories(walk_result, "leaf", recursive=False)

        assert subdirs == []


class TestRootRecursiveCountFix:
    """Tests for root directory recursive count fix (Issue 2.2)."""

    def test_root_recursive_count_includes_all_files(self, tmp_path):
        """Root directory should correctly aggregate all files recursively."""
        # Create nested structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "lib").mkdir()
        (tmp_path / "root_file.py").write_text("1")
        (tmp_path / "src" / "main.py").write_text("2")
        (tmp_path / "src" / "lib" / "utils.py").write_text("3")

        walk_result = walk_repository(tmp_path)
        metrics = compute_directory_metrics(walk_result, {}, {})

        # Root should aggregate all 3 files
        assert metrics[""].recursive_file_count == 3
        # Root should have 1 direct file
        assert metrics[""].direct_file_count == 1
        # Root should aggregate all subdirectories (src + src/lib)
        assert metrics[""].recursive_directory_count == 2

    def test_root_recursive_size_includes_all(self, tmp_path):
        """Root directory should correctly aggregate size from all descendants."""
        (tmp_path / "a").mkdir()
        (tmp_path / "a" / "b").mkdir()
        (tmp_path / "file1.py").write_text("x" * 100)
        (tmp_path / "a" / "file2.py").write_text("x" * 200)
        (tmp_path / "a" / "b" / "file3.py").write_text("x" * 300)

        walk_result = walk_repository(tmp_path)
        metrics = compute_directory_metrics(walk_result, {}, {})

        # Root should have total size 100 + 200 + 300 = 600
        assert metrics[""].recursive_size_bytes == 600
        # Root direct size is only file1 = 100
        assert metrics[""].direct_size_bytes == 100


class TestHierarchyIntegration:
    """Integration tests for hierarchy building."""

    def test_full_hierarchy_workflow(self, tmp_path):
        """Test complete workflow of building hierarchy."""
        # Create a realistic structure
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "src" / "lib").mkdir()
        (tmp_path / "src" / "main.py").write_text("x" * 100)
        (tmp_path / "src" / "utils.py").write_text("x" * 50)
        (tmp_path / "src" / "lib" / "core.py").write_text("x" * 75)
        (tmp_path / "tests" / "test_main.py").write_text("x" * 40)
        (tmp_path / "README.md").write_text("x" * 200)

        walk_result = walk_repository(tmp_path)

        classifications = {
            "src/main.py": "source",
            "src/utils.py": "source",
            "src/lib/core.py": "source",
            "tests/test_main.py": "test",
            "README.md": "docs",
        }
        languages = {
            "src/main.py": "python",
            "src/utils.py": "python",
            "src/lib/core.py": "python",
            "tests/test_main.py": "python",
            "README.md": "markdown",
        }

        hierarchy, metrics = build_hierarchy(walk_result, classifications, languages)

        # Verify hierarchy
        assert hierarchy.total_files == 5
        assert hierarchy.total_directories == 4  # root, src, tests, src/lib
        assert hierarchy.total_size_bytes == 465  # 100+50+75+40+200

        # Verify root metrics
        root_metrics = metrics[""]
        assert root_metrics.direct_file_count == 1  # README.md
        # Root now correctly aggregates all child directories
        assert root_metrics.recursive_file_count == 5  # All 5 files

        # Verify src metrics
        src_metrics = metrics["src"]
        assert src_metrics.direct_file_count == 2  # main.py, utils.py
        assert src_metrics.recursive_file_count == 3  # + core.py

        # Verify tests metrics
        tests_metrics = metrics["tests"]
        assert tests_metrics.direct_file_count == 1
        assert tests_metrics.recursive_file_count == 1

        # Verify classification distribution at src (non-root)
        assert src_metrics.classification_distribution.get("source", 0) == 3

        # Verify language distribution at src (non-root)
        assert src_metrics.language_distribution.get("python", 0) == 3
