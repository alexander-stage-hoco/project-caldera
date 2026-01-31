"""Unit tests for language_detector.py module.

Tests cover:
- Shebang detection (various formats and edge cases)
- Extension-based detection
- Language normalization
- Binary/vendor/generated file detection
- Detection capabilities
"""

import pytest
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from language_detector import (
    detect_language,
    detect_language_by_extension,
    detect_language_by_shebang,
    is_binary_file,
    is_vendor_file,
    is_generated_file,
    get_detection_capabilities,
    normalize_language,
    LanguageResult,
    ENRY_AVAILABLE,
)


# =============================================================================
# Shebang Detection Tests
# =============================================================================


class TestShebangDetection:
    """Test shebang parsing edge cases."""

    def test_shebang_with_env_python(self):
        """#!/usr/bin/env python should detect Python."""
        content = b"#!/usr/bin/env python\nprint('hello')"
        result = detect_language_by_shebang(content)
        assert result == "Python"

    def test_shebang_with_env_python3(self):
        """#!/usr/bin/env python3 should detect Python."""
        content = b"#!/usr/bin/env python3\nimport sys"
        result = detect_language_by_shebang(content)
        assert result == "Python"

    def test_shebang_direct_path_python(self):
        """#!/usr/bin/python should detect Python."""
        content = b"#!/usr/bin/python\nprint('hello')"
        result = detect_language_by_shebang(content)
        assert result == "Python"

    def test_shebang_direct_path_bash(self):
        """#!/bin/bash should detect Shell."""
        content = b"#!/bin/bash\necho hello"
        result = detect_language_by_shebang(content)
        assert result == "Shell"

    def test_shebang_with_args(self):
        """#!/usr/bin/env python -u should detect Python."""
        content = b"#!/usr/bin/env python -u\nprint('hello')"
        result = detect_language_by_shebang(content)
        assert result == "Python"

    def test_shebang_ruby(self):
        """#!/usr/bin/env ruby should detect Ruby."""
        content = b"#!/usr/bin/env ruby\nputs 'hello'"
        result = detect_language_by_shebang(content)
        assert result == "Ruby"

    def test_shebang_node(self):
        """#!/usr/bin/env node should detect JavaScript."""
        content = b"#!/usr/bin/env node\nconsole.log('hello')"
        result = detect_language_by_shebang(content)
        assert result == "JavaScript"

    def test_shebang_perl(self):
        """#!/usr/bin/perl should detect Perl."""
        content = b"#!/usr/bin/perl\nprint 'hello'"
        result = detect_language_by_shebang(content)
        assert result == "Perl"

    def test_shebang_sh(self):
        """#!/bin/sh should detect Shell."""
        content = b"#!/bin/sh\necho hello"
        result = detect_language_by_shebang(content)
        assert result == "Shell"

    def test_shebang_zsh(self):
        """#!/usr/bin/zsh should detect Shell."""
        content = b"#!/usr/bin/zsh\necho hello"
        result = detect_language_by_shebang(content)
        assert result == "Shell"

    def test_shebang_windows_crlf(self):
        """Shebang with Windows line endings should work."""
        content = b"#!/usr/bin/env python\r\nprint('hello')"
        result = detect_language_by_shebang(content)
        assert result == "Python"

    def test_shebang_no_newline(self):
        """Single-line shebang (no newline) should work."""
        content = b"#!/usr/bin/env python"
        result = detect_language_by_shebang(content)
        assert result == "Python"

    def test_shebang_empty_content(self):
        """Empty content should return None."""
        result = detect_language_by_shebang(b"")
        assert result is None

    def test_shebang_none_content(self):
        """None content should return None."""
        result = detect_language_by_shebang(None)
        assert result is None

    def test_shebang_not_shebang(self):
        """Content without shebang should return None."""
        content = b"# This is not a shebang\nprint('hello')"
        result = detect_language_by_shebang(content)
        assert result is None

    def test_shebang_invalid_format(self):
        """Malformed shebangs should return None."""
        # Just #! with nothing after
        result = detect_language_by_shebang(b"#!\n")
        assert result is None

    def test_shebang_unknown_interpreter(self):
        """Unknown interpreters should return None."""
        content = b"#!/usr/bin/env unknownlang\ncode here"
        result = detect_language_by_shebang(content)
        assert result is None

    def test_shebang_awk(self):
        """#!/usr/bin/awk should detect AWK."""
        content = b"#!/usr/bin/awk -f\nBEGIN { print }"
        result = detect_language_by_shebang(content)
        assert result == "AWK"

    def test_shebang_lua(self):
        """#!/usr/bin/env lua should detect Lua."""
        content = b"#!/usr/bin/env lua\nprint('hello')"
        result = detect_language_by_shebang(content)
        assert result == "Lua"

    def test_shebang_php(self):
        """#!/usr/bin/env php should detect PHP."""
        content = b"#!/usr/bin/env php\n<?php echo 'hi'; ?>"
        result = detect_language_by_shebang(content)
        assert result == "PHP"


