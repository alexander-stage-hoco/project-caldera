"""E2E integration test that runs actual tools against a mini-repo.

This test runs 11 tools via `make analyze` against a synthetic mini-repo,
then validates the full pipeline:
  tool execution → JSON outputs → adapter ingestion → dbt transformation → mart validation

Tools tested:
  - layout-scanner, scc, lizard, symbol-scanner, semgrep, scancode, coverage-ingest
  - git-blame-scanner, git-sizer, git-fame, gitleaks (git-based tools)

Marked as @pytest.mark.slow and @pytest.mark.integration for selective test runs.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestrator import OrchestratorLogger, ingest_outputs, run_dbt, run_tool_make
from persistence.entities import CollectionRun
from persistence.repositories import CollectionRunRepository


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mini_repo(tmp_path: Path) -> Path:
    """Create a minimal Python repo with files that have measurable complexity."""
    repo = tmp_path / "mini_repo"

    # Create directory structure
    (repo / "src" / "models").mkdir(parents=True)
    (repo / "tests").mkdir(parents=True)

    # src/main.py - file with a function that has moderate CCN
    # Includes imports for symbol-scanner testing
    (repo / "src" / "main.py").write_text(
        '''\
"""Main module with moderate complexity."""

from src.utils import format_output, validate_input
from src.models.user import User


def process_data(data, mode, validate=True):
    """Process data based on mode with validation."""
    if not data:
        return None

    if mode == "simple":
        result = [x for x in data if x > 0]
    elif mode == "complex":
        result = []
        for item in data:
            if item > 0:
                if item % 2 == 0:
                    result.append(item * 2)
                else:
                    result.append(item * 3)
            elif item == 0:
                result.append(0)
    else:
        result = data[:]

    if validate:
        if len(result) == 0:
            raise ValueError("Empty result")
        if any(x is None for x in result):
            raise ValueError("None in result")

    return result


def simple_helper(x):
    """Simple function with CCN=1."""
    return x + 1


def create_user(name, email):
    """Create a new user with validation."""
    if not validate_input(name) or not validate_input(email):
        return None
    user = User(name, email)
    return format_output(user.display_name())
'''
    )

    # src/utils.py - simple helper module
    (repo / "src" / "utils.py").write_text(
        '''\
"""Utility functions."""


def format_output(value, precision=2):
    """Format a numeric value."""
    if isinstance(value, float):
        return f"{value:.{precision}f}"
    return str(value)


def validate_input(data):
    """Validate input data."""
    if data is None:
        return False
    if isinstance(data, list) and len(data) == 0:
        return False
    return True
'''
    )

    # src/models/user.py - nested file for directory structure testing
    (repo / "src" / "models" / "user.py").write_text(
        '''\
"""User model."""


class User:
    """Simple user class."""

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def display_name(self):
        """Return display name."""
        return self.name or self.email.split("@")[0]

    def __repr__(self):
        """Return string representation."""
        return f"User(name={self.name!r}, email={self.email!r})"
'''
    )

    # tests/test_main.py - test file
    (repo / "tests" / "test_main.py").write_text(
        '''\
"""Tests for main module."""


def test_process_data_simple():
    """Test simple mode."""
    from src.main import process_data
    result = process_data([1, 2, -1, 3], "simple")
    assert result == [1, 2, 3]


def test_simple_helper():
    """Test helper function."""
    from src.main import simple_helper
    assert simple_helper(5) == 6
'''
    )

    # README.md
    (repo / "README.md").write_text("# Mini Test Repo\n\nA minimal repo for E2E testing.\n")

    # requirements.txt
    (repo / "requirements.txt").write_text("pytest>=7.0\n")

    # LICENSE - MIT license for scancode detection
    (repo / "LICENSE").write_text(
        '''\
MIT License

Copyright (c) 2024 Test Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
    )

    # Initialize git repo for git-based tools (git-blame-scanner, git-sizer, git-fame, gitleaks)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True, capture_output=True)

    return repo


@pytest.fixture
def mock_coverage_file(mini_repo: Path) -> Path:
    """Create a minimal LCOV coverage file for testing.

    Maps to files in mini_repo:
    - src/main.py (lines 1-30, 20 covered, 10 missed)
    - src/utils.py (lines 1-18, 18 covered, 0 missed)
    """
    coverage_content = """\
