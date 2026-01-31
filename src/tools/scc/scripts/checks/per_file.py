"""Per-file output checks (PF-1 to PF-6)."""

import json
import subprocess
from pathlib import Path
from typing import List

from . import CheckResult


def run_scc_by_file(base_path: Path) -> tuple:
    """Run scc with --by-file and return output."""
    scc_path = base_path / "bin" / "scc"
    result = subprocess.run(
        [str(scc_path), "eval-repos/synthetic", "--by-file", "--uloc", "--min", "--gen", "-f", "json"],
        capture_output=True,
        text=True,
        cwd=base_path,
        timeout=60
    )
    return result.stdout, result.returncode, result.stderr


def check_per_file_json_valid(base_path: Path) -> CheckResult:
    """PF-1: Verify per-file JSON output is valid."""
    try:
        stdout, exit_code, stderr = run_scc_by_file(base_path)

        if exit_code != 0:
            return CheckResult(
                check_id="PF-1",
                name="Per-File JSON Valid",
                passed=False,
                message=f"scc failed with exit code {exit_code}",
                expected="exit code 0",
                actual=f"exit code {exit_code}",
                evidence={"stderr": stderr[:200] if stderr else ""}
            )

        data = json.loads(stdout)
        return CheckResult(
            check_id="PF-1",
            name="Per-File JSON Valid",
            passed=True,
            message=f"Valid JSON with {len(data)} language entries",
            expected="valid JSON",
            actual=f"{len(data)} language entries"
        )

    except json.JSONDecodeError as e:
        return CheckResult(
            check_id="PF-1",
            name="Per-File JSON Valid",
            passed=False,
            message=f"Invalid JSON: {e}",
            expected="valid JSON",
            actual=str(e)
        )
    except Exception as e:
        return CheckResult(
            check_id="PF-1",
            name="Per-File JSON Valid",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_files_have_location(base_path: Path) -> CheckResult:
    """PF-2: Verify all file entries have Location field."""
    try:
        stdout, exit_code, _ = run_scc_by_file(base_path)
        if exit_code != 0:
            return CheckResult(
                check_id="PF-2",
                name="Files Have Location",
                passed=False,
                message=f"scc failed with exit code {exit_code}"
            )

        data = json.loads(stdout)
        all_files = []
        for lang in data:
            if "Files" in lang:
                all_files.extend(lang["Files"])

        files_with_location = sum(1 for f in all_files if "Location" in f and f["Location"])
        all_have_location = files_with_location == len(all_files)

        return CheckResult(
            check_id="PF-2",
            name="Files Have Location",
            passed=all_have_location,
            message=f"{files_with_location}/{len(all_files)} files have Location field",
            expected=len(all_files),
            actual=files_with_location,
            evidence={"sample_locations": [f.get("Location", "")[:50] for f in all_files[:3]]}
        )

    except Exception as e:
        return CheckResult(
            check_id="PF-2",
            name="Files Have Location",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_files_have_complexity(base_path: Path) -> CheckResult:
    """PF-3: Verify all files have Complexity >= 0."""
    try:
        stdout, exit_code, _ = run_scc_by_file(base_path)
        if exit_code != 0:
            return CheckResult(
                check_id="PF-3",
                name="Files Have Complexity",
                passed=False,
                message=f"scc failed with exit code {exit_code}"
            )

        data = json.loads(stdout)
        all_files = []
        for lang in data:
            if "Files" in lang:
                all_files.extend(lang["Files"])

        files_with_complexity = sum(
            1 for f in all_files
            if "Complexity" in f and isinstance(f["Complexity"], int) and f["Complexity"] >= 0
        )
        all_have_complexity = files_with_complexity == len(all_files)

        return CheckResult(
            check_id="PF-3",
            name="Files Have Complexity",
            passed=all_have_complexity,
            message=f"{files_with_complexity}/{len(all_files)} files have valid Complexity",
            expected=len(all_files),
            actual=files_with_complexity
        )

    except Exception as e:
        return CheckResult(
            check_id="PF-3",
            name="Files Have Complexity",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_files_have_uloc(base_path: Path) -> CheckResult:
    """PF-4: Verify all files have Uloc field with --uloc."""
    try:
        stdout, exit_code, _ = run_scc_by_file(base_path)
        if exit_code != 0:
            return CheckResult(
                check_id="PF-4",
                name="Files Have ULOC",
                passed=False,
                message=f"scc failed with exit code {exit_code}"
            )

        data = json.loads(stdout)
        all_files = []
        for lang in data:
            if "Files" in lang:
                all_files.extend(lang["Files"])

        # Note: Uloc might be 0 for some files, but the field should be present
        files_with_uloc = sum(
            1 for f in all_files
            if "Uloc" in f and isinstance(f["Uloc"], int) and f["Uloc"] >= 0
        )
        all_have_uloc = files_with_uloc == len(all_files)

        return CheckResult(
            check_id="PF-4",
            name="Files Have ULOC",
            passed=all_have_uloc,
            message=f"{files_with_uloc}/{len(all_files)} files have Uloc field",
            expected=len(all_files),
            actual=files_with_uloc
        )

    except Exception as e:
        return CheckResult(
            check_id="PF-4",
            name="Files Have ULOC",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_minified_detection(base_path: Path) -> CheckResult:
    """PF-5: Verify Minified field is present with --min."""
    try:
        stdout, exit_code, _ = run_scc_by_file(base_path)
        if exit_code != 0:
            return CheckResult(
                check_id="PF-5",
                name="Minified Detection",
                passed=False,
                message=f"scc failed with exit code {exit_code}"
            )

        data = json.loads(stdout)
        all_files = []
        for lang in data:
            if "Files" in lang:
                all_files.extend(lang["Files"])

        files_with_minified = sum(1 for f in all_files if "Minified" in f)
        all_have_minified = files_with_minified == len(all_files)

        minified_count = sum(1 for f in all_files if f.get("Minified", False))

        return CheckResult(
            check_id="PF-5",
            name="Minified Detection",
            passed=all_have_minified,
            message=f"Minified field present: {files_with_minified}/{len(all_files)}, flagged: {minified_count}",
            expected=len(all_files),
            actual=files_with_minified,
            evidence={"minified_count": minified_count}
        )

    except Exception as e:
        return CheckResult(
            check_id="PF-5",
            name="Minified Detection",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_generated_detection(base_path: Path) -> CheckResult:
    """PF-6: Verify Generated field is present with --gen."""
    try:
        stdout, exit_code, _ = run_scc_by_file(base_path)
        if exit_code != 0:
            return CheckResult(
                check_id="PF-6",
                name="Generated Detection",
                passed=False,
                message=f"scc failed with exit code {exit_code}"
            )

        data = json.loads(stdout)
        all_files = []
        for lang in data:
            if "Files" in lang:
                all_files.extend(lang["Files"])

        files_with_generated = sum(1 for f in all_files if "Generated" in f)
        all_have_generated = files_with_generated == len(all_files)

        generated_count = sum(1 for f in all_files if f.get("Generated", False))

        return CheckResult(
            check_id="PF-6",
            name="Generated Detection",
            passed=all_have_generated,
            message=f"Generated field present: {files_with_generated}/{len(all_files)}, flagged: {generated_count}",
            expected=len(all_files),
            actual=files_with_generated,
            evidence={"generated_count": generated_count}
        )

    except Exception as e:
        return CheckResult(
            check_id="PF-6",
            name="Generated Detection",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def run_per_file_checks(base_path: Path) -> List[CheckResult]:
    """Run all per-file output checks."""
    return [
        check_per_file_json_valid(base_path),
        check_files_have_location(base_path),
        check_files_have_complexity(base_path),
        check_files_have_uloc(base_path),
        check_minified_detection(base_path),
        check_generated_detection(base_path),
    ]
