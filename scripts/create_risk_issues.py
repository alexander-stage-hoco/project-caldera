#!/usr/bin/env python3
"""Create GitHub issues from risk register entries using the gh CLI.

Reads high/critical risks from lz_risks in DuckDB and creates GitHub issues.
Dry-run by default — use ``--apply`` to actually create issues.

Usage::

    # Dry-run: preview issues that would be created
    python scripts/create_risk_issues.py --db ~/.caldera/caldera_sot.duckdb

    # Create issues for a specific run
    python scripts/create_risk_issues.py --db ~/.caldera/caldera_sot.duckdb \\
        --collection-run-id <uuid> --apply

    # Only critical risks
    python scripts/create_risk_issues.py --db ~/.caldera/caldera_sot.duckdb \\
        --min-severity critical --apply
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import duckdb

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
DEFAULT_LABELS = ["risk", "caldera"]


def _fetch_risks(
    conn: duckdb.DuckDBPyConnection,
    collection_run_id: str | None,
    min_severity: str,
) -> list[dict[str, str | None]]:
    """
    Retrieve risk records from `lz_risks` whose severity is at or above `min_severity`.
    
    If `collection_run_id` is provided, fetches risks for that run; otherwise selects risks from the latest collection run. Results are ordered by severity priority (critical, high, medium, low) and, when selecting the latest run, by collection run start time.
    
    Parameters:
        conn: DuckDB connection to execute the query.
        collection_run_id (str | None): Specific collection_run_id to filter by, or None to use the latest run.
        min_severity (str): Minimum severity threshold ("critical", "high", "medium", or "low").
    
    Returns:
        list[dict[str, str | None]]: A list of risk records where each dict contains:
            - "risk_id": risk identifier.
            - "description": human-readable description of the risk.
            - "technical_cause": technical root cause text, if any.
            - "manifests_in": affected manifests/locations (may be None or a delimited string).
            - "triggered_by": triggering entity or signal.
            - "severity": severity label.
            - "action": suggested action text, if any.
            - "sla_date": SLA or target remediation date, if any.
            - "status": risk status (e.g., "open"), if any.
    """
    threshold = SEVERITY_ORDER.get(min_severity, 1)
    allowed = [s for s, v in SEVERITY_ORDER.items() if v <= threshold]
    placeholders = ", ".join("?" for _ in allowed)

    if collection_run_id:
        query = f"""
            SELECT risk_id, description, technical_cause, manifests_in,
                   triggered_by, severity, action, sla_date, status
            FROM lz_risks
            WHERE collection_run_id = ?
              AND severity IN ({placeholders})
            ORDER BY
                CASE severity
                    WHEN 'critical' THEN 0
                    WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'low' THEN 3
                END
        """
        params = [collection_run_id, *allowed]
    else:
        # Pick the latest collection run
        query = f"""
            SELECT r.risk_id, r.description, r.technical_cause, r.manifests_in,
                   r.triggered_by, r.severity, r.action, r.sla_date, r.status
            FROM lz_risks r
            JOIN lz_collection_runs cr ON r.collection_run_id = cr.collection_run_id
            WHERE r.severity IN ({placeholders})
            ORDER BY cr.started_at DESC,
                CASE r.severity
                    WHEN 'critical' THEN 0
                    WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'low' THEN 3
                END
        """
        params = list(allowed)

    rows = conn.execute(query, params).fetchall()
    results: list[dict[str, str | None]] = []
    for row in rows:
        results.append({
            "risk_id": row[0],
            "description": row[1],
            "technical_cause": row[2],
            "manifests_in": row[3],
            "triggered_by": row[4],
            "severity": row[5],
            "action": row[6],
            "sla_date": row[7],
            "status": row[8],
        })
    return results


def _build_issue_title(risk: dict[str, str | None]) -> str:
    """
    Builds a GitHub issue title from a risk record.
    
    Parameters:
        risk (dict): Risk record containing at least the keys 'risk_id' and 'description'.
    
    Returns:
        str: Issue title in the format "[<risk_id>] <description>".
    """
    return f"[{risk['risk_id']}] {risk['description']}"


def _build_issue_body(risk: dict[str, str | None]) -> str:
    """
    Builds a Markdown-formatted GitHub issue body describing the given risk entry.
    
    Parameters:
        risk (dict[str, str | None]): Risk record containing keys:
            - 'triggered_by': entity that triggered the risk.
            - 'severity': severity label.
            - 'status': current status (may be None).
            - 'description': human-readable description (may be None).
            - 'technical_cause': technical cause text (may be None).
            - 'action' (optional): suggested action text.
            - 'sla_date' (optional): SLA date string.
            - 'manifests_in' (optional): comma-separated affected locations.
    
    Returns:
        str: A Markdown string for a GitHub issue body that includes:
            - a header for the triggering entity,
            - severity and status (defaults status to 'open' if missing),
            - Description and Technical Cause sections,
            - optional Suggested Action and SLA Date,
            - an Affected Locations list showing up to 10 items with a note if more exist,
            - and a footer crediting Project Caldera.
    """
    lines = [
        f"## {risk['triggered_by']}",
        "",
        f"**Severity:** {risk['severity']}",
        f"**Status:** {risk['status'] or 'open'}",
        "",
        "### Description",
        "",
        risk["description"] or "",
        "",
        "### Technical Cause",
        "",
        risk["technical_cause"] or "Not specified",
        "",
    ]

    if risk.get("action"):
        lines += ["### Suggested Action", "", risk["action"], ""]

    if risk.get("sla_date"):
        lines += [f"**SLA Date:** {risk['sla_date']}", ""]

    manifests = risk.get("manifests_in") or ""
    if manifests:
        locations = [loc.strip() for loc in manifests.split(",") if loc.strip()]
        if locations:
            lines += ["### Affected Locations", ""]
            for loc in locations[:10]:
                lines.append(f"- `{loc}`")
            if len(locations) > 10:
                lines.append(f"- ... and {len(locations) - 10} more")
            lines.append("")

    lines += [
        "---",
        "*Generated by [Project Caldera](https://github.com/alexander-stage-hoco/project-caldera) risk register*",
    ]
    return "\n".join(lines)


def _existing_issue_titles(repo: str | None) -> set[str]:
    """
    Retrieve titles of existing GitHub issues labeled "caldera" to detect duplicates.
    
    Parameters:
    	repo (str | None): Optional repository in "owner/name" format to scope the search. If None, searches the default CLI repository context.
    
    Returns:
    	titles (set[str]): A set of issue titles; returns an empty set if the gh CLI call fails or output cannot be parsed.
    """
    cmd = ["gh", "issue", "list", "--label", "caldera", "--state", "all", "--json", "title", "--limit", "200"]
    if repo:
        cmd += ["--repo", repo]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return set()

    try:
        issues = json.loads(result.stdout)
        return {issue["title"] for issue in issues}
    except (json.JSONDecodeError, KeyError):
        return set()


def _create_issue(
    title: str,
    body: str,
    labels: list[str],
    repo: str | None,
) -> str | None:
    """
    Create a GitHub issue using the GitHub CLI (gh).
    
    Returns:
        issue URL (str) on success, `None` on failure.
    """
    cmd = ["gh", "issue", "create", "--title", title, "--body", body]
    for label in labels:
        cmd += ["--label", label]
    if repo:
        cmd += ["--repo", repo]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}", file=sys.stderr)
        return None
    return result.stdout.strip()


def main() -> int:
    """
    Create GitHub issues from risk register entries in a DuckDB file according to CLI arguments.
    
    Parses command-line options (--db, --collection-run-id, --min-severity, --repo, --apply), reads matching risks from the specified DuckDB, and for each risk builds an issue title, body, and labels. In apply mode, deduplicates against existing issues (label "caldera") and creates missing issues via the GitHub CLI, printing created issue URLs; in dry-run mode, prints what would be created without making changes. Prints a summary and exits with an appropriate code.
    
    Returns:
        exit_code (int): 0 on success (including no matching risks), 1 if the specified DuckDB file is not found.
    """
    parser = argparse.ArgumentParser(
        description="Create GitHub issues from risk register entries."
    )
    parser.add_argument("--db", required=True, help="Path to DuckDB file")
    parser.add_argument(
        "--collection-run-id",
        default=None,
        help="Specific collection run ID (default: latest)",
    )
    parser.add_argument(
        "--min-severity",
        default="high",
        choices=["critical", "high", "medium", "low"],
        help="Minimum severity to create issues for (default: high)",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="GitHub repo (owner/name) to create issues in (default: current repo)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Actually create issues (default: dry-run)",
    )
    args = parser.parse_args()

    db_path = Path(args.db).expanduser().resolve()
    if not db_path.exists():
        print(f"ERROR: DuckDB file not found: {db_path}", file=sys.stderr)
        return 1

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        risks = _fetch_risks(conn, args.collection_run_id, args.min_severity)
    finally:
        conn.close()

    if not risks:
        print("No risks found matching criteria.")
        return 0

    print(f"Found {len(risks)} risk(s) at severity >= {args.min_severity}")
    print()

    # Check for existing issues to deduplicate
    existing = _existing_issue_titles(args.repo) if args.apply else set()

    created = 0
    skipped = 0
    for risk in risks:
        title = _build_issue_title(risk)
        body = _build_issue_body(risk)
        labels = DEFAULT_LABELS + [f"severity:{risk['severity']}"]

        if title in existing:
            print(f"  SKIP (exists): {title}")
            skipped += 1
            continue

        if args.apply:
            url = _create_issue(title, body, labels, args.repo)
            if url:
                print(f"  CREATED: {title}")
                print(f"           {url}")
                created += 1
        else:
            print(f"  [DRY-RUN] Would create: {title}")
            print(f"            Severity: {risk['severity']}")
            if risk.get("action"):
                print(f"            Action: {risk['action']}")
            if risk.get("sla_date"):
                print(f"            SLA: {risk['sla_date']}")
            print()

    print()
    if args.apply:
        print(f"=== Summary: {created} created, {skipped} skipped (already exist) ===")
    else:
        print(f"=== Dry-run: {len(risks) - skipped} issue(s) would be created ===")
        print("    Use --apply to create issues.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
