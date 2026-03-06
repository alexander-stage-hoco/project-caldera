"""End-to-end tests for the evidence system with synthetic DuckDB data.

Bypasses dbt by inserting synthetic data directly into the tables that
evidence queries read from. Runs in ~seconds, not minutes.

Profiles tested:
- **default**: standard thresholds (complexity>=15, coverage<50 & CCN>15, density>=20, LOC>=500)
- **conservative**: higher thresholds (complexity>=25, coverage<30 & CCN>25, density>=40)
- **pe_due_diligence**: lower thresholds (complexity>=10, coverage<70 & CCN>10, density>=10)
"""

from __future__ import annotations

import json
import uuid

import duckdb
import pytest

from insights.config.loader import ConfigLoader
from insights.data_fetcher import DataFetcher
from insights.evidence.builder import EvidenceRegistryBuilder
from insights.evidence.collector import EvidenceCollector
from insights.evidence.entities import (
    EvidenceRegistry,
    ParameterSet,
)
from insights.evidence.reviewer import EvidenceReviewer

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COLLECTION_RUN_ID = "e2e-synth-" + uuid.uuid4().hex[:12]
REPO_ID = "synth-repo"
COMMIT_SHA = "a" * 40

# Tool run_pk assignments (deterministic)
SCC_RUN_PK = 1000
LIZARD_RUN_PK = 1001
TRIVY_RUN_PK = 1002
GITLEAKS_RUN_PK = 1003
SYMBOL_RUN_PK = 1004
BLAME_RUN_PK = 1005
SEMGREP_RUN_PK = 1006
LAYOUT_RUN_PK = 1007
PMD_CPD_RUN_PK = 1008
COVERAGE_RUN_PK = 1009


# ---------------------------------------------------------------------------
# Synthetic data per category (used in assertions)
# ---------------------------------------------------------------------------

# Complexity CCN values: engine=25, database=18, validators=16, routes=12, serializers=10
# Coverage values:       engine=20%, validators=30%, routes=60%
# Ownership:             engine(1 author,800L,critical), validators(1 author,700L,critical), database(2 authors,600L,high)
# Quality density:       helpers=40 smells/KLOC (6/150)
# Maintainability LOC:   routes=1200, engine=800, validators=700, database=600

# Expected items per profile per category (from diagnostic run):
#   category         default  conservative  pe_due_diligence
#   complexity       3        1             5
#   security         3        3             3
#   coupling         2        2             2
#   coverage         2        0             3
#   ownership        3        3             3
#   quality          1        1             1
#   maintainability  4        4             4
#   architecture     1        1             1
#   dependencies     2        2             2
#   duplication      1        1             1
#   TOTAL           22       18            25

# Expected claims per profile:
#   default(8):          1 HighCoupling, 2 KnowledgeSilo, 2 CoverageGap, 2 SecurityExposure, 1 PervasiveDebt
#   conservative(4):     1 HighCoupling, 2 SecurityExposure, 1 PervasiveDebt
#   pe_due_diligence(8): 1 HighCoupling, 2 KnowledgeSilo, 2 CoverageGap, 2 SecurityExposure, 1 PervasiveDebt

# Expected risks per profile:
#   default(2):          Security exposure(critical), Knowledge concentration(high)
#   conservative(1):     Security exposure(critical)
#   pe_due_diligence(2): Security exposure(critical), Knowledge concentration(high)


# ---------------------------------------------------------------------------
# Fixture: synthetic DuckDB database
# ---------------------------------------------------------------------------


def _create_tool_runs(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE lz_tool_runs (
            run_pk BIGINT PRIMARY KEY,
            collection_run_id VARCHAR NOT NULL,
            tool_name VARCHAR NOT NULL,
            repo_id VARCHAR,
            commit_sha VARCHAR,
            status VARCHAR DEFAULT 'completed',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    tools = [
        (SCC_RUN_PK, "scc"),
        (LIZARD_RUN_PK, "lizard"),
        (TRIVY_RUN_PK, "trivy"),
        (GITLEAKS_RUN_PK, "gitleaks"),
        (SYMBOL_RUN_PK, "symbol-scanner"),
        (BLAME_RUN_PK, "git-blame-scanner"),
        (SEMGREP_RUN_PK, "semgrep"),
        (LAYOUT_RUN_PK, "layout-scanner"),
        (PMD_CPD_RUN_PK, "pmd-cpd"),
        (COVERAGE_RUN_PK, "coverage-ingest"),
    ]
    conn.executemany(
        "INSERT INTO lz_tool_runs VALUES (?, ?, ?, ?, ?, 'completed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
        [(pk, COLLECTION_RUN_ID, name, REPO_ID, COMMIT_SHA) for pk, name in tools],
    )


def _create_unified_file_metrics(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE unified_file_metrics (
            run_pk BIGINT NOT NULL,
            relative_path VARCHAR NOT NULL,
            language VARCHAR,
            loc_total INTEGER DEFAULT 0,
            complexity_max INTEGER DEFAULT 0,
            complexity_total_ccn INTEGER DEFAULT 0,
            function_count INTEGER DEFAULT 0,
            coverage_line_pct DOUBLE,
            coverage_branch_pct DOUBLE,
            semgrep_smell_count INTEGER DEFAULT 0,
            devskim_issue_count INTEGER DEFAULT 0,
            sonarqube_issue_count INTEGER DEFAULT 0
        )
    """)
    rows = [
        # (run_pk, path, lang, loc, ccn_max, ccn_total, funcs, cov_line, cov_branch, smells, devskim, sonar)
        (SCC_RUN_PK, "src/core/engine.py", "Python", 800, 25, 80, 12, 20.0, 15.0, 2, 0, 0),
        (SCC_RUN_PK, "src/core/database.py", "Python", 600, 18, 55, 8, None, None, 1, 1, 0),
        (SCC_RUN_PK, "src/core/config.py", "Python", 200, 5, 10, 4, 90.0, 85.0, 0, 0, 0),
        (SCC_RUN_PK, "src/api/routes.py", "Python", 1200, 12, 40, 15, 60.0, 50.0, 3, 0, 0),
        (SCC_RUN_PK, "src/api/middleware.py", "Python", 300, 8, 20, 5, 70.0, 60.0, 0, 0, 0),
        (SCC_RUN_PK, "src/api/serializers.py", "Python", 400, 10, 25, 6, 55.0, 40.0, 1, 0, 0),
        (SCC_RUN_PK, "src/utils/helpers.py", "Python", 150, 3, 6, 3, 80.0, 70.0, 6, 2, 0),
        (SCC_RUN_PK, "src/utils/validators.py", "Python", 700, 16, 48, 10, 30.0, 25.0, 0, 0, 0),
        (SCC_RUN_PK, "src/utils/formatters.py", "Python", 250, 4, 8, 5, 75.0, 65.0, 0, 0, 0),
        (SCC_RUN_PK, "tests/test_engine.py", "Python", 300, 2, 4, 10, None, None, 0, 0, 0),
        (SCC_RUN_PK, "tests/test_routes.py", "Python", 200, 1, 2, 8, None, None, 0, 0, 0),
        (SCC_RUN_PK, "docs/README.md", "Markdown", 100, 0, 0, 0, None, None, 0, 0, 0),
    ]
    conn.executemany(
        "INSERT INTO unified_file_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )


def _create_coupling_hotspots(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE mart_symbol_coupling_hotspots (
            run_pk BIGINT NOT NULL,
            symbol_name VARCHAR,
            symbol_type VARCHAR,
            relative_path VARCHAR,
            fan_in INTEGER DEFAULT 0,
            fan_out INTEGER DEFAULT 0,
            total_coupling INTEGER DEFAULT 0,
            instability DOUBLE DEFAULT 0.0,
            coupling_risk VARCHAR,
            coupling_pattern VARCHAR
        )
    """)
    conn.executemany(
        "INSERT INTO mart_symbol_coupling_hotspots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (SYMBOL_RUN_PK, "handle_request", "function", "src/api/routes.py",
             2, 15, 17, 0.88, "critical", "hub"),
            (SYMBOL_RUN_PK, "DatabasePool", "class", "src/core/database.py",
             8, 3, 11, 0.27, "high", "service"),
        ],
    )


