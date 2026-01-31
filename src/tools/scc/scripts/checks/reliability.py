"""Reliability checks (RL-1 to RL-8)."""

import json
import subprocess
import hashlib
from pathlib import Path
from typing import List

from . import CheckResult


def _matches_edge_case(location: str, pattern: str) -> bool:
    """Check if location matches an edge case pattern (handles both snake_case and PascalCase)."""
    loc_lower = location.lower()
    # Handle both snake_case (comments_only) and PascalCase (CommentsOnly)
    snake_pattern = pattern.lower()  # e.g., "comments_only"
    pascal_pattern = pattern.lower().replace("_", "")  # e.g., "commentsonly"
    return snake_pattern in loc_lower or pascal_pattern in loc_lower


def run_scc_by_file(base_path: Path, target: str) -> tuple:
    """Run scc with --by-file to get per-file output."""
    scc_path = base_path / "bin" / "scc"
    result = subprocess.run(
        [str(scc_path), target, "--by-file", "-f", "json"],
        capture_output=True,
        text=True,
        cwd=base_path,
        timeout=30
    )
    if result.returncode == 0:
        data = json.loads(result.stdout)
        # Flatten the nested structure: each language entry has a "Files" array
        all_files = []
        for lang_entry in data:
            if "Files" in lang_entry:
                all_files.extend(lang_entry["Files"])
        return all_files, result.returncode, result.stderr
    return [], result.returncode, result.stderr