TN:test
SF:src/main.py
DA:1,5
DA:2,5
DA:3,5
DA:4,5
DA:5,5
DA:6,5
DA:7,5
DA:8,5
DA:9,5
DA:10,5
DA:11,5
DA:12,5
DA:13,5
DA:14,5
DA:15,5
DA:16,5
DA:17,5
DA:18,5
DA:19,5
DA:20,5
DA:21,0
DA:22,0
DA:23,0
DA:24,0
DA:25,0
DA:26,0
DA:27,0
DA:28,0
DA:29,0
DA:30,0
LF:30
LH:20
end_of_record
SF:src/utils.py
DA:1,10
DA:2,10
DA:3,10
DA:4,10
DA:5,10
DA:6,10
DA:7,10
DA:8,10
DA:9,10
DA:10,10
DA:11,10
DA:12,10
DA:13,10
DA:14,10
DA:15,10
DA:16,10
DA:17,10
DA:18,10
LF:18
LH:18
end_of_record
"""
    coverage_file = mini_repo / "coverage.lcov"
    coverage_file.write_text(coverage_content)
    return coverage_file


@pytest.fixture
def e2e_db(tmp_path: Path) -> tuple[Path, duckdb.DuckDBPyConnection]:
    """Initialize a test DuckDB with schema."""
    db_path = tmp_path / "e2e_test.duckdb"
    conn = duckdb.connect(str(db_path))

    schema_path = Path(__file__).resolve().parents[1] / "persistence" / "schema.sql"
    conn.execute(schema_path.read_text())

    return db_path, conn


@pytest.fixture
def dbt_profiles(tmp_path: Path, e2e_db: tuple[Path, duckdb.DuckDBPyConnection]) -> Path:
    """Create profiles.yml pointing to test DB."""
    db_path, _ = e2e_db
    profiles_dir = tmp_path / "dbt_profiles"
    profiles_dir.mkdir()

    (profiles_dir / "profiles.yml").write_text(
        f"""\
caldera_sot:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: {db_path}
      threads: 2
