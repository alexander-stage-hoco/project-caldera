"""Directory analysis checks (DA-1 to DA-12).

Updated for schema v2.0 with:
- 22 distribution fields including inequality metrics
- File classifications
- Per-language breakdown
- 8 COCOMO presets
- Structural metrics
"""

import json
import subprocess
from pathlib import Path
from typing import List, Optional, Union

from . import CheckResult


# Type alias for data input - either Path to run analyzer, or pre-computed dict
DataInput = Union[Path, dict]


# All 22 distribution fields in schema v2.0
DISTRIBUTION_FIELDS = [
    "min", "max", "mean", "median", "stddev",
    "p25", "p75", "p90", "p95", "p99",
    "skewness", "kurtosis", "cv", "iqr",
    "gini", "theil", "hoover", "palma",
    "top_10_pct_share", "top_20_pct_share", "bottom_50_pct_share"
]

# Expected COCOMO preset ordering (effort increases with org complexity)
COCOMO_ORDERING = [
    "early_startup", "growth_startup", "scale_up", "sme",
    "mid_market", "large_enterprise", "regulated"
]


def run_directory_analysis(base_path: Path) -> dict:
    """Run directory analysis and return result."""
    python_path = base_path / ".venv" / "bin" / "python"
    script_path = base_path / "scripts" / "directory_analyzer.py"
    output_path = base_path / "evaluation" / "results" / "directory_analysis_eval.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            str(python_path),
            str(script_path),
            "eval-repos/synthetic",
            "--cocomo-preset", "sme",
            "--output", str(output_path)
        ],
        capture_output=True,
        text=True,
        cwd=base_path,
        timeout=120
    )

    if result.returncode != 0:
        raise RuntimeError(f"Directory analysis failed: {result.stderr}")

    with open(output_path) as f:
        return json.load(f)


def _get_data(input_data: DataInput) -> dict:
    """Get analysis data from either a Path (runs analyzer) or pre-computed dict."""
    if isinstance(input_data, dict):
        return input_data
    return run_directory_analysis(input_data)


