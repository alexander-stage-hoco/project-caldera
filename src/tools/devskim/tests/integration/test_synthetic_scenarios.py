"""Integration tests for synthetic repository scenarios."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from security_analyzer import (
    analyze_with_devskim,
    result_to_dict,
    get_devskim_version,
)
from checks import load_ground_truth

# Paths
TOOL_ROOT = Path(__file__).parents[2]
SYNTHETIC_REPOS = TOOL_ROOT / "eval-repos" / "synthetic"
GROUND_TRUTH_DIR = TOOL_ROOT / "evaluation" / "ground-truth"
CUSTOM_RULES_DIR = TOOL_ROOT / "rules" / "custom"


def is_devskim_available() -> bool:
    """Check if DevSkim is available."""
    version = get_devskim_version()
    return version != "unknown"


def get_custom_rules_path() -> str | None:
    """Get custom rules path if directory exists."""
    if CUSTOM_RULES_DIR.exists():
        return str(CUSTOM_RULES_DIR)
    return None


def skip_if_missing_deps():
    """Skip if DevSkim or synthetic repos are missing."""
    if not is_devskim_available():
        pytest.skip("DevSkim not available (run make setup)")
    if not SYNTHETIC_REPOS.exists():
        pytest.skip("Synthetic repos missing")


@pytest.fixture
def ground_truth() -> dict[str, dict]:
    """Load all ground truth files."""
    truths = {}
    for gt_file in GROUND_TRUTH_DIR.glob("*.json"):
        truths[gt_file.stem] = json.loads(gt_file.read_text())
    return truths


@pytest.mark.integration
class TestCSharpScenario:
    """Tests for the C# synthetic repository."""

    def test_csharp_repo_analyzed(self) -> None:
        """C# repository should be successfully analyzed."""
        skip_if_missing_deps()

        repo_path = SYNTHETIC_REPOS / "csharp"
        if not repo_path.exists():
            pytest.skip("C# synthetic repo not built")

        result = analyze_with_devskim(
            str(repo_path),
            repo_name="csharp-synthetic",
            custom_rules_path=get_custom_rules_path(),
        )

        assert len(result.files) > 0
        assert any(f.language == "csharp" for f in result.files)

    def test_csharp_detects_expected_issues(self, ground_truth: dict) -> None:
        """C# analysis should detect expected issues."""
        skip_if_missing_deps()

        repo_path = SYNTHETIC_REPOS / "csharp"
        if not repo_path.exists():
            pytest.skip("C# synthetic repo not built")

        result = analyze_with_devskim(
            str(repo_path),
            repo_name="csharp-synthetic",
            custom_rules_path=get_custom_rules_path(),
        )

        gt = ground_truth.get("csharp", {})
        expected = gt.get("expected", {}).get("aggregate_expectations", {})
        min_total = expected.get("min_total_issues", 0)

        total_issues = len(result.findings)
        assert total_issues >= min_total, (
            f"Expected >= {min_total} issues, found {total_issues}"
        )

    def test_csharp_covers_required_categories(self, ground_truth: dict) -> None:
        """C# analysis should cover required security categories."""
        skip_if_missing_deps()

        repo_path = SYNTHETIC_REPOS / "csharp"
        if not repo_path.exists():
            pytest.skip("C# synthetic repo not built")

        result = analyze_with_devskim(
            str(repo_path),
            repo_name="csharp-synthetic",
            custom_rules_path=get_custom_rules_path(),
        )

        gt = ground_truth.get("csharp", {})
        expected = gt.get("expected", {}).get("aggregate_expectations", {})
        required_cats = expected.get("required_categories", [])

        detected_cats = set(result.by_category.keys())
        for cat in required_cats:
            assert cat in detected_cats or result.by_category.get(cat, 0) > 0, (
                f"Required category '{cat}' not detected"
            )


@pytest.mark.integration
class TestInsecureCryptoFile:
    """Tests for InsecureCrypto.cs file analysis."""

    def test_detects_md5_usage(self) -> None:
        """Should detect MD5 weak hash usage."""
        skip_if_missing_deps()

        repo_path = SYNTHETIC_REPOS / "csharp"
        if not repo_path.exists():
            pytest.skip("C# synthetic repo not built")

        result = analyze_with_devskim(
            str(repo_path),
            repo_name="csharp-synthetic",
            custom_rules_path=get_custom_rules_path(),
        )

        # Find InsecureCrypto.cs findings
        crypto_file = next(
            (f for f in result.files if "InsecureCrypto.cs" in f.path),
            None,
        )

        assert crypto_file is not None, "InsecureCrypto.cs not found in results"
        assert crypto_file.issue_count > 0, "InsecureCrypto.cs should have issues"
        assert crypto_file.by_category.get("insecure_crypto", 0) > 0

    def test_matches_ground_truth_count(self, ground_truth: dict) -> None:
        """Detected issues should match ground truth expectations."""
        skip_if_missing_deps()

        repo_path = SYNTHETIC_REPOS / "csharp"
        if not repo_path.exists():
            pytest.skip("C# synthetic repo not built")

        result = analyze_with_devskim(
            str(repo_path),
            repo_name="csharp-synthetic",
            custom_rules_path=get_custom_rules_path(),
        )

        gt = ground_truth.get("csharp", {})
        file_gt = gt.get("files", {}).get("InsecureCrypto.cs", {})
        expected_total = file_gt.get("total_expected", 0)

        crypto_file = next(
            (f for f in result.files if "InsecureCrypto.cs" in f.path),
            None,
        )

        if crypto_file and expected_total > 0:
            # Allow some tolerance
            assert crypto_file.issue_count >= expected_total * 0.5, (
                f"Expected >= {expected_total * 0.5} issues, got {crypto_file.issue_count}"
            )


