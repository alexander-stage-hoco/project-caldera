#!/usr/bin/env python3
"""Destroy orphaned Caldera cloud VMs that have exceeded their TTL.

Queries the Hetzner Cloud API via the ``hcloud`` CLI for servers labelled
``project=caldera`` and destroys any whose ``created`` timestamp is older
than the configured TTL.

Usage::

    python scripts/cloud_cleanup.py                  # default 4h TTL
    python scripts/cloud_cleanup.py --ttl-hours 2    # 2h TTL
    python scripts/cloud_cleanup.py --dry-run        # list only, don't destroy

Requires:
    - ``hcloud`` CLI installed and configured (``brew install hcloud``)
    - A valid Hetzner API context (``hcloud context create ...``)
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone


def _run_hcloud(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run an hcloud CLI command and return the result."""
    cmd = ["hcloud"] + args
    return subprocess.run(cmd, capture_output=True, text=True)


def list_caldera_servers() -> list[dict]:
    """List Hetzner servers with the ``project=caldera`` label."""
    result = _run_hcloud(["server", "list", "-l", "project=caldera", "-o", "json"])
    if result.returncode != 0:
        print(f"ERROR: hcloud server list failed: {result.stderr.strip()}", file=sys.stderr)
        return []
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"ERROR: Could not parse hcloud output: {result.stdout[:200]}", file=sys.stderr)
        return []


def server_age_hours(server: dict) -> float:
    """Return the age of a server in hours based on its ``created`` timestamp."""
    created_str = server.get("created", "")
    if not created_str:
        return 0.0
    try:
        created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return (now - created).total_seconds() / 3600
    except (ValueError, TypeError):
        return 0.0


def destroy_server(server_id: int, server_name: str) -> bool:
    """Destroy a server by ID. Returns True on success."""
    result = _run_hcloud(["server", "delete", str(server_id)])
    if result.returncode != 0:
        print(f"  ERROR: Failed to destroy {server_name} (id={server_id}): {result.stderr.strip()}")
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Destroy orphaned Caldera cloud VMs older than TTL.",
    )
    parser.add_argument(
        "--ttl-hours",
        type=float,
        default=4.0,
        help="Maximum age in hours before a VM is considered orphaned (default: 4)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List servers that would be destroyed without actually destroying them",
    )
    args = parser.parse_args()

    # Check hcloud CLI is available
    if not shutil.which("hcloud"):
        print("ERROR: hcloud CLI is not installed.", file=sys.stderr)
        print("Install with: brew install hcloud", file=sys.stderr)
        print("Then configure: hcloud context create caldera", file=sys.stderr)
        sys.exit(1)

    servers = list_caldera_servers()
    if not servers:
        print("No Caldera servers found.")
        return

    print(f"Found {len(servers)} Caldera server(s). TTL: {args.ttl_hours}h")
    print()

    orphaned = []
    for s in servers:
        name = s.get("name", "unknown")
        server_id = s.get("id", 0)
        age = server_age_hours(s)
        status = s.get("status", "unknown")
        server_type = s.get("server_type", {}).get("name", "?")

        age_str = f"{age:.1f}h"
        is_orphan = age > args.ttl_hours

        marker = " [ORPHANED]" if is_orphan else ""
        print(f"  {name} (id={server_id}, type={server_type}, status={status}, age={age_str}){marker}")

        if is_orphan:
            orphaned.append(s)

    if not orphaned:
        print()
        print("No orphaned servers to destroy.")
        return

    print()
    print(f"{len(orphaned)} server(s) exceed TTL of {args.ttl_hours}h.")

    if args.dry_run:
        print("[DRY RUN] Would destroy the above servers. Re-run without --dry-run to proceed.")
        return

    destroyed = 0
    for s in orphaned:
        name = s.get("name", "unknown")
        server_id = s.get("id", 0)
        print(f"  Destroying {name} (id={server_id})...", end=" ")
        if destroy_server(server_id, name):
            print("done.")
            destroyed += 1
        else:
            print("FAILED.")

    print()
    print(f"Destroyed {destroyed}/{len(orphaned)} orphaned server(s).")


if __name__ == "__main__":
    main()