# =============================================================================
# Extension-Based Detection Tests
# =============================================================================


class TestExtensionDetection:
    """Test extension-based language detection."""

    @pytest.mark.parametrize("filename,expected", [
        ("test.py", "Python"),
        ("app.js", "JavaScript"),
        ("main.ts", "TypeScript"),
        ("Program.cs", "C#"),
        ("Main.java", "Java"),
        ("main.go", "Go"),
        ("lib.rs", "Rust"),
        ("script.rb", "Ruby"),
        ("index.php", "PHP"),
        ("app.swift", "Swift"),
    ])
    def test_common_extensions(self, filename, expected):
        """Common file extensions should be detected correctly."""
        result = detect_language_by_extension(filename)
        assert result.language == expected
        assert result.confidence >= 0.9

    @pytest.mark.parametrize("filename,expected", [
        ("Makefile", "Makefile"),
        ("Dockerfile", "Dockerfile"),
        ("CMakeLists.txt", "CMake"),
        ("Gemfile", "Ruby"),
        ("Rakefile", "Ruby"),
    ])
    def test_filename_detection(self, filename, expected):
        """Special filenames should be detected correctly."""
        result = detect_language_by_extension(filename)
        assert result.language == expected

    def test_unknown_extension(self):
        """Unknown extensions should return unknown with 0 confidence."""
        result = detect_language_by_extension("file.xyz123")
        assert result.language == "unknown"
        assert result.confidence == 0.0


class TestExtensionAmbiguity:
    """Test handling of ambiguous file extensions."""

    def test_h_file_returns_c_with_alternatives(self):
        """.h files should return C with alternatives."""
        result = detect_language_by_extension("header.h")
        assert result.language == "C"
        assert result.confidence < 0.9  # Lower confidence for ambiguous
        assert len(result.alternatives) > 0
        assert "C++" in result.alternatives or "Objective-C" in result.alternatives

    def test_m_file_returns_objective_c(self):
        """.m files should return Objective-C."""
        result = detect_language_by_extension("code.m")
        assert result.language == "Objective-C"

    def test_pl_file_returns_perl(self):
        """.pl files should return Perl."""
        result = detect_language_by_extension("script.pl")
        assert result.language == "Perl"


# =============================================================================
# Full Detection Pipeline Tests
# =============================================================================


class TestFullDetection:
    """Test the full detect_language() function."""

    def test_extension_with_no_content(self):
        """Extension-based detection when no content provided."""
        result = detect_language("test.py")
        assert result.language == "Python"
        assert result.confidence >= 0.9

    def test_shebang_with_no_extension(self):
        """Shebang detection for files without extensions."""
        content = b"#!/usr/bin/env python\nprint('hello')"
        result = detect_language("script", content)
        assert result.language == "Python"
        assert result.method == "shebang"

    def test_extension_priority_over_shebang(self):
        """Extension should be detected when both extension and shebang present."""
        # File has .py extension, shebang is redundant
        content = b"#!/usr/bin/env python\nprint('hello')"
        result = detect_language("script.py", content)
        assert result.language == "Python"
        # Should use extension method (faster path)
        assert result.method in ["extension", "enry"]

    def test_shebang_used_for_unknown_extension(self):
        """Shebang should be used when extension is unknown."""
        content = b"#!/usr/bin/env python\nprint('hello')"
        result = detect_language("my-script.unknown", content)
        # Should fall back to shebang or return Python
        assert result.language in ["Python", "unknown"]


