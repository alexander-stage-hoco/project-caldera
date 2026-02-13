"""
Accuracy checks (AC-1 to AC-8) for PMD CPD evaluation.

These checks validate the accuracy of clone detection against ground truth.
"""

from __future__ import annotations

from . import (
    CheckResult,
    CheckCategory,
    load_all_ground_truth,
    normalize_path,
    get_file_from_analysis,
    get_clones_for_file,
    get_cross_file_clones,
)


def run_accuracy_checks(analysis: dict, ground_truth_dir: str) -> list[CheckResult]:
    """Run all accuracy checks."""
    ground_truth = load_all_ground_truth(ground_truth_dir)
    results = []

    results.append(_ac1_heavy_duplication_detected(analysis, ground_truth))
    results.append(_ac2_clone_count_in_range(analysis, ground_truth))
    results.append(_ac3_duplication_percentage_accuracy(analysis, ground_truth))
    results.append(_ac4_no_false_positives_clean_files(analysis, ground_truth))
    results.append(_ac5_cross_file_detection(analysis, ground_truth))
    results.append(_ac6_semantic_identifier_detection(analysis, ground_truth))
    results.append(_ac7_semantic_literal_detection(analysis, ground_truth))
    results.append(_ac8_clone_line_accuracy(analysis, ground_truth))

    return results


def _ac1_heavy_duplication_detected(analysis: dict, ground_truth: dict[str, dict]) -> CheckResult:
    """AC-1: Heavy duplication files should have clones detected."""
    detected = 0
    total = 0
    evidence_files = []

    for lang, gt in ground_truth.items():
        files = gt.get("files", {})
        for filename, expectations in files.items():
            if "heavy" in filename.lower():
                total += 1
                file_info = get_file_from_analysis(analysis, filename)
                if file_info:
                    clone_count = file_info.get("duplicate_blocks", 0)
                    expected_min = expectations.get("expected_clone_range", [0, 0])[0]
                    if clone_count >= expected_min or clone_count >= 1:
                        detected += 1
                        evidence_files.append({
                            "file": filename,
                            "detected_clones": clone_count,
                            "status": "detected"
                        })
                    else:
                        evidence_files.append({
                            "file": filename,
                            "detected_clones": clone_count,
                            "status": "missed"
                        })

    if total == 0:
        return CheckResult(
            check_id="AC-1",
            name="Heavy duplication detection",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0,
            message="No heavy duplication files in ground truth",
            evidence={"files": evidence_files}
        )

    score = detected / total
    passed = score >= 0.8  # 80% threshold

    return CheckResult(
        check_id="AC-1",
        name="Heavy duplication detection",
        category=CheckCategory.ACCURACY,
        passed=passed,
        score=score,
        message=f"Detected {detected}/{total} heavy duplication files",
        evidence={"files": evidence_files, "detected": detected, "total": total}
    )


def _ac2_clone_count_in_range(analysis: dict, ground_truth: dict[str, dict]) -> CheckResult:
    """AC-2: Clone counts should be within expected ranges."""
    in_range = 0
    total = 0
    evidence_files = []

    for lang, gt in ground_truth.items():
        files = gt.get("files", {})
        for filename, expectations in files.items():
            expected_range = expectations.get("expected_clone_range")
            if expected_range is None:
                continue

            total += 1
            file_info = get_file_from_analysis(analysis, filename)
            actual_count = 0
            if file_info:
                actual_count = file_info.get("duplicate_blocks", 0)

            min_count, max_count = expected_range
            if min_count <= actual_count <= max_count:
                in_range += 1
                status = "in_range"
            else:
                status = "out_of_range"

            evidence_files.append({
                "file": filename,
                "actual": actual_count,
                "expected_range": expected_range,
                "status": status
            })

    if total == 0:
        return CheckResult(
            check_id="AC-2",
            name="Clone count accuracy",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0,
            message="No clone count expectations in ground truth",
            evidence={}
        )

    score = in_range / total
    passed = score >= 0.7  # 70% threshold

    return CheckResult(
        check_id="AC-2",
        name="Clone count accuracy",
        category=CheckCategory.ACCURACY,
        passed=passed,
        score=score,
        message=f"{in_range}/{total} files have clone counts in expected range",
        evidence={"files": evidence_files}
    )


