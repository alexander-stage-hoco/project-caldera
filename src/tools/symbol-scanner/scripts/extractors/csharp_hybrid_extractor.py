"""C# hybrid symbol extractor.

Combines Roslyn (primary) and tree-sitter (fallback) extraction strategies
for robust C# code analysis.
"""

from __future__ import annotations

from pathlib import Path

from .base import (
    BaseExtractor,
    ExtractionResult,
)
from .csharp_roslyn_extractor import CSharpRoslynExtractor
from .csharp_treesitter_extractor import CSharpTreeSitterExtractor


class CSharpHybridExtractor(BaseExtractor):
    """Extract symbols from C# files using Roslyn with tree-sitter fallback.

    This extractor attempts to use Roslyn for semantic analysis first. If Roslyn
    fails (e.g., .NET SDK not installed, build errors), it falls back to
    tree-sitter for syntactic analysis.

    Benefits:
    - Roslyn provides accurate type resolution and cross-file analysis
    - Tree-sitter provides fast fallback with good error recovery
    - Graceful degradation when Roslyn is unavailable
    """

    def __init__(self, roslyn_tool_path: Path | None = None) -> None:
        """Initialize the hybrid extractor.

        Args:
            roslyn_tool_path: Path to the roslyn-tool directory. Defaults to
                the roslyn-tool directory relative to this file.
        """
        self._roslyn_extractor = CSharpRoslynExtractor(roslyn_tool_path)
        self._treesitter_extractor = CSharpTreeSitterExtractor()
        self._roslyn_available: bool | None = None

    @property
    def language(self) -> str:
        return "csharp"

    @property
    def file_extensions(self) -> tuple[str, ...]:
        return (".cs",)

    def _check_roslyn_available(self) -> bool:
        """Check if Roslyn tool is available and working."""
        if self._roslyn_available is not None:
            return self._roslyn_available

        try:
            self._roslyn_extractor._ensure_built()
            self._roslyn_available = True
        except (FileNotFoundError, RuntimeError):
            self._roslyn_available = False

        return self._roslyn_available

    def extract_file(self, file_path: Path, relative_path: str) -> ExtractionResult:
        """Extract symbols from a single file.

        Uses Roslyn if available, falls back to tree-sitter.

        Args:
            file_path: Absolute path to the file
            relative_path: Repo-relative path for output

        Returns:
            ExtractionResult containing extracted entities
        """
        # For single file, tree-sitter is more efficient
        # Roslyn requires building a compilation which is overkill for one file
        return self._treesitter_extractor.extract_file(file_path, relative_path)

    def extract_directory(
        self,
        directory: Path,
        repo_root: Path | None = None,
        exclude_patterns: tuple[str, ...] = ("__pycache__", ".git", ".venv", "venv", "node_modules", "obj", "bin"),
        resolve_calls: bool = True,
    ) -> ExtractionResult:
        """Extract symbols from all C# files in a directory.

        Attempts Roslyn first for semantic analysis, falls back to tree-sitter
        if Roslyn fails.

        Args:
            directory: Path to directory to scan
            repo_root: Root path for relative paths (defaults to directory)
            exclude_patterns: Directory names to exclude
            resolve_calls: Whether to resolve callee_file for cross-module calls

        Returns:
            Combined ExtractionResult from all files
        """
        repo_root = repo_root or directory
        result = ExtractionResult()

        # Try Roslyn first
        if self._check_roslyn_available():
            try:
                roslyn_result = self._roslyn_extractor.extract_directory(
                    directory,
                    repo_root,
                    exclude_patterns,
                    resolve_calls,
                )

                # Check if Roslyn succeeded (no fatal errors)
                fatal_errors = [
                    e for e in roslyn_result.errors
                    if not e.get("recoverable", True)
                ]

                if not fatal_errors:
                    # Add note that Roslyn was used
                    if roslyn_result.resolution_stats:
                        roslyn_result.resolution_stats["extractor"] = "roslyn"
                    return roslyn_result

                # Fall through to tree-sitter on fatal errors
                result.errors.append({
                    "file": str(directory),
                    "message": "Roslyn extraction failed, falling back to tree-sitter",
                    "code": "ROSLYN_FALLBACK",
                    "recoverable": True,
                })

            except Exception as e:
                result.errors.append({
                    "file": str(directory),
                    "message": f"Roslyn extraction error: {e}, falling back to tree-sitter",
                    "code": "ROSLYN_FALLBACK",
                    "recoverable": True,
                })

        # Fall back to tree-sitter
        treesitter_result = self._treesitter_extractor.extract_directory(
            directory,
            repo_root,
            exclude_patterns,
            resolve_calls,
        )

        # Merge any errors from the fallback attempt
        result.symbols = treesitter_result.symbols
        result.calls = treesitter_result.calls
        result.imports = treesitter_result.imports
        result.errors.extend(treesitter_result.errors)
        result.resolution_stats = treesitter_result.resolution_stats

        # Add note that tree-sitter was used
        if result.resolution_stats:
            result.resolution_stats["extractor"] = "treesitter"

        return result
