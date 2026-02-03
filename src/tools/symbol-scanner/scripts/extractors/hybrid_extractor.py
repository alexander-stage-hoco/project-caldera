"""Hybrid extractor: AST first, tree-sitter fallback on syntax errors.

This extractor provides the best of both worlds:
- AST's precision on valid Python code (F1 = 1.00)
- Tree-sitter's error recovery on malformed code (F1 ≈ 0.79)
"""

from __future__ import annotations

from pathlib import Path

from .base import BaseExtractor, ExtractionResult
from .python_extractor import PythonExtractor
from .treesitter_extractor import TreeSitterExtractor


class HybridExtractor(BaseExtractor):
    """Hybrid extractor that uses AST first, falls back to tree-sitter on errors.

    Strategy:
        1. Try AST extractor first (most accurate for valid code)
        2. If AST fails with SyntaxError, fall back to tree-sitter (error recovery)
        3. Track which files used the fallback for reporting

    Attributes:
        fallback_files: List of relative paths that used tree-sitter fallback
    """

    def __init__(self) -> None:
        """Initialize both extractors."""
        self._ast_extractor = PythonExtractor()
        self._ts_extractor: TreeSitterExtractor | None = None  # Lazy init
        self.fallback_files: list[str] = []

    @property
    def _treesitter_extractor(self) -> TreeSitterExtractor:
        """Lazy initialization of tree-sitter extractor."""
        if self._ts_extractor is None:
            self._ts_extractor = TreeSitterExtractor()
        return self._ts_extractor

    @property
    def language(self) -> str:
        return "python"

    @property
    def file_extensions(self) -> tuple[str, ...]:
        return (".py",)

    def extract_file(self, file_path: Path, relative_path: str) -> ExtractionResult:
        """Extract symbols, calls, and imports from a Python file.

        Uses AST extractor first. If AST fails with a syntax error, falls back
        to tree-sitter which can recover and extract partial results.

        Args:
            file_path: Absolute path to the file
            relative_path: Repo-relative path for output

        Returns:
            ExtractionResult containing extracted entities
        """
        # Try AST first
        result = self._ast_extractor.extract_file(file_path, relative_path)

        # Check if AST had a syntax error
        has_syntax_error = any(
            e.get("code") == "SYNTAX_ERROR" for e in result.errors
        )

        if has_syntax_error:
            # Fall back to tree-sitter for error recovery
            self.fallback_files.append(relative_path)
            result = self._treesitter_extractor.extract_file(file_path, relative_path)

        return result

    def reset_fallback_tracking(self) -> None:
        """Reset the list of files that used fallback.

        Call this before processing a new repository to get accurate
        fallback tracking per-repo.
        """
        self.fallback_files = []

    @property
    def fallback_count(self) -> int:
        """Return the number of files that used tree-sitter fallback."""
        return len(self.fallback_files)