def _create_knowledge_risk(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE mart_git_blame_knowledge_risk (
            run_pk BIGINT NOT NULL,
            relative_path VARCHAR,
            unique_authors INTEGER DEFAULT 0,
            top_author VARCHAR,
            top_author_pct DOUBLE DEFAULT 0.0,
            total_lines INTEGER DEFAULT 0,
            risk_level VARCHAR
        )
    """)
    conn.executemany(
        "INSERT INTO mart_git_blame_knowledge_risk VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (BLAME_RUN_PK, "src/core/engine.py", 1, "alice", 100.0, 800, "critical"),
            (BLAME_RUN_PK, "src/core/database.py", 2, "alice", 70.0, 600, "high"),
            (BLAME_RUN_PK, "src/utils/validators.py", 1, "bob", 100.0, 700, "critical"),
            (BLAME_RUN_PK, "src/api/middleware.py", 3, "alice", 50.0, 300, "low"),
        ],
    )


def _create_trivy_vulns(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE stg_trivy_vulnerabilities (
            run_pk BIGINT NOT NULL,
            vulnerability_id VARCHAR,
            pkg_name VARCHAR,
            package_name VARCHAR,
            installed_version VARCHAR,
            fixed_version VARCHAR,
            severity VARCHAR,
            title VARCHAR,
            relative_path VARCHAR
        )
    """)
    conn.executemany(
        "INSERT INTO stg_trivy_vulnerabilities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (TRIVY_RUN_PK, "CVE-2025-0001", "cryptolib", "cryptolib",
             "1.0.0", "1.0.1", "CRITICAL", "Remote code execution in cryptolib", "requirements.txt"),
            (TRIVY_RUN_PK, "CVE-2025-0002", "webframework", "webframework",
             "2.3.0", "2.3.1", "HIGH", "XSS in template engine", "requirements.txt"),
        ],
    )


def _create_gitleaks_secrets(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE stg_lz_gitleaks_secrets (
            run_pk BIGINT NOT NULL,
            relative_path VARCHAR,
            rule_id VARCHAR,
            description VARCHAR
        )
    """)
    conn.execute(
        "INSERT INTO stg_lz_gitleaks_secrets VALUES (?, ?, ?, ?)",
        [GITLEAKS_RUN_PK, "src/api/middleware.py", "aws-access-key", "AWS Access Key detected"],
    )


def _create_pmd_cpd(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE stg_lz_pmd_cpd_duplications (
            run_pk BIGINT NOT NULL,
            source_file VARCHAR,
            tokens INTEGER DEFAULT 0,
            lines INTEGER DEFAULT 0,
            occurrences INTEGER DEFAULT 0
        )
    """)
    conn.execute(
        "INSERT INTO stg_lz_pmd_cpd_duplications VALUES (?, ?, ?, ?, ?)",
        [PMD_CPD_RUN_PK, "src/utils/formatters.py", 200, 30, 3],
    )


def _create_layout_files(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE lz_layout_files (
            run_pk BIGINT NOT NULL,
            directory_path VARCHAR,
            relative_path VARCHAR
        )
    """)
    rows = []
    for f in [
        "src/core/engine.py", "src/core/database.py", "src/core/config.py",
        "src/api/routes.py", "src/api/middleware.py", "src/api/serializers.py",
        "src/utils/helpers.py", "src/utils/validators.py", "src/utils/formatters.py",
    ]:
        parts = f.rsplit("/", 1)
        rows.append((LAYOUT_RUN_PK, parts[0], f))
    for i in range(15):
        rows.append((LAYOUT_RUN_PK, "src/generated", f"src/generated/auto_{i}.py"))
    # Deep nesting (depth=6) triggers architecture query at default min_depth=6
    rows.append((LAYOUT_RUN_PK, "src/a/b/c/d/e/f", "src/a/b/c/d/e/f/deep.py"))
    conn.executemany(
        "INSERT INTO lz_layout_files VALUES (?, ?, ?)",
        rows,
    )


def _create_semgrep_smells(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE stg_lz_semgrep_smells (
            run_pk BIGINT NOT NULL,
            rule_id VARCHAR,
            relative_path VARCHAR
        )
    """)
    # Pervasive smell affecting 7 of 12 files = 58% (>50% default threshold)
    affected_files = [
        "src/core/engine.py", "src/core/database.py", "src/api/routes.py",
        "src/api/serializers.py", "src/utils/helpers.py", "src/utils/helpers.py",
        "src/utils/validators.py", "src/utils/formatters.py",
    ]
    conn.executemany(
        "INSERT INTO stg_lz_semgrep_smells VALUES (?, ?, ?)",
        [(SEMGREP_RUN_PK, "python.lang.security.audit.exec-used", f) for f in affected_files],
    )


