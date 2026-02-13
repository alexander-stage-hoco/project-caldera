"""Programmatic evaluation script for dependensee."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_checks() -> list[tuple[str, Any]]:
    """Load all check modules from scripts/checks/."""
    checks_dir = Path(__file__).parent / "checks"
    check_modules = []

    for check_file in sorted(checks_dir.glob("*.py")):
        if check_file.name.startswith("_"):
            continue
        module_name = f"scripts.checks.{check_file.stem}"
        try:
            module = importlib.import_module(module_name)
            check_modules.append((check_file.stem, module))
        except ImportError as e:
            print(f"Warning: Could not load {module_name}: {e}", file=sys.stderr)

    return check_modules


def run_checks(output: dict, ground_truth: dict | None) -> list[dict]:
    """Run all checks and collect results."""
    results = []
    check_modules = load_checks()

    for name, module in check_modules:
        # Find all check_* functions in the module
        for attr_name in dir(module):
            if not attr_name.startswith("check_"):
                continue
            check_fn = getattr(module, attr_name)
            if not callable(check_fn):
                continue

            try:
                result = check_fn(output, ground_truth)
                if isinstance(result, dict):
                    results.append(result)
                elif isinstance(result, list):
                    results.extend(result)
            except Exception as e:
                results.append({
                    "check_id": f"{name}.{attr_name}",
                    "status": "error",
                    "message": str(e),
                })

    return results


def compute_summary(results: list[dict]) -> dict:
    """Compute summary statistics from check results."""
    total = len(results)
    passed = sum(1 for r in results if r.get("status") == "pass")
    failed = sum(1 for r in results if r.get("status") == "fail")
    warned = sum(1 for r in results if r.get("status") == "warn")
    errored = sum(1 for r in results if r.get("status") == "error")

    score = passed / total if total > 0 else 0.0

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "warned": warned,
        "errored": errored,
        "score": round(score, 4),
        "decision": "PASS" if failed == 0 and errored == 0 else "FAIL",
    }


def generate_scorecard(summary: dict, results: list[dict], output_dir: Path) -> None:
    """Generate scorecard.md from evaluation results."""
    status_icon = {"pass": "\u2713 Pass", "fail": "\u2717 Fail", "warn": "\u26a0 Warn", "error": "\u2717 Error"}

    lines = [
        "# dependensee Evaluation Scorecard",
        "",
        f"**Score:** {summary['score']:.1%}",
        f"**Decision:** {summary['decision']}",
        f"**Checks Passed:** {summary['passed']}/{summary['total']}",
        "",
        "## Check Details",
        "",
        "| ID | Status | Message |",
        "|----|--------|---------|",
    ]

    for check in results:
        cid = check.get("check_id", "unknown")
        status = status_icon.get(check.get("status", ""), check.get("status", ""))
        msg = check.get("message", "")
        lines.append(f"| {cid} | {status} | {msg} |")

    lines.append("")

    scorecard_path = output_dir / "scorecard.md"
    scorecard_path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run programmatic evaluation")
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--ground-truth-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    # Load analysis output
    output_path = args.results_dir / "output.json"
    if not output_path.exists():
        # Try finding in subdirectories
        candidates = list(args.results_dir.glob("*/output.json"))
        if candidates:
            output_path = max(candidates, key=lambda p: p.stat().st_mtime)
        else:
            print(f"Error: No output.json found in {args.results_dir}", file=sys.stderr)
            return 1

    output = json.loads(output_path.read_text())

    # Load ground truth if available
    # Extract repo_path from output metadata for dynamic scenario detection
    metadata = output.get("metadata", {})
    repo_path = metadata.get("repo_path", "")

    # Extract scenario name (e.g., "synthetic" from "eval-repos/synthetic")
    if "/" in repo_path:
        scenario = repo_path.split("/")[-1]
    else:
        scenario = repo_path or "synthetic"  # fallback

    # Load matching ground truth
    ground_truth = None
    gt_path = args.ground_truth_dir / f"{scenario}.json"
    if gt_path.exists():
        ground_truth = json.loads(gt_path.read_text())

    # Run checks
    results = run_checks(output, ground_truth)
    summary = compute_summary(results)

    # Write report with root-level fields for compliance
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decision": summary["decision"],
        "score": summary["score"],
        "summary": summary,
        "checks": results,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))

    # Generate scorecard
    generate_scorecard(summary, results, args.output.parent)

    print(f"Evaluation complete. Decision: {summary['decision']}")
    print(f"Score: {summary['score']:.1%} ({summary['passed']}/{summary['total']} passed)")
    print(f"Scorecard written to: {args.output.parent / 'scorecard.md'}")

    return 0 if summary["decision"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
