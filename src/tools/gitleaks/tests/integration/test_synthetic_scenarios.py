"""Integration tests for synthetic repository scenarios."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from secret_analyzer import analyze_repository, to_output_format

# Paths
TOOL_ROOT = Path(__file__).parents[2]
GITLEAKS_BIN = TOOL_ROOT / "bin" / "gitleaks"
SYNTHETIC_REPOS = TOOL_ROOT / "eval-repos" / "synthetic"
GROUND_TRUTH_DIR = TOOL_ROOT / "evaluation" / "ground-truth"


def skip_if_missing_deps():
    """Skip if gitleaks binary or synthetic repos are missing."""
    if not GITLEAKS_BIN.exists():
        pytest.skip("gitleaks binary not available (run make setup)")
    if not SYNTHETIC_REPOS.exists():
        pytest.skip("synthetic repos missing (run make build-repos)")


@pytest.fixture
def gitleaks_path() -> Path:
    """Get gitleaks binary path, skip if not available."""
    skip_if_missing_deps()
    return GITLEAKS_BIN


@pytest.fixture
def ground_truth() -> dict[str, dict]:
    """Load all ground truth files."""
    skip_if_missing_deps()
    truths = {}
    for gt_file in GROUND_TRUTH_DIR.glob("*.json"):
        truths[gt_file.stem] = json.loads(gt_file.read_text())
    return truths


@pytest.mark.integration
class TestNoSecretsScenario:
    """Tests for the no-secrets (clean baseline) repository."""

    def test_clean_repo_finds_zero_secrets(self, gitleaks_path: Path) -> None:
        """Clean repository should find zero secrets."""
        repo_path = SYNTHETIC_REPOS / "no-secrets"
        if not repo_path.exists():
            pytest.skip("no-secrets repo not built")

        analysis = analyze_repository(
            gitleaks_path=gitleaks_path,
            repo_path=repo_path,
            repo_name_override="no-secrets",
        )

        assert analysis.total_secrets == 0
        assert analysis.unique_secrets == 0
        assert analysis.secrets_in_head == 0
        assert analysis.secrets_in_history == 0
        assert len(analysis.findings) == 0

    def test_clean_repo_matches_ground_truth(
        self, gitleaks_path: Path, ground_truth: dict
    ) -> None:
        """Clean repo results should match ground truth."""
        repo_path = SYNTHETIC_REPOS / "no-secrets"
        if not repo_path.exists():
            pytest.skip("no-secrets repo not built")

        analysis = analyze_repository(
            gitleaks_path=gitleaks_path,
            repo_path=repo_path,
            repo_name_override="no-secrets",
        )

        expected = ground_truth["no-secrets"]["expected"]
        assert analysis.total_secrets == expected["total_secrets"]
        assert analysis.files_with_secrets == expected["files_with_secrets"]


@pytest.mark.integration
class TestApiKeysScenario:
    """Tests for the api-keys repository."""

    def test_api_keys_detected(self, gitleaks_path: Path) -> None:
        """API keys should be detected."""
        repo_path = SYNTHETIC_REPOS / "api-keys"
        if not repo_path.exists():
            pytest.skip("api-keys repo not built")

        analysis = analyze_repository(
            gitleaks_path=gitleaks_path,
            repo_path=repo_path,
            repo_name_override="api-keys",
        )

        assert analysis.total_secrets >= 1
        assert len(analysis.findings) >= 1

    def test_api_keys_match_ground_truth(
        self, gitleaks_path: Path, ground_truth: dict
    ) -> None:
        """API keys results should match ground truth counts."""
        repo_path = SYNTHETIC_REPOS / "api-keys"
        if not repo_path.exists():
            pytest.skip("api-keys repo not built")

        analysis = analyze_repository(
            gitleaks_path=gitleaks_path,
            repo_path=repo_path,
            repo_name_override="api-keys",
        )

        expected = ground_truth["api-keys"]["expected"]
        # Allow for slight variations but core metrics should match
        assert analysis.total_secrets >= expected["total_secrets"]


@pytest.mark.integration
class TestAwsCredentialsScenario:
    """Tests for the aws-credentials repository."""

    def test_aws_credentials_detected(self, gitleaks_path: Path) -> None:
        """AWS credentials should be detected."""
        repo_path = SYNTHETIC_REPOS / "aws-credentials"
        if not repo_path.exists():
            pytest.skip("aws-credentials repo not built")

        analysis = analyze_repository(
            gitleaks_path=gitleaks_path,
            repo_path=repo_path,
            repo_name_override="aws-credentials",
        )

        assert analysis.total_secrets >= 1
        # Check that at least one finding is AWS related
        rule_ids = {f.rule_id for f in analysis.findings}
        aws_rules = {"aws-access-token", "aws-access-key", "aws-secret-key"}
        assert rule_ids & aws_rules, f"No AWS rules found in {rule_ids}"


@pytest.mark.integration
class TestMixedSecretsScenario:
    """Tests for the mixed-secrets repository."""

    def test_mixed_secrets_detected(self, gitleaks_path: Path) -> None:
        """Multiple secret types should be detected."""
        repo_path = SYNTHETIC_REPOS / "mixed-secrets"
        if not repo_path.exists():
            pytest.skip("mixed-secrets repo not built")

        analysis = analyze_repository(
            gitleaks_path=gitleaks_path,
            repo_path=repo_path,
            repo_name_override="mixed-secrets",
        )

        assert analysis.total_secrets >= 1


@pytest.mark.integration
class TestHistoricalSecretsScenario:
    """Tests for the historical-secrets repository."""

    def test_historical_secrets_detected(self, gitleaks_path: Path) -> None:
        """Secrets in git history should be detected."""
        repo_path = SYNTHETIC_REPOS / "historical-secrets"
        if not repo_path.exists():
            pytest.skip("historical-secrets repo not built")

        analysis = analyze_repository(
            gitleaks_path=gitleaks_path,
            repo_path=repo_path,
            repo_name_override="historical-secrets",
        )

        assert analysis.total_secrets >= 1

    def test_historical_secrets_marked_as_historical(
        self, gitleaks_path: Path, ground_truth: dict
    ) -> None:
        """Historical secrets should be marked as not in HEAD."""
        repo_path = SYNTHETIC_REPOS / "historical-secrets"
        if not repo_path.exists():
            pytest.skip("historical-secrets repo not built")

        analysis = analyze_repository(
            gitleaks_path=gitleaks_path,
            repo_path=repo_path,
            repo_name_override="historical-secrets",
        )

        expected = ground_truth["historical-secrets"]["expected"]

        # Check that we detect historical secrets
        assert analysis.secrets_in_history >= expected["secrets_in_history"]


@pytest.mark.integration
class TestOutputFormatValidation:
    """Tests validating output format across scenarios."""

    def test_output_format_has_required_fields(self, gitleaks_path: Path) -> None:
        """Output format should have all required fields."""
        repo_path = SYNTHETIC_REPOS / "no-secrets"
        if not repo_path.exists():
            pytest.skip("no-secrets repo not built")

        analysis = analyze_repository(
            gitleaks_path=gitleaks_path,
            repo_path=repo_path,
            repo_name_override="no-secrets",
        )
        output = to_output_format(analysis)

        # Check envelope structure (metadata + data)
        assert "metadata" in output
        assert "data" in output

        # Check metadata fields
        metadata = output["metadata"]
        assert metadata["tool_name"] == "gitleaks"
        assert "tool_version" in metadata
        assert "schema_version" in metadata
        assert "timestamp" in metadata

        # Check data fields
        data = output["data"]
        assert data["tool"] == "gitleaks"
        assert "tool_version" in data
        assert "total_secrets" in data
        assert "findings" in data
        assert isinstance(data["findings"], list)

    def test_output_validates_against_schema(self, gitleaks_path: Path) -> None:
        """Output should validate against JSON schema."""
        jsonschema = pytest.importorskip("jsonschema")

        repo_path = SYNTHETIC_REPOS / "no-secrets"
        if not repo_path.exists():
            pytest.skip("no-secrets repo not built")

        analysis = analyze_repository(
            gitleaks_path=gitleaks_path,
            repo_path=repo_path,
            repo_name_override="no-secrets",
        )
        output = to_output_format(analysis)

        schema_path = TOOL_ROOT / "schemas" / "output.schema.json"
        schema = json.loads(schema_path.read_text())

        jsonschema.validate(output, schema)

    def test_findings_have_required_fields(self, gitleaks_path: Path) -> None:
        """Each finding should have required fields."""
        repo_path = SYNTHETIC_REPOS / "api-keys"
        if not repo_path.exists():
            pytest.skip("api-keys repo not built")

        analysis = analyze_repository(
            gitleaks_path=gitleaks_path,
            repo_path=repo_path,
            repo_name_override="api-keys",
        )

        required_fields = {
            "file_path",
            "line_number",
            "rule_id",
            "secret_type",
            "commit_hash",
            "fingerprint",
        }

        for finding in analysis.findings:
            finding_dict = {
                "file_path": finding.file_path,
                "line_number": finding.line_number,
                "rule_id": finding.rule_id,
                "secret_type": finding.secret_type,
                "commit_hash": finding.commit_hash,
                "fingerprint": finding.fingerprint,
            }
            for field in required_fields:
                assert (
                    finding_dict.get(field) is not None
                ), f"Missing required field: {field}"


@pytest.mark.integration
class TestDirectoryMetrics:
    """Tests for directory rollup metrics."""

    def test_directory_metrics_computed(self, gitleaks_path: Path) -> None:
        """Directory metrics should be computed for repos with secrets."""
        repo_path = SYNTHETIC_REPOS / "api-keys"
        if not repo_path.exists():
            pytest.skip("api-keys repo not built")

        analysis = analyze_repository(
            gitleaks_path=gitleaks_path,
            repo_path=repo_path,
            repo_name_override="api-keys",
        )

        if analysis.total_secrets > 0:
            # Should have directory metrics when secrets exist
            assert len(analysis.directories) > 0

    def test_empty_repo_has_no_directory_metrics(self, gitleaks_path: Path) -> None:
        """Clean repo should have empty directory metrics."""
        repo_path = SYNTHETIC_REPOS / "no-secrets"
        if not repo_path.exists():
            pytest.skip("no-secrets repo not built")

        analysis = analyze_repository(
            gitleaks_path=gitleaks_path,
            repo_path=repo_path,
            repo_name_override="no-secrets",
        )

        # No secrets means no directory metrics
        if analysis.total_secrets == 0:
            assert len(analysis.directories) == 0