def _create_evidence_persistence_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create lz_evidence, lz_claims, lz_risks, lz_warnings, lz_evidence_sets, lz_evidence_reviews."""
    conn.execute("""
        CREATE TABLE lz_evidence (
            collection_run_id VARCHAR NOT NULL,
            evidence_id VARCHAR NOT NULL,
            evidence_type VARCHAR NOT NULL,
            category VARCHAR NOT NULL,
            location VARCHAR NOT NULL,
            excerpt TEXT,
            observation TEXT,
            why_it_matters TEXT,
            tool_source VARCHAR NOT NULL,
            run_pk BIGINT NOT NULL,
            confidence VARCHAR NOT NULL DEFAULT 'high',
            metadata_json TEXT,
            evidence_set_id VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (collection_run_id, evidence_id)
        )
    """)
    conn.execute("""
        CREATE TABLE lz_evidence_sets (
            evidence_set_id VARCHAR NOT NULL,
            collection_run_id VARCHAR NOT NULL,
            parameter_set_name VARCHAR NOT NULL,
            parameter_set_json TEXT NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP,
            total_items INTEGER DEFAULT 0,
            reviewed_items INTEGER DEFAULT 0,
            accepted_items INTEGER DEFAULT 0,
            rejected_items INTEGER DEFAULT 0,
            PRIMARY KEY (evidence_set_id)
        )
    """)
    conn.execute("""
        CREATE TABLE lz_evidence_reviews (
            evidence_set_id VARCHAR NOT NULL,
            evidence_id VARCHAR NOT NULL,
            verdict VARCHAR NOT NULL DEFAULT 'pending',
            reviewer VARCHAR,
            reviewed_at TIMESTAMP,
            notes TEXT,
            enhanced_observation TEXT,
            enhanced_why_it_matters TEXT,
            PRIMARY KEY (evidence_set_id, evidence_id)
        )
    """)
    conn.execute("""
        CREATE TABLE lz_claims (
            collection_run_id VARCHAR NOT NULL,
            claim_id VARCHAR NOT NULL,
            category VARCHAR NOT NULL,
            statement TEXT NOT NULL,
            evidence_ids VARCHAR NOT NULL,
            implication TEXT,
            confidence VARCHAR NOT NULL,
            triggered_by VARCHAR NOT NULL,
            severity VARCHAR,
            evidence_set_id VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (collection_run_id, claim_id)
        )
    """)
    conn.execute("""
        CREATE TABLE lz_risks (
            collection_run_id VARCHAR NOT NULL,
            risk_id VARCHAR NOT NULL,
            description TEXT NOT NULL,
            technical_cause TEXT,
            claim_ids VARCHAR NOT NULL,
            manifests_in VARCHAR,
            triggered_by VARCHAR NOT NULL,
            severity VARCHAR NOT NULL,
            owner VARCHAR,
            action TEXT,
            sla_date VARCHAR,
            status VARCHAR DEFAULT 'open',
            evidence_set_id VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (collection_run_id, risk_id)
        )
    """)
    conn.execute("""
        CREATE TABLE lz_warnings (
            collection_run_id VARCHAR NOT NULL,
            category VARCHAR NOT NULL,
            source VARCHAR NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE lz_evidence_query_params (
            evidence_set_id VARCHAR NOT NULL,
            query_name VARCHAR NOT NULL,
            threshold INTEGER,
            limit_rows INTEGER,
            coverage_threshold INTEGER,
            ccn_threshold INTEGER,
            density_threshold INTEGER,
            loc_threshold INTEGER,
            min_files INTEGER,
            min_depth INTEGER,
            gini_threshold DOUBLE,
            pct_threshold INTEGER,
            PRIMARY KEY (evidence_set_id, query_name)
        )
    """)
    conn.execute("""
        CREATE TABLE lz_evidence_claim_params (
            evidence_set_id VARCHAR NOT NULL,
            rule_name VARCHAR NOT NULL,
            fan_out_multiplier INTEGER,
            min_fan_out INTEGER,
            max_authors INTEGER,
            min_lines INTEGER,
            max_coverage INTEGER,
            min_ccn INTEGER,
            min_categories INTEGER,
            PRIMARY KEY (evidence_set_id, rule_name)
        )
    """)
    conn.execute("""
        CREATE TABLE lz_evidence_risk_params (
            evidence_set_id VARCHAR NOT NULL,
            pattern_name VARCHAR NOT NULL,
            min_claims INTEGER,
            default_severity VARCHAR,
            PRIMARY KEY (evidence_set_id, pattern_name)
        )
    """)


# ---------------------------------------------------------------------------
# Module-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def synth_db(tmp_path_factory):
    """Create a synthetic DuckDB with all tables the evidence system needs."""
    db_path = str(tmp_path_factory.mktemp("evidence_e2e") / "synth.duckdb")
    conn = duckdb.connect(db_path)
    _create_tool_runs(conn)
    _create_unified_file_metrics(conn)
    _create_coupling_hotspots(conn)
    _create_knowledge_risk(conn)
    _create_trivy_vulns(conn)
    _create_gitleaks_secrets(conn)
    _create_pmd_cpd(conn)
    _create_layout_files(conn)
    _create_semgrep_smells(conn)
    _create_evidence_persistence_tables(conn)
    conn.close()
    return db_path


@pytest.fixture(scope="module")
def fetcher(synth_db):
    return DataFetcher(synth_db)


@pytest.fixture(scope="module")
def category_registry():
    return ConfigLoader.load_categories()


@pytest.fixture(scope="module")
def default_params():
    return ConfigLoader.load_parameter_set("default")


@pytest.fixture(scope="module")
def conservative_params():
    return ConfigLoader.load_parameter_set("conservative")


@pytest.fixture(scope="module")
def pe_params():
    return ConfigLoader.load_parameter_set("pe_due_diligence")


def _build_registry(fetcher, category_registry, params):
    """Helper: build a full evidence registry for a given parameter set."""
    builder = EvidenceRegistryBuilder(
        parameter_set=params,
        category_registry=category_registry,
    )
    return builder.build(fetcher, SCC_RUN_PK)


@pytest.fixture(scope="module")
def default_registry(fetcher, category_registry, default_params):
    return _build_registry(fetcher, category_registry, default_params)


@pytest.fixture(scope="module")
def conservative_registry(fetcher, category_registry, conservative_params):
    return _build_registry(fetcher, category_registry, conservative_params)


@pytest.fixture(scope="module")
def pe_registry(fetcher, category_registry, pe_params):
    return _build_registry(fetcher, category_registry, pe_params)


# ===========================================================================
# Default Profile E2E
# ===========================================================================


class TestDefaultProfile:
    """Evidence, claims, and risks for the 'default' parameter set.

    Thresholds: complexity>=15, coverage<50 & CCN>15, quality density>=20, LOC>=500.
    Expected: 22 evidence, 8 claims, 2 risks.
    """

    def test_total_evidence(self, default_registry):
        assert len(default_registry.evidence) == 22

    def test_total_claims(self, default_registry):
        assert len(default_registry.claims) == 8

    def test_total_risks(self, default_registry):
        assert len(default_registry.risks) == 2

    def test_all_10_categories_present(self, default_registry):
        categories = {e.category for e in default_registry.evidence}
        assert categories == {
            "complexity", "security", "coupling", "coverage", "ownership",
            "quality", "maintainability", "architecture", "dependencies", "duplication",
        }

    # -- complexity (threshold=15) → 3 items: engine(25), database(18), validators(16)

    def test_complexity_items(self, default_registry):
        items = default_registry.evidence_by_category("complexity")
        assert len(items) == 3
        locs = {e.location for e in items}
        assert locs == {"src/core/engine.py", "src/core/database.py", "src/utils/validators.py"}

    def test_complexity_metadata(self, default_registry):
        items = default_registry.evidence_by_category("complexity")
        engine = next(e for e in items if e.location == "src/core/engine.py")
        assert engine.metadata == {"complexity_max": 25, "function_count": 12, "loc_total": 800}
        assert engine.evidence_id.startswith("E-CCN-")
        assert engine.tool_source == "lizard"

    # -- security → 3 items: 1 CRITICAL CVE, 1 HIGH CVE, 1 secret

    def test_security_items(self, default_registry):
        items = default_registry.evidence_by_category("security")
        assert len(items) == 3
        types = sorted(e.evidence_type for e in items)
        assert types == ["secret_detection", "vulnerability", "vulnerability"]

    def test_security_critical_cve(self, default_registry):
        items = default_registry.evidence_by_category("security")
        critical = [e for e in items if "CRITICAL" in e.excerpt and e.evidence_type == "vulnerability"]
        assert len(critical) == 1
        assert "CVE-2025-0001" in critical[0].excerpt
        assert critical[0].metadata["package_name"] == "cryptolib"

    def test_security_secret(self, default_registry):
        items = default_registry.evidence_by_category("security")
        secrets = [e for e in items if e.evidence_type == "secret_detection"]
        assert len(secrets) == 1
        assert secrets[0].location == "src/api/middleware.py"
        assert secrets[0].metadata["finding_id"] == "aws-access-key"

    # -- coupling → 2 items: routes(critical), database(high)

    def test_coupling_items(self, default_registry):
        items = default_registry.evidence_by_category("coupling")
        assert len(items) == 2
        routes = next(e for e in items if e.location == "src/api/routes.py")
        assert routes.metadata == {"fan_in": 2, "fan_out": 15, "total_coupling": 17}
        db = next(e for e in items if e.location == "src/core/database.py")
        assert db.metadata == {"fan_in": 8, "fan_out": 3, "total_coupling": 11}

    # -- coverage (coverage<50, CCN>15) → 2 items: engine(20%,25), validators(30%,16)

    def test_coverage_items(self, default_registry):
        items = default_registry.evidence_by_category("coverage")
        assert len(items) == 2
        locs = {e.location for e in items}
        assert locs == {"src/core/engine.py", "src/utils/validators.py"}

    def test_coverage_metadata(self, default_registry):
        items = default_registry.evidence_by_category("coverage")
        engine = next(e for e in items if e.location == "src/core/engine.py")
        assert engine.metadata["coverage_line_pct"] == 20.0
        assert engine.metadata["complexity_max"] == 25

    # -- ownership (risk_level critical/high) → 3 items

    def test_ownership_items(self, default_registry):
        items = default_registry.evidence_by_category("ownership")
        assert len(items) == 3
        locs = {e.location for e in items}
        assert locs == {"src/core/engine.py", "src/utils/validators.py", "src/core/database.py"}

    def test_ownership_silo_metadata(self, default_registry):
        items = default_registry.evidence_by_category("ownership")
        engine = next(e for e in items if e.location == "src/core/engine.py")
        assert engine.metadata["unique_authors"] == 1
        assert engine.metadata["total_lines"] == 800
        assert engine.metadata["top_author_pct"] == 100.0

    # -- quality (density>=20) → 1 item: helpers(40 smells/KLOC)

    def test_quality_items(self, default_registry):
        items = default_registry.evidence_by_category("quality")
        assert len(items) == 1
        assert items[0].location == "src/utils/helpers.py"
        assert items[0].metadata["smell_density_per_kloc"] == 40.0

    # -- maintainability (LOC>=500) → 4 items

    def test_maintainability_items(self, default_registry):
        items = default_registry.evidence_by_category("maintainability")
        assert len(items) == 4
        locs = {e.location for e in items}
        assert locs == {
            "src/api/routes.py", "src/core/engine.py",
            "src/utils/validators.py", "src/core/database.py",
        }

    # -- architecture (depth>=6) → 1 item: deep path

    def test_architecture_items(self, default_registry):
        items = default_registry.evidence_by_category("architecture")
        assert len(items) == 1
        assert items[0].location == "src/a/b/c/d/e/f"
        assert items[0].metadata["depth"] == 6

    # -- dependencies → 2 items (CRITICAL+HIGH trivy)

    def test_dependencies_items(self, default_registry):
        items = default_registry.evidence_by_category("dependencies")
        assert len(items) == 2
        pkgs = {e.metadata["package_name"] for e in items}
        assert pkgs == {"cryptolib", "webframework"}

    # -- duplication → 1 item: formatters.py

    def test_duplication_items(self, default_registry):
        items = default_registry.evidence_by_category("duplication")
        assert len(items) == 1
        assert items[0].location == "src/utils/formatters.py"
        assert items[0].metadata == {"tokens": 200, "lines": 30, "occurrences": 3}

    # -- claims breakdown

    def test_claim_high_coupling(self, default_registry):
        claims = [c for c in default_registry.claims if c.triggered_by == "HighCouplingRule"]
        assert len(claims) == 1
        assert "routes.py" in claims[0].statement
        assert "fan_out=15" in claims[0].statement

    def test_claim_knowledge_silo(self, default_registry):
        claims = [c for c in default_registry.claims if c.triggered_by == "KnowledgeSiloRule"]
        assert len(claims) == 2
        statements = " ".join(c.statement for c in claims)
        assert "validators.py" in statements
        assert "engine.py" in statements

    def test_claim_coverage_gap(self, default_registry):
        claims = [c for c in default_registry.claims if c.triggered_by == "CoverageGapRule"]
        assert len(claims) == 2
        statements = " ".join(c.statement for c in claims)
        assert "engine.py" in statements
        assert "validators.py" in statements

    def test_claim_security_exposure(self, default_registry):
        claims = [c for c in default_registry.claims if c.triggered_by == "SecurityExposureRule"]
        assert len(claims) == 2
        severities = {c.severity for c in claims}
        assert severities == {"critical", "high"}

    def test_claim_pervasive_debt(self, default_registry):
        claims = [c for c in default_registry.claims if c.triggered_by == "PervasiveDebtRule"]
        assert len(claims) == 1
        assert "exec-used" in claims[0].statement
        assert "58%" in claims[0].statement

    # -- risks breakdown

    def test_risk_security(self, default_registry):
        risks = [r for r in default_registry.risks if r.triggered_by == "Security exposure"]
        assert len(risks) == 1
        assert risks[0].severity == "critical"  # escalated from claim severity
        assert len(risks[0].claim_ids) == 2

    def test_risk_knowledge_concentration(self, default_registry):
        risks = [r for r in default_registry.risks if r.triggered_by == "Knowledge concentration"]
        assert len(risks) == 1
        assert risks[0].severity == "high"
        assert len(risks[0].claim_ids) == 2


# ===========================================================================
# Conservative Profile E2E
# ===========================================================================


class TestConservativeProfile:
    """Evidence, claims, and risks for the 'conservative' parameter set.

    Overrides: complexity>=25, coverage<30 & CCN>25, quality density>=40, silo min_lines=1000.
    Expected: 18 evidence, 4 claims, 1 risk.
    """

    def test_total_evidence(self, conservative_registry):
        assert len(conservative_registry.evidence) == 18

    def test_total_claims(self, conservative_registry):
        assert len(conservative_registry.claims) == 4

    def test_total_risks(self, conservative_registry):
        assert len(conservative_registry.risks) == 1

    # -- complexity (threshold=25) → 1 item: only engine(25)

    def test_complexity_only_engine(self, conservative_registry):
        items = conservative_registry.evidence_by_category("complexity")
        assert len(items) == 1
        assert items[0].location == "src/core/engine.py"
        assert items[0].metadata["complexity_max"] == 25

    # -- coverage (coverage<30, CCN>25) → 0 items
    #    engine has cov=20 < 30 but CCN=25 is NOT > 25 (strict >), so no items

    def test_coverage_empty(self, conservative_registry):
        items = conservative_registry.evidence_by_category("coverage")
        assert len(items) == 0

    # -- quality (density>=40) → still 1 item: helpers at 40/KLOC

    def test_quality_still_helpers(self, conservative_registry):
        items = conservative_registry.evidence_by_category("quality")
        assert len(items) == 1
        assert items[0].location == "src/utils/helpers.py"

    # -- categories unchanged by conservative: security, coupling, ownership,
    #    maintainability, architecture, dependencies, duplication

    def test_security_unchanged(self, conservative_registry):
        assert len(conservative_registry.evidence_by_category("security")) == 3

    def test_coupling_unchanged(self, conservative_registry):
        assert len(conservative_registry.evidence_by_category("coupling")) == 2

    def test_ownership_unchanged(self, conservative_registry):
        assert len(conservative_registry.evidence_by_category("ownership")) == 3

    def test_maintainability_unchanged(self, conservative_registry):
        assert len(conservative_registry.evidence_by_category("maintainability")) == 4

    def test_architecture_unchanged(self, conservative_registry):
        assert len(conservative_registry.evidence_by_category("architecture")) == 1

    def test_dependencies_unchanged(self, conservative_registry):
        assert len(conservative_registry.evidence_by_category("dependencies")) == 2

    def test_duplication_unchanged(self, conservative_registry):
        assert len(conservative_registry.evidence_by_category("duplication")) == 1

    # -- claims: no silo claims (min_lines=1000), no coverage gap claims (no coverage evidence)

    def test_no_silo_claims(self, conservative_registry):
        claims = [c for c in conservative_registry.claims if c.triggered_by == "KnowledgeSiloRule"]
        assert len(claims) == 0

    def test_no_coverage_gap_claims(self, conservative_registry):
        claims = [c for c in conservative_registry.claims if c.triggered_by == "CoverageGapRule"]
        assert len(claims) == 0

    def test_claim_coupling_still_fires(self, conservative_registry):
        claims = [c for c in conservative_registry.claims if c.triggered_by == "HighCouplingRule"]
        assert len(claims) == 1

    def test_claim_security_still_fires(self, conservative_registry):
        claims = [c for c in conservative_registry.claims if c.triggered_by == "SecurityExposureRule"]
        assert len(claims) == 2

    def test_claim_pervasive_debt_still_fires(self, conservative_registry):
        claims = [c for c in conservative_registry.claims if c.triggered_by == "PervasiveDebtRule"]
        assert len(claims) == 1

    # -- risks: only Security exposure (no Knowledge concentration — needs 2 silo claims)

    def test_only_security_risk(self, conservative_registry):
        triggers = {r.triggered_by for r in conservative_registry.risks}
        assert triggers == {"Security exposure"}
        assert conservative_registry.risks[0].severity == "critical"

    def test_no_knowledge_risk(self, conservative_registry):
        risks = [r for r in conservative_registry.risks if r.triggered_by == "Knowledge concentration"]
        assert len(risks) == 0


# ===========================================================================
# PE Due Diligence Profile E2E
# ===========================================================================


class TestPEDueDiligenceProfile:
    """Evidence, claims, and risks for the 'pe_due_diligence' parameter set.

    Overrides: complexity>=10, coverage<70 & CCN>10, quality density>=10.
    Expected: 25 evidence, 8 claims, 2 risks.
    """

    def test_total_evidence(self, pe_registry):
        assert len(pe_registry.evidence) == 25

    def test_total_claims(self, pe_registry):
        assert len(pe_registry.claims) == 8

    def test_total_risks(self, pe_registry):
        assert len(pe_registry.risks) == 2

    # -- complexity (threshold=10) → 5 items: engine(25), database(18), validators(16), routes(12), serializers(10)

    def test_complexity_five_items(self, pe_registry):
        items = pe_registry.evidence_by_category("complexity")
        assert len(items) == 5
        locs = {e.location for e in items}
        assert locs == {
            "src/core/engine.py", "src/core/database.py", "src/utils/validators.py",
            "src/api/routes.py", "src/api/serializers.py",
        }

    def test_complexity_includes_routes_and_serializers(self, pe_registry):
        items = pe_registry.evidence_by_category("complexity")
        routes = next(e for e in items if e.location == "src/api/routes.py")
        assert routes.metadata["complexity_max"] == 12
        serializers = next(e for e in items if e.location == "src/api/serializers.py")
        assert serializers.metadata["complexity_max"] == 10

    # -- coverage (coverage<70, CCN>10) → 3 items: engine(20%,25), validators(30%,16), routes(60%,12)

    def test_coverage_three_items(self, pe_registry):
        items = pe_registry.evidence_by_category("coverage")
        assert len(items) == 3
        locs = {e.location for e in items}
        assert locs == {"src/core/engine.py", "src/utils/validators.py", "src/api/routes.py"}

    def test_coverage_routes_now_included(self, pe_registry):
        items = pe_registry.evidence_by_category("coverage")
        routes = next(e for e in items if e.location == "src/api/routes.py")
        assert routes.metadata["coverage_line_pct"] == 60.0
        assert routes.metadata["complexity_max"] == 12

    # -- quality (density>=10) → still 1 item (only helpers exceeds even 10)

    def test_quality_items(self, pe_registry):
        items = pe_registry.evidence_by_category("quality")
        assert len(items) == 1
        assert items[0].location == "src/utils/helpers.py"

    # -- categories unchanged from default

    def test_security_unchanged(self, pe_registry):
        assert len(pe_registry.evidence_by_category("security")) == 3

    def test_coupling_unchanged(self, pe_registry):
        assert len(pe_registry.evidence_by_category("coupling")) == 2

    def test_ownership_unchanged(self, pe_registry):
        assert len(pe_registry.evidence_by_category("ownership")) == 3

    def test_maintainability_unchanged(self, pe_registry):
        assert len(pe_registry.evidence_by_category("maintainability")) == 4

    def test_architecture_unchanged(self, pe_registry):
        assert len(pe_registry.evidence_by_category("architecture")) == 1

    def test_dependencies_unchanged(self, pe_registry):
        assert len(pe_registry.evidence_by_category("dependencies")) == 2

    def test_duplication_unchanged(self, pe_registry):
        assert len(pe_registry.evidence_by_category("duplication")) == 1

    # -- claims: same as default (silo/coverage thresholds unchanged in PE)

    def test_claim_silo_same_as_default(self, pe_registry):
        claims = [c for c in pe_registry.claims if c.triggered_by == "KnowledgeSiloRule"]
        assert len(claims) == 2

    def test_claim_coverage_gap_same_as_default(self, pe_registry):
        claims = [c for c in pe_registry.claims if c.triggered_by == "CoverageGapRule"]
        assert len(claims) == 2

    def test_claim_security(self, pe_registry):
        claims = [c for c in pe_registry.claims if c.triggered_by == "SecurityExposureRule"]
        assert len(claims) == 2

    # -- risks: same pattern as default

    def test_risk_security_critical(self, pe_registry):
        risks = [r for r in pe_registry.risks if r.triggered_by == "Security exposure"]
        assert len(risks) == 1
        assert risks[0].severity == "critical"

    def test_risk_knowledge(self, pe_registry):
        risks = [r for r in pe_registry.risks if r.triggered_by == "Knowledge concentration"]
        assert len(risks) == 1
        assert risks[0].severity == "high"


# ===========================================================================
# Cross-Profile Comparison E2E
# ===========================================================================


class TestCrossProfileComparison:
    """Verify monotonic ordering: conservative < default < pe_due_diligence."""

    def test_total_evidence_ordering(self, conservative_registry, default_registry, pe_registry):
        assert len(conservative_registry.evidence) < len(default_registry.evidence) < len(pe_registry.evidence)

    def test_complexity_ordering(self, conservative_registry, default_registry, pe_registry):
        c = len(conservative_registry.evidence_by_category("complexity"))
        d = len(default_registry.evidence_by_category("complexity"))
        p = len(pe_registry.evidence_by_category("complexity"))
        assert c < d < p, f"conservative={c}, default={d}, pe={p}"

    def test_coverage_ordering(self, conservative_registry, default_registry, pe_registry):
        c = len(conservative_registry.evidence_by_category("coverage"))
        d = len(default_registry.evidence_by_category("coverage"))
        p = len(pe_registry.evidence_by_category("coverage"))
        assert c < d < p, f"conservative={c}, default={d}, pe={p}"

    def test_claims_ordering(self, conservative_registry, default_registry, pe_registry):
        assert len(conservative_registry.claims) < len(default_registry.claims)
        assert len(default_registry.claims) == len(pe_registry.claims)  # same claim params

    def test_risks_ordering(self, conservative_registry, default_registry, pe_registry):
        assert len(conservative_registry.risks) < len(default_registry.risks)
        assert len(default_registry.risks) == len(pe_registry.risks)  # same risk params

    def test_unchanged_categories_same_across_profiles(
        self, conservative_registry, default_registry, pe_registry,
    ):
        """Categories not affected by any override produce identical counts."""
        for cat in ("security", "coupling", "ownership", "maintainability",
                    "architecture", "dependencies", "duplication"):
            c = len(conservative_registry.evidence_by_category(cat))
            d = len(default_registry.evidence_by_category(cat))
            p = len(pe_registry.evidence_by_category(cat))
            assert c == d == p, f"{cat}: conservative={c}, default={d}, pe={p}"


# ===========================================================================
# Custom Parameter Overrides E2E
# ===========================================================================


class TestCustomParameterOverrides:
    """Test ad-hoc parameter sets to verify threshold mechanics."""

    def test_strict_silo_filters_all(self, fetcher, category_registry):
        """KnowledgeSiloRule min_lines=1000 excludes engine(800) and validators(700)."""
        params = ParameterSet(
            name="strict_silo",
            description="",
            query_params=ConfigLoader.load_parameter_set("default").query_params,
            claim_params={"KnowledgeSiloRule": {"max_authors": 1, "min_lines": 1000}},
            risk_params={},
            action_params={},
        )
        registry = _build_registry(fetcher, category_registry, params)
        silo_claims = [c for c in registry.claims if c.triggered_by == "KnowledgeSiloRule"]
        assert len(silo_claims) == 0

    def test_low_architecture_thresholds(self, fetcher, category_registry):
        """Lowering min_files/min_depth surfaces more architecture evidence."""
        params = ParameterSet(
            name="arch_sensitive",
            description="",
            query_params={
                **ConfigLoader.load_parameter_set("default").query_params,
                "evidence_architecture": {"min_files": 5, "min_depth": 5, "limit": 50},
            },
            claim_params={},
            risk_params={},
            action_params={},
        )
        registry = _build_registry(fetcher, category_registry, params)
        arch_items = registry.evidence_by_category("architecture")
        # min_files=5 surfaces src/generated (15 files); min_depth=5 surfaces deep path
        assert len(arch_items) >= 2
        locs = {e.location for e in arch_items}
        assert "src/generated" in locs
        assert "src/a/b/c/d/e/f" in locs

    def test_risk_severity_override(self, fetcher, category_registry):
        """Even with default_severity=medium, critical claims still escalate severity."""
        params = ParameterSet(
            name="downgraded_security",
            description="",
            query_params=ConfigLoader.load_parameter_set("default").query_params,
            claim_params={},
            risk_params={"Security exposure": {"min_claims": 1, "default_severity": "medium"}},
            action_params={},
        )
        registry = _build_registry(fetcher, category_registry, params)
        sec_risks = [r for r in registry.risks if r.triggered_by == "Security exposure"]
        assert len(sec_risks) == 1
        # Critical claim escalates medium default to critical
        assert sec_risks[0].severity == "critical"


# ===========================================================================
# Evidence Persistence E2E
# ===========================================================================


class TestEvidencePersistenceE2E:
    """Test persisting evidence/claims/risks to DuckDB."""

    def test_persist_evidence_to_db(self, synth_db, default_registry):
        conn = duckdb.connect(synth_db)
        EvidenceRegistryBuilder.persist(default_registry, conn, COLLECTION_RUN_ID)
        rows = conn.execute(
            "SELECT COUNT(*) FROM lz_evidence WHERE collection_run_id = ?",
            [COLLECTION_RUN_ID],
        ).fetchone()
        assert rows[0] == 22
        conn.close()

    def test_persist_claims_to_db(self, synth_db):
        conn = duckdb.connect(synth_db)
        rows = conn.execute(
            "SELECT claim_id, evidence_ids FROM lz_claims WHERE collection_run_id = ?",
            [COLLECTION_RUN_ID],
        ).fetchall()
        assert len(rows) == 8
        for _, eids in rows:
            assert eids
            for eid in eids.split(","):
                assert eid.startswith("E-")
        conn.close()

    def test_persist_risks_to_db(self, synth_db):
        conn = duckdb.connect(synth_db)
        rows = conn.execute(
            "SELECT risk_id, claim_ids FROM lz_risks WHERE collection_run_id = ?",
            [COLLECTION_RUN_ID],
        ).fetchall()
        assert len(rows) == 2
        for _, cids in rows:
            assert cids
            for cid in cids.split(","):
                assert cid.startswith("CLM-")
        conn.close()

    def test_persist_metadata_json(self, synth_db):
        conn = duckdb.connect(synth_db)
        rows = conn.execute(
            "SELECT metadata_json FROM lz_evidence WHERE collection_run_id = ? AND metadata_json IS NOT NULL",
            [COLLECTION_RUN_ID],
        ).fetchall()
        assert len(rows) == 22  # all items have metadata
        for (mj,) in rows:
            parsed = json.loads(mj)
            assert isinstance(parsed, dict)
        conn.close()

    def test_persist_idempotent(self, synth_db, default_registry):
        conn = duckdb.connect(synth_db)
        EvidenceRegistryBuilder.persist(default_registry, conn, COLLECTION_RUN_ID)
        rows = conn.execute(
            "SELECT COUNT(*) FROM lz_evidence WHERE collection_run_id = ?",
            [COLLECTION_RUN_ID],
        ).fetchone()
        assert rows[0] == 22  # no duplicates
        conn.close()

    def test_persist_conservative_fewer_rows(self, synth_db, conservative_registry):
        crid = f"persist-conserv-{uuid.uuid4().hex[:8]}"
        conn = duckdb.connect(synth_db)
        EvidenceRegistryBuilder.persist(conservative_registry, conn, crid)
        count = conn.execute(
            "SELECT COUNT(*) FROM lz_evidence WHERE collection_run_id = ?",
            [crid],
        ).fetchone()[0]
        assert count == 18
        conn.close()


# ===========================================================================
# Structured Parameter Persistence E2E
# ===========================================================================


class TestStructuredParameterPersistenceE2E:
    """Test auto-creation of evidence sets with structured parameter storage."""

    def test_persist_creates_evidence_set(self, synth_db, default_registry, default_params):
        crid = f"param-e2e-{uuid.uuid4().hex[:8]}"
        conn = duckdb.connect(synth_db)
        es_id = EvidenceRegistryBuilder.persist(
            default_registry, conn, crid, parameter_set=default_params,
        )
        assert es_id is not None
        row = conn.execute(
            "SELECT parameter_set_name, status, total_items FROM lz_evidence_sets WHERE evidence_set_id = ?",
            [es_id],
        ).fetchone()
        assert row is not None
        assert row[0] == "default"
        assert row[1] == "open"
        assert row[2] == len(default_registry.evidence)
        conn.close()

    def test_persist_query_params(self, synth_db, default_registry, default_params):
        crid = f"param-qp-{uuid.uuid4().hex[:8]}"
        conn = duckdb.connect(synth_db)
        es_id = EvidenceRegistryBuilder.persist(
            default_registry, conn, crid, parameter_set=default_params,
        )
        rows = conn.execute(
            "SELECT query_name, threshold, limit_rows FROM lz_evidence_query_params WHERE evidence_set_id = ?",
            [es_id],
        ).fetchall()
        names = {r[0] for r in rows}
        assert "evidence_complexity" in names
        ccn_row = next(r for r in rows if r[0] == "evidence_complexity")
        assert ccn_row[1] == 15  # threshold
        assert ccn_row[2] == 100  # limit_rows
        conn.close()

    def test_persist_claim_params(self, synth_db, default_registry, default_params):
        crid = f"param-cp-{uuid.uuid4().hex[:8]}"
        conn = duckdb.connect(synth_db)
        es_id = EvidenceRegistryBuilder.persist(
            default_registry, conn, crid, parameter_set=default_params,
        )
        rows = conn.execute(
            "SELECT rule_name, fan_out_multiplier FROM lz_evidence_claim_params WHERE evidence_set_id = ?",
            [es_id],
        ).fetchall()
        names = {r[0] for r in rows}
        assert "HighCouplingRule" in names
        hc = next(r for r in rows if r[0] == "HighCouplingRule")
        assert hc[1] == 3
        conn.close()

    def test_persist_risk_params(self, synth_db, default_registry, default_params):
        crid = f"param-rp-{uuid.uuid4().hex[:8]}"
        conn = duckdb.connect(synth_db)
        es_id = EvidenceRegistryBuilder.persist(
            default_registry, conn, crid, parameter_set=default_params,
        )
        rows = conn.execute(
            "SELECT pattern_name, min_claims, default_severity FROM lz_evidence_risk_params WHERE evidence_set_id = ?",
            [es_id],
        ).fetchall()
        names = {r[0] for r in rows}
        assert "Security exposure" in names
        sec = next(r for r in rows if r[0] == "Security exposure")
        assert sec[1] == 1
        assert sec[2] == "high"
        conn.close()

    def test_roundtrip_parameter_set(self, synth_db, default_registry, default_params):
        from insights.evidence.param_persistence import load_parameter_set_from_db

        crid = f"param-rt-{uuid.uuid4().hex[:8]}"
        conn = duckdb.connect(synth_db)
        es_id = EvidenceRegistryBuilder.persist(
            default_registry, conn, crid, parameter_set=default_params,
        )
        loaded = load_parameter_set_from_db(conn, es_id)
        assert loaded is not None
        assert loaded.query_params == default_params.query_params
        assert loaded.claim_params == default_params.claim_params
        assert loaded.risk_params == default_params.risk_params
        conn.close()

    def test_evidence_linked_to_set(self, synth_db, default_registry, default_params):
        crid = f"param-link-{uuid.uuid4().hex[:8]}"
        conn = duckdb.connect(synth_db)
        es_id = EvidenceRegistryBuilder.persist(
            default_registry, conn, crid, parameter_set=default_params,
        )
        count = conn.execute(
            "SELECT COUNT(*) FROM lz_evidence WHERE collection_run_id = ? AND evidence_set_id = ?",
            [crid, es_id],
        ).fetchone()[0]
        assert count == len(default_registry.evidence)
        conn.close()

    def test_persist_without_params_returns_none(self, synth_db, default_registry):
        crid = f"param-none-{uuid.uuid4().hex[:8]}"
        conn = duckdb.connect(synth_db)
        result = EvidenceRegistryBuilder.persist(default_registry, conn, crid)
        assert result is None
        conn.close()


# ===========================================================================
# Evidence Set Lifecycle E2E
# ===========================================================================


class TestEvidenceSetLifecycleE2E:
    """Test evidence set review workflow."""

    @pytest.fixture()
    def review_db(self, synth_db, default_registry):
        """Create a fresh evidence set for review tests."""
        conn = duckdb.connect(synth_db)
        es_id = f"es-review-{uuid.uuid4().hex[:8]}"

        EvidenceRegistryBuilder.persist(default_registry, conn, COLLECTION_RUN_ID)

        conn.execute(
            """
            INSERT INTO lz_evidence_sets
                (evidence_set_id, collection_run_id, parameter_set_name, parameter_set_json, status, total_items)
            VALUES (?, ?, 'default', '{}', 'open', ?)
            """,
            [es_id, COLLECTION_RUN_ID, len(default_registry.evidence)],
        )

        conn.execute(
            "UPDATE lz_evidence SET evidence_set_id = ? WHERE collection_run_id = ?",
            [es_id, COLLECTION_RUN_ID],
        )

        yield conn, es_id, default_registry
        conn.close()

    def test_create_evidence_set(self, review_db):
        conn, es_id, _ = review_db
        reviewer = EvidenceReviewer(conn)
        es = reviewer.get_set(es_id)
        assert es is not None
        assert es.status == "open"
        assert es.parameter_set_name == "default"
        assert es.total_items == 22

    def test_review_workflow(self, review_db):
        conn, es_id, registry = review_db
        reviewer = EvidenceReviewer(conn)

        reviewer.transition_status(es_id, "in_review")
        assert reviewer.get_set(es_id).status == "in_review"

        first_eid = registry.evidence[0].evidence_id
        reviewer.submit_review(es_id, first_eid, "accepted", "test-user")

        reviews = reviewer.get_reviews(es_id)
        assert len(reviews) == 1
        assert reviews[0].verdict == "accepted"

    def test_batch_accept(self, review_db):
        conn, es_id, registry = review_db
        reviewer = EvidenceReviewer(conn)

        reviewer.transition_status(es_id, "in_review")
        count = reviewer.batch_accept(es_id, "auto-reviewer")
        assert count == 22  # all 22 default items

        es = reviewer.get_set(es_id)
        assert es.accepted_items == 22

    def test_state_transitions(self, review_db):
        conn, es_id, _ = review_db
        reviewer = EvidenceReviewer(conn)

        reviewer.transition_status(es_id, "in_review")
        reviewer.transition_status(es_id, "closed")
        reviewer.transition_status(es_id, "accepted")
        assert reviewer.get_set(es_id).status == "accepted"

    def test_invalid_transition_rejected(self, review_db):
        conn, es_id, _ = review_db
        reviewer = EvidenceReviewer(conn)
        with pytest.raises(ValueError, match="Cannot transition"):
            reviewer.transition_status(es_id, "closed")

    def test_fully_reviewed_check(self, review_db):
        conn, es_id, _ = review_db
        reviewer = EvidenceReviewer(conn)
        reviewer.transition_status(es_id, "in_review")
        assert not reviewer.is_fully_reviewed(es_id)
        reviewer.batch_accept(es_id, "auto-reviewer")
        assert reviewer.is_fully_reviewed(es_id)


# ===========================================================================
# Multi-Set Comparison E2E
# ===========================================================================


class TestMultiSetComparisonE2E:
    """Test persisting and comparing evidence sets from different profiles."""

    def test_three_profiles_persisted_correctly(
        self, synth_db, fetcher, category_registry,
        default_params, conservative_params, pe_params,
    ):
        reg_default = _build_registry(fetcher, category_registry, default_params)
        reg_conservative = _build_registry(fetcher, category_registry, conservative_params)
        reg_pe = _build_registry(fetcher, category_registry, pe_params)

        crid_d = f"multi-default-{uuid.uuid4().hex[:8]}"
        crid_c = f"multi-conserv-{uuid.uuid4().hex[:8]}"
        crid_p = f"multi-pe-{uuid.uuid4().hex[:8]}"

        conn = duckdb.connect(synth_db)
        EvidenceRegistryBuilder.persist(reg_default, conn, crid_d)
        EvidenceRegistryBuilder.persist(reg_conservative, conn, crid_c)
        EvidenceRegistryBuilder.persist(reg_pe, conn, crid_p)

        count_d = conn.execute(
            "SELECT COUNT(*) FROM lz_evidence WHERE collection_run_id = ?", [crid_d],
        ).fetchone()[0]
        count_c = conn.execute(
            "SELECT COUNT(*) FROM lz_evidence WHERE collection_run_id = ?", [crid_c],
        ).fetchone()[0]
        count_p = conn.execute(
            "SELECT COUNT(*) FROM lz_evidence WHERE collection_run_id = ?", [crid_p],
        ).fetchone()[0]
        conn.close()

        assert count_c == 18
        assert count_d == 22
        assert count_p == 25
        assert count_c < count_d < count_p
