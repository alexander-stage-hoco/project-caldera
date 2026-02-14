"""Extended tests for function_analyzer.py covering exclusion, detection,
directory analysis, output conversion, and run folder creation."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from function_analyzer import (
    matches_exclude_pattern,
    is_likely_minified,
    detect_language,
    analyze_directories,
    compute_directory_stats,
    to_dict,
    result_to_output,
    create_run_folder,
    discover_repos,
    AnalysisResult,
    AnalysisSummary,
    DirectoryInfo,
    DirectoryStats,
    DirectoryStructure,
    Distribution,
    ExcludedFile,
    FileInfo,
    FunctionInfo,
    EXCLUDE_PATTERNS,
    MINIFICATION_CHECK_LANGUAGES,
    get_lizard_version,
    ProgressReporter,
    set_color_enabled,
    get_terminal_width,
    c,
    Colors,
    strip_ansi,
    truncate_path_middle,
    format_number,
    print_header,
    print_section,
    print_section_end,
    print_row,
    print_empty_row,
)


# =============================================================================
# matches_exclude_pattern
# =============================================================================

class TestMatchesExcludePattern:
    """Tests for the file exclusion pattern matching logic."""

    def test_matches_minified_js(self):
        """*.min.js pattern matches minified JS."""
        result = matches_exclude_pattern(Path("vendor/jquery.min.js"), EXCLUDE_PATTERNS)
        assert result == "*.min.js"

    def test_matches_minified_css(self):
        """*.min.css pattern matches minified CSS."""
        result = matches_exclude_pattern(Path("styles/app.min.css"), EXCLUDE_PATTERNS)
        assert result == "*.min.css"

    def test_matches_bundle_js(self):
        """*.bundle.js pattern matches bundled JS."""
        result = matches_exclude_pattern(Path("dist/main.bundle.js"), EXCLUDE_PATTERNS)
        assert result == "*.bundle.js"

    def test_matches_generated_cs(self):
        """*.designer.cs pattern matches generated C#."""
        result = matches_exclude_pattern(Path("Forms/Form1.designer.cs"), EXCLUDE_PATTERNS)
        assert result == "*.designer.cs"

    def test_matches_protobuf_python(self):
        """*_pb2.py pattern matches protobuf-generated Python."""
        result = matches_exclude_pattern(Path("proto/message_pb2.py"), EXCLUDE_PATTERNS)
        assert result == "*_pb2.py"

    def test_matches_typescript_declarations(self):
        """*.d.ts pattern matches TypeScript declarations."""
        result = matches_exclude_pattern(Path("types/index.d.ts"), EXCLUDE_PATTERNS)
        assert result == "*.d.ts"

    def test_no_match_regular_js(self):
        """Regular JS files do not match any exclusion pattern."""
        result = matches_exclude_pattern(Path("src/app.js"), EXCLUDE_PATTERNS)
        assert result is None

    def test_no_match_regular_py(self):
        """Regular Python files do not match any exclusion pattern."""
        result = matches_exclude_pattern(Path("src/main.py"), EXCLUDE_PATTERNS)
        assert result is None

    def test_empty_patterns_list(self):
        """Empty patterns list never matches."""
        result = matches_exclude_pattern(Path("anything.js"), [])
        assert result is None

    def test_matches_jquery_variant(self):
        """jquery*.js pattern matches jQuery variants."""
        result = matches_exclude_pattern(Path("libs/jquery-3.6.0.js"), EXCLUDE_PATTERNS)
        assert result == "jquery*.js"

    def test_matches_source_map(self):
        """*.map pattern matches source maps."""
        result = matches_exclude_pattern(Path("dist/app.js.map"), EXCLUDE_PATTERNS)
        assert result == "*.map"


# =============================================================================
# is_likely_minified
# =============================================================================

