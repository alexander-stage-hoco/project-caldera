"""Tests for path normalization and truncation functions."""

import pytest
import sys
from pathlib import Path

# Add scripts and shared src to path for imports
scripts_path = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from directory_analyzer import truncate_path_middle
from shared.path_utils import normalize_file_path


class TestTruncatePathMiddle:
    """Tests for the truncate_path_middle function."""

    def test_short_path_unchanged(self):
        """Short paths should not be truncated."""
        path = "src/main.py"
        result = truncate_path_middle(path, max_len=50)
        assert result == path

    def test_exact_length_unchanged(self):
        """Path exactly at max length should not be truncated."""
        path = "a" * 30
        result = truncate_path_middle(path, max_len=30)
        assert result == path

    def test_long_path_truncated(self):
        """Long paths should be truncated with ellipsis."""
        path = "eval-repos/real/SomeProject/src/components/features/UserProfile.tsx"
        result = truncate_path_middle(path, max_len=40)
        assert len(result) <= 40
        assert "..." in result

    def test_preserves_start_and_end(self):
        """Truncation should preserve start and end of path."""
        path = "eval-repos/real/SomeProject/src/components/features/UserProfile.tsx"
        result = truncate_path_middle(path, max_len=40)
        # Should start with beginning of original path
        assert result.startswith("eval-repo")
        # Should end with end of original path
        assert result.endswith(".tsx")

    def test_very_short_max_len(self):
        """Very short max_len should still work."""
        path = "eval-repos/real/SomeProject/src/main.py"
        result = truncate_path_middle(path, max_len=15)
        assert len(result) <= 15
        assert "..." in result

    def test_empty_path(self):
        """Empty path should return empty string."""
        result = truncate_path_middle("", max_len=50)
        assert result == ""

    def test_path_with_unicode(self):
        """Path with unicode characters should work."""
        path = "src/components/日本語/main.py"
        # Note: Unicode may affect character count vs display width
        result = truncate_path_middle(path, max_len=50)
        assert isinstance(result, str)


class TestPathNormalization:
    """Tests for path normalization patterns used in scc."""

    def test_relative_path_format(self):
        """Paths should use forward slashes."""
        # This tests the expected format, not a specific function
        paths = [
            "src/main.py",
            "tests/unit/test_main.py",
            "eval-repos/synthetic/python/simple.py",
        ]
        for path in paths:
            assert "\\" not in path  # No backslashes
            assert not path.startswith("/")  # Relative, not absolute
            assert not path.startswith("./")  # No leading ./

    def test_consistent_separator(self):
        """All paths should use / as separator."""
        test_paths = [
            ("src\\main.py", "src/main.py"),
            (".\\src\\main.py", "src/main.py"),
            ("./src/main.py", "src/main.py"),
        ]
        for input_path, expected in test_paths:
            # Manual normalization that scc output should follow
            normalized = input_path.replace("\\", "/")
            if normalized.startswith("./"):
                normalized = normalized[2:]
            assert normalized == expected

    def test_strips_repo_prefix_without_leading_slash(self):
        """Paths with repo prefix but no leading slash are normalized."""
        repo_root = Path("/tmp/keepass2android")
        input_path = "tmp/keepass2android/.github/PULL_REQUEST_TEMPLATE.md"
        normalized = normalize_file_path(input_path, repo_root)
        assert normalized == ".github/PULL_REQUEST_TEMPLATE.md"