@pytest.mark.integration
class TestDeserializationFile:
    """Tests for Deserialization.cs file analysis."""

    def test_detects_unsafe_deserialization(self) -> None:
        """Should detect unsafe deserialization patterns."""
        skip_if_missing_deps()

        repo_path = SYNTHETIC_REPOS / "csharp"
        if not repo_path.exists():
            pytest.skip("C# synthetic repo not built")

        result = analyze_with_devskim(
            str(repo_path),
            repo_name="csharp-synthetic",
            custom_rules_path=get_custom_rules_path(),
        )

        # Find Deserialization.cs findings
        deser_file = next(
            (f for f in result.files if "Deserialization.cs" in f.path),
            None,
        )

        assert deser_file is not None, "Deserialization.cs not found in results"
        assert deser_file.issue_count > 0, "Deserialization.cs should have issues"


@pytest.mark.integration
class TestSafeCodeFile:
    """Tests for SafeCode.cs file analysis."""

    def test_clean_code_minimal_issues(self) -> None:
        """SafeCode.cs should have minimal or no issues."""
        skip_if_missing_deps()

        repo_path = SYNTHETIC_REPOS / "csharp"
        if not repo_path.exists():
            pytest.skip("C# synthetic repo not built")

        result = analyze_with_devskim(
            str(repo_path),
            repo_name="csharp-synthetic",
            custom_rules_path=get_custom_rules_path(),
        )

        safe_file = next(
            (f for f in result.files if "SafeCode.cs" in f.path),
            None,
        )

        if safe_file:
            # Allow 0-1 issues (potential false positives)
            assert safe_file.issue_count <= 1, (
                f"SafeCode.cs should be clean, found {safe_file.issue_count} issues"
            )


@pytest.mark.integration
class TestOutputFormatValidation:
    """Tests validating output format across scenarios."""

    def test_output_format_has_required_fields(self) -> None:
        """Output format should have all required fields."""
        skip_if_missing_deps()

        repo_path = SYNTHETIC_REPOS / "csharp"
        if not repo_path.exists():
            pytest.skip("C# synthetic repo not built")

        result = analyze_with_devskim(
            str(repo_path),
            repo_name="csharp-synthetic",
            custom_rules_path=get_custom_rules_path(),
        )
        output = result_to_dict(result)

        # Check root fields
        assert "schema_version" in output
        assert "generated_at" in output
        assert "repo_name" in output
        assert "repo_path" in output
        assert "results" in output

        # Check results fields
        results = output["results"]
        assert results["tool"] == "devskim"
        assert "tool_version" in results
        assert "metadata" in results
        assert "summary" in results
        assert "files" in results

    def test_files_have_required_fields(self) -> None:
        """Each file entry should have required fields."""
        skip_if_missing_deps()

        repo_path = SYNTHETIC_REPOS / "csharp"
        if not repo_path.exists():
            pytest.skip("C# synthetic repo not built")

        result = analyze_with_devskim(
            str(repo_path),
            repo_name="csharp-synthetic",
            custom_rules_path=get_custom_rules_path(),
        )
        output = result_to_dict(result)

        required_file_fields = [
            "path",
            "language",
            "lines",
            "issue_count",
            "issue_density",
        ]

        for file_entry in output["results"]["files"]:
            for field in required_file_fields:
                assert field in file_entry, f"Missing field '{field}' in file entry"


@pytest.mark.integration
class TestDirectoryRollups:
    """Tests for directory rollup metrics."""

    def test_directory_rollups_computed(self) -> None:
        """Directory rollups should be computed."""
        skip_if_missing_deps()

        repo_path = SYNTHETIC_REPOS / "csharp"
        if not repo_path.exists():
            pytest.skip("C# synthetic repo not built")

        result = analyze_with_devskim(
            str(repo_path),
            repo_name="csharp-synthetic",
            custom_rules_path=get_custom_rules_path(),
        )

        # Should have directory entries
        assert len(result.directories) > 0

    def test_root_directory_aggregates_all(self) -> None:
        """Root directory should aggregate all files."""
        skip_if_missing_deps()

        repo_path = SYNTHETIC_REPOS / "csharp"
        if not repo_path.exists():
            pytest.skip("C# synthetic repo not built")

        result = analyze_with_devskim(
            str(repo_path),
            repo_name="csharp-synthetic",
            custom_rules_path=get_custom_rules_path(),
        )

        root_dir = next(
            (d for d in result.directories if d.path == "."),
            None,
        )

        assert root_dir is not None
        assert root_dir.recursive.file_count == len(result.files)
        assert root_dir.recursive.issue_count == len(result.findings)
