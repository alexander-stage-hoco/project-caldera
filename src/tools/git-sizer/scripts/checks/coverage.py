"""
Coverage checks (CV-1 to CV-8) for git-sizer repository analysis.

Tests metric coverage:
- CV-1: Blob metrics coverage
- CV-2: Tree metrics coverage
- CV-3: Commit metrics coverage
- CV-4: Reference metrics coverage
- CV-5: Path metrics coverage
- CV-6: Expanded checkout metrics
- CV-7: Health grade coverage
- CV-8: Violation detail coverage
"""

from . import (
    CheckResult,
    CheckCategory,
)


def run_coverage_checks(
    analysis: dict,
) -> list[CheckResult]:
    """Run all coverage checks (CV-1 to CV-8)."""
    results = []
    repos = analysis.get("repositories", [])

    if not repos:
        # No repos - all checks fail
        for i in range(1, 9):
            results.append(CheckResult(
                check_id=f"CV-{i}",
                name=f"Coverage check {i}",
                category=CheckCategory.COVERAGE,
                passed=False,
                score=0.0,
                message="No repositories analyzed",
            ))
        return results

    # CV-1: Blob metrics coverage
    blob_metrics = ["blob_count", "blob_total_size", "max_blob_size"]
    blob_coverage = 0
    for repo in repos:
        metrics = repo.get("metrics", {})
        for metric in blob_metrics:
            if metric in metrics and metrics[metric] is not None:
                blob_coverage += 1

    cv1_score = blob_coverage / (len(repos) * len(blob_metrics))
    cv1_passed = cv1_score >= 0.8

    results.append(CheckResult(
        check_id="CV-1",
        name="Blob metrics coverage",
        category=CheckCategory.COVERAGE,
        passed=cv1_passed,
        score=cv1_score,
        message=f"Blob metrics: {blob_coverage}/{len(repos) * len(blob_metrics)} present",
        evidence={"metrics": blob_metrics, "coverage": blob_coverage},
    ))

    # CV-2: Tree metrics coverage
    tree_metrics = ["tree_count", "tree_total_size", "tree_total_entries", "max_tree_entries"]
    tree_coverage = 0
    for repo in repos:
        metrics = repo.get("metrics", {})
        for metric in tree_metrics:
            if metric in metrics and metrics[metric] is not None:
                tree_coverage += 1

    cv2_score = tree_coverage / (len(repos) * len(tree_metrics))
    cv2_passed = cv2_score >= 0.8

    results.append(CheckResult(
        check_id="CV-2",
        name="Tree metrics coverage",
        category=CheckCategory.COVERAGE,
        passed=cv2_passed,
        score=cv2_score,
        message=f"Tree metrics: {tree_coverage}/{len(repos) * len(tree_metrics)} present",
        evidence={"metrics": tree_metrics, "coverage": tree_coverage},
    ))

    # CV-3: Commit metrics coverage
    commit_metrics = ["commit_count", "commit_total_size", "max_commit_size", "max_history_depth"]
    commit_coverage = 0
    for repo in repos:
        metrics = repo.get("metrics", {})
        for metric in commit_metrics:
            if metric in metrics and metrics[metric] is not None:
                commit_coverage += 1

    cv3_score = commit_coverage / (len(repos) * len(commit_metrics))
    cv3_passed = cv3_score >= 0.8

    results.append(CheckResult(
        check_id="CV-3",
        name="Commit metrics coverage",
        category=CheckCategory.COVERAGE,
        passed=cv3_passed,
        score=cv3_score,
        message=f"Commit metrics: {commit_coverage}/{len(repos) * len(commit_metrics)} present",
        evidence={"metrics": commit_metrics, "coverage": commit_coverage},
    ))

    # CV-4: Reference metrics coverage
    ref_metrics = ["reference_count", "branch_count", "tag_count"]
    ref_coverage = 0
    for repo in repos:
        metrics = repo.get("metrics", {})
        for metric in ref_metrics:
            if metric in metrics and metrics[metric] is not None:
                ref_coverage += 1

    cv4_score = ref_coverage / (len(repos) * len(ref_metrics))
    cv4_passed = cv4_score >= 0.8

    results.append(CheckResult(
        check_id="CV-4",
        name="Reference metrics coverage",
        category=CheckCategory.COVERAGE,
        passed=cv4_passed,
        score=cv4_score,
        message=f"Reference metrics: {ref_coverage}/{len(repos) * len(ref_metrics)} present",
        evidence={"metrics": ref_metrics, "coverage": ref_coverage},
    ))

    # CV-5: Path metrics coverage
    path_metrics = ["max_path_depth", "max_path_length"]
    path_coverage = 0
    for repo in repos:
        metrics = repo.get("metrics", {})
        for metric in path_metrics:
            if metric in metrics and metrics[metric] is not None:
                path_coverage += 1

    cv5_score = path_coverage / (len(repos) * len(path_metrics))
    cv5_passed = cv5_score >= 0.8

    results.append(CheckResult(
        check_id="CV-5",
        name="Path metrics coverage",
        category=CheckCategory.COVERAGE,
        passed=cv5_passed,
        score=cv5_score,
        message=f"Path metrics: {path_coverage}/{len(repos) * len(path_metrics)} present",
        evidence={"metrics": path_metrics, "coverage": path_coverage},
    ))

    # CV-6: Expanded checkout metrics
    expanded_metrics = ["expanded_tree_count", "expanded_blob_count", "expanded_blob_size"]
    expanded_coverage = 0
    for repo in repos:
        metrics = repo.get("metrics", {})
        for metric in expanded_metrics:
            if metric in metrics and metrics[metric] is not None:
                expanded_coverage += 1

    cv6_score = expanded_coverage / (len(repos) * len(expanded_metrics))
    cv6_passed = cv6_score >= 0.8

    results.append(CheckResult(
        check_id="CV-6",
        name="Expanded checkout metrics",
        category=CheckCategory.COVERAGE,
        passed=cv6_passed,
        score=cv6_score,
        message=f"Expanded metrics: {expanded_coverage}/{len(repos) * len(expanded_metrics)} present",
        evidence={"metrics": expanded_metrics, "coverage": expanded_coverage},
    ))

    # CV-7: Health grade coverage
    grade_coverage = 0
    for repo in repos:
        if repo.get("health_grade"):
            grade_coverage += 1

    cv7_score = grade_coverage / len(repos)
    cv7_passed = cv7_score >= 0.8

    results.append(CheckResult(
        check_id="CV-7",
        name="Health grade coverage",
        category=CheckCategory.COVERAGE,
        passed=cv7_passed,
        score=cv7_score,
        message=f"Health grades: {grade_coverage}/{len(repos)} repos have grades",
        evidence={"coverage": grade_coverage, "total": len(repos)},
    ))

    # CV-8: Violation detail coverage
    # Check that violations have required fields
    violation_fields = ["metric", "level"]  # Required fields per schema
    violation_coverage = 0
    total_violations = 0

    for repo in repos:
        for violation in repo.get("violations", []):
            total_violations += 1
            fields_present = sum(1 for f in violation_fields if f in violation)
            if fields_present == len(violation_fields):
                violation_coverage += 1

    if total_violations > 0:
        cv8_score = violation_coverage / total_violations
    else:
        cv8_score = 1.0  # No violations to check, pass by default

    cv8_passed = cv8_score >= 0.8

    results.append(CheckResult(
        check_id="CV-8",
        name="Violation detail coverage",
        category=CheckCategory.COVERAGE,
        passed=cv8_passed,
        score=cv8_score,
        message=f"Violation details: {violation_coverage}/{total_violations} complete",
        evidence={"complete": violation_coverage, "total": total_violations},
    ))

    return results
