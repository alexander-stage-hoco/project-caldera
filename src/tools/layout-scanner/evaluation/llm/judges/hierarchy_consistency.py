"""Hierarchy Consistency Judge for Layout Scanner evaluation.

Evaluates the consistency and correctness of parent-child relationships
in the file/directory hierarchy.
"""

from __future__ import annotations

from typing import Any

from .base import BaseJudge


class HierarchyConsistencyJudge(BaseJudge):
    """Judge that evaluates hierarchy consistency.

    Focuses on:
    - Parent-child ID relationships
    - Depth calculations
    - Recursive count consistency
    - Path coherence with hierarchy
    """

    @property
    def dimension_name(self) -> str:
        return "hierarchy_consistency"

    @property
    def weight(self) -> float:
        return 0.25  # 25% of total LLM score

    def get_default_prompt(self) -> str:
        """Return the default prompt template."""
        return """# Hierarchy Consistency Evaluation

You are evaluating the Layout Scanner's hierarchy consistency.

## Evaluation Dimension: Hierarchy Consistency (Weight: 25%)

### What to Evaluate

1. **Parent-Child Relationships** (35%)
   - Does every file's `parent_directory_id` point to a valid directory?
   - Are directory parent IDs correctly linked?
   - Is the root directory properly identified?

2. **Depth Calculations** (25%)
   - Are `depth` values correct for files and directories?
   - Does depth=0 correspond to root, depth=1 to first level, etc.?
   - Is max_depth in statistics correct?

3. **Count Consistency** (25%)
   - Do `direct_file_count` values match actual child counts?
   - Do `recursive_file_count` values include all descendants?
   - Are size rollups (direct_size_bytes, recursive_size_bytes) consistent?

4. **Path Coherence** (15%)
   - Does the path match the expected position in hierarchy?
   - Are path segments consistent with parent directory names?

## Evidence

### Hierarchy Sample
{{ hierarchy_sample }}

### Statistics
{{ statistics }}

### Parent-Child Relationships
{{ relationships }}

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | All relationships valid, depths correct, counts consistent, paths coherent |
| 4 | 99%+ valid, minor depth or count discrepancies |
| 3 | 95%+ valid, some inconsistencies in counts |
| 2 | 90%+ valid, multiple hierarchy issues |
| 1 | <90% valid, hierarchy unreliable |

## Required Output

Return a JSON object with this structure:
```json
{
    "dimension": "hierarchy_consistency",
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "sub_scores": {
        "parent_child_relationships": <1-5>,
        "depth_calculations": <1-5>,
        "count_consistency": <1-5>,
        "path_coherence": <1-5>
    },
    "evidence_cited": ["<specific examples from the output>"],
    "recommendations": ["<improvements if score < 5>"]
}
```
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence for hierarchy consistency evaluation."""
        outputs = self._load_output_files()

        hierarchy_samples = []
        all_statistics = []
        relationships = []

        for output in outputs:
            repo = output.get("repository", "unknown")
            files = output.get("files", {})
            directories = output.get("directories", {})
            hierarchy = output.get("hierarchy", {})
            statistics = output.get("statistics", {})

            all_statistics.append({"repository": repo, **statistics})

            # Sample hierarchy structure
            if hierarchy:
                hierarchy_samples.append(
                    {
                        "repository": repo,
                        "root_id": hierarchy.get("root_id"),
                        "max_depth": hierarchy.get("max_depth"),
                        "depth_distribution": hierarchy.get("depth_distribution", {}),
                    }
                )

            # Build relationship samples
            dir_by_id = {d.get("id"): d for d in directories.values()}
            file_samples = list(files.values())[:10]

            for f in file_samples:
                parent_id = f.get("parent_directory_id")
                parent = dir_by_id.get(parent_id, {})

                relationships.append(
                    {
                        "repository": repo,
                        "file_path": f.get("path"),
                        "file_depth": f.get("depth"),
                        "parent_id": parent_id,
                        "parent_path": parent.get("path", "NOT_FOUND"),
                        "parent_depth": parent.get("depth", "N/A"),
                    }
                )

            # Sample directory relationships
            dir_samples = list(directories.values())[:10]
            for d in dir_samples:
                relationships.append(
                    {
                        "repository": repo,
                        "dir_path": d.get("path"),
                        "dir_depth": d.get("depth"),
                        "direct_file_count": d.get("direct_file_count"),
                        "recursive_file_count": d.get("recursive_file_count"),
                        "direct_size_bytes": d.get("direct_size_bytes"),
                        "recursive_size_bytes": d.get("recursive_size_bytes"),
                    }
                )

        return {
            "hierarchy_sample": hierarchy_samples,
            "statistics": all_statistics,
            "relationships": relationships[:40],
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions for hierarchy consistency."""
        outputs = self._load_output_files()
        failures = []

        for output in outputs:
            repo = output.get("repository", "unknown")
            files = output.get("files", {})
            directories = output.get("directories", {})

            # Build directory lookup
            dir_by_id = {d.get("id"): d for d in directories.values()}

            # Verify every file has a valid parent
            for f in files.values():
                parent_id = f.get("parent_directory_id")
                if parent_id and parent_id not in dir_by_id:
                    failures.append(
                        f"{repo}: File {f.get('path')} has invalid "
                        f"parent_directory_id {parent_id}"
                    )

            # Verify depth consistency
            for f in files.values():
                path = f.get("path", "")
                depth = f.get("depth", 0)
                expected_depth = path.count("/")

                if depth != expected_depth:
                    failures.append(
                        f"{repo}: File {path} has depth {depth} "
                        f"but path suggests depth {expected_depth}"
                    )

            # Verify directory depths
            for d in directories.values():
                path = d.get("path", "")
                depth = d.get("depth", 0)
                expected_depth = path.count("/") if path else 0

                if depth != expected_depth:
                    failures.append(
                        f"{repo}: Directory {path} has depth {depth} "
                        f"but path suggests depth {expected_depth}"
                    )

            # Verify recursive counts >= direct counts
            for d in directories.values():
                direct = d.get("direct_file_count", 0)
                recursive = d.get("recursive_file_count", 0)

                if recursive < direct:
                    failures.append(
                        f"{repo}: Directory {d.get('path')} has "
                        f"recursive_file_count ({recursive}) < "
                        f"direct_file_count ({direct})"
                    )

        return len(failures) == 0, failures[:20]  # Limit failure count