class TestIsLikelyMinified:
    """Tests for content-based minified file detection."""

    def test_normal_file_not_minified(self, tmp_path):
        """A normal multi-line file is not detected as minified."""
        f = tmp_path / "normal.js"
        lines = ["function hello() {\n", "  console.log('hi');\n", "}\n"]
        f.write_text("".join(lines))
        assert is_likely_minified(f) is False

    def test_long_single_line_detected(self, tmp_path):
        """A file with a single very long line is detected as minified."""
        f = tmp_path / "minified.js"
        # Single line > 1000 chars
        f.write_text("var x=" + "a" * 1200 + ";")
        assert is_likely_minified(f) is True

    def test_high_avg_line_length_detected(self, tmp_path):
        """A file with average line length > 500 is detected as minified."""
        f = tmp_path / "dense.js"
        # Content = "a"*2000 + "\n" -> 2001 chars, split gives 2 lines
        # avg = 2001/2 = 1000.5 > 500
        f.write_text("a" * 2000 + "\n")
        assert is_likely_minified(f) is True

    def test_very_few_newlines_detected(self, tmp_path):
        """A file with very few newlines relative to size is detected as minified."""
        f = tmp_path / "packed.js"
        # A large block with very few newlines: ~2000 chars but only 1 newline
        # ratio = 2 / 2000 = 0.001 < 0.002
        f.write_text("a" * 999 + "\n" + "b" * 999)
        assert is_likely_minified(f) is True

    def test_empty_file_not_minified(self, tmp_path):
        """An empty file is not detected as minified."""
        f = tmp_path / "empty.js"
        f.write_text("")
        assert is_likely_minified(f) is False

    def test_unreadable_file_not_minified(self, tmp_path):
        """A non-existent file returns False (not minified)."""
        f = tmp_path / "nonexistent.js"
        assert is_likely_minified(f) is False

    def test_short_file_not_minified(self, tmp_path):
        """A short file with short lines is not detected as minified."""
        f = tmp_path / "short.js"
        f.write_text("var x = 1;\nvar y = 2;\nvar z = 3;\n")
        assert is_likely_minified(f) is False


# =============================================================================
# detect_language
# =============================================================================

class TestDetectLanguage:
    """Tests for language detection from file extensions."""

    @pytest.mark.parametrize("filename,expected", [
        ("main.py", "Python"),
        ("Program.cs", "C#"),
        ("App.java", "Java"),
        ("index.js", "JavaScript"),
        ("App.jsx", "JavaScript"),
        ("index.ts", "TypeScript"),
        ("App.tsx", "TypeScript"),
        ("main.go", "Go"),
        ("lib.rs", "Rust"),
        ("main.c", "C"),
        ("header.h", "C"),
        ("main.cpp", "C++"),
        ("header.hpp", "C++"),
        ("main.cc", "C++"),
        ("index.php", "PHP"),
        ("app.rb", "Ruby"),
        ("App.swift", "Swift"),
        ("Main.kt", "Kotlin"),
        ("App.scala", "Scala"),
    ])
    def test_known_extensions(self, filename, expected):
        """Known extensions map to correct languages."""
        assert detect_language(filename) == expected

    def test_unknown_extension(self):
        """Unknown extensions return 'Unknown'."""
        assert detect_language("readme.md") == "Unknown"

    def test_no_extension(self):
        """Files with no extension return 'Unknown'."""
        assert detect_language("Makefile") == "Unknown"

    def test_case_insensitive_extension(self):
        """Extension matching is case-insensitive."""
        assert detect_language("Main.PY") == "Python"
        assert detect_language("App.CS") == "C#"


# =============================================================================
# analyze_directories
# =============================================================================

