"""
Unit tests for ignore_filter.py

Tests the IgnoreFilter class which uses pathspec library for gitignore-style
pattern matching.
"""

import pytest
from pathlib import Path

from scripts.ignore_filter import (
    IgnoreFilter,
    load_ignore_filter,
)


class TestIgnoreFilter:
    """Tests for IgnoreFilter class."""

    def test_empty_filter_has_default_patterns(self):
        """Empty filter should have default patterns for .git."""
        filter_obj = IgnoreFilter.from_patterns([])
        # Check that default patterns are working (via .git/** pattern)
        assert filter_obj.should_ignore(".git/config", is_dir=False)
        assert filter_obj.should_ignore(".git/objects/pack", is_dir=True)

    def test_simple_pattern(self):
        """Filter should match simple patterns."""
        filter_obj = IgnoreFilter.from_patterns(["*.pyc"])
        assert filter_obj.should_ignore("test.pyc", is_dir=False)
        assert filter_obj.should_ignore("src/test.pyc", is_dir=False)
        assert not filter_obj.should_ignore("test.py", is_dir=False)

    def test_directory_pattern(self):
        """Filter should match directory patterns."""
        filter_obj = IgnoreFilter.from_patterns(["node_modules/"])
        assert filter_obj.should_ignore("node_modules", is_dir=True)
        assert not filter_obj.should_ignore("node_modules", is_dir=False)

    def test_negation_pattern(self):
        """Negation should override previous ignore."""
        filter_obj = IgnoreFilter.from_patterns([
            "*.log",
            "!important.log",
        ])
        assert filter_obj.should_ignore("debug.log", is_dir=False)
        assert not filter_obj.should_ignore("important.log", is_dir=False)

    def test_multiple_patterns(self):
        """Multiple patterns should all be checked."""
        filter_obj = IgnoreFilter.from_patterns([
            "*.pyc",
            "*.log",
            "__pycache__/",
        ])
        assert filter_obj.should_ignore("test.pyc", is_dir=False)
        assert filter_obj.should_ignore("app.log", is_dir=False)
        assert filter_obj.should_ignore("__pycache__", is_dir=True)
        assert not filter_obj.should_ignore("test.py", is_dir=False)

    def test_path_normalization(self):
        """Paths should be normalized before matching."""
        filter_obj = IgnoreFilter.from_patterns(["*.pyc"])
        # Leading ./ should be stripped
        assert filter_obj.should_ignore("./test.pyc", is_dir=False)
        # Backslashes should work on Windows
        assert filter_obj.should_ignore("src\\test.pyc", is_dir=False)

    def test_anchored_pattern(self):
        """Anchored patterns should only match at root."""
        filter_obj = IgnoreFilter.from_patterns(["/config.json"])
        assert filter_obj.should_ignore("config.json", is_dir=False)
        assert not filter_obj.should_ignore("subdir/config.json", is_dir=False)

    def test_double_star_pattern(self):
        """Double star patterns should match at any depth."""
        filter_obj = IgnoreFilter.from_patterns(["**/build"])
        assert filter_obj.should_ignore("build", is_dir=True)
        assert filter_obj.should_ignore("src/build", is_dir=True)
        assert filter_obj.should_ignore("deep/nested/build", is_dir=True)


class TestIgnoreFilterFromGitignore:
    """Tests for loading IgnoreFilter from .gitignore files."""

    def test_load_missing_gitignore(self, tmp_path):
        """Loading from missing .gitignore should return filter with defaults."""
        filter_obj = IgnoreFilter.from_gitignore(tmp_path / ".gitignore")
        # Should still have default patterns (via .git/** pattern)
        assert filter_obj.should_ignore(".git/config", is_dir=False)

    def test_load_empty_gitignore(self, tmp_path):
        """Loading from empty .gitignore should work."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("")
        filter_obj = IgnoreFilter.from_gitignore(gitignore)
        # Default patterns still apply (via .git/** pattern)
        assert filter_obj.should_ignore(".git/config", is_dir=False)

    def test_load_gitignore_with_patterns(self, tmp_path):
        """Loading .gitignore with patterns should parse them."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\nnode_modules/\n")
        filter_obj = IgnoreFilter.from_gitignore(gitignore)
        assert filter_obj.should_ignore("test.pyc", is_dir=False)
        assert filter_obj.should_ignore("node_modules", is_dir=True)

    def test_load_gitignore_with_comments(self, tmp_path):
        """Comments should be ignored."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("# This is a comment\n*.pyc\n# Another comment\n")
        filter_obj = IgnoreFilter.from_gitignore(gitignore)
        assert filter_obj.should_ignore("test.pyc", is_dir=False)
        assert not filter_obj.should_ignore("# This is a comment", is_dir=False)

    def test_load_gitignore_with_blank_lines(self, tmp_path):
        """Blank lines should be ignored."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n\n\n*.log\n")
        filter_obj = IgnoreFilter.from_gitignore(gitignore)
        assert filter_obj.should_ignore("test.pyc", is_dir=False)
        assert filter_obj.should_ignore("debug.log", is_dir=False)

    def test_load_gitignore_with_negation(self, tmp_path):
        """Negation patterns should work."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.log\n!important.log\n")
        filter_obj = IgnoreFilter.from_gitignore(gitignore)
        assert filter_obj.should_ignore("debug.log", is_dir=False)
        assert not filter_obj.should_ignore("important.log", is_dir=False)


class TestAddPatternLine:
    """Tests for add_pattern_line method."""

    def test_strips_newlines(self):
        """Newlines should be stripped."""
        filter_obj = IgnoreFilter()
        filter_obj.add_pattern_line("*.pyc\n")
        filter_obj.add_pattern_line("*.log\r\n")
        # Verify patterns work
        assert filter_obj.should_ignore("test.pyc", is_dir=False)
        assert filter_obj.should_ignore("test.log", is_dir=False)

    def test_skips_comments(self):
        """Comment lines starting with # should be skipped."""
        filter_obj = IgnoreFilter()
        filter_obj.add_pattern_line("# comment")
        filter_obj.add_pattern_line("*.pyc")
        # Comment should not match anything
        assert not filter_obj.should_ignore("# comment", is_dir=False)
        # Pattern should work
        assert filter_obj.should_ignore("test.pyc", is_dir=False)

    def test_skips_blank_lines(self):
        """Blank lines should be skipped."""
        filter_obj = IgnoreFilter()
        filter_obj.add_pattern_line("")
        filter_obj.add_pattern_line("   ")
        filter_obj.add_pattern_line("\t\t")
        filter_obj.add_pattern_line("*.pyc")
        # Only the actual pattern should work
        assert filter_obj.should_ignore("test.pyc", is_dir=False)


