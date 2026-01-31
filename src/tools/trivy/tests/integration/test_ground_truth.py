"""Integration tests for ground truth validation."""

import json
from pathlib import Path

import pytest


class TestGroundTruthStructure:
    """Tests for ground truth file structure validation."""

    @pytest.fixture
    def trivy_root(self) -> Path:
        """Return the trivy tool root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def ground_truth_dir(self, trivy_root) -> Path:
        """Return the ground truth directory."""
        return trivy_root / "evaluation" / "ground-truth"

    def test_ground_truth_directory_exists(self, ground_truth_dir):
        """Test that ground truth directory exists."""
        assert ground_truth_dir.exists(), f"Ground truth dir not found: {ground_truth_dir}"

    def test_ground_truth_files_are_valid_json(self, ground_truth_dir):
        """Test that all ground truth files are valid JSON."""
        for gt_file in ground_truth_dir.glob("*.json"):
            try:
                data = json.loads(gt_file.read_text())
                assert isinstance(data, dict), f"{gt_file.name} is not a dict"
            except json.JSONDecodeError as e:
                pytest.fail(f"{gt_file.name} is not valid JSON: {e}")

    def test_ground_truth_files_have_scenario(self, ground_truth_dir):
        """Test that ground truth files have scenario field."""
        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())

            # Should have scenario or filename match
            scenario = data.get("scenario", gt_file.stem)
            assert scenario, f"{gt_file.name} missing scenario identifier"

    def test_ground_truth_expected_field(self, ground_truth_dir):
        """Test that ground truth files have expected field or direct expectations."""
        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())

            # Either has "expected" wrapper or direct fields
            has_expected_wrapper = "expected" in data
            has_direct_fields = any(
                key.startswith("expected_") for key in data.keys()
            )

            assert (
                has_expected_wrapper or has_direct_fields
            ), f"{gt_file.name} has no expectations defined"


class TestGroundTruthExpectations:
    """Tests for ground truth expectation values."""

    @pytest.fixture
    def trivy_root(self) -> Path:
        """Return the trivy tool root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def ground_truth_dir(self, trivy_root) -> Path:
        """Return the ground truth directory."""
        return trivy_root / "evaluation" / "ground-truth"

    def _get_expectations(self, data):
        """Extract expectations from ground truth data."""
        if "expected" in data:
            return data["expected"]
        return {k: v for k, v in data.items() if k.startswith("expected_")}

    def test_vulnerability_expectations_are_valid(self, ground_truth_dir):
        """Test that vulnerability expectations have valid ranges."""
        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())
            expected = self._get_expectations(data)

            if "expected_vulnerabilities" in expected:
                vulns = expected["expected_vulnerabilities"]

                if isinstance(vulns, dict):
                    assert "min" in vulns or "max" in vulns, (
                        f"{gt_file.name} has expected_vulnerabilities dict without min/max"
                    )

                    min_val = vulns.get("min", 0)
                    max_val = vulns.get("max", float("inf"))
                    assert min_val >= 0, f"{gt_file.name} has negative min"
                    assert max_val >= min_val, f"{gt_file.name} max < min"
                else:
                    # Exact value
                    assert isinstance(vulns, (int, float))
                    assert vulns >= 0

    def test_severity_expectations_are_valid(self, ground_truth_dir):
        """Test that severity expectations have valid ranges."""
        severity_fields = [
            "expected_critical",
            "expected_high",
            "expected_medium",
            "expected_low",
        ]

        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())
            expected = self._get_expectations(data)

            for field in severity_fields:
                if field in expected:
                    value = expected[field]

                    if isinstance(value, dict):
                        min_val = value.get("min", 0)
                        max_val = value.get("max", float("inf"))
                        assert min_val >= 0, f"{gt_file.name} {field} has negative min"
                        assert (
                            max_val >= min_val
                        ), f"{gt_file.name} {field} max < min"
                    else:
                        assert value >= 0, f"{gt_file.name} {field} is negative"

    def test_required_packages_are_strings(self, ground_truth_dir):
        """Test that required_packages contains strings."""
        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())
            expected = self._get_expectations(data)

            if "required_packages" in expected:
                packages = expected["required_packages"]
                assert isinstance(packages, list), (
                    f"{gt_file.name} required_packages is not a list"
                )

                for pkg in packages:
                    assert isinstance(pkg, str), (
                        f"{gt_file.name} required_packages contains non-string: {pkg}"
                    )

    def test_freshness_expectations_are_valid(self, ground_truth_dir):
        """Test that freshness expectations are valid."""
        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())
            expected = self._get_expectations(data)

            if "freshness_expected" in expected:
                assert isinstance(expected["freshness_expected"], bool), (
                    f"{gt_file.name} freshness_expected is not bool"
                )

            if "expected_outdated_count" in expected:
                value = expected["expected_outdated_count"]

                if isinstance(value, dict):
                    assert value.get("min", 0) >= 0
                else:
                    assert value >= 0

    def test_iac_expectations_are_valid(self, ground_truth_dir):
        """Test that IaC expectations are valid."""
        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())
            expected = self._get_expectations(data)

            if "iac_expected" in expected:
                assert isinstance(expected["iac_expected"], bool), (
                    f"{gt_file.name} iac_expected is not bool"
                )

            if "expected_iac" in expected:
                iac = expected["expected_iac"]
                assert isinstance(iac, dict), (
                    f"{gt_file.name} expected_iac is not a dict"
                )

            if "required_iac_types" in expected:
                types = expected["required_iac_types"]
                assert isinstance(types, list)
                for t in types:
                    assert isinstance(t, str)

            if "required_iac_ids" in expected:
                ids = expected["required_iac_ids"]
                assert isinstance(ids, list)
                for i in ids:
                    assert isinstance(i, str)


