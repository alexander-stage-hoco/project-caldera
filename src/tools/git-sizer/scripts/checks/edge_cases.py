"""
Edge case checks (EC-1 to EC-8) for git-sizer repository analysis.

Tests handling of edge cases:
- EC-1: Empty/minimal repo handling
- EC-2: Large repo handling (many commits)
- EC-3: Wide tree handling (many files)
- EC-4: Deep path handling
- EC-5: No violations case (healthy repo)
- EC-6: Multiple violations case
- EC-7: JSON output validity
- EC-8: Raw output preservation
"""

from . import (
    CheckResult,
    CheckCategory,
    get_repo_by_name,
)


def run_edge_case_checks(
    analysis: dict,
) -> list[CheckResult]:
    """Run all edge case checks (EC-1 to EC-8)."""
    results = []
    repos = analysis.get("repositories", [])

    # EC-1: Empty/minimal repo handling (healthy repo)
    healthy = get_repo_by_name(analysis, "healthy")
    ec1_passed = healthy is not None and healthy.get("metrics", {}).get("commit_count", 0) > 0

    results.append(CheckResult(
        check_id="EC-1",
        name="Minimal repo handling",
        category=CheckCategory.EDGE_CASES,
        passed=ec1_passed,
        score=1.0 if ec1_passed else 0.0,
        message="Minimal repo analyzed successfully" if ec1_passed else "Failed to analyze minimal repo",
        evidence={"repo": "healthy", "analyzed": ec1_passed},
    ))

    # EC-2: Large repo handling (many commits)
    deep_history = get_repo_by_name(analysis, "deep-history")
    ec2_passed = deep_history is not None and deep_history.get("metrics", {}).get("commit_count", 0) > 400

    results.append(CheckResult(
        check_id="EC-2",
        name="Large history handling",
        category=CheckCategory.EDGE_CASES,
        passed=ec2_passed,
        score=1.0 if ec2_passed else 0.0,
        message="Deep history repo analyzed successfully" if ec2_passed else "Failed to analyze deep history repo",
        evidence={"repo": "deep-history", "analyzed": ec2_passed},
    ))

    # EC-3: Wide tree handling (many files)
    wide_tree = get_repo_by_name(analysis, "wide-tree")
    ec3_passed = wide_tree is not None and wide_tree.get("metrics", {}).get("max_tree_entries", 0) > 500

    results.append(CheckResult(
        check_id="EC-3",
        name="Wide tree handling",
        category=CheckCategory.EDGE_CASES,
        passed=ec3_passed,
        score=1.0 if ec3_passed else 0.0,
        message="Wide tree repo analyzed successfully" if ec3_passed else "Failed to analyze wide tree repo",
        evidence={"repo": "wide-tree", "analyzed": ec3_passed},
    ))

    # EC-4: Deep path handling
    ec4_passed = wide_tree is not None and wide_tree.get("metrics", {}).get("max_path_depth", 0) > 10

    results.append(CheckResult(
        check_id="EC-4",
        name="Deep path handling",
        category=CheckCategory.EDGE_CASES,
        passed=ec4_passed,
        score=1.0 if ec4_passed else 0.0,
        message="Deep paths detected correctly" if ec4_passed else "Failed to detect deep paths",
        evidence={"max_depth": wide_tree.get("metrics", {}).get("max_path_depth", 0) if wide_tree else 0},
    ))

    # EC-5: No violations case (healthy repo should have 0 violations)
    ec5_passed = healthy is not None and len(healthy.get("violations", [])) == 0

    results.append(CheckResult(
        check_id="EC-5",
        name="No violations case",
        category=CheckCategory.EDGE_CASES,
        passed=ec5_passed,
        score=1.0 if ec5_passed else 0.0,
        message="Healthy repo correctly has no violations" if ec5_passed else "Healthy repo incorrectly flagged",
        evidence={"violations": len(healthy.get("violations", [])) if healthy else -1},
    ))

    # EC-6: Multiple violations case
    ec6_passed = wide_tree is not None and len(wide_tree.get("violations", [])) >= 2

    results.append(CheckResult(
        check_id="EC-6",
        name="Multiple violations case",
        category=CheckCategory.EDGE_CASES,
        passed=ec6_passed,
        score=1.0 if ec6_passed else 0.0,
        message="Multiple violations detected correctly" if ec6_passed else "Failed to detect multiple violations",
        evidence={"violations": len(wide_tree.get("violations", [])) if wide_tree else 0},
    ))

    # EC-7: JSON output validity (check structure - Caldera envelope format)
    # For Caldera, we check each repo has required fields from envelope
    required_fields = ["tool", "health_grade", "metrics"]
    fields_valid = 0
    total_checks = 0

    for repo in repos:
        total_checks += 1
        fields_present = sum(1 for f in required_fields if f in repo)
        if fields_present == len(required_fields):
            fields_valid += 1

    ec7_score = fields_valid / total_checks if total_checks > 0 else 0.0
    ec7_passed = ec7_score >= 0.75

    results.append(CheckResult(
        check_id="EC-7",
        name="JSON output validity",
        category=CheckCategory.EDGE_CASES,
        passed=ec7_passed,
        score=ec7_score,
        message=f"JSON structure: {fields_valid}/{total_checks} repos have required fields",
        evidence={"required": required_fields, "valid": fields_valid, "total": total_checks},
    ))

    # EC-8: Raw output preservation
    raw_preserved = 0
    for repo in repos:
        if repo.get("raw_output") and len(repo["raw_output"]) > 0:
            raw_preserved += 1

    ec8_score = raw_preserved / len(repos) if repos else 0.0
    ec8_passed = ec8_score >= 0.8

    results.append(CheckResult(
        check_id="EC-8",
        name="Raw output preservation",
        category=CheckCategory.EDGE_CASES,
        passed=ec8_passed,
        score=ec8_score,
        message=f"Raw output preserved: {raw_preserved}/{len(repos)} repos",
        evidence={"preserved": raw_preserved, "total": len(repos)},
    ))

    return results
