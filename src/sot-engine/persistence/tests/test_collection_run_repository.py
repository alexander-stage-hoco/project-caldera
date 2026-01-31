from datetime import datetime, timezone

from persistence.entities import CollectionRun
from persistence.repositories import CollectionRunRepository


def test_collection_run_repository_get_insert(duckdb_conn) -> None:
    repo = CollectionRunRepository(duckdb_conn)
    run = CollectionRun(
        collection_run_id="run-123",
        repo_id="repo-1",
        run_id="run-123",
        branch="main",
        commit="a" * 40,
        started_at=datetime.now(timezone.utc),
        completed_at=None,
        status="running",
    )
    repo.insert(run)
    fetched = repo.get_by_repo_commit("repo-1", "a" * 40)
    assert fetched is not None
    assert fetched.collection_run_id == "run-123"
