"""Multi-tool integration tests.

Ingests multiple tool fixtures and verifies cross-tool consistency
at the landing zone level (no dbt dependency).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _pipeline_helpers import FIXTURES_DIR, SCHEMA_PATH, load_all_fixtures
from orchestrator import OrchestratorLogger, ingest_outputs
from persistence.entities import CollectionRun
from persistence.repositories import CollectionRunRepository

# ── Constants ───────────────────────────────────────────────────────────────

REPO_ID = "integ-test-repo"
RUN_ID = "integ-test-run"
COMMIT = "a" * 40

# Subset of tools to ingest for focused tests
SUBSET_TOOLS = {"layout_output", "scc_output", "lizard_output", "semgrep_output", "scancode_output"}

# LZ tables with run_pk foreign key for path consistency checks
LZ_TABLES_WITH_PATHS = [
    ("lz_layout_files", "relative_path"),
    ("lz_scc_file_metrics", "relative_path"),
    ("lz_lizard_file_metrics", "relative_path"),
    ("lz_semgrep_smells", "relative_path"),
    ("lz_scancode_file_licenses", "relative_path"),
]


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def integration_db(tmp_path: Path) -> tuple[duckdb.DuckDBPyConnection, dict[str, Path]]:
    """Set up an in-memory DB with schema and load all fixtures."""
    conn = duckdb.connect(":memory:")
    conn.execute(SCHEMA_PATH.read_text())

    # Create collection run
    cr_repo = CollectionRunRepository(conn)
    cr_repo.insert(CollectionRun(
        collection_run_id=RUN_ID,
        repo_id=REPO_ID,
        run_id=RUN_ID,
        branch="main",
        commit=COMMIT,
        started_at=datetime.now(timezone.utc),
        completed_at=None,
        status="running",
    ))

    fixture_paths = load_all_fixtures(tmp_path, REPO_ID, RUN_ID, COMMIT)
    return conn, fixture_paths


@pytest.fixture
def ingested_db(integration_db: tuple[duckdb.DuckDBPyConnection, dict[str, Path]]) -> duckdb.DuckDBPyConnection:
    """Ingest all tool fixtures into the DB."""
    conn, fixture_paths = integration_db
    ingest_outputs(
        conn=conn,
        repo_id=REPO_ID,
        collection_run_id=RUN_ID,
        run_id=RUN_ID,
        branch="main",
        commit=COMMIT,
        repo_path=Path("."),
        schema_path=SCHEMA_PATH,
        **fixture_paths,
    )
    return conn


@pytest.fixture
def subset_db(integration_db: tuple[duckdb.DuckDBPyConnection, dict[str, Path]]) -> duckdb.DuckDBPyConnection:
    """Ingest only a subset of tools (layout + scc + lizard + semgrep + scancode)."""
    conn, fixture_paths = integration_db
    subset = {k: v for k, v in fixture_paths.items() if k in SUBSET_TOOLS}
    # Fill required positional args with None for tools not in subset
    all_keys = {
        "layout_output", "scc_output", "lizard_output", "roslyn_output",
        "semgrep_output", "sonarqube_output", "trivy_output", "gitleaks_output",
        "symbol_scanner_output", "scancode_output", "pmd_cpd_output",
        "devskim_output", "dotcover_output", "git_fame_output",
        "git_sizer_output", "git_blame_scanner_output", "dependensee_output",
        "coverage_output",
    }
    kwargs = {k: subset.get(k) for k in all_keys}
    ingest_outputs(
        conn=conn,
        repo_id=REPO_ID,
        collection_run_id=RUN_ID,
        run_id=RUN_ID,
        branch="main",
        commit=COMMIT,
        repo_path=Path("."),
        schema_path=SCHEMA_PATH,
        **kwargs,
    )
    return conn


# ── Ingestion Consistency ───────────────────────────────────────────────────

class TestIngestionConsistency:
    def test_all_tools_share_collection_run(self, ingested_db: duckdb.DuckDBPyConnection) -> None:
        """All tool runs reference the same collection_run_id."""
        cids = ingested_db.execute(
            "SELECT DISTINCT collection_run_id FROM lz_tool_runs"
        ).fetchall()
        assert len(cids) == 1
        assert cids[0][0] == RUN_ID

    def test_tool_runs_has_expected_names(self, ingested_db: duckdb.DuckDBPyConnection) -> None:
        """All 18 tool names present in lz_tool_runs."""
        names = {
            row[0] for row in ingested_db.execute(
                "SELECT tool_name FROM lz_tool_runs"
            ).fetchall()
        }
        expected = {
            "layout-scanner", "scc", "lizard", "roslyn-analyzers",
            "semgrep", "sonarqube", "trivy", "gitleaks",
            "symbol-scanner", "scancode", "pmd-cpd", "devskim",
            "dotcover", "git-fame", "git-sizer", "git-blame-scanner",
            "dependensee", "coverage-ingest",
        }
        assert names == expected

    def test_lz_tables_reference_valid_run_pk(self, ingested_db: duckdb.DuckDBPyConnection) -> None:
        """Every run_pk in LZ tables exists in lz_tool_runs."""
        valid_pks = {
            row[0] for row in ingested_db.execute(
                "SELECT run_pk FROM lz_tool_runs"
            ).fetchall()
        }
        # Check a representative set of tables
        tables = [
            "lz_layout_files", "lz_scc_file_metrics",
            "lz_lizard_file_metrics", "lz_semgrep_smells",
            "lz_scancode_file_licenses", "lz_coverage_summary",
        ]
        for table in tables:
            pks = {
                row[0] for row in ingested_db.execute(
                    f"SELECT DISTINCT run_pk FROM {table}"
                ).fetchall()
            }
            assert pks.issubset(valid_pks), f"{table} has orphan run_pk: {pks - valid_pks}"


# ── Cross-Tool File Identity ───────────────────────────────────────────────

class TestCrossToolFileIdentity:
    def test_file_ids_consistent_across_tools(self, subset_db: duckdb.DuckDBPyConnection) -> None:
        """file_id values for the same relative_path are consistent across tools."""
        # Get scc file_id for a known path
        scc_rows = subset_db.execute(
            "SELECT file_id, relative_path FROM lz_scc_file_metrics ORDER BY relative_path"
        ).fetchall()
        layout_map = {}
        for row in subset_db.execute(
            "SELECT file_id, relative_path FROM lz_layout_files"
        ).fetchall():
            layout_map[row[1]] = row[0]

        for file_id, rel_path in scc_rows:
            assert rel_path in layout_map, f"scc path {rel_path} not in layout"
            assert file_id == layout_map[rel_path], (
                f"file_id mismatch for {rel_path}: scc={file_id} layout={layout_map[rel_path]}"
            )

    def test_directory_ids_consistent(self, subset_db: duckdb.DuckDBPyConnection) -> None:
        """directory_id values match between layout and scc for same files."""
        scc_dirs = subset_db.execute(
            "SELECT directory_id, relative_path FROM lz_scc_file_metrics"
        ).fetchall()
        layout_dir_map = {}
        for row in subset_db.execute(
            "SELECT directory_id, relative_path FROM lz_layout_files"
        ).fetchall():
            layout_dir_map[row[1]] = row[0]

        for dir_id, rel_path in scc_dirs:
            if rel_path in layout_dir_map:
                assert dir_id == layout_dir_map[rel_path], (
                    f"directory_id mismatch for {rel_path}"
                )

    def test_tool_file_refs_exist_in_layout(self, subset_db: duckdb.DuckDBPyConnection) -> None:
        """All file_ids in tool tables exist in lz_layout_files."""
        layout_pk = subset_db.execute(
            "SELECT run_pk FROM lz_tool_runs WHERE tool_name = 'layout-scanner'"
        ).fetchone()[0]
        layout_file_ids = {
            row[0] for row in subset_db.execute(
                "SELECT file_id FROM lz_layout_files WHERE run_pk = ?", [layout_pk]
            ).fetchall()
        }
        # Check scc
        scc_file_ids = {
            row[0] for row in subset_db.execute(
                "SELECT DISTINCT file_id FROM lz_scc_file_metrics"
            ).fetchall()
        }
        assert scc_file_ids.issubset(layout_file_ids), (
            f"scc has file_ids not in layout: {scc_file_ids - layout_file_ids}"
        )


# ── Collection Lifecycle ───────────────────────────────────────────────────

class TestCollectionLifecycle:
    def test_full_lifecycle(self, ingested_db: duckdb.DuckDBPyConnection) -> None:
        """Create → ingest → complete → verify."""
        cr_repo = CollectionRunRepository(ingested_db)
        now = datetime.now(timezone.utc)
        cr_repo.mark_status(RUN_ID, "completed", now)
        fetched = cr_repo.get_by_repo_commit(REPO_ID, COMMIT)
        assert fetched is not None
        assert fetched.status == "completed"

    def test_replace_mode(self, integration_db: tuple[duckdb.DuckDBPyConnection, dict[str, Path]], tmp_path: Path) -> None:
        """Replace mode deletes and re-ingests cleanly."""
        conn, fixture_paths = integration_db

        # First ingest
        ingest_outputs(
            conn=conn, repo_id=REPO_ID, collection_run_id=RUN_ID,
            run_id=RUN_ID, branch="main", commit=COMMIT,
            repo_path=Path("."), schema_path=SCHEMA_PATH,
            **fixture_paths,
        )
        first_count = conn.execute("SELECT COUNT(*) FROM lz_tool_runs").fetchone()[0]
        assert first_count > 0

        # Delete and re-ingest (simulate replace)
        cr_repo = CollectionRunRepository(conn)
        cr_repo.delete_collection_data(RUN_ID)
        assert conn.execute("SELECT COUNT(*) FROM lz_tool_runs").fetchone()[0] == 0

        # Re-ingest
        ingest_outputs(
            conn=conn, repo_id=REPO_ID, collection_run_id=RUN_ID,
            run_id=RUN_ID, branch="main", commit=COMMIT,
            repo_path=Path("."), schema_path=SCHEMA_PATH,
            **fixture_paths,
        )
        second_count = conn.execute("SELECT COUNT(*) FROM lz_tool_runs").fetchone()[0]
        assert second_count == first_count

    def test_collection_run_exists_after_ingest(self, ingested_db: duckdb.DuckDBPyConnection) -> None:
        """Collection run record is accessible after full ingest."""
        cr_repo = CollectionRunRepository(ingested_db)
        fetched = cr_repo.get_by_repo_commit(REPO_ID, COMMIT)
        assert fetched is not None
        assert fetched.collection_run_id == RUN_ID


# ── Path Consistency ───────────────────────────────────────────────────────

class TestPathConsistency:
    def test_no_leading_dot_slash(self, ingested_db: duckdb.DuckDBPyConnection) -> None:
        """No path starts with './' across any LZ table."""
        for table, col in LZ_TABLES_WITH_PATHS:
            rows = ingested_db.execute(
                f"SELECT {col} FROM {table} WHERE {col} LIKE './%'"
            ).fetchall()
            assert rows == [], f"{table}.{col} has paths starting with './': {rows[:3]}"

    def test_no_leading_slash(self, ingested_db: duckdb.DuckDBPyConnection) -> None:
        """No path starts with '/' across any LZ table."""
        for table, col in LZ_TABLES_WITH_PATHS:
            rows = ingested_db.execute(
                f"SELECT {col} FROM {table} WHERE {col} LIKE '/%'"
            ).fetchall()
            assert rows == [], f"{table}.{col} has absolute paths: {rows[:3]}"

    def test_paths_consistent_across_tools(self, subset_db: duckdb.DuckDBPyConnection) -> None:
        """Same file paths appear identically normalized across tools."""
        # Get paths from layout
        layout_paths = {
            row[0] for row in subset_db.execute(
                "SELECT relative_path FROM lz_layout_files"
            ).fetchall()
        }
        # Get paths from scc
        scc_paths = {
            row[0] for row in subset_db.execute(
                "SELECT relative_path FROM lz_scc_file_metrics"
            ).fetchall()
        }
        # scc paths should be a subset of layout paths
        assert scc_paths.issubset(layout_paths), (
            f"scc has paths not in layout: {scc_paths - layout_paths}"
        )
