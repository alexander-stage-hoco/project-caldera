"""Adapter for git-fame output persistence."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .base_adapter import BaseAdapter
from ..entities import GitFameAuthor, GitFameSummary
from ..repositories import GitFameRepository, LayoutRepository, ToolRunRepository
from ..validation import (
    check_bounded,
    check_non_negative,
    check_required,
)

# Schema path points to the local git-fame tool directory
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "git-fame" / "schemas" / "output.schema.json"

LZ_TABLES = {
    "lz_git_fame_authors": {
        "run_pk": "BIGINT",
        "author_name": "VARCHAR",
        "author_email": "VARCHAR",
        "surviving_loc": "INTEGER",
        "ownership_pct": "DOUBLE",
        "insertions_total": "INTEGER",
        "deletions_total": "INTEGER",
        "commit_count": "INTEGER",
        "files_touched": "INTEGER",
    },
    "lz_git_fame_summary": {
        "run_pk": "BIGINT",
        "repo_id": "VARCHAR",
        "author_count": "INTEGER",
        "total_loc": "INTEGER",
        "hhi_index": "DOUBLE",
        "bus_factor": "INTEGER",
        "top_author_pct": "DOUBLE",
        "top_two_pct": "DOUBLE",
    },
}

TABLE_DDL = {
    "lz_git_fame_authors": """
        CREATE TABLE IF NOT EXISTS lz_git_fame_authors (
            run_pk BIGINT NOT NULL,
            author_name VARCHAR NOT NULL,
            author_email VARCHAR,
            surviving_loc INTEGER NOT NULL,
            ownership_pct DOUBLE NOT NULL,
            insertions_total INTEGER NOT NULL,
            deletions_total INTEGER NOT NULL,
            commit_count INTEGER NOT NULL,
            files_touched INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, author_name)
        )
    """,
    "lz_git_fame_summary": """
        CREATE TABLE IF NOT EXISTS lz_git_fame_summary (
            run_pk BIGINT NOT NULL PRIMARY KEY,
            repo_id VARCHAR NOT NULL,
            author_count INTEGER NOT NULL,
            total_loc INTEGER NOT NULL,
            hhi_index DOUBLE NOT NULL,
            bus_factor INTEGER NOT NULL,
            top_author_pct DOUBLE NOT NULL,
            top_two_pct DOUBLE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
}

QUALITY_RULES = ["hhi_valid", "ownership_sums_100", "bus_factor_valid"]


