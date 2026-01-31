"""Tests for integration fit checks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.integration_fit import run_integration_fit_checks


def test_integration_fit_checks_pass_for_relative_paths():
    analysis = {
        "metadata": {"root_path": "/repo"},
        "files": [
            {
                "path": "src/app.py",
                "smells": [
                    {
                        "dd_smell_id": "D1_EMPTY_CATCH",
                        "dd_category": "error_handling",
                        "line_start": 1,
                        "line_end": 2,
                        "severity": "HIGH",
                    }
                ],
            }
        ],
    }

    results = run_integration_fit_checks(analysis)

    assert all(r.passed for r in results)