def check_empty_file_handled(base_path: Path) -> CheckResult:
    """RL-1: Verify empty files are handled (counted, LOC=0)."""
    try:
        files, _, _ = run_scc_by_file(base_path, "eval-repos/synthetic")
        empty_files = [f for f in files if "empty" in f.get("Location", "").lower()]

        # Should find 7 empty files (one per language)
        found_count = len(empty_files)
        expected_count = 7

        # All should have 0 code lines
        all_zero_loc = all(f.get("Code", -1) == 0 for f in empty_files)

        passed = found_count >= expected_count and all_zero_loc

        return CheckResult(
            check_id="RL-1",
            name="Empty File Handled",
            passed=passed,
            message=f"Found {found_count}/{expected_count} empty files, all 0 LOC: {all_zero_loc}",
            expected={"count": expected_count, "all_zero_loc": True},
            actual={"count": found_count, "all_zero_loc": all_zero_loc},
            evidence={"files": [f["Location"] for f in empty_files]}
        )
    except Exception as e:
        return CheckResult(
            check_id="RL-1",
            name="Empty File Handled",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_comments_only_handled(base_path: Path) -> CheckResult:
    """RL-2: Verify comments-only files: Code=0, Comment>0."""
    try:
        files, _, _ = run_scc_by_file(base_path, "eval-repos/synthetic")
        comment_files = [f for f in files if _matches_edge_case(f.get("Location", ""), "comments_only")]

        found_count = len(comment_files)
        expected_count = 7

        # All should have 0 code lines and >0 comment lines
        all_zero_code = all(f.get("Code", -1) == 0 for f in comment_files)
        all_have_comments = all(f.get("Comment", 0) > 0 for f in comment_files)

        passed = found_count >= expected_count and all_zero_code and all_have_comments

        return CheckResult(
            check_id="RL-2",
            name="Comments Only Handled",
            passed=passed,
            message=f"Found {found_count} files, Code=0: {all_zero_code}, Comment>0: {all_have_comments}",
            expected={"count": expected_count, "code_zero": True, "has_comments": True},
            actual={"count": found_count, "code_zero": all_zero_code, "has_comments": all_have_comments},
            evidence={"files": [{"loc": f["Location"], "code": f.get("Code"), "comment": f.get("Comment")} for f in comment_files]}
        )
    except Exception as e:
        return CheckResult(
            check_id="RL-2",
            name="Comments Only Handled",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_single_line_handled(base_path: Path) -> CheckResult:
    """RL-3: Verify single-line files: Code=1."""
    try:
        files, _, _ = run_scc_by_file(base_path, "eval-repos/synthetic")
        single_files = [f for f in files if _matches_edge_case(f.get("Location", ""), "single_line")]

        found_count = len(single_files)
        expected_count = 7

        # All should have 1 code line
        all_one_code = all(f.get("Code", -1) == 1 for f in single_files)

        passed = found_count >= expected_count and all_one_code

        return CheckResult(
            check_id="RL-3",
            name="Single Line Handled",
            passed=passed,
            message=f"Found {found_count} files, Code=1: {all_one_code}",
            expected={"count": expected_count, "code_one": True},
            actual={"count": found_count, "code_one": all_one_code},
            evidence={"files": [{"loc": f["Location"], "code": f.get("Code")} for f in single_files]}
        )
    except Exception as e:
        return CheckResult(
            check_id="RL-3",
            name="Single Line Handled",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_unicode_handled(base_path: Path) -> CheckResult:
    """RL-4: Verify unicode files parse successfully."""
    try:
        files, _, _ = run_scc_by_file(base_path, "eval-repos/synthetic")
        unicode_files = [f for f in files if "unicode" in f.get("Location", "").lower()]

        found_count = len(unicode_files)
        expected_count = 7

        # All should have positive line counts (parsed successfully)
        all_have_lines = all(f.get("Lines", 0) > 0 for f in unicode_files)

        passed = found_count >= expected_count and all_have_lines

        return CheckResult(
            check_id="RL-4",
            name="Unicode Handled",
            passed=passed,
            message=f"Found {found_count} unicode files, all parsed: {all_have_lines}",
            expected={"count": expected_count, "all_parsed": True},
            actual={"count": found_count, "all_parsed": all_have_lines},
            evidence={"files": [{"loc": f["Location"], "lines": f.get("Lines")} for f in unicode_files]}
        )
    except Exception as e:
        return CheckResult(
            check_id="RL-4",
            name="Unicode Handled",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_deep_nesting_handled(base_path: Path) -> CheckResult:
    """RL-5: Verify deep nesting files parse and report complexity."""
    try:
        files, _, _ = run_scc_by_file(base_path, "eval-repos/synthetic")
        nesting_files = [f for f in files if _matches_edge_case(f.get("Location", ""), "deep_nesting")]

        found_count = len(nesting_files)
        expected_count = 7

        # All should have positive complexity
        all_have_complexity = all(f.get("Complexity", 0) > 0 for f in nesting_files)

        passed = found_count >= expected_count and all_have_complexity

        return CheckResult(
            check_id="RL-5",
            name="Deep Nesting Handled",
            passed=passed,
            message=f"Found {found_count} files, complexity reported: {all_have_complexity}",
            expected={"count": expected_count, "has_complexity": True},
            actual={"count": found_count, "has_complexity": all_have_complexity},
            evidence={"files": [{"loc": f["Location"], "complexity": f.get("Complexity")} for f in nesting_files]}
        )
    except Exception as e:
        return CheckResult(
            check_id="RL-5",
            name="Deep Nesting Handled",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_deterministic_output(base_path: Path) -> CheckResult:
    """RL-6: Verify 3 consecutive runs produce identical output."""
    try:
        scc_path = base_path / "bin" / "scc"
        target = "eval-repos/synthetic"

        hashes = []
        for i in range(3):
            result = subprocess.run(
                [str(scc_path), target, "-f", "json"],
                capture_output=True,
                text=True,
                cwd=base_path,
                timeout=30
            )
            if result.returncode == 0:
                # Normalize JSON (sort keys) before hashing
                data = json.loads(result.stdout)
                normalized = json.dumps(data, sort_keys=True)
                hashes.append(hashlib.md5(normalized.encode()).hexdigest())

        all_same = len(set(hashes)) == 1

        return CheckResult(
            check_id="RL-6",
            name="Deterministic Output",
            passed=all_same and len(hashes) == 3,
            message=f"3 runs identical: {all_same}",
            expected="all hashes identical",
            actual=f"unique hashes: {len(set(hashes))}",
            evidence={"hashes": hashes}
        )
    except Exception as e:
        return CheckResult(
            check_id="RL-6",
            name="Deterministic Output",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_all_files_detected(base_path: Path, expected_total: int = 63) -> CheckResult:
    """RL-7: Verify all files are detected."""
    try:
        files, _, _ = run_scc_by_file(base_path, "eval-repos/synthetic")
        found_count = len(files)

        return CheckResult(
            check_id="RL-7",
            name="All Files Detected",
            passed=found_count >= expected_total,
            message=f"Found {found_count}/{expected_total} files",
            expected=expected_total,
            actual=found_count,
            evidence={"file_count": found_count}
        )
    except Exception as e:
        return CheckResult(
            check_id="RL-7",
            name="All Files Detected",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_no_crashes(base_path: Path) -> CheckResult:
    """RL-8: Verify scc exits with code 0."""
    try:
        scc_path = base_path / "bin" / "scc"
        result = subprocess.run(
            [str(scc_path), "eval-repos/synthetic", "-f", "json"],
            capture_output=True,
            text=True,
            cwd=base_path,
            timeout=30
        )

        return CheckResult(
            check_id="RL-8",
            name="No Crashes",
            passed=result.returncode == 0,
            message=f"Exit code: {result.returncode}",
            expected=0,
            actual=result.returncode,
            evidence={"exit_code": result.returncode, "stderr": result.stderr[:200] if result.stderr else ""}
        )
    except Exception as e:
        return CheckResult(
            check_id="RL-8",
            name="No Crashes",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_semantic_consistency(base_path: Path, previous_run_path: Path = None) -> CheckResult:
    """RL-9: Verify semantic consistency between analysis runs.

    Unlike RL-6 which compares hashes, this check compares actual metrics
    to identify which specific values changed between runs.

    Args:
        base_path: Path to the scc tool directory
        previous_run_path: Optional path to previous run output for comparison.
                          If None, will run scc twice and compare.
    """
    try:
        scc_path = base_path / "bin" / "scc"
        target = "eval-repos/synthetic"

        # Run scc to get current results
        current_result = subprocess.run(
            [str(scc_path), target, "-f", "json"],
            capture_output=True,
            text=True,
            cwd=base_path,
            timeout=30
        )

        if current_result.returncode != 0:
            return CheckResult(
                check_id="RL-9",
                name="Semantic Consistency",
                passed=False,
                message=f"Current run failed with exit code {current_result.returncode}",
                evidence={"error": current_result.stderr[:200]}
            )

        current_data = json.loads(current_result.stdout)

        # If previous run path provided, load it; otherwise run again
        if previous_run_path and previous_run_path.exists():
            with open(previous_run_path) as f:
                previous_data = json.load(f)
        else:
            # Run again to compare (should be identical for deterministic tool)
            previous_result = subprocess.run(
                [str(scc_path), target, "-f", "json"],
                capture_output=True,
                text=True,
                cwd=base_path,
                timeout=30
            )
            if previous_result.returncode != 0:
                return CheckResult(
                    check_id="RL-9",
                    name="Semantic Consistency",
                    passed=False,
                    message="Previous run failed",
                    evidence={"error": previous_result.stderr[:200]}
                )
            previous_data = json.loads(previous_result.stdout)

        # Compare semantically - check specific metric differences
        changes = []

        # Build lookup by language
        current_by_lang = {entry.get("Name"): entry for entry in current_data}
        previous_by_lang = {entry.get("Name"): entry for entry in previous_data}

        # Check for new/removed languages
        current_langs = set(current_by_lang.keys())
        previous_langs = set(previous_by_lang.keys())

        added_langs = current_langs - previous_langs
        removed_langs = previous_langs - current_langs

        if added_langs:
            changes.append({"type": "languages_added", "languages": list(added_langs)})
        if removed_langs:
            changes.append({"type": "languages_removed", "languages": list(removed_langs)})

        # Compare metrics for common languages
        common_langs = current_langs & previous_langs
        metrics_to_check = ["Code", "Comment", "Blank", "Lines", "Complexity", "Count"]

        for lang in common_langs:
            current_entry = current_by_lang[lang]
            previous_entry = previous_by_lang[lang]

            for metric in metrics_to_check:
                current_val = current_entry.get(metric, 0)
                previous_val = previous_entry.get(metric, 0)

                if current_val != previous_val:
                    changes.append({
                        "type": "metric_changed",
                        "language": lang,
                        "metric": metric,
                        "previous": previous_val,
                        "current": current_val,
                        "delta": current_val - previous_val
                    })

        passed = len(changes) == 0

        return CheckResult(
            check_id="RL-9",
            name="Semantic Consistency",
            passed=passed,
            message=f"Semantic comparison: {len(changes)} differences found",
            expected="No semantic differences between runs",
            actual=f"changes={len(changes)}",
            evidence={
                "changes": changes[:10],  # Limit to first 10 changes
                "total_changes": len(changes),
                "languages_compared": len(common_langs)
            }
        )
    except Exception as e:
        return CheckResult(
            check_id="RL-9",
            name="Semantic Consistency",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def run_reliability_checks(base_path: Path, previous_run_path: Path = None) -> List[CheckResult]:
    """Run all reliability checks.

    Args:
        base_path: Path to the scc tool directory
        previous_run_path: Optional path to previous run for RL-9 comparison
    """
    return [
        check_empty_file_handled(base_path),
        check_comments_only_handled(base_path),
        check_single_line_handled(base_path),
        check_unicode_handled(base_path),
        check_deep_nesting_handled(base_path),
        check_deterministic_output(base_path),
        check_all_files_detected(base_path),
        check_no_crashes(base_path),
        check_semantic_consistency(base_path, previous_run_path),
    ]
