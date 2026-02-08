from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from persistence.adapters import TrivyAdapter
from persistence.entities import LayoutDirectory, LayoutFile, ToolRun
from persistence.repositories import (
    LayoutRepository,
    ToolRunRepository,
    TrivyRepository,
)


def test_trivy_adapter_inserts_vulnerabilities(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter correctly maps vulnerabilities to TrivyVulnerability entities."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "trivy_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Seed layout with files referenced by trivy targets
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000003", "d-000000000001", "package-lock.json"),
            ("f-000000000004", "d-000000000001", "requirements.txt"),
        ],
    )

    trivy_repo = TrivyRepository(duckdb_conn)
    adapter = TrivyAdapter(
        tool_run_repo,
        layout_repo,
        trivy_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify vulnerabilities were inserted
    result = duckdb_conn.execute(
        "SELECT vulnerability_id, package_name, severity, cvss_score FROM lz_trivy_vulnerabilities WHERE run_pk = ?",
        [run_pk],
    ).fetchall()

    assert len(result) == 4  # 4 vulnerabilities in fixture
    vuln_ids = {row[0] for row in result}
    assert "CVE-2024-0001" in vuln_ids
    assert "CVE-2024-0002" in vuln_ids
    assert "CVE-2024-0003" in vuln_ids
    assert "GHSA-abcd-1234" in vuln_ids


def test_trivy_adapter_inserts_targets(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter correctly creates target records with vulnerability counts."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "trivy_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Seed layout with files referenced by trivy targets
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000003", "d-000000000001", "package-lock.json"),
            ("f-000000000004", "d-000000000001", "requirements.txt"),
        ],
    )

    trivy_repo = TrivyRepository(duckdb_conn)
    adapter = TrivyAdapter(
        tool_run_repo,
        layout_repo,
        trivy_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify targets were inserted with correct counts
    result = duckdb_conn.execute(
        """SELECT relative_path, target_type, vulnerability_count, critical_count, high_count
           FROM lz_trivy_targets WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    assert len(result) == 2  # 2 targets in fixture
    targets_by_path = {row[0]: row for row in result}

    # package-lock.json: 3 vulns (1 critical, 1 high, 1 medium)
    assert targets_by_path["package-lock.json"][2] == 3  # vulnerability_count
    assert targets_by_path["package-lock.json"][3] == 1  # critical_count
    assert targets_by_path["package-lock.json"][4] == 1  # high_count

    # requirements.txt: 1 vuln (0 critical, 1 high)
    assert targets_by_path["requirements.txt"][2] == 1  # vulnerability_count
    assert targets_by_path["requirements.txt"][3] == 0  # critical_count
    assert targets_by_path["requirements.txt"][4] == 1  # high_count


def test_trivy_adapter_inserts_iac_misconfigs(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter correctly inserts IaC misconfiguration records."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "trivy_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Seed layout with Dockerfile for IaC findings
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000003", "d-000000000001", "package-lock.json"),
            ("f-000000000004", "d-000000000001", "requirements.txt"),
            ("f-000000000005", "d-000000000001", "Dockerfile"),
        ],
    )

    trivy_repo = TrivyRepository(duckdb_conn)
    adapter = TrivyAdapter(
        tool_run_repo,
        layout_repo,
        trivy_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify IaC misconfigs were inserted
    result = duckdb_conn.execute(
        """SELECT relative_path, misconfig_id, severity, title, start_line
           FROM lz_trivy_iac_misconfigs WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    assert len(result) == 2  # 2 IaC misconfigs in fixture
    misconfig_ids = {row[1] for row in result}
    assert "AVD-DS-0001" in misconfig_ids
    assert "AVD-DS-0002" in misconfig_ids


def test_trivy_adapter_raises_on_missing_layout(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
) -> None:
    """Verify adapter raises KeyError when no layout run exists for collection."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "trivy_output.json"
    payload = json.loads(fixture_path.read_text())

    # Don't seed layout - should raise KeyError
    trivy_repo = TrivyRepository(duckdb_conn)
    adapter = TrivyAdapter(
        tool_run_repo,
        layout_repo,
        trivy_repo,
    )

    with pytest.raises(KeyError):
        adapter.persist(payload)


def test_trivy_adapter_handles_optional_file_linkage(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify targets may have NULL file_id when file not in layout."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "trivy_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Seed layout with only one of the target files
    # package-lock.json will be in layout, requirements.txt will not
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000003", "d-000000000001", "package-lock.json"),
            # requirements.txt intentionally omitted
        ],
    )

    logs: list[str] = []
    trivy_repo = TrivyRepository(duckdb_conn)
    adapter = TrivyAdapter(
        tool_run_repo,
        layout_repo,
        trivy_repo,
        logger=logs.append,
    )
    run_pk = adapter.persist(payload)

    # Verify warning was logged for missing file
    assert any("target not in layout" in log and "requirements.txt" in log for log in logs)

    # Verify targets were still inserted - file_id is nullable for targets
    result = duckdb_conn.execute(
        """SELECT relative_path, file_id FROM lz_trivy_targets WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    targets_by_path = {row[0]: row[1] for row in result}

    # package-lock.json should have file_id
    assert targets_by_path["package-lock.json"] is not None

    # requirements.txt should have NULL file_id
    assert targets_by_path["requirements.txt"] is None