class TestGroundTruthCompleteness:
    """Tests for ground truth coverage completeness."""

    @pytest.fixture
    def trivy_root(self) -> Path:
        """Return the trivy tool root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def ground_truth_dir(self, trivy_root) -> Path:
        """Return the ground truth directory."""
        return trivy_root / "evaluation" / "ground-truth"

    @pytest.fixture
    def synthetic_dir(self, trivy_root) -> Path:
        """Return the synthetic repos directory."""
        return trivy_root / "eval-repos" / "synthetic"

    def test_all_synthetic_repos_have_ground_truth(
        self, synthetic_dir, ground_truth_dir
    ):
        """Test that every synthetic repo has a ground truth file."""
        if not synthetic_dir.exists():
            pytest.skip("Synthetic repos directory not found")

        synthetic_repos = [d.name for d in synthetic_dir.iterdir() if d.is_dir()]
        gt_files = [f.stem for f in ground_truth_dir.glob("*.json")]

        missing = []
        for repo in synthetic_repos:
            if repo not in gt_files:
                missing.append(repo)

        if missing:
            pytest.fail(f"Synthetic repos without ground truth: {missing}")

    def test_ground_truth_count(self, ground_truth_dir):
        """Test that we have expected number of ground truth files."""
        gt_files = list(ground_truth_dir.glob("*.json"))

        # We expect at least 5 ground truth files
        assert len(gt_files) >= 5, (
            f"Expected at least 5 ground truth files, found {len(gt_files)}"
        )

    def test_each_ground_truth_covers_key_scenarios(self, ground_truth_dir):
        """Test that ground truth files cover key vulnerability scenarios."""
        gt_files = [f.stem for f in ground_truth_dir.glob("*.json")]

        # Key scenarios we expect to have coverage for
        key_scenarios = [
            "critical-cves",  # High severity vulnerabilities
            "no-vulnerabilities",  # Clean repo
        ]

        # Check at least some key scenarios are covered
        covered = [s for s in key_scenarios if s in gt_files]

        assert len(covered) >= 1, f"Missing key scenarios: {key_scenarios}"


class TestGroundTruthEvaluation:
    """Tests for running evaluation against ground truth."""

    @pytest.fixture
    def trivy_root(self) -> Path:
        """Return the trivy tool root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def ground_truth_dir(self, trivy_root) -> Path:
        """Return the ground truth directory."""
        return trivy_root / "evaluation" / "ground-truth"

    @pytest.fixture
    def output_dir(self, trivy_root) -> Path:
        """Return the output runs directory."""
        return trivy_root / "output" / "runs"

    def test_evaluate_against_ground_truth(self, output_dir, ground_truth_dir):
        """Test that evaluation can run against ground truth."""
        from evaluate import evaluate_repository

        if not output_dir.exists():
            pytest.skip("No output directory")

        gt_files = list(ground_truth_dir.glob("*.json"))

        evaluated = 0
        for gt_file in gt_files:
            output_file = output_dir / f"{gt_file.stem}.json"

            if not output_file.exists():
                continue

            report = evaluate_repository(output_file, gt_file)

            assert report is not None
            assert report.total_checks > 0
            evaluated += 1

        if evaluated == 0:
            pytest.skip("No matching output files for ground truth")

        assert evaluated >= 1, "At least one evaluation should have run"

    def test_evaluation_pass_rate_reasonable(self, output_dir, ground_truth_dir):
        """Test that evaluation pass rate is reasonable for synthetic scenarios."""
        from evaluate import evaluate_repository

        if not output_dir.exists():
            pytest.skip("No output directory")

        pass_rates = []

        for gt_file in ground_truth_dir.glob("*.json"):
            output_file = output_dir / f"{gt_file.stem}.json"

            if not output_file.exists():
                continue

            report = evaluate_repository(output_file, gt_file)

            if report.total_checks > 0:
                pass_rates.append(report.pass_rate)

        if not pass_rates:
            pytest.skip("No evaluations completed")

        avg_pass_rate = sum(pass_rates) / len(pass_rates)

        # Expect reasonable pass rate for synthetic scenarios
        assert avg_pass_rate >= 0.5, (
            f"Average pass rate {avg_pass_rate:.2%} is too low"
        )
