"""C# Roslyn-based symbol extractor.

Python wrapper that invokes the Roslyn .NET tool via subprocess for semantic C# analysis.
Provides full type resolution and accurate cross-file call resolution.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import jsonschema

from .base import (
    BaseExtractor,
    ExtractedCall,
    ExtractedImport,
    ExtractedSymbol,
    ExtractionResult,
)

# Schema path for validating Roslyn output
_SCHEMA_PATH = Path(__file__).parent.parent.parent / "schemas" / "output.schema.json"
_CACHED_SCHEMA: dict | None = None


def _get_data_schema() -> dict:
    """Load and cache the data schema for Roslyn output validation.

    Returns the symbolScannerData definition from the schema since Roslyn
    outputs the data portion, not the full envelope.
    """
    global _CACHED_SCHEMA
    if _CACHED_SCHEMA is None:
        with open(_SCHEMA_PATH) as f:
            full_schema = json.load(f)
        # Extract the data schema definition for validation
        # Roslyn outputs data structure, not the full envelope
        _CACHED_SCHEMA = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "symbols": full_schema["$defs"]["symbolScannerData"]["properties"]["symbols"],
                "calls": full_schema["$defs"]["symbolScannerData"]["properties"]["calls"],
                "imports": full_schema["$defs"]["symbolScannerData"]["properties"]["imports"],
                "errors": full_schema.get("properties", {}).get("errors", {"type": "array"}),
            },
            "$defs": full_schema.get("$defs", {}),
        }
    return _CACHED_SCHEMA


class CSharpRoslynExtractor(BaseExtractor):
    """Extract symbols, calls, and imports from C# source files using Roslyn.

    This extractor invokes the roslyn-tool .NET console application to perform
    semantic analysis of C# code. It provides better type resolution and
    cross-file analysis than the tree-sitter based extractor.
    """

    def __init__(self, roslyn_tool_path: Path | None = None) -> None:
        """Initialize the Roslyn extractor.

        Args:
            roslyn_tool_path: Path to the roslyn-tool directory. Defaults to
                the roslyn-tool directory relative to this file.
        """
        if roslyn_tool_path is None:
            # Default to roslyn-tool directory relative to symbol-scanner
            self._roslyn_tool_path = (
                Path(__file__).parent.parent.parent / "roslyn-tool"
            )
        else:
            self._roslyn_tool_path = roslyn_tool_path

        self._built = False

    @property
    def language(self) -> str:
        return "csharp"

    @property
    def file_extensions(self) -> tuple[str, ...]:
        return (".cs",)

    def _ensure_built(self) -> None:
        """Ensure the Roslyn tool is built."""
        if self._built:
            return

        if not self._roslyn_tool_path.exists():
            raise FileNotFoundError(
                f"Roslyn tool not found at {self._roslyn_tool_path}. "
                "Please ensure the roslyn-tool directory exists."
            )

        # Check if build is needed (no bin directory or outdated)
        bin_dir = self._roslyn_tool_path / "bin"
        csproj = self._roslyn_tool_path / "SymbolExtractor.csproj"
        program = self._roslyn_tool_path / "Program.cs"

        needs_build = (
            not bin_dir.exists()
            or not any(bin_dir.rglob("SymbolExtractor.dll"))
            or (csproj.exists() and program.exists() and
                max(csproj.stat().st_mtime, program.stat().st_mtime)
                > bin_dir.stat().st_mtime)
        )

        if needs_build:
            result = subprocess.run(
                ["dotnet", "build", "-c", "Release"],
                cwd=self._roslyn_tool_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"Failed to build Roslyn tool:\n{result.stderr}"
                )

        self._built = True

    def extract_file(self, file_path: Path, relative_path: str) -> ExtractionResult:
        """Extract symbols from a single file.

        Note: For better results, use extract_directory which can perform
        cross-file semantic analysis.

        Args:
            file_path: Absolute path to the file
            relative_path: Repo-relative path for output

        Returns:
            ExtractionResult containing extracted entities
        """
        # For single file extraction, create a temporary directory context
        # The Roslyn tool expects a directory
        return self.extract_directory(
            file_path.parent,
            file_path.parent,
            resolve_calls=False,
        )

    def extract_directory(
        self,
        directory: Path,
        repo_root: Path | None = None,
        exclude_patterns: tuple[str, ...] = ("__pycache__", ".git", ".venv", "venv", "node_modules", "obj", "bin"),
        resolve_calls: bool = True,
    ) -> ExtractionResult:
        """Extract symbols from all C# files in a directory using Roslyn.

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

        self._ensure_built()

        # Run the Roslyn tool
        try:
            proc_result = subprocess.run(
                ["dotnet", "run", "--project", str(self._roslyn_tool_path), "--", str(directory)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
        except subprocess.TimeoutExpired:
            result.errors.append({
                "file": str(directory),
                "message": "Roslyn tool timed out after 5 minutes",
                "code": "TIMEOUT_ERROR",
                "recoverable": False,
            })
            return result
        except FileNotFoundError:
            result.errors.append({
                "file": str(directory),
                "message": "dotnet CLI not found. Please install .NET SDK.",
                "code": "DOTNET_NOT_FOUND",
                "recoverable": False,
            })
            return result

        if proc_result.returncode != 0:
            result.errors.append({
                "file": str(directory),
                "message": f"Roslyn tool failed: {proc_result.stderr}",
                "code": "ROSLYN_ERROR",
                "recoverable": False,
            })
            return result

        # Parse JSON output
        try:
            data = json.loads(proc_result.stdout)
        except json.JSONDecodeError as e:
            result.errors.append({
                "file": str(directory),
                "message": f"Failed to parse Roslyn output: {e}",
                "code": "JSON_PARSE_ERROR",
                "recoverable": False,
            })
            return result

        # Convert Roslyn output to ExtractionResult
        self._parse_roslyn_output(data, result, repo_root, directory)

        # Perform call resolution if requested
        if resolve_calls and result.calls:
            from .call_resolver import CallResolver

            resolver = CallResolver(repo_root, result.symbols, result.imports)
            result.calls = resolver.resolve(result.calls)
            result.resolution_stats = resolver.stats.to_dict()

        return result

    def _parse_roslyn_output(
        self,
        data: dict,
        result: ExtractionResult,
        repo_root: Path,
        directory: Path,
    ) -> None:
        """Parse Roslyn JSON output into ExtractionResult.

        Args:
            data: Parsed JSON from Roslyn tool
            result: ExtractionResult to populate
            repo_root: Repository root for path normalization
            directory: Directory that was analyzed
        """
        # Validate against schema before processing
        try:
            schema = _get_data_schema()
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as e:
            result.errors.append({
                "file": "<roslyn-output>",
                "message": f"Schema validation failed: {e.message}",
                "code": "SCHEMA_ERROR",
                "recoverable": True,
            })
            # Continue processing despite validation error - may still extract useful data

        # Parse symbols
        for sym in data.get("symbols", []):
            path = sym.get("path", "")
            # Make path relative to repo_root if directory != repo_root
            if directory != repo_root:
                try:
                    full_path = directory / path
                    path = str(full_path.relative_to(repo_root))
                except ValueError:
                    pass  # Keep original path
            # Normalize path separators
            path = path.replace("\\", "/")

            result.symbols.append(
                ExtractedSymbol(
                    path=path,
                    symbol_name=sym.get("symbol_name", ""),
                    symbol_type=sym.get("symbol_type", ""),
                    line_start=sym.get("line_start", 1),
                    line_end=sym.get("line_end", 1),
                    is_exported=sym.get("is_exported", True),
                    parameters=sym.get("parameters"),
                    parent_symbol=sym.get("parent_symbol"),
                    docstring=sym.get("docstring"),
                )
            )

        # Parse calls
        for call in data.get("calls", []):
            caller_file = call.get("caller_file", "")
            if directory != repo_root:
                try:
                    full_path = directory / caller_file
                    caller_file = str(full_path.relative_to(repo_root))
                except ValueError:
                    pass
            caller_file = caller_file.replace("\\", "/")

            callee_file = call.get("callee_file")
            if callee_file and directory != repo_root:
                try:
                    full_path = directory / callee_file
                    callee_file = str(full_path.relative_to(repo_root))
                except ValueError:
                    pass
                if callee_file:
                    callee_file = callee_file.replace("\\", "/")

            result.calls.append(
                ExtractedCall(
                    caller_file=caller_file,
                    caller_symbol=call.get("caller_symbol", "<module>"),
                    callee_symbol=call.get("callee_symbol", ""),
                    callee_file=callee_file,
                    line_number=call.get("line_number", 1),
                    call_type=call.get("call_type", "direct"),
                    is_dynamic_code_execution=call.get("is_dynamic_code_execution", False),
                    callee_object=call.get("callee_object"),
                )
            )

        # Parse imports
        for imp in data.get("imports", []):
            file_path = imp.get("file", "")
            if directory != repo_root:
                try:
                    full_path = directory / file_path
                    file_path = str(full_path.relative_to(repo_root))
                except ValueError:
                    pass
            file_path = file_path.replace("\\", "/")

            result.imports.append(
                ExtractedImport(
                    file=file_path,
                    imported_path=imp.get("imported_path", ""),
                    imported_symbols=imp.get("imported_symbols"),
                    import_type=imp.get("import_type", "static"),
                    line_number=imp.get("line_number", 1),
                    module_alias=imp.get("module_alias"),
                )
            )

        # Parse errors
        for err in data.get("errors", []):
            result.errors.append({
                "file": err.get("file", ""),
                "message": err.get("message", ""),
                "code": err.get("code", "UNKNOWN_ERROR"),
                "recoverable": err.get("recoverable", True),
            })
