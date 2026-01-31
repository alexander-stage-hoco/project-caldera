from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import duckdb
import pytest

from datetime import datetime

from persistence.entities import LayoutDirectory, LayoutFile, ToolRun
from persistence.repositories import LayoutRepository, ToolRunRepository


def _load_schema(conn: duckdb.DuckDBPyConnection) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"
    conn.execute(schema_path.read_text())


@pytest.fixture
def duckdb_conn() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(":memory:")
    _load_schema(conn)
    conn.execute("PRAGMA enable_verification")
    return conn


@pytest.fixture
def tool_run_repo(duckdb_conn: duckdb.DuckDBPyConnection) -> ToolRunRepository:
    return ToolRunRepository(duckdb_conn)


@pytest.fixture
def layout_repo(duckdb_conn: duckdb.DuckDBPyConnection) -> LayoutRepository:
    return LayoutRepository(duckdb_conn)


@pytest.fixture
def seed_layout(
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
):
    def _seed(
        repo_id: str,
        run_id: str,
        layout_files: list[tuple[str, str, str]],
    ) -> int:
        run_pk = tool_run_repo.insert(
            ToolRun(
                collection_run_id=run_id,
                repo_id=repo_id,
                run_id=run_id,
                tool_name="layout",
                tool_version="1.0.0",
                schema_version="1.0.0",
                branch="main",
                commit="c" * 40,
                timestamp=datetime(2026, 1, 25, 9, 0, 0),
            )
        )

        files = [
            LayoutFile(
                run_pk=run_pk,
                file_id=file_id,
                relative_path=path,
                directory_id=directory_id,
                filename=path.split("/")[-1],
                extension=f".{path.split('.')[-1]}",
                language="Python",
                category="source",
                size_bytes=1024,
                line_count=10,
                is_binary=False,
            )
            for file_id, directory_id, path in layout_files
        ]
        layout_repo.insert_files(files)

        directories = [
            LayoutDirectory(
                run_pk=run_pk,
                directory_id="d-000000000002",
                relative_path="src",
                parent_id=None,
                depth=1,
                file_count=1,
                total_size_bytes=1024,
            ),
            LayoutDirectory(
                run_pk=run_pk,
                directory_id="d-000000000003",
                relative_path="src/utils",
                parent_id="d-000000000002",
                depth=2,
                file_count=1,
                total_size_bytes=1024,
            ),
        ]
        layout_repo.insert_directories(directories)
        return run_pk

    return _seed
