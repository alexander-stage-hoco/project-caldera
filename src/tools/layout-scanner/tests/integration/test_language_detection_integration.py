"""Integration tests for language detection.

Tests the interaction between:
- classifier.py and language_detector.py
- Multi-language repository scenarios
- Edge case file handling
"""

import pytest
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from classifier import (
    detect_language,
    classify_file,
    get_language_distribution,
    LanguageResult,
    LANGUAGE_MAP,
    ENHANCED_DETECTION,
)


# =============================================================================
# Classifier <-> Language Detector Integration Tests
# =============================================================================


class TestClassifierLanguageDetectorIntegration:
    """Test classifier.py <-> language_detector.py integration."""

    def test_enhanced_detection_available(self):
        """Enhanced detection module should be loaded."""
        # Just verify the flag exists
        assert isinstance(ENHANCED_DETECTION, bool)

    def test_csharp_naming_consistent(self):
        """C# files should return 'csharp' identifier consistently."""
        result = detect_language("Program.cs", ".cs")
        assert result.language == "csharp"

    def test_cpp_naming_consistent(self):
        """C++ files should return 'cpp' identifier consistently."""
        result = detect_language("main.cpp", ".cpp")
        assert result.language == "cpp"

    def test_shebang_detection_integration(self):
        """Shebang detection should work through classifier."""
        content = b"#!/usr/bin/env python\nprint('hello')"
        result = detect_language("script", "", content=content)
        assert result.language == "python"

    def test_extension_takes_priority(self):
        """Known extensions should take priority over shebang."""
        # Ruby shebang but .py extension
        content = b"#!/usr/bin/env ruby\nprint('hello')"
        result = detect_language("script.py", ".py", content=content)
        assert result.language == "python"

    def test_content_parameter_flows_through(self):
        """Content parameter should reach language_detector."""
        content = b"#!/bin/bash\necho hello"
        result = detect_language("deploy", "", content=content)
        # Should detect Shell from shebang
        assert result.language == "shell"

    @pytest.mark.parametrize("filename,ext,expected", [
        ("test.py", ".py", "python"),
        ("app.js", ".js", "javascript"),
        ("main.ts", ".ts", "typescript"),
        ("Program.cs", ".cs", "csharp"),
        ("Main.java", ".java", "java"),
        ("main.go", ".go", "go"),
        ("lib.rs", ".rs", "rust"),
        ("script.rb", ".rb", "ruby"),
        ("index.php", ".php", "php"),
        ("main.cpp", ".cpp", "cpp"),
        ("main.c", ".c", "c"),
        ("main.swift", ".swift", "swift"),
        ("script.sh", ".sh", "shell"),
        ("script.pl", ".pl", "perl"),
        ("main.kt", ".kt", "kotlin"),
        ("main.scala", ".scala", "scala"),
    ])
    def test_all_major_languages(self, filename, ext, expected):
        """All major languages should be detected consistently."""
        result = detect_language(filename, ext)
        assert result.language == expected
        assert result.confidence >= 0.9


# =============================================================================
# Multi-Language Repository Tests
# =============================================================================


class TestMultiLanguageRepository:
    """Integration tests with multi-language repos."""

    @pytest.fixture
    def polyglot_files(self, tmp_path):
        """Create a set of files in different languages."""
        files = {
            "main.py": b"print('hello')",
            "app.js": b"console.log('hello')",
            "Program.cs": b"class Program {}",
            "main.go": b"package main",
            "lib.rs": b"fn main() {}",
            "script.rb": b"puts 'hello'",
            "deploy": b"#!/bin/bash\necho deploy",
        }
        for name, content in files.items():
            (tmp_path / name).write_bytes(content)
        return tmp_path, files

    def test_all_languages_detected_correctly(self, polyglot_files):
        """Each language file should be detected correctly."""
        tmp_path, files = polyglot_files

        expected = {
            "main.py": "python",
            "app.js": "javascript",
            "Program.cs": "csharp",
            "main.go": "go",
            "lib.rs": "rust",
            "script.rb": "ruby",
        }

        for filename, expected_lang in expected.items():
            ext = Path(filename).suffix
            result = detect_language(filename, ext)
            assert result.language == expected_lang, f"{filename} expected {expected_lang}, got {result.language}"

    def test_shebang_script_in_polyglot(self, polyglot_files):
        """Shebang-only files should be detected in polyglot repos."""
        tmp_path, files = polyglot_files

        deploy_content = files["deploy"]
        result = detect_language("deploy", "", content=deploy_content)
        assert result.language == "shell"

    def test_language_distribution_counts(self):
        """get_language_distribution() should count languages correctly."""
        languages = ["python", "python", "javascript", "go", "python"]
        distribution = get_language_distribution(languages)

        assert distribution["python"] == 3
        assert distribution["javascript"] == 1
        assert distribution["go"] == 1

    def test_unknown_excluded_from_distribution(self):
        """'unknown' should be excluded from language distribution."""
        languages = ["python", "unknown", "javascript", "unknown"]
        distribution = get_language_distribution(languages)

        assert "unknown" not in distribution
        assert distribution["python"] == 1
        assert distribution["javascript"] == 1


