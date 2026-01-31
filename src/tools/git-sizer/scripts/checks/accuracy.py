"""
Accuracy checks (AC-1 to AC-8) for git-sizer repository analysis.

Tests accuracy of size detection:
- AC-1: Large blob detection
- AC-2: Total blob size accuracy
- AC-3: Commit count accuracy
- AC-4: Tree entries detection
- AC-5: Path depth detection
- AC-6: Health grade accuracy
- AC-7: LFS candidate identification
- AC-8: Threshold violation detection
"""

from . import (
    CheckResult,
    CheckCategory,
    get_repo_by_name,
    load_all_ground_truth,
)


def run_accuracy_checks(
    analysis: dict,
    ground_truth_dir: str,
) -> list[CheckResult]:
    """Run all accuracy checks (AC-1 to AC-8)."""
    results = []
    ground_truth = load_all_ground_truth(ground_truth_dir)

    # AC-1: Large blob detection
    # Check if bloated repo correctly detected large blobs
    bloated = get_repo_by_name(analysis, "bloated")
    if bloated:
        max_blob = bloated.get("metrics", {}).get("max_blob_size", 0)
        # Expected: ~10 MB blob
        ac1_passed = max_blob >= 5 * 1024 * 1024  # At least 5 MB detected
        ac1_score = min(1.0, max_blob / (10 * 1024 * 1024))
    else:
        ac1_passed = False
        ac1_score = 0.0
        max_blob = 0

    results.append(CheckResult(
        check_id="AC-1",
        name="Large blob detection",
        category=CheckCategory.ACCURACY,
        passed=ac1_passed,
        score=ac1_score,
        message=f"Detected max blob size: {max_blob / (1024*1024):.1f} MiB",
        evidence={"max_blob_bytes": max_blob, "expected_min_bytes": 5 * 1024 * 1024},
    ))

    # AC-2: Total blob size accuracy
    if bloated:
        total_blob = bloated.get("metrics", {}).get("blob_total_size", 0)
        # Expected: ~22 MB total
        ac2_passed = total_blob >= 15 * 1024 * 1024  # At least 15 MB
        ac2_score = min(1.0, total_blob / (22 * 1024 * 1024))
    else:
        ac2_passed = False
        ac2_score = 0.0
        total_blob = 0

    results.append(CheckResult(
        check_id="AC-2",
        name="Total blob size accuracy",
        category=CheckCategory.ACCURACY,
        passed=ac2_passed,
        score=ac2_score,
        message=f"Detected total blob size: {total_blob / (1024*1024):.1f} MiB",
        evidence={"total_blob_bytes": total_blob, "expected_min_bytes": 15 * 1024 * 1024},
    ))

    # AC-3: Commit count accuracy
    deep_history = get_repo_by_name(analysis, "deep-history")
    if deep_history:
        commit_count = deep_history.get("metrics", {}).get("commit_count", 0)
        # Expected: 501 commits
        ac3_passed = 490 <= commit_count <= 510
        ac3_score = 1.0 if ac3_passed else max(0, 1.0 - abs(commit_count - 501) / 501)
    else:
        ac3_passed = False
        ac3_score = 0.0
        commit_count = 0

    results.append(CheckResult(
        check_id="AC-3",
        name="Commit count accuracy",
        category=CheckCategory.ACCURACY,
        passed=ac3_passed,
        score=ac3_score,
        message=f"Detected {commit_count} commits (expected ~501)",
        evidence={"commit_count": commit_count, "expected": 501},
    ))

    # AC-4: Tree entries detection
    wide_tree = get_repo_by_name(analysis, "wide-tree")
    if wide_tree:
        max_entries = wide_tree.get("metrics", {}).get("max_tree_entries", 0)
        # Expected: 1000 files in one directory
        ac4_passed = max_entries >= 900  # At least 900 detected
        ac4_score = min(1.0, max_entries / 1000)
    else:
        ac4_passed = False
        ac4_score = 0.0
        max_entries = 0

    results.append(CheckResult(
        check_id="AC-4",
        name="Tree entries detection",
        category=CheckCategory.ACCURACY,
        passed=ac4_passed,
        score=ac4_score,
        message=f"Detected max tree entries: {max_entries} (expected ~1000)",
        evidence={"max_tree_entries": max_entries, "expected": 1000},
    ))

    # AC-5: Path depth detection
    if wide_tree:
        max_depth = wide_tree.get("metrics", {}).get("max_path_depth", 0)
        # Expected: 20+ deep nested path
        ac5_passed = max_depth >= 15
        ac5_score = min(1.0, max_depth / 20)
    else:
        ac5_passed = False
        ac5_score = 0.0
        max_depth = 0

    results.append(CheckResult(
        check_id="AC-5",
        name="Path depth detection",
        category=CheckCategory.ACCURACY,
        passed=ac5_passed,
        score=ac5_score,
        message=f"Detected max path depth: {max_depth} (expected ~20)",
        evidence={"max_path_depth": max_depth, "expected": 20},
    ))

    # AC-6: Health grade accuracy
    # Check that problematic repos get worse grades
    healthy = get_repo_by_name(analysis, "healthy")
    grade_correct = 0
    grade_total = 0

    if healthy:
        grade_total += 1
        if healthy.get("health_grade", "F")[0] in "AB":
            grade_correct += 1

    if bloated:
        grade_total += 1
        if bloated.get("health_grade", "A")[0] in "CDF":
            grade_correct += 1

    if wide_tree:
        grade_total += 1
        if wide_tree.get("health_grade", "A")[0] in "CDF":
            grade_correct += 1

    ac6_score = grade_correct / grade_total if grade_total > 0 else 0.0
    ac6_passed = ac6_score >= 0.5

    results.append(CheckResult(
        check_id="AC-6",
        name="Health grade accuracy",
        category=CheckCategory.ACCURACY,
        passed=ac6_passed,
        score=ac6_score,
        message=f"Correct grades: {grade_correct}/{grade_total}",
        evidence={"correct": grade_correct, "total": grade_total},
    ))

    # AC-7: LFS candidate identification
    if bloated:
        lfs_candidates = bloated.get("lfs_candidates", [])
        ac7_passed = len(lfs_candidates) > 0
        ac7_score = 1.0 if ac7_passed else 0.0
    else:
        ac7_passed = False
        ac7_score = 0.0
        lfs_candidates = []

    results.append(CheckResult(
        check_id="AC-7",
        name="LFS candidate identification",
        category=CheckCategory.ACCURACY,
        passed=ac7_passed,
        score=ac7_score,
        message=f"Identified {len(lfs_candidates)} LFS candidates",
        evidence={"lfs_candidates": lfs_candidates},
    ))

    # AC-8: Threshold violation detection
    violations_expected = {
        "bloated": 1,  # max_blob_size
        "wide-tree": 2,  # max_tree_entries, max_path_depth
        "healthy": 0,
        "deep-history": 0,
    }

    violations_correct = 0
    violations_total = 0

    for repo_name, expected_count in violations_expected.items():
        repo = get_repo_by_name(analysis, repo_name)
        if repo:
            violations_total += 1
            actual_count = len(repo.get("violations", []))
            if actual_count >= expected_count * 0.5:  # At least half expected
                violations_correct += 1

    ac8_score = violations_correct / violations_total if violations_total > 0 else 0.0
    ac8_passed = ac8_score >= 0.5

    results.append(CheckResult(
        check_id="AC-8",
        name="Threshold violation detection",
        category=CheckCategory.ACCURACY,
        passed=ac8_passed,
        score=ac8_score,
        message=f"Violation detection: {violations_correct}/{violations_total} repos correct",
        evidence={"correct": violations_correct, "total": violations_total},
    ))

    return results