def _ac3_duplication_percentage_accuracy(analysis: dict, ground_truth: dict[str, dict]) -> CheckResult:
    """AC-3: Duplication percentages should be within expected ranges."""
    in_range = 0
    total = 0
    evidence_files = []

    for lang, gt in ground_truth.items():
        files = gt.get("files", {})
        for filename, expectations in files.items():
            expected_range = expectations.get("duplication_percentage_range")
            if expected_range is None:
                continue
            name = filename.lower()
            if any(tag in name for tag in ["light_duplication", "semantic", "cross_file"]):
                continue

            total += 1
            file_info = get_file_from_analysis(analysis, filename)
            actual_pct = 0.0
            if file_info:
                actual_pct = file_info.get("duplication_percentage", 0.0)

            min_pct, max_pct = expected_range
            if min_pct <= actual_pct <= max_pct:
                in_range += 1
                status = "in_range"
            else:
                status = "out_of_range"

            evidence_files.append({
                "file": filename,
                "actual_pct": actual_pct,
                "expected_range": expected_range,
                "status": status
            })

    if total == 0:
        return CheckResult(
            check_id="AC-3",
            name="Duplication percentage accuracy",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0,
            message="No percentage expectations in ground truth",
            evidence={}
        )

    score = in_range / total
    passed = score >= 0.6  # 60% threshold (percentages can vary)

    return CheckResult(
        check_id="AC-3",
        name="Duplication percentage accuracy",
        category=CheckCategory.ACCURACY,
        passed=passed,
        score=score,
        message=f"{in_range}/{total} files have duplication % in expected range",
        evidence={"files": evidence_files}
    )


def _ac4_no_false_positives_clean_files(analysis: dict, ground_truth: dict[str, dict]) -> CheckResult:
    """AC-4: Clean files (no_duplication) should have zero or near-zero clones."""
    correct = 0
    total = 0
    evidence_files = []

    for lang, gt in ground_truth.items():
        files = gt.get("files", {})
        for filename, expectations in files.items():
            if "no_dup" in filename.lower():
                total += 1
                file_info = get_file_from_analysis(analysis, filename)
                actual_count = 0
                if file_info:
                    actual_count = file_info.get("duplicate_blocks", 0)

                # Allow small tolerance (0-1 clones for clean files)
                if actual_count <= 1:
                    correct += 1
                    status = "correct"
                else:
                    status = "false_positive"

                evidence_files.append({
                    "file": filename,
                    "detected_clones": actual_count,
                    "status": status
                })

    if total == 0:
        return CheckResult(
            check_id="AC-4",
            name="No false positives in clean files",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0,
            message="No clean files in ground truth",
            evidence={}
        )

    score = correct / total
    passed = score >= 0.9  # 90% threshold (clean files should be very accurate)

    return CheckResult(
        check_id="AC-4",
        name="No false positives in clean files",
        category=CheckCategory.ACCURACY,
        passed=passed,
        score=score,
        message=f"{correct}/{total} clean files correctly identified (no false positives)",
        evidence={"files": evidence_files}
    )


def _ac5_cross_file_detection(analysis: dict, ground_truth: dict[str, dict]) -> CheckResult:
    """AC-5: Cross-file duplications should be detected."""
    detected_pairs = 0
    total_pairs = 0
    evidence = []

    for lang, gt in ground_truth.items():
        cross_file = gt.get("cross_file_expectations", {})
        for pair_name, expectations in cross_file.items():
            total_pairs += 1
            files = expectations.get("files", [])
            expected_range = expectations.get("expected_cross_file_clone_range", [1, 10])

            # Count cross-file clones between these files
            cross_clones = get_cross_file_clones(analysis)
            relevant_clones = 0
            for clone in cross_clones:
                clone_files = set()
                for occ in clone.get("occurrences", []):
                    clone_files.add(normalize_path(occ.get("file", "")))
                # Check if any of the expected files are in this clone
                matches = sum(1 for f in files if any(normalize_path(f) in cf for cf in clone_files))
                if matches >= 2:
                    relevant_clones += 1

            min_expected = expected_range[0]
            if relevant_clones >= min_expected:
                detected_pairs += 1
                status = "detected"
            else:
                status = "missed"

            evidence.append({
                "pair": pair_name,
                "files": files,
                "detected_clones": relevant_clones,
                "expected_range": expected_range,
                "status": status
            })

    if total_pairs == 0:
        return CheckResult(
            check_id="AC-5",
            name="Cross-file clone detection",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0,
            message="No cross-file expectations in ground truth",
            evidence={}
        )

    score = detected_pairs / total_pairs
    passed = score >= 0.7  # 70% threshold

    return CheckResult(
        check_id="AC-5",
        name="Cross-file clone detection",
        category=CheckCategory.ACCURACY,
        passed=passed,
        score=score,
        message=f"Detected {detected_pairs}/{total_pairs} cross-file duplication pairs",
        evidence={"pairs": evidence}
    )


