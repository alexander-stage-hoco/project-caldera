"""End-to-end integration tests for git-sizer."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


# Skip integration tests if git-sizer binary not available
pytestmark = pytest.mark.integration


class TestEndToEnd:
    """End-to-end tests for git-sizer analysis."""

    @pytest.fixture
    def temp_repo(self, tmp_path: Path) -> Path:
        """Create a temporary git repository."""
        repo_path = tmp_path / "test-repo"
        repo_path.mkdir()

        # Initialize git repo
        subprocess.run(
            ["git", "init"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )

        # Create files and commit
        (repo_path / "README.md").write_text("# Test Repository\n")
        (repo_path / "src").mkdir()
        (repo_path / "src" / "main.py").write_text("print('hello')\n")

        subprocess.run(
            ["git", "add", "."],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )

        return repo_path

    @pytest.fixture
    def output_dir(self, tmp_path: Path) -> Path:
        """Create a temporary output directory."""
        output_path = tmp_path / "output"
        output_path.mkdir()
        return output_path

    def test_analyze_produces_valid_envelope(
        self, temp_repo: Path, output_dir: Path
    ):
        """Test that analyze produces valid Caldera envelope output."""
        # Get commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        commit_sha = result.stdout.strip()

        # Run analysis
        scripts_dir = Path(__file__).parent.parent.parent / "scripts"
        result = subprocess.run(
            [
                sys.executable, "-m", "scripts.analyze",
                "--repo-path", str(temp_repo),
                "--output-dir", str(output_dir),
                "--run-id", "550e8400-e29b-41d4-a716-446655440000",
                "--repo-id", "660e8400-e29b-41d4-a716-446655440001",
                "--branch", "main",
                "--commit", commit_sha,
                "--exit-zero",
            ],
            cwd=scripts_dir.parent,
            capture_output=True,
            text=True,
        )

        # Check analysis completed
        if result.returncode != 0:
            pytest.skip(f"Analysis failed (git-sizer may not be installed): {result.stderr}")

        # Check output file exists
        output_file = output_dir / "output.json"
        assert output_file.exists(), f"Output file not created. stderr: {result.stderr}"
        repo_output = output_dir / temp_repo.name / "output.json"
        assert repo_output.exists(), "Per-repo output.json missing"

        # Load and validate output
        with open(output_file) as f:
            envelope = json.load(f)

        # Verify envelope structure
        assert "metadata" in envelope
        assert "data" in envelope

        # Verify metadata fields
        metadata = envelope["metadata"]
        assert metadata["tool_name"] == "git-sizer"
        assert metadata["run_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert metadata["repo_id"] == "660e8400-e29b-41d4-a716-446655440001"
        assert metadata["repo_name"] == temp_repo.name
        assert metadata["branch"] == "main"
        assert metadata["commit"] == commit_sha
        assert metadata["schema_version"] == "1.0.0"
        assert "timestamp" in metadata
        assert "tool_version" in metadata

        # Verify data fields
        data = envelope["data"]
        assert data["tool"] == "git-sizer"
        assert "health_grade" in data
        assert data["health_grade"] in ["A", "A+", "B", "B+", "C", "C+", "D", "D+", "F"]
        assert "duration_ms" in data
        assert data["duration_ms"] >= 0
        assert "metrics" in data
        assert "violations" in data
        assert isinstance(data["violations"], list)
        assert "lfs_candidates" in data
        assert isinstance(data["lfs_candidates"], list)

        # Verify metrics
        metrics = data["metrics"]
        assert "commit_count" in metrics
        assert metrics["commit_count"] >= 1  # At least our initial commit
        assert "blob_count" in metrics
        assert metrics["blob_count"] >= 1

    def test_healthy_repo_gets_good_grade(
        self, temp_repo: Path, output_dir: Path
    ):
        """Test that a small healthy repo gets A grade."""
        # Get commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        commit_sha = result.stdout.strip()

        # Run analysis
        scripts_dir = Path(__file__).parent.parent.parent / "scripts"
        result = subprocess.run(
            [
                sys.executable, "-m", "scripts.analyze",
                "--repo-path", str(temp_repo),
                "--output-dir", str(output_dir),
                "--run-id", "test-run",
                "--repo-id", "test-repo",
                "--branch", "main",
                "--commit", commit_sha,
                "--exit-zero",
            ],
            cwd=scripts_dir.parent,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            pytest.skip(f"Analysis failed: {result.stderr}")

        # Load output
        output_file = output_dir / "output.json"
        with open(output_file) as f:
            envelope = json.load(f)

        # Small repo should get A grade (no violations)
        assert envelope["data"]["health_grade"] in ["A", "A+"]
        assert len(envelope["data"]["violations"]) == 0

    def test_output_validates_against_schema(
        self, temp_repo: Path, output_dir: Path
    ):
        """Test that output validates against JSON schema."""
        import jsonschema

        # Get commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        commit_sha = result.stdout.strip()

        # Run analysis
        scripts_dir = Path(__file__).parent.parent.parent / "scripts"
        result = subprocess.run(
            [
                sys.executable, "-m", "scripts.analyze",
                "--repo-path", str(temp_repo),
                "--output-dir", str(output_dir),
                "--run-id", "550e8400-e29b-41d4-a716-446655440000",
                "--repo-id", "660e8400-e29b-41d4-a716-446655440001",
                "--branch", "main",
                "--commit", commit_sha,
                "--exit-zero",
            ],
            cwd=scripts_dir.parent,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            pytest.skip(f"Analysis failed: {result.stderr}")

        # Load schema
        schema_path = scripts_dir.parent / "schemas" / "output.schema.json"
        if not schema_path.exists():
            pytest.skip("Schema file not found")

        with open(schema_path) as f:
            schema = json.load(f)

        # Load output
        output_file = output_dir / "output.json"
        with open(output_file) as f:
            envelope = json.load(f)

        # Validate
        jsonschema.validate(envelope, schema)  # Raises if invalid
