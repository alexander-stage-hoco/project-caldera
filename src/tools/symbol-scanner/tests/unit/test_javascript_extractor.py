"""Unit tests for JavaScript tree-sitter extractor."""

from __future__ import annotations

from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from extractors.javascript_treesitter_extractor import JavaScriptTreeSitterExtractor


class TestJavaScriptTreeSitterExtractor:
    """Tests for JavaScriptTreeSitterExtractor."""

    @pytest.fixture
    def extractor(self):
        return JavaScriptTreeSitterExtractor()

    # ============ Basic Properties ============

    def test_language_property(self, extractor):
        assert extractor.language == "javascript"

    def test_file_extensions(self, extractor):
        assert ".js" in extractor.file_extensions
        assert ".mjs" in extractor.file_extensions
        assert ".jsx" in extractor.file_extensions

    # ============ Function Declarations ============

    def test_extract_function_declaration(self, extractor, temp_dir):
        """Test extraction of a named function declaration."""
        code = 'function greet(name) {\n    return "Hello, " + name;\n}\n'
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        functions = [s for s in result.symbols if s.symbol_type == "function"]
        assert len(functions) == 1
        assert functions[0].symbol_name == "greet"
        assert functions[0].parameters == 1
        assert functions[0].is_exported is False

    def test_extract_exported_function(self, extractor, temp_dir):
        """Test extraction of an exported function."""
        code = 'export function add(a, b) {\n    return a + b;\n}\n'
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        functions = [s for s in result.symbols if s.symbol_type == "function"]
        assert len(functions) == 1
        assert functions[0].symbol_name == "add"
        assert functions[0].is_exported is True
        assert functions[0].parameters == 2

    def test_extract_arrow_function(self, extractor, temp_dir):
        """Test extraction of arrow function assigned to const."""
        code = "const multiply = (a, b) => a * b;\n"
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        functions = [s for s in result.symbols if s.symbol_type == "function"]
        assert len(functions) == 1
        assert functions[0].symbol_name == "multiply"
        assert functions[0].parameters == 2

    def test_extract_generator_function(self, extractor, temp_dir):
        """Test extraction of a generator function."""
        code = "function* range(start, end) {\n    for (let i = start; i < end; i++) yield i;\n}\n"
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        functions = [s for s in result.symbols if s.symbol_type == "function"]
        assert len(functions) == 1
        assert functions[0].symbol_name == "range"
        assert functions[0].parameters == 2

    def test_extract_export_default_class(self, extractor, temp_dir):
        """Test extraction of export default class."""
        code = "export default class Greeter {\n    greet() { return 'hi'; }\n}\n"
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "Greeter"
        assert classes[0].is_exported is True

    # ============ Class & Method Extraction ============

    def test_extract_class_with_methods(self, extractor, temp_dir):
        """Test extraction of class with methods."""
        code = """export class Calculator {
    constructor(initial) {
        this.value = initial;
    }

    add(x) {
        this.value += x;
        return this;
    }

    #secret() {
        return 42;
    }
}
"""
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "Calculator"
        assert classes[0].is_exported is True

        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}
        assert "constructor" in method_names
        assert "add" in method_names
        assert "#secret" in method_names

        # Private method
        secret = next(m for m in methods if m.symbol_name == "#secret")
        assert secret.is_exported is False
        assert secret.parent_symbol == "Calculator"

    # ============ Variable Extraction ============

    def test_extract_module_variable(self, extractor, temp_dir):
        """Test extraction of module-level const."""
        code = 'export const VERSION = "1.0.0";\nconst internal = 42;\n'
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        variables = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variables) == 2

        exported = next(v for v in variables if v.symbol_name == "VERSION")
        assert exported.is_exported is True

        private = next(v for v in variables if v.symbol_name == "internal")
        assert private.is_exported is False

    # ============ Call Extraction ============

    def test_extract_direct_call(self, extractor, temp_dir):
        """Test extraction of direct function calls."""
        code = "function main() {\n    foo();\n    bar(1, 2);\n}\n"
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        direct_calls = [c for c in result.calls if c.call_type == "direct"]
        callee_names = {c.callee_symbol for c in direct_calls}
        assert "foo" in callee_names
        assert "bar" in callee_names
        # All calls should have caller_symbol = main
        for call in direct_calls:
            assert call.caller_symbol == "main"

    def test_extract_member_call(self, extractor, temp_dir):
        """Test extraction of object method calls."""
        code = "function test() {\n    obj.method();\n    console.log('hi');\n}\n"
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        dynamic_calls = [c for c in result.calls if c.call_type == "dynamic"]
        assert len(dynamic_calls) == 2

        method_call = next(c for c in dynamic_calls if c.callee_symbol == "method")
        assert method_call.callee_object == "obj"

        log_call = next(c for c in dynamic_calls if c.callee_symbol == "log")
        assert log_call.callee_object == "console"

    def test_extract_async_call(self, extractor, temp_dir):
        """Test extraction of awaited calls as async type."""
        code = "async function load() {\n    const data = await fetchData();\n    return data;\n}\n"
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        async_calls = [c for c in result.calls if c.call_type == "async"]
        assert len(async_calls) == 1
        assert async_calls[0].callee_symbol == "fetchData"
        assert async_calls[0].caller_symbol == "load"

    def test_extract_constructor_call(self, extractor, temp_dir):
        """Test extraction of new expression."""
        code = "function test() {\n    const m = new Map();\n    const d = new Date();\n}\n"
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        constructors = [c for c in result.calls if c.call_type == "constructor"]
        callee_names = {c.callee_symbol for c in constructors}
        assert "Map" in callee_names
        assert "Date" in callee_names

    def test_extract_eval_as_dynamic_exec(self, extractor, temp_dir):
        """Test that eval() is flagged as dynamic code execution."""
        code = 'function danger() {\n    eval("code");\n}\n'
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        eval_calls = [c for c in result.calls if c.callee_symbol == "eval"]
        assert len(eval_calls) == 1
        assert eval_calls[0].is_dynamic_code_execution is True

    # ============ Import Extraction ============

    def test_extract_named_imports(self, extractor, temp_dir):
        """Test extraction of named imports."""
        code = 'import { foo, bar } from "./utils";\n'
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        assert len(result.imports) == 1
        imp = result.imports[0]
        assert imp.imported_path == "./utils"
        assert imp.imported_symbols == "foo,bar"
        assert imp.import_type == "static"

    def test_extract_default_import(self, extractor, temp_dir):
        """Test extraction of default import."""
        code = 'import React from "react";\n'
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        assert len(result.imports) == 1
        imp = result.imports[0]
        assert imp.imported_path == "react"
        assert imp.imported_symbols is None
        assert imp.module_alias == "React"
        assert imp.import_type == "static"

    def test_extract_star_import(self, extractor, temp_dir):
        """Test extraction of namespace import."""
        code = 'import * as utils from "./utils";\n'
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        assert len(result.imports) == 1
        imp = result.imports[0]
        assert imp.imported_path == "./utils"
        assert imp.imported_symbols == "*"
        assert imp.module_alias == "utils"

    def test_extract_side_effect_import(self, extractor, temp_dir):
        """Test extraction of side-effect import."""
        code = 'import "./styles.css";\n'
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        assert len(result.imports) == 1
        imp = result.imports[0]
        assert imp.imported_path == "./styles.css"
        assert imp.import_type == "side_effect"
        assert imp.imported_symbols is None

    def test_extract_dynamic_import(self, extractor, temp_dir):
        """Test extraction of dynamic import()."""
        code = 'async function load() {\n    const mod = await import("./lazy");\n}\n'
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        dynamic_imports = [i for i in result.imports if i.import_type == "dynamic"]
        assert len(dynamic_imports) == 1
        assert dynamic_imports[0].imported_path == "./lazy"

    def test_extract_require_as_import(self, extractor, temp_dir):
        """Test extraction of require() as dynamic import."""
        code = 'const fs = require("fs");\nconst mod = require("./local");\n'
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        dynamic_imports = [i for i in result.imports if i.import_type == "dynamic"]
        assert len(dynamic_imports) == 2
        paths = {i.imported_path for i in dynamic_imports}
        assert "fs" in paths
        assert "./local" in paths

    # ============ JSDoc Extraction ============

    def test_extract_jsdoc(self, extractor, temp_dir):
        """Test JSDoc comment extraction."""
        code = """/**
 * Compute the sum of two values.
 * @param {number} a - First value
 * @param {number} b - Second value
 */
function add(a, b) {
    return a + b;
}
"""
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        func = result.symbols[0]
        assert func.docstring is not None
        assert "sum" in func.docstring.lower()

    # ============ Export Detection ============

    def test_export_detection(self, extractor, temp_dir):
        """Test various export patterns."""
        code = """export function exported1() {}
export const exported2 = () => {};
function notExported() {}
const alsoNotExported = 42;
export default class DefaultExport {}
"""
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        symbol_map = {s.symbol_name: s for s in result.symbols}
        assert symbol_map["exported1"].is_exported is True
        assert symbol_map["exported2"].is_exported is True
        assert symbol_map["notExported"].is_exported is False
        assert symbol_map["alsoNotExported"].is_exported is False
        assert symbol_map["DefaultExport"].is_exported is True

    # ============ Directory Extraction ============

    def test_extract_directory(self, extractor):
        """Test full directory extraction with call resolution."""
        repo = Path(__file__).resolve().parents[2] / "eval-repos" / "synthetic" / "js-simple-functions"
        if not repo.exists():
            pytest.skip("js-simple-functions eval repo not found")

        result = extractor.extract_directory(repo, repo)

        assert len(result.symbols) >= 6
        assert len(result.imports) >= 2
        assert len(result.calls) >= 5

        # Check cross-file resolution worked
        resolved = [c for c in result.calls if c.callee_file is not None]
        assert len(resolved) >= 4

    # ============ Syntax Error Recovery ============

    def test_syntax_error_recovery(self, extractor, temp_dir):
        """Test that partial extraction works on malformed code."""
        code = "function valid() { return 1; }\nfunction broken( { incomplete\nfunction alsoValid() { return 2; }\n"
        test_file = temp_dir / "test.js"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.js")

        # Should have syntax error recorded
        assert len(result.errors) > 0
        assert result.errors[0]["code"] == "SYNTAX_ERROR"

        # Should still extract valid functions
        assert len(result.symbols) >= 1
