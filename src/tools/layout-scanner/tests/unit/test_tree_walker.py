"""
Unit tests for tree_walker.py
"""

import os
import pytest
from pathlib import Path

from scripts.tree_walker import (
    FileInfo,
    DirectoryInfo,
    WalkResult,
    get_extension,
    format_mtime,
    walk_repository,
    iter_files,
    iter_directories,
)
from scripts.id_generator import generate_root_id
from scripts.ignore_filter import IgnoreFilter


class TestFileInfoDataclass:
    """Tests for FileInfo dataclass."""

    def test_fileinfo_fields(self):
        """FileInfo should have all required fields."""
        info = FileInfo(
            id="f-123456789abc",
            path="src/main.py",
            name="main.py",
            extension=".py",
            size_bytes=100,
            modified_time="2024-01-15T10:30:00Z",
            is_symlink=False,
            parent_directory_id="d-abcdef012345",
            depth=2,
        )
        assert info.id == "f-123456789abc"
        assert info.path == "src/main.py"
        assert info.name == "main.py"
        assert info.extension == ".py"
        assert info.size_bytes == 100
        assert info.modified_time == "2024-01-15T10:30:00Z"
        assert info.is_symlink is False
        assert info.parent_directory_id == "d-abcdef012345"
        assert info.depth == 2


class TestDirectoryInfoDataclass:
    """Tests for DirectoryInfo dataclass."""

    def test_directoryinfo_fields(self):
        """DirectoryInfo should have all required fields."""
        info = DirectoryInfo(
            id="d-123456789abc",
            path="src",
            name="src",
            modified_time="2024-01-15T10:30:00Z",
            is_symlink=False,
            parent_directory_id="d-000000000000",
            depth=1,
        )
        assert info.id == "d-123456789abc"
        assert info.path == "src"
        assert info.name == "src"
        assert info.modified_time == "2024-01-15T10:30:00Z"
        assert info.is_symlink is False
        assert info.parent_directory_id == "d-000000000000"
        assert info.depth == 1

    def test_directoryinfo_default_lists(self):
        """DirectoryInfo should have empty default lists."""
        info = DirectoryInfo(
            id="d-123456789abc",
            path="src",
            name="src",
            modified_time="2024-01-15T10:30:00Z",
            is_symlink=False,
            parent_directory_id=None,
            depth=0,
        )
        assert info.child_file_ids == []
        assert info.child_directory_ids == []


class TestWalkResultDataclass:
    """Tests for WalkResult dataclass."""

    def test_walkresult_fields(self):
        """WalkResult should have all required fields."""
        result = WalkResult(
            files={},
            directories={},
            root_path="/path/to/repo",
            max_depth=3,
            total_size_bytes=12345,
        )
        assert result.files == {}
        assert result.directories == {}
        assert result.root_path == "/path/to/repo"
        assert result.max_depth == 3
        assert result.total_size_bytes == 12345

    def test_walkresult_defaults(self):
        """WalkResult should have sensible defaults."""
        result = WalkResult(
            files={},
            directories={},
            root_path="/path",
        )
        assert result.max_depth == 0
        assert result.total_size_bytes == 0


class TestGetExtension:
    """Tests for get_extension function."""

    def test_simple_extension(self):
        """.py extension should be extracted."""
        assert get_extension("main.py") == ".py"

    def test_multiple_dots(self):
        """Last extension should be extracted."""
        assert get_extension("file.test.js") == ".js"
        assert get_extension("archive.tar.gz") == ".gz"

    def test_no_extension(self):
        """Files without extension should return empty."""
        assert get_extension("Makefile") == ""
        assert get_extension("README") == ""

    def test_hidden_file_no_extension(self):
        """Hidden files with only one dot should return empty."""
        assert get_extension(".gitignore") == ""
        assert get_extension(".env") == ""

    def test_hidden_file_with_extension(self):
        """Hidden files with extension should extract it."""
        assert get_extension(".eslintrc.json") == ".json"
        assert get_extension(".travis.yml") == ".yml"

    def test_uppercase_extension(self):
        """Extension case should be preserved."""
        assert get_extension("README.MD") == ".MD"
        assert get_extension("image.PNG") == ".PNG"


