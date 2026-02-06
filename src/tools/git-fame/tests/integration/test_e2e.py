"""End-to-end integration tests for git-fame.

Integration tests verify the complete pipeline works:
1. analyze.py produces valid output
2. evaluate.py scores the output
3. Output matches schema

For examples, see:
- src/tools/scc/tests/integration/test_e2e.py
- src/tools/git-sizer/tests/integration/test_e2e.py
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tool_root() -> Path:
    """Return the tool root directory."""
    return Path(__file__).parents[2]


@pytest.fixture
def synthetic_repo(tool_root: Path) -> Path:
    """Return the synthetic test repository path."""
    return tool_root / "eval-repos" / "synthetic"


def test_full_pipeline(tool_root: Path, synthetic_repo: Path):
    """Test complete analysis and evaluation pipeline.

    This test runs:
    1. make analyze on synthetic repo
    2. Verifies output.json is created
    3. Verifies output validates against schema

    TODO: Implement once analyze.py is complete
    """
    # Skip if synthetic repo is empty
    if not synthetic_repo.exists() or not any(synthetic_repo.iterdir()):
        pytest.skip("Synthetic repo is empty - add test files first")

    # Create temp output directory
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Run analysis
        env = os.environ.copy()
        env.update({
            "REPO_PATH": str(synthetic_repo),
            "REPO_NAME": "synthetic",
            "OUTPUT_DIR": str(output_dir),
            "RUN_ID": "test-integration",
            "REPO_ID": "test-repo",
            "BRANCH": "main",
            "SKIP_SETUP": "1",
        })

        # Run make analyze
        result = subprocess.run(
            ["make", "analyze"],
            cwd=tool_root,
            env=env,
            capture_output=True,
            text=True,
        )

        # Check analysis succeeded
        assert result.returncode == 0, f"make analyze failed: {result.stderr}"

        # Check output file was created
        output_path = output_dir / "output.json"
        assert output_path.exists(), "output.json not created"

        # Load and validate structure
        output = json.loads(output_path.read_text())
        assert "metadata" in output
        assert "data" in output
        assert output["metadata"]["tool_name"] == "git-fame"


def test_schema_validation(tool_root: Path):
    """Test that existing output validates against schema.

    Loads the most recent output and validates it against the schema.
    """
    # Find most recent output
    outputs_dir = tool_root / "outputs"
    if not outputs_dir.exists():
        pytest.skip("No outputs directory - run make analyze first")

    output_dirs = sorted(
        [d for d in outputs_dir.iterdir() if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    if not output_dirs:
        pytest.skip("No output directories found")

    output_path = output_dirs[0] / "output.json"
    if not output_path.exists():
        pytest.skip("No output.json in latest output directory")

    # Load schema
    schema_path = tool_root / "schemas" / "output.schema.json"
    assert schema_path.exists(), "Schema file missing"

    # Validate
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed")

    schema = json.loads(schema_path.read_text())
    output = json.loads(output_path.read_text())
    jsonschema.validate(output, schema)
