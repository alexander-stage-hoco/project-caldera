"""Unit tests for Python extractor."""

from __future__ import annotations

from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from extractors.python_extractor import PythonExtractor


class TestPythonExtractor:
    """Tests for PythonExtractor."""

    @pytest.fixture
    def extractor(self):
        return PythonExtractor()

    def test_language_property(self, extractor):
        assert extractor.language == "python"

    def test_file_extensions(self, extractor):
        assert extractor.file_extensions == (".py",)

    def test_extract_simple_functions(self, extractor, temp_dir, simple_function_code):
        """Test extraction of simple functions."""
        test_file = temp_dir / "test.py"
        test_file.write_text(simple_function_code)

        result = extractor.extract_file(test_file, "test.py")

        # Should find 3 functions
        assert len(result.symbols) == 3

        # Check function names
        names = {s.symbol_name for s in result.symbols}
        assert names == {"hello", "add", "main"}

        # Check all are functions
        for symbol in result.symbols:
            assert symbol.symbol_type == "function"
            assert symbol.is_exported is True  # No underscore prefix

        # Check hello function
        hello = next(s for s in result.symbols if s.symbol_name == "hello")
        assert hello.parameters == 1
        assert hello.docstring == "Say hello."

        # Check add function
        add = next(s for s in result.symbols if s.symbol_name == "add")
        assert add.parameters == 2

    def test_extract_classes_and_methods(self, extractor, temp_dir, class_code):
        """Test extraction of classes and methods."""
        test_file = temp_dir / "test.py"
        test_file.write_text(class_code)

        result = extractor.extract_file(test_file, "test.py")

        # Check classes
        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 2
        class_names = {c.symbol_name for c in classes}
        assert class_names == {"Calculator", "AdvancedCalculator"}

        # Check methods
        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}
        assert "__init__" in method_names
        assert "add" in method_names
        assert "_internal" in method_names
        assert "multiply" in method_names

        # Check _internal is not exported
        internal = next(s for s in result.symbols if s.symbol_name == "_internal")
        assert internal.is_exported is False

        # Check method parent symbols
        calc_methods = [m for m in methods if m.parent_symbol == "Calculator"]
        assert len(calc_methods) >= 3  # __init__, add, _internal

    def test_extract_imports(self, extractor, temp_dir, import_code):
        """Test extraction of imports."""
        test_file = temp_dir / "test.py"
        test_file.write_text(import_code)

        result = extractor.extract_file(test_file, "test.py")

        # Should find multiple imports
        assert len(result.imports) >= 5

        # Check import types
        import_paths = {i.imported_path for i in result.imports}
        assert "os" in import_paths
        assert "sys" in import_paths
        assert "pathlib" in import_paths
        assert "typing" in import_paths
        assert "json" in import_paths
        assert "collections" in import_paths

        # Check from imports have symbols
        pathlib_import = next(i for i in result.imports if i.imported_path == "pathlib")
        assert pathlib_import.imported_symbols == "Path"

        # Check aliased import
        json_import = next(i for i in result.imports if i.imported_path == "json")
        assert json_import.imported_symbols is None  # Full module import

        # Check star import
        collections_import = next(i for i in result.imports if i.imported_path == "collections")
        assert collections_import.imported_symbols == "*"

    def test_extract_calls(self, extractor, temp_dir, simple_function_code):
        """Test extraction of function calls."""
        test_file = temp_dir / "test.py"
        test_file.write_text(simple_function_code)

        result = extractor.extract_file(test_file, "test.py")

        # Should find calls in main()
        main_calls = [c for c in result.calls if c.caller_symbol == "main"]
        assert len(main_calls) >= 3  # print, hello, add

        callee_symbols = {c.callee_symbol for c in main_calls}
        assert "hello" in callee_symbols
        assert "add" in callee_symbols
        assert "print" in callee_symbols

    def test_extract_directory(self, extractor, cross_module_repo):
        """Test extraction from a directory."""
        result = extractor.extract_directory(cross_module_repo)

        # Should find symbols from both files
        paths = {s.path for s in result.symbols}
        assert "utils.py" in paths
        assert "main.py" in paths

        # Should find imports
        assert len(result.imports) >= 1
        import_paths = {i.imported_path for i in result.imports}
        assert "utils" in import_paths

        # Should find calls
        assert len(result.calls) >= 2

    def test_syntax_error_handling(self, extractor, temp_dir):
        """Test handling of syntax errors."""
        test_file = temp_dir / "bad.py"
        test_file.write_text("def broken(:\n    pass")

        result = extractor.extract_file(test_file, "bad.py")

        assert len(result.errors) == 1
        assert result.errors[0]["code"] == "SYNTAX_ERROR"
        assert result.errors[0]["recoverable"] is True

    def test_async_functions(self, extractor, temp_dir):
        """Test extraction of async functions."""
        code = '''
async def fetch_data(url: str) -> dict:
    """Fetch data from URL."""
    return {}

async def process():
    data = await fetch_data("http://example.com")
    return data
'''
        test_file = temp_dir / "async_test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "async_test.py")

        # Should find async functions
        assert len(result.symbols) == 2
        for symbol in result.symbols:
            assert symbol.symbol_type == "function"

        # Should find async call
        async_calls = [c for c in result.calls if c.call_type == "async"]
        assert len(async_calls) >= 1

    def test_nested_functions(self, extractor, temp_dir):
        """Test extraction handles nested functions."""
        code = '''
def outer():
    def inner():
        pass
    inner()
'''
        test_file = temp_dir / "nested.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "nested.py")

        # Should find both functions
        names = {s.symbol_name for s in result.symbols}
        assert "outer" in names
        assert "inner" in names

    def test_method_parameter_count(self, extractor, temp_dir):
        """Test that self/cls are not counted in method parameters."""
        code = '''
class MyClass:
    def instance_method(self, x, y):
        pass

    @classmethod
    def class_method(cls, x):
        pass

    @staticmethod
    def static_method(x, y, z):
        pass
'''
        test_file = temp_dir / "methods.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "methods.py")

        methods = {s.symbol_name: s for s in result.symbols if s.symbol_type == "method"}

        # instance_method has self, x, y - should count 2
        assert methods["instance_method"].parameters == 2

        # class_method has cls, x - should count 1
        assert methods["class_method"].parameters == 1

        # static_method has x, y, z - should count 3 (no self/cls to exclude)
        assert methods["static_method"].parameters == 3


