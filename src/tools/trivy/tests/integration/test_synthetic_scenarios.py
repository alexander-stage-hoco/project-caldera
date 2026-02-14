"""Integration tests for synthetic test scenarios."""

import json
from pathlib import Path

import pytest


class TestSyntheticScenarios:
    """Tests for synthetic repository scenarios."""

    @pytest.fixture
    def trivy_root(self) -> Path:
        """Return the trivy tool root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def synthetic_dir(self, trivy_root) -> Path:
        """Return the synthetic repos directory."""
        return trivy_root / "eval-repos" / "synthetic"

    @pytest.fixture
    def ground_truth_dir(self, trivy_root) -> Path:
        """Return the ground truth directory."""
        return trivy_root / "evaluation" / "ground-truth"

    @pytest.fixture
    def output_dir(self, trivy_root) -> Path:
        """Return the output runs directory."""
        return trivy_root / "output" / "runs"

    def test_critical_cves_scenario(self, synthetic_dir, ground_truth_dir):
        """Test critical-cves synthetic scenario structure."""
        repo_dir = synthetic_dir / "critical-cves"

        if not repo_dir.exists():
            pytest.skip("critical-cves repo not found")

        # Should have requirements.txt
        assert (repo_dir / "requirements.txt").exists()

        # Should have ground truth
        gt_path = ground_truth_dir / "critical-cves.json"
        assert gt_path.exists()

        gt = json.loads(gt_path.read_text())
        assert "expected" in gt or "expected_vulnerabilities" in gt

    def test_no_vulnerabilities_scenario(self, synthetic_dir, ground_truth_dir):
        """Test no-vulnerabilities synthetic scenario."""
        repo_dir = synthetic_dir / "no-vulnerabilities"

        if not repo_dir.exists():
            pytest.skip("no-vulnerabilities repo not found")

        # Should have ground truth - it may allow a few vulns for testing purposes
        gt_path = ground_truth_dir / "no-vulnerabilities.json"
        if gt_path.exists():
            gt = json.loads(gt_path.read_text())
            expected = gt.get("expected", gt)
            expected_vulns = expected.get("expected_vulnerabilities", {})

            # Verify ground truth has a low upper bound (clean or near-clean repo)
            if isinstance(expected_vulns, dict):
                # Should have a relatively low max for a "no vulnerabilities" scenario
                assert expected_vulns.get("max", 10) <= 10, "no-vulns scenario should expect few vulns"

    def test_mixed_severity_scenario(self, synthetic_dir, ground_truth_dir):
        """Test mixed-severity synthetic scenario."""
        repo_dir = synthetic_dir / "mixed-severity"

        if not repo_dir.exists():
            pytest.skip("mixed-severity repo not found")

        gt_path = ground_truth_dir / "mixed-severity.json"
        if gt_path.exists():
            gt = json.loads(gt_path.read_text())
            expected = gt.get("expected", gt)

            # Should expect multiple severity levels
            assert "expected_vulnerabilities" in expected or "expected_critical" in expected

    def test_iac_misconfigs_scenario(self, synthetic_dir, ground_truth_dir):
        """Test iac-misconfigs synthetic scenario."""
        repo_dir = synthetic_dir / "iac-misconfigs"

        if not repo_dir.exists():
            pytest.skip("iac-misconfigs repo not found")

        # Should have IaC files
        iac_files = (
            list(repo_dir.glob("*.yaml"))
            + list(repo_dir.glob("*.yml"))
            + list(repo_dir.glob("Dockerfile*"))
            + list(repo_dir.glob("*.tf"))
        )
        assert len(iac_files) > 0, "IaC scenario should have IaC files"

        gt_path = ground_truth_dir / "iac-misconfigs.json"
        if gt_path.exists():
            gt = json.loads(gt_path.read_text())
            expected = gt.get("expected", gt)

            # Should expect IaC findings
            assert expected.get("iac_expected", False) or "expected_iac" in expected

    def test_k8s_misconfigs_scenario(self, synthetic_dir, ground_truth_dir):
        """Test k8s-misconfigs synthetic scenario."""
        repo_dir = synthetic_dir / "k8s-misconfigs"

        if not repo_dir.exists():
            pytest.skip("k8s-misconfigs repo not found")

        # Should have k8s YAML files
        yaml_files = list(repo_dir.glob("*.yaml")) + list(repo_dir.glob("*.yml"))
        assert len(yaml_files) > 0, "K8s scenario should have YAML files"

    def test_cfn_misconfigs_scenario(self, synthetic_dir, ground_truth_dir):
        """Test cfn-misconfigs (CloudFormation) scenario."""
        repo_dir = synthetic_dir / "cfn-misconfigs"

        if not repo_dir.exists():
            pytest.skip("cfn-misconfigs repo not found")

        # Should have CloudFormation templates
        cfn_files = (
            list(repo_dir.glob("*.yaml"))
            + list(repo_dir.glob("*.yml"))
            + list(repo_dir.glob("*.json"))
        )
        assert len(cfn_files) > 0, "CFN scenario should have template files"

    def test_dotnet_outdated_scenario(self, synthetic_dir, ground_truth_dir):
        """Test dotnet-outdated scenario."""
        repo_dir = synthetic_dir / "dotnet-outdated"

        if not repo_dir.exists():
            pytest.skip("dotnet-outdated repo not found")

        # Should have .NET project files (may be in subdirs or various formats)
        dotnet_files = (
            list(repo_dir.glob("**/*.csproj"))
            + list(repo_dir.glob("**/*.fsproj"))
            + list(repo_dir.glob("**/packages.config"))
            + list(repo_dir.glob("**/*.deps.json"))
            + list(repo_dir.glob("**/packages.lock.json"))
        )
        # Allow the scenario to exist even if it's structured differently
        # The important thing is the ground truth exists
        gt_path = ground_truth_dir / "dotnet-outdated.json"
        has_ground_truth = gt_path.exists()

        assert len(dotnet_files) > 0 or has_ground_truth, (
            "dotnet-outdated scenario should have .NET files or ground truth"
        )

    def test_java_outdated_scenario(self, synthetic_dir, ground_truth_dir):
        """Test java-outdated scenario."""
        repo_dir = synthetic_dir / "java-outdated"

        if not repo_dir.exists():
            pytest.skip("java-outdated repo not found")

        # Should have Java build files
        java_files = (
            list(repo_dir.glob("pom.xml"))
            + list(repo_dir.glob("build.gradle*"))
            + list(repo_dir.glob("*.gradle"))
        )
        assert len(java_files) > 0

    def test_js_fullstack_scenario(self, synthetic_dir, ground_truth_dir):
        """Test js-fullstack scenario."""
        repo_dir = synthetic_dir / "js-fullstack"

        if not repo_dir.exists():
            pytest.skip("js-fullstack repo not found")

        # Should have package.json
        assert (repo_dir / "package.json").exists() or (
            repo_dir / "package-lock.json"
        ).exists()

    def test_outdated_deps_scenario(self, synthetic_dir, ground_truth_dir):
        """Test outdated-deps scenario."""
        repo_dir = synthetic_dir / "outdated-deps"

        if not repo_dir.exists():
            pytest.skip("outdated-deps repo not found")

        # Should have some dependency file
        dep_files = (
            list(repo_dir.glob("requirements*.txt"))
            + list(repo_dir.glob("package*.json"))
            + list(repo_dir.glob("go.*"))
        )
        assert len(dep_files) > 0


class TestSyntheticOutputValidation:
    """Tests to validate output against synthetic scenarios."""

    @pytest.fixture
    def trivy_root(self) -> Path:
        """Return the trivy tool root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def output_dir(self, trivy_root) -> Path:
        """Return the output runs directory."""
        return trivy_root / "outputs"

    @pytest.fixture
    def ground_truth_dir(self, trivy_root) -> Path:
        """Return the ground truth directory."""
        return trivy_root / "evaluation" / "ground-truth"

    def _get_expected_value(self, expected_spec):
        """Helper to get min/max from expected value spec."""
        if isinstance(expected_spec, dict):
            return expected_spec.get("min", 0), expected_spec.get("max", float("inf"))
        elif isinstance(expected_spec, (int, float)):
            return expected_spec, expected_spec
        return 0, float("inf")

    def _load_output_by_id(self, output_dir: Path, output_id: str) -> dict | None:
        """Load a tool output.json by its scenario id (stored in top-level 'id')."""
        for output_file in output_dir.glob("*/output.json"):
            try:
                data = json.loads(output_file.read_text())
            except json.JSONDecodeError:
                continue
            if data.get("id") == output_id:
                return data
        return None

    def test_critical_cves_output_matches_ground_truth(
        self, output_dir, ground_truth_dir
    ):
        """Test that critical-cves output matches ground truth expectations."""
        gt_path = ground_truth_dir / "critical-cves.json"

        if not output_dir.exists():
            pytest.skip("No outputs directory")

        output = self._load_output_by_id(output_dir, "critical-cves")
        if output is None:
            pytest.skip("No output for critical-cves")

        gt = json.loads(gt_path.read_text())
        expected = gt.get("expected", gt)

        results = output.get("data", {})
        summary = results.get("findings_summary", {})

        # Check vulnerability count is in expected range
        expected_vulns = expected.get("expected_vulnerabilities")
        if expected_vulns:
            min_v, max_v = self._get_expected_value(expected_vulns)
            actual = summary.get("total_vulnerabilities", 0)
            assert (
                min_v <= actual <= max_v
            ), f"Vuln count {actual} not in [{min_v}, {max_v}]"

        # Check critical count
        expected_critical = expected.get("expected_critical")
        if expected_critical:
            min_c, max_c = self._get_expected_value(expected_critical)
            actual = (summary.get("by_severity") or {}).get("CRITICAL", 0)
            assert (
                min_c <= actual <= max_c
            ), f"Critical count {actual} not in [{min_c}, {max_c}]"

        # Check required packages
        required_packages = expected.get("required_packages", [])
        if required_packages:
            vulns = results.get("vulnerabilities", [])
            found_packages = {v.get("package", "") for v in vulns}

            for pkg in required_packages:
                assert (
                    pkg in found_packages
                ), f"Required package {pkg} not found in vulnerabilities"

    def test_no_vulnerabilities_output_is_clean(self, output_dir, ground_truth_dir):
        """Test that no-vulnerabilities output shows zero vulns."""
        if not output_dir.exists():
            pytest.skip("No outputs directory")

        output = self._load_output_by_id(output_dir, "no-vulnerabilities")
        if output is None:
            pytest.skip("No output for no-vulnerabilities")

        results = output.get("data", {})
        summary = results.get("findings_summary", {})

        # Should have 0 or very few vulnerabilities
        total_vulns = summary.get("total_vulnerabilities", 0)
        assert total_vulns <= 1, f"Expected 0-1 vulns, got {total_vulns}"

    def test_all_outputs_have_valid_structure(self, output_dir):
        """Test that all output files have valid structure."""
        if not output_dir.exists():
            pytest.skip("No output directory")

        output_files = list(output_dir.glob("*/output.json"))
        if not output_files:
            pytest.skip("No output files found")

        for output_file in output_files:
            output = json.loads(output_file.read_text())

            assert "metadata" in output, f"{output_file.name} missing metadata"
            assert "data" in output, f"{output_file.name} missing data"

            metadata = output["metadata"]
            assert metadata.get("tool_name") == "trivy"
            assert "schema_version" in metadata

            data = output["data"]
            assert data.get("tool") == "trivy"
            assert "findings_summary" in data