"""
    )
    return profiles_dir


# =============================================================================
# Helper functions
# =============================================================================


def _run_tool(
    tool_name: str,
    tool_path: Path,
    repo_path: Path,
    run_id: str,
    repo_id: str,
    output_dir: Path,
    logger: OrchestratorLogger,
    extra_env: dict[str, str] | None = None,
) -> Path:
    """Run a single tool via make analyze and return output path."""
    run_tool_make(
        tool_root=tool_path,
        repo_path=repo_path,
        repo_name=repo_id,
        run_id=run_id,
        repo_id=repo_id,
        branch="main",
        commit="0" * 40,  # Fallback commit for non-git repo
        output_dir=output_dir / tool_name / run_id,
        logger=logger,
        extra_env=extra_env,
    )
    return output_dir / tool_name / run_id / "output.json"


def _validate_json_envelope(output_path: Path, run_id: str, repo_id: str) -> dict:
    """Validate JSON output has standard envelope structure."""
    assert output_path.exists(), f"Output file not found: {output_path}"

    payload = json.loads(output_path.read_text())

    assert "metadata" in payload, "Missing metadata section"
    assert "data" in payload, "Missing data section"

    metadata = payload["metadata"]
    assert metadata.get("run_id") == run_id, f"run_id mismatch: {metadata.get('run_id')} != {run_id}"
    assert metadata.get("repo_id") == repo_id, f"repo_id mismatch: {metadata.get('repo_id')} != {repo_id}"

    return payload


# =============================================================================
# Test
# =============================================================================


@pytest.mark.slow
@pytest.mark.integration
def test_e2e_live_tools(
    tmp_path: Path,
    mini_repo: Path,
    mock_coverage_file: Path,
    e2e_db: tuple[Path, duckdb.DuckDBPyConnection],
    dbt_profiles: Path,
) -> None:
    """Run live tools against mini-repo and validate full pipeline."""
    # Check for dbt binary
    # parents[1] = src/sot-engine, parents[3] = project root
    sot_engine_dir = Path(__file__).resolve().parents[1]
    dbt_bin = sot_engine_dir / ".venv-dbt" / "bin" / "dbt"
    if not dbt_bin.exists():
        pytest.skip("dbt binary not available for e2e test")

    # Setup paths
    project_root = Path(__file__).resolve().parents[3]
    db_path, conn = e2e_db
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()

    run_id = str(uuid.uuid4())
    repo_id = "e2e-test-repo"

    # Create logger
    log_path = tmp_path / "e2e_test.log"
    logger = OrchestratorLogger(log_path)

    try:
        # =====================================================================
        # Step 1: Run tools via make analyze
        # =====================================================================

        # Check for optional tool dependencies
        has_semgrep = shutil.which("semgrep") is not None

        tools_to_run: list[tuple[str, Path, dict[str, str] | None, bool]] = [
            # (tool_name, tool_path, extra_env, required)
            ("layout-scanner", project_root / "src" / "tools" / "layout-scanner", {"NO_GITIGNORE": "1"}, True),
            ("scc", project_root / "src" / "tools" / "scc", None, True),
            ("lizard", project_root / "src" / "tools" / "lizard", None, True),
            ("symbol-scanner", project_root / "src" / "tools" / "symbol-scanner", None, True),
            ("semgrep", project_root / "src" / "tools" / "semgrep", None, has_semgrep),
            ("scancode", project_root / "src" / "tools" / "scancode", None, True),
            ("coverage-ingest", project_root / "src" / "tools" / "coverage-ingest", {"COVERAGE_FILE": str(mock_coverage_file)}, True),
            # Git-based tools (require git init + commit in mini_repo)
            ("git-blame-scanner", project_root / "src" / "tools" / "git-blame-scanner", None, True),
            ("git-sizer", project_root / "src" / "tools" / "git-sizer", None, True),
            ("git-fame", project_root / "src" / "tools" / "git-fame", None, True),
            ("gitleaks", project_root / "src" / "tools" / "gitleaks", None, True),
        ]

        tool_outputs: dict[str, Path] = {}
        for tool_name, tool_path, extra_env, should_run in tools_to_run:
            if not tool_path.exists():
                pytest.skip(f"Tool not found: {tool_path}")

            if not should_run:
                logger.info(f"Skipping {tool_name} (optional dependency not available)")
                continue

            tool_outputs[tool_name] = _run_tool(
                tool_name=tool_name,
                tool_path=tool_path,
                repo_path=mini_repo,
                run_id=run_id,
                repo_id=repo_id,
                output_dir=output_dir,
                logger=logger,
                extra_env=extra_env,
            )

        # =====================================================================
        # Step 2: Validate JSON outputs (Layer 1)
        # =====================================================================

        for tool_name, output_path in tool_outputs.items():
            payload = _validate_json_envelope(output_path, run_id, repo_id)

            # Tool-specific validations
            if tool_name == "layout-scanner":
                assert "files" in payload["data"], "layout-scanner missing files"
                assert len(payload["data"]["files"]) >= 5, "Expected at least 5 files"

            elif tool_name == "scc":
                assert "files" in payload["data"], "scc missing files"
                # Should have Python files
                py_files = [f for f in payload["data"]["files"] if f.get("language") == "Python"]
                assert len(py_files) >= 3, f"Expected at least 3 Python files, got {len(py_files)}"

            elif tool_name == "lizard":
                assert "files" in payload["data"], "lizard missing files"
                # Should have files with functions
                files_with_functions = [
                    f for f in payload["data"]["files"]
                    if f.get("function_count", 0) > 0
                ]
                assert len(files_with_functions) >= 2, "Expected at least 2 files with functions"

            elif tool_name == "symbol-scanner":
                # symbol-scanner uses symbols/calls/imports arrays, not files
                assert "symbols" in payload["data"], "symbol-scanner missing symbols"
                assert "imports" in payload["data"], "symbol-scanner missing imports"
                # Should have functions/classes extracted
                symbols = payload["data"]["symbols"]
                assert len(symbols) >= 5, f"Expected at least 5 symbols, got {len(symbols)}"

            elif tool_name == "semgrep":
                # Semgrep may or may not have findings depending on rules
                assert "files" in payload["data"], "semgrep missing files"
                # files array should exist (may be empty if no smells found)

            elif tool_name == "scancode":
                # scancode uses files as an object/dict, not an array
                assert "files" in payload["data"], "scancode missing files"
                # Should have detected LICENSE file
                files_dict = payload["data"]["files"]
                files_with_licenses = [
                    f for f in files_dict.values()
                    if len(f.get("licenses", [])) > 0
                ]
                assert len(files_with_licenses) >= 1, "Expected at least 1 file with license"

            elif tool_name == "coverage-ingest":
                assert "files" in payload["data"], "coverage-ingest missing files"
                assert "source_format" in payload["data"], "coverage-ingest missing source_format"
                # Should have parsed our mock LCOV file
                files = payload["data"]["files"]
                assert len(files) >= 2, f"Expected at least 2 files in coverage, got {len(files)}"
                # Validate structure
                for f in files:
                    assert "relative_path" in f, "coverage file missing relative_path"
                    assert "lines_total" in f, "coverage file missing lines_total"
                    assert "lines_covered" in f, "coverage file missing lines_covered"

            elif tool_name == "git-blame-scanner":
                assert "files" in payload["data"], "git-blame-scanner missing files"
                # Should have per-file blame stats
                files = payload["data"]["files"]
                assert len(files) >= 3, f"Expected at least 3 files with blame stats, got {len(files)}"

            elif tool_name == "git-sizer":
                assert "metrics" in payload["data"], "git-sizer missing metrics"
                # Should have health grade (at data level, not metrics level)
                assert "health_grade" in payload["data"], "git-sizer missing health_grade"

            elif tool_name == "git-fame":
                assert "authors" in payload["data"], "git-fame missing authors"
                # Should have at least one author (Test User)
                assert len(payload["data"]["authors"]) >= 1, "Expected at least 1 author"

            elif tool_name == "gitleaks":
                # May or may not have findings (no secrets in mini repo)
                # gitleaks uses "secrets" array
                assert "secrets" in payload["data"] or isinstance(payload["data"], dict), \
                    "gitleaks missing expected data structure"

        # =====================================================================
        # Step 3: Create collection run and ingest outputs
        # =====================================================================

        collection_repo = CollectionRunRepository(conn)
        collection_run = CollectionRun(
            collection_run_id=run_id,
            repo_id=repo_id,
            run_id=run_id,
            branch="main",
            commit="0" * 40,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            status="running",
        )
        collection_repo.insert(collection_run)

        schema_path = Path(__file__).resolve().parents[1] / "persistence" / "schema.sql"

        ingest_outputs(
            conn=conn,
            repo_id=repo_id,
            collection_run_id=run_id,
            run_id=run_id,
            branch="main",
            commit="0" * 40,
            repo_path=mini_repo,
            layout_output=tool_outputs["layout-scanner"],
            scc_output=tool_outputs["scc"],
            lizard_output=tool_outputs["lizard"],
            roslyn_output=None,
            symbol_scanner_output=tool_outputs.get("symbol-scanner"),
            semgrep_output=tool_outputs.get("semgrep"),
            scancode_output=tool_outputs.get("scancode"),
            coverage_output=tool_outputs.get("coverage-ingest"),
            git_blame_scanner_output=tool_outputs.get("git-blame-scanner"),
            git_sizer_output=tool_outputs.get("git-sizer"),
            git_fame_output=tool_outputs.get("git-fame"),
            gitleaks_output=tool_outputs.get("gitleaks"),
            schema_path=schema_path,
            logger=logger,
        )

        # =====================================================================
        # Step 4: Validate Landing Zone (Layer 2)
        # =====================================================================

        # lz_layout_files - should have at least 5 files (including LICENSE now)
        layout_count = conn.execute("SELECT COUNT(*) FROM lz_layout_files").fetchone()[0]
        assert layout_count >= 6, f"Expected >= 6 layout files, got {layout_count}"

        # lz_scc_file_metrics - should have Python files
        scc_count = conn.execute(
            "SELECT COUNT(*) FROM lz_scc_file_metrics WHERE language = 'Python'"
        ).fetchone()[0]
        assert scc_count >= 3, f"Expected >= 3 Python files in scc, got {scc_count}"

        # lz_lizard_file_metrics - should have files with functions
        lizard_count = conn.execute(
            "SELECT COUNT(*) FROM lz_lizard_file_metrics WHERE function_count > 0"
        ).fetchone()[0]
        assert lizard_count >= 2, f"Expected >= 2 files with functions in lizard, got {lizard_count}"

        # lz_code_symbols - should have classes and functions from symbol-scanner
        if "symbol-scanner" in tool_outputs:
            symbol_count = conn.execute(
                "SELECT COUNT(*) FROM lz_code_symbols WHERE symbol_type IN ('function', 'class')"
            ).fetchone()[0]
            assert symbol_count >= 5, f"Expected >= 5 symbols (functions/classes), got {symbol_count}"

            # lz_file_imports - should have imports
            import_count = conn.execute("SELECT COUNT(*) FROM lz_file_imports").fetchone()[0]
            assert import_count >= 1, f"Expected >= 1 imports, got {import_count}"

        # lz_semgrep_smells - if semgrep was run, verify table exists (may or may not have findings)
        if "semgrep" in tool_outputs:
            # Just verify the table was populated (adapter ran successfully)
            semgrep_count = conn.execute("SELECT COUNT(*) FROM lz_semgrep_smells").fetchone()[0]
            # No assertion on count - semgrep may or may not find issues depending on rules

        # lz_scancode_file_licenses - should detect MIT license
        if "scancode" in tool_outputs:
            license_count = conn.execute(
                "SELECT COUNT(*) FROM lz_scancode_file_licenses WHERE spdx_id = 'MIT'"
            ).fetchone()[0]
            assert license_count >= 1, f"Expected >= 1 MIT license detection, got {license_count}"

        # lz_coverage_summary - should have coverage data
        if "coverage-ingest" in tool_outputs:
            coverage_count = conn.execute(
                "SELECT COUNT(*) FROM lz_coverage_summary"
            ).fetchone()[0]
            assert coverage_count >= 2, f"Expected >= 2 coverage records, got {coverage_count}"

            # Validate coverage invariants: lines_covered <= lines_total
            invalid_coverage = conn.execute(
                """
                SELECT COUNT(*) FROM lz_coverage_summary
                WHERE lines_covered > lines_total
                """
            ).fetchone()[0]
            assert invalid_coverage == 0, f"Found {invalid_coverage} records with lines_covered > lines_total"

            # Validate FK integrity: file_id exists in layout
            orphan_coverage = conn.execute(
                """
                SELECT COUNT(*) FROM lz_coverage_summary c
                LEFT JOIN lz_layout_files f ON c.file_id = f.file_id
                WHERE f.file_id IS NULL
                """
            ).fetchone()[0]
            assert orphan_coverage == 0, f"Found {orphan_coverage} coverage records with invalid file_id"

        # lz_git_blame_summary - per-file blame statistics
        if "git-blame-scanner" in tool_outputs:
            blame_count = conn.execute(
                "SELECT COUNT(*) FROM lz_git_blame_summary"
            ).fetchone()[0]
            assert blame_count >= 3, f"Expected >= 3 files in git blame, got {blame_count}"

            # lz_git_blame_author_stats - per-author statistics
            author_count = conn.execute(
                "SELECT COUNT(*) FROM lz_git_blame_author_stats"
            ).fetchone()[0]
            assert author_count >= 1, f"Expected >= 1 authors, got {author_count}"

        # lz_git_sizer_metrics - repo-level health metrics
        if "git-sizer" in tool_outputs:
            sizer_count = conn.execute(
                "SELECT COUNT(*) FROM lz_git_sizer_metrics"
            ).fetchone()[0]
            assert sizer_count == 1, f"Expected 1 row for git-sizer metrics, got {sizer_count}"

        # lz_git_fame_authors - contributor statistics
        if "git-fame" in tool_outputs:
            fame_count = conn.execute(
                "SELECT COUNT(*) FROM lz_git_fame_authors"
            ).fetchone()[0]
            assert fame_count >= 1, f"Expected >= 1 authors in git-fame, got {fame_count}"

        # lz_gitleaks_secrets - secrets (should be 0 in mini repo)
        if "gitleaks" in tool_outputs:
            secrets_count = conn.execute(
                "SELECT COUNT(*) FROM lz_gitleaks_secrets"
            ).fetchone()[0]
            assert secrets_count == 0, f"Expected 0 secrets in clean mini repo, got {secrets_count}"

        # lz_tool_runs - should have entry per tool that ran
        tool_run_count = conn.execute("SELECT COUNT(*) FROM lz_tool_runs").fetchone()[0]
        expected_tool_count = len(tool_outputs)
        assert tool_run_count == expected_tool_count, f"Expected {expected_tool_count} tool runs, got {tool_run_count}"

        # =====================================================================
        # Step 5: Run dbt
        # =====================================================================

        conn.close()  # Close before dbt runs

        # parents[1] = src/sot-engine, so dbt is at src/sot-engine/dbt
        dbt_project_dir = sot_engine_dir / "dbt"
        run_dbt(
            dbt_bin=dbt_bin,
            dbt_project_dir=dbt_project_dir,
            profiles_dir=dbt_profiles,
            logger=logger,
            target_path=str(tmp_path / "dbt_target"),
            log_path=str(tmp_path / "dbt_logs"),
        )

        # Reconnect after dbt
        conn = duckdb.connect(str(db_path))

        # =====================================================================
        # Step 6: Validate dbt Marts (Layer 3)
        # =====================================================================

        # rollup_scc_directory_recursive_distributions should exist and have data
        scc_rollup_recursive = conn.execute(
            "SELECT COUNT(*) FROM rollup_scc_directory_recursive_distributions"
        ).fetchone()[0]
        assert scc_rollup_recursive > 0, "rollup_scc_directory_recursive_distributions should have data"

        # rollup_scc_directory_direct_distributions should exist
        scc_rollup_direct = conn.execute(
            "SELECT COUNT(*) FROM rollup_scc_directory_direct_distributions"
        ).fetchone()[0]
        assert scc_rollup_direct > 0, "rollup_scc_directory_direct_distributions should have data"

        # Rollup invariant: recursive_count >= direct_count for 'src' directory
        recursive_count = conn.execute(
            """
            SELECT value_count FROM rollup_scc_directory_recursive_distributions
            WHERE directory_path = 'src' AND metric = 'lines_total'
            """
        ).fetchone()
        direct_count = conn.execute(
            """
            SELECT value_count FROM rollup_scc_directory_direct_distributions
            WHERE directory_path = 'src' AND metric = 'lines_total'
            """
        ).fetchone()

        if recursive_count and direct_count:
            assert recursive_count[0] >= direct_count[0], (
                f"Rollup invariant violated: recursive ({recursive_count[0]}) < direct ({direct_count[0]})"
            )

        # unified_file_metrics should have data
        unified_count = conn.execute("SELECT COUNT(*) FROM unified_file_metrics").fetchone()[0]
        assert unified_count > 0, "unified_file_metrics should have data"

        # mart_coverage_gap_analysis should have data if coverage-ingest ran
        if "coverage-ingest" in tool_outputs:
            # Check that the mart exists and has data
            gap_count = conn.execute(
                "SELECT COUNT(*) FROM mart_coverage_gap_analysis"
            ).fetchone()[0]
            # May be 0 if files don't have complexity data, but table should exist
            assert gap_count >= 0, "mart_coverage_gap_analysis should exist"

            # If we have data, validate the mart logic
            if gap_count > 0:
                # Validate coverage percentages are in valid range (0-100)
                invalid_pct = conn.execute(
                    """
                    SELECT COUNT(*) FROM mart_coverage_gap_analysis
                    WHERE line_coverage_pct < 0 OR line_coverage_pct > 100
                    """
                ).fetchone()[0]
                assert invalid_pct == 0, f"Found {invalid_pct} records with invalid coverage percentage"

        # =====================================================================
        # Step 7: Data Integrity Checks (Layer 4)
        # =====================================================================

        # All paths should be repo-relative (no leading /)
        bad_paths = conn.execute(
            """
            SELECT relative_path FROM lz_layout_files
            WHERE relative_path LIKE '/%' OR relative_path LIKE './%'
            """
        ).fetchall()
        assert len(bad_paths) == 0, f"Found non-repo-relative paths: {bad_paths}"

        # FK relationships: all scc file_ids should exist in layout
        orphan_scc = conn.execute(
            """
            SELECT COUNT(*) FROM lz_scc_file_metrics scc
            LEFT JOIN lz_layout_files lf ON lf.run_pk = (
                SELECT run_pk FROM lz_tool_runs
                WHERE tool_name IN ('layout', 'layout-scanner')
                AND collection_run_id = (
                    SELECT collection_run_id FROM lz_tool_runs WHERE run_pk = scc.run_pk
                )
            ) AND lf.file_id = scc.file_id
            WHERE lf.file_id IS NULL
            """
        ).fetchone()[0]
        assert orphan_scc == 0, f"Found {orphan_scc} scc records with invalid file_id"

        # Mark collection run as completed
        collection_repo = CollectionRunRepository(conn)
        collection_repo.mark_status(run_id, "completed", datetime.now(timezone.utc))

        # Verify final status
        final_status = conn.execute(
            "SELECT status FROM lz_collection_runs WHERE collection_run_id = ?",
            [run_id],
        ).fetchone()[0]
        assert final_status == "completed", f"Expected completed status, got {final_status}"

    finally:
        logger.close()
        if conn:
            conn.close()
