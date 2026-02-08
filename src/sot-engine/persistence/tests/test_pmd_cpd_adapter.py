from __future__ import annotations

import json
from pathlib import Path

import pytest

from persistence.adapters import PmdCpdAdapter
from persistence.repositories import (
    LayoutRepository,
    PmdCpdRepository,
    ToolRunRepository,
)


def test_pmd_cpd_adapter_inserts_file_metrics(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter correctly persists per-file duplication metrics."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "pmd_cpd_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Seed layout with files referenced by pmd-cpd
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000002", "src/app.py"),
            ("f-000000000002", "d-000000000002", "src/utils.py"),
            ("f-000000000003", "d-000000000002", "src/helpers.py"),
        ],
    )

    pmd_cpd_repo = PmdCpdRepository(duckdb_conn)
    adapter = PmdCpdAdapter(
        tool_run_repo,
        layout_repo,
        pmd_cpd_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify file metrics were inserted
    result = duckdb_conn.execute(
        """SELECT relative_path, total_lines, duplicate_lines, duplication_percentage
           FROM lz_pmd_cpd_file_metrics WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    assert len(result) == 3  # 3 files in fixture
    metrics_by_path = {row[0]: row for row in result}

    assert metrics_by_path["src/app.py"][1] == 100  # total_lines
    assert metrics_by_path["src/app.py"][2] == 30  # duplicate_lines
    assert metrics_by_path["src/app.py"][3] == 30.0  # duplication_percentage


def test_pmd_cpd_adapter_inserts_duplications(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter correctly persists clone group records."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "pmd_cpd_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000002", "src/app.py"),
            ("f-000000000002", "d-000000000002", "src/utils.py"),
            ("f-000000000003", "d-000000000002", "src/helpers.py"),
        ],
    )

    pmd_cpd_repo = PmdCpdRepository(duckdb_conn)
    adapter = PmdCpdAdapter(
        tool_run_repo,
        layout_repo,
        pmd_cpd_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify duplications were inserted
    result = duckdb_conn.execute(
        """SELECT clone_id, lines, tokens, occurrence_count, is_cross_file
           FROM lz_pmd_cpd_duplications WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    assert len(result) == 2  # 2 duplications in fixture
    dups_by_id = {row[0]: row for row in result}

    # CPD-0001 is cross-file (app.py + utils.py)
    assert dups_by_id["CPD-0001"][1] == 15  # lines
    assert dups_by_id["CPD-0001"][2] == 75  # tokens
    assert dups_by_id["CPD-0001"][3] == 2  # occurrence_count
    assert dups_by_id["CPD-0001"][4] is True  # is_cross_file

    # CPD-0002 is same-file (both in app.py)
    assert dups_by_id["CPD-0002"][4] is False  # is_cross_file


def test_pmd_cpd_adapter_inserts_occurrences(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter correctly persists individual clone locations."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "pmd_cpd_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000002", "src/app.py"),
            ("f-000000000002", "d-000000000002", "src/utils.py"),
            ("f-000000000003", "d-000000000002", "src/helpers.py"),
        ],
    )

    pmd_cpd_repo = PmdCpdRepository(duckdb_conn)
    adapter = PmdCpdAdapter(
        tool_run_repo,
        layout_repo,
        pmd_cpd_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify occurrences were inserted
    result = duckdb_conn.execute(
        """SELECT clone_id, relative_path, line_start, line_end
           FROM lz_pmd_cpd_occurrences WHERE run_pk = ?
           ORDER BY clone_id, line_start""",
        [run_pk],
    ).fetchall()

    assert len(result) == 4  # 4 occurrences total (2 for each duplication)

    # Verify CPD-0001 occurrences link to correct files
    cpd_0001_occs = [r for r in result if r[0] == "CPD-0001"]
    assert len(cpd_0001_occs) == 2
    occ_paths = {r[1] for r in cpd_0001_occs}
    assert "src/app.py" in occ_paths
    assert "src/utils.py" in occ_paths


def test_pmd_cpd_adapter_raises_on_missing_layout(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
) -> None:
    """Verify adapter raises KeyError when no layout run exists."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "pmd_cpd_output.json"
    payload = json.loads(fixture_path.read_text())

    pmd_cpd_repo = PmdCpdRepository(duckdb_conn)
    adapter = PmdCpdAdapter(
        tool_run_repo,
        layout_repo,
        pmd_cpd_repo,
    )

    with pytest.raises(KeyError):
        adapter.persist(payload)