class GitFameAdapter(BaseAdapter):
    """Adapter for persisting git-fame authorship analysis to the landing zone.

    git-fame provides author-level metrics (not per-file), so this adapter
    handles per-author records plus a summary record per run.
    """

    @property
    def tool_name(self) -> str:
        return "git-fame"

    @property
    def schema_path(self) -> Path | None:
        return SCHEMA_PATH if SCHEMA_PATH.exists() else None

    def validate_schema(self, payload: dict) -> None:
        """Skip native schema validation for Caldera envelope format.

        The git-fame adapter expects Caldera envelope format (metadata/data),
        not the native git-fame output format. Schema validation is skipped
        because the fixture/orchestrator wraps native output in Caldera envelope.
        Data quality validation still runs via validate_quality().
        """
        # Skip JSON schema validation - Caldera envelope format differs from native
        pass

    @property
    def lz_tables(self) -> dict[str, dict[str, str]]:
        return LZ_TABLES

    @property
    def table_ddl(self) -> dict[str, str]:
        return TABLE_DDL

    def __init__(
        self,
        run_repo: ToolRunRepository,
        layout_repo: LayoutRepository | None = None,
        git_fame_repo: GitFameRepository | None = None,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._git_fame_repo = git_fame_repo or GitFameRepository(self._conn)

    def _do_persist(self, payload: dict) -> int:
        """Persist git-fame output to landing zone.

        git-fame output follows Caldera envelope format:
        - metadata: run_id, repo_id, branch, commit, timestamp, etc.
        - data: summary metrics and authors array
        """
        metadata = payload.get("metadata", {})
        data = payload.get("data", {})

        # Validate data quality before persisting
        self.validate_quality(data)

        # Create tool run
        run_pk = self._create_tool_run(metadata)

        # Extract summary metrics
        summary_data = data.get("summary", {})
        summary = GitFameSummary(
            run_pk=run_pk,
            repo_id=metadata["repo_id"],
            author_count=summary_data.get("author_count", 0),
            total_loc=summary_data.get("total_loc", 0),
            hhi_index=summary_data.get("hhi_index", 0.0),
            bus_factor=summary_data.get("bus_factor", 0),
            top_author_pct=summary_data.get("top_author_pct", 0.0),
            top_two_pct=summary_data.get("top_two_pct", 0.0),
        )
        self._git_fame_repo.insert_summary([summary])

        # Persist author records
        # Support both analyze.py output format and fixture format
        authors = [
            GitFameAuthor(
                run_pk=run_pk,
                author_name=a.get("name", a.get("author", "")),
                author_email=a.get("email"),
                surviving_loc=a.get("surviving_loc", a.get("loc", 0)),
                ownership_pct=a.get("ownership_pct", 0.0),
                insertions_total=a.get("insertions_total", a.get("insertions", 0)),
                deletions_total=a.get("deletions_total", a.get("deletions", 0)),
                commit_count=a.get("commit_count", a.get("commits", 0)),
                files_touched=a.get("files_touched", a.get("files", 0)),
            )
            for a in data.get("authors", [])
        ]
        if authors:
            self._git_fame_repo.insert_authors(authors)

        self._log(
            f"Persisted git-fame summary (authors={summary.author_count}, "
            f"loc={summary.total_loc}, bus_factor={summary.bus_factor}, "
            f"hhi={summary.hhi_index:.2f})"
        )

        return run_pk

    def validate_quality(self, data: Any) -> None:
        """Validate git-fame data quality.

        Validates:
        - Summary: hhi_index (0-1), bus_factor non-negative, author_count non-negative
        - Authors: required name/author, ownership_pct (0-100), non-negative metrics
        - Aggregate: ownership_pct values sum to ~100%
        """
        errors = []

        summary = data.get("summary", {})

        # Summary validations
        errors.extend(check_bounded(summary.get("hhi_index"), 0, 1, "summary.hhi_index"))
        errors.extend(check_non_negative(summary.get("bus_factor"), "summary.bus_factor"))
        errors.extend(check_non_negative(summary.get("author_count"), "summary.author_count"))
        errors.extend(check_non_negative(summary.get("total_loc"), "summary.total_loc"))
        errors.extend(check_bounded(summary.get("top_author_pct"), 0, 100, "summary.top_author_pct"))
        errors.extend(check_bounded(summary.get("top_two_pct"), 0, 100, "summary.top_two_pct"))

        # Bus factor vs author_count invariant
        bus_factor = summary.get("bus_factor", 0)
        author_count = summary.get("author_count", 0)
        if author_count > 0 and bus_factor > author_count:
            errors.append(f"bus_factor ({bus_factor}) cannot exceed author_count ({author_count})")

        # Per-author validation
        authors = data.get("authors", [])
        for i, a in enumerate(authors):
            prefix = f"authors[{i}]"

            # Required fields - support both "name" (analyze.py) and "author" (fixture) field names
            author_name = a.get("name", a.get("author"))
            errors.extend(check_required(author_name, f"{prefix}.name/author"))

            # Bounded metrics
            errors.extend(check_bounded(a.get("ownership_pct"), 0, 100, f"{prefix}.ownership_pct"))

            # Non-negative metrics
            errors.extend(check_non_negative(
                a.get("surviving_loc", a.get("loc")),
                f"{prefix}.surviving_loc",
            ))
            errors.extend(check_non_negative(
                a.get("commit_count", a.get("commits")),
                f"{prefix}.commit_count",
            ))
            errors.extend(check_non_negative(
                a.get("files_touched", a.get("files")),
                f"{prefix}.files_touched",
            ))
            errors.extend(check_non_negative(
                a.get("insertions_total", a.get("insertions")),
                f"{prefix}.insertions_total",
            ))
            errors.extend(check_non_negative(
                a.get("deletions_total", a.get("deletions")),
                f"{prefix}.deletions_total",
            ))

        # Aggregate ownership validation
        total_ownership = sum(a.get("ownership_pct", 0) for a in authors)
        if authors and abs(total_ownership - 100.0) > 0.5:
            errors.append(f"ownership_pct values should sum to ~100%, got {total_ownership:.2f}%")

        self._raise_quality_errors(errors)
