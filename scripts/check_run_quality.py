#!/usr/bin/env python3
"""Check trust score and warning budget for a collection run.

Used in CI Gate C to enforce quality thresholds after pipeline completion.

Usage:
    python scripts/check_run_quality.py --db ~/.caldera/caldera_sot.duckdb [--min-trust 50]
    python scripts/check_run_quality.py --db ~/.caldera/caldera_sot.duckdb --check-warnings path/to/warnings.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import duckdb


def _check_warnings(warnings_path: Path) -> bool:
    """Validate warnings.json against its embedded budgets. Returns True if passed."""
    if not warnings_path.exists():
        print(f"WARNING: {warnings_path} not found — skipping warning budget check")
        return True

    data = json.loads(warnings_path.read_text(encoding="utf-8"))
    counts = data.get("counts", {})
    budgets = data.get("budgets", {})
    budget_passed = data.get("budget_passed", True)
    total = data.get("total", 0)

    print(f"\nWarning budget check ({warnings_path.name}):")
    print(f"  Total warnings: {total}")

    failed = False
    for category in ("expected_missing", "regression", "degraded"):
        actual = counts.get(category, 0)
        limit = budgets.get(category, 0)
        status = "OK" if actual <= limit else "FAIL"
        print(f"  {category}: {actual}/{limit} [{status}]")
        if actual > limit:
            failed = True

    if failed:
        print("\nFAIL: Warning budget exceeded")
    else:
        print("\nOK: Warning budget passed")

    return not failed


def main() -> int:
    parser = argparse.ArgumentParser(description="Check run quality gates")
    parser.add_argument("--db", required=True, help="Path to DuckDB database")
    parser.add_argument("--min-trust", type=int, default=50, help="Minimum trust score (0-100)")
    parser.add_argument("--collection-run-id", help="Specific collection run ID (default: latest)")
    parser.add_argument("--check-warnings", metavar="PATH", help="Path to warnings.json to validate budget")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"ERROR: Database not found: {db_path}")
        return 1

    conn = duckdb.connect(str(db_path), read_only=True)

    # Get quality summary (latest or specific)
    if args.collection_run_id:
        row = conn.execute(
            "SELECT * FROM lz_run_quality_summary WHERE collection_run_id = ?",
            [args.collection_run_id],
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT qs.* FROM lz_run_quality_summary qs "
            "JOIN lz_collection_runs cr ON cr.collection_run_id = qs.collection_run_id "
            "ORDER BY cr.started_at DESC LIMIT 1"
        ).fetchone()

    if not row:
        print("WARNING: No quality summary found — skipping quality gate")
        return 0

    columns = [desc[0] for desc in conn.description]
    quality = dict(zip(columns, row))
    conn.close()

    trust_score = quality.get("trust_score", 0)
    warning_count = quality.get("warning_count", 0)
    tools_completed = quality.get("tools_completed", 0)
    tools_expected = quality.get("tools_expected", 0)
    tools_failed = quality.get("tools_failed", 0)

    print(f"Trust score:     {trust_score}/100 (minimum: {args.min_trust})")
    print(f"Tools completed: {tools_completed}/{tools_expected}")
    print(f"Tools failed:    {tools_failed}")
    print(f"Warning count:   {warning_count}")

    failed = False

    if trust_score < args.min_trust:
        print(f"\nFAIL: Trust score {trust_score} is below minimum {args.min_trust}")
        failed = True

    if tools_failed > 0:
        print(f"\nWARN: {tools_failed} tool(s) failed")

    # Check warning budget if path provided
    if args.check_warnings:
        if not _check_warnings(Path(args.check_warnings)):
            failed = True

    if not failed:
        print("\nOK: Quality gates passed")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
