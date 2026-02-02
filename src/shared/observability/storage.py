"""
File storage for LLM interactions.

Persists LLMInteraction records to JSON-Lines files organized by date.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator
import json

from .schemas import LLMInteraction, EvaluationSpan


class FileStore:
    """
    JSON-Lines file storage for LLM interactions.

    Stores interactions in files organized by date:
        {base_dir}/{YYYY-MM-DD}/interactions.jsonl

    Each line in the file is a complete JSON object representing
    one LLMInteraction.
    """

    def __init__(self, base_dir: Path | str = Path("output/llm_logs")):
        """
        Initialize the file store.

        Args:
            base_dir: Base directory for log files
        """
        self.base_dir = Path(base_dir) if isinstance(base_dir, str) else base_dir

    def _get_log_file(self, date: datetime | None = None) -> Path:
        """Get the log file path for a given date."""
        date = date or datetime.now()
        date_dir = self.base_dir / date.strftime("%Y-%m-%d")
        return date_dir / "interactions.jsonl"

    def append(self, interaction: LLMInteraction) -> None:
        """
        Append an interaction to the log file.

        Creates the directory structure if it doesn't exist.
        """
        log_file = self._get_log_file(interaction.timestamp_start)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(interaction.to_json() + "\n")

    def read_date(self, date: datetime | None = None) -> list[LLMInteraction]:
        """
        Read all interactions for a given date.

        Args:
            date: Date to read (defaults to today)

        Returns:
            List of LLMInteraction objects
        """
        log_file = self._get_log_file(date)
        if not log_file.exists():
            return []

        interactions = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    interactions.append(LLMInteraction.from_dict(data))

        return interactions

    def read_range(
        self,
        start_date: datetime,
        end_date: datetime | None = None,
    ) -> Iterator[LLMInteraction]:
        """
        Read interactions from a date range.

        Args:
            start_date: Start of range (inclusive)
            end_date: End of range (inclusive, defaults to today)

        Yields:
            LLMInteraction objects in chronological order
        """
        end_date = end_date or datetime.now()
        current = start_date

        while current <= end_date:
            for interaction in self.read_date(current):
                yield interaction
            current += timedelta(days=1)

    def query_by_trace(self, trace_id: str, date: datetime | None = None) -> list[LLMInteraction]:
        """
        Find all interactions with a given trace_id.

        Args:
            trace_id: The trace ID to search for
            date: Optional date to limit search (searches today if None)

        Returns:
            List of matching LLMInteraction objects
        """
        interactions = self.read_date(date)
        return [i for i in interactions if i.trace_id == trace_id]

    def query_by_trace_in_range(
        self,
        trace_id: str,
        start_date: datetime,
        end_date: datetime | None = None,
    ) -> list[LLMInteraction]:
        """
        Find all interactions with a given trace_id in a date range.

        Args:
            trace_id: The trace ID to search for
            start_date: Start of search range
            end_date: End of search range (defaults to today)

        Returns:
            List of matching LLMInteraction objects
        """
        return [i for i in self.read_range(start_date, end_date) if i.trace_id == trace_id]

    def query_by_judge(
        self,
        judge_name: str,
        date: datetime | None = None,
    ) -> list[LLMInteraction]:
        """
        Find all interactions for a specific judge.

        Args:
            judge_name: The judge name to filter by
            date: Optional date to limit search

        Returns:
            List of matching LLMInteraction objects
        """
        interactions = self.read_date(date)
        return [i for i in interactions if i.judge_name == judge_name]

    def query_by_status(
        self,
        status: str,
        date: datetime | None = None,
    ) -> list[LLMInteraction]:
        """
        Find all interactions with a specific status.

        Args:
            status: Status to filter by ("success", "error", "timeout")
            date: Optional date to limit search

        Returns:
            List of matching LLMInteraction objects
        """
        interactions = self.read_date(date)
        return [i for i in interactions if i.status == status]

    def get_evaluation_span(
        self,
        trace_id: str,
        date: datetime | None = None,
    ) -> EvaluationSpan | None:
        """
        Build an EvaluationSpan from interactions with a given trace_id.

        Args:
            trace_id: The trace ID to search for
            date: Optional date to limit search

        Returns:
            EvaluationSpan or None if no interactions found
        """
        interactions = self.query_by_trace(trace_id, date)
        if not interactions:
            return None

        return EvaluationSpan.from_interactions(trace_id, interactions)

    def list_dates(self) -> list[datetime]:
        """
        List all dates that have log files.

        Returns:
            List of dates with logs, sorted oldest to newest
        """
        if not self.base_dir.exists():
            return []

        dates = []
        for entry in self.base_dir.iterdir():
            if entry.is_dir():
                try:
                    date = datetime.strptime(entry.name, "%Y-%m-%d")
                    dates.append(date)
                except ValueError:
                    continue  # Not a date directory

        return sorted(dates)

    def get_stats(self, date: datetime | None = None) -> dict:
        """
        Get statistics for interactions on a given date.

        Args:
            date: Date to get stats for (defaults to today)

        Returns:
            Dictionary with stats (count, success_count, error_count, etc.)
        """
        interactions = self.read_date(date)

        if not interactions:
            return {
                "date": (date or datetime.now()).strftime("%Y-%m-%d"),
                "total_count": 0,
                "success_count": 0,
                "error_count": 0,
                "timeout_count": 0,
                "unique_traces": 0,
                "judges": {},
                "avg_duration_ms": 0,
            }

        success_count = sum(1 for i in interactions if i.status == "success")
        error_count = sum(1 for i in interactions if i.status == "error")
        timeout_count = sum(1 for i in interactions if i.status == "timeout")
        unique_traces = len(set(i.trace_id for i in interactions))

        # Count by judge
        judges: dict[str, int] = {}
        for i in interactions:
            judge = i.judge_name or "unknown"
            judges[judge] = judges.get(judge, 0) + 1

        # Average duration
        total_duration = sum(i.duration_ms for i in interactions)
        avg_duration = total_duration / len(interactions) if interactions else 0

        return {
            "date": (date or datetime.now()).strftime("%Y-%m-%d"),
            "total_count": len(interactions),
            "success_count": success_count,
            "error_count": error_count,
            "timeout_count": timeout_count,
            "unique_traces": unique_traces,
            "judges": judges,
            "avg_duration_ms": round(avg_duration, 2),
        }

    def cleanup_old_logs(self, retention_days: int) -> int:
        """
        Remove log files older than retention_days.

        Args:
            retention_days: Number of days to retain (0 = no cleanup)

        Returns:
            Number of directories removed
        """
        if retention_days <= 0:
            return 0

        cutoff = datetime.now() - timedelta(days=retention_days)
        removed = 0

        for date_dir in self.base_dir.iterdir():
            if not date_dir.is_dir():
                continue

            try:
                dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                if dir_date < cutoff:
                    # Remove all files in directory
                    for file in date_dir.iterdir():
                        file.unlink()
                    date_dir.rmdir()
                    removed += 1
            except (ValueError, OSError):
                continue

        return removed