class TestLoadIgnoreFilter:
    """Tests for load_ignore_filter function."""

    def test_loads_gitignore_by_default(self, tmp_path):
        """Should load .gitignore by default."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n")
        filter_obj = load_ignore_filter(tmp_path)
        assert filter_obj.should_ignore("test.pyc", is_dir=False)

    def test_respects_gitignore_false(self, tmp_path):
        """Should skip .gitignore when respect_gitignore=False."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n")
        filter_obj = load_ignore_filter(tmp_path, respect_gitignore=False)
        # .pyc should not be ignored (only defaults)
        assert not filter_obj.should_ignore("test.pyc", is_dir=False)
        # Default patterns for .git should still be present (via .git/** pattern)
        assert filter_obj.should_ignore(".git/config", is_dir=False)

    def test_additional_patterns(self, tmp_path):
        """Additional patterns should be added."""
        filter_obj = load_ignore_filter(
            tmp_path,
            additional_patterns=["*.log", "temp/"],
        )
        assert filter_obj.should_ignore("debug.log", is_dir=False)
        assert filter_obj.should_ignore("temp", is_dir=True)

    def test_additional_patterns_with_gitignore(self, tmp_path):
        """Additional patterns should combine with .gitignore."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n")
        filter_obj = load_ignore_filter(
            tmp_path,
            additional_patterns=["*.log"],
        )
        assert filter_obj.should_ignore("test.pyc", is_dir=False)
        assert filter_obj.should_ignore("debug.log", is_dir=False)


class TestCommonPatterns:
    """Tests for common .gitignore patterns."""

    def test_python_patterns(self):
        """Common Python patterns should work."""
        filter_obj = IgnoreFilter.from_patterns([
            "*.pyc",
            "__pycache__/",
            "*.pyo",
        ])
        assert filter_obj.should_ignore("module.pyc", is_dir=False)
        assert filter_obj.should_ignore("__pycache__", is_dir=True)
        assert filter_obj.should_ignore("src/__pycache__", is_dir=True)

    def test_node_patterns(self):
        """Common Node.js patterns should work."""
        filter_obj = IgnoreFilter.from_patterns([
            "node_modules/",
            "npm-debug.log",
            "dist/",
        ])
        assert filter_obj.should_ignore("node_modules", is_dir=True)
        assert filter_obj.should_ignore("npm-debug.log", is_dir=False)
        assert filter_obj.should_ignore("dist", is_dir=True)

    def test_extension_patterns(self):
        """Extension-based patterns should work."""
        filter_obj = IgnoreFilter.from_patterns([
            "*.swp",
            "*.log",
            "*.tmp",
        ])
        assert filter_obj.should_ignore("file.swp", is_dir=False)
        assert filter_obj.should_ignore("debug.log", is_dir=False)
        assert filter_obj.should_ignore("data.tmp", is_dir=False)

    def test_nested_path_patterns(self):
        """Patterns in nested paths should work."""
        filter_obj = IgnoreFilter.from_patterns([
            "logs/*.log",
            "build/output/",
        ])
        assert filter_obj.should_ignore("logs/app.log", is_dir=False)
        assert filter_obj.should_ignore("build/output", is_dir=True)


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_path(self):
        """Empty path should be handled."""
        filter_obj = IgnoreFilter.from_patterns(["*.pyc"])
        # Empty path shouldn't match .pyc pattern
        assert not filter_obj.should_ignore("", is_dir=False)

    def test_unicode_patterns(self):
        """Unicode patterns should work."""
        filter_obj = IgnoreFilter.from_patterns(["日本語/"])
        assert filter_obj.should_ignore("日本語", is_dir=True)

    def test_very_long_patterns(self):
        """Very long patterns should work."""
        long_pattern = "a" * 100 + "*.txt"
        filter_obj = IgnoreFilter.from_patterns([long_pattern])
        assert filter_obj.should_ignore("a" * 100 + "file.txt", is_dir=False)

    def test_pattern_order_matters(self):
        """Later patterns should override earlier ones."""
        filter_obj = IgnoreFilter.from_patterns([
            "*.log",
            "!important.log",
            "important.log",  # Re-ignore
        ])
        # Last pattern wins
        assert filter_obj.should_ignore("important.log", is_dir=False)
