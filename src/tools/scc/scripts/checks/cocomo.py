"""COCOMO checks (CO-1 to CO-3)."""

import json
import subprocess
from pathlib import Path
from typing import List

from . import CheckResult


def run_scc_json2(base_path: Path, custom_params: str = None) -> dict:
    """Run scc with json2 format and optional custom COCOMO params."""
    scc_path = base_path / "bin" / "scc"

    cmd = [str(scc_path), "eval-repos/synthetic", "-f", "json2"]
    if custom_params:
        cmd.extend(["--cocomo-project-type", custom_params])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=base_path,
        timeout=60
    )

    if result.returncode != 0:
        raise RuntimeError(f"scc failed: {result.stderr}")

    return json.loads(result.stdout)


def check_cocomo_output_present(base_path: Path) -> CheckResult:
    """CO-1: Verify COCOMO output is present in json2."""
    try:
        data = run_scc_json2(base_path)

        # json2 format should include COCOMO estimates
        has_cost = "estimatedCost" in data
        has_schedule = "estimatedScheduleMonths" in data
        has_people = "estimatedPeople" in data

        all_present = has_cost and has_schedule and has_people

        return CheckResult(
            check_id="CO-1",
            name="COCOMO Output Present",
            passed=all_present,
            message=f"Cost: {has_cost}, Schedule: {has_schedule}, People: {has_people}",
            expected="all COCOMO fields present",
            actual={
                "estimatedCost": data.get("estimatedCost"),
                "estimatedScheduleMonths": data.get("estimatedScheduleMonths"),
                "estimatedPeople": data.get("estimatedPeople")
            }
        )

    except Exception as e:
        return CheckResult(
            check_id="CO-1",
            name="COCOMO Output Present",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_custom_params_applied(base_path: Path) -> CheckResult:
    """CO-2: Verify changing COCOMO params changes estimates."""
    try:
        # Run with default (organic)
        default_data = run_scc_json2(base_path)
        default_cost = default_data.get("estimatedCost", 0)

        # Run with embedded (higher coefficients)
        embedded_data = run_scc_json2(base_path, "embedded")
        embedded_cost = embedded_data.get("estimatedCost", 0)

        # Embedded should have higher cost than organic
        params_applied = embedded_cost > default_cost

        return CheckResult(
            check_id="CO-2",
            name="Custom Params Applied",
            passed=params_applied,
            message=f"Default: ${default_cost:,.0f}, Embedded: ${embedded_cost:,.0f}",
            expected="embedded cost > default cost",
            actual={
                "default_cost": default_cost,
                "embedded_cost": embedded_cost,
                "difference_pct": round((embedded_cost - default_cost) / default_cost * 100, 1) if default_cost > 0 else 0
            }
        )

    except Exception as e:
        return CheckResult(
            check_id="CO-2",
            name="Custom Params Applied",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_preset_values_match(base_path: Path) -> CheckResult:
    """CO-3: Verify preset values produce expected ranges."""
    try:
        # Run with custom coefficients matching our SME preset
        # a=3.0, b=1.12, c=2.5, d=0.35
        scc_path = base_path / "bin" / "scc"
        result = subprocess.run(
            [
                str(scc_path), "eval-repos/synthetic", "-f", "json2",
                "--cocomo-project-type", "custom,3.0,1.12,2.5,0.35",
                "--avg-wage", "120000",
                "--overhead", "2.4",
                "--eaf", "1.0"
            ],
            capture_output=True,
            text=True,
            cwd=base_path,
            timeout=60
        )

        if result.returncode != 0:
            raise RuntimeError(f"scc failed: {result.stderr}")

        data = json.loads(result.stdout)
        cost = data.get("estimatedCost", 0)
        schedule = data.get("estimatedScheduleMonths", 0)
        people = data.get("estimatedPeople", 0)

        # For ~6K LOC with SME params, expect:
        # - Cost: $300K - $800K range
        # - Schedule: 5-15 months
        # - People: 1-5
        cost_in_range = 300000 <= cost <= 800000
        schedule_in_range = 5 <= schedule <= 15
        people_in_range = 1 <= people <= 5

        all_in_range = cost_in_range and schedule_in_range and people_in_range

        return CheckResult(
            check_id="CO-3",
            name="Preset Values Match",
            passed=all_in_range,
            message=f"Cost: ${cost:,.0f} ({'OK' if cost_in_range else 'OUT'}), "
                    f"Schedule: {schedule:.1f}mo ({'OK' if schedule_in_range else 'OUT'}), "
                    f"People: {people:.1f} ({'OK' if people_in_range else 'OUT'})",
            expected={
                "cost_range": [300000, 800000],
                "schedule_range": [5, 15],
                "people_range": [1, 5]
            },
            actual={
                "cost": cost,
                "schedule": schedule,
                "people": people
            }
        )

    except Exception as e:
        return CheckResult(
            check_id="CO-3",
            name="Preset Values Match",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def run_cocomo_checks(base_path: Path) -> List[CheckResult]:
    """Run all COCOMO checks."""
    return [
        check_cocomo_output_present(base_path),
        check_custom_params_applied(base_path),
        check_preset_values_match(base_path),
    ]