class TestFormatMtime:
    """Tests for format_mtime function."""

    def test_format_mtime_produces_iso8601(self, tmp_path):
        """format_mtime should produce ISO 8601 format."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        stat = test_file.stat()
        mtime = format_mtime(stat)
        # Should end with Z (UTC timezone)
        assert mtime.endswith("Z")
        # Should have ISO format
        assert "T" in mtime
        # Should be parseable as ISO 8601
        from datetime import datetime
        datetime.fromisoformat(mtime.replace("Z", "+00:00"))


class TestWalkRepository:
    """Tests for walk_repository function."""

    def test_walk_empty_directory(self, tmp_path):
        """Walking empty directory should return only root."""
        result = walk_repository(tmp_path)
        assert len(result.files) == 0
        assert len(result.directories) == 1  # Just the root
        assert "" in result.directories
        assert result.directories[""].name == tmp_path.name

    def test_walk_single_file(self, tmp_path):
        """Walking directory with one file should find it."""
        (tmp_path / "test.py").write_text("print('hello')")
        result = walk_repository(tmp_path)
        assert len(result.files) == 1
        assert "test.py" in result.files
        file_info = result.files["test.py"]
        assert file_info.name == "test.py"
        assert file_info.extension == ".py"
        assert file_info.depth == 0  # Root-level file has depth 0 (path.count('/') == 0)

    def test_walk_nested_directories(self, tmp_path):
        """Walking nested directories should find all levels."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "lib").mkdir()
        (tmp_path / "src" / "lib" / "main.py").write_text("code")

        result = walk_repository(tmp_path)

        # Check directories
        assert "src" in result.directories
        assert "src/lib" in result.directories

        # Check file
        assert "src/lib/main.py" in result.files
        assert result.files["src/lib/main.py"].depth == 2  # path.count('/') == 2

    def test_walk_respects_ignore_filter(self, tmp_path):
        """Walking should respect ignore patterns."""
        (tmp_path / "src").mkdir()
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "src" / "main.py").write_text("code")
        (tmp_path / "node_modules" / "lodash.js").write_text("module")

        # Create ignore filter
        ignore_filter = IgnoreFilter.from_patterns(["node_modules/"])
        result = walk_repository(tmp_path, ignore_filter=ignore_filter)

        # src should be present
        assert "src" in result.directories
        assert "src/main.py" in result.files

        # node_modules should be ignored
        assert "node_modules" not in result.directories
        assert "node_modules/lodash.js" not in result.files

    def test_walk_fileinfo_complete(self, tmp_path):
        """FileInfo should have all required fields."""
        (tmp_path / "main.py").write_text("x" * 100)
        result = walk_repository(tmp_path)

        file_info = result.files["main.py"]
        assert file_info.id.startswith("f-")
        assert file_info.path == "main.py"
        assert file_info.name == "main.py"
        assert file_info.extension == ".py"
        assert file_info.size_bytes == 100
        assert file_info.modified_time.endswith("Z")
        assert file_info.is_symlink is False
        assert file_info.parent_directory_id == generate_root_id()
        assert file_info.depth == 0  # Root-level file has depth 0

    def test_walk_directoryinfo_complete(self, tmp_path):
        """DirectoryInfo should have all required fields."""
        (tmp_path / "src").mkdir()
        result = walk_repository(tmp_path)

        dir_info = result.directories["src"]
        assert dir_info.id.startswith("d-")
        assert dir_info.path == "src"
        assert dir_info.name == "src"
        assert dir_info.modified_time.endswith("Z")
        assert dir_info.is_symlink is False
        assert dir_info.parent_directory_id == generate_root_id()
        assert dir_info.depth == 0  # Root-level directory has depth 0

    def test_walk_file_sizes(self, tmp_path):
        """File sizes should be captured correctly."""
        (tmp_path / "small.txt").write_text("x" * 10)
        (tmp_path / "large.txt").write_text("x" * 1000)

        result = walk_repository(tmp_path)
        assert result.files["small.txt"].size_bytes == 10
        assert result.files["large.txt"].size_bytes == 1000
        assert result.total_size_bytes == 1010

    def test_walk_hidden_files(self, tmp_path):
        """Hidden files should be found."""
        (tmp_path / ".gitignore").write_text("node_modules/")
        (tmp_path / ".env").write_text("SECRET=123")

        result = walk_repository(tmp_path, respect_gitignore=False)
        # Note: .git is always ignored by default, but .gitignore and .env are not
        # The default filter only ignores .git directory
        found_hidden = [p for p in result.files.keys() if p.startswith(".")]
        assert len(found_hidden) >= 1

    def test_walk_unicode_paths(self, tmp_path):
        """Unicode paths should be handled."""
        (tmp_path / "日本語").mkdir()
        (tmp_path / "日本語" / "ファイル.py").write_text("# Japanese")

        result = walk_repository(tmp_path)
        assert "日本語" in result.directories
        assert "日本語/ファイル.py" in result.files

    def test_walk_max_depth_tracking(self, tmp_path):
        """Max depth should be tracked correctly."""
        # Create 5 levels deep
        current = tmp_path
        for i in range(5):
            current = current / f"level{i}"
            current.mkdir()
            (current / f"file{i}.txt").write_text("test")

        result = walk_repository(tmp_path)
        # Depth = path.count('/'), so:
        # level0 dir has depth 0, level0/file0.txt has depth 1
        # level4 dir has depth 4, level4/file4.txt has depth 5
        # Max depth = 5 (deepest file at level0/level1/level2/level3/level4/file4.txt)
        assert result.max_depth == 5

    def test_walk_child_ids_populated(self, tmp_path):
        """Child IDs should be populated correctly."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("code")
        (tmp_path / "src" / "utils").mkdir()

        result = walk_repository(tmp_path)

        # Root should have src as child
        root = result.directories[""]
        assert len(root.child_directory_ids) >= 1

        # src should have both file and dir children
        src_dir = result.directories["src"]
        assert len(src_dir.child_file_ids) >= 1
        assert len(src_dir.child_directory_ids) >= 1

    def test_walk_nonexistent_path_raises(self, tmp_path):
        """Walking nonexistent path should raise ValueError."""
        with pytest.raises(ValueError):
            walk_repository(tmp_path / "nonexistent")

    def test_walk_file_as_path_raises(self, tmp_path):
        """Walking a file as path should raise ValueError."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        with pytest.raises(ValueError):
            walk_repository(test_file)

    def test_walk_with_additional_ignores(self, tmp_path):
        """Additional ignore patterns should be respected."""
        (tmp_path / "src").mkdir()
        (tmp_path / "output").mkdir()
        (tmp_path / "src" / "main.py").write_text("code")
        (tmp_path / "output" / "result.txt").write_text("output")

        result = walk_repository(
            tmp_path,
            additional_ignores=["output/"]
        )

        assert "src" in result.directories
        assert "output" not in result.directories

    def test_walk_deterministic_order(self, tmp_path):
        """Results should be in deterministic order."""
        # Create files in random order
        for name in ["zebra.py", "apple.py", "mango.py"]:
            (tmp_path / name).write_text("code")

        # Walk multiple times
        result1 = walk_repository(tmp_path)
        result2 = walk_repository(tmp_path)

        # Order should be consistent
        assert list(result1.files.keys()) == list(result2.files.keys())


