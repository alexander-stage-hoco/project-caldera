"""Integration tests verifying AST and tree-sitter extractors produce identical results."""

from __future__ import annotations

from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from extractors import PythonExtractor, TreeSitterExtractor


class TestExtractorParity:
    """Verify AST and tree-sitter produce identical results on valid Python code."""

    @pytest.fixture
    def ast_extractor(self):
        return PythonExtractor()

    @pytest.fixture
    def ts_extractor(self):
        return TreeSitterExtractor()

    def _assert_symbols_match(self, ast_symbols, ts_symbols):
        """Assert that symbols from both extractors match."""
        # Compare by (path, name, type) - these are the core identity fields
        ast_set = {
            (s.path, s.symbol_name, s.symbol_type)
            for s in ast_symbols
        }
        ts_set = {
            (s.path, s.symbol_name, s.symbol_type)
            for s in ts_symbols
        }

        only_ast = ast_set - ts_set
        only_ts = ts_set - ast_set

        if only_ast or only_ts:
            msg = []
            if only_ast:
                msg.append(f"Only in AST: {only_ast}")
            if only_ts:
                msg.append(f"Only in tree-sitter: {only_ts}")
            pytest.fail("\n".join(msg))

        # Also verify other fields match
        ast_by_key = {(s.path, s.symbol_name, s.symbol_type): s for s in ast_symbols}
        ts_by_key = {(s.path, s.symbol_name, s.symbol_type): s for s in ts_symbols}

        for key in ast_by_key:
            ast_s = ast_by_key[key]
            ts_s = ts_by_key[key]

            assert ast_s.is_exported == ts_s.is_exported, f"is_exported mismatch for {key}"
            assert ast_s.parameters == ts_s.parameters, f"parameters mismatch for {key}: AST={ast_s.parameters}, TS={ts_s.parameters}"
            assert ast_s.parent_symbol == ts_s.parent_symbol, f"parent_symbol mismatch for {key}"
            # Line numbers should be close (tree-sitter may differ by 1 for some edge cases)
            assert abs(ast_s.line_start - ts_s.line_start) <= 1, f"line_start mismatch for {key}: AST={ast_s.line_start}, TS={ts_s.line_start}"
            assert abs(ast_s.line_end - ts_s.line_end) <= 1, f"line_end mismatch for {key}: AST={ast_s.line_end}, TS={ts_s.line_end}"

    def _assert_calls_match(self, ast_calls, ts_calls):
        """Assert that calls from both extractors match."""
        # Compare by (caller_file, caller_symbol, callee_symbol, line)
        ast_set = {
            (c.caller_file, c.caller_symbol, c.callee_symbol, c.line_number)
            for c in ast_calls
        }
        ts_set = {
            (c.caller_file, c.caller_symbol, c.callee_symbol, c.line_number)
            for c in ts_calls
        }

        only_ast = ast_set - ts_set
        only_ts = ts_set - ast_set

        if only_ast or only_ts:
            msg = []
            if only_ast:
                msg.append(f"Only in AST: {only_ast}")
            if only_ts:
                msg.append(f"Only in tree-sitter: {only_ts}")
            pytest.fail("\n".join(msg))

    def _assert_imports_match(self, ast_imports, ts_imports):
        """Assert that imports from both extractors match."""
        # Compare by (file, path, symbols, type)
        ast_set = {
            (i.file, i.imported_path, i.imported_symbols, i.import_type)
            for i in ast_imports
        }
        ts_set = {
            (i.file, i.imported_path, i.imported_symbols, i.import_type)
            for i in ts_imports
        }

        only_ast = ast_set - ts_set
        only_ts = ts_set - ast_set

        if only_ast or only_ts:
            msg = []
            if only_ast:
                msg.append(f"Only in AST: {only_ast}")
            if only_ts:
                msg.append(f"Only in tree-sitter: {only_ts}")
            pytest.fail("\n".join(msg))

    def test_simple_functions_parity(self, ast_extractor, ts_extractor, temp_dir, simple_function_code):
        """Test parity on simple function code."""
        test_file = temp_dir / "test.py"
        test_file.write_text(simple_function_code)

        ast_result = ast_extractor.extract_file(test_file, "test.py")
        ts_result = ts_extractor.extract_file(test_file, "test.py")

        self._assert_symbols_match(ast_result.symbols, ts_result.symbols)
        self._assert_calls_match(ast_result.calls, ts_result.calls)
        self._assert_imports_match(ast_result.imports, ts_result.imports)

    def test_class_code_parity(self, ast_extractor, ts_extractor, temp_dir, class_code):
        """Test parity on class/method code."""
        test_file = temp_dir / "test.py"
        test_file.write_text(class_code)

        ast_result = ast_extractor.extract_file(test_file, "test.py")
        ts_result = ts_extractor.extract_file(test_file, "test.py")

        self._assert_symbols_match(ast_result.symbols, ts_result.symbols)
        self._assert_calls_match(ast_result.calls, ts_result.calls)
        self._assert_imports_match(ast_result.imports, ts_result.imports)

    def test_import_code_parity(self, ast_extractor, ts_extractor, temp_dir, import_code):
        """Test parity on import statements."""
        test_file = temp_dir / "test.py"
        test_file.write_text(import_code)

        ast_result = ast_extractor.extract_file(test_file, "test.py")
        ts_result = ts_extractor.extract_file(test_file, "test.py")

        self._assert_symbols_match(ast_result.symbols, ts_result.symbols)
        self._assert_imports_match(ast_result.imports, ts_result.imports)

    def test_cross_module_repo_parity(self, ast_extractor, ts_extractor, cross_module_repo):
        """Test parity on a multi-file repository."""
        ast_result = ast_extractor.extract_directory(cross_module_repo, resolve_calls=False)
        ts_result = ts_extractor.extract_directory(cross_module_repo, resolve_calls=False)

        self._assert_symbols_match(ast_result.symbols, ts_result.symbols)
        self._assert_calls_match(ast_result.calls, ts_result.calls)
        self._assert_imports_match(ast_result.imports, ts_result.imports)

    def test_async_code_parity(self, ast_extractor, ts_extractor, temp_dir):
        """Test parity on async code."""
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

        ast_result = ast_extractor.extract_file(test_file, "async_test.py")
        ts_result = ts_extractor.extract_file(test_file, "async_test.py")

        self._assert_symbols_match(ast_result.symbols, ts_result.symbols)
        self._assert_calls_match(ast_result.calls, ts_result.calls)

    def test_nested_functions_parity(self, ast_extractor, ts_extractor, temp_dir):
        """Test parity on nested functions."""
        code = '''
def outer():
    def inner():
        pass
    inner()
'''
        test_file = temp_dir / "nested.py"
        test_file.write_text(code)

        ast_result = ast_extractor.extract_file(test_file, "nested.py")
        ts_result = ts_extractor.extract_file(test_file, "nested.py")

        self._assert_symbols_match(ast_result.symbols, ts_result.symbols)
        self._assert_calls_match(ast_result.calls, ts_result.calls)

    def test_decorator_parity(self, ast_extractor, ts_extractor, temp_dir):
        """Test parity on decorated functions."""
        code = '''
def decorator(func):
    return func

@decorator
def decorated_func():
    pass

class MyClass:
    @staticmethod
    def static_method():
        pass

    @classmethod
    def class_method(cls):
        pass

    @property
    def my_property(self):
        return self._value
'''
        test_file = temp_dir / "decorated.py"
        test_file.write_text(code)

        ast_result = ast_extractor.extract_file(test_file, "decorated.py")
        ts_result = ts_extractor.extract_file(test_file, "decorated.py")

        self._assert_symbols_match(ast_result.symbols, ts_result.symbols)

    def test_complex_parameters_parity(self, ast_extractor, ts_extractor, temp_dir):
        """Test parity on functions with complex parameter patterns."""
        code = '''
def simple(a, b, c):
    pass

def with_defaults(a, b=1, c="hello"):
    pass

def with_types(a: int, b: str = "x") -> None:
    pass

def with_args(*args, **kwargs):
    pass

def positional_only(a, /, b, c):
    pass

def keyword_only(a, *, b, c):
    pass

def combined(a, /, b, *args, c, d=1, **kwargs):
    pass
'''
        test_file = temp_dir / "params.py"
        test_file.write_text(code)

        ast_result = ast_extractor.extract_file(test_file, "params.py")
        ts_result = ts_extractor.extract_file(test_file, "params.py")

        self._assert_symbols_match(ast_result.symbols, ts_result.symbols)

    def test_synthetic_repo_parity(self, ast_extractor, ts_extractor):
        """Test parity on actual synthetic eval repos if they exist."""
        eval_repos = Path(__file__).resolve().parents[2] / "eval-repos" / "synthetic"
        if not eval_repos.exists():
            pytest.skip("Eval repos not found")

        for repo_dir in eval_repos.iterdir():
            if not repo_dir.is_dir():
                continue

            # Skip repos designed to test syntax error recovery (expected to differ)
            if "syntax-error" in repo_dir.name:
                continue

            # Skip repos without Python files
            py_files = list(repo_dir.glob("**/*.py"))
            if not py_files:
                continue

            ast_result = ast_extractor.extract_directory(repo_dir, resolve_calls=False)
            ts_result = ts_extractor.extract_directory(repo_dir, resolve_calls=False)

            try:
                self._assert_symbols_match(ast_result.symbols, ts_result.symbols)
                self._assert_calls_match(ast_result.calls, ts_result.calls)
                self._assert_imports_match(ast_result.imports, ts_result.imports)
            except AssertionError as e:
                pytest.fail(f"Parity failed for {repo_dir.name}: {e}")


class TestExtractorDifferences:
    """Tests that document expected differences between extractors."""

    @pytest.fixture
    def ast_extractor(self):
        return PythonExtractor()

    @pytest.fixture
    def ts_extractor(self):
        return TreeSitterExtractor()

    def test_syntax_error_recovery(self, ast_extractor, ts_extractor, temp_dir):
        """Tree-sitter should recover from syntax errors better than AST."""
        code = '''
def valid_before():
    return 1

def broken(:  # Syntax error
    pass

def valid_after():
    return 2
'''
        test_file = temp_dir / "mixed.py"
        test_file.write_text(code)

        ast_result = ast_extractor.extract_file(test_file, "mixed.py")
        ts_result = ts_extractor.extract_file(test_file, "mixed.py")

        # AST should fail completely and extract nothing
        assert len(ast_result.symbols) == 0
        assert len(ast_result.errors) == 1

        # Tree-sitter should recover and extract valid parts
        assert len(ts_result.errors) == 1  # Error recorded
        ts_names = {s.symbol_name for s in ts_result.symbols}
        assert "valid_before" in ts_names
        assert "valid_after" in ts_names
