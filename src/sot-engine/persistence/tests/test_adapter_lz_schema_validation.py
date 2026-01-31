from __future__ import annotations

import duckdb
import pytest

from persistence.adapters.scc_adapter import SccAdapter
from persistence.adapters.lizard_adapter import LizardAdapter
from persistence.adapters.layout_adapter import LayoutAdapter
from persistence.adapters.semgrep_adapter import SemgrepAdapter
from persistence.repositories import (
    ToolRunRepository,
    LayoutRepository,
    SccRepository,
    LizardRepository,
    SemgrepRepository,
)


def _empty_conn() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(":memory:")


def test_scc_lz_schema_validation_fails() -> None:
    conn = _empty_conn()
    adapter = SccAdapter(ToolRunRepository(conn), LayoutRepository(conn), SccRepository(conn))
    with pytest.raises(ValueError):
        adapter.validate_lz_schema()


def test_lizard_lz_schema_validation_fails() -> None:
    conn = _empty_conn()
    adapter = LizardAdapter(ToolRunRepository(conn), LayoutRepository(conn), LizardRepository(conn))
    with pytest.raises(ValueError):
        adapter.validate_lz_schema()


def test_layout_lz_schema_validation_fails() -> None:
    conn = _empty_conn()
    adapter = LayoutAdapter(ToolRunRepository(conn), LayoutRepository(conn))
    with pytest.raises(ValueError):
        adapter.validate_lz_schema()


def test_semgrep_lz_schema_validation_fails() -> None:
    conn = _empty_conn()
    adapter = SemgrepAdapter(
        ToolRunRepository(conn),
        LayoutRepository(conn),
        SemgrepRepository(conn),
    )
    with pytest.raises(ValueError):
        adapter.validate_lz_schema()