class TestWalkRepositorySymlinks:
    """Tests for symlink handling in walk_repository.

    Note: The implementation uses is_file(follow_symlinks=False) and
    is_dir(follow_symlinks=False) which means symlinks are skipped entirely.
    They're neither files nor directories when symlinks are not followed.
    """

    def test_symlink_file_skipped(self, tmp_path):
        """Symlink files are skipped (not processed as regular files)."""
        real_file = tmp_path / "real.txt"
        real_file.write_text("content")
        link = tmp_path / "link.txt"
        link.symlink_to(real_file)

        result = walk_repository(tmp_path)

        # Real file should be found
        assert "real.txt" in result.files
        assert result.files["real.txt"].is_symlink is False
        # Symlink is skipped (not followed)
        assert "link.txt" not in result.files

    def test_symlink_directory_skipped(self, tmp_path):
        """Symlink directories are skipped (not processed as directories)."""
        real_dir = tmp_path / "real_dir"
        real_dir.mkdir()
        link_dir = tmp_path / "link_dir"
        link_dir.symlink_to(real_dir)

        result = walk_repository(tmp_path)

        # Real directory should be found
        assert "real_dir" in result.directories
        assert result.directories["real_dir"].is_symlink is False
        # Symlink directory is skipped
        assert "link_dir" not in result.directories

    def test_symlink_directory_not_followed(self, tmp_path):
        """Symlink directories should not be followed to avoid cycles."""
        real_dir = tmp_path / "real_dir"
        real_dir.mkdir()
        (real_dir / "file.txt").write_text("content")
        link_dir = tmp_path / "link_dir"
        link_dir.symlink_to(real_dir)

        result = walk_repository(tmp_path)

        # File in real_dir should be found
        assert "real_dir/file.txt" in result.files
        # Symlink directory is skipped, so no files through it
        assert "link_dir/file.txt" not in result.files
        assert "link_dir" not in result.directories