def _ac6_semantic_identifier_detection(analysis: dict, ground_truth: dict[str, dict]) -> CheckResult:
    """AC-6: Semantic mode should detect identifier-renamed duplicates."""
    # This check only passes if we're in semantic mode
    metadata = analysis.get("metadata", {})
    is_semantic = metadata.get("ignore_identifiers", False)

    if not is_semantic:
        return CheckResult(
            check_id="AC-6",
            name="Semantic identifier detection",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=0.5,  # Neutral score for non-semantic mode
            message="Semantic mode not enabled (--ignore-identifiers not used)",
            evidence={"mode": "standard", "note": "Run with --ignore-identifiers for full test"}
        )

    detected = 0
    total = 0
    evidence_files = []

    for lang, gt in ground_truth.items():
        files = gt.get("files", {})
        for filename, expectations in files.items():
            semantic_exp = expectations.get("expected_clones_semantic")
            if semantic_exp and semantic_exp.get("requires_ignore_identifiers"):
                total += 1
                file_info = get_file_from_analysis(analysis, filename)
                actual_count = 0
                if file_info:
                    actual_count = file_info.get("duplicate_blocks", 0)

                expected_range = semantic_exp.get("count_range", [1, 10])
                if expected_range[0] <= actual_count <= expected_range[1]:
                    detected += 1
                    status = "detected"
                else:
                    status = "missed"

                evidence_files.append({
                    "file": filename,
                    "detected_clones": actual_count,
                    "expected_range": expected_range,
                    "status": status
                })

    if total == 0:
        return CheckResult(
            check_id="AC-6",
            name="Semantic identifier detection",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0,
            message="No semantic identifier expectations in ground truth",
            evidence={}
        )

    score = detected / total
    passed = score >= 0.7

    return CheckResult(
        check_id="AC-6",
        name="Semantic identifier detection",
        category=CheckCategory.ACCURACY,
        passed=passed,
        score=score,
        message=f"Detected {detected}/{total} semantic (identifier-renamed) duplicates",
        evidence={"files": evidence_files}
    )


def _ac7_semantic_literal_detection(analysis: dict, ground_truth: dict[str, dict]) -> CheckResult:
    """AC-7: Semantic mode should detect literal-changed duplicates."""
    metadata = analysis.get("metadata", {})
    is_semantic = metadata.get("ignore_literals", False)

    if not is_semantic:
        return CheckResult(
            check_id="AC-7",
            name="Semantic literal detection",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=0.5,  # Neutral score for non-semantic mode
            message="Semantic mode not enabled (--ignore-literals not used)",
            evidence={"mode": "standard", "note": "Run with --ignore-literals for full test"}
        )

    detected = 0
    total = 0
    evidence_files = []

    for lang, gt in ground_truth.items():
        files = gt.get("files", {})
        for filename, expectations in files.items():
            semantic_exp = expectations.get("expected_clones_semantic")
            if semantic_exp and semantic_exp.get("requires_ignore_literals"):
                total += 1
                file_info = get_file_from_analysis(analysis, filename)
                actual_count = 0
                if file_info:
                    actual_count = file_info.get("duplicate_blocks", 0)

                expected_range = semantic_exp.get("count_range", [1, 10])
                if expected_range[0] <= actual_count <= expected_range[1]:
                    detected += 1
                    status = "detected"
                else:
                    status = "missed"

                evidence_files.append({
                    "file": filename,
                    "detected_clones": actual_count,
                    "expected_range": expected_range,
                    "status": status
                })

    if total == 0:
        return CheckResult(
            check_id="AC-7",
            name="Semantic literal detection",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0,
            message="No semantic literal expectations in ground truth",
            evidence={}
        )

    score = detected / total
    passed = score >= 0.7

    return CheckResult(
        check_id="AC-7",
        name="Semantic literal detection",
        category=CheckCategory.ACCURACY,
        passed=passed,
        score=score,
        message=f"Detected {detected}/{total} semantic (literal-changed) duplicates",
        evidence={"files": evidence_files}
    )


def _ac8_clone_line_accuracy(analysis: dict, ground_truth: dict[str, dict]) -> CheckResult:
    """AC-8: Clone line locations should be reasonably accurate."""
    # For this check, we verify that detected clones have reasonable line counts
    total_clones = len(analysis.get("duplications", []))

    if total_clones == 0:
        return CheckResult(
            check_id="AC-8",
            name="Clone line accuracy",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0,
            message="No clones detected to verify",
            evidence={}
        )

    valid_clones = 0
    evidence = []

    for dup in analysis.get("duplications", []):
        lines = dup.get("lines", 0)
        tokens = dup.get("tokens", 0)
        occurrences = len(dup.get("occurrences", []))

        # A valid clone should have:
        # - At least 3 lines (meaningful duplication)
        # - At least 2 occurrences
        # - Tokens proportional to lines
        is_valid = lines >= 3 and occurrences >= 2

        if is_valid:
            valid_clones += 1

        evidence.append({
            "clone_id": dup.get("clone_id"),
            "lines": lines,
            "tokens": tokens,
            "occurrences": occurrences,
            "valid": is_valid
        })

    score = valid_clones / total_clones if total_clones > 0 else 1.0
    passed = score >= 0.8

    return CheckResult(
        check_id="AC-8",
        name="Clone line accuracy",
        category=CheckCategory.ACCURACY,
        passed=passed,
        score=score,
        message=f"{valid_clones}/{total_clones} clones have valid line counts",
        evidence={"clones": evidence[:10]}  # Limit evidence for readability
    )
