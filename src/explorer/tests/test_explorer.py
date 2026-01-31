from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT_SRC = Path(__file__).resolve().parents[2]
if str(ROOT_SRC) not in sys.path:
    sys.path.append(str(ROOT_SRC))

from explorer import explorer


def test_query_requires_sql(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["explorer.py", "query", ""])
    with pytest.raises(SystemExit, match="Provide a SQL query"):
        explorer.main()
