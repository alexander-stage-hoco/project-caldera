"""Comprehensive dbt pipeline E2E tests.

Loads ALL 18 tool fixtures → ingests → runs ``dbt run`` + ``dbt test`` →
verifies every layer: landing zone, staging, marts, rollups, and insights.

All tests are marked ``@pytest.mark.slow`` and are skipped when the dbt
binary is not available.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _pipeline_helpers import (
    DBT_PROJECT_DIR,
    SCHEMA_PATH,
    find_dbt_binary,
    load_all_fixtures,
    write_dbt_profile,
)
from orchestrator import OrchestratorLogger, ingest_outputs, run_dbt
from persistence.entities import CollectionRun
from persistence.repositories import CollectionRunRepository

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
RUN_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
COMMIT = "a" * 40

EXPECTED_TOOL_NAMES = {
    "layout-scanner",
    "scc",
    "lizard",
    "roslyn-analyzers",
    "semgrep",
    "sonarqube",
    "trivy",
    "gitleaks",
    "symbol-scanner",
    "scancode",
    "pmd-cpd",
    "devskim",
    "dotcover",
    "git-fame",
    "git-sizer",
    "git-blame-scanner",
    "dependensee",
    "coverage-ingest",
}

# -- Landing-zone table → minimum expected row count -------------------------
LZ_TABLE_EXPECTED_COUNTS: list[tuple[str, int]] = [
    ("lz_layout_files", 15),
    ("lz_layout_directories", 4),
    ("lz_scc_file_metrics", 2),
    ("lz_lizard_file_metrics", 2),
    ("lz_lizard_function_metrics", 4),
    ("lz_semgrep_smells", 2),
    ("lz_sonarqube_issues", 3),
    ("lz_sonarqube_metrics", 2),
    ("lz_trivy_vulnerabilities", 4),
    ("lz_trivy_targets", 2),
    ("lz_trivy_iac_misconfigs", 2),
    ("lz_gitleaks_secrets", 2),
    ("lz_roslyn_violations", 3),
    ("lz_code_symbols", 5),
    ("lz_symbol_calls", 5),
    ("lz_file_imports", 4),
    ("lz_scancode_file_licenses", 2),
    ("lz_scancode_summary", 1),
    ("lz_pmd_cpd_file_metrics", 3),
    ("lz_pmd_cpd_duplications", 2),
    ("lz_pmd_cpd_occurrences", 4),
    ("lz_dotcover_assembly_coverage", 2),
    ("lz_dotcover_type_coverage", 3),
    ("lz_dotcover_method_coverage", 5),
    ("lz_git_fame_authors", 2),
    ("lz_git_fame_summary", 1),
    ("lz_git_sizer_metrics", 1),
    ("lz_git_sizer_violations", 1),
    ("lz_git_sizer_lfs_candidates", 1),
    ("lz_git_blame_summary", 3),
    ("lz_git_blame_author_stats", 2),
    ("lz_dependensee_projects", 2),
    ("lz_dependensee_project_refs", 1),
    ("lz_dependensee_package_refs", 3),
    ("lz_coverage_summary", 2),
]

# -- Staging views expected to be non-empty ----------------------------------
STAGING_VIEWS_NON_EMPTY: list[str] = [
    # Direct LZ staging
    "stg_lz_layout_files",
    "stg_lz_layout_directories",
    "stg_lz_scc_file_metrics",
    "stg_lz_lizard_file_metrics",
    "stg_lz_lizard_function_metrics",
    "stg_lz_semgrep_smells",
    "stg_lz_gitleaks_secrets",
    "stg_lz_roslyn_violations",
    "stg_lz_devskim_findings",
    "stg_lz_scancode_file_licenses",
    "stg_lz_scancode_summary",
    "stg_lz_pmd_cpd_file_metrics",
    "stg_lz_pmd_cpd_duplications",
    "stg_lz_pmd_cpd_occurrences",
    "stg_lz_dotcover_assembly_coverage",
    "stg_lz_dotcover_type_coverage",
    "stg_lz_dotcover_method_coverage",
    "stg_lz_git_fame_authors",
    "stg_lz_git_fame_summary",
    "stg_lz_git_sizer_metrics",
    "stg_lz_git_sizer_violations",
    "stg_lz_git_sizer_lfs_candidates",
    "stg_lz_code_symbols",
    "stg_lz_symbol_calls",
    "stg_lz_file_imports",
    "stg_lz_tool_runs",
    "stg_lz_coverage_summary",
    # Derived staging (aggregated per file / per tool)
    "stg_semgrep_file_metrics",
    "stg_roslyn_file_metrics",
    "stg_devskim_file_metrics",
    "stg_sonarqube_file_metrics",
    "stg_sonarqube_issues",
    "stg_symbols_file_metrics",
    "stg_file_imports_file_metrics",
    "stg_symbol_calls_file_metrics",
    "stg_trivy_file_metrics",
    "stg_trivy_targets",
    "stg_trivy_target_metrics",
    "stg_trivy_iac_misconfigs",
    "stg_gitleaks_secrets",
    "stg_scancode_file_metrics",
    "stg_git_blame_summary",
    "stg_git_blame_author_stats",
    # Dependensee (derived staging)
    "stg_dependensee_projects",
    "stg_dependensee_project_refs",
    "stg_dependensee_package_refs",
    # Trivy vulnerabilities (derived staging)
    "stg_trivy_vulnerabilities",
    # Symbol coupling (derived staging)
    "stg_symbol_coupling_metrics",
]

# -- Mart tables expected to be non-empty ------------------------------------
MART_TABLES_NON_EMPTY: list[str] = [
    "unified_file_metrics",
    "unified_run_summary",
    "repo_health_summary",
    "mart_scc_size_hotspots",
    "mart_semgrep_rule_hotspots",
    "mart_roslyn_rule_hotspots",
    "mart_devskim_rule_hotspots",
    "mart_sonarqube_rule_hotspots",
    "mart_trivy_vulnerability_hotspots",
    "mart_trivy_iac_misconfig_hotspots",
    "mart_gitleaks_secret_hotspots",
    "mart_scancode_license_hotspots",
    "mart_pmd_cpd_clone_hotspots",
    "mart_git_fame_contributor_hotspots",
    "mart_git_sizer_violation_hotspots",
    "mart_git_blame_knowledge_risk",
    "mart_layout_structure_hotspots",
    "unified_repo_metrics",
    "mart_author_contributions",
    "mart_authorship_risk",
    "mart_authorship_summary",
    "mart_dependency_health_summary",
    "mart_project_blast_radius",
    "mart_coverage_gap_analysis",
    "mart_blast_radius_symbol",
]

# -- Rollup tables expected to be non-empty ----------------------------------
ROLLUP_TABLES_NON_EMPTY: list[str] = [
    "rollup_scc_directory_counts_direct",
    "rollup_scc_directory_counts_recursive",
    "rollup_scc_directory_direct_distributions",
    "rollup_scc_directory_recursive_distributions",
    "rollup_lizard_directory_counts_direct",
    "rollup_lizard_directory_counts_recursive",
    "rollup_lizard_directory_direct_distributions",
    "rollup_lizard_directory_recursive_distributions",
    "rollup_layout_directory_counts_direct",
    "rollup_layout_directory_counts_recursive",
    "rollup_semgrep_directory_counts_direct",
    "rollup_semgrep_directory_counts_recursive",
    "rollup_roslyn_directory_counts_direct",
    "rollup_roslyn_directory_counts_recursive",
    "rollup_devskim_directory_counts_direct",
    "rollup_devskim_directory_counts_recursive",
    "rollup_gitleaks_directory_counts_direct",
    "rollup_gitleaks_directory_counts_recursive",
    "rollup_sonarqube_directory_counts_direct",
    "rollup_sonarqube_directory_counts_recursive",
    "rollup_pmd_cpd_directory_counts_direct",
    "rollup_pmd_cpd_directory_counts_recursive",
    "rollup_scancode_directory_counts_direct",
    "rollup_scancode_directory_counts_recursive",
    "rollup_symbols_directory_counts_direct",
    "rollup_symbols_directory_counts_recursive",
    "rollup_symbol_calls_directory_counts_direct",
    "rollup_symbol_calls_directory_counts_recursive",
    "rollup_file_imports_directory_counts_direct",
    "rollup_file_imports_directory_counts_recursive",
    "rollup_trivy_directory_counts_direct",
    "rollup_trivy_directory_counts_recursive",
    # -- Distribution rollups (matching existing count rollups) --
    "rollup_semgrep_directory_direct_distributions",
    "rollup_semgrep_directory_recursive_distributions",
    "rollup_sonarqube_directory_direct_distributions",
    "rollup_sonarqube_directory_recursive_distributions",
    "rollup_gitleaks_directory_direct_distributions",
    "rollup_gitleaks_directory_recursive_distributions",
    "rollup_trivy_directory_direct_distributions",
    "rollup_trivy_directory_recursive_distributions",
    "rollup_symbols_directory_direct_distributions",
    "rollup_symbols_directory_recursive_distributions",
    "rollup_symbol_calls_directory_direct_distributions",
    "rollup_symbol_calls_directory_recursive_distributions",
    "rollup_file_imports_directory_direct_distributions",
    "rollup_file_imports_directory_recursive_distributions",
    "rollup_pmd_cpd_directory_direct_distributions",
    "rollup_pmd_cpd_directory_recursive_distributions",
    "rollup_devskim_directory_direct_distributions",
    "rollup_devskim_directory_recursive_distributions",
    "rollup_scancode_directory_direct_distributions",
    "rollup_scancode_directory_recursive_distributions",
]

# -- Distribution rollup pairs for invariant checking ------------------------
DISTRIBUTION_ROLLUP_PAIRS: list[tuple[str, str]] = [
    (
        "rollup_scc_directory_direct_distributions",
        "rollup_scc_directory_recursive_distributions",
    ),
    (
        "rollup_lizard_directory_direct_distributions",
        "rollup_lizard_directory_recursive_distributions",
    ),
    (
        "rollup_semgrep_directory_direct_distributions",
        "rollup_semgrep_directory_recursive_distributions",
    ),
    (
        "rollup_sonarqube_directory_direct_distributions",
        "rollup_sonarqube_directory_recursive_distributions",
    ),
    (
        "rollup_gitleaks_directory_direct_distributions",
        "rollup_gitleaks_directory_recursive_distributions",
    ),
    (
        "rollup_trivy_directory_direct_distributions",
        "rollup_trivy_directory_recursive_distributions",
    ),
    (
        "rollup_symbols_directory_direct_distributions",
        "rollup_symbols_directory_recursive_distributions",
    ),
    (
        "rollup_symbol_calls_directory_direct_distributions",
        "rollup_symbol_calls_directory_recursive_distributions",
    ),
    (
        "rollup_file_imports_directory_direct_distributions",
        "rollup_file_imports_directory_recursive_distributions",
    ),
    (
        "rollup_pmd_cpd_directory_direct_distributions",
        "rollup_pmd_cpd_directory_recursive_distributions",
    ),
    (
        "rollup_devskim_directory_direct_distributions",
        "rollup_devskim_directory_recursive_distributions",
    ),
    (
        "rollup_scancode_directory_direct_distributions",
        "rollup_scancode_directory_recursive_distributions",
    ),
]

# -- Count rollup pairs for recursive >= direct invariant -------------------
COUNT_ROLLUP_PAIRS: list[tuple[str, str, str]] = [
    ("rollup_scc_directory_counts_direct", "rollup_scc_directory_counts_recursive", "file_count"),
    ("rollup_lizard_directory_counts_direct", "rollup_lizard_directory_counts_recursive", "file_count"),
    ("rollup_layout_directory_counts_direct", "rollup_layout_directory_counts_recursive", "file_count"),
    ("rollup_semgrep_directory_counts_direct", "rollup_semgrep_directory_counts_recursive", "file_count"),
    ("rollup_roslyn_directory_counts_direct", "rollup_roslyn_directory_counts_recursive", "file_count"),
    ("rollup_devskim_directory_counts_direct", "rollup_devskim_directory_counts_recursive", "file_count"),
    ("rollup_gitleaks_directory_counts_direct", "rollup_gitleaks_directory_counts_recursive", "file_count"),
    ("rollup_sonarqube_directory_counts_direct", "rollup_sonarqube_directory_counts_recursive", "file_count"),
    ("rollup_pmd_cpd_directory_counts_direct", "rollup_pmd_cpd_directory_counts_recursive", "file_count"),
    ("rollup_scancode_directory_counts_direct", "rollup_scancode_directory_counts_recursive", "file_count"),
    ("rollup_symbols_directory_counts_direct", "rollup_symbols_directory_counts_recursive", "file_count"),
    ("rollup_symbol_calls_directory_counts_direct", "rollup_symbol_calls_directory_counts_recursive", "file_count"),
    ("rollup_file_imports_directory_counts_direct", "rollup_file_imports_directory_counts_recursive", "file_count"),
    ("rollup_trivy_directory_counts_direct", "rollup_trivy_directory_counts_recursive", "target_count"),
]

# -- Data quality: non-negative columns ------------------------------------
NON_NEGATIVE_COLUMNS: list[tuple[str, str]] = [
    ("unified_file_metrics", "loc_total"),
    ("unified_file_metrics", "loc_code"),
    ("unified_file_metrics", "loc_comment"),
    ("unified_file_metrics", "loc_blank"),
]

# -- Data quality: required NOT NULL columns --------------------------------
REQUIRED_NOT_NULL: list[tuple[str, str]] = [
    ("lz_tool_runs", "run_pk"),
    ("lz_tool_runs", "tool_name"),
    ("lz_tool_runs", "collection_run_id"),
    ("lz_layout_files", "file_id"),
    ("lz_layout_files", "relative_path"),
    ("unified_file_metrics", "file_id"),
    ("unified_file_metrics", "relative_path"),
]

# -- Data quality: percentage range (0-100) columns ------------------------
PERCENTAGE_COLUMNS: list[tuple[str, str]] = [
    ("lz_coverage_summary", "line_coverage_pct"),
    ("lz_dotcover_assembly_coverage", "statement_coverage_pct"),
    ("lz_dotcover_type_coverage", "statement_coverage_pct"),
    ("lz_dotcover_method_coverage", "statement_coverage_pct"),
]


# ============================================================================
# Session-scoped fixture: ingest + dbt (runs once)
# ============================================================================
@pytest.fixture(scope="session")
def pipeline_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Ingest all 18 tool fixtures and run dbt.  Returns the DuckDB path."""
    dbt_bin = find_dbt_binary()
    if dbt_bin is None:
        pytest.skip("dbt binary not available")

    base = tmp_path_factory.mktemp("pipeline_e2e")

    # Minimal repo tree (adapters may resolve paths against it)
    repo_root = base / "repo"
    (repo_root / "src" / "utils").mkdir(parents=True)
    (repo_root / "src" / "app.py").write_text("print('hi')\n")
    (repo_root / "src" / "utils" / "helpers.py").write_text("def helper(): pass\n")

    # Database setup
    db_path = base / "caldera_sot.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute(SCHEMA_PATH.read_text())

    CollectionRunRepository(conn).insert(
        CollectionRun(
            collection_run_id=RUN_ID,
            repo_id=REPO_ID,
            run_id=RUN_ID,
            branch="main",
            commit=COMMIT,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            status="running",
        )
    )

    # Load & ingest all 18 fixtures
    fixture_paths = load_all_fixtures(base, REPO_ID, RUN_ID, COMMIT)
    ingest_outputs(
        conn,
        repo_id=REPO_ID,
        collection_run_id=RUN_ID,
        run_id=RUN_ID,
        branch="main",
        commit=COMMIT,
        repo_path=repo_root,
        schema_path=SCHEMA_PATH,
        **fixture_paths,
    )
    conn.close()

    # dbt run + dbt test
    profiles_dir = write_dbt_profile(base, db_path)
    logger = OrchestratorLogger(base / "dbt.log")
    try:
        run_dbt(
            dbt_bin=dbt_bin,
            dbt_project_dir=DBT_PROJECT_DIR,
            profiles_dir=profiles_dir,
            logger=logger,
            target_path=str(base / "dbt_target"),
            log_path=str(base / "dbt_logs"),
        )
    finally:
        logger.close()

    return db_path


