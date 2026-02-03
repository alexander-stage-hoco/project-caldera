"""End-to-end integration tests for symbol-scanner."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


class TestEndToEnd:
    """End-to-end tests for the symbol-scanner tool."""

    @pytest.fixture
    def tool_dir(self):
        """Get the tool directory."""
        return Path(__file__).resolve().parents[2]

    @pytest.fixture
    def synthetic_repos_dir(self, tool_dir):
        """Get the synthetic repos directory."""
        return tool_dir / "eval-repos" / "synthetic"

    def test_simple_functions_repo(self, tool_dir, synthetic_repos_dir, tmp_path):
        """Test analysis of simple-functions repo."""
        repo_path = synthetic_repos_dir / "simple-functions"
        if not repo_path.exists():
            pytest.skip("simple-functions repo not found")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Run analysis
        result = subprocess.run(
            [
                "python", "scripts/analyze.py",
                "--repo-path", str(repo_path),
                "--output-dir", str(output_dir),
                "--run-id", "test-run-1",
                "--repo-id", "test-repo-1",
                "--branch", "main",
                "--commit", "0" * 40,
            ],
            cwd=tool_dir,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Analysis failed: {result.stderr}"

        # Check output file
        output_file = output_dir / "output.json"
        assert output_file.exists()

        # Validate output structure
        with open(output_file) as f:
            output = json.load(f)

        assert "metadata" in output
        assert "data" in output
        assert output["metadata"]["tool_name"] == "symbol-scanner"
        assert output["metadata"]["run_id"] == "test-run-1"
        assert output["metadata"]["repo_id"] == "test-repo-1"

        # Check data
        data = output["data"]
        assert "symbols" in data
        assert "calls" in data
        assert "imports" in data
        assert "summary" in data

        # Should find functions
        assert len(data["symbols"]) > 0
        symbol_names = {s["symbol_name"] for s in data["symbols"]}
        assert "greet" in symbol_names
        assert "process" in symbol_names
        assert "main" in symbol_names

    def test_class_hierarchy_repo(self, tool_dir, synthetic_repos_dir, tmp_path):
        """Test analysis of class-hierarchy repo."""
        repo_path = synthetic_repos_dir / "class-hierarchy"
        if not repo_path.exists():
            pytest.skip("class-hierarchy repo not found")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Run analysis
        result = subprocess.run(
            [
                "python", "scripts/analyze.py",
                "--repo-path", str(repo_path),
                "--output-dir", str(output_dir),
                "--run-id", "test-run-2",
                "--repo-id", "test-repo-2",
                "--branch", "main",
                "--commit", "0" * 40,
            ],
            cwd=tool_dir,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Analysis failed: {result.stderr}"

        output_file = output_dir / "output.json"
        with open(output_file) as f:
            output = json.load(f)

        data = output["data"]

        # Should find classes
        classes = [s for s in data["symbols"] if s["symbol_type"] == "class"]
        class_names = {c["symbol_name"] for c in classes}
        assert "BaseModel" in class_names
        assert "User" in class_names
        assert "Admin" in class_names

        # Should find methods
        methods = [s for s in data["symbols"] if s["symbol_type"] == "method"]
        assert len(methods) > 0

    def test_import_patterns_repo(self, tool_dir, synthetic_repos_dir, tmp_path):
        """Test analysis of import-patterns repo."""
        repo_path = synthetic_repos_dir / "import-patterns"
        if not repo_path.exists():
            pytest.skip("import-patterns repo not found")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Run analysis
        result = subprocess.run(
            [
                "python", "scripts/analyze.py",
                "--repo-path", str(repo_path),
                "--output-dir", str(output_dir),
                "--run-id", "test-run-3",
                "--repo-id", "test-repo-3",
                "--branch", "main",
                "--commit", "0" * 40,
            ],
            cwd=tool_dir,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Analysis failed: {result.stderr}"

        output_file = output_dir / "output.json"
        with open(output_file) as f:
            output = json.load(f)

        data = output["data"]

        # Should find imports
        assert len(data["imports"]) > 0
        import_paths = {i["imported_path"] for i in data["imports"]}
        assert "os" in import_paths
        assert "sys" in import_paths
        assert "pathlib" in import_paths

    def test_cross_module_calls_repo(self, tool_dir, synthetic_repos_dir, tmp_path):
        """Test analysis of cross-module-calls repo."""
        repo_path = synthetic_repos_dir / "cross-module-calls"
        if not repo_path.exists():
            pytest.skip("cross-module-calls repo not found")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Run analysis
        result = subprocess.run(
            [
                "python", "scripts/analyze.py",
                "--repo-path", str(repo_path),
                "--output-dir", str(output_dir),
                "--run-id", "test-run-4",
                "--repo-id", "test-repo-4",
                "--branch", "main",
                "--commit", "0" * 40,
            ],
            cwd=tool_dir,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Analysis failed: {result.stderr}"

        output_file = output_dir / "output.json"
        with open(output_file) as f:
            output = json.load(f)

        data = output["data"]

        # Should find multiple files
        file_paths = {s["path"] for s in data["symbols"]}
        assert len(file_paths) >= 2  # utils.py, processor.py, main.py

        # Should find cross-module imports
        assert len(data["imports"]) > 0
        import_paths = {i["imported_path"] for i in data["imports"]}
        assert "utils" in import_paths

        # Should find calls
        assert len(data["calls"]) > 0

    def test_output_schema_validation(self, tool_dir, synthetic_repos_dir, tmp_path):
        """Test that output conforms to JSON schema."""
        try:
            import jsonschema
        except ImportError:
            pytest.skip("jsonschema not installed")

        repo_path = synthetic_repos_dir / "simple-functions"
        if not repo_path.exists():
            pytest.skip("simple-functions repo not found")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Run analysis
        subprocess.run(
            [
                "python", "scripts/analyze.py",
                "--repo-path", str(repo_path),
                "--output-dir", str(output_dir),
                "--run-id", "test-run-schema",
                "--repo-id", "test-repo-schema",
                "--branch", "main",
                "--commit", "0" * 40,
            ],
            cwd=tool_dir,
            capture_output=True,
            text=True,
            check=True,
        )

        # Load output and schema
        output_file = output_dir / "output.json"
        schema_file = tool_dir / "schemas" / "output.schema.json"

        with open(output_file) as f:
            output = json.load(f)
        with open(schema_file) as f:
            schema = json.load(f)

        # Validate
        jsonschema.validate(output, schema)
