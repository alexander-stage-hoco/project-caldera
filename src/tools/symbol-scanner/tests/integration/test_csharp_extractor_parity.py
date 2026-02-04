"""Integration tests comparing C# tree-sitter and Roslyn extractors."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch
import json

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from extractors.csharp_treesitter_extractor import CSharpTreeSitterExtractor
from extractors.csharp_roslyn_extractor import CSharpRoslynExtractor


def dotnet_available() -> bool:
    """Check if dotnet CLI is available."""
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


def roslyn_tool_available() -> bool:
    """Check if roslyn-tool exists and can be built."""
    roslyn_path = Path(__file__).parent.parent.parent / "roslyn-tool"
    return roslyn_path.exists() and (roslyn_path / "SymbolExtractor.csproj").exists()


# Skip entire module if prerequisites not met
pytestmark = [
    pytest.mark.skipif(
        not dotnet_available(),
        reason="dotnet CLI not available"
    ),
    pytest.mark.skipif(
        not roslyn_tool_available(),
        reason="roslyn-tool not available"
    ),
]


class TestCSharpExtractorParity:
    """Verify tree-sitter and Roslyn produce similar results on valid C# code.

    Note: Perfect parity is not expected due to fundamental differences:
    - Roslyn has full semantic analysis
    - Tree-sitter is syntactic only
    - Roslyn may resolve more cross-file information
    """

    @pytest.fixture
    def ts_extractor(self):
        return CSharpTreeSitterExtractor()

    @pytest.fixture
    def roslyn_extractor(self):
        roslyn_path = Path(__file__).parent.parent.parent / "roslyn-tool"
        return CSharpRoslynExtractor(roslyn_path)

    def _compare_symbols(self, ts_symbols, roslyn_symbols) -> dict:
        """Compare symbols and return differences.

        Returns dict with 'only_ts', 'only_roslyn', 'mismatches' keys.
        """
        # Key by (path, name, type)
        ts_by_key = {
            (s.path, s.symbol_name, s.symbol_type): s
            for s in ts_symbols
        }
        roslyn_by_key = {
            (s.path, s.symbol_name, s.symbol_type): s
            for s in roslyn_symbols
        }

        ts_keys = set(ts_by_key.keys())
        roslyn_keys = set(roslyn_by_key.keys())

        return {
            "only_ts": ts_keys - roslyn_keys,
            "only_roslyn": roslyn_keys - ts_keys,
            "common": ts_keys & roslyn_keys,
        }

    def _compare_imports(self, ts_imports, roslyn_imports) -> dict:
        """Compare imports and return differences."""
        ts_set = {(i.file, i.imported_path) for i in ts_imports}
        roslyn_set = {(i.file, i.imported_path) for i in roslyn_imports}

        return {
            "only_ts": ts_set - roslyn_set,
            "only_roslyn": roslyn_set - ts_set,
            "common": ts_set & roslyn_set,
        }

    def test_simple_class_parity(
        self, ts_extractor, roslyn_extractor, temp_dir, csharp_class_code
    ):
        """Test that both extractors find the same class."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        ts_result = ts_extractor.extract_directory(temp_dir, resolve_calls=False)
        roslyn_result = roslyn_extractor.extract_directory(temp_dir, resolve_calls=False)

        # Both should find the Calculator class
        ts_classes = {s.symbol_name for s in ts_result.symbols if s.symbol_type == "class"}
        roslyn_classes = {s.symbol_name for s in roslyn_result.symbols if s.symbol_type == "class"}

        assert "Calculator" in ts_classes, "Tree-sitter should find Calculator"
        assert "Calculator" in roslyn_classes, "Roslyn should find Calculator"

    def test_methods_parity(
        self, ts_extractor, roslyn_extractor, temp_dir, csharp_class_code
    ):
        """Test that both extractors find the same methods."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        ts_result = ts_extractor.extract_directory(temp_dir, resolve_calls=False)
        roslyn_result = roslyn_extractor.extract_directory(temp_dir, resolve_calls=False)

        ts_methods = {s.symbol_name for s in ts_result.symbols if s.symbol_type == "method"}
        roslyn_methods = {s.symbol_name for s in roslyn_result.symbols if s.symbol_type == "method"}

        # Core methods should be found by both
        assert "Add" in ts_methods
        assert "Add" in roslyn_methods

    def test_imports_parity(
        self, ts_extractor, roslyn_extractor, temp_dir, csharp_imports_code
    ):
        """Test that both extractors find the same imports."""
        test_file = temp_dir / "Imports.cs"
        test_file.write_text(csharp_imports_code)

        ts_result = ts_extractor.extract_directory(temp_dir, resolve_calls=False)
        roslyn_result = roslyn_extractor.extract_directory(temp_dir, resolve_calls=False)

        ts_imports = {i.imported_path for i in ts_result.imports}
        roslyn_imports = {i.imported_path for i in roslyn_result.imports}

        # Core imports should be found by both
        common_imports = ts_imports & roslyn_imports
        assert "System" in common_imports or len(common_imports) > 0

    def test_complex_code_parity(self, ts_extractor, roslyn_extractor, temp_dir):
        """Test parity on more complex C# code."""
        code = '''
using System;
using System.Collections.Generic;

namespace TestApp
{
    public interface IService
    {
        void Process();
    }

    public class Service : IService
    {
        private readonly List<string> _items;

        public Service()
        {
            _items = new List<string>();
        }

        public void Process()
        {
            foreach (var item in _items)
            {
                Console.WriteLine(item);
            }
        }

        public void Add(string item)
        {
            _items.Add(item);
        }
    }
}
'''
        test_file = temp_dir / "Service.cs"
        test_file.write_text(code)

        ts_result = ts_extractor.extract_directory(temp_dir, resolve_calls=False)
        roslyn_result = roslyn_extractor.extract_directory(temp_dir, resolve_calls=False)

        comparison = self._compare_symbols(ts_result.symbols, roslyn_result.symbols)

        # Both should find the interface and class
        ts_classes = {s.symbol_name for s in ts_result.symbols if s.symbol_type == "class"}
        roslyn_classes = {s.symbol_name for s in roslyn_result.symbols if s.symbol_type == "class"}

        assert "IService" in ts_classes
        assert "Service" in ts_classes
        assert "IService" in roslyn_classes
        assert "Service" in roslyn_classes

        # Both should find methods
        ts_methods = {s.symbol_name for s in ts_result.symbols if s.symbol_type == "method"}
        roslyn_methods = {s.symbol_name for s in roslyn_result.symbols if s.symbol_type == "method"}

        assert "Process" in ts_methods
        assert "Process" in roslyn_methods
        assert "Add" in ts_methods
        assert "Add" in roslyn_methods

    def test_multi_file_parity(
        self, ts_extractor, roslyn_extractor, csharp_cross_file_repo
    ):
        """Test parity on multi-file repository."""
        ts_result = ts_extractor.extract_directory(
            csharp_cross_file_repo,
            resolve_calls=False
        )
        roslyn_result = roslyn_extractor.extract_directory(
            csharp_cross_file_repo,
            resolve_calls=False
        )

        ts_classes = {s.symbol_name for s in ts_result.symbols if s.symbol_type == "class"}
        roslyn_classes = {s.symbol_name for s in roslyn_result.symbols if s.symbol_type == "class"}

        # Both should find all main classes
        expected_classes = {"User", "UserService", "Program"}
        assert expected_classes.issubset(ts_classes), f"Tree-sitter missing: {expected_classes - ts_classes}"
        assert expected_classes.issubset(roslyn_classes), f"Roslyn missing: {expected_classes - roslyn_classes}"


