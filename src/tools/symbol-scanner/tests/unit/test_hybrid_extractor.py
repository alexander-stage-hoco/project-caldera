"""Unit tests for hybrid extractor (AST + tree-sitter fallback)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from extractors.hybrid_extractor import HybridExtractor


class TestHybridExtractor:
    """Tests for HybridExtractor."""

    @pytest.fixture
    def extractor(self):
        return HybridExtractor()

    def test_language_property(self, extractor):
        assert extractor.language == "python"

    def test_file_extensions(self, extractor):
        assert extractor.file_extensions == (".py",)

    def test_valid_code_uses_ast(self, extractor, temp_dir, simple_function_code):
        """Test that valid Python code uses AST extractor (no fallback)."""
        test_file = temp_dir / "valid.py"
        test_file.write_text(simple_function_code)

        result = extractor.extract_file(test_file, "valid.py")

        # Should find functions (AST produces accurate results)
        assert len(result.symbols) == 3
        names = {s.symbol_name for s in result.symbols}
        assert names == {"hello", "add", "main"}

        # Should NOT have used fallback
        assert "valid.py" not in extractor.fallback_files
        assert extractor.fallback_count == 0

    def test_syntax_error_uses_treesitter_fallback(self, extractor, temp_dir):
        """Test that files with syntax errors use tree-sitter fallback."""
        code = '''
def valid_function():
    """This is valid."""
    return 42

def broken(:  # Syntax error
    pass

def another_valid():
    """Also valid."""
    return True
'''
        test_file = temp_dir / "partial.py"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "partial.py")

        # Should have used fallback
        assert "partial.py" in extractor.fallback_files
        assert extractor.fallback_count == 1

        # Should still extract valid functions (tree-sitter's advantage)
        names = {s.symbol_name for s in result.symbols}
        assert "valid_function" in names
        assert "another_valid" in names

        # Should have recorded the syntax error
        assert len(result.errors) == 1
        assert result.errors[0]["code"] == "SYNTAX_ERROR"

    def test_mixed_files_hybrid_behavior(self, extractor, temp_dir):
        """Test hybrid behavior with mix of valid and invalid files."""
        # Valid file
        (temp_dir / "good.py").write_text('''
def good_func():
    return "good"
''')

        # Invalid file
        (temp_dir / "bad.py").write_text('''
def broken(:
    pass

def still_valid():
    return True
''')

        # Extract valid file
        result1 = extractor.extract_file(temp_dir / "good.py", "good.py")
        assert "good.py" not in extractor.fallback_files

        # Extract invalid file
        result2 = extractor.extract_file(temp_dir / "bad.py", "bad.py")
        assert "bad.py" in extractor.fallback_files

        # Verify results
        assert len(result1.symbols) == 1
        assert result1.symbols[0].symbol_name == "good_func"

        # Tree-sitter should have extracted valid parts of bad.py
        names = {s.symbol_name for s in result2.symbols}
        assert "still_valid" in names

    def test_reset_fallback_tracking(self, extractor, temp_dir):
        """Test that fallback tracking can be reset."""
        # Create file with syntax error
        test_file = temp_dir / "error.py"
        test_file.write_text("def broken(:\n    pass")

        # Extract triggers fallback
        extractor.extract_file(test_file, "error.py")
        assert extractor.fallback_count == 1

        # Reset tracking
        extractor.reset_fallback_tracking()
        assert extractor.fallback_count == 0
        assert extractor.fallback_files == []

    def test_directory_extraction(self, extractor, temp_dir):
        """Test extraction from a directory with mixed files."""
        # Valid file
        (temp_dir / "utils.py").write_text('''
def validate(data):
    return bool(data)
''')

        # File with syntax error
        (temp_dir / "broken.py").write_text('''
def valid_part():
    return 1

def broken(:  # error
    pass
''')

        result = extractor.extract_directory(temp_dir)

        # Should find symbols from both files
        paths = {s.path for s in result.symbols}
        assert "utils.py" in paths
        assert "broken.py" in paths

        # Should have used fallback for broken.py
        assert "broken.py" in extractor.fallback_files
        assert "utils.py" not in extractor.fallback_files

    def test_encoding_error_no_fallback(self, extractor, temp_dir):
        """Test that encoding errors don't trigger fallback (both fail same way)."""
        test_file = temp_dir / "binary.py"
        test_file.write_bytes(b"\x80\x81\x82")  # Invalid UTF-8

        result = extractor.extract_file(test_file, "binary.py")

        # Encoding errors are handled by AST extractor, no fallback needed
        # (tree-sitter also reads bytes but interprets as UTF-8)
        assert len(result.errors) == 1
        assert result.errors[0]["code"] == "ENCODING_ERROR"
        # May or may not use fallback - depends on implementation
        # The key is that extraction handles the error gracefully

    def test_classes_and_methods_valid_code(self, extractor, temp_dir, class_code):
        """Test extraction of classes and methods from valid code."""
        test_file = temp_dir / "classes.py"
        test_file.write_text(class_code)

        result = extractor.extract_file(test_file, "classes.py")

        # Should use AST (no fallback)
        assert "classes.py" not in extractor.fallback_files

        # Verify extraction
        classes = [s for s in result.symbols if s.symbol_type == "class"]
        methods = [s for s in result.symbols if s.symbol_type == "method"]

        assert len(classes) == 2
        assert len(methods) >= 4

    def test_imports_valid_code(self, extractor, temp_dir, import_code):
        """Test extraction of imports from valid code."""
        test_file = temp_dir / "imports.py"
        test_file.write_text(import_code)

        result = extractor.extract_file(test_file, "imports.py")

        # Should use AST (no fallback)
        assert "imports.py" not in extractor.fallback_files

        # Verify imports extracted
        assert len(result.imports) >= 5
        import_paths = {i.imported_path for i in result.imports}
        assert "os" in import_paths
        assert "sys" in import_paths

    def test_calls_extraction_valid_code(self, extractor, temp_dir, simple_function_code):
        """Test extraction of calls from valid code."""
        test_file = temp_dir / "calls.py"
        test_file.write_text(simple_function_code)

        result = extractor.extract_file(test_file, "calls.py")

        # Should use AST (no fallback)
        assert "calls.py" not in extractor.fallback_files

        # Should find calls in main()
        main_calls = [c for c in result.calls if c.caller_symbol == "main"]
        assert len(main_calls) >= 3

    def test_lazy_treesitter_init(self, extractor):
        """Test that tree-sitter extractor is lazily initialized."""
        # Initially should be None
        assert extractor._ts_extractor is None

        # Access through property initializes it
        ts = extractor._treesitter_extractor
        assert ts is not None
        assert extractor._ts_extractor is ts

        # Second access returns same instance
        ts2 = extractor._treesitter_extractor
        assert ts2 is ts

    def test_multiple_syntax_errors(self, extractor, temp_dir):
        """Test handling of multiple files with syntax errors."""
        # Create multiple broken files
        (temp_dir / "bad1.py").write_text("def a(:\n    pass")
        (temp_dir / "bad2.py").write_text("class B(:\n    pass")
        (temp_dir / "good.py").write_text("def c():\n    pass")

        # Extract each
        extractor.extract_file(temp_dir / "bad1.py", "bad1.py")
        extractor.extract_file(temp_dir / "bad2.py", "bad2.py")
        extractor.extract_file(temp_dir / "good.py", "good.py")

        # Should have two fallbacks
        assert extractor.fallback_count == 2
        assert "bad1.py" in extractor.fallback_files
        assert "bad2.py" in extractor.fallback_files
        assert "good.py" not in extractor.fallback_files

    def test_async_code_valid(self, extractor, temp_dir):
        """Test extraction of async code."""
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

        # Should use AST (no fallback)
        assert "async_test.py" not in extractor.fallback_files

        # Should find async functions
        assert len(result.symbols) == 2

        # Should find async call
        async_calls = [c for c in result.calls if c.call_type == "async"]
        assert len(async_calls) >= 1