class TestVariableExtraction:
    """Tests for module-level variable extraction."""

    @pytest.fixture
    def extractor(self):
        return PythonExtractor()

    def test_simple_assignment(self, extractor, temp_dir):
        """Test extraction of simple variable assignment."""
        code = "VERSION = '1.0.0'"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        assert len(result.symbols) == 1
        var = result.symbols[0]
        assert var.symbol_name == "VERSION"
        assert var.symbol_type == "variable"
        assert var.is_exported is True
        assert var.parameters is None
        assert var.parent_symbol is None

    def test_annotated_assignment(self, extractor, temp_dir):
        """Test extraction of annotated variable."""
        code = "MAX_RETRIES: int = 3"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        assert len(result.symbols) == 1
        var = result.symbols[0]
        assert var.symbol_name == "MAX_RETRIES"
        assert var.symbol_type == "variable"
        assert var.is_exported is True

    def test_tuple_unpacking(self, extractor, temp_dir):
        """Test extraction of tuple unpacking creates multiple symbols."""
        code = "x, y, z = 1, 2, 3"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        assert len(result.symbols) == 3
        names = {s.symbol_name for s in result.symbols}
        assert names == {"x", "y", "z"}
        for symbol in result.symbols:
            assert symbol.symbol_type == "variable"

    def test_dunder_variables_skipped(self, extractor, temp_dir):
        """Test that __all__ and similar are not extracted."""
        code = "__all__ = ['foo']\n__version__ = '1.0'\nVERSION = '1.0'"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        # Only VERSION should be extracted
        assert len(result.symbols) == 1
        assert result.symbols[0].symbol_name == "VERSION"

    def test_private_variable(self, extractor, temp_dir):
        """Test private variable has is_exported=False."""
        code = "_internal = 42"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        assert len(result.symbols) == 1
        var = result.symbols[0]
        assert var.symbol_name == "_internal"
        assert var.is_exported is False

    def test_function_local_not_extracted(self, extractor, temp_dir):
        """Test that variables inside functions are not extracted."""
        code = "def foo():\n    x = 1"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        # Only the function should be extracted, not x
        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 0

    def test_class_attribute_not_extracted(self, extractor, temp_dir):
        """Test that class-level attributes are not extracted as module variables."""
        code = "class Foo:\n    x = 1\n\nMODULE_VAR = 2"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        # Only MODULE_VAR should be extracted as variable (x is class attribute)
        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 1
        assert variable_symbols[0].symbol_name == "MODULE_VAR"

    def test_type_variable(self, extractor, temp_dir):
        """Test extraction of TypeVar assignment."""
        code = "from typing import TypeVar\nT = TypeVar('T')"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 1
        assert variable_symbols[0].symbol_name == "T"

    def test_multiple_assignments(self, extractor, temp_dir):
        """Test extraction of multiple module-level assignments."""
        code = "A = 1\nB = 2\nC: str = 'hello'\nx, y = 1, 2"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 5
        names = {s.symbol_name for s in variable_symbols}
        assert names == {"A", "B", "C", "x", "y"}

    def test_variable_line_numbers(self, extractor, temp_dir):
        """Test that variable line numbers are correct."""
        code = "A = 1\n\nB = 2"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        symbols_by_name = {s.symbol_name: s for s in result.symbols}
        assert symbols_by_name["A"].line_start == 1
        assert symbols_by_name["B"].line_start == 3

    # ========== Complex Unpacking Patterns ==========

    def test_nested_tuple_unpacking(self, extractor, temp_dir):
        """Test nested tuple unpacking extracts all targets."""
        code = "(a, (b, c)) = (1, (2, 3))"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 3
        names = {s.symbol_name for s in variable_symbols}
        assert names == {"a", "b", "c"}

    def test_list_unpacking(self, extractor, temp_dir):
        """Test list unpacking works like tuple unpacking."""
        code = "[a, b, c] = [1, 2, 3]"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 3
        names = {s.symbol_name for s in variable_symbols}
        assert names == {"a", "b", "c"}

    def test_starred_unpacking(self, extractor, temp_dir):
        """Test starred expression in unpacking."""
        code = "first, *middle, last = range(10)"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 3
        names = {s.symbol_name for s in variable_symbols}
        assert names == {"first", "middle", "last"}

    def test_chained_assignment(self, extractor, temp_dir):
        """Test chained assignment creates multiple symbols."""
        code = "a = b = c = 1"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 3
        names = {s.symbol_name for s in variable_symbols}
        assert names == {"a", "b", "c"}
        # All should be on the same line
        for var in variable_symbols:
            assert var.line_start == 1

    # ========== Non-Variable Assignments (Should NOT Extract) ==========

    def test_attribute_assignment_not_extracted(self, extractor, temp_dir):
        """Test attribute assignments are not extracted as variables."""
        code = "import sys\nsys.path = []\nVAR = 1"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 1
        assert variable_symbols[0].symbol_name == "VAR"

    def test_subscript_assignment_not_extracted(self, extractor, temp_dir):
        """Test subscript assignments are not extracted."""
        code = "data = {}\ndata['key'] = 1\nVAR = 2"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 2
        names = {s.symbol_name for s in variable_symbols}
        assert names == {"data", "VAR"}

    def test_augmented_assignment_not_extracted(self, extractor, temp_dir):
        """Test augmented assignments (+=, -=) don't create new variables."""
        code = "counter = 0\ncounter += 1"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 1
        assert variable_symbols[0].symbol_name == "counter"

    # ========== Control Flow Scope (Should NOT Extract) ==========

    def test_variable_in_if_block_not_extracted(self, extractor, temp_dir):
        """Test variables inside if blocks are not module-level."""
        code = "if True:\n    x = 1\nMODULE_VAR = 2"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 1
        assert variable_symbols[0].symbol_name == "MODULE_VAR"

    def test_variable_in_for_loop_not_extracted(self, extractor, temp_dir):
        """Test loop variables and body variables are not extracted."""
        code = "for i in range(10):\n    x = i\nMODULE_VAR = 2"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 1
        assert variable_symbols[0].symbol_name == "MODULE_VAR"

    def test_variable_in_try_except_not_extracted(self, extractor, temp_dir):
        """Test variables in try/except blocks are not extracted."""
        code = "try:\n    x = 1\nexcept:\n    y = 2\nMODULE_VAR = 3"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 1
        assert variable_symbols[0].symbol_name == "MODULE_VAR"

    def test_variable_in_with_block_not_extracted(self, extractor, temp_dir):
        """Test with-statement context variables are not extracted."""
        code = "with open('f') as f:\n    x = 1\nMODULE_VAR = 2"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 1
        assert variable_symbols[0].symbol_name == "MODULE_VAR"

    def test_variable_in_while_loop_not_extracted(self, extractor, temp_dir):
        """Test variables in while loops are not extracted."""
        code = "while True:\n    x = 1\n    break\nMODULE_VAR = 2"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 1
        assert variable_symbols[0].symbol_name == "MODULE_VAR"

    def test_variable_in_main_block_not_extracted(self, extractor, temp_dir):
        """Test if __name__ == '__main__' block variables not extracted."""
        code = "VAR = 1\nif __name__ == '__main__':\n    x = 2"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 1
        assert variable_symbols[0].symbol_name == "VAR"

    # ========== Annotation Edge Cases ==========

    def test_annotated_without_value(self, extractor, temp_dir):
        """Test annotated variable without assignment is not extracted.

        Python's AST treats `x: int` (no value) differently from `x: int = 1`.
        The AnnAssign node has value=None when there's no assignment.
        We only extract when there's an actual assignment.
        """
        code = "x: int\nVAR: str = 'hello'"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        # x: int has no value, so shouldn't create a variable in runtime sense
        # VAR: str = 'hello' has a value, so should be extracted
        assert len(variable_symbols) == 1
        assert variable_symbols[0].symbol_name == "VAR"

    def test_complex_type_annotation(self, extractor, temp_dir):
        """Test variable with complex type annotation."""
        code = "data: dict[str, list[int]] = {}"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 1
        assert variable_symbols[0].symbol_name == "data"

    # ========== Parity and Interaction Tests ==========

    def test_variable_alongside_function_class(self, extractor, temp_dir):
        """Test variables coexist correctly with functions and classes."""
        code = '''VAR1 = 1
def func(): pass
VAR2 = 2
class Cls: pass
VAR3 = 3
'''
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        # Should extract 3 variables + 1 function + 1 class = 5 symbols
        assert len(result.symbols) == 5

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        function_symbols = [s for s in result.symbols if s.symbol_type == "function"]
        class_symbols = [s for s in result.symbols if s.symbol_type == "class"]

        assert len(variable_symbols) == 3
        assert len(function_symbols) == 1
        assert len(class_symbols) == 1

        var_names = {s.symbol_name for s in variable_symbols}
        assert var_names == {"VAR1", "VAR2", "VAR3"}
        assert function_symbols[0].symbol_name == "func"
        assert class_symbols[0].symbol_name == "Cls"

    def test_walrus_operator_not_extracted(self, extractor, temp_dir):
        """Test walrus operator (:=) assignments are not extracted as module variables."""
        code = "if (n := 10) > 5:\n    pass\nVAR = 1"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.py")

        variable_symbols = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variable_symbols) == 1
        assert variable_symbols[0].symbol_name == "VAR"
