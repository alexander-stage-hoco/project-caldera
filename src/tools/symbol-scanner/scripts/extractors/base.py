"""Abstract base class for language-specific symbol extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ExtractedSymbol:
    """Represents an extracted symbol (function, class, method)."""

    path: str  # repo-relative file path
    symbol_name: str
    symbol_type: str  # "function", "class", "method", "variable"
    line_start: int
    line_end: int
    is_exported: bool  # True if public (no leading underscore)
    parameters: int | None  # Number of parameters (for functions/methods)
    parent_symbol: str | None  # Containing class name (for methods)
    docstring: str | None  # Documentation string if present


@dataclass
class ExtractedCall:
    """Represents an extracted function/method call."""

    caller_file: str  # repo-relative file path
    caller_symbol: str  # function/method that contains the call
    callee_symbol: str  # function/method being called
    callee_file: str | None  # resolved file path or None if external/unresolved
    line_number: int
    call_type: str  # "direct", "dynamic", "async"
    is_dynamic_code_execution: bool = False  # True for eval(), exec(), compile()
    callee_object: str | None = None  # Object/module for attribute calls (e.g., "json" for json.loads)


@dataclass
class ExtractedImport:
    """Represents an extracted import statement."""

    file: str  # repo-relative file path
    imported_path: str  # module path (e.g., "src.utils")
    imported_symbols: str | None  # comma-separated symbols or None for "import x"
    import_type: str  # "static", "dynamic", "type_checking", "side_effect"
    line_number: int
    module_alias: str | None = None  # Alias for module imports (e.g., "u" for "import utils as u")


@dataclass
class ExtractionResult:
    """Result of extracting symbols from a repository."""

    symbols: list[ExtractedSymbol] = field(default_factory=list)
    calls: list[ExtractedCall] = field(default_factory=list)
    imports: list[ExtractedImport] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    resolution_stats: dict | None = field(default=None)

    @property
    def summary(self) -> dict:
        """Generate summary statistics."""
        result = {
            "total_files": len(set(s.path for s in self.symbols)),
            "total_symbols": len(self.symbols),
            "total_calls": len(self.calls),
            "total_imports": len(self.imports),
            "symbols_by_type": self._count_by_type(),
            "calls_by_type": self._count_calls_by_type(),
            "imports_by_type": self._count_imports_by_type(),
        }
        if self.resolution_stats:
            result["resolution"] = self.resolution_stats
        return result

    def _count_by_type(self) -> dict[str, int]:
        """Count symbols by type."""
        counts: dict[str, int] = {}
        for symbol in self.symbols:
            counts[symbol.symbol_type] = counts.get(symbol.symbol_type, 0) + 1
        return counts

    def _count_calls_by_type(self) -> dict[str, int]:
        """Count calls by type."""
        counts: dict[str, int] = {}
        for call in self.calls:
            counts[call.call_type] = counts.get(call.call_type, 0) + 1
        return counts

    def _count_imports_by_type(self) -> dict[str, int]:
        """Count imports by type."""
        counts: dict[str, int] = {}
        for imp in self.imports:
            counts[imp.import_type] = counts.get(imp.import_type, 0) + 1
        return counts


class BaseExtractor(ABC):
    """Abstract base class for language-specific symbol extractors."""

    @property
    @abstractmethod
    def language(self) -> str:
        """Return the language this extractor handles (e.g., 'python')."""
        ...

    @property
    @abstractmethod
    def file_extensions(self) -> tuple[str, ...]:
        """Return file extensions this extractor handles (e.g., ('.py',))."""
        ...

    @abstractmethod
    def extract_file(self, file_path: Path, relative_path: str) -> ExtractionResult:
        """Extract symbols, calls, and imports from a single file.

        Args:
            file_path: Absolute path to the file
            relative_path: Repo-relative path for output

        Returns:
            ExtractionResult containing extracted entities
        """
        ...

    def extract_directory(
        self,
        directory: Path,
        repo_root: Path | None = None,
        exclude_patterns: tuple[str, ...] = ("__pycache__", ".git", ".venv", "venv", "node_modules"),
        resolve_calls: bool = True,
    ) -> ExtractionResult:
        """Extract symbols from all matching files in a directory.

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

        for ext in self.file_extensions:
            for file_path in directory.rglob(f"*{ext}"):
                # Skip excluded directories
                if any(part in exclude_patterns for part in file_path.parts):
                    continue

                try:
                    relative_path = str(file_path.relative_to(repo_root))
                    # Normalize to POSIX separators
                    relative_path = relative_path.replace("\\", "/")

                    file_result = self.extract_file(file_path, relative_path)
                    result.symbols.extend(file_result.symbols)
                    result.calls.extend(file_result.calls)
                    result.imports.extend(file_result.imports)
                    result.errors.extend(file_result.errors)
                except Exception as e:
                    result.errors.append({
                        "file": str(file_path),
                        "message": str(e),
                        "code": "EXTRACTION_ERROR",
                        "recoverable": True,
                    })

        # Phase 2: Resolve cross-module calls
        if resolve_calls and result.calls:
            if self.language in ("javascript", "typescript"):
                from .js_call_resolver import JSCallResolver

                resolver = JSCallResolver(repo_root, result.symbols, result.imports)
            else:
                from .call_resolver import CallResolver

                resolver = CallResolver(repo_root, result.symbols, result.imports)
            result.calls = resolver.resolve(result.calls)
            result.resolution_stats = resolver.stats.to_dict()

        return result