@pytest.fixture()
def db(pipeline_db: Path) -> duckdb.DuckDBPyConnection:
    """Per-test read-only connection reusing the session database."""
    conn = duckdb.connect(str(pipeline_db), read_only=True)
    yield conn
    conn.close()


# ============================================================================
# 1. Landing Zone Ingestion
# ============================================================================
@pytest.mark.slow
class TestLZIngestion:
    """Verify all 18 tools ingested into landing zone tables."""

    @pytest.mark.parametrize(
        "table,expected_min",
        LZ_TABLE_EXPECTED_COUNTS,
        ids=[t for t, _ in LZ_TABLE_EXPECTED_COUNTS],
    )
    def test_lz_table_row_count(
        self,
        db: duckdb.DuckDBPyConnection,
        table: str,
        expected_min: int,
    ) -> None:
        actual = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert actual >= expected_min, (
            f"{table}: expected >= {expected_min}, got {actual}"
        )

    def test_all_18_tools_in_tool_runs(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        rows = db.execute(
            "SELECT DISTINCT tool_name FROM lz_tool_runs"
        ).fetchall()
        tool_names = {r[0] for r in rows}
        assert tool_names == EXPECTED_TOOL_NAMES

    def test_collection_run_exists(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        row = db.execute(
            "SELECT repo_id, run_id FROM lz_collection_runs "
            "WHERE collection_run_id = ?",
            [RUN_ID],
        ).fetchone()
        assert row is not None
        assert row[0] == REPO_ID
        assert row[1] == RUN_ID

    def test_tool_runs_reference_collection(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        orphans = db.execute(
            """
            SELECT COUNT(*) FROM lz_tool_runs tr
            WHERE NOT EXISTS (
                SELECT 1 FROM lz_collection_runs cr
                WHERE cr.collection_run_id = tr.collection_run_id
            )
            """
        ).fetchone()[0]
        assert orphans == 0


# ============================================================================
# 2. Staging Views
# ============================================================================
@pytest.mark.slow
class TestStagingViews:
    """Verify dbt staging views are populated."""

    @pytest.mark.parametrize("view", STAGING_VIEWS_NON_EMPTY)
    def test_staging_view_non_empty(
        self, db: duckdb.DuckDBPyConnection, view: str
    ) -> None:
        count = db.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
        assert count > 0, f"{view} should have rows"


# ============================================================================
# 3. Unified / Summary Marts
# ============================================================================
@pytest.mark.slow
class TestUnifiedMarts:
    """Verify unified and summary mart tables."""

    def test_unified_file_metrics_has_rows(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        count = db.execute(
            "SELECT COUNT(*) FROM unified_file_metrics"
        ).fetchone()[0]
        assert count > 0

    def test_unified_file_metrics_no_negative_loc(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        bad = db.execute(
            "SELECT COUNT(*) FROM unified_file_metrics WHERE loc_total < 0"
        ).fetchone()[0]
        assert bad == 0, "loc_total should never be negative"

    def test_unified_file_metrics_valid_run_pk(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        orphans = db.execute(
            """
            SELECT COUNT(*) FROM unified_file_metrics ufm
            WHERE NOT EXISTS (
                SELECT 1 FROM lz_tool_runs tr WHERE tr.run_pk = ufm.run_pk
            )
            """
        ).fetchone()[0]
        assert orphans == 0

    def test_unified_file_metrics_valid_file_ids(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        orphans = db.execute(
            """
            SELECT COUNT(*) FROM unified_file_metrics ufm
            LEFT JOIN lz_layout_files lf
                ON lf.run_pk = ufm.layout_run_pk AND lf.file_id = ufm.file_id
            WHERE lf.file_id IS NULL
            """
        ).fetchone()[0]
        assert orphans == 0

    def test_unified_run_summary_has_data(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        count = db.execute(
            "SELECT COUNT(*) FROM unified_run_summary"
        ).fetchone()[0]
        assert count > 0, "unified_run_summary should have rows"

    def test_all_18_tools_in_stg_tool_runs(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        rows = db.execute(
            "SELECT DISTINCT tool_name FROM stg_lz_tool_runs"
        ).fetchall()
        tool_names = {r[0] for r in rows}
        assert tool_names == EXPECTED_TOOL_NAMES

    def test_repo_health_summary_has_data(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        count = db.execute(
            "SELECT COUNT(*) FROM repo_health_summary"
        ).fetchone()[0]
        assert count > 0


# ============================================================================
# 4. Rollup Tables
# ============================================================================
@pytest.mark.slow
class TestRollupTables:
    """Verify rollup tables are populated and invariants hold."""

    @pytest.mark.parametrize("table", ROLLUP_TABLES_NON_EMPTY)
    def test_rollup_table_non_empty(
        self, db: duckdb.DuckDBPyConnection, table: str
    ) -> None:
        count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert count > 0, f"{table} should have rows"

    @pytest.mark.parametrize(
        "direct_table,recursive_table",
        DISTRIBUTION_ROLLUP_PAIRS,
        ids=[
            p[0].split("_directory_")[0].replace("rollup_", "")
            for p in DISTRIBUTION_ROLLUP_PAIRS
        ],
    )
    def test_distribution_rollup_invariant(
        self,
        db: duckdb.DuckDBPyConnection,
        direct_table: str,
        recursive_table: str,
    ) -> None:
        """recursive value_count >= direct value_count for every
        (directory_path, metric) pair."""
        violations = db.execute(
            f"""
            SELECT r.directory_path, r.metric,
                   r.value_count AS rec, d.value_count AS dir
            FROM {recursive_table} r
            JOIN {direct_table} d
              ON d.directory_path = r.directory_path
             AND d.metric = r.metric
             AND d.run_pk = r.run_pk
            WHERE r.value_count < d.value_count
            """
        ).fetchall()
        assert len(violations) == 0, (
            f"Invariant violated (recursive < direct): {violations}"
        )

    @pytest.mark.parametrize(
        "direct_table,recursive_table,count_col",
        COUNT_ROLLUP_PAIRS,
        ids=[
            p[0].split("_directory_")[0].replace("rollup_", "")
            for p in COUNT_ROLLUP_PAIRS
        ],
    )
    def test_count_rollup_invariant(
        self,
        db: duckdb.DuckDBPyConnection,
        direct_table: str,
        recursive_table: str,
        count_col: str,
    ) -> None:
        """recursive count >= direct count for every directory_path."""
        violations = db.execute(
            f"""
            SELECT r.directory_path, r.{count_col} AS rec, d.{count_col} AS dir
            FROM {recursive_table} r
            JOIN {direct_table} d
              ON d.directory_path = r.directory_path
             AND d.run_pk = r.run_pk
            WHERE r.{count_col} < d.{count_col}
            """
        ).fetchall()
        assert len(violations) == 0, (
            f"Invariant violated (recursive < direct): {violations}"
        )

    def test_scc_src_recursive_gt_direct(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        """src/ directory has files in a subdirectory, so its recursive
        count must exceed its direct count for SCC lines_total."""
        rec = db.execute(
            """
            SELECT value_count
            FROM rollup_scc_directory_recursive_distributions
            WHERE directory_path = 'src' AND metric = 'lines_total'
            """
        ).fetchone()
        direct = db.execute(
            """
            SELECT value_count
            FROM rollup_scc_directory_direct_distributions
            WHERE directory_path = 'src' AND metric = 'lines_total'
            """
        ).fetchone()
        assert rec is not None and direct is not None
        assert rec[0] > direct[0]


# ============================================================================
# 5. Mart Tables
# ============================================================================
@pytest.mark.slow
class TestMartTables:
    """Verify mart tables are populated."""

    @pytest.mark.parametrize("table", MART_TABLES_NON_EMPTY)
    def test_mart_table_non_empty(
        self, db: duckdb.DuckDBPyConnection, table: str
    ) -> None:
        count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert count > 0, f"{table} should have rows"


# ============================================================================
# 6. Cross-Tool Referential Integrity
# ============================================================================
@pytest.mark.slow
class TestCrossToolIntegrity:
    """Verify cross-tool referential integrity."""

    @pytest.mark.parametrize(
        "tool_table,id_col",
        [
            ("lz_scc_file_metrics", "file_id"),
            ("lz_lizard_file_metrics", "file_id"),
            ("lz_semgrep_smells", "file_id"),
            ("lz_roslyn_violations", "file_id"),
            ("lz_devskim_findings", "file_id"),
            ("lz_code_symbols", "file_id"),
            ("lz_scancode_file_licenses", "file_id"),
            ("lz_pmd_cpd_file_metrics", "file_id"),
            ("lz_git_blame_summary", "file_id"),
            ("lz_coverage_summary", "file_id"),
            ("lz_sonarqube_issues", "file_id"),
            ("lz_sonarqube_metrics", "file_id"),
            ("lz_trivy_iac_misconfigs", "file_id"),
            ("lz_lizard_function_metrics", "file_id"),
            ("lz_file_imports", "file_id"),
        ],
        ids=lambda x: x if isinstance(x, str) and x.startswith("lz_") else "",
    )
    def test_file_ids_match_layout(
        self,
        db: duckdb.DuckDBPyConnection,
        tool_table: str,
        id_col: str,
    ) -> None:
        """Every file_id in a tool table must exist in lz_layout_files."""
        orphans = db.execute(
            f"""
            SELECT COUNT(*) FROM {tool_table} t
            JOIN lz_tool_runs tr ON tr.run_pk = t.run_pk
            JOIN lz_tool_runs tr_layout
              ON tr_layout.collection_run_id = tr.collection_run_id
             AND tr_layout.tool_name IN ('layout', 'layout-scanner')
            WHERE NOT EXISTS (
                SELECT 1 FROM lz_layout_files lf
                WHERE lf.run_pk = tr_layout.run_pk
                  AND lf.file_id = t.{id_col}
            )
            """
        ).fetchone()[0]
        assert orphans == 0, (
            f"{tool_table}.{id_col} has {orphans} orphan reference(s)"
        )

    @pytest.mark.parametrize(
        "table",
        [t for t, _ in LZ_TABLE_EXPECTED_COUNTS],
        ids=[t for t, _ in LZ_TABLE_EXPECTED_COUNTS],
    )
    def test_run_pk_references_tool_runs(
        self, db: duckdb.DuckDBPyConnection, table: str
    ) -> None:
        """Every run_pk in an LZ table must exist in lz_tool_runs."""
        orphans = db.execute(
            f"""
            SELECT COUNT(*) FROM {table} t
            WHERE NOT EXISTS (
                SELECT 1 FROM lz_tool_runs tr WHERE tr.run_pk = t.run_pk
            )
            """
        ).fetchone()[0]
        assert orphans == 0, (
            f"{table} has {orphans} orphan run_pk reference(s)"
        )

    def test_symbol_calls_file_ids_match_layout(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        """Both caller_file_id and callee_file_id must exist in layout."""
        for col in ("caller_file_id", "callee_file_id"):
            orphans = db.execute(
                f"""
                SELECT COUNT(*) FROM lz_symbol_calls t
                JOIN lz_tool_runs tr ON tr.run_pk = t.run_pk
                JOIN lz_tool_runs tr_layout
                  ON tr_layout.collection_run_id = tr.collection_run_id
                 AND tr_layout.tool_name IN ('layout', 'layout-scanner')
                WHERE t.{col} IS NOT NULL AND NOT EXISTS (
                    SELECT 1 FROM lz_layout_files lf
                    WHERE lf.run_pk = tr_layout.run_pk
                      AND lf.file_id = t.{col}
                )
                """
            ).fetchone()[0]
            assert orphans == 0, (
                f"lz_symbol_calls.{col} has {orphans} orphan reference(s)"
            )


# ============================================================================
# 7. Insights Integration
# ============================================================================
@pytest.mark.slow
class TestInsightsIntegration:
    """Verify insights reports generate from real dbt-populated data."""

    @pytest.fixture(autouse=True)
    def _setup_insights(self, pipeline_db: Path) -> None:
        try:
            from insights.generator import InsightsGenerator
        except ImportError:
            pytest.skip("insights module not available")
        self.generator = InsightsGenerator(
            db_path=pipeline_db,
            dbt_project_dir=DBT_PROJECT_DIR,
        )

    def _scc_run_pk(self, db: duckdb.DuckDBPyConnection) -> int:
        return db.execute(
            "SELECT run_pk FROM lz_tool_runs WHERE tool_name = 'scc'"
        ).fetchone()[0]

    def test_validate_database(self) -> None:
        result = self.generator.validate_database()
        assert isinstance(result, dict)

    def test_generate_html_report(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        html = self.generator.generate(
            run_pk=self._scc_run_pk(db), format="html"
        )
        assert len(html) > 0, "HTML report should be non-empty"

    def test_generate_md_report(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        md = self.generator.generate(
            run_pk=self._scc_run_pk(db), format="md"
        )
        assert len(md) > 0, "Markdown report should be non-empty"

    def test_generate_all_sections_no_exceptions(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        """Each of the 37 sections should render without raising."""
        run_pk = self._scc_run_pk(db)
        sections = self.generator.list_sections()
        assert len(sections) >= 37, (
            f"Expected >= 37 sections, got {len(sections)}"
        )
        for info in sections:
            name = info["name"]
            result = self.generator.generate_section(
                section_name=name, run_pk=run_pk, format="md"
            )
            assert isinstance(result, str), (
                f"Section {name} should return a string"
            )

    def test_generate_by_collection(self) -> None:
        report = self.generator.generate_by_collection(
            collection_run_id=RUN_ID, format="md"
        )
        assert len(report) > 0, "Collection-based report should be non-empty"

    def test_validate_report_data(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        warnings = self.generator.validate_report_data(
            run_pk=self._scc_run_pk(db)
        )
        assert isinstance(warnings, list)

    def test_html_report_has_section_structure(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        html = self.generator.generate(
            run_pk=self._scc_run_pk(db), format="html"
        )
        assert "<section" in html or "<h2" in html

    def test_sections_produce_meaningful_content(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        run_pk = self._scc_run_pk(db)
        for info in self.generator.list_sections():
            content = self.generator.generate_section(
                section_name=info["name"], run_pk=run_pk, format="md"
            )
            assert len(content) > 20, (
                f"Section {info['name']} appears empty ({len(content)} chars)"
            )


# ============================================================================
# 8. Data Quality Invariants
# ============================================================================
@pytest.mark.slow
class TestDataQualityInvariants:
    """Verify data quality constraints: non-negatives, NOT NULLs, ranges."""

    @pytest.mark.parametrize(
        "table,column",
        NON_NEGATIVE_COLUMNS,
        ids=[f"{t}.{c}" for t, c in NON_NEGATIVE_COLUMNS],
    )
    def test_non_negative_values(
        self, db: duckdb.DuckDBPyConnection, table: str, column: str
    ) -> None:
        bad = db.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {column} IS NOT NULL AND {column} < 0"
        ).fetchone()[0]
        assert bad == 0, f"{table}.{column} has {bad} negative value(s)"

    @pytest.mark.parametrize(
        "table,column",
        REQUIRED_NOT_NULL,
        ids=[f"{t}.{c}" for t, c in REQUIRED_NOT_NULL],
    )
    def test_required_not_null(
        self, db: duckdb.DuckDBPyConnection, table: str, column: str
    ) -> None:
        nulls = db.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL"
        ).fetchone()[0]
        assert nulls == 0, f"{table}.{column} has {nulls} NULL value(s)"

    @pytest.mark.parametrize(
        "table,column",
        PERCENTAGE_COLUMNS,
        ids=[f"{t}.{c}" for t, c in PERCENTAGE_COLUMNS],
    )
    def test_percentage_in_range(
        self, db: duckdb.DuckDBPyConnection, table: str, column: str
    ) -> None:
        bad = db.execute(
            f"""
            SELECT COUNT(*) FROM {table}
            WHERE {column} IS NOT NULL AND ({column} < 0 OR {column} > 100)
            """
        ).fetchone()[0]
        assert bad == 0, (
            f"{table}.{column} has {bad} value(s) outside 0-100 range"
        )


# ============================================================================
# 9. Mart Content Validation
# ============================================================================
@pytest.mark.slow
class TestMartContentValidation:
    """Selective content validation for unified marts."""

    def test_unified_file_metrics_has_scc_data(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        """At least some files should have SCC metric data."""
        count = db.execute(
            "SELECT COUNT(*) FROM unified_file_metrics WHERE scc_run_pk IS NOT NULL"
        ).fetchone()[0]
        assert count > 0

    def test_unified_file_metrics_loc_consistency(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        """loc_total >= loc_code where both exist."""
        bad = db.execute(
            """
            SELECT COUNT(*) FROM unified_file_metrics
            WHERE loc_code IS NOT NULL AND loc_total IS NOT NULL
              AND loc_total < loc_code
            """
        ).fetchone()[0]
        assert bad == 0, f"{bad} row(s) where loc_total < loc_code"
