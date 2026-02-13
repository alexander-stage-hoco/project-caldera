"""Unit tests for JavaScript/TypeScript call resolver."""

from __future__ import annotations

from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from extractors.base import ExtractedCall, ExtractedImport, ExtractedSymbol
from extractors.js_call_resolver import JSCallResolver, NODE_BUILTINS, JS_GLOBALS


class TestJSCallResolver:
    """Tests for JSCallResolver."""

    @pytest.fixture
    def basic_symbols(self):
        """Symbols from a simple two-file JS project."""
        return [
            ExtractedSymbol(
                path="utils.js", symbol_name="greet", symbol_type="function",
                line_start=1, line_end=3, is_exported=True, parameters=1,
                parent_symbol=None, docstring=None,
            ),
            ExtractedSymbol(
                path="utils.js", symbol_name="helper", symbol_type="function",
                line_start=5, line_end=7, is_exported=True, parameters=0,
                parent_symbol=None, docstring=None,
            ),
            ExtractedSymbol(
                path="main.js", symbol_name="main", symbol_type="function",
                line_start=3, line_end=6, is_exported=False, parameters=0,
                parent_symbol=None, docstring=None,
            ),
        ]

    @pytest.fixture
    def basic_imports(self):
        """Imports for a simple two-file JS project."""
        return [
            ExtractedImport(
                file="main.js", imported_path="./utils",
                imported_symbols="greet,helper", import_type="static",
                line_number=1,
            ),
        ]

    # ============ Same-File Resolution ============

    def test_resolve_same_file(self, basic_symbols, basic_imports):
        """Test that calls to functions in the same file resolve correctly."""
        calls = [
            ExtractedCall(
                caller_file="utils.js", caller_symbol="greet",
                callee_symbol="helper", callee_file=None,
                line_number=2, call_type="direct",
            ),
        ]

        repo_root = Path("/fake/repo")
        resolver = JSCallResolver(repo_root, basic_symbols, basic_imports)
        resolved = resolver.resolve(calls)

        assert resolved[0].callee_file == "utils.js"
        assert resolver.stats.resolved_same_file == 1

    # ============ Cross-File Resolution ============

    def test_resolve_cross_file_named_import(self, basic_symbols, basic_imports):
        """Test resolution of named imports across files."""
        calls = [
            ExtractedCall(
                caller_file="main.js", caller_symbol="main",
                callee_symbol="greet", callee_file=None,
                line_number=4, call_type="direct",
            ),
        ]

        repo_root = Path("/fake/repo")
        resolver = JSCallResolver(repo_root, basic_symbols, basic_imports)
        resolved = resolver.resolve(calls)

        assert resolved[0].callee_file == "utils.js"
        assert resolver.stats.resolved_cross_file == 1

    # ============ JS Globals ============

    def test_resolve_js_global(self):
        """Test that JS globals (console, setTimeout, etc.) resolve to None."""
        symbols = [
            ExtractedSymbol(
                path="main.js", symbol_name="main", symbol_type="function",
                line_start=1, line_end=3, is_exported=False, parameters=0,
                parent_symbol=None, docstring=None,
            ),
        ]
        calls = [
            ExtractedCall(
                caller_file="main.js", caller_symbol="main",
                callee_symbol="setTimeout", callee_file=None,
                line_number=2, call_type="direct",
            ),
        ]

        resolver = JSCallResolver(Path("/fake"), symbols, [])
        resolved = resolver.resolve(calls)

        assert resolved[0].callee_file is None
        assert resolver.stats.unresolved_builtin == 1

    # ============ Node.js Builtins ============

    def test_node_builtins_not_resolved(self):
        """Test that imports from Node.js builtins don't resolve to files."""
        symbols = [
            ExtractedSymbol(
                path="main.js", symbol_name="main", symbol_type="function",
                line_start=1, line_end=3, is_exported=False, parameters=0,
                parent_symbol=None, docstring=None,
            ),
        ]
        imports = [
            ExtractedImport(
                file="main.js", imported_path="fs",
                imported_symbols="readFile", import_type="static",
                line_number=1,
            ),
        ]
        calls = [
            ExtractedCall(
                caller_file="main.js", caller_symbol="main",
                callee_symbol="readFile", callee_file=None,
                line_number=3, call_type="direct",
            ),
        ]

        resolver = JSCallResolver(Path("/fake"), symbols, imports)
        resolved = resolver.resolve(calls)

        # readFile is from Node builtin fs, should not resolve
        assert resolved[0].callee_file is None

    # ============ Bare Specifiers (npm) ============

    def test_bare_specifier_not_resolved(self):
        """Test that npm package imports don't resolve to repo files."""
        symbols = [
            ExtractedSymbol(
                path="app.js", symbol_name="app", symbol_type="function",
                line_start=1, line_end=3, is_exported=True, parameters=0,
                parent_symbol=None, docstring=None,
            ),
        ]
        imports = [
            ExtractedImport(
                file="app.js", imported_path="express",
                imported_symbols=None, import_type="static",
                line_number=1, module_alias="express",
            ),
        ]
        calls = [
            ExtractedCall(
                caller_file="app.js", caller_symbol="app",
                callee_symbol="listen", callee_file=None,
                line_number=5, call_type="dynamic",
                callee_object="express",
            ),
        ]

        resolver = JSCallResolver(Path("/fake"), symbols, imports)
        resolved = resolver.resolve(calls)

        # express is a bare specifier (npm), should not resolve
        assert resolved[0].callee_file is None

    # ============ Relative Path Resolution ============

    def test_resolve_relative_import_with_extension(self):
        """Test resolution of relative imports that need extension appending."""
        symbols = [
            ExtractedSymbol(
                path="lib/utils.js", symbol_name="format", symbol_type="function",
                line_start=1, line_end=3, is_exported=True, parameters=1,
                parent_symbol=None, docstring=None,
            ),
            ExtractedSymbol(
                path="main.js", symbol_name="main", symbol_type="function",
                line_start=3, line_end=5, is_exported=False, parameters=0,
                parent_symbol=None, docstring=None,
            ),
        ]
        imports = [
            ExtractedImport(
                file="main.js", imported_path="./lib/utils",
                imported_symbols="format", import_type="static",
                line_number=1,
            ),
        ]
        calls = [
            ExtractedCall(
                caller_file="main.js", caller_symbol="main",
                callee_symbol="format", callee_file=None,
                line_number=4, call_type="direct",
            ),
        ]

        resolver = JSCallResolver(Path("/fake"), symbols, imports)
        resolved = resolver.resolve(calls)

        assert resolved[0].callee_file == "lib/utils.js"

    def test_resolve_index_file(self):
        """Test resolution of imports pointing to directory with index file."""
        symbols = [
            ExtractedSymbol(
                path="utils/index.js", symbol_name="foo", symbol_type="function",
                line_start=1, line_end=2, is_exported=True, parameters=0,
                parent_symbol=None, docstring=None,
            ),
            ExtractedSymbol(
                path="main.js", symbol_name="main", symbol_type="function",
                line_start=3, line_end=5, is_exported=False, parameters=0,
                parent_symbol=None, docstring=None,
            ),
        ]
        imports = [
            ExtractedImport(
                file="main.js", imported_path="./utils",
                imported_symbols="foo", import_type="static",
                line_number=1,
            ),
        ]
        calls = [
            ExtractedCall(
                caller_file="main.js", caller_symbol="main",
                callee_symbol="foo", callee_file=None,
                line_number=4, call_type="direct",
            ),
        ]

        resolver = JSCallResolver(Path("/fake"), symbols, imports)
        resolved = resolver.resolve(calls)

        assert resolved[0].callee_file == "utils/index.js"

    # ============ Module Alias Resolution ============

    def test_resolve_module_alias_call(self):
        """Test resolution of module.function() pattern."""
        symbols = [
            ExtractedSymbol(
                path="utils.js", symbol_name="validate", symbol_type="function",
                line_start=1, line_end=3, is_exported=True, parameters=1,
                parent_symbol=None, docstring=None,
            ),
            ExtractedSymbol(
                path="main.js", symbol_name="main", symbol_type="function",
                line_start=3, line_end=5, is_exported=False, parameters=0,
                parent_symbol=None, docstring=None,
            ),
        ]
        imports = [
            ExtractedImport(
                file="main.js", imported_path="./utils",
                imported_symbols="*", import_type="static",
                line_number=1, module_alias="utils",
            ),
        ]
        calls = [
            ExtractedCall(
                caller_file="main.js", caller_symbol="main",
                callee_symbol="validate", callee_file=None,
                line_number=4, call_type="dynamic",
                callee_object="utils",
            ),
        ]

        resolver = JSCallResolver(Path("/fake"), symbols, imports)
        resolved = resolver.resolve(calls)

        assert resolved[0].callee_file == "utils.js"
        assert resolver.stats.resolved_module_attr == 1

    # ============ this/super Skip ============

    def test_this_calls_unresolved(self):
        """Test that this.method() calls are classified as unresolved dynamic."""
        symbols = [
            ExtractedSymbol(
                path="class.js", symbol_name="MyClass", symbol_type="class",
                line_start=1, line_end=10, is_exported=True, parameters=None,
                parent_symbol=None, docstring=None,
            ),
        ]
        calls = [
            ExtractedCall(
                caller_file="class.js", caller_symbol="method",
                callee_symbol="other", callee_file=None,
                line_number=5, call_type="dynamic",
                callee_object="this",
            ),
        ]

        resolver = JSCallResolver(Path("/fake"), symbols, [])
        resolved = resolver.resolve(calls)

        assert resolved[0].callee_file is None
        assert resolver.stats.unresolved_dynamic == 1

    # ============ Constants Coverage ============

    def test_node_builtins_contains_common_modules(self):
        """Verify common Node.js built-in modules are in the set."""
        for module in ("fs", "path", "http", "crypto", "os", "net", "stream"):
            assert module in NODE_BUILTINS

    def test_js_globals_contains_common_functions(self):
        """Verify common JS globals are in the set."""
        for fn in ("console", "setTimeout", "fetch", "JSON", "Math", "Promise"):
            assert fn in JS_GLOBALS
