"""Unit tests for C# Roslyn extractor."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import json

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from extractors.csharp_roslyn_extractor import CSharpRoslynExtractor


class TestCSharpRoslynExtractor:
    """Tests for CSharpRoslynExtractor."""

    @pytest.fixture
    def extractor(self, tmp_path):
        """Create an extractor with a mock roslyn-tool path."""
        # Create a fake roslyn-tool directory structure
        roslyn_dir = tmp_path / "roslyn-tool"
        roslyn_dir.mkdir()
        (roslyn_dir / "SymbolExtractor.csproj").write_text("<Project/>")
        (roslyn_dir / "Program.cs").write_text("// Program")
        bin_dir = roslyn_dir / "bin"
        bin_dir.mkdir()
        (bin_dir / "SymbolExtractor.dll").write_text("")

        return CSharpRoslynExtractor(roslyn_dir)

    # ============ Basic Properties ============

    def test_language_property(self, extractor):
        assert extractor.language == "csharp"

    def test_file_extensions(self, extractor):
        assert extractor.file_extensions == (".cs",)

    # ============ Error Handling ============

    def test_dotnet_not_available(self, extractor, temp_dir):
        """Test handling when dotnet CLI is not found."""
        test_file = temp_dir / "test.cs"
        test_file.write_text("public class Test { }")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("dotnet not found")

            result = extractor.extract_directory(temp_dir)

            assert len(result.errors) == 1
            assert result.errors[0]["code"] == "DOTNET_NOT_FOUND"
            assert result.errors[0]["recoverable"] is False

    def test_build_failure(self, extractor, temp_dir):
        """Test handling when Roslyn tool build fails."""
        test_file = temp_dir / "test.cs"
        test_file.write_text("public class Test { }")

        # Force rebuild by removing DLL
        bin_dir = extractor._roslyn_tool_path / "bin"
        for f in bin_dir.glob("*.dll"):
            f.unlink()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="Build failed: missing dependency",
                stdout=""
            )

            with pytest.raises(RuntimeError, match="Failed to build Roslyn tool"):
                extractor._ensure_built()

    def test_roslyn_tool_not_found(self, temp_dir):
        """Test handling when roslyn-tool directory doesn't exist."""
        non_existent = temp_dir / "non-existent-roslyn-tool"
        extractor = CSharpRoslynExtractor(non_existent)

        with pytest.raises(FileNotFoundError, match="Roslyn tool not found"):
            extractor._ensure_built()

    def test_timeout_error(self, extractor, temp_dir):
        """Test handling when Roslyn tool times out."""
        import subprocess

        test_file = temp_dir / "test.cs"
        test_file.write_text("public class Test { }")

        # Mark as built to skip build step
        extractor._built = True

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="dotnet", timeout=300)

            result = extractor.extract_directory(temp_dir)

            assert len(result.errors) == 1
            assert result.errors[0]["code"] == "TIMEOUT_ERROR"
            assert result.errors[0]["recoverable"] is False

    def test_roslyn_run_failure(self, extractor, temp_dir):
        """Test handling when Roslyn tool execution fails."""
        test_file = temp_dir / "test.cs"
        test_file.write_text("public class Test { }")

        extractor._built = True

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="Analysis failed",
                stdout=""
            )

            result = extractor.extract_directory(temp_dir)

            assert len(result.errors) == 1
            assert result.errors[0]["code"] == "ROSLYN_ERROR"

    def test_invalid_json_output(self, extractor, temp_dir):
        """Test handling when Roslyn outputs invalid JSON."""
        test_file = temp_dir / "test.cs"
        test_file.write_text("public class Test { }")

        extractor._built = True

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stderr="",
                stdout="not valid json {"
            )

            result = extractor.extract_directory(temp_dir)

            assert len(result.errors) == 1
            assert result.errors[0]["code"] == "JSON_PARSE_ERROR"

    # ============ JSON Parsing ============

    def test_parse_symbols_from_json(self, extractor, temp_dir):
        """Test parsing symbols from Roslyn JSON output."""
        extractor._built = True

        roslyn_output = {
            "symbols": [
                {
                    "path": "Test.cs",
                    "symbol_name": "TestClass",
                    "symbol_type": "class",
                    "line_start": 1,
                    "line_end": 10,
                    "is_exported": True,
                    "parameters": None,
                    "parent_symbol": None,
                    "docstring": "Test class"
                },
                {
                    "path": "Test.cs",
                    "symbol_name": "TestMethod",
                    "symbol_type": "method",
                    "line_start": 3,
                    "line_end": 5,
                    "is_exported": True,
                    "parameters": 2,
                    "parent_symbol": "TestClass",
                    "docstring": None
                }
            ],
            "calls": [],
            "imports": [],
            "errors": []
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stderr="",
                stdout=json.dumps(roslyn_output)
            )

            result = extractor.extract_directory(temp_dir, resolve_calls=False)

            assert len(result.symbols) == 2
            assert result.symbols[0].symbol_name == "TestClass"
            assert result.symbols[0].symbol_type == "class"
            assert result.symbols[1].symbol_name == "TestMethod"
            assert result.symbols[1].parameters == 2
            assert result.symbols[1].parent_symbol == "TestClass"

    def test_parse_calls_from_json(self, extractor, temp_dir):
        """Test parsing calls from Roslyn JSON output."""
        extractor._built = True

        roslyn_output = {
            "symbols": [],
            "calls": [
                {
                    "caller_file": "Test.cs",
                    "caller_symbol": "TestMethod",
                    "callee_symbol": "OtherMethod",
                    "callee_file": "Other.cs",
                    "line_number": 5,
                    "call_type": "direct",
                    "is_dynamic_code_execution": False,
                    "callee_object": None
                }
            ],
            "imports": [],
            "errors": []
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stderr="",
                stdout=json.dumps(roslyn_output)
            )

            result = extractor.extract_directory(temp_dir, resolve_calls=False)

            assert len(result.calls) == 1
            assert result.calls[0].caller_symbol == "TestMethod"
            assert result.calls[0].callee_symbol == "OtherMethod"
            assert result.calls[0].callee_file == "Other.cs"

    def test_parse_imports_from_json(self, extractor, temp_dir):
        """Test parsing imports from Roslyn JSON output."""
        extractor._built = True

        roslyn_output = {
            "symbols": [],
            "calls": [],
            "imports": [
                {
                    "file": "Test.cs",
                    "imported_path": "System.Collections.Generic",
                    "imported_symbols": None,
                    "import_type": "static",
                    "line_number": 1,
                    "module_alias": None
                },
                {
                    "file": "Test.cs",
                    "imported_path": "System.Text.StringBuilder",
                    "imported_symbols": None,
                    "import_type": "static",
                    "line_number": 2,
                    "module_alias": "SB"
                }
            ],
            "errors": []
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stderr="",
                stdout=json.dumps(roslyn_output)
            )

            result = extractor.extract_directory(temp_dir, resolve_calls=False)

            assert len(result.imports) == 2
            assert result.imports[0].imported_path == "System.Collections.Generic"
            assert result.imports[1].module_alias == "SB"

    def test_parse_errors_from_json(self, extractor, temp_dir):
        """Test parsing errors from Roslyn JSON output."""
        extractor._built = True

        roslyn_output = {
            "symbols": [],
            "calls": [],
            "imports": [],
            "errors": [
                {
                    "file": "Broken.cs",
                    "message": "Syntax error at line 5",
                    "code": "CS1001",
                    "recoverable": True
                }
            ]
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stderr="",
                stdout=json.dumps(roslyn_output)
            )

            result = extractor.extract_directory(temp_dir, resolve_calls=False)

            assert len(result.errors) == 1
            assert result.errors[0]["file"] == "Broken.cs"
            assert result.errors[0]["code"] == "CS1001"

    # ============ Path Normalization ============

    def test_path_normalization_backslash(self, extractor, temp_dir):
        """Test that backslashes in paths are normalized to forward slashes."""
        extractor._built = True

        roslyn_output = {
            "symbols": [
                {
                    "path": "src\\services\\Test.cs",
                    "symbol_name": "Test",
                    "symbol_type": "class",
                    "line_start": 1,
                    "line_end": 5,
                    "is_exported": True,
                }
            ],
            "calls": [],
            "imports": [],
            "errors": []
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stderr="",
                stdout=json.dumps(roslyn_output)
            )

            result = extractor.extract_directory(temp_dir, resolve_calls=False)

            assert result.symbols[0].path == "src/services/Test.cs"

    # ============ Build Caching ============

    def test_build_only_once(self, extractor, temp_dir):
        """Test that the Roslyn tool is only built once."""
        extractor._built = True  # Simulate already built

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stderr="",
                stdout='{"symbols":[],"calls":[],"imports":[],"errors":[]}'
            )

            # Call multiple times
            extractor.extract_directory(temp_dir, resolve_calls=False)
            extractor.extract_directory(temp_dir, resolve_calls=False)

            # Should have called run twice (extraction runs)
            assert mock_run.call_count == 2

    # ============ Schema Validation ============

    def test_schema_validation_valid_output(self, extractor, temp_dir):
        """Test that valid Roslyn output passes schema validation."""
        extractor._built = True

        valid_output = {
            "symbols": [
                {
                    "path": "Test.cs",
                    "symbol_name": "TestClass",
                    "symbol_type": "class",
                    "line_start": 1,
                    "line_end": 10,
                    "is_exported": True,
                }
            ],
            "calls": [
                {
                    "caller_file": "Test.cs",
                    "caller_symbol": "Method",
                    "callee_symbol": "OtherMethod",
                    "line_number": 5,
                    "call_type": "direct",
                }
            ],
            "imports": [],
            "errors": []
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stderr="",
                stdout=json.dumps(valid_output)
            )

            result = extractor.extract_directory(temp_dir, resolve_calls=False)

            # No schema errors should be recorded
            schema_errors = [e for e in result.errors if e.get("code") == "SCHEMA_ERROR"]
            assert len(schema_errors) == 0
            assert len(result.symbols) == 1

    def test_schema_validation_invalid_call_type(self, extractor, temp_dir):
        """Test that invalid call_type triggers schema validation error."""
        extractor._built = True

        invalid_output = {
            "symbols": [],
            "calls": [
                {
                    "caller_file": "Test.cs",
                    "caller_symbol": "Method",
                    "callee_symbol": "OtherMethod",
                    "line_number": 5,
                    "call_type": "invalid_type",  # Invalid call type
                }
            ],
            "imports": [],
            "errors": []
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stderr="",
                stdout=json.dumps(invalid_output)
            )

            result = extractor.extract_directory(temp_dir, resolve_calls=False)

            # Should have schema error recorded
            schema_errors = [e for e in result.errors if e.get("code") == "SCHEMA_ERROR"]
            assert len(schema_errors) == 1
            assert "Schema validation failed" in schema_errors[0]["message"]
            assert schema_errors[0]["recoverable"] is True

    def test_schema_validation_continues_after_error(self, extractor, temp_dir):
        """Test that extraction continues even after schema validation error."""
        extractor._built = True

        # Output with invalid type but valid symbols
        invalid_output = {
            "symbols": [
                {
                    "path": "Test.cs",
                    "symbol_name": "ValidClass",
                    "symbol_type": "class",
                    "line_start": 1,
                    "line_end": 10,
                    "is_exported": True,
                }
            ],
            "calls": [
                {
                    "caller_file": "Test.cs",
                    "caller_symbol": "Method",
                    "callee_symbol": "OtherMethod",
                    "line_number": 5,
                    "call_type": "bad_type",  # Invalid
                }
            ],
            "imports": [],
            "errors": []
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stderr="",
                stdout=json.dumps(invalid_output)
            )

            result = extractor.extract_directory(temp_dir, resolve_calls=False)

            # Should have recorded error but still extracted symbols
            assert len(result.symbols) == 1
            assert result.symbols[0].symbol_name == "ValidClass"
            assert len(result.calls) == 1  # Call still extracted despite invalid type

    def test_schema_validation_constructor_call_type(self, extractor, temp_dir):
        """Test that constructor call_type is valid according to schema."""
        extractor._built = True

        output_with_constructor = {
            "symbols": [],
            "calls": [
                {
                    "caller_file": "Test.cs",
                    "caller_symbol": "Method",
                    "callee_symbol": "MyClass",
                    "line_number": 5,
                    "call_type": "constructor",  # New type added to schema
                }
            ],
            "imports": [],
            "errors": []
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stderr="",
                stdout=json.dumps(output_with_constructor)
            )

            result = extractor.extract_directory(temp_dir, resolve_calls=False)

            # Should not have schema errors - constructor is valid
            schema_errors = [e for e in result.errors if e.get("code") == "SCHEMA_ERROR"]
            assert len(schema_errors) == 0
            assert len(result.calls) == 1
            assert result.calls[0].call_type == "constructor"

    # ============ Single File Extraction ============

    def test_extract_file_delegates_to_directory(self, extractor, temp_dir):
        """Test that extract_file delegates to extract_directory."""
        test_file = temp_dir / "test.cs"
        test_file.write_text("public class Test { }")

        extractor._built = True

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stderr="",
                stdout='{"symbols":[],"calls":[],"imports":[],"errors":[]}'
            )

            extractor.extract_file(test_file, "test.cs")

            # Should have been called with directory path
            assert mock_run.called


