"""Detection quality checks (SD-1 to SD-6)."""

from __future__ import annotations

from . import CheckResult, check_boolean


def run_detection_checks(analysis: dict, ground_truth: dict) -> list[CheckResult]:
    """Run all detection quality checks."""
    check_results: list[CheckResult] = []
    expected = ground_truth.get("expected", {})
    # Handle both old format (flat) and new format (with results wrapper)
    results = analysis.get("results", analysis)

    # SD-1: No false negatives for known secrets
    expected_secret_count = expected.get("total_secrets", 0)
    actual_secret_count = results.get("total_secrets", 0)
    check_results.append(
        CheckResult(
            check_id="SD-1",
            category="Detection",
            passed=actual_secret_count >= expected_secret_count,
            message=f"Found {actual_secret_count} secrets, expected at least {expected_secret_count}",
            expected=f">= {expected_secret_count}",
            actual=actual_secret_count,
        )
    )

    # SD-2: No unexpected rule IDs (false positives by type)
    expected_rules = set(expected.get("rule_ids", []))
    actual_rules = set(results.get("secrets_by_rule", {}).keys())
    unexpected_rules = actual_rules - expected_rules if expected_rules else set()

    # Only consider it a failure if we have expected rules defined and found unexpected ones
    if expected_rules:
        check_results.append(
            CheckResult(
                check_id="SD-2",
                category="Detection",
                passed=len(unexpected_rules) == 0,
                message="No unexpected rule IDs" if len(unexpected_rules) == 0 else f"Unexpected rules: {unexpected_rules}",
                expected=list(expected_rules),
                actual=list(actual_rules),
            )
        )
    else:
        check_results.append(
            CheckResult(
                check_id="SD-2",
                category="Detection",
                passed=True,
                message="No expected rules defined, skipping check",
                expected=[],
                actual=list(actual_rules),
            )
        )

    # SD-3: Historical secrets detected
    expected_historical = expected.get("secrets_in_history", 0)
    actual_historical = results.get("secrets_in_history", 0)
    check_results.append(
        CheckResult(
            check_id="SD-3",
            category="Detection",
            passed=actual_historical == expected_historical,
            message=f"Historical secrets: expected {expected_historical}, found {actual_historical}",
            expected=expected_historical,
            actual=actual_historical,
        )
    )

    # SD-4: Clean repos have zero secrets
    if expected.get("total_secrets", 0) == 0:
        check_results.append(
            check_boolean(
                "SD-4",
                "Detection",
                "Clean repo has zero secrets",
                True,
                results.get("total_secrets", 0) == 0,
            )
        )
    else:
        check_results.append(
            CheckResult(
                check_id="SD-4",
                category="Detection",
                passed=True,
                message="N/A - repo expected to have secrets",
                expected="N/A",
                actual="N/A",
            )
        )

    # SD-5: Entropy values are reasonable (0-8 bits)
    findings = results.get("findings", [])
    entropy_valid = True
    invalid_entropy = []

    for finding in findings:
        entropy = finding.get("entropy", 0)
        if entropy < 0 or entropy > 8:
            entropy_valid = False
            invalid_entropy.append(f"{finding.get('file_path')}:{finding.get('line_number')} entropy={entropy}")

    check_results.append(
        CheckResult(
            check_id="SD-5",
            category="Detection",
            passed=entropy_valid,
            message="All entropy values valid" if entropy_valid else f"Invalid entropy: {invalid_entropy[:3]}",
            expected="0 <= entropy <= 8",
            actual="all valid" if entropy_valid else invalid_entropy,
        )
    )

    # SD-6: All secrets have masked preview
    all_masked = True
    unmasked = []

    for finding in findings:
        preview = finding.get("secret_preview", "")
        if "*" not in preview and len(preview) > 8:
            all_masked = False
            unmasked.append(finding.get("file_path"))

    check_results.append(
        CheckResult(
            check_id="SD-6",
            category="Detection",
            passed=all_masked,
            message="All secrets masked" if all_masked else f"Unmasked secrets in: {unmasked[:3]}",
            expected="all masked",
            actual="all masked" if all_masked else unmasked,
        )
    )

    return check_results