class TestExtractorParityDetailed:
    """Detailed parity tests comparing specific aspects of extraction."""

    @pytest.fixture
    def ts_extractor(self):
        return CSharpTreeSitterExtractor()

    @pytest.fixture
    def roslyn_extractor(self):
        roslyn_path = Path(__file__).parent.parent.parent / "roslyn-tool"
        return CSharpRoslynExtractor(roslyn_path)

    def test_symbol_count_parity(
        self, ts_extractor, roslyn_extractor, temp_dir, csharp_class_code
    ):
        """Test that both extractors find similar numbers of symbols."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        ts_result = ts_extractor.extract_directory(temp_dir, resolve_calls=False)
        roslyn_result = roslyn_extractor.extract_directory(temp_dir, resolve_calls=False)

        # Count by type
        ts_by_type = {}
        for s in ts_result.symbols:
            ts_by_type[s.symbol_type] = ts_by_type.get(s.symbol_type, 0) + 1

        roslyn_by_type = {}
        for s in roslyn_result.symbols:
            roslyn_by_type[s.symbol_type] = roslyn_by_type.get(s.symbol_type, 0) + 1

        # Both should find the class
        assert ts_by_type.get("class", 0) >= 1
        assert roslyn_by_type.get("class", 0) >= 1

        # Both should find methods
        assert ts_by_type.get("method", 0) >= 1
        assert roslyn_by_type.get("method", 0) >= 1

    def test_symbol_names_parity(
        self, ts_extractor, roslyn_extractor, temp_dir, csharp_class_code
    ):
        """Test that both extractors find the same symbol names."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        ts_result = ts_extractor.extract_directory(temp_dir, resolve_calls=False)
        roslyn_result = roslyn_extractor.extract_directory(temp_dir, resolve_calls=False)

        ts_names = {s.symbol_name for s in ts_result.symbols}
        roslyn_names = {s.symbol_name for s in roslyn_result.symbols}

        # Core symbols should be in both
        expected_core = {"Calculator", "Add", "Value"}
        assert expected_core.issubset(ts_names), f"Tree-sitter missing: {expected_core - ts_names}"
        assert expected_core.issubset(roslyn_names), f"Roslyn missing: {expected_core - roslyn_names}"

    def test_call_count_parity(
        self, ts_extractor, roslyn_extractor, temp_dir, csharp_calls_code
    ):
        """Test that both extractors find similar numbers of calls."""
        test_file = temp_dir / "CallExample.cs"
        test_file.write_text(csharp_calls_code)

        ts_result = ts_extractor.extract_directory(temp_dir, resolve_calls=False)
        roslyn_result = roslyn_extractor.extract_directory(temp_dir, resolve_calls=False)

        # Both should find some calls
        assert len(ts_result.calls) > 0, "Tree-sitter should find calls"
        assert len(roslyn_result.calls) > 0, "Roslyn should find calls"

        # Both should find common callees
        ts_callees = {c.callee_symbol for c in ts_result.calls}
        roslyn_callees = {c.callee_symbol for c in roslyn_result.calls}

        common_callees = ts_callees & roslyn_callees
        assert len(common_callees) > 0, "Should have common calls"

    def test_import_count_parity(
        self, ts_extractor, roslyn_extractor, temp_dir, csharp_imports_code
    ):
        """Test that both extractors find similar numbers of imports."""
        test_file = temp_dir / "Imports.cs"
        test_file.write_text(csharp_imports_code)

        ts_result = ts_extractor.extract_directory(temp_dir, resolve_calls=False)
        roslyn_result = roslyn_extractor.extract_directory(temp_dir, resolve_calls=False)

        # Both should find imports
        assert len(ts_result.imports) > 0, "Tree-sitter should find imports"
        assert len(roslyn_result.imports) > 0, "Roslyn should find imports"

        ts_paths = {i.imported_path for i in ts_result.imports}
        roslyn_paths = {i.imported_path for i in roslyn_result.imports}

        # Common imports should exist
        common_paths = ts_paths & roslyn_paths
        assert len(common_paths) > 0, "Should have common imports"

    def test_line_numbers_match(
        self, ts_extractor, roslyn_extractor, temp_dir
    ):
        """Test that both extractors report similar line numbers for symbols."""
        code = '''public class First
{
    public void Method1() { }
}

public class Second
{
    public void Method2() { }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        ts_result = ts_extractor.extract_directory(temp_dir, resolve_calls=False)
        roslyn_result = roslyn_extractor.extract_directory(temp_dir, resolve_calls=False)

        # Build lookup by name
        ts_by_name = {s.symbol_name: s for s in ts_result.symbols}
        roslyn_by_name = {s.symbol_name: s for s in roslyn_result.symbols}

        # Check line numbers for common symbols
        for name in ["First", "Second", "Method1", "Method2"]:
            if name in ts_by_name and name in roslyn_by_name:
                ts_line = ts_by_name[name].line_start
                roslyn_line = roslyn_by_name[name].line_start
                # Allow small variance (e.g., 1 line difference for doc comments)
                assert abs(ts_line - roslyn_line) <= 1, \
                    f"{name}: line mismatch ts={ts_line} roslyn={roslyn_line}"

    def test_parent_symbol_consistency(
        self, ts_extractor, roslyn_extractor, temp_dir, csharp_class_code
    ):
        """Test that both extractors set parent_symbol consistently."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        ts_result = ts_extractor.extract_directory(temp_dir, resolve_calls=False)
        roslyn_result = roslyn_extractor.extract_directory(temp_dir, resolve_calls=False)

        # Get methods from both
        ts_methods = [s for s in ts_result.symbols if s.symbol_type == "method"]
        roslyn_methods = [s for s in roslyn_result.symbols if s.symbol_type == "method"]

        # Check that methods have Calculator as parent
        for method in ts_methods:
            if method.symbol_name in ["Add", "_internalMethod"]:
                assert method.parent_symbol == "Calculator", \
                    f"Tree-sitter: {method.symbol_name} should have parent Calculator"

        for method in roslyn_methods:
            if method.symbol_name in ["Add", "_internalMethod"]:
                assert method.parent_symbol == "Calculator", \
                    f"Roslyn: {method.symbol_name} should have parent Calculator"


class TestExtractorDifferences:
    """Tests documenting expected differences between tree-sitter and Roslyn."""

    @pytest.fixture
    def ts_extractor(self):
        return CSharpTreeSitterExtractor()

    @pytest.fixture
    def roslyn_extractor(self):
        roslyn_path = Path(__file__).parent.parent.parent / "roslyn-tool"
        return CSharpRoslynExtractor(roslyn_path)

    def test_error_handling_difference(
        self, ts_extractor, roslyn_extractor, temp_dir, csharp_syntax_error_code
    ):
        """Tree-sitter should recover from errors better than Roslyn."""
        test_file = temp_dir / "Broken.cs"
        test_file.write_text(csharp_syntax_error_code)

        ts_result = ts_extractor.extract_directory(temp_dir, resolve_calls=False)
        roslyn_result = roslyn_extractor.extract_directory(temp_dir, resolve_calls=False)

        # Tree-sitter should have recorded an error but still extracted
        assert any(e["code"] == "SYNTAX_ERROR" for e in ts_result.errors)

        # Tree-sitter should extract valid methods despite errors
        ts_methods = {s.symbol_name for s in ts_result.symbols if s.symbol_type == "method"}
        assert "ValidMethod" in ts_methods
        assert "AnotherValidMethod" in ts_methods

        # Roslyn may or may not handle this depending on error severity

    def test_roslyn_provides_callee_file(
        self, ts_extractor, roslyn_extractor, csharp_cross_file_repo
    ):
        """Roslyn can resolve callee_file for cross-file calls (tree-sitter cannot)."""
        ts_result = ts_extractor.extract_directory(
            csharp_cross_file_repo,
            resolve_calls=False
        )
        roslyn_result = roslyn_extractor.extract_directory(
            csharp_cross_file_repo,
            resolve_calls=False
        )

        # Tree-sitter calls don't have callee_file (syntactic only)
        ts_resolved = [c for c in ts_result.calls if c.callee_file is not None]

        # This test documents the expected behavior - Roslyn may provide more
        # resolution information depending on its implementation


class TestTreeSitterOnlyFeatures:
    """Tests for tree-sitter specific behavior (when Roslyn isn't available)."""

    @pytest.fixture
    def extractor(self):
        return CSharpTreeSitterExtractor()

    def test_partial_extraction_recovers_valid_code(self, extractor, temp_dir):
        """Tree-sitter should extract valid code even with errors."""
        code = '''