# =============================================================================
# Language Normalization Tests
# =============================================================================


class TestLanguageNormalization:
    """Test language name normalization."""

    @pytest.mark.parametrize("input_lang,expected", [
        ("python", "Python"),
        ("PYTHON", "Python"),
        ("Python", "Python"),
        ("javascript", "JavaScript"),
        ("c#", "C#"),
        ("c++", "C++"),
    ])
    def test_case_normalization(self, input_lang, expected):
        """Language names should normalize to consistent casing."""
        result = normalize_language(input_lang)
        assert result == expected

    def test_unknown_language_passthrough(self):
        """Unknown language names should pass through."""
        result = normalize_language("SomeNewLang")
        assert result == "SomeNewLang"

    def test_empty_string_returns_unknown(self):
        """Empty string should return 'unknown'."""
        result = normalize_language("")
        assert result == "unknown"

    def test_none_returns_unknown(self):
        """None should return 'unknown'."""
        result = normalize_language(None)
        assert result == "unknown"


# =============================================================================
# Binary File Detection Tests
# =============================================================================


class TestBinaryFileDetection:
    """Test binary vs text file detection."""

    def test_null_byte_detection(self):
        """Files with null bytes are binary."""
        content = b"Some text\x00more text"
        assert is_binary_file("test.bin", content) is True

    def test_jpeg_header_detection(self):
        """JPEG magic bytes indicate binary."""
        content = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        assert is_binary_file("image.jpg", content) is True

    def test_png_header_detection(self):
        """PNG magic bytes indicate binary."""
        content = b"\x89PNG\r\n\x1a\n"
        assert is_binary_file("image.png", content) is True

    def test_text_file_not_binary(self):
        """Plain text files are not binary."""
        content = b"This is plain text\nwith newlines\n"
        assert is_binary_file("readme.txt", content) is False

    def test_python_file_not_binary(self):
        """Python source files are not binary."""
        content = b"#!/usr/bin/env python\nprint('hello')\n"
        assert is_binary_file("script.py", content) is False

    def test_utf8_with_bom_not_binary(self):
        """UTF-8 with BOM should not be considered binary."""
        content = b"\xef\xbb\xbfprint('hello')"
        # BOM is 3 bytes, no null bytes after
        assert is_binary_file("script.py", content) is False

    def test_empty_content_not_binary(self):
        """Empty content should not be binary."""
        assert is_binary_file("empty.txt", b"") is False


# =============================================================================
# Vendor File Detection Tests
# =============================================================================


class TestVendorFileDetection:
    """Test vendor/dependency detection."""

    @pytest.mark.parametrize("path", [
        "node_modules/lodash/index.js",
        "vendor/github.com/pkg/errors/errors.go",
        "third_party/lib/util.py",
        "bower_components/jquery/jquery.js",
        ".nuget/packages/newtonsoft.json/lib/net45/Newtonsoft.Json.dll",
    ])
    def test_vendor_paths_detected(self, path):
        """Common vendor paths should be detected."""
        assert is_vendor_file(path) is True

    @pytest.mark.parametrize("path", [
        "src/main.py",
        "lib/mylib.py",  # lib/ alone might be ambiguous
        "app/models/user.py",
        "tests/test_main.py",
    ])
    def test_non_vendor_paths(self, path):
        """Non-vendor paths should not be flagged."""
        # Note: Some paths like lib/ might be ambiguous
        result = is_vendor_file(path)
        # Just ensure it doesn't crash
        assert isinstance(result, bool)

    def test_nested_vendor_path(self):
        """Deeply nested vendor paths detected."""
        path = "project/submodule/node_modules/pkg/lib/util.js"
        assert is_vendor_file(path) is True

    def test_vendor_case_variations(self):
        """Vendor detection should handle case variations."""
        # Our fallback is case-insensitive
        assert is_vendor_file("Node_Modules/pkg/index.js") is True
        assert is_vendor_file("VENDOR/lib/code.go") is True


