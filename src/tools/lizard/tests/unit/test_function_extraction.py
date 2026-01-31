"""Tests for function detection and extraction logic."""

import sys
from pathlib import Path

import pytest

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from function_analyzer import (
    FunctionInfo,
    FileInfo,
    detect_language,
)


class TestLanguageDetection:
    """Tests for language detection from file extensions."""

    @pytest.mark.parametrize("filename,expected", [
        ("main.py", "Python"),
        ("app.cs", "C#"),
        ("Main.java", "Java"),
        ("index.js", "JavaScript"),
        ("component.jsx", "JavaScript"),
        ("app.ts", "TypeScript"),
        ("component.tsx", "TypeScript"),
        ("main.go", "Go"),
        ("lib.rs", "Rust"),
        ("main.c", "C"),
        ("header.h", "C"),
        ("main.cpp", "C++"),
        ("header.hpp", "C++"),
        ("code.cc", "C++"),
        ("script.php", "PHP"),
        ("app.rb", "Ruby"),
        ("main.swift", "Swift"),
        ("App.kt", "Kotlin"),
        ("Main.scala", "Scala"),
    ])
    def test_known_extensions(self, filename, expected):
        """Test detection for known file extensions."""
        assert detect_language(filename) == expected

    def test_unknown_extension(self):
        """Test detection returns Unknown for unrecognized extensions."""
        assert detect_language("data.xyz") == "Unknown"
        assert detect_language("README.md") == "Unknown"
        assert detect_language("config.yaml") == "Unknown"

    def test_case_insensitive(self):
        """Test detection is case-insensitive for extensions."""
        assert detect_language("main.PY") == "Python"
        assert detect_language("main.Py") == "Python"
        assert detect_language("Main.CS") == "C#"

    def test_path_with_directory(self):
        """Test detection works with full paths."""
        assert detect_language("/src/main.py") == "Python"
        assert detect_language("src/lib/app.cs") == "C#"
        assert detect_language("./scripts/run.js") == "JavaScript"


class TestFunctionInfo:
    """Tests for FunctionInfo data class."""

    def test_function_info_creation(self):
        """Test creating a FunctionInfo instance."""
        func = FunctionInfo(
            name="calculate",
            long_name="Calculator.calculate",
            start_line=10,
            end_line=20,
            nloc=8,
            ccn=3,
            token_count=50,
            parameter_count=2,
            length=10,
        )
        assert func.name == "calculate"
        assert func.long_name == "Calculator.calculate"
        assert func.start_line == 10
        assert func.end_line == 20
        assert func.nloc == 8
        assert func.ccn == 3
        assert func.token_count == 50
        assert func.parameter_count == 2
        assert func.length == 10

    def test_function_info_with_zero_values(self):
        """Test FunctionInfo with zero values (edge case)."""
        func = FunctionInfo(
            name="empty",
            long_name="empty",
            start_line=1,
            end_line=1,
            nloc=0,
            ccn=1,  # Minimum CCN is 1
            token_count=0,
            parameter_count=0,
            length=0,
        )
        assert func.ccn == 1  # CCN is always at least 1


class TestFileInfo:
    """Tests for FileInfo data class."""

    def test_file_info_with_functions(self, sample_function_info):
        """Test creating a FileInfo with functions."""
        file_info = FileInfo(
            path="/test/file.py",
            language="Python",
            nloc=100,
            functions=[sample_function_info],
            function_count=1,
            total_ccn=8,
            avg_ccn=8.0,
            max_ccn=8,
        )
        assert file_info.path == "/test/file.py"
        assert file_info.language == "Python"
        assert len(file_info.functions) == 1
        assert file_info.functions[0].name == "process_data"

    def test_file_info_empty(self):
        """Test FileInfo for file with no functions."""
        file_info = FileInfo(
            path="/test/empty.py",
            language="Python",
            nloc=10,
            functions=[],
            function_count=0,
            total_ccn=0,
            avg_ccn=0.0,
            max_ccn=0,
        )
        assert file_info.function_count == 0
        assert file_info.total_ccn == 0
        assert file_info.avg_ccn == 0.0


class TestFunctionNaming:
    """Tests for function naming conventions."""

    def test_qualified_name_format(self):
        """Test that qualified names follow expected format."""
        func = FunctionInfo(
            name="process",
            long_name="MyClass.process",
            start_line=1,
            end_line=10,
            nloc=8,
            ccn=2,
            token_count=30,
            parameter_count=1,
            length=9,
        )
        # Qualified name should contain class and method
        assert "." in func.long_name
        assert func.name in func.long_name

    def test_nested_function_naming(self):
        """Test naming for nested functions."""
        func = FunctionInfo(
            name="inner",
            long_name="outer::inner",
            start_line=5,
            end_line=10,
            nloc=4,
            ccn=1,
            token_count=20,
            parameter_count=0,
            length=5,
        )
        # Nested function should have qualified name
        assert "::" in func.long_name or "." in func.long_name or func.name in func.long_name
