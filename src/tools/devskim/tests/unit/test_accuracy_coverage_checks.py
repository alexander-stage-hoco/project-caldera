import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks import run_accuracy_checks, run_coverage_checks


def test_accuracy_skips_missing_categories(tmp_path):
    ground_truth = {
        "expected": {
            "aggregate_expectations": {
                "required_categories": ["insecure_crypto"]
            }
        },
        "files": {
            "InsecureCrypto.cs": {
                "expected_issues": [
                    {"category": "insecure_crypto", "count": 1}
                ],
                "total_expected": 1,
                "false_positives_allowed": 0,
            }
        },
    }
    gt_path = tmp_path / "csharp.json"
    gt_path.write_text(json.dumps(ground_truth))

    analysis = {
        "summary": {
            "issues_by_category": {
                "insecure_crypto": 1,
            },
        },
        "files": [],
    }

    results = run_accuracy_checks(analysis, str(tmp_path))
    sql_check = next(check for check in results if check.check_id == "AC-1")
    crypto_check = next(check for check in results if check.check_id == "AC-3")

    assert sql_check.passed is True
    assert sql_check.evidence.get("skipped") is True
    assert crypto_check.evidence.get("skipped") is None


def test_coverage_skips_languages_not_in_ground_truth(tmp_path):
    ground_truth = {
        "files": {
            "Sample.cs": {
                "expected_issues": [],
                "total_expected": 0,
                "false_positives_allowed": 0,
            }
        }
    }
    gt_path = tmp_path / "csharp.json"
    gt_path.write_text(json.dumps(ground_truth))

    analysis = {
        "summary": {
            "issues_by_category": {},
        },
        "files": [
            {"path": "Program.cs", "language": "csharp", "issues": []},
        ],
    }

    results = run_coverage_checks(analysis, ground_truth_dir=str(tmp_path))
    python_check = next(check for check in results if check.check_id == "CV-2")
    csharp_check = next(check for check in results if check.check_id == "CV-1")

    assert python_check.passed is True
    assert python_check.evidence.get("skipped") is True
    assert csharp_check.evidence.get("skipped") is None