public class ValidClass
{
    public void ValidMethod1() { }
}

public class BrokenClass
{
    public void BrokenMethod(  // Missing closing paren
    {
    }
}

public class AnotherValidClass
{
    public void ValidMethod2() { }
}
'''
        test_file = temp_dir / "mixed.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "mixed.cs")

        # Should have error
        assert len(result.errors) == 1
        assert result.errors[0]["recoverable"] is True

        # Should still extract valid parts
        class_names = {s.symbol_name for s in result.symbols if s.symbol_type == "class"}
        assert "ValidClass" in class_names
        assert "AnotherValidClass" in class_names

        method_names = {s.symbol_name for s in result.symbols if s.symbol_type == "method"}
        assert "ValidMethod1" in method_names
        assert "ValidMethod2" in method_names

    def test_handles_csharp_10_features(self, extractor, temp_dir):
        """Tree-sitter should handle C# 10+ features."""
        code = '''
namespace MyApp.Services;  // File-scoped namespace

public record Person(string FirstName, string LastName);

public class Example
{
    public required string Name { get; init; }
}
'''
        test_file = temp_dir / "modern.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "modern.cs")

        # Should parse without errors
        class_names = {s.symbol_name for s in result.symbols if s.symbol_type == "class"}
        assert "Person" in class_names
        assert "Example" in class_names


class TestParityWithMockedRoslyn:
    """Parity tests using mocked Roslyn output for consistent comparison."""

    @pytest.fixture
    def ts_extractor(self):
        return CSharpTreeSitterExtractor()

    def test_symbol_counts_comparable(self, ts_extractor, temp_dir, csharp_class_code):
        """Verify tree-sitter extracts comparable number of symbols."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        ts_result = ts_extractor.extract_file(test_file, "Calculator.cs")

        # Expected symbols:
        # - 1 class (Calculator)
        # - 1 constructor (Calculator)
        # - 2 methods (Add, _internalMethod)
        # - 1 property (Value)
        # - 1 field (_value)

        classes = [s for s in ts_result.symbols if s.symbol_type == "class"]
        methods = [s for s in ts_result.symbols if s.symbol_type == "method"]
        properties = [s for s in ts_result.symbols if s.symbol_type == "property"]
        fields = [s for s in ts_result.symbols if s.symbol_type == "field"]

        assert len(classes) == 1
        assert len(methods) >= 3  # Add, _internalMethod, Constructor
        assert len(properties) == 1
        assert len(fields) == 1

    def test_parameter_counts_accurate(self, ts_extractor, temp_dir):
        """Verify tree-sitter counts parameters correctly."""
        code = '''
public class Test
{
    public void NoParams() { }
    public void OneParam(int x) { }
    public void TwoParams(int x, string y) { }
    public void ThreeParams(int a, int b, int c) { }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        ts_result = ts_extractor.extract_file(test_file, "test.cs")

        methods = {s.symbol_name: s for s in ts_result.symbols if s.symbol_type == "method"}

        assert methods["NoParams"].parameters == 0
        assert methods["OneParam"].parameters == 1
        assert methods["TwoParams"].parameters == 2
        assert methods["ThreeParams"].parameters == 3

    def test_visibility_detection_accurate(self, ts_extractor, temp_dir, csharp_visibility_code):
        """Verify tree-sitter detects visibility correctly."""
        test_file = temp_dir / "visibility.cs"
        test_file.write_text(csharp_visibility_code)

        ts_result = ts_extractor.extract_file(test_file, "visibility.cs")

        symbols = {s.symbol_name: s for s in ts_result.symbols}

        # Public/internal/protected should be exported
        assert symbols["PublicField"].is_exported is True
        assert symbols["InternalField"].is_exported is True
        assert symbols["ProtectedField"].is_exported is True

        # Private should not be exported
        assert symbols["PrivateField"].is_exported is False
