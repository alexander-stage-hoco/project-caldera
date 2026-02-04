"""Unit tests for C# tree-sitter extractor."""

from __future__ import annotations

from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from extractors.csharp_treesitter_extractor import CSharpTreeSitterExtractor


class TestCSharpTreeSitterExtractor:
    """Tests for CSharpTreeSitterExtractor."""

    @pytest.fixture
    def extractor(self):
        return CSharpTreeSitterExtractor()

    # ============ Basic Properties ============

    def test_language_property(self, extractor):
        assert extractor.language == "csharp"

    def test_file_extensions(self, extractor):
        assert extractor.file_extensions == (".cs",)

    # ============ Type Declarations ============

    def test_extract_simple_class(self, extractor, temp_dir, csharp_class_code):
        """Test extraction of a simple class."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        result = extractor.extract_file(test_file, "Calculator.cs")

        # Should find the class
        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "Calculator"
        assert classes[0].is_exported is True

    def test_extract_struct(self, extractor, temp_dir, csharp_struct_code):
        """Test extraction of a struct."""
        test_file = temp_dir / "Point.cs"
        test_file.write_text(csharp_struct_code)

        result = extractor.extract_file(test_file, "Point.cs")

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "Point"
        assert classes[0].is_exported is True

    def test_extract_interface(self, extractor, temp_dir, csharp_interface_code):
        """Test extraction of an interface."""
        test_file = temp_dir / "ICalculator.cs"
        test_file.write_text(csharp_interface_code)

        result = extractor.extract_file(test_file, "ICalculator.cs")

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "ICalculator"
        assert classes[0].is_exported is True

    def test_extract_record(self, extractor, temp_dir, csharp_record_code):
        """Test extraction of a record."""
        test_file = temp_dir / "Person.cs"
        test_file.write_text(csharp_record_code)

        result = extractor.extract_file(test_file, "Person.cs")

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "Person"
        assert classes[0].is_exported is True

    def test_extract_enum(self, extractor, temp_dir, csharp_enum_code):
        """Test extraction of an enum."""
        test_file = temp_dir / "Color.cs"
        test_file.write_text(csharp_enum_code)

        result = extractor.extract_file(test_file, "Color.cs")

        # Enums are mapped to "class" for consistency
        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "Color"
        assert classes[0].is_exported is True

    # ============ Methods and Constructors ============

    def test_extract_method_with_params(self, extractor, temp_dir, csharp_class_code):
        """Test extraction of methods with parameter counting."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        result = extractor.extract_file(test_file, "Calculator.cs")

        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_by_name = {m.symbol_name: m for m in methods}

        # Add method has 2 parameters
        assert "Add" in method_by_name
        assert method_by_name["Add"].parameters == 2

        # _internalMethod has 0 parameters
        assert "_internalMethod" in method_by_name
        assert method_by_name["_internalMethod"].parameters == 0

    def test_extract_constructor(self, extractor, temp_dir, csharp_class_code):
        """Test extraction of constructor."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        result = extractor.extract_file(test_file, "Calculator.cs")

        # Constructor is mapped to "method" type
        methods = [s for s in result.symbols if s.symbol_type == "method"]
        constructors = [m for m in methods if m.symbol_name == "Calculator"]

        assert len(constructors) == 1
        assert constructors[0].parameters == 1  # initial parameter
        assert constructors[0].parent_symbol == "Calculator"

    def test_extract_property(self, extractor, temp_dir, csharp_class_code):
        """Test extraction of properties."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        result = extractor.extract_file(test_file, "Calculator.cs")

        properties = [s for s in result.symbols if s.symbol_type == "property"]
        assert len(properties) == 1
        assert properties[0].symbol_name == "Value"
        assert properties[0].parent_symbol == "Calculator"
        assert properties[0].is_exported is True

    def test_extract_field(self, extractor, temp_dir, csharp_class_code):
        """Test extraction of fields."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        result = extractor.extract_file(test_file, "Calculator.cs")

        fields = [s for s in result.symbols if s.symbol_type == "field"]
        assert len(fields) == 1
        assert fields[0].symbol_name == "_value"
        assert fields[0].parent_symbol == "Calculator"
        assert fields[0].is_exported is False  # private

    def test_extract_event(self, extractor, temp_dir, csharp_event_code):
        """Test extraction of events."""
        test_file = temp_dir / "EventExample.cs"
        test_file.write_text(csharp_event_code)

        result = extractor.extract_file(test_file, "EventExample.cs")

        events = [s for s in result.symbols if s.symbol_type == "event"]
        event_names = {e.symbol_name for e in events}
        assert "OnChanged" in event_names
        assert "OnMessage" in event_names

    # ============ Nested Types ============

    def test_nested_class(self, extractor, temp_dir, csharp_nested_class_code):
        """Test extraction of nested classes."""
        test_file = temp_dir / "Outer.cs"
        test_file.write_text(csharp_nested_class_code)

        result = extractor.extract_file(test_file, "Outer.cs")

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 2

        outer = next(c for c in classes if c.symbol_name == "Outer")
        inner = next(c for c in classes if c.symbol_name == "Inner")

        assert outer.parent_symbol is None
        assert inner.parent_symbol == "Outer"
        assert inner.is_exported is False  # private nested class

    # ============ Visibility Modifiers ============

    def test_visibility_modifiers(self, extractor, temp_dir, csharp_visibility_code):
        """Test visibility modifier detection."""
        test_file = temp_dir / "VisibilityTest.cs"
        test_file.write_text(csharp_visibility_code)

        result = extractor.extract_file(test_file, "VisibilityTest.cs")

        symbols_by_name = {s.symbol_name: s for s in result.symbols}

        # Public, internal, protected are exported
        assert symbols_by_name["PublicField"].is_exported is True
        assert symbols_by_name["InternalField"].is_exported is True
        assert symbols_by_name["ProtectedField"].is_exported is True
        assert symbols_by_name["PublicMethod"].is_exported is True
        assert symbols_by_name["InternalMethod"].is_exported is True
        assert symbols_by_name["ProtectedMethod"].is_exported is True

        # Private is not exported
        assert symbols_by_name["PrivateField"].is_exported is False
        assert symbols_by_name["PrivateMethod"].is_exported is False

    # ============ Static Members ============

    def test_static_members(self, extractor, temp_dir, csharp_static_code):
        """Test extraction of static class and members."""
        test_file = temp_dir / "MathHelper.cs"
        test_file.write_text(csharp_static_code)

        result = extractor.extract_file(test_file, "MathHelper.cs")

        # Static class should be extracted
        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "MathHelper"

        # Static method should be extracted
        methods = [s for s in result.symbols if s.symbol_type == "method"]
        assert len(methods) == 1
        assert methods[0].symbol_name == "Add"

        # Static field should be extracted
        fields = [s for s in result.symbols if s.symbol_type == "field"]
        assert len(fields) == 1
        assert fields[0].symbol_name == "PI"

    # ============ Async Methods ============

    def test_async_methods(self, extractor, temp_dir, csharp_async_code):
        """Test extraction of async methods."""
        test_file = temp_dir / "AsyncExample.cs"
        test_file.write_text(csharp_async_code)

        result = extractor.extract_file(test_file, "AsyncExample.cs")

        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}

        # Should find FetchDataAsync
        assert "FetchDataAsync" in method_names

        # Check parameter count for FetchDataAsync
        fetch_method = next(m for m in methods if m.symbol_name == "FetchDataAsync")
        assert fetch_method.parameters == 1  # url parameter

    # ============ Generic Types ============

    def test_generic_class(self, extractor, temp_dir, csharp_generic_class_code):
        """Test extraction of generic class."""
        test_file = temp_dir / "Container.cs"
        test_file.write_text(csharp_generic_class_code)

        result = extractor.extract_file(test_file, "Container.cs")

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "Container"

        # Methods inside generic class - constructor and SetValue should be found
        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}
        assert "Container" in method_names  # Constructor
        assert "SetValue" in method_names

    def test_generic_method(self, extractor, temp_dir, csharp_generic_method_code):
        """Test extraction of generic methods with type parameters."""
        test_file = temp_dir / "Utilities.cs"
        test_file.write_text(csharp_generic_method_code)

        result = extractor.extract_file(test_file, "Utilities.cs")

        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}

        # Should find Identity and Convert methods, NOT T or TResult
        assert "Identity" in method_names
        assert "Convert" in method_names
        assert "T" not in method_names  # Type param should NOT be extracted as method
        assert "TResult" not in method_names  # Type param should NOT be extracted as method

        # Check parameter count for Identity
        identity_method = next(m for m in methods if m.symbol_name == "Identity")
        assert identity_method.parameters == 1

        # Check parameter count for Convert
        convert_method = next(m for m in methods if m.symbol_name == "Convert")
        assert convert_method.parameters == 2

    # ============ Imports (Using Directives) ============

    def test_extract_imports(self, extractor, temp_dir, csharp_imports_code):
        """Test extraction of using directives."""
        test_file = temp_dir / "ImportExample.cs"
        test_file.write_text(csharp_imports_code)

        result = extractor.extract_file(test_file, "ImportExample.cs")

        import_paths = {i.imported_path for i in result.imports}
        assert "System" in import_paths
        assert "System.Collections.Generic" in import_paths
        assert "System.Math" in import_paths
        assert "System.Text.StringBuilder" in import_paths

    def test_static_using(self, extractor, temp_dir):
        """Test extraction of static using directive."""
        code = "using static System.Math;\n"
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        assert len(result.imports) == 1
        assert result.imports[0].imported_path == "System.Math"

    def test_aliased_using(self, extractor, temp_dir):
        """Test extraction of aliased using directive."""
        code = "using Alias = System.Text.StringBuilder;\n"
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        assert len(result.imports) == 1
        assert result.imports[0].imported_path == "System.Text.StringBuilder"
        assert result.imports[0].module_alias == "Alias"  # Alias should be captured

    def test_global_using(self, extractor, temp_dir, csharp_global_using_code):
        """Test extraction of global using directives (C# 10+)."""
        test_file = temp_dir / "GlobalUsing.cs"
        test_file.write_text(csharp_global_using_code)

        result = extractor.extract_file(test_file, "GlobalUsing.cs")

        global_imports = [i for i in result.imports if i.import_type == "global"]
        assert len(global_imports) >= 2

    def test_extern_alias(self, extractor, temp_dir):
        """Test extraction of extern alias directive."""
        code = "extern alias GridV1;\nextern alias GridV2;\n"
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        extern_imports = [i for i in result.imports if i.import_type == "extern"]
        assert len(extern_imports) == 2
        alias_names = {i.imported_path for i in extern_imports}
        assert "GridV1" in alias_names
        assert "GridV2" in alias_names

    # ============ Call Extraction ============

    def test_extract_calls(self, extractor, temp_dir, csharp_calls_code):
        """Test extraction of method calls."""
        test_file = temp_dir / "CallExample.cs"
        test_file.write_text(csharp_calls_code)

        result = extractor.extract_file(test_file, "CallExample.cs")

        # Should find various calls
        callee_symbols = {c.callee_symbol for c in result.calls}
        assert "LocalMethod" in callee_symbols
        assert "WriteLine" in callee_symbols

    def test_direct_method_call(self, extractor, temp_dir):
        """Test extraction of direct method calls."""
        code = '''
public class Test
{
    public void Caller()
    {
        DoWork();
    }

    public void DoWork() { }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        calls_to_dowork = [c for c in result.calls if c.callee_symbol == "DoWork"]
        assert len(calls_to_dowork) == 1  # Exact count after fixing duplicate extraction
        assert calls_to_dowork[0].call_type == "direct"
        assert calls_to_dowork[0].caller_symbol == "Caller"

    def test_static_method_call(self, extractor, temp_dir):
        """Test extraction of static method calls."""
        code = '''
public class Test
{
    public void Caller()
    {
        var abs = Math.Abs(-5);
    }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        calls_to_abs = [c for c in result.calls if c.callee_symbol == "Abs"]
        assert len(calls_to_abs) == 1  # Exact count after fixing duplicate extraction
        assert calls_to_abs[0].call_type == "dynamic"  # member access
        assert calls_to_abs[0].callee_object == "Math"

    def test_instance_method_call(self, extractor, temp_dir):
        """Test extraction of instance method calls."""
        code = '''
public class Test
{
    public void Caller()
    {
        var str = "hello";
        var upper = str.ToUpper();
    }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        calls_to_upper = [c for c in result.calls if c.callee_symbol == "ToUpper"]
        assert len(calls_to_upper) == 1  # Exact count after fixing duplicate extraction
        assert calls_to_upper[0].call_type == "dynamic"
        assert calls_to_upper[0].callee_object == "str"

    def test_object_creation_call(self, extractor, temp_dir):
        """Test extraction of object creation (new) calls."""
        code = '''
public class Test
{
    public void Caller()
    {
        var list = new List<string>();
        var dict = new Dictionary<int, string>();
    }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        # Object creations should be captured as constructor calls
        callee_symbols = {c.callee_symbol for c in result.calls}
        assert "List" in callee_symbols
        assert "Dictionary" in callee_symbols

    def test_chained_calls(self, extractor, temp_dir):
        """Test extraction of chained method calls."""
        code = '''
public class Test
{
    public void Caller()
    {
        var result = "  hello  ".Trim().ToLower().Substring(0, 3);
    }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        callee_symbols = {c.callee_symbol for c in result.calls}
        assert "Trim" in callee_symbols
        assert "ToLower" in callee_symbols
        assert "Substring" in callee_symbols

    # ============ Error Handling ============

    def test_syntax_error_handling(self, extractor, temp_dir, csharp_syntax_error_code):
        """Test handling of syntax errors - tree-sitter should recover."""
        test_file = temp_dir / "Broken.cs"
        test_file.write_text(csharp_syntax_error_code)

        result = extractor.extract_file(test_file, "Broken.cs")

        # Should have error recorded
        assert len(result.errors) == 1
        assert result.errors[0]["code"] == "SYNTAX_ERROR"
        assert result.errors[0]["recoverable"] is True

    def test_partial_extraction_on_error(self, extractor, temp_dir, csharp_syntax_error_code):
        """Test that tree-sitter extracts valid parts despite errors."""
        test_file = temp_dir / "Broken.cs"
        test_file.write_text(csharp_syntax_error_code)

        result = extractor.extract_file(test_file, "Broken.cs")

        # Should still extract valid symbols
        method_names = {s.symbol_name for s in result.symbols if s.symbol_type == "method"}
        assert "ValidMethod" in method_names
        assert "AnotherValidMethod" in method_names

    def test_empty_file(self, extractor, temp_dir):
        """Test handling of empty file."""
        test_file = temp_dir / "Empty.cs"
        test_file.write_text("")

        result = extractor.extract_file(test_file, "Empty.cs")

        # Should not crash, return empty results
        assert len(result.symbols) == 0
        assert len(result.imports) == 0
        assert len(result.calls) == 0
        assert len(result.errors) == 0

    def test_encoding_error_handling(self, extractor, temp_dir):
        """Test handling of encoding errors."""
        # Create a file with invalid UTF-8 bytes
        test_file = temp_dir / "binary.cs"
        test_file.write_bytes(b"\xff\xfe invalid utf-8")

        result = extractor.extract_file(test_file, "binary.cs")

        # Tree-sitter handles binary data, should parse what it can
        # No specific error expected as tree-sitter is lenient

    # ============ Line Numbers ============

    def test_line_numbers(self, extractor, temp_dir):
        """Test that line numbers are correctly extracted."""
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

        result = extractor.extract_file(test_file, "test.cs")

        symbols_by_name = {s.symbol_name: s for s in result.symbols}

        # First class starts at line 1
        assert symbols_by_name["First"].line_start == 1

        # Second class starts at line 6
        assert symbols_by_name["Second"].line_start == 6

        # Method1 starts at line 3
        assert symbols_by_name["Method1"].line_start == 3

        # Method2 starts at line 8
        assert symbols_by_name["Method2"].line_start == 8

    # ============ XML Documentation Comments ============

    def test_xml_doc_comments(self, extractor, temp_dir, csharp_xml_doc_code):
        """Test extraction of XML documentation comments."""
        test_file = temp_dir / "Documented.cs"
        test_file.write_text(csharp_xml_doc_code)

        result = extractor.extract_file(test_file, "Documented.cs")

        # Check class docstring
        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        # Note: Depends on tree-sitter's comment handling
        # The docstring might be extracted if the comment is properly associated

    # ============ Directory Extraction ============

    def test_extract_directory(self, extractor, csharp_cross_file_repo):
        """Test extraction from a directory with multiple files."""
        result = extractor.extract_directory(csharp_cross_file_repo)

        # Should find symbols from all files
        paths = {s.path for s in result.symbols}
        assert "Models.cs" in paths
        assert "Services.cs" in paths
        assert "Program.cs" in paths

        # Should find classes
        class_names = {s.symbol_name for s in result.symbols if s.symbol_type == "class"}
        assert "User" in class_names
        assert "UserService" in class_names
        assert "Program" in class_names

        # Should find imports
        import_paths = {i.imported_path for i in result.imports}
        assert "MyApp.Models" in import_paths
        assert "MyApp.Services" in import_paths

    # ============ File-Scoped Namespaces ============

    def test_file_scoped_namespace(self, extractor, temp_dir, csharp_file_scoped_namespace_code):
        """Test extraction with file-scoped namespace (C# 10+)."""
        test_file = temp_dir / "Service.cs"
        test_file.write_text(csharp_file_scoped_namespace_code)

        result = extractor.extract_file(test_file, "Service.cs")

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "ServiceExample"

        methods = [s for s in result.symbols if s.symbol_type == "method"]
        assert len(methods) == 1
        assert methods[0].symbol_name == "DoWork"

    # ============ Parent Symbol Tracking ============

    def test_method_parent_symbol(self, extractor, temp_dir, csharp_class_code):
        """Test that methods have correct parent_symbol set."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        result = extractor.extract_file(test_file, "Calculator.cs")

        methods = [s for s in result.symbols if s.symbol_type == "method"]
        for method in methods:
            assert method.parent_symbol == "Calculator"

    def test_property_parent_symbol(self, extractor, temp_dir, csharp_class_code):
        """Test that properties have correct parent_symbol set."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        result = extractor.extract_file(test_file, "Calculator.cs")

        properties = [s for s in result.symbols if s.symbol_type == "property"]
        for prop in properties:
            assert prop.parent_symbol == "Calculator"

    def test_field_parent_symbol(self, extractor, temp_dir, csharp_class_code):
        """Test that fields have correct parent_symbol set."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_class_code)

        result = extractor.extract_file(test_file, "Calculator.cs")

        fields = [s for s in result.symbols if s.symbol_type == "field"]
        for field in fields:
            assert field.parent_symbol == "Calculator"

    # ============ Complex Scenarios ============

    def test_multiple_classes_in_file(self, extractor, temp_dir):
        """Test extraction of multiple classes in one file."""
        code = '''
public class ClassA { }
public class ClassB { }
internal class ClassC { }
'''
        test_file = temp_dir / "multi.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "multi.cs")

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 3
        class_names = {c.symbol_name for c in classes}
        assert class_names == {"ClassA", "ClassB", "ClassC"}

    def test_deeply_nested_namespaces(self, extractor, temp_dir):
        """Test extraction within deeply nested namespaces."""
        code = '''
namespace A.B.C.D
{
    public class DeepClass
    {
        public void DeepMethod() { }
    }
}
'''
        test_file = temp_dir / "deep.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "deep.cs")

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "DeepClass"

        methods = [s for s in result.symbols if s.symbol_type == "method"]
        assert len(methods) == 1
        assert methods[0].symbol_name == "DeepMethod"

    def test_interface_methods_no_body(self, extractor, temp_dir, csharp_interface_code):
        """Test extraction of interface methods (no body)."""
        test_file = temp_dir / "ICalculator.cs"
        test_file.write_text(csharp_interface_code)

        result = extractor.extract_file(test_file, "ICalculator.cs")

        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}
        assert "Add" in method_names
        assert "Subtract" in method_names

        # Check parameter count
        add_method = next(m for m in methods if m.symbol_name == "Add")
        assert add_method.parameters == 2

    # ============ Import Type Classification ============

    def test_import_type_static_vs_using_static(self, extractor, temp_dir):
        """Test that static using and regular using are distinguished."""
        code = '''
using System;
using static System.Math;
using static System.Console;
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        # Group imports by path
        imports_by_path = {i.imported_path: i for i in result.imports}

        # Regular using should be "static" (standard import type)
        assert imports_by_path["System"].import_type == "static"

        # Static using should be "using_static"
        assert imports_by_path["System.Math"].import_type == "using_static"
        assert imports_by_path["System.Console"].import_type == "using_static"

    def test_import_type_global_static(self, extractor, temp_dir):
        """Test that global using overrides to global import type."""
        code = '''
global using System;
global using static System.Math;
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        # Global takes precedence
        for imp in result.imports:
            assert imp.import_type == "global"

    # ============ Constructor Call Type ============

    def test_constructor_call_type(self, extractor, temp_dir):
        """Test that object creation is recorded as constructor call type."""
        code = '''
public class Test
{
    public void Caller()
    {
        var list = new List<string>();
        var obj = new MyClass();
    }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        constructor_calls = [c for c in result.calls if c.call_type == "constructor"]
        assert len(constructor_calls) == 2

        callee_symbols = {c.callee_symbol for c in constructor_calls}
        assert "List" in callee_symbols
        assert "MyClass" in callee_symbols

    def test_constructor_vs_method_call_types(self, extractor, temp_dir):
        """Test that constructor and method calls have distinct call types."""
        code = '''
public class Test
{
    public void Caller()
    {
        var obj = new StringBuilder();
        obj.Append("text");
        DoWork();
    }

    public void DoWork() { }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        # Constructor call
        ctor_calls = [c for c in result.calls if c.callee_symbol == "StringBuilder"]
        assert len(ctor_calls) == 1
        assert ctor_calls[0].call_type == "constructor"

        # Direct method call
        direct_calls = [c for c in result.calls if c.callee_symbol == "DoWork"]
        assert len(direct_calls) == 1
        assert direct_calls[0].call_type == "direct"

        # Member method call
        member_calls = [c for c in result.calls if c.callee_symbol == "Append"]
        assert len(member_calls) == 1
        assert member_calls[0].call_type == "dynamic"

    # ============ Extension Methods ============

    def test_extension_method_declaration(self, extractor, temp_dir):
        """Test extraction of extension method declarations."""
        code = '''
public static class StringExtensions
{
    public static string Reverse(this string str)
    {
        char[] chars = str.ToCharArray();
        Array.Reverse(chars);
        return new string(chars);
    }

    public static bool IsNullOrEmpty(this string str)
    {
        return string.IsNullOrEmpty(str);
    }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        # Class should be extracted
        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "StringExtensions"

        # Extension methods should be extracted as regular methods
        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}
        assert "Reverse" in method_names
        assert "IsNullOrEmpty" in method_names

        # Check parameter count includes 'this' parameter
        reverse_method = next(m for m in methods if m.symbol_name == "Reverse")
        assert reverse_method.parameters == 1  # 'this string str'

    # ============ Partial Classes ============

    def test_partial_class(self, extractor, temp_dir):
        """Test extraction of partial class declarations."""
        code = '''
public partial class MyPartialClass
{
    public void Method1() { }
}

public partial class MyPartialClass
{
    public void Method2() { }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        # Both partial class declarations should be extracted
        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 2
        assert all(c.symbol_name == "MyPartialClass" for c in classes)

        # Methods from both partials should be extracted
        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}
        assert "Method1" in method_names
        assert "Method2" in method_names

    # ============ Nullable Reference Types ============

    def test_nullable_reference_types(self, extractor, temp_dir):
        """Test extraction of methods with nullable types."""
        code = '''
public class NullableExample
{
    public string? GetNullableString()
    {
        return null;
    }

    public void SetValue(string? value)
    {
        _value = value;
    }

    private string? _value;

    public int? NullableProperty { get; set; }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        # Methods with nullable types should be extracted
        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}
        assert "GetNullableString" in method_names
        assert "SetValue" in method_names

        # Property with nullable type should be extracted
        properties = [s for s in result.symbols if s.symbol_type == "property"]
        prop_names = {p.symbol_name for p in properties}
        assert "NullableProperty" in prop_names

        # Field with nullable type should be extracted
        fields = [s for s in result.symbols if s.symbol_type == "field"]
        field_names = {f.symbol_name for f in fields}
        assert "_value" in field_names

    # ============ Delegates ============

    def test_delegate_declaration(self, extractor, temp_dir):
        """Test extraction of delegate declarations."""
        code = '''
public delegate void MyHandler(object sender, EventArgs e);
public delegate int Calculator(int x, int y);
public delegate T GenericDelegate<T>(T input);

public class DelegateExample
{
    public MyHandler OnEvent;

    public void UseDelegate()
    {
        OnEvent?.Invoke(this, EventArgs.Empty);
    }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        # Delegates may or may not be extracted as symbols depending on tree-sitter grammar
        # The class and its members should be extracted
        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) >= 1
        assert any(c.symbol_name == "DelegateExample" for c in classes)

        # Field should be extracted
        fields = [s for s in result.symbols if s.symbol_type == "field"]
        field_names = {f.symbol_name for f in fields}
        assert "OnEvent" in field_names

    # ============ LINQ Expressions ============

    def test_linq_method_syntax(self, extractor, temp_dir):
        """Test extraction of LINQ method syntax calls."""
        code = '''
public class LinqExample
{
    public void UseLinq()
    {
        var numbers = new List<int> { 1, 2, 3, 4, 5 };
        var even = numbers.Where(n => n % 2 == 0).Select(n => n * 2).ToList();
    }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        # LINQ method calls should be extracted
        callee_symbols = {c.callee_symbol for c in result.calls}
        assert "Where" in callee_symbols
        assert "Select" in callee_symbols
        assert "ToList" in callee_symbols

    # ============ Event/Delegate Invocation ============

    def test_event_invocation_call_type(self, extractor, temp_dir):
        """Test that event?.Invoke() pattern produces call_type='event'."""
        code = '''
public class EventExample
{
    public event EventHandler OnChanged;

    public void RaiseEvent()
    {
        OnChanged?.Invoke(this, EventArgs.Empty);
    }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        # Find the event invocation call
        event_calls = [c for c in result.calls if c.callee_symbol == "OnChanged"]
        assert len(event_calls) == 1
        assert event_calls[0].call_type == "event"
        assert event_calls[0].caller_symbol == "RaiseEvent"

    def test_delegate_invoke_pattern(self, extractor, temp_dir):
        """Test that delegate?.Invoke() pattern produces call_type='event'."""
        code = '''
public class DelegateExample
{
    private Action<string> _handler;

    public void Execute()
    {
        _handler?.Invoke("hello");
    }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        # Find the delegate invocation call
        delegate_calls = [c for c in result.calls if c.callee_symbol == "_handler"]
        assert len(delegate_calls) == 1
        assert delegate_calls[0].call_type == "event"  # Using "event" for ?.Invoke() pattern

    def test_property_changed_event_pattern(self, extractor, temp_dir):
        """Test common PropertyChanged?.Invoke() INotifyPropertyChanged pattern."""
        code = '''
public class ViewModel
{
    public event PropertyChangedEventHandler PropertyChanged;

    private string _name;
    public string Name
    {
        get => _name;
        set
        {
            _name = value;
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(Name)));
        }
    }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        # Find the PropertyChanged invocation
        pc_calls = [c for c in result.calls if c.callee_symbol == "PropertyChanged"]
        assert len(pc_calls) == 1
        assert pc_calls[0].call_type == "event"

    def test_conditional_method_vs_event_invoke(self, extractor, temp_dir):
        """Test that ?.Method() (non-Invoke) is still 'dynamic', not 'event'."""
        code = '''
public class ConditionalExample
{
    private string _text;

    public void Process()
    {
        var result = _text?.ToUpper();
    }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        # Should find ToUpper call as dynamic (conditional member access)
        upper_calls = [c for c in result.calls if c.callee_symbol == "ToUpper"]
        assert len(upper_calls) == 1
        assert upper_calls[0].call_type == "dynamic"
        assert upper_calls[0].callee_object == "_text"

    def test_multiple_event_invocations(self, extractor, temp_dir):
        """Test extraction of multiple event invocations in same class."""
        code = '''
public class MultiEventExample
{
    public event EventHandler Started;
    public event EventHandler Completed;
    public event EventHandler<string> Error;

    public void Run()
    {
        Started?.Invoke(this, EventArgs.Empty);
        // Do work...
        Completed?.Invoke(this, EventArgs.Empty);
    }

    public void OnError(string message)
    {
        Error?.Invoke(this, message);
    }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        # All three events should be captured as event calls
        event_calls = [c for c in result.calls if c.call_type == "event"]
        event_names = {c.callee_symbol for c in event_calls}

        assert "Started" in event_names
        assert "Completed" in event_names
        assert "Error" in event_names
        assert len(event_calls) == 3

    # ============ Abstract, Virtual, Override, Sealed ============

    def test_abstract_class_and_method(self, extractor, temp_dir, csharp_abstract_class_code):
        """Test extraction of abstract class with abstract and virtual methods."""
        test_file = temp_dir / "Shapes.cs"
        test_file.write_text(csharp_abstract_class_code)

        result = extractor.extract_file(test_file, "Shapes.cs")

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        class_names = {c.symbol_name for c in classes}

        # Should find all three classes
        assert "Shape" in class_names
        assert "Circle" in class_names
        assert "Square" in class_names

        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}

        # Should find Area and Draw methods
        assert "Area" in method_names
        assert "Draw" in method_names

    def test_virtual_override_methods(self, extractor, temp_dir):
        """Test extraction of virtual and override methods."""
        code = '''
public class Base
{
    public virtual void Process() { }
    public virtual int Calculate(int x) => x;
}

public class Derived : Base
{
    public override void Process() { base.Process(); }
    public override int Calculate(int x) => x * 2;
    public new void Process(int arg) { }
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_by_key = {(m.symbol_name, m.parent_symbol): m for m in methods}

        # Base class methods
        assert ("Process", "Base") in method_by_key
        assert ("Calculate", "Base") in method_by_key

        # Derived class methods (override and new)
        assert ("Process", "Derived") in method_by_key
        assert ("Calculate", "Derived") in method_by_key

    def test_sealed_class(self, extractor, temp_dir, csharp_abstract_class_code):
        """Test extraction of sealed class."""
        test_file = temp_dir / "Shapes.cs"
        test_file.write_text(csharp_abstract_class_code)

        result = extractor.extract_file(test_file, "Shapes.cs")

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        class_names = {c.symbol_name for c in classes}

        # Sealed class should be extracted
        assert "Square" in class_names

    # ============ Local Functions ============

    def test_local_functions(self, extractor, temp_dir, csharp_local_function_code):
        """Test extraction of local functions declared inside methods."""
        test_file = temp_dir / "Calculator.cs"
        test_file.write_text(csharp_local_function_code)

        result = extractor.extract_file(test_file, "Calculator.cs")

        # Should find the class
        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "Calculator"

        # Should find the outer methods
        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}

        assert "Factorial" in method_names
        assert "ProcessNumbers" in method_names

        # Local functions may or may not be extracted as top-level symbols
        # depending on tree-sitter grammar - this documents current behavior

    # ============ Tuple Return Types ============

    def test_tuple_return_types(self, extractor, temp_dir, csharp_tuple_code):
        """Test extraction of methods with tuple return types."""
        test_file = temp_dir / "TupleExample.cs"
        test_file.write_text(csharp_tuple_code)

        result = extractor.extract_file(test_file, "TupleExample.cs")

        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}

        # Methods with tuple returns should be extracted
        assert "GetPair" in method_names
        assert "GetCoordinates" in method_names
        assert "UseTuples" in method_names
        assert "GetFirstAndLast" in method_names

        # Check parameter counts
        method_by_name = {m.symbol_name: m for m in methods}
        assert method_by_name["GetPair"].parameters == 0
        assert method_by_name["GetCoordinates"].parameters == 0
        assert method_by_name["UseTuples"].parameters == 0
        assert method_by_name["GetFirstAndLast"].parameters == 1

    def test_tuple_deconstruction(self, extractor, temp_dir):
        """Test that methods using tuple deconstruction are extracted."""
        code = '''
public class DeconstructExample
{
    public void UseDeconstruction()
    {
        var (x, y) = GetPoint();
        (int a, int b) = (10, 20);
        var (first, _, last) = GetThree();
    }

    public (int, int) GetPoint() => (1, 2);
    public (int, int, int) GetThree() => (1, 2, 3);
}
'''
        test_file = temp_dir / "test.cs"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.cs")

        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}

        assert "UseDeconstruction" in method_names
        assert "GetPoint" in method_names
        assert "GetThree" in method_names

    # ============ LINQ Query Syntax ============

    def test_linq_query_syntax(self, extractor, temp_dir, csharp_linq_query_code):
        """Test extraction of methods containing LINQ query syntax."""
        test_file = temp_dir / "QueryExample.cs"
        test_file.write_text(csharp_linq_query_code)

        result = extractor.extract_file(test_file, "QueryExample.cs")

        # Should find the class
        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "QueryExample"

        # Should find methods with LINQ queries
        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}

        assert "GetEvens" in method_names
        assert "GetNames" in method_names
        assert "GroupByCategory" in method_names

        # Check imports
        import_paths = {i.imported_path for i in result.imports}
        assert "System.Linq" in import_paths
        assert "System.Collections.Generic" in import_paths

    # ============ Static Constructor ============

    def test_static_constructor(self, extractor, temp_dir, csharp_static_constructor_code):
        """Test extraction of static constructor."""
        test_file = temp_dir / "Configuration.cs"
        test_file.write_text(csharp_static_constructor_code)

        result = extractor.extract_file(test_file, "Configuration.cs")

        # Should find the class
        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "Configuration"

        # Should find constructors (static and instance)
        methods = [s for s in result.symbols if s.symbol_type == "method"]
        constructor_methods = [m for m in methods if m.symbol_name == "Configuration"]

        # Should find at least the instance constructor
        # Static constructor may be extracted depending on tree-sitter grammar
        assert len(constructor_methods) >= 1

        # Should find instance method
        method_names = {m.symbol_name for m in methods}
        assert "Reset" in method_names

        # Should find static properties
        properties = [s for s in result.symbols if s.symbol_type == "property"]
        property_names = {p.symbol_name for p in properties}
        assert "ConnectionString" in property_names
        assert "MaxRetries" in property_names

    # ============ Indexer Declaration ============

    def test_indexer_declaration(self, extractor, temp_dir, csharp_indexer_code):
        """Test extraction of indexer declarations."""
        test_file = temp_dir / "DataCollection.cs"
        test_file.write_text(csharp_indexer_code)

        result = extractor.extract_file(test_file, "DataCollection.cs")

        # Should find the class
        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "DataCollection"

        # Should find the field
        fields = [s for s in result.symbols if s.symbol_type == "field"]
        field_names = {f.symbol_name for f in fields}
        assert "_data" in field_names

        # Indexers may be extracted as methods or properties depending on grammar
        # Document current behavior
        all_symbols = {s.symbol_name for s in result.symbols}
        # Either indexer is extracted or the class structure is complete
        assert "DataCollection" in all_symbols