class TestIterHelpers:
    """Tests for iteration helper functions."""

    def test_iter_files_empty(self, tmp_path):
        """iter_files on empty walk should yield nothing."""
        result = walk_repository(tmp_path)
        files = list(iter_files(result))
        assert len(files) == 0

    def test_iter_files_returns_all(self, tmp_path):
        """iter_files should yield all files."""
        (tmp_path / "a.py").write_text("a")
        (tmp_path / "b.py").write_text("b")
        (tmp_path / "c.py").write_text("c")

        result = walk_repository(tmp_path)
        files = list(iter_files(result))

        assert len(files) == 3
        names = {f.name for f in files}
        assert names == {"a.py", "b.py", "c.py"}

    def test_iter_directories_returns_root(self, tmp_path):
        """iter_directories should include root."""
        result = walk_repository(tmp_path)
        dirs = list(iter_directories(result))

        assert len(dirs) == 1
        assert dirs[0].path == ""

    def test_iter_directories_returns_all(self, tmp_path):
        """iter_directories should yield all directories."""
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "docs").mkdir()

        result = walk_repository(tmp_path)
        dirs = list(iter_directories(result))

        # Root + 3 subdirectories
        assert len(dirs) == 4
        names = {d.name for d in dirs}
        assert "src" in names
        assert "tests" in names
        assert "docs" in names


class TestWalkRepositoryEdgeCases:
    """Tests for edge cases in walk_repository."""

    def test_special_characters_in_filename(self, tmp_path):
        """Files with special characters should be handled."""
        special_files = [
            "file with spaces.py",
            "file-with-dashes.py",
            "file_with_underscores.py",
            "file (copy).txt",
        ]
        for name in special_files:
            (tmp_path / name).write_text("content")

        result = walk_repository(tmp_path)

        for name in special_files:
            assert name in result.files

    def test_very_long_filename(self, tmp_path):
        """Very long filenames should be handled."""
        long_name = "a" * 200 + ".txt"
        try:
            (tmp_path / long_name).write_text("content")
            result = walk_repository(tmp_path)
            assert long_name in result.files
        except OSError:
            # Some filesystems have name length limits
            pytest.skip("Filesystem doesn't support long filenames")

    def test_empty_file(self, tmp_path):
        """Empty files should be handled."""
        (tmp_path / "empty.txt").write_text("")
        result = walk_repository(tmp_path)

        assert "empty.txt" in result.files
        assert result.files["empty.txt"].size_bytes == 0

    def test_binary_file(self, tmp_path):
        """Binary files should be handled."""
        (tmp_path / "binary.bin").write_bytes(b"\x00\x01\x02\x03")
        result = walk_repository(tmp_path)

        assert "binary.bin" in result.files
        assert result.files["binary.bin"].size_bytes == 4


class TestDepthCalculation:
    """Tests for depth calculation based on path separators."""

    def test_depth_matches_path_slash_count(self, tmp_path):
        """Depth should equal the number of slashes in the path."""
        # Create nested structure
        (tmp_path / "a").mkdir()
        (tmp_path / "a" / "b").mkdir()
        (tmp_path / "a" / "b" / "c").mkdir()
        (tmp_path / "root_file.txt").write_text("0")
        (tmp_path / "a" / "file_a.txt").write_text("1")
        (tmp_path / "a" / "b" / "file_b.txt").write_text("2")
        (tmp_path / "a" / "b" / "c" / "file_c.txt").write_text("3")

        result = walk_repository(tmp_path)

        # Verify file depths match path.count('/')
        assert result.files["root_file.txt"].depth == 0  # "root_file.txt".count('/') == 0
        assert result.files["a/file_a.txt"].depth == 1  # "a/file_a.txt".count('/') == 1
        assert result.files["a/b/file_b.txt"].depth == 2  # "a/b/file_b.txt".count('/') == 2
        assert result.files["a/b/c/file_c.txt"].depth == 3  # "a/b/c/file_c.txt".count('/') == 3

        # Verify directory depths match path.count('/')
        assert result.directories[""].depth == 0  # Root always has depth 0
        assert result.directories["a"].depth == 0  # "a".count('/') == 0
        assert result.directories["a/b"].depth == 1  # "a/b".count('/') == 1
        assert result.directories["a/b/c"].depth == 2  # "a/b/c".count('/') == 2

    def test_root_has_depth_zero(self, tmp_path):
        """Root directory should always have depth 0."""
        result = walk_repository(tmp_path)
        assert result.directories[""].depth == 0
