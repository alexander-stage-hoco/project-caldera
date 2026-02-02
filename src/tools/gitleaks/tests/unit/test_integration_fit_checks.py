"""Tests for integration fit checks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.integration_fit import run_integration_fit_checks


def test_integration_fit_checks_pass_for_relative_paths():
    analysis = {
        "findings": [
            {"file_path": "src/config.env"},
            {"file_path": "secrets.txt"},
        ]
    }

    results = run_integration_fit_checks(analysis)

    assert results[0].passed