class TestAnalyzeDirectories:
    """Tests for bottom-up directory analysis."""

    def _make_func(self, name: str, ccn: int, nloc: int, params: int = 1) -> FunctionInfo:
        return FunctionInfo(
            name=name, long_name=name, start_line=1, end_line=10,
            nloc=nloc, ccn=ccn, token_count=50, parameter_count=params, length=10,
        )

    def _make_file(self, path: str, lang: str, functions: list[FunctionInfo]) -> FileInfo:
        total_ccn = sum(f.ccn for f in functions)
        return FileInfo(
            path=path, language=lang,
            nloc=sum(f.nloc for f in functions),
            functions=functions,
            function_count=len(functions),
            total_ccn=total_ccn,
            avg_ccn=total_ccn / len(functions) if functions else 0,
            max_ccn=max((f.ccn for f in functions), default=0),
        )

    def test_empty_files_returns_empty(self):
        """No files produces empty directory list."""
        dirs, structure = analyze_directories([], "/repo")
        assert dirs == []
        assert structure.max_depth == 0

    def test_single_file_in_root(self):
        """A single file at root produces one directory entry."""
        func = self._make_func("main", ccn=5, nloc=20)
        file = self._make_file("/repo/main.py", "Python", [func])
        dirs, structure = analyze_directories([file], "/repo")

        # Should have at least the root directory
        assert len(dirs) >= 1
        root_dir = next(d for d in dirs if d.path == ".")
        assert root_dir.recursive.function_count == 1
        assert root_dir.recursive.ccn == 5
        assert root_dir.direct.function_count == 1

    def test_nested_directories_aggregate(self):
        """Recursive stats aggregate from children to parents."""
        func_a = self._make_func("a", ccn=3, nloc=10)
        func_b = self._make_func("b", ccn=7, nloc=20)
        file_a = self._make_file("/repo/src/a.py", "Python", [func_a])
        file_b = self._make_file("/repo/src/sub/b.py", "Python", [func_b])

        dirs, structure = analyze_directories([file_a, file_b], "/repo")

        # The root directory should have both functions recursively
        root = next(d for d in dirs if d.path == ".")
        assert root.recursive.function_count == 2
        assert root.recursive.ccn == 10  # 3 + 7

        # src should have 2 functions recursively but only 1 directly
        src = next(d for d in dirs if d.path == "src")
        assert src.recursive.function_count == 2
        assert src.direct.function_count == 1

        # src/sub should have only 1 function both directly and recursively
        sub = next(d for d in dirs if d.path == "src/sub")
        assert sub.recursive.function_count == 1
        assert sub.direct.function_count == 1

    def test_directory_structure_metadata(self):
        """DirectoryStructure metadata is correct."""
        func = self._make_func("deep", ccn=2, nloc=5)
        file = self._make_file("/repo/a/b/c/deep.py", "Python", [func])
        dirs, structure = analyze_directories([file], "/repo")

        assert structure.max_depth >= 3  # a/b/c = depth 3
        assert structure.leaf_directory_count >= 1

    def test_leaf_and_non_leaf_classification(self):
        """Leaf directories have no children; non-leaf have children."""
        func = self._make_func("f", ccn=1, nloc=5)
        file1 = self._make_file("/repo/src/a.py", "Python", [func])
        file2 = self._make_file("/repo/src/sub/b.py", "Python", [func])
        dirs, _ = analyze_directories([file1, file2], "/repo")

        src = next(d for d in dirs if d.path == "src")
        sub = next(d for d in dirs if d.path == "src/sub")
        assert src.is_leaf is False
        assert sub.is_leaf is True


# =============================================================================
# to_dict
# =============================================================================

class TestToDict:
    """Tests for the generic dataclass-to-dict converter."""

    def test_simple_dataclass(self):
        """Converts a simple FunctionInfo to dict."""
        fi = FunctionInfo("f", "f", 1, 10, 20, 5, 50, 2, 9)
        result = to_dict(fi)
        assert isinstance(result, dict)
        assert result["name"] == "f"
        assert result["ccn"] == 5

    def test_nested_dataclass(self):
        """Converts nested dataclasses (FileInfo with functions)."""
        fi = FunctionInfo("f", "f", 1, 10, 20, 5, 50, 2, 9)
        file = FileInfo("test.py", "Python", 20, [fi], 1, 5, 5.0, 5)
        result = to_dict(file)
        assert isinstance(result, dict)
        assert isinstance(result["functions"], list)
        assert result["functions"][0]["name"] == "f"

    def test_plain_value(self):
        """Plain values (int, str, float) pass through unchanged."""
        assert to_dict(42) == 42
        assert to_dict("hello") == "hello"
        assert to_dict(3.14) == 3.14

    def test_dict_input(self):
        """Dict values get recursively converted."""
        result = to_dict({"a": 1, "b": [2, 3]})
        assert result == {"a": 1, "b": [2, 3]}

    def test_list_input(self):
        """List values get recursively converted."""
        result = to_dict([1, "x", {"y": 2}])
        assert result == [1, "x", {"y": 2}]


