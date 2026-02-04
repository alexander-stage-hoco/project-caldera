"""Unit tests for C# hybrid extractor."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from extractors.csharp_hybrid_extractor import CSharpHybridExtractor
from extractors.base import ExtractionResult, ExtractedSymbol, ExtractedCall, ExtractedImport


def make_symbol(
    path: str,
    symbol_name: str,
    symbol_type: str = "class",
    line_start: int = 1,
    line_end: int = 10,
    is_exported: bool = True,
    parameters: int | None = None,
    parent_symbol: str | None = None,
    docstring: str | None = None,
) -> ExtractedSymbol:
    """Helper to create ExtractedSymbol with defaults."""
    return ExtractedSymbol(
        path=path,
        symbol_name=symbol_name,
        symbol_type=symbol_type,
        line_start=line_start,
        line_end=line_end,
        is_exported=is_exported,
        parameters=parameters,
        parent_symbol=parent_symbol,
        docstring=docstring,
    )


class TestCSharpHybridExtractor:
    """Tests for CSharpHybridExtractor."""

    @pytest.fixture
    def extractor(self, tmp_path):
        """Create a hybrid extractor with mock roslyn-tool path."""
        roslyn_dir = tmp_path / "roslyn-tool"
        roslyn_dir.mkdir()
        (roslyn_dir / "SymbolExtractor.csproj").write_text("<Project/>")
        (roslyn_dir / "Program.cs").write_text("// Program")
        bin_dir = roslyn_dir / "bin"
        bin_dir.mkdir()
        (bin_dir / "SymbolExtractor.dll").write_text("")

        return CSharpHybridExtractor(roslyn_dir)

    # ============ Basic Properties ============

    def test_language_property(self, extractor):
        assert extractor.language == "csharp"

    def test_file_extensions(self, extractor):
        assert extractor.file_extensions == (".cs",)

    # ============ Single File Extraction ============

    def test_extract_file_uses_treesitter(self, extractor, temp_dir, csharp_class_code):
        """Test that extract_file always uses tree-sitter for efficiency."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        # Mock the tree-sitter extractor to verify it's called
        mock_result = ExtractionResult()
        mock_result.symbols.append(make_symbol("Calculator.cs", "Calculator"))

        with patch.object(
            extractor._treesitter_extractor,
            'extract_file',
            return_value=mock_result
        ) as mock_ts:
            result = extractor.extract_file(test_file, "Calculator.cs")

            mock_ts.assert_called_once_with(test_file, "Calculator.cs")
            assert len(result.symbols) == 1
            assert result.symbols[0].symbol_name == "Calculator"

    # ============ Directory Extraction - Roslyn Success ============

    def test_uses_roslyn_when_available(self, extractor, temp_dir, csharp_class_code):
        """Test that directory extraction uses Roslyn when available."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        # Create mock Roslyn result
        roslyn_result = ExtractionResult()
        roslyn_result.symbols.append(make_symbol("Calculator.cs", "Calculator"))
        roslyn_result.resolution_stats = {"resolved": 5}

        with patch.object(
            extractor._roslyn_extractor,
            '_ensure_built'
        ) as mock_build:
            with patch.object(
                extractor._roslyn_extractor,
                'extract_directory',
                return_value=roslyn_result
            ) as mock_roslyn:
                extractor._roslyn_available = None  # Reset cached state

                result = extractor.extract_directory(temp_dir)

                mock_roslyn.assert_called_once()
                assert len(result.symbols) == 1
                assert result.resolution_stats["extractor"] == "roslyn"

    # ============ Directory Extraction - Fallback to Tree-sitter ============

    def test_falls_back_to_treesitter_when_roslyn_unavailable(
        self, extractor, temp_dir, csharp_class_code
    ):
        """Test fallback to tree-sitter when Roslyn is not available."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        # Create mock tree-sitter result
        ts_result = ExtractionResult()
        ts_result.symbols.append(make_symbol("Calculator.cs", "Calculator"))
        ts_result.resolution_stats = {"resolved": 3}

        with patch.object(
            extractor._roslyn_extractor,
            '_ensure_built',
            side_effect=FileNotFoundError("Roslyn tool not found")
        ):
            with patch.object(
                extractor._treesitter_extractor,
                'extract_directory',
                return_value=ts_result
            ) as mock_ts:
                extractor._roslyn_available = None  # Reset cached state

                result = extractor.extract_directory(temp_dir)

                mock_ts.assert_called_once()
                assert len(result.symbols) == 1
                assert result.resolution_stats["extractor"] == "treesitter"

    def test_falls_back_to_treesitter_on_build_error(
        self, extractor, temp_dir, csharp_class_code
    ):
        """Test fallback to tree-sitter when Roslyn build fails."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        ts_result = ExtractionResult()
        ts_result.symbols.append(make_symbol("Calculator.cs", "Calculator"))
        ts_result.resolution_stats = {"some_stat": 1}  # Non-empty for extractor to be added

        with patch.object(
            extractor._roslyn_extractor,
            '_ensure_built',
            side_effect=RuntimeError("Build failed")
        ):
            with patch.object(
                extractor._treesitter_extractor,
                'extract_directory',
                return_value=ts_result
            ) as mock_ts:
                extractor._roslyn_available = None

                result = extractor.extract_directory(temp_dir)

                mock_ts.assert_called_once()
                assert result.resolution_stats["extractor"] == "treesitter"

    def test_falls_back_on_roslyn_fatal_errors(
        self, extractor, temp_dir, csharp_class_code
    ):
        """Test fallback when Roslyn returns fatal errors."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        # Roslyn result with fatal errors
        roslyn_result = ExtractionResult()
        roslyn_result.errors.append({
            "file": str(temp_dir),
            "message": "Compilation failed",
            "code": "BUILD_ERROR",
            "recoverable": False
        })

        ts_result = ExtractionResult()
        ts_result.symbols.append(make_symbol("Calculator.cs", "Calculator"))
        ts_result.resolution_stats = {}

        with patch.object(
            extractor._roslyn_extractor,
            '_ensure_built'
        ):
            with patch.object(
                extractor._roslyn_extractor,
                'extract_directory',
                return_value=roslyn_result
            ):
                with patch.object(
                    extractor._treesitter_extractor,
                    'extract_directory',
                    return_value=ts_result
                ) as mock_ts:
                    extractor._roslyn_available = None

                    result = extractor.extract_directory(temp_dir)

                    mock_ts.assert_called_once()
                    # Should have fallback error recorded
                    assert any(
                        e["code"] == "ROSLYN_FALLBACK"
                        for e in result.errors
                    )

    def test_falls_back_on_roslyn_exception(
        self, extractor, temp_dir, csharp_class_code
    ):
        """Test fallback when Roslyn raises an exception during extraction."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        ts_result = ExtractionResult()
        ts_result.symbols.append(make_symbol("Calculator.cs", "Calculator"))
        ts_result.resolution_stats = {}

        with patch.object(
            extractor._roslyn_extractor,
            '_ensure_built'
        ):
            with patch.object(
                extractor._roslyn_extractor,
                'extract_directory',
                side_effect=Exception("Unexpected error")
            ):
                with patch.object(
                    extractor._treesitter_extractor,
                    'extract_directory',
                    return_value=ts_result
                ) as mock_ts:
                    extractor._roslyn_available = None

                    result = extractor.extract_directory(temp_dir)

                    mock_ts.assert_called_once()
                    # Should have fallback error recorded
                    assert any(
                        e["code"] == "ROSLYN_FALLBACK"
                        for e in result.errors
                    )

    # ============ Roslyn Availability Caching ============

    def test_records_fallback_in_stats(self, extractor, temp_dir, csharp_class_code):
        """Test that the extractor used is recorded in resolution_stats."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        ts_result = ExtractionResult()
        ts_result.symbols.append(make_symbol("Calculator.cs", "Calculator"))
        ts_result.resolution_stats = {"some_stat": 1}

        # Force tree-sitter path
        extractor._roslyn_available = False

        with patch.object(
            extractor._treesitter_extractor,
            'extract_directory',
            return_value=ts_result
        ):
            result = extractor.extract_directory(temp_dir)

            assert result.resolution_stats["extractor"] == "treesitter"
            assert result.resolution_stats["some_stat"] == 1

    def test_roslyn_availability_cached(self, extractor, temp_dir):
        """Test that Roslyn availability check is cached."""
        # First check - should call _ensure_built
        with patch.object(
            extractor._roslyn_extractor,
            '_ensure_built'
        ) as mock_build:
            extractor._roslyn_available = None
            result1 = extractor._check_roslyn_available()
            mock_build.assert_called_once()

        # Second check - should use cached value
        with patch.object(
            extractor._roslyn_extractor,
            '_ensure_built'
        ) as mock_build:
            result2 = extractor._check_roslyn_available()
            mock_build.assert_not_called()

        assert result1 == result2

    def test_roslyn_availability_cached_as_false(self, extractor, temp_dir):
        """Test that Roslyn unavailability is cached."""
        with patch.object(
            extractor._roslyn_extractor,
            '_ensure_built',
            side_effect=FileNotFoundError("not found")
        ):
            extractor._roslyn_available = None
            result = extractor._check_roslyn_available()
            assert result is False

        # Subsequent calls should return cached False
        assert extractor._check_roslyn_available() is False

    # ============ Error Merging ============

    def test_errors_merged_from_treesitter(self, extractor, temp_dir):
        """Test that tree-sitter errors are included in result."""
        test_file = temp_dir / "Broken.cs"
        test_file.write_text("public class Broken {")  # Syntax error

        ts_result = ExtractionResult()
        ts_result.errors.append({
            "file": "Broken.cs",
            "message": "Syntax error",
            "code": "SYNTAX_ERROR",
            "recoverable": True
        })
        ts_result.resolution_stats = {}

        extractor._roslyn_available = False

        with patch.object(
            extractor._treesitter_extractor,
            'extract_directory',
            return_value=ts_result
        ):
            result = extractor.extract_directory(temp_dir)

            assert any(
                e["code"] == "SYNTAX_ERROR"
                for e in result.errors
            )

    # ============ Result Merging ============

    def test_symbols_calls_imports_merged(self, extractor, temp_dir):
        """Test that symbols, calls, and imports are correctly merged from tree-sitter."""
        test_file = temp_dir / "Test.cs"
        test_file.write_text("using System;\npublic class Test { void Method() { Console.WriteLine(); } }")

        ts_result = ExtractionResult()
        ts_result.symbols.append(make_symbol("Test.cs", "Test", line_start=2, line_end=2))
        ts_result.calls.append(ExtractedCall(
            caller_file="Test.cs",
            caller_symbol="Method",
            callee_symbol="WriteLine",
            callee_file=None,
            line_number=2,
            call_type="dynamic",
            is_dynamic_code_execution=False,
            callee_object="Console",
        ))
        ts_result.imports.append(ExtractedImport(
            file="Test.cs",
            imported_path="System",
            imported_symbols=None,
            import_type="static",
            line_number=1,
        ))
        ts_result.resolution_stats = {"resolved": 1}

        extractor._roslyn_available = False

        with patch.object(
            extractor._treesitter_extractor,
            'extract_directory',
            return_value=ts_result
        ):
            result = extractor.extract_directory(temp_dir)

            assert len(result.symbols) == 1
            assert result.symbols[0].symbol_name == "Test"
            assert len(result.calls) == 1
            assert result.calls[0].callee_symbol == "WriteLine"
            assert len(result.imports) == 1
            assert result.imports[0].imported_path == "System"