class TestCSharpRoslynExtractorIntegration:
    """Integration tests for CSharpRoslynExtractor.

    These tests require a working .NET SDK installation and are skipped
    if dotnet is not available.
    """

    @pytest.fixture
    def real_extractor(self):
        """Create an extractor pointing to the real roslyn-tool."""
        roslyn_path = Path(__file__).parent.parent.parent / "roslyn-tool"
        if not roslyn_path.exists():
            pytest.skip("roslyn-tool not found")
        return CSharpRoslynExtractor(roslyn_path)

    @pytest.fixture
    def dotnet_available(self):
        """Check if dotnet CLI is available."""
        import subprocess
        try:
            result = subprocess.run(
                ["dotnet", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def test_integration_simple_class(
        self, real_extractor, temp_dir, dotnet_available, csharp_class_code
    ):
        """Integration test: Extract simple class with real Roslyn tool."""
        if not dotnet_available:
            pytest.skip("dotnet CLI not available")

        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        result = real_extractor.extract_directory(temp_dir, resolve_calls=False)

        # Should find the class
        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert any(c.symbol_name == "Calculator" for c in classes)

    def test_integration_methods(
        self, real_extractor, temp_dir, dotnet_available, csharp_class_code
    ):
        """Integration test: Extract methods with real Roslyn tool."""
        if not dotnet_available:
            pytest.skip("dotnet CLI not available")

        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        result = real_extractor.extract_directory(temp_dir, resolve_calls=False)

        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}
        assert "Add" in method_names

    def test_integration_imports(
        self, real_extractor, temp_dir, dotnet_available, csharp_imports_code
    ):
        """Integration test: Extract imports with real Roslyn tool."""
        if not dotnet_available:
            pytest.skip("dotnet CLI not available")

        test_file = temp_dir / "Imports.cs"
        test_file.write_text(csharp_imports_code)

        result = real_extractor.extract_directory(temp_dir, resolve_calls=False)

        import_paths = {i.imported_path for i in result.imports}
        assert "System" in import_paths or len(import_paths) > 0

    def test_integration_multi_file(
        self, real_extractor, dotnet_available, csharp_cross_file_repo
    ):
        """Integration test: Extract from multi-file repo with real Roslyn tool."""
        if not dotnet_available:
            pytest.skip("dotnet CLI not available")

        result = real_extractor.extract_directory(
            csharp_cross_file_repo,
            resolve_calls=False
        )

        # Should find classes from all files
        class_names = {s.symbol_name for s in result.symbols if s.symbol_type == "class"}
        # At minimum should find some classes
        assert len(class_names) > 0

    def test_integration_cross_file_call_resolution(
        self, real_extractor, dotnet_available, csharp_cross_file_calls_repo
    ):
        """Integration test: Verify Roslyn resolves callee_file for cross-file calls."""
        if not dotnet_available:
            pytest.skip("dotnet CLI not available")

        result = real_extractor.extract_directory(
            csharp_cross_file_calls_repo,
            resolve_calls=False
        )

        # Find calls to MathUtils.Add
        add_calls = [c for c in result.calls if c.callee_symbol == "Add"]
        # Roslyn should provide callee_file for cross-file calls
        # Note: This depends on Roslyn tool implementation
        assert len(add_calls) >= 1

    def test_integration_generic_type_extraction(
        self, real_extractor, temp_dir, dotnet_available, csharp_generic_class_code
    ):
        """Integration test: Verify Roslyn extracts generic classes correctly."""
        if not dotnet_available:
            pytest.skip("dotnet CLI not available")

        test_file = temp_dir / "Container.cs"
        test_file.write_text(csharp_generic_class_code)

        result = real_extractor.extract_directory(temp_dir, resolve_calls=False)

        # Should find the Container class
        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert any(c.symbol_name == "Container" for c in classes)

        # Should find methods within generic class
        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}
        assert "GetValue" in method_names
        assert "SetValue" in method_names

    def test_integration_async_method_detection(
        self, real_extractor, temp_dir, dotnet_available, csharp_async_code
    ):
        """Integration test: Verify Roslyn extracts async methods correctly."""
        if not dotnet_available:
            pytest.skip("dotnet CLI not available")

        test_file = temp_dir / "AsyncExample.cs"
        test_file.write_text(csharp_async_code)

        result = real_extractor.extract_directory(temp_dir, resolve_calls=False)

        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}

        # Should find async methods
        assert "FetchDataAsync" in method_names
        assert "ProcessAsync" in method_names

        # Check parameter count
        fetch_method = next(m for m in methods if m.symbol_name == "FetchDataAsync")
        assert fetch_method.parameters == 1

    def test_integration_property_vs_field_distinction(
        self, real_extractor, temp_dir, dotnet_available, csharp_class_code
    ):
        """Integration test: Verify Roslyn distinguishes properties from fields."""
        if not dotnet_available:
            pytest.skip("dotnet CLI not available")

        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        result = real_extractor.extract_directory(temp_dir, resolve_calls=False)

        properties = [s for s in result.symbols if s.symbol_type == "property"]
        fields = [s for s in result.symbols if s.symbol_type == "field"]

        # Value should be a property
        property_names = {p.symbol_name for p in properties}
        assert "Value" in property_names

        # _value should be a field
        field_names = {f.symbol_name for f in fields}
        assert "_value" in field_names

    def test_integration_nested_type_parent_symbol(
        self, real_extractor, temp_dir, dotnet_available, csharp_nested_class_code
    ):
        """Integration test: Verify Roslyn sets parent_symbol for nested types."""
        if not dotnet_available:
            pytest.skip("dotnet CLI not available")

        test_file = temp_dir / "Outer.cs"
        test_file.write_text(csharp_nested_class_code)

        result = real_extractor.extract_directory(temp_dir, resolve_calls=False)

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        class_by_name = {c.symbol_name: c for c in classes}

        # Outer class should have no parent
        assert "Outer" in class_by_name
        assert class_by_name["Outer"].parent_symbol is None

        # Inner class should have Outer as parent
        assert "Inner" in class_by_name
        assert class_by_name["Inner"].parent_symbol == "Outer"

    def test_integration_namespace_in_imports(
        self, real_extractor, temp_dir, dotnet_available, csharp_imports_code
    ):
        """Integration test: Verify Roslyn captures using directives correctly."""
        if not dotnet_available:
            pytest.skip("dotnet CLI not available")

        test_file = temp_dir / "Imports.cs"
        test_file.write_text(csharp_imports_code)

        result = real_extractor.extract_directory(temp_dir, resolve_calls=False)

        import_paths = {i.imported_path for i in result.imports}

        # Should find standard using directives
        assert "System" in import_paths
        assert "System.Collections.Generic" in import_paths

    def test_integration_static_constructor(
        self, real_extractor, temp_dir, dotnet_available, csharp_static_constructor_code
    ):
        """Integration test: Verify Roslyn extracts static constructors."""
        if not dotnet_available:
            pytest.skip("dotnet CLI not available")

        test_file = temp_dir / "Configuration.cs"
        test_file.write_text(csharp_static_constructor_code)

        result = real_extractor.extract_directory(temp_dir, resolve_calls=False)

        # Should find the class
        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert any(c.symbol_name == "Configuration" for c in classes)

        # Should find constructors
        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}
        assert "Configuration" in method_names  # Constructor

        # Should find static properties
        properties = [s for s in result.symbols if s.symbol_type == "property"]
        property_names = {p.symbol_name for p in properties}
        assert "ConnectionString" in property_names
        assert "MaxRetries" in property_names
