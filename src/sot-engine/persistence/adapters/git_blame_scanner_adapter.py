"""Adapter for persisting git-blame-scanner output to the landing zone.

git-blame-scanner provides per-file authorship metrics for knowledge concentration
and bus factor analysis at the file level.

Output structure:
- data.files[]: Per-file authorship metrics
- data.authors[]: Per-author aggregate statistics
- data.summary: Repository-level summary
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from .base_adapter import BaseAdapter
from ..entities import GitBlameAuthorStats, GitBlameFileSummary
from ..repositories import GitBlameRepository, LayoutRepository, ToolRunRepository
from common.path_normalization import is_repo_relative_path, normalize_file_path
from ..validation import (
    check_bounded,
    check_non_negative,
    check_required,
)

# Path to the tool's JSON schema for validation
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "git-blame-scanner" / "schemas" / "output.schema.json"

# Landing zone table column definitions
LZ_TABLES = {
    "lz_git_blame_summary": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "total_lines": "INTEGER",
        "unique_authors": "INTEGER",
        "top_author": "VARCHAR",
        "top_author_lines": "INTEGER",
        "top_author_pct": "DOUBLE",
        "last_modified": "DATE",
        "churn_30d": "INTEGER",
        "churn_90d": "INTEGER",
    },
    "lz_git_blame_author_stats": {
        "run_pk": "BIGINT",
        "author_email": "VARCHAR",
        "total_files": "INTEGER",
        "total_lines": "INTEGER",
        "exclusive_files": "INTEGER",
        "avg_ownership_pct": "DOUBLE",
    },
}

TABLE_DDL = {
    "lz_git_blame_summary": """
        CREATE TABLE IF NOT EXISTS lz_git_blame_summary (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            total_lines INTEGER NOT NULL,
            unique_authors INTEGER NOT NULL,
            top_author VARCHAR NOT NULL,
            top_author_lines INTEGER NOT NULL,
            top_author_pct DOUBLE NOT NULL,
            last_modified DATE,
            churn_30d INTEGER NOT NULL,
            churn_90d INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, file_id)
        )
    """,
    "lz_git_blame_author_stats": """
        CREATE TABLE IF NOT EXISTS lz_git_blame_author_stats (
            run_pk BIGINT NOT NULL,
            author_email VARCHAR NOT NULL,
            total_files INTEGER NOT NULL,
            total_lines INTEGER NOT NULL,
            exclusive_files INTEGER NOT NULL,
            avg_ownership_pct DOUBLE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, author_email)
        )
    """,
}

QUALITY_RULES = ["paths", "ownership_valid", "churn_monotonic", "authors_positive"]


class GitBlameScannerAdapter(BaseAdapter):
    """Adapter for persisting git-blame-scanner output to the landing zone.

    Handles two types of records:
    1. Per-file summaries (lz_git_blame_summary)
    2. Per-author statistics (lz_git_blame_author_stats)
    """

    @property
    def tool_name(self) -> str:
        return "git-blame-scanner"

    @property
    def schema_path(self) -> Path | None:
        return SCHEMA_PATH if SCHEMA_PATH.exists() else None

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
        git_blame_repo: GitBlameRepository | None = None,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._git_blame_repo = git_blame_repo or GitBlameRepository(self._conn)

    def _do_persist(self, payload: dict) -> int:
        """Persist git-blame-scanner output to landing zone."""
        metadata = payload.get("metadata", {})
        data = payload.get("data", {})

        # Validate data quality before persisting
        self.validate_quality(data)

        # Create tool run
        run_pk = self._create_tool_run(metadata)
        layout_run_pk = self._get_layout_run_pk(metadata["run_id"])

        # Persist file summaries
        file_summaries = list(self._map_file_summaries(
            run_pk, layout_run_pk, data.get("files", [])
        ))
        self._git_blame_repo.insert_file_summaries(file_summaries)

        # Persist author statistics
        author_stats = list(self._map_author_stats(run_pk, data.get("authors", [])))
        self._git_blame_repo.insert_author_stats(author_stats)

        summary = data.get("summary", {})
        self._log(
            f"Persisted git-blame-scanner (files={summary.get('total_files_analyzed', 0)}, "
            f"authors={summary.get('total_authors', 0)}, "
            f"silos={summary.get('knowledge_silo_count', 0)})"
        )

        return run_pk

    def validate_quality(self, data: Any) -> None:
        """Validate git-blame-scanner data quality.

        Validates:
        - Paths are repo-relative
        - Ownership percentages are valid (0-100)
        - Churn is monotonic (30d <= 90d)
        - Unique authors >= 1
        """
        errors = []

        files = data.get("files", [])
        for idx, entry in enumerate(files):
            prefix = f"files[{idx}]"

            # Path validation
            raw_path = entry.get("path", "")
            normalized = normalize_file_path(raw_path, self._repo_root)
            if not is_repo_relative_path(normalized):
                errors.append(f"{prefix}.path invalid: {raw_path}")

            # Non-negative metrics
            errors.extend(check_non_negative(
                entry.get("total_lines"), f"{prefix}.total_lines"
            ))
            errors.extend(check_non_negative(
                entry.get("unique_authors"), f"{prefix}.unique_authors"
            ))
            errors.extend(check_non_negative(
                entry.get("top_author_lines"), f"{prefix}.top_author_lines"
            ))
            errors.extend(check_non_negative(
                entry.get("churn_30d"), f"{prefix}.churn_30d"
            ))
            errors.extend(check_non_negative(
                entry.get("churn_90d"), f"{prefix}.churn_90d"
            ))

            # Bounded metrics
            errors.extend(check_bounded(
                entry.get("top_author_pct"), 0, 100, f"{prefix}.top_author_pct"
            ))

            # Unique authors must be >= 1
            unique_authors = entry.get("unique_authors", 0)
            if unique_authors < 1:
                errors.append(f"{prefix}.unique_authors must be >= 1, got {unique_authors}")

            # Churn invariant: 30d <= 90d
            churn_30d = entry.get("churn_30d", 0)
            churn_90d = entry.get("churn_90d", 0)
            if churn_30d > churn_90d:
                errors.append(
                    f"{prefix} churn_30d ({churn_30d}) > churn_90d ({churn_90d})"
                )

            # Required fields
            errors.extend(check_required(entry.get("top_author"), f"{prefix}.top_author"))

        # Validate author statistics
        authors = data.get("authors", [])
        for idx, author in enumerate(authors):
            prefix = f"authors[{idx}]"

            errors.extend(check_required(
                author.get("author_email"), f"{prefix}.author_email"
            ))
            errors.extend(check_non_negative(
                author.get("total_files"), f"{prefix}.total_files"
            ))
            errors.extend(check_non_negative(
                author.get("total_lines"), f"{prefix}.total_lines"
            ))
            errors.extend(check_non_negative(
                author.get("exclusive_files"), f"{prefix}.exclusive_files"
            ))
            errors.extend(check_bounded(
                author.get("avg_ownership_pct"), 0, 100, f"{prefix}.avg_ownership_pct"
            ))

            # Invariant: exclusive_files <= total_files
            exclusive = author.get("exclusive_files", 0)
            total = author.get("total_files", 0)
            if exclusive > total:
                errors.append(
                    f"{prefix} exclusive_files ({exclusive}) > total_files ({total})"
                )

        self._raise_quality_errors(errors)

    def _map_file_summaries(
        self, run_pk: int, layout_run_pk: int, files: Iterable[dict]
    ) -> Iterable[GitBlameFileSummary]:
        """Map raw file entries to GitBlameFileSummary entities."""
        for entry in files:
            relative_path = self._normalize_path(entry.get("path", ""))
            file_id, directory_id = self._layout_repo.get_file_record(
                layout_run_pk, relative_path
            )

            # Handle last_modified - convert "unknown" to None
            last_modified = entry.get("last_modified")
            if last_modified == "unknown":
                last_modified = None

            yield GitBlameFileSummary(
                run_pk=run_pk,
                file_id=file_id,
                directory_id=directory_id,
                relative_path=relative_path,
                total_lines=entry.get("total_lines", 0),
                unique_authors=entry.get("unique_authors", 1),
                top_author=entry.get("top_author", "unknown"),
                top_author_lines=entry.get("top_author_lines", 0),
                top_author_pct=entry.get("top_author_pct", 0.0),
                last_modified=last_modified,
                churn_30d=entry.get("churn_30d", 0),
                churn_90d=entry.get("churn_90d", 0),
            )

    def _map_author_stats(
        self, run_pk: int, authors: Iterable[dict]
    ) -> Iterable[GitBlameAuthorStats]:
        """Map raw author entries to GitBlameAuthorStats entities."""
        for entry in authors:
            yield GitBlameAuthorStats(
                run_pk=run_pk,
                author_email=entry.get("author_email", "unknown"),
                total_files=entry.get("total_files", 0),
                total_lines=entry.get("total_lines", 0),
                exclusive_files=entry.get("exclusive_files", 0),
                avg_ownership_pct=entry.get("avg_ownership_pct", 0.0),
            )