def check_directory_stats_complete(input_data: DataInput) -> CheckResult:
    """DA-1: Verify all directories have direct/recursive stats."""
    try:
        data = _get_data(input_data)
        directories = data.get("directories", [])

        complete_count = 0
        for d in directories:
            has_direct = "direct" in d and isinstance(d["direct"], dict)
            has_recursive = "recursive" in d and isinstance(d["recursive"], dict)
            if has_direct and has_recursive:
                complete_count += 1

        all_complete = complete_count == len(directories)

        return CheckResult(
            check_id="DA-1",
            name="Directory Stats Complete",
            passed=all_complete,
            message=f"{complete_count}/{len(directories)} directories have complete stats",
            expected=len(directories),
            actual=complete_count,
            evidence={"total_directories": len(directories)}
        )

    except Exception as e:
        return CheckResult(
            check_id="DA-1",
            name="Directory Stats Complete",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_distribution_stats_valid(input_data: DataInput) -> CheckResult:
    """DA-2: Verify all distributions have all 22 required fields."""
    try:
        data = _get_data(input_data)
        directories = data.get("directories", [])

        valid_count = 0
        total_with_dist = 0
        missing_fields = []

        for d in directories:
            # Check loc_distribution in recursive stats
            loc_dist = d.get("recursive", {}).get("loc_distribution")
            if loc_dist:
                total_with_dist += 1
                missing = [f for f in DISTRIBUTION_FIELDS if f not in loc_dist]
                if not missing:
                    valid_count += 1
                else:
                    missing_fields.append({
                        "path": d.get("path"),
                        "missing": missing[:5]  # Limit for readability
                    })

        all_valid = valid_count == total_with_dist

        return CheckResult(
            check_id="DA-2",
            name="Distribution Stats Valid (22 fields)",
            passed=all_valid,
            message=f"{valid_count}/{total_with_dist} distributions have all 22 fields",
            expected=total_with_dist,
            actual=valid_count,
            evidence={
                "required_fields": len(DISTRIBUTION_FIELDS),
                "missing_examples": missing_fields[:3] if missing_fields else []
            }
        )

    except Exception as e:
        return CheckResult(
            check_id="DA-2",
            name="Distribution Stats Valid (22 fields)",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_structural_metrics_valid(input_data: DataInput) -> CheckResult:
    """DA-3: Verify structural metrics are consistent (is_leaf, child_count, depth)."""
    try:
        data = _get_data(input_data)
        directories = data.get("directories", [])

        valid_count = 0
        violations = []

        for d in directories:
            is_leaf = d.get("is_leaf", False)
            child_count = d.get("child_count", 0)
            depth = d.get("depth", 0)

            # is_leaf should match child_count == 0
            leaf_consistent = is_leaf == (child_count == 0)
            # depth should be non-negative
            depth_valid = depth >= 0

            if leaf_consistent and depth_valid:
                valid_count += 1
            else:
                violations.append({
                    "path": d.get("path"),
                    "is_leaf": is_leaf,
                    "child_count": child_count,
                    "depth": depth
                })

        all_valid = valid_count == len(directories)

        return CheckResult(
            check_id="DA-3",
            name="Structural Metrics Valid",
            passed=all_valid,
            message=f"{valid_count}/{len(directories)} directories have valid structural metrics",
            expected=len(directories),
            actual=valid_count,
            evidence={"violations": violations[:5]} if violations else {}
        )

    except Exception as e:
        return CheckResult(
            check_id="DA-3",
            name="Structural Metrics Valid",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_file_count_matches(input_data: DataInput) -> CheckResult:
    """DA-4: Verify sum of direct.file_count equals total files."""
    try:
        data = _get_data(input_data)
        directories = data.get("directories", [])
        summary = data.get("summary", {})
        total_files = summary.get("total_files", 0)

        # Sum of direct.file_count for each directory
        direct_files_sum = sum(
            d.get("direct", {}).get("file_count", 0)
            for d in directories
        )

        # Also verify root files array matches
        root_files_count = len(data.get("files", []))

        matches = direct_files_sum == total_files and root_files_count == total_files

        return CheckResult(
            check_id="DA-4",
            name="File Count Matches",
            passed=matches,
            message=f"Sum of direct.file_count ({direct_files_sum}), root files ({root_files_count}), total ({total_files})",
            expected=total_files,
            actual=direct_files_sum,
            evidence={"root_files_count": root_files_count}
        )

    except Exception as e:
        return CheckResult(
            check_id="DA-4",
            name="File Count Matches",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_recursive_includes_direct(input_data: DataInput) -> CheckResult:
    """DA-5: Verify recursive.file_count >= direct.file_count for each directory."""
    try:
        data = _get_data(input_data)
        directories = data.get("directories", [])

        valid_count = 0
        violations = []

        for d in directories:
            direct_count = d.get("direct", {}).get("file_count", 0)
            recursive_count = d.get("recursive", {}).get("file_count", 0)

            if recursive_count >= direct_count:
                valid_count += 1
            else:
                violations.append({
                    "path": d.get("path"),
                    "direct": direct_count,
                    "recursive": recursive_count
                })

        all_valid = valid_count == len(directories)

        return CheckResult(
            check_id="DA-5",
            name="Recursive Includes Direct",
            passed=all_valid,
            message=f"{valid_count}/{len(directories)} directories have recursive >= direct",
            expected=len(directories),
            actual=valid_count,
            evidence={"violations": violations[:5]} if violations else {}
        )

    except Exception as e:
        return CheckResult(
            check_id="DA-5",
            name="Recursive Includes Direct",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_inequality_metrics_valid(input_data: DataInput) -> CheckResult:
    """DA-6: Verify all inequality metrics are present and in valid ranges."""
    try:
        data = _get_data(input_data)
        directories = data.get("directories", [])

        valid_count = 0
        total_checked = 0
        violations = []

        for d in directories:
            loc_dist = d.get("recursive", {}).get("loc_distribution")
            if loc_dist:
                total_checked += 1
                issues = []

                # Check ranges
                gini = loc_dist.get("gini", 0)
                if not (0 <= gini <= 1):
                    issues.append(f"gini={gini} not in [0,1]")

                theil = loc_dist.get("theil", 0)
                if theil < 0:
                    issues.append(f"theil={theil} < 0")

                hoover = loc_dist.get("hoover", 0)
                if not (0 <= hoover <= 1):
                    issues.append(f"hoover={hoover} not in [0,1]")

                palma = loc_dist.get("palma", 0)
                if palma < 0:
                    issues.append(f"palma={palma} < 0")

                for share in ["top_10_pct_share", "top_20_pct_share", "bottom_50_pct_share"]:
                    val = loc_dist.get(share, 0)
                    if not (0 <= val <= 1):
                        issues.append(f"{share}={val} not in [0,1]")

                if not issues:
                    valid_count += 1
                else:
                    violations.append({"path": d.get("path"), "issues": issues})

        all_valid = valid_count == total_checked

        return CheckResult(
            check_id="DA-6",
            name="Inequality Metrics Valid",
            passed=all_valid,
            message=f"{valid_count}/{total_checked} distributions have valid inequality metrics",
            expected=total_checked,
            actual=valid_count,
            evidence={"violations": violations[:3]} if violations else {}
        )

    except Exception as e:
        return CheckResult(
            check_id="DA-6",
            name="Inequality Metrics Valid",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_file_classification_counts(input_data: DataInput) -> CheckResult:
    """DA-7: Verify file classification counts sum to total files."""
    try:
        data = _get_data(input_data)
        summary = data.get("summary", {})
        fc = summary.get("file_classifications", {})
        total_files = summary.get("total_files", 0)

        classification_sum = (
            fc.get("test_file_count", 0) +
            fc.get("config_file_count", 0) +
            fc.get("docs_file_count", 0) +
            fc.get("build_file_count", 0) +
            fc.get("ci_file_count", 0) +
            fc.get("source_file_count", 0)
        )

        matches = classification_sum == total_files

        return CheckResult(
            check_id="DA-7",
            name="File Classification Counts",
            passed=matches,
            message=f"Classification sum ({classification_sum}) {'==' if matches else '!='} total_files ({total_files})",
            expected=total_files,
            actual=classification_sum,
            evidence={"classifications": fc}
        )

    except Exception as e:
        return CheckResult(
            check_id="DA-7",
            name="File Classification Counts",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_per_language_consistency(input_data: DataInput) -> CheckResult:
    """DA-8: Verify per-language LOC sums match aggregate."""
    try:
        data = _get_data(input_data)
        summary = data.get("summary", {})
        by_language = summary.get("by_language", {})
        total_loc = summary.get("total_loc", 0)

        lang_loc_sum = sum(
            lang_stats.get("lines_code", 0)
            for lang_stats in by_language.values()
        )

        matches = lang_loc_sum == total_loc

        return CheckResult(
            check_id="DA-8",
            name="Per-Language Consistency",
            passed=matches,
            message=f"Language LOC sum ({lang_loc_sum}) {'==' if matches else '!='} total_loc ({total_loc})",
            expected=total_loc,
            actual=lang_loc_sum,
            evidence={"language_count": len(by_language)}
        )

    except Exception as e:
        return CheckResult(
            check_id="DA-8",
            name="Per-Language Consistency",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_cocomo_preset_ordering(input_data: DataInput) -> CheckResult:
    """DA-9: Verify COCOMO effort increases with org complexity."""
    try:
        data = _get_data(input_data)
        cocomo = data.get("summary", {}).get("cocomo", {})

        violations = []
        for i in range(len(COCOMO_ORDERING) - 1):
            curr_preset = COCOMO_ORDERING[i]
            next_preset = COCOMO_ORDERING[i + 1]
            curr = cocomo.get(curr_preset, {}).get("effort_person_months", 0)
            next_val = cocomo.get(next_preset, {}).get("effort_person_months", 0)

            if curr > next_val:
                violations.append(f"{curr_preset} ({curr:.1f}) > {next_preset} ({next_val:.1f})")

        # Open source cost should be 0
        open_source_cost = cocomo.get("open_source", {}).get("cost", -1)
        if open_source_cost != 0:
            violations.append(f"open_source cost ({open_source_cost}) != 0")

        # All 8 presets present
        all_presets = COCOMO_ORDERING + ["open_source"]
        missing = [p for p in all_presets if p not in cocomo]
        if missing:
            violations.append(f"Missing presets: {missing}")

        all_valid = len(violations) == 0

        return CheckResult(
            check_id="DA-9",
            name="COCOMO Preset Ordering",
            passed=all_valid,
            message="COCOMO presets valid" if all_valid else f"Issues: {len(violations)}",
            expected=0,
            actual=len(violations),
            evidence={"violations": violations} if violations else {"presets_checked": len(all_presets)}
        )

    except Exception as e:
        return CheckResult(
            check_id="DA-9",
            name="COCOMO Preset Ordering",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_p99_monotonicity(input_data: DataInput) -> CheckResult:
    """DA-10: Verify p95 <= p99 <= max for all distributions."""
    try:
        data = _get_data(input_data)
        directories = data.get("directories", [])

        valid_count = 0
        total_checked = 0
        violations = []

        for d in directories:
            loc_dist = d.get("recursive", {}).get("loc_distribution")
            if loc_dist:
                total_checked += 1
                p95 = loc_dist.get("p95", 0)
                p99 = loc_dist.get("p99", 0)
                max_val = loc_dist.get("max", 0)

                if p95 <= p99 <= max_val:
                    valid_count += 1
                else:
                    violations.append({
                        "path": d.get("path"),
                        "p95": p95, "p99": p99, "max": max_val
                    })

        all_valid = valid_count == total_checked

        return CheckResult(
            check_id="DA-10",
            name="P99 Monotonicity",
            passed=all_valid,
            message=f"{valid_count}/{total_checked} distributions have p95 <= p99 <= max",
            expected=total_checked,
            actual=valid_count,
            evidence={"violations": violations[:3]} if violations else {}
        )

    except Exception as e:
        return CheckResult(
            check_id="DA-10",
            name="P99 Monotonicity",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_summary_structure(input_data: DataInput) -> CheckResult:
    """DA-11: Verify all 7 summary subsections are present."""
    try:
        data = _get_data(input_data)
        summary = data.get("summary", {})

        required_sections = [
            "structure", "ratios", "file_classifications",
            "languages", "distributions", "by_language", "cocomo"
        ]

        present = [s for s in required_sections if s in summary]
        missing = [s for s in required_sections if s not in summary]

        all_present = len(missing) == 0

        return CheckResult(
            check_id="DA-11",
            name="Summary Structure Complete",
            passed=all_present,
            message=f"{len(present)}/{len(required_sections)} summary sections present",
            expected=len(required_sections),
            actual=len(present),
            evidence={"missing": missing} if missing else {}
        )

    except Exception as e:
        return CheckResult(
            check_id="DA-11",
            name="Summary Structure Complete",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_file_entry_fields(input_data: DataInput) -> CheckResult:
    """DA-12: Verify all file entries have required fields."""
    try:
        data = _get_data(input_data)
        files = data.get("files", [])

        required_fields = [
            "path", "filename", "directory", "language", "extension",
            "lines_total", "lines_code", "lines_comment", "lines_blank",
            "bytes", "complexity", "uloc",
            "comment_ratio", "blank_ratio", "code_ratio",
            "complexity_density", "dryness", "bytes_per_loc",
            "is_minified", "is_generated", "is_binary", "classification"
        ]

        valid_count = 0
        missing_examples = []

        for f in files:
            missing = [field for field in required_fields if field not in f]
            if not missing:
                valid_count += 1
            elif len(missing_examples) < 3:
                missing_examples.append({
                    "path": f.get("path", "unknown"),
                    "missing": missing[:5]
                })

        all_valid = valid_count == len(files)

        return CheckResult(
            check_id="DA-12",
            name="File Entry Fields Complete",
            passed=all_valid,
            message=f"{valid_count}/{len(files)} files have all {len(required_fields)} fields",
            expected=len(files),
            actual=valid_count,
            evidence={"missing_examples": missing_examples} if missing_examples else {}
        )

    except Exception as e:
        return CheckResult(
            check_id="DA-12",
            name="File Entry Fields Complete",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def run_directory_analysis_checks(input_data: DataInput) -> List[CheckResult]:
    """Run all directory analysis checks (DA-1 to DA-12).

    Args:
        input_data: Either a Path to the project root (will run analyzer),
                   or a pre-computed dict of analysis results.
    """
    return [
        check_directory_stats_complete(input_data),
        check_distribution_stats_valid(input_data),
        check_structural_metrics_valid(input_data),  # Replaced hotspot_scores
        check_file_count_matches(input_data),
        check_recursive_includes_direct(input_data),
        check_inequality_metrics_valid(input_data),
        check_file_classification_counts(input_data),
        check_per_language_consistency(input_data),
        check_cocomo_preset_ordering(input_data),
        check_p99_monotonicity(input_data),
        check_summary_structure(input_data),
        check_file_entry_fields(input_data),
    ]