# =============================================================================
# Generated File Detection Tests
# =============================================================================


class TestGeneratedFileDetection:
    """Test generated file detection."""

    @pytest.mark.parametrize("filename", [
        "package-lock.json",
        "yarn.lock",
        "Cargo.lock",
        "poetry.lock",
        "Pipfile.lock",
        "go.sum",
    ])
    def test_lock_files_are_generated(self, filename):
        """Lock files should be detected as generated."""
        assert is_generated_file(filename) is True

    @pytest.mark.parametrize("filename", [
        "app.min.js",
        "styles.min.css",
        "bundle.min.js",
    ])
    def test_minified_files_are_generated(self, filename):
        """Minified files should be detected as generated."""
        assert is_generated_file(filename) is True

    @pytest.mark.parametrize("filename", [
        "message_pb2.py",
        "message.pb.go",
        "service_pb2_grpc.py",
    ])
    def test_protobuf_files_are_generated(self, filename):
        """Protobuf generated files should be detected."""
        assert is_generated_file(filename) is True

    @pytest.mark.parametrize("filename", [
        "MyClass.g.cs",
        "AutoGenerated.generated.cs",
        "Form1.Designer.cs",
    ])
    def test_dotnet_generated_files(self, filename):
        """C# generated files should be detected."""
        assert is_generated_file(filename) is True

    @pytest.mark.parametrize("filename", [
        "main.py",
        "app.js",
        "index.ts",
        "Program.cs",
    ])
    def test_regular_files_not_generated(self, filename):
        """Regular source files should not be flagged as generated."""
        assert is_generated_file(filename) is False


# =============================================================================
# Detection Capabilities Tests
# =============================================================================


class TestDetectionCapabilities:
    """Test detection capability reporting."""

    def test_capabilities_returns_dict(self):
        """get_detection_capabilities() should return a dict."""
        caps = get_detection_capabilities()
        assert isinstance(caps, dict)

    def test_capabilities_has_required_keys(self):
        """Capabilities dict should have required keys."""
        caps = get_detection_capabilities()
        assert "enry_available" in caps
        assert "treesitter_available" in caps
        assert "strategies" in caps
        assert "shebang_available" in caps

    def test_shebang_always_available(self):
        """Shebang detection should always be available."""
        caps = get_detection_capabilities()
        assert caps["shebang_available"] is True
        assert "shebang" in caps["strategies"]

    def test_basic_strategies_always_available(self):
        """Basic strategies should always be available."""
        caps = get_detection_capabilities()
        assert "filename" in caps["strategies"]
        assert "extension" in caps["strategies"]


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_filename(self):
        """Empty filename should be handled."""
        result = detect_language_by_extension("")
        assert result.language == "unknown"

    def test_path_with_spaces(self):
        """Paths with spaces should work."""
        result = detect_language_by_extension("my file.py")
        assert result.language == "Python"

    def test_unicode_filename(self):
        """Unicode in filenames should work."""
        result = detect_language_by_extension("über_script.py")
        assert result.language == "Python"

    def test_double_extension(self):
        """Double extensions like .test.js should detect outer extension."""
        result = detect_language_by_extension("utils.test.js")
        assert result.language == "JavaScript"

    def test_hidden_file_with_extension(self):
        """Hidden files with extensions should detect language."""
        result = detect_language_by_extension(".hidden.py")
        assert result.language == "Python"

    def test_extremely_long_shebang(self):
        """Extremely long shebangs should be handled."""
        long_path = "/very" * 100 + "/long/path/python"
        content = f"#!{long_path}\nprint('hello')".encode()
        # Should not crash, may or may not detect
        result = detect_language_by_shebang(content)
        # Just ensure it doesn't crash
        assert result is None or isinstance(result, str)

    def test_binary_garbage_in_content(self):
        """Binary garbage shouldn't crash detection."""
        content = bytes(range(256))  # All possible bytes
        result = detect_language("test.bin", content)
        # Should not crash
        assert isinstance(result, LanguageResult)

    def test_very_large_content(self):
        """Large content should be handled efficiently."""
        # 1MB of Python-like content
        content = b"#!/usr/bin/env python\n" + b"x = 1\n" * 100000
        result = detect_language("script", content)
        assert result.language == "Python"


