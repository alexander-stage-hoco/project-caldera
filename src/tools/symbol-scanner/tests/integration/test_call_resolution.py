"""Integration tests for call resolution."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from extractors.python_extractor import PythonExtractor


class TestCrossModuleCallsResolution:
    """Integration tests for cross-module call resolution."""

    @pytest.fixture
    def extractor(self):
        return PythonExtractor()

    @pytest.fixture
    def cross_module_repo(self):
        """Path to the cross-module-calls synthetic repo."""
        repo_path = (
            Path(__file__).resolve().parents[2]
            / "eval-repos"
            / "synthetic"
            / "cross-module-calls"
        )
        if not repo_path.exists():
            pytest.skip("cross-module-calls repo not found")
        return repo_path

    @pytest.fixture
    def unresolved_externals_repo(self):
        """Path to the unresolved-externals synthetic repo."""
        repo_path = (
            Path(__file__).resolve().parents[2]
            / "eval-repos"
            / "synthetic"
            / "unresolved-externals"
        )
        if not repo_path.exists():
            pytest.skip("unresolved-externals repo not found")
        return repo_path

    def test_cross_module_calls_resolution(self, extractor, cross_module_repo):
        """Test that cross-module calls resolve correctly."""
        result = extractor.extract_directory(cross_module_repo, cross_module_repo)

        # Get calls from processor.py
        processor_calls = [
            c for c in result.calls if c.caller_file == "processor.py"
        ]

        # Calls to utils functions should resolve to utils.py
        validate_call = next(
            (c for c in processor_calls if c.callee_symbol == "validate"), None
        )
        assert validate_call is not None, "validate call not found"
        assert validate_call.callee_file == "utils.py"

        sanitize_call = next(
            (c for c in processor_calls if c.callee_symbol == "sanitize"), None
        )
        assert sanitize_call is not None, "sanitize call not found"
        assert sanitize_call.callee_file == "utils.py"

        # Get calls from main.py
        main_calls = [c for c in result.calls if c.caller_file == "main.py"]

        # Calls to processor functions should resolve to processor.py
        process_input_call = next(
            (c for c in main_calls if c.callee_symbol == "process_input"), None
        )
        assert process_input_call is not None, "process_input call not found"
        assert process_input_call.callee_file == "processor.py"

        batch_process_call = next(
            (c for c in main_calls if c.callee_symbol == "batch_process"), None
        )
        assert batch_process_call is not None, "batch_process call not found"
        assert batch_process_call.callee_file == "processor.py"

        # Call to utils.format_output should resolve to utils.py
        format_output_call = next(
            (c for c in main_calls if c.callee_symbol == "format_output"), None
        )
        assert format_output_call is not None, "format_output call not found"
        assert format_output_call.callee_file == "utils.py"

    def test_cross_module_calls_stats(self, extractor, cross_module_repo):
        """Test that resolution stats are populated."""
        result = extractor.extract_directory(cross_module_repo, cross_module_repo)

        assert result.resolution_stats is not None
        stats = result.resolution_stats

        # Should have resolved calls
        assert stats["total_resolved"] > 0
        assert stats["resolved_cross_file"] > 0

        # Summary should include resolution stats
        assert "resolution" in result.summary

    def test_same_file_resolution(self, extractor, cross_module_repo):
        """Test that calls to functions in the same file resolve correctly."""
        result = extractor.extract_directory(cross_module_repo, cross_module_repo)

        # batch_process calls process_input (same file)
        batch_process_calls = [
            c for c in result.calls
            if c.caller_file == "processor.py" and c.caller_symbol == "batch_process"
        ]

        process_input_call = next(
            (c for c in batch_process_calls if c.callee_symbol == "process_input"), None
        )
        assert process_input_call is not None
        assert process_input_call.callee_file == "processor.py"

    def test_unresolved_externals_stdlib(self, extractor, unresolved_externals_repo):
        """Test that stdlib calls remain unresolved in unresolved-externals repo."""
        result = extractor.extract_directory(
            unresolved_externals_repo, unresolved_externals_repo
        )

        # Calls to json.loads, json.dumps should remain unresolved (stdlib via dynamic)
        json_calls = [
            c for c in result.calls
            if c.callee_symbol in ("loads", "dumps")
        ]

        # These are dynamic calls to json module methods
        for call in json_calls:
            # Dynamic calls to stdlib should remain None
            assert call.callee_file is None or call.call_type == "dynamic"

    def test_unresolved_externals_local_resolution(
        self, extractor, unresolved_externals_repo
    ):
        """Test that local function calls still resolve in unresolved-externals repo."""
        result = extractor.extract_directory(
            unresolved_externals_repo, unresolved_externals_repo
        )

        # __init__ calls get_timestamp (same file)
        init_calls = [
            c for c in result.calls
            if c.caller_symbol == "__init__"
        ]

        get_timestamp_call = next(
            (c for c in init_calls if c.callee_symbol == "get_timestamp"), None
        )
        assert get_timestamp_call is not None
        assert get_timestamp_call.callee_file == "api_client.py"

        # get method calls fetch_data (same file)
        get_calls = [
            c for c in result.calls
            if c.caller_symbol == "get"
        ]

        fetch_data_call = next(
            (c for c in get_calls if c.callee_symbol == "fetch_data"), None
        )
        assert fetch_data_call is not None
        assert fetch_data_call.callee_file == "api_client.py"

    def test_builtin_calls_unresolved(self, extractor, cross_module_repo):
        """Test that builtin function calls remain unresolved."""
        result = extractor.extract_directory(cross_module_repo, cross_module_repo)

        # print calls should remain None
        print_calls = [c for c in result.calls if c.callee_symbol == "print"]

        for call in print_calls:
            assert call.callee_file is None

    def test_no_resolve_calls_flag(self, extractor, cross_module_repo):
        """Test that --no-resolve-calls flag works."""
        result = extractor.extract_directory(
            cross_module_repo, cross_module_repo, resolve_calls=False
        )

        # All callee_file should be None
        for call in result.calls:
            assert call.callee_file is None

        # No resolution stats
        assert result.resolution_stats is None


class TestResolutionWithPackages:
    """Tests for resolution with package structures."""

    @pytest.fixture
    def extractor(self):
        return PythonExtractor()

    def test_package_structure_resolution(self, extractor, temp_dir):
        """Test resolution in a package structure."""
        # Create package structure
        pkg = temp_dir / "myapp"
        pkg.mkdir()
        (pkg / "__init__.py").write_text('from .utils import helper\n')
        (pkg / "utils.py").write_text('def helper(): pass\n')
        (pkg / "main.py").write_text(
            'from . import utils\n'
            'from .utils import helper\n\n'
            'def run():\n'
            '    helper()\n'
        )

        result = extractor.extract_directory(temp_dir, temp_dir)

        # Find the helper call from main.py
        main_calls = [
            c for c in result.calls
            if c.caller_file == "myapp/main.py" and c.callee_symbol == "helper"
        ]

        assert len(main_calls) >= 1
        assert main_calls[0].callee_file == "myapp/utils.py"


class TestEdgeCases:
    """Tests for edge cases in call resolution."""

    @pytest.fixture
    def extractor(self):
        return PythonExtractor()

    def test_empty_repo(self, extractor, temp_dir):
        """Test resolution with no files."""
        result = extractor.extract_directory(temp_dir, temp_dir)

        assert result.calls == []
        # With no calls, resolution_stats should be None
        assert result.resolution_stats is None

    def test_single_file_repo(self, extractor, temp_dir):
        """Test resolution with a single file."""
        (temp_dir / "main.py").write_text(
            'def helper():\n'
            '    pass\n\n'
            'def main():\n'
            '    helper()\n'
            '    print("done")\n'
        )

        result = extractor.extract_directory(temp_dir, temp_dir)

        # helper call should resolve to same file
        helper_call = next(
            (c for c in result.calls if c.callee_symbol == "helper"), None
        )
        assert helper_call is not None
        assert helper_call.callee_file == "main.py"

        # print call should remain unresolved
        print_call = next(
            (c for c in result.calls if c.callee_symbol == "print"), None
        )
        assert print_call is not None
        assert print_call.callee_file is None

    def test_circular_imports(self, extractor, temp_dir):
        """Test resolution handles circular imports."""
        (temp_dir / "a.py").write_text(
            'from b import func_b\n\n'
            'def func_a():\n'
            '    func_b()\n'
        )
        (temp_dir / "b.py").write_text(
            'from a import func_a\n\n'
            'def func_b():\n'
            '    func_a()\n'
        )

        result = extractor.extract_directory(temp_dir, temp_dir)

        # func_b call in a.py should resolve to b.py
        a_calls = [c for c in result.calls if c.caller_file == "a.py"]
        func_b_call = next((c for c in a_calls if c.callee_symbol == "func_b"), None)
        assert func_b_call is not None
        assert func_b_call.callee_file == "b.py"

        # func_a call in b.py should resolve to a.py
        b_calls = [c for c in result.calls if c.caller_file == "b.py"]
        func_a_call = next((c for c in b_calls if c.callee_symbol == "func_a"), None)
        assert func_a_call is not None
        assert func_a_call.callee_file == "a.py"

    def test_multiple_imports_same_symbol(self, extractor, temp_dir):
        """Test that the most recent import wins for symbol resolution."""
        (temp_dir / "utils1.py").write_text('def helper(): pass\n')
        (temp_dir / "utils2.py").write_text('def helper(): pass\n')
        (temp_dir / "main.py").write_text(
            'from utils1 import helper\n'
            'from utils2 import helper  # shadows utils1.helper\n\n'
            'def main():\n'
            '    helper()\n'
        )

        result = extractor.extract_directory(temp_dir, temp_dir)

        # The last import should win
        main_calls = [c for c in result.calls if c.caller_file == "main.py"]
        helper_call = next((c for c in main_calls if c.callee_symbol == "helper"), None)
        assert helper_call is not None
        # Should resolve to utils2.py (last import)
        assert helper_call.callee_file == "utils2.py"
