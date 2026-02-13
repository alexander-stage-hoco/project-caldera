"""
Ignore Filter for Layout Scanner.

Parses .gitignore files and filters paths based on ignore patterns.
Supports standard .gitignore syntax including wildcards and negations.

Uses the pathspec library for correct gitignore semantics including
proper handling of ** for recursive matching.
"""
from __future__ import annotations

import os
from pathlib import Path

import pathspec


class IgnoreFilter:
    """
    Filter for checking if paths should be ignored.

    Supports .gitignore patterns and additional custom patterns.
    Uses pathspec library for correct gitignore semantics.
    """

    # Default patterns to always ignore
    DEFAULT_IGNORES = [
        ".git",
        ".git/**",
    ]

    def __init__(self):
        """Initialize an empty ignore filter."""
        self._patterns: list[str] = []
        self._spec: pathspec.PathSpec | None = None

    @classmethod
    def from_gitignore(cls, gitignore_path: Path) -> "IgnoreFilter":
        """
        Create an IgnoreFilter from a .gitignore file.

        Args:
            gitignore_path: Path to .gitignore file

        Returns:
            IgnoreFilter with patterns from file
        """
        filter_obj = cls()

        # Add default ignores
        for pattern in cls.DEFAULT_IGNORES:
            filter_obj.add_pattern(pattern)

        if gitignore_path.exists():
            with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    filter_obj.add_pattern_line(line)

        return filter_obj

    @classmethod
    def from_patterns(cls, patterns: list[str]) -> "IgnoreFilter":
        """
        Create an IgnoreFilter from a list of patterns.

        Args:
            patterns: List of gitignore-style patterns

        Returns:
            IgnoreFilter with given patterns
        """
        filter_obj = cls()

        # Add default ignores
        for pattern in cls.DEFAULT_IGNORES:
            filter_obj.add_pattern(pattern)

        for pattern in patterns:
            filter_obj.add_pattern(pattern)

        return filter_obj

    def add_pattern_line(self, line: str) -> None:
        """Add a pattern from a .gitignore line (handles comments, blank lines)."""
        line = line.rstrip("\n\r")

        # Skip blank lines and comments
        if not line or line.startswith("#"):
            return

        # Handle trailing spaces (only if escaped with backslash)
        if line.endswith("\\ "):
            line = line[:-2] + " "
        else:
            line = line.rstrip()

        if not line:
            return

        self.add_pattern(line)

    def add_pattern(self, pattern: str) -> None:
        """Add a gitignore pattern."""
        self._patterns.append(pattern)
        self._spec = None  # Invalidate cached spec

    def _get_spec(self) -> pathspec.PathSpec:
        """Get or create the pathspec matcher."""
        if self._spec is None:
            self._spec = pathspec.PathSpec.from_lines("gitwildmatch", self._patterns)
        return self._spec

    def should_ignore(self, path: str, is_dir: bool = False) -> bool:
        """
        Check if a path should be ignored.

        Args:
            path: Relative path from repository root
            is_dir: Whether the path is a directory

        Returns:
            True if the path should be ignored
        """
        # Normalize path
        path = path.replace("\\", "/")
        # Strip leading ./ but not leading . (for dotfiles like .git)
        while path.startswith("./"):
            path = path[2:]

        # For directories, pathspec needs trailing slash for some patterns
        check_path = path + "/" if is_dir else path

        return self._get_spec().match_file(check_path)

    def filter_entries(
        self,
        entries: list[os.DirEntry],
        base_path: str = ""
    ) -> list[os.DirEntry]:
        """
        Filter directory entries based on ignore patterns.

        Args:
            entries: List of os.DirEntry objects
            base_path: Base path to prepend for relative path computation

        Returns:
            Filtered list of entries that should not be ignored
        """
        result = []

        for entry in entries:
            rel_path = f"{base_path}/{entry.name}" if base_path else entry.name
            rel_path = rel_path.lstrip("/")

            if not self.should_ignore(rel_path, entry.is_dir(follow_symlinks=False)):
                result.append(entry)

        return result


def load_ignore_filter(
    repo_root: Path,
    additional_patterns: list[str] | None = None,
    respect_gitignore: bool = True
) -> IgnoreFilter:
    """
    Load an ignore filter for a repository.

    Args:
        repo_root: Path to repository root
        additional_patterns: Additional patterns to add
        respect_gitignore: Whether to load .gitignore

    Returns:
        IgnoreFilter configured for the repository
    """
    if respect_gitignore:
        gitignore_path = repo_root / ".gitignore"
        filter_obj = IgnoreFilter.from_gitignore(gitignore_path)
    else:
        filter_obj = IgnoreFilter.from_patterns(IgnoreFilter.DEFAULT_IGNORES)

    if additional_patterns:
        for pattern in additional_patterns:
            filter_obj.add_pattern(pattern)

    return filter_obj
