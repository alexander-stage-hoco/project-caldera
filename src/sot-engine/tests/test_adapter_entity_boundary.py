"""Tests for the schema-valid-but-entity-fails boundary.

These tests verify that JSON payloads which pass schema validation but
contain values that fail entity __post_init__ validation are handled
correctly by adapters (raised with a clear error via quality validation
or caught during entity construction).

This covers the narrow gap between JSON schema constraints and the
stricter frozen-dataclass __post_init__ validators.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import (
    GitBlameScannerAdapter,
    GitleaksAdapter,
    LayoutScannerAdapter,
    LizardAdapter,
    RoslynAnalyzersAdapter,
    SccAdapter,
    SemgrepAdapter,
    SonarqubeAdapter,
    TrivyAdapter,
)
from persistence.repositories import (
    GitBlameRepository,
    GitleaksRepository,
    LayoutRepository,
    LizardRepository,
    RoslynRepository,
    SccRepository,
    SemgrepRepository,
    SonarqubeRepository,
    ToolRunRepository,
    TrivyRepository,
)


def _load_schema(conn: duckdb.DuckDBPyConnection) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "persistence" / "schema.sql"
    conn.execute(schema_path.read_text())


def _create_layout_run(
    conn: duckdb.DuckDBPyConnection,
    run_id: str,
    repo_id: str,
    extra_files: list[dict] | None = None,
) -> int:
    layout_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "layout_output.json"
    layout_payload = json.loads(layout_fixture.read_text())
    layout_payload["metadata"]["repo_id"] = repo_id
    layout_payload["metadata"]["run_id"] = run_id
    if extra_files:
        layout_payload["data"]["files"].extend(extra_files)

    run_repo = ToolRunRepository(conn)
    layout_repo = LayoutRepository(conn)
    LayoutScannerAdapter(run_repo, layout_repo, Path("/tmp/test-repo"), None).persist(layout_payload)
    return run_repo.get_run_pk(run_id, "layout-scanner")


def _load_fixture(name: str) -> dict:
    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / f"{name}_output.json"
    return json.loads(fixture_path.read_text())


def _prep(fixture_name: str) -> dict:
    """Load and stamp a fixture with test IDs."""
    payload = _load_fixture(fixture_name)
    payload["metadata"]["repo_id"] = REPO_ID
    payload["metadata"]["run_id"] = RUN_ID
    return payload


REPO_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
RUN_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


@pytest.mark.integration
class TestSchemaValidButEntityFails:
    """Tests for payloads that pass schema validation but fail entity construction.

    The JSON schemas use regex patterns and minimum constraints, but some
    edge-case paths (like ~/...) pass the regex while failing the entity's
    stricter __post_init__ validators.
    """

    # ── scc ──────────────────────────────────────────────────────────────

    def test_scc_tilde_path_passes_schema_fails_entity(self, tmp_path: Path) -> None:
        """A tilde path like '~/.bashrc' passes the JSON schema path regex
        (^[^/].*) but fails entity _validate_relative_path which rejects
        paths starting with '~'.

        Verifies the adapter catches this via quality validation.
        """
        conn = duckdb.connect(str(tmp_path / "test.duckdb"))
        _load_schema(conn)
        _create_layout_run(conn, RUN_ID, REPO_ID)

        payload = _prep("scc")
        # Tilde path — passes schema regex, fails entity validation
        payload["data"]["files"][0]["path"] = "~/.bashrc"

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scc_repo = SccRepository(conn)
        adapter = SccAdapter(run_repo, layout_repo, scc_repo, Path("/tmp/test-repo"), None)

        with pytest.raises((ValueError, KeyError)):
            adapter.persist(payload)

        conn.close()

    def test_scc_line_components_exceed_total(self, tmp_path: Path) -> None:
        """code + comment + blank > lines passes JSON schema (each is valid
        individually) but fails the adapter's quality validation invariant.
        """
        conn = duckdb.connect(str(tmp_path / "test.duckdb"))
        _load_schema(conn)
        _create_layout_run(conn, RUN_ID, REPO_ID)

        payload = _prep("scc")
        # Each field is valid individually, but sum exceeds total
        payload["data"]["files"][0]["lines"] = 100
        payload["data"]["files"][0]["code"] = 80
        payload["data"]["files"][0]["comment"] = 30
        payload["data"]["files"][0]["blank"] = 20

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scc_repo = SccRepository(conn)
        adapter = SccAdapter(run_repo, layout_repo, scc_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(ValueError, match="quality validation failed"):
            adapter.persist(payload)

        conn.close()

    # ── lizard ───────────────────────────────────────────────────────────

    def test_lizard_valid_fixture_persists(self, tmp_path: Path) -> None:
        """Verify the lizard adapter persists cleanly with valid data."""
        conn = duckdb.connect(str(tmp_path / "test.duckdb"))
        _load_schema(conn)
        _create_layout_run(conn, RUN_ID, REPO_ID)

        payload = _prep("lizard")

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        lizard_repo = LizardRepository(conn)
        adapter = LizardAdapter(run_repo, layout_repo, lizard_repo, Path("/tmp/test-repo"), None)

        run_pk = adapter.persist(payload)
        assert run_pk > 0

        conn.close()

    # ── semgrep ──────────────────────────────────────────────────────────

    def test_semgrep_tilde_path_fails_quality(self, tmp_path: Path) -> None:
        """A tilde path in a semgrep file entry fails quality validation."""
        conn = duckdb.connect(str(tmp_path / "test.duckdb"))
        _load_schema(conn)
        _create_layout_run(conn, RUN_ID, REPO_ID)

        payload = _prep("semgrep")
        payload["data"]["files"][0]["path"] = "~/.config/app.py"

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        semgrep_repo = SemgrepRepository(conn)
        adapter = SemgrepAdapter(run_repo, layout_repo, semgrep_repo, Path("/tmp/test-repo"), None)

        with pytest.raises((ValueError, KeyError)):
            adapter.persist(payload)

        conn.close()

    def test_semgrep_zero_line_start_fails(self, tmp_path: Path) -> None:
        """line_start=0 fails at schema or quality level (must be >= 1)."""
        conn = duckdb.connect(str(tmp_path / "test.duckdb"))
        _load_schema(conn)
        _create_layout_run(conn, RUN_ID, REPO_ID)

        payload = _prep("semgrep")
        # Set line_start to 0 — fails at schema or quality level
        if payload["data"]["files"][0].get("smells"):
            payload["data"]["files"][0]["smells"][0]["line_start"] = 0

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        semgrep_repo = SemgrepRepository(conn)
        adapter = SemgrepAdapter(run_repo, layout_repo, semgrep_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    # ── gitleaks ─────────────────────────────────────────────────────────

    def test_gitleaks_valid_fixture_persists(self, tmp_path: Path) -> None:
        """Verify gitleaks adapter persists cleanly with valid data."""
        conn = duckdb.connect(str(tmp_path / "test.duckdb"))
        _load_schema(conn)
        _create_layout_run(conn, RUN_ID, REPO_ID)

        payload = _prep("gitleaks")

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        gitleaks_repo = GitleaksRepository(conn)
        adapter = GitleaksAdapter(run_repo, layout_repo, gitleaks_repo, Path("/tmp/test-repo"), None)

        run_pk = adapter.persist(payload)
        assert run_pk > 0

        conn.close()

    def test_gitleaks_zero_line_number_fails_quality(self, tmp_path: Path) -> None:
        """line_number=0 passes JSON schema but fails adapter quality (must be >= 1)."""
        conn = duckdb.connect(str(tmp_path / "test.duckdb"))
        _load_schema(conn)
        _create_layout_run(conn, RUN_ID, REPO_ID)

        payload = _prep("gitleaks")
        payload["data"]["findings"][0]["line_number"] = 0

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        gitleaks_repo = GitleaksRepository(conn)
        adapter = GitleaksAdapter(run_repo, layout_repo, gitleaks_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(ValueError, match="quality validation failed"):
            adapter.persist(payload)

        conn.close()

    # ── roslyn-analyzers ─────────────────────────────────────────────────

    def test_roslyn_valid_fixture_persists(self, tmp_path: Path) -> None:
        """Verify roslyn adapter persists cleanly with valid data."""
        conn = duckdb.connect(str(tmp_path / "test.duckdb"))
        _load_schema(conn)
        _create_layout_run(conn, RUN_ID, REPO_ID)

        payload = _prep("roslyn")

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        roslyn_repo = RoslynRepository(conn)
        adapter = RoslynAnalyzersAdapter(run_repo, layout_repo, roslyn_repo, Path("/tmp/test-repo"), None)

        run_pk = adapter.persist(payload)
        assert run_pk > 0

        conn.close()

    def test_roslyn_zero_line_start_fails(self, tmp_path: Path) -> None:
        """line_start=0 in a violation fails at schema or quality level."""
        conn = duckdb.connect(str(tmp_path / "test.duckdb"))
        _load_schema(conn)
        _create_layout_run(conn, RUN_ID, REPO_ID)

        payload = _prep("roslyn")
        if payload["data"]["files"][0].get("violations"):
            payload["data"]["files"][0]["violations"][0]["line_start"] = 0

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        roslyn_repo = RoslynRepository(conn)
        adapter = RoslynAnalyzersAdapter(run_repo, layout_repo, roslyn_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    # ── sonarqube ────────────────────────────────────────────────────────

    def test_sonarqube_valid_fixture_persists(self, tmp_path: Path) -> None:
        """Verify sonarqube adapter persists cleanly with valid data."""
        conn = duckdb.connect(str(tmp_path / "test.duckdb"))
        _load_schema(conn)
        _create_layout_run(conn, RUN_ID, REPO_ID)

        payload = _prep("sonarqube")

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        sonarqube_repo = SonarqubeRepository(conn)
        adapter = SonarqubeAdapter(run_repo, layout_repo, sonarqube_repo, Path("/tmp/test-repo"), None)

        run_pk = adapter.persist(payload)
        assert run_pk > 0

        conn.close()

    # ── git-blame-scanner ────────────────────────────────────────────────

    def test_git_blame_tilde_path_fails_quality(self, tmp_path: Path) -> None:
        """A tilde path in a git-blame-scanner file entry fails quality."""
        conn = duckdb.connect(str(tmp_path / "test.duckdb"))
        _load_schema(conn)
        _create_layout_run(conn, RUN_ID, REPO_ID)

        payload = _prep("git_blame_scanner")
        payload["data"]["files"][0]["path"] = "~/secret.py"

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        git_blame_repo = GitBlameRepository(conn)
        adapter = GitBlameScannerAdapter(run_repo, layout_repo, git_blame_repo, Path("/tmp/test-repo"), None)

        with pytest.raises((ValueError, KeyError)):
            adapter.persist(payload)

        conn.close()

    def test_git_blame_ownership_pct_over_100_fails(self, tmp_path: Path) -> None:
        """top_author_pct > 100 fails at schema or quality level."""
        conn = duckdb.connect(str(tmp_path / "test.duckdb"))
        _load_schema(conn)
        _create_layout_run(conn, RUN_ID, REPO_ID)

        payload = _prep("git_blame_scanner")
        payload["data"]["files"][0]["top_author_pct"] = 150.0

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        git_blame_repo = GitBlameRepository(conn)
        adapter = GitBlameScannerAdapter(run_repo, layout_repo, git_blame_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    # ── trivy ────────────────────────────────────────────────────────────

    def test_trivy_valid_fixture_persists(self, tmp_path: Path) -> None:
        """Verify trivy adapter persists cleanly with valid data."""
        conn = duckdb.connect(str(tmp_path / "test.duckdb"))
        _load_schema(conn)
        _create_layout_run(conn, RUN_ID, REPO_ID)

        payload = _prep("trivy")

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        trivy_repo = TrivyRepository(conn)
        adapter = TrivyAdapter(run_repo, layout_repo, trivy_repo, Path("/tmp/test-repo"), None)

        run_pk = adapter.persist(payload)
        assert run_pk > 0

        conn.close()

    def test_trivy_negative_cvss_score_fails_quality(self, tmp_path: Path) -> None:
        """cvss_score=-1 passes JSON schema (valid number) but should fail
        quality validation (CVSS scores are 0-10).
        """
        conn = duckdb.connect(str(tmp_path / "test.duckdb"))
        _load_schema(conn)
        _create_layout_run(conn, RUN_ID, REPO_ID)

        payload = _prep("trivy")
        if payload["data"].get("vulnerabilities"):
            payload["data"]["vulnerabilities"][0]["cvss_score"] = -1.0

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        trivy_repo = TrivyRepository(conn)
        adapter = TrivyAdapter(run_repo, layout_repo, trivy_repo, Path("/tmp/test-repo"), None)

        # May fail at quality or entity level; either is acceptable
        with pytest.raises((ValueError, KeyError)):
            adapter.persist(payload)

        conn.close()
