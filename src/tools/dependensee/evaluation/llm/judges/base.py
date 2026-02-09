"""Base judge class for LLM-as-a-Judge evaluation of DependenSee dependency analysis.

This module re-exports the shared BaseJudge and JudgeResult classes,
and provides DependenSee-specific extensions.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Import from shared module - eliminates duplicate code
from shared.evaluation import BaseJudge as SharedBaseJudge, JudgeResult
from shared.output_management import unwrap_envelope

# Re-export JudgeResult for backwards compatibility
__all__ = ["BaseJudge", "JudgeResult"]


class BaseJudge(SharedBaseJudge):
    """DependenSee-specific base judge for dependency analysis evaluation.

    Extends the shared BaseJudge with DependenSee-specific functionality:
    - Project dependency analysis loading
    - Dependency graph extraction
    """

    def __init__(
        self,
        model: str = "opus-4.5",
        timeout: int = 120,
        working_dir: Path | None = None,
        analysis_path: Path | None = None,
        output_dir: Path | None = None,
        trace_id: str | None = None,
        enable_observability: bool = True,
        evaluation_mode: str | None = None,
    ):
        """Initialize the DependenSee judge.

        Args:
            model: Model name ("sonnet", "opus", "haiku") or full API ID
            timeout: Timeout in seconds for LLM invocation
            working_dir: Working directory for the tool
            analysis_path: Legacy single file path (for backwards compatibility)
            output_dir: Directory containing analysis output files
            trace_id: Correlation ID for linking all judges in one evaluation run
            enable_observability: Whether to log LLM interactions (default True)
            evaluation_mode: Evaluation mode ("synthetic", "real_world", or None for auto-detect)
        """
        super().__init__(
            model=model,
            timeout=timeout,
            working_dir=working_dir,
            output_dir=output_dir or (working_dir or Path.cwd()) / "outputs",
            trace_id=trace_id,
            enable_observability=enable_observability,
            evaluation_mode=evaluation_mode,
        )
        # Legacy single file path (for backwards compatibility)
        self.analysis_path = analysis_path or self.working_dir / "output" / "output.json"

    @property
    def prompt_file(self) -> Path:
        """Path to the prompt template file."""
        return Path(__file__).parent.parent / "prompts" / f"{self.dimension_name}.md"

    def load_all_analysis_results(self) -> dict[str, Any]:
        """Load all analysis JSON files from output_dir.

        Returns dict keyed by repo name (filename stem) -> analysis data.
        Falls back to single analysis_path file if output_dir doesn't exist.
        """
        results = {}

        # Debug: Print what we're looking for
        print(f"  [DEBUG] Looking for analysis files in: {self.output_dir}", file=sys.stderr)

        # Try output_dir first (new pattern)
        if self.output_dir.exists() and self.output_dir.is_dir():
            json_files = list(self.output_dir.glob("*.json"))
            if not json_files:
                json_files = list(self.output_dir.rglob("output.json"))
            print(f"  [DEBUG] Found {len(json_files)} JSON files", file=sys.stderr)
            for json_file in sorted(json_files):
                if json_file.name.startswith("."):
                    continue
                try:
                    data = json.loads(json_file.read_text())
                    repo_name = json_file.parent.name if json_file.name == "output.json" else json_file.stem
                    results[repo_name] = data
                    print(f"  [DEBUG] Loaded: {json_file.name}", file=sys.stderr)
                except json.JSONDecodeError as e:
                    print(f"  [DEBUG] Failed to parse {json_file.name}: {e}", file=sys.stderr)
                    continue
        else:
            print(f"  [DEBUG] output_dir does not exist or is not a directory", file=sys.stderr)

        # Fallback to single file (legacy pattern)
        if not results and self.analysis_path.exists():
            print(f"  [DEBUG] Falling back to single file: {self.analysis_path}", file=sys.stderr)
            try:
                data = json.loads(self.analysis_path.read_text())
                results["default"] = data
            except json.JSONDecodeError:
                pass

        if not results:
            print(f"  [DEBUG] WARNING: No analysis results loaded!", file=sys.stderr)

        return results

    def extract_projects(self, data: dict) -> list[dict]:
        """Extract projects from analysis data."""
        inner = unwrap_envelope(data)
        return inner.get("projects", [])

    def extract_dependency_graph(self, data: dict) -> dict:
        """Extract dependency graph from analysis data."""
        inner = unwrap_envelope(data)
        return inner.get("dependency_graph", {"nodes": [], "edges": []})