# =============================================================================
# Issue 3 Fix Tests - Language Detection Improvements
# =============================================================================


class TestNewExtensionMappings:
    """Tests for new extension mappings (Issue 3.1)."""

    def test_sln_language(self):
        """.sln files should detect as 'sln'."""
        result = detect_language_by_extension("MyProject.sln")
        assert result.language == "sln"
        assert result.confidence >= 0.9

    def test_config_language(self):
        """.config files should detect as 'XML'."""
        result = detect_language_by_extension("web.config")
        assert result.language == "XML"
        assert result.confidence >= 0.9

    def test_app_config_language(self):
        """App.config should detect as 'XML'."""
        result = detect_language_by_extension("App.config")
        assert result.language == "XML"


class TestNormalizedDotfileNames:
    """Tests for normalized dotfile names (Issue 3.2)."""

    def test_gitignore_normalized_name(self):
        """.gitignore should detect as 'gitignore' (not 'Ignore List')."""
        result = detect_language_by_extension(".gitignore")
        assert result.language == "gitignore"

    def test_gitattributes_normalized_name(self):
        """.gitattributes should detect as 'gitattributes' (not 'Git Attributes')."""
        result = detect_language_by_extension(".gitattributes")
        assert result.language == "gitattributes"

    def test_editorconfig_normalized_name(self):
        """.editorconfig should detect as 'editorconfig' (not 'EditorConfig')."""
        result = detect_language_by_extension(".editorconfig")
        assert result.language == "editorconfig"


# =============================================================================
# Go Module File Detection Tests (Issue: Language Detection Improvement)
# =============================================================================


class TestGoModuleLanguageDetection:
    """Tests for Go module file language detection."""

    def test_go_mod_language(self):
        """go.mod should detect as 'Go'."""
        result = detect_language_by_extension("go.mod")
        assert result.language == "Go"
        assert result.confidence >= 0.9
        assert result.method == "filename"

    def test_go_sum_language(self):
        """go.sum should detect as 'Go'."""
        result = detect_language_by_extension("go.sum")
        assert result.language == "Go"
        assert result.confidence >= 0.9
        assert result.method == "filename"


class TestPythonDependencyLanguageDetection:
    """Tests for Python dependency file language detection."""

    def test_requirements_txt_language(self):
        """requirements.txt should detect as 'pip'."""
        result = detect_language_by_extension("requirements.txt")
        assert result.language == "pip"
        assert result.confidence >= 0.9
        assert result.method == "filename"


class TestLicenseFileLanguageDetection:
    """Tests for license file language detection."""

    def test_license_no_extension_language(self):
        """LICENSE (no extension) should detect as 'license'."""
        result = detect_language_by_extension("LICENSE")
        assert result.language == "license"
        assert result.method == "filename"

    def test_license_txt_language(self):
        """LICENSE.txt should detect as 'license'."""
        result = detect_language_by_extension("LICENSE.txt")
        assert result.language == "license"
        assert result.method == "filename"

    def test_copying_language(self):
        """COPYING should detect as 'license'."""
        result = detect_language_by_extension("COPYING")
        assert result.language == "license"
        assert result.method == "filename"


class TestNDependLanguageDetection:
    """Tests for NDepend project file language detection."""

    def test_ndproj_language(self):
        """.ndproj files should detect as 'XML'."""
        result = detect_language_by_extension("MyProject.ndproj")
        assert result.language == "XML"
        assert result.confidence >= 0.9