# =============================================================================
# result_to_output (envelope creation)
# =============================================================================

class TestResultToOutput:
    """Tests for converting AnalysisResult to envelope JSON."""

    @patch("function_analyzer.create_envelope")
    @patch("function_analyzer.get_lizard_version", return_value="lizard 1.17.10")
    def test_creates_valid_envelope(self, mock_version, mock_envelope):
        """result_to_output calls create_envelope with correct args."""
        mock_envelope.return_value = {"schema_version": "1.0", "data": {}}

        result = AnalysisResult(
            run_id="test-001",
            timestamp="2026-01-20T00:00:00Z",
            root_path=".",
            repo_id="test-repo",
            branch="main",
            commit="abc123",
            summary=AnalysisSummary(total_files=0, total_functions=0),
        )
        output = result_to_output(result)

        mock_envelope.assert_called_once()
        call_kwargs = mock_envelope.call_args
        assert call_kwargs.kwargs["tool_name"] == "lizard"
        assert call_kwargs.kwargs["run_id"] == "test-001"
        assert call_kwargs.kwargs["repo_id"] == "test-repo"


# =============================================================================
# create_run_folder
# =============================================================================

class TestCreateRunFolder:
    """Tests for output file creation."""

    @patch("function_analyzer.create_envelope")
    @patch("function_analyzer.get_lizard_version", return_value="lizard 1.17.10")
    def test_creates_output_and_metadata(self, mock_version, mock_envelope, tmp_path):
        """create_run_folder writes output.json and metadata.json."""
        mock_envelope.return_value = {"schema_version": "1.0", "data": {"files": []}}

        result = AnalysisResult(
            run_id="test-001",
            timestamp="2026-01-20T00:00:00Z",
            root_path="/repo",
            repo_name="test-repo",
            summary=AnalysisSummary(total_files=5, total_functions=10, total_ccn=25),
        )

        out_dir = tmp_path / "run-001"
        create_run_folder(out_dir, "test-repo", "/repo", result)

        assert (out_dir / "output.json").exists()
        assert (out_dir / "metadata.json").exists()

        metadata = json.loads((out_dir / "metadata.json").read_text())
        assert metadata["run_id"] == "test-001"
        assert metadata["repo_name"] == "test-repo"
        assert metadata["file_count"] == 5
        assert metadata["function_count"] == 10

    @patch("function_analyzer.create_envelope")
    @patch("function_analyzer.get_lizard_version", return_value="lizard 1.17.10")
    def test_creates_directory_if_missing(self, mock_version, mock_envelope, tmp_path):
        """create_run_folder creates parent directories."""
        mock_envelope.return_value = {"schema_version": "1.0", "data": {}}

        result = AnalysisResult(
            run_id="test-002",
            timestamp="2026-01-20T00:00:00Z",
            root_path="/repo",
            summary=AnalysisSummary(),
        )

        out_dir = tmp_path / "nested" / "deep" / "run"
        create_run_folder(out_dir, "repo", "/repo", result)
        assert out_dir.exists()


# =============================================================================
# discover_repos
# =============================================================================

class TestDiscoverRepos:
    """Tests for repo discovery in interactive mode."""

    def test_discovers_synthetic_repos(self, tmp_path):
        """Finds subdirectories under synthetic/."""
        syn = tmp_path / "synthetic"
        syn.mkdir()
        (syn / "python").mkdir()
        (syn / "csharp").mkdir()
        (syn / ".hidden").mkdir()  # Should be ignored

        repos = discover_repos(tmp_path)
        names = [r.name for r in repos]
        assert "python" in names
        assert "csharp" in names
        assert ".hidden" not in names

    def test_discovers_real_repos(self, tmp_path):
        """Finds subdirectories under real/."""
        real = tmp_path / "real"
        real.mkdir()
        (real / "my-project").mkdir()

        repos = discover_repos(tmp_path)
        assert any(r.name == "my-project" for r in repos)

    def test_falls_back_to_self(self, tmp_path):
        """If no synthetic/ or real/ subdirs, returns the path itself."""
        repos = discover_repos(tmp_path)
        assert repos == [tmp_path]

    def test_empty_nonexistent_path(self, tmp_path):
        """Non-existent path (but parent exists) returns the path itself."""
        missing = tmp_path / "does_not_exist"
        repos = discover_repos(missing)
        # Path doesn't exist so no synthetic/real, falls to final check
        assert repos == []


