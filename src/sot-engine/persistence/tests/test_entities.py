from datetime import datetime, timezone

import pytest

from persistence.entities import ToolRun


def test_tool_run_accepts_non_uuid_ids() -> None:
    run = ToolRun(
        collection_run_id="keepass2android-run-1",
        repo_id="keepass2android",
        run_id="keepass2android-run-1",
        tool_name="scc",
        tool_version="1.0.0",
        schema_version="1.0.0",
        branch="main",
        commit="c1513bf4d55b61b1b49f638a79e168c67ea3cdf6",
        timestamp=datetime.now(timezone.utc),
    )
    assert run.repo_id == "keepass2android"


def test_tool_run_rejects_blank_repo_id() -> None:
    with pytest.raises(ValueError, match="repo_id must be a non-empty identifier"):
        ToolRun(
            collection_run_id="run-1",
            repo_id="",
            run_id="run-1",
            tool_name="scc",
            tool_version="1.0.0",
            schema_version="1.0.0",
            branch="main",
            commit="c1513bf4d55b61b1b49f638a79e168c67ea3cdf6",
            timestamp=datetime.now(timezone.utc),
        )
