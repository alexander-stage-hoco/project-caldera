from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import LayoutScannerAdapter, TrivyAdapter
from persistence.repositories import LayoutRepository, ToolRunRepository, TrivyRepository


def _load_schema(conn: duckdb.DuckDBPyConnection) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "persistence" / "schema.sql"
    conn.execute(schema_path.read_text())


def _create_layout_run(conn: duckdb.DuckDBPyConnection, run_id: str, repo_id: str) -> int:
    """Create a layout run for testing with required files.

    The layout fixture includes trivy-specific files:
    - package-lock.json
    - requirements.txt
    - Dockerfile
    """
    layout_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "layout_output.json"
    layout_payload = json.loads(layout_fixture.read_text())
    layout_payload["metadata"]["repo_id"] = repo_id
    layout_payload["metadata"]["run_id"] = run_id

    run_repo = ToolRunRepository(conn)
    layout_repo = LayoutRepository(conn)
    LayoutScannerAdapter(run_repo, layout_repo, Path("/tmp/test-repo"), None).persist(layout_payload)
    return run_repo.get_run_pk(run_id, "layout-scanner")


class TestTrivyAdapter:
    """Test the Trivy adapter for persisting vulnerability data."""

    def test_persist_vulnerabilities(self, tmp_path: Path) -> None:
        """Test persisting Trivy vulnerabilities to database."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        # Create layout run first
        _create_layout_run(conn, run_id, repo_id)

        # Load trivy fixture
        trivy_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "trivy_output.json"
        trivy_payload = json.loads(trivy_fixture.read_text())

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        trivy_repo = TrivyRepository(conn)

        adapter = TrivyAdapter(
            run_repo,
            layout_repo,
            trivy_repo,
            Path("/tmp/test-repo"),
            None,
        )
        run_pk = adapter.persist(trivy_payload)

        assert run_pk > 0

        # Verify vulnerabilities were inserted
        vuln_count = conn.execute(
            "SELECT COUNT(*) FROM lz_trivy_vulnerabilities WHERE run_pk = ?",
            [run_pk],
        ).fetchone()[0]
        assert vuln_count == 4  # 4 vulnerabilities in fixture

        # Verify targets were inserted
        target_count = conn.execute(
            "SELECT COUNT(*) FROM lz_trivy_targets WHERE run_pk = ?",
            [run_pk],
        ).fetchone()[0]
        assert target_count == 2  # 2 targets in fixture

        # Verify IaC misconfigs were inserted
        iac_count = conn.execute(
            "SELECT COUNT(*) FROM lz_trivy_iac_misconfigs WHERE run_pk = ?",
            [run_pk],
        ).fetchone()[0]
        assert iac_count == 2  # 2 misconfigs in fixture

        conn.close()

    def test_persist_severity_counts(self, tmp_path: Path) -> None:
        """Test that severity counts are correctly persisted."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        _create_layout_run(conn, run_id, repo_id)

        trivy_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "trivy_output.json"
        trivy_payload = json.loads(trivy_fixture.read_text())

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        trivy_repo = TrivyRepository(conn)

        adapter = TrivyAdapter(
            run_repo,
            layout_repo,
            trivy_repo,
            Path("/tmp/test-repo"),
            None,
        )
        run_pk = adapter.persist(trivy_payload)

        # Query npm target severity counts
        npm_target = conn.execute(
            """
            SELECT vulnerability_count, critical_count, high_count, medium_count, low_count
            FROM lz_trivy_targets
            WHERE run_pk = ? AND target_type = 'npm'
            """,
            [run_pk],
        ).fetchone()

        assert npm_target is not None
        assert npm_target[0] == 3  # vulnerability_count
        assert npm_target[1] == 1  # critical_count
        assert npm_target[2] == 1  # high_count
        assert npm_target[3] == 1  # medium_count
        assert npm_target[4] == 0  # low_count

        conn.close()

    def test_validate_quality_invalid_severity(self, tmp_path: Path) -> None:
        """Test that invalid severity values are rejected.

        Note: JSON schema validation catches this before data quality validation
        because the schema defines severity as an enum.
        """
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        _create_layout_run(conn, run_id, repo_id)

        trivy_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "trivy_output.json"
        trivy_payload = json.loads(trivy_fixture.read_text())

        # Modify to have invalid severity (use 'data' key for envelope format)
        trivy_payload["data"]["vulnerabilities"][0]["severity"] = "INVALID"

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        trivy_repo = TrivyRepository(conn)

        adapter = TrivyAdapter(
            run_repo,
            layout_repo,
            trivy_repo,
            Path("/tmp/test-repo"),
            None,
        )

        # Schema validation catches invalid severity values (enum constraint)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(trivy_payload)

        conn.close()

    def test_validate_quality_invalid_cvss(self, tmp_path: Path) -> None:
        """Test that invalid CVSS scores are rejected.

        Note: JSON schema validation catches this before data quality validation
        because the schema defines cvss_score as max 10.
        """
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        _create_layout_run(conn, run_id, repo_id)

        trivy_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "trivy_output.json"
        trivy_payload = json.loads(trivy_fixture.read_text())

        # Modify to have invalid CVSS score (use 'data' key for envelope format)
        trivy_payload["data"]["vulnerabilities"][0]["cvss_score"] = 15.0

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        trivy_repo = TrivyRepository(conn)

        adapter = TrivyAdapter(
            run_repo,
            layout_repo,
            trivy_repo,
            Path("/tmp/test-repo"),
            None,
        )

        # Schema validation catches out-of-range CVSS scores (max 10)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(trivy_payload)

        conn.close()

    def test_validate_quality_missing_required_fields(self, tmp_path: Path) -> None:
        """Test that missing required fields are rejected.

        Note: JSON schema validation catches this before data quality validation
        because the schema defines id as a required field.
        """
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        _create_layout_run(conn, run_id, repo_id)

        trivy_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "trivy_output.json"
        trivy_payload = json.loads(trivy_fixture.read_text())

        # Remove required field (use 'data' key for envelope format)
        del trivy_payload["data"]["vulnerabilities"][0]["id"]

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        trivy_repo = TrivyRepository(conn)

        adapter = TrivyAdapter(
            run_repo,
            layout_repo,
            trivy_repo,
            Path("/tmp/test-repo"),
            None,
        )

        # Schema validation catches missing required fields
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(trivy_payload)

        conn.close()

    def test_target_file_id_linkage(self, tmp_path: Path) -> None:
        """Test that targets correctly link to layout files via file_id."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        _create_layout_run(conn, run_id, repo_id)

        trivy_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "trivy_output.json"
        trivy_payload = json.loads(trivy_fixture.read_text())

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        trivy_repo = TrivyRepository(conn)

        adapter = TrivyAdapter(
            run_repo,
            layout_repo,
            trivy_repo,
            Path("/tmp/test-repo"),
            None,
        )
        run_pk = adapter.persist(trivy_payload)

        # Verify targets can join with layout files
        joined_rows = conn.execute(
            """
            SELECT t.relative_path, lf.relative_path, t.target_type
            FROM lz_trivy_targets t
            JOIN lz_tool_runs tr_trivy
              ON tr_trivy.run_pk = t.run_pk
            JOIN lz_tool_runs tr_layout
              ON tr_layout.collection_run_id = tr_trivy.collection_run_id
             AND tr_layout.tool_name IN ('layout', 'layout-scanner')
            JOIN lz_layout_files lf
              ON lf.run_pk = tr_layout.run_pk
             AND lf.file_id = t.file_id
            WHERE t.run_pk = ?
            ORDER BY t.relative_path
            """,
            [run_pk],
        ).fetchall()

        # package-lock.json and requirements.txt should join
        assert len(joined_rows) == 2
        paths = [row[0] for row in joined_rows]
        assert "package-lock.json" in paths
        assert "requirements.txt" in paths

        conn.close()

    def test_iac_misconfig_start_line_zero(self, tmp_path: Path) -> None:
        """Test that IaC misconfigs with start_line=0 (file-level) persist with -1 sentinel."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        _create_layout_run(conn, run_id, repo_id)

        trivy_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "trivy_output.json"
        trivy_payload = json.loads(trivy_fixture.read_text())

        # Inject a file-level IaC misconfig with start_line=0, end_line=0
        trivy_payload["data"]["iac_misconfigurations"]["misconfigurations"].append(
            {
                "id": "AVD-DS-0099",
                "severity": "LOW",
                "title": "File-level finding",
                "description": "A file-level IaC finding with no specific line",
                "resolution": "Review entire file",
                "target": "Dockerfile",
                "target_type": "dockerfile",
                "start_line": 0,
                "end_line": 0,
            }
        )
        trivy_payload["data"]["iac_misconfigurations"]["count"] = 3

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        trivy_repo = TrivyRepository(conn)

        adapter = TrivyAdapter(
            run_repo,
            layout_repo,
            trivy_repo,
            Path("/tmp/test-repo"),
            None,
        )
        run_pk = adapter.persist(trivy_payload)

        # Verify the file-level misconfig persisted with -1 sentinel
        rows = conn.execute(
            """
            SELECT misconfig_id, start_line, end_line
            FROM lz_trivy_iac_misconfigs
            WHERE run_pk = ? AND misconfig_id = 'AVD-DS-0099'
            """,
            [run_pk],
        ).fetchall()

        assert len(rows) == 1
        assert rows[0][1] == -1  # start_line: 0 → -1
        assert rows[0][2] == -1  # end_line: 0 → -1

        conn.close()

    def test_iac_misconfig_inverted_line_range(self, tmp_path: Path) -> None:
        """Test that IaC misconfigs with end_line < start_line are rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        _create_layout_run(conn, run_id, repo_id)

        trivy_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "trivy_output.json"
        trivy_payload = json.loads(trivy_fixture.read_text())

        # Inject an IaC misconfig with inverted line range (end < start)
        trivy_payload["data"]["iac_misconfigurations"]["misconfigurations"].append(
            {
                "id": "AVD-DS-0098",
                "severity": "MEDIUM",
                "title": "Inverted line range",
                "description": "A misconfig with end_line < start_line",
                "resolution": "Fix line range",
                "target": "Dockerfile",
                "target_type": "dockerfile",
                "start_line": 10,
                "end_line": 5,
            }
        )
        trivy_payload["data"]["iac_misconfigurations"]["count"] = 3

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        trivy_repo = TrivyRepository(conn)

        adapter = TrivyAdapter(
            run_repo,
            layout_repo,
            trivy_repo,
            Path("/tmp/test-repo"),
            None,
        )

        with pytest.raises(ValueError, match="quality validation failed"):
            adapter.persist(trivy_payload)

        conn.close()

    def test_iac_misconfig_mixed_sentinel_line_range(self, tmp_path: Path) -> None:
        """Test that IaC misconfigs with mixed sentinel/real lines are rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        _create_layout_run(conn, run_id, repo_id)

        trivy_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "trivy_output.json"
        trivy_payload = json.loads(trivy_fixture.read_text())

        # Inject an IaC misconfig with mixed sentinel/real line range
        trivy_payload["data"]["iac_misconfigurations"]["misconfigurations"].append(
            {
                "id": "AVD-DS-0099",
                "severity": "HIGH",
                "title": "Mixed sentinel lines",
                "description": "A misconfig with start_line=10 but end_line=0 (sentinel)",
                "resolution": "Fix line range",
                "target": "Dockerfile",
                "target_type": "dockerfile",
                "start_line": 10,
                "end_line": 0,
            }
        )
        trivy_payload["data"]["iac_misconfigurations"]["count"] = 3

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        trivy_repo = TrivyRepository(conn)

        adapter = TrivyAdapter(
            run_repo,
            layout_repo,
            trivy_repo,
            Path("/tmp/test-repo"),
            None,
        )

        with pytest.raises(ValueError, match="quality validation failed"):
            adapter.persist(trivy_payload)

        conn.close()

    def test_iac_misconfig_string_line_values(self, tmp_path: Path) -> None:
        """Test that IaC misconfigs with string line numbers are coerced or rejected.

        When schema validation is unavailable (e.g. schema file missing), string
        line numbers like start_line="10" should be coerced to int, while
        non-numeric values like end_line="abc" should produce a quality error
        instead of a TypeError.
        """
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        _create_layout_run(conn, run_id, repo_id)

        trivy_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "trivy_output.json"
        trivy_payload = json.loads(trivy_fixture.read_text())

        # Inject an IaC misconfig with string line numbers: "10" (coercible) and "abc" (not)
        trivy_payload["data"]["iac_misconfigurations"]["misconfigurations"].append(
            {
                "id": "AVD-DS-0099",
                "severity": "HIGH",
                "title": "String line numbers",
                "description": "A misconfig with string start_line and non-numeric end_line",
                "resolution": "Fix line types",
                "target": "Dockerfile",
                "target_type": "dockerfile",
                "start_line": "10",
                "end_line": "abc",
            }
        )
        trivy_payload["data"]["iac_misconfigurations"]["count"] = 3

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        trivy_repo = TrivyRepository(conn)

        adapter = TrivyAdapter(
            run_repo,
            layout_repo,
            trivy_repo,
            Path("/tmp/test-repo"),
            None,
        )

        # Simulate schema file unavailable so string types reach quality validation
        with patch.object(type(adapter), "schema_path", new_callable=lambda: property(lambda self: None)):
            with pytest.raises(ValueError, match="quality validation failed"):
                adapter.persist(trivy_payload)

        conn.close()

    def test_iac_misconfig_file_linkage(self, tmp_path: Path) -> None:
        """Test that IaC misconfigs correctly link to layout files."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        _create_layout_run(conn, run_id, repo_id)

        trivy_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "trivy_output.json"
        trivy_payload = json.loads(trivy_fixture.read_text())

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        trivy_repo = TrivyRepository(conn)

        adapter = TrivyAdapter(
            run_repo,
            layout_repo,
            trivy_repo,
            Path("/tmp/test-repo"),
            None,
        )
        run_pk = adapter.persist(trivy_payload)

        # Verify IaC misconfigs can join with layout files
        joined_rows = conn.execute(
            """
            SELECT m.relative_path, lf.relative_path, m.misconfig_id, m.severity
            FROM lz_trivy_iac_misconfigs m
            JOIN lz_tool_runs tr_trivy
              ON tr_trivy.run_pk = m.run_pk
            JOIN lz_tool_runs tr_layout
              ON tr_layout.collection_run_id = tr_trivy.collection_run_id
             AND tr_layout.tool_name IN ('layout', 'layout-scanner')
            JOIN lz_layout_files lf
              ON lf.run_pk = tr_layout.run_pk
             AND lf.file_id = m.file_id
            WHERE m.run_pk = ?
            ORDER BY m.misconfig_id
            """,
            [run_pk],
        ).fetchall()

        # Both Dockerfile misconfigs should join
        assert len(joined_rows) == 2
        assert all(row[0] == "Dockerfile" for row in joined_rows)

        conn.close()