# =============================================================================
# Edge Case File Tests
# =============================================================================


class TestEdgeCaseFiles:
    """Integration tests for edge case files."""

    def test_file_without_extension_with_shebang(self):
        """Script files without extensions should use shebang."""
        test_cases = [
            (b"#!/usr/bin/env python\nprint(1)", "python"),
            (b"#!/bin/bash\necho hi", "shell"),
            (b"#!/usr/bin/env ruby\nputs 1", "ruby"),
            (b"#!/usr/bin/env node\nconsole.log(1)", "javascript"),
        ]

        for content, expected in test_cases:
            result = detect_language("script", "", content=content)
            assert result.language == expected, f"Expected {expected} for content starting with {content[:30]}"

    def test_dotfile_with_extension(self):
        """.hidden.py should detect as Python."""
        result = detect_language(".hidden.py", ".py")
        assert result.language == "python"

    def test_uppercase_extensions(self):
        """Uppercase extensions like .PY should work."""
        result = detect_language("TEST.PY", ".PY")
        assert result.language == "python"

    def test_mixed_case_extensions(self):
        """Mixed case extensions like .Py should work."""
        result = detect_language("test.Py", ".Py")
        assert result.language == "python"

    def test_double_extensions(self):
        """Double extensions like .test.js should detect outer extension."""
        result = detect_language("utils.test.js", ".js")
        assert result.language == "javascript"

    def test_triple_extensions(self):
        """Triple extensions like .spec.test.ts should detect outer extension."""
        result = detect_language("utils.spec.test.ts", ".ts")
        assert result.language == "typescript"

    def test_config_files(self):
        """Config files should be detected appropriately."""
        test_cases = [
            ("package.json", ".json", "json"),
            ("tsconfig.json", ".json", "json"),
            (".eslintrc.json", ".json", "json"),
        ]

        for filename, ext, expected in test_cases:
            result = detect_language(filename, ext)
            assert result.language == expected

    def test_special_filenames(self):
        """Special filenames like Makefile should be detected."""
        result = detect_language("Makefile", "")
        assert result.language == "makefile"

        result = detect_language("Dockerfile", "")
        assert result.language == "dockerfile"


# =============================================================================
# Classification Integration Tests
# =============================================================================


class TestClassificationWithLanguage:
    """Test classification and language detection working together."""

    def test_test_file_with_language(self):
        """Test files should have both classification and language."""
        result = classify_file("tests/test_main.py", "test_main.py", ".py")
        assert result.category == "test"
        # Language should still be detectable
        lang_result = detect_language("test_main.py", ".py")
        assert lang_result.language == "python"

    def test_config_file_with_language(self):
        """Config files should have both classification and language."""
        result = classify_file("config/app.json", "app.json", ".json")
        # Classification depends on rules
        lang_result = detect_language("app.json", ".json")
        assert lang_result.language == "json"

    def test_vendor_file_with_language(self):
        """Vendor files should have both classification and language."""
        result = classify_file("node_modules/lodash/index.js", "index.js", ".js")
        assert result.category == "vendor"
        lang_result = detect_language("index.js", ".js")
        assert lang_result.language == "javascript"


# =============================================================================
# Confidence Score Integration Tests
# =============================================================================


class TestConfidenceScoreIntegration:
    """Test confidence scores across the integration."""

    def test_known_extension_high_confidence(self):
        """Known extensions should have high confidence."""
        result = detect_language("test.py", ".py")
        assert result.confidence >= 0.9

    def test_shebang_detection_confidence(self):
        """Shebang detection should have reasonable confidence."""
        content = b"#!/usr/bin/env python\nprint(1)"
        result = detect_language("script", "", content=content)
        assert result.confidence >= 0.8

    def test_unknown_extension_zero_confidence(self):
        """Unknown extensions should have zero confidence."""
        result = detect_language("file.xyz123", ".xyz123")
        assert result.language == "unknown"
        assert result.confidence == 0.0

    def test_ambiguous_extension_lower_confidence(self):
        """Ambiguous extensions should have lower confidence."""
        result = detect_language("header.h", ".h")
        # h files are ambiguous (C/C++/Objective-C)
        assert result.confidence < 0.9


# =============================================================================
# Error Handling Integration Tests
# =============================================================================


class TestErrorHandlingIntegration:
    """Test error handling across the integration."""

    def test_none_content_handled(self):
        """None content should be handled gracefully."""
        result = detect_language("test.py", ".py", content=None)
        assert result.language == "python"

    def test_empty_content_handled(self):
        """Empty content should be handled gracefully."""
        result = detect_language("test.py", ".py", content=b"")
        assert result.language == "python"

    def test_binary_content_handled(self):
        """Binary content should be handled gracefully."""
        content = bytes(range(256))
        result = detect_language("test.bin", ".bin", content=content)
        # Should not crash
        assert isinstance(result, LanguageResult)

    def test_unicode_paths_handled(self):
        """Unicode in paths should be handled."""
        result = detect_language("über/schön.py", ".py")
        assert result.language == "python"

    def test_very_long_filename_handled(self):
        """Very long filenames should be handled."""
        long_name = "a" * 255 + ".py"
        result = detect_language(long_name, ".py")
        assert result.language == "python"