class TestCSharpHybridExtractorIntegration:
    """Integration tests for CSharpHybridExtractor.

    These tests use the actual tree-sitter extractor.
    """

    @pytest.fixture
    def hybrid_extractor(self, tmp_path):
        """Create a hybrid extractor that will use tree-sitter fallback."""
        # Use non-existent path to force tree-sitter fallback
        return CSharpHybridExtractor(tmp_path / "non-existent-roslyn")

    def test_integration_single_file(
        self, hybrid_extractor, temp_dir, csharp_class_code
    ):
        """Integration test: Extract single file (uses tree-sitter)."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        result = hybrid_extractor.extract_file(test_file, "Calculator.cs")

        # Should find the class using tree-sitter
        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "Calculator"

    def test_integration_directory_treesitter_fallback(
        self, hybrid_extractor, temp_dir, csharp_class_code
    ):
        """Integration test: Directory extraction falls back to tree-sitter."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        result = hybrid_extractor.extract_directory(temp_dir)

        # Should find the class using tree-sitter fallback
        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "Calculator"

        # Verify tree-sitter was used (either no stats or stats show treesitter)
        if result.resolution_stats:
            assert result.resolution_stats.get("extractor") == "treesitter"

    def test_integration_multi_file(
        self, hybrid_extractor, csharp_cross_file_repo
    ):
        """Integration test: Multi-file extraction with tree-sitter fallback."""
        result = hybrid_extractor.extract_directory(csharp_cross_file_repo)

        # Should find classes from all files
        class_names = {s.symbol_name for s in result.symbols if s.symbol_type == "class"}
        assert "User" in class_names
        assert "UserService" in class_names
        assert "Program" in class_names

        # Should find imports
        import_paths = {i.imported_path for i in result.imports}
        assert "MyApp.Models" in import_paths
        assert "MyApp.Services" in import_paths