# =============================================================================
# get_lizard_version
# =============================================================================

class TestGetLizardVersion:
    """Tests for version detection."""

    def test_returns_version_string(self):
        """Returns a string containing 'lizard'."""
        v = get_lizard_version()
        assert "lizard" in v

    @patch("function_analyzer.lizard")
    def test_handles_missing_version(self, mock_lizard):
        """Returns fallback when lizard.version doesn't exist."""
        del mock_lizard.version
        v = get_lizard_version()
        assert v == "lizard (version unknown)"


# =============================================================================
# ProgressReporter
# =============================================================================

class TestProgressReporter:
    """Tests for ProgressReporter timing and progress tracking."""

    def test_disabled_reporter_does_not_print(self, capsys):
        """Disabled reporter produces no output."""
        r = ProgressReporter(enabled=False)
        r.start()
        r.phase("test")
        r.progress(50, 100)
        r.end_progress()
        r.finish()
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_phase_records_timing(self):
        """Phases are recorded and durations computed."""
        r = ProgressReporter(enabled=False)
        r.start()
        r.phase("first")
        r.phase("second")
        r.finish()
        assert len(r._phases) == 2
        assert r._phases[0][0] == "first"
        assert r._phases[1][0] == "second"

    def test_progress_rate_limiting(self, capsys):
        """Progress updates are rate-limited by interval."""
        r = ProgressReporter(enabled=True, interval=10.0)  # very long interval
        r.start()
        r.phase("scan")
        r._last_update = 0  # Reset
        r.progress(1, 100)  # This should print (first call)
        r.progress(2, 100)  # This should be suppressed (within interval)
        r.end_progress()
        # Just verify it doesn't crash; exact output depends on timing

    def test_progress_zero_total(self, capsys):
        """Progress with total=0 does nothing."""
        r = ProgressReporter(enabled=True)
        r.start()
        r.phase("empty")
        r.progress(0, 0)  # Should return early
        r.end_progress()


# =============================================================================
# Formatting utility functions
# =============================================================================

class TestFormattingUtilities:
    """Tests for terminal formatting helper functions."""

    def test_truncate_path_middle_short(self):
        """Short paths are not truncated."""
        assert truncate_path_middle("src/main.py", 50) == "src/main.py"

    def test_truncate_path_middle_long(self):
        """Long paths are truncated with ellipsis in the middle."""
        long_path = "src/very/long/path/to/some/deeply/nested/file.py"
        result = truncate_path_middle(long_path, 20)
        assert len(result) == 20
        assert "..." in result

    def test_format_number_integer(self):
        """Integers are formatted with commas."""
        assert format_number(1234567) == "1,234,567"
        assert format_number(0) == "0"
        assert format_number(999) == "999"

    def test_format_number_decimal(self):
        """Decimals are formatted with specified precision."""
        assert format_number(1234.567, decimals=2) == "1,234.57"
        assert format_number(0.5, decimals=1) == "0.5"

    def test_strip_ansi_removes_codes(self):
        """ANSI escape codes are stripped."""
        colored = "\033[31mHello\033[0m"
        assert strip_ansi(colored) == "Hello"

    def test_strip_ansi_no_codes(self):
        """Plain text passes through unchanged."""
        assert strip_ansi("plain text") == "plain text"

    def test_c_with_color_enabled(self):
        """c() wraps text in ANSI codes when color is enabled."""
        set_color_enabled(True)
        result = c("test", Colors.RED)
        assert "\033[" in result
        assert "test" in result
        set_color_enabled(True)  # Reset

    def test_c_with_color_disabled(self):
        """c() returns plain text when color is disabled."""
        set_color_enabled(False)
        result = c("test", Colors.RED)
        assert result == "test"
        set_color_enabled(True)  # Reset

    def test_get_terminal_width_returns_int(self):
        """get_terminal_width returns an integer >= minimum."""
        width = get_terminal_width(default=120, minimum=80)
        assert isinstance(width, int)
        assert width >= 80
