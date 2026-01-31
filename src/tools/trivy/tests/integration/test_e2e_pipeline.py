"""End-to-end integration tests for the Trivy analysis pipeline."""

import json
import subprocess
from pathlib import Path

import pytest


class TestE2EPipeline:
    """End-to-end tests for the full analysis pipeline."""

    @pytest.fixture
    def trivy_root(self) -> Path:
        """Return the trivy tool root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def scripts_dir(self, trivy_root) -> Path:
        """Return the scripts directory."""
        return trivy_root / "scripts"

    @pytest.fixture
    def venv_python(self, trivy_root) -> Path:
        """Return the virtual environment Python path."""
        return trivy_root / ".venv" / "bin" / "python"

    @pytest.fixture
    def trivy_binary(self, trivy_root) -> Path:
        """Return the trivy binary path."""
        return trivy_root / "bin" / "trivy"

    def test_trivy_binary_exists(self, trivy_binary):
        """Test that the trivy binary exists."""
        assert trivy_binary.exists(), f"Trivy binary not found at {trivy_binary}"

    def test_trivy_version(self, trivy_binary):
        """Test that trivy can report its version."""
        result = subprocess.run(
            [str(trivy_binary), "version", "--format", "json"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"trivy version failed: {result.stderr}"

        version_info = json.loads(result.stdout)
        assert "Version" in version_info

    def test_analyze_script_exists(self, scripts_dir):
        """Test that analyze.py script exists."""
        analyze_script = scripts_dir / "analyze.py"
        assert analyze_script.exists()

    def test_evaluate_script_exists(self, scripts_dir):
        """Test that evaluate.py script exists."""
        evaluate_script = scripts_dir / "evaluate.py"
        assert evaluate_script.exists()

    def test_output_schema_exists(self, trivy_root):
        """Test that output schema exists."""
        schema_path = trivy_root / "schemas" / "output.schema.json"
        assert schema_path.exists()

        # Verify it's valid JSON
        schema = json.loads(schema_path.read_text())
        assert "$schema" in schema

    def test_ground_truth_files_exist(self, trivy_root):
        """Test that ground truth files exist."""
        gt_dir = trivy_root / "evaluation" / "ground-truth"
        assert gt_dir.exists()

        gt_files = list(gt_dir.glob("*.json"))
        assert len(gt_files) >= 5, f"Expected at least 5 ground truth files, found {len(gt_files)}"

    def test_synthetic_repos_exist(self, trivy_root):
        """Test that synthetic repos exist."""
        repos_dir = trivy_root / "eval-repos" / "synthetic"
        assert repos_dir.exists()

        repos = [d for d in repos_dir.iterdir() if d.is_dir()]
        assert len(repos) >= 5, f"Expected at least 5 synthetic repos, found {len(repos)}"


class TestOutputValidation:
    """Tests for output file validation."""

    @pytest.fixture
    def trivy_root(self) -> Path:
        """Return the trivy tool root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def output_dir(self, trivy_root) -> Path:
        """Return the output directory."""
        return trivy_root / "output" / "runs"

    def test_output_files_valid_json(self, output_dir):
        """Test that existing output files are valid JSON."""
        if not output_dir.exists():
            pytest.skip("No output directory found")

        output_files = list(output_dir.glob("*.json"))
        if not output_files:
            pytest.skip("No output files found")

        for output_file in output_files:
            try:
                data = json.loads(output_file.read_text())
                assert isinstance(data, dict), f"{output_file.name} is not a dict"
            except json.JSONDecodeError as e:
                pytest.fail(f"{output_file.name} is not valid JSON: {e}")

    def test_output_files_have_required_fields(self, output_dir):
        """Test that output files have required top-level fields."""
        if not output_dir.exists():
            pytest.skip("No output directory found")

        output_files = list(output_dir.glob("*.json"))
        if not output_files:
            pytest.skip("No output files found")

        required_fields = ["schema_version", "generated_at", "repo_name", "results"]

        for output_file in output_files:
            data = json.loads(output_file.read_text())

            for field in required_fields:
                assert field in data, f"{output_file.name} missing field: {field}"

    def test_output_results_have_summary(self, output_dir):
        """Test that output results have summary section."""
        if not output_dir.exists():
            pytest.skip("No output directory found")

        output_files = list(output_dir.glob("*.json"))
        if not output_files:
            pytest.skip("No output files found")

        for output_file in output_files:
            data = json.loads(output_file.read_text())
            results = data.get("results", {})

            assert "summary" in results, f"{output_file.name} results missing summary"

            summary = results["summary"]
            assert "total_vulnerabilities" in summary
            assert "critical_count" in summary


class TestChecksModuleIntegration:
    """Integration tests for the checks module."""

    @pytest.fixture
    def trivy_root(self) -> Path:
        """Return the trivy tool root directory."""
        return Path(__file__).parent.parent.parent

    def test_all_check_modules_importable(self):
        """Test that all check modules can be imported."""
        from checks import CheckResult, EvaluationReport
        from checks.accuracy import run_accuracy_checks
        from checks.detection import run_detection_checks
        from checks.freshness import run_freshness_checks
        from checks.iac import run_iac_checks
        from checks.integration import run_integration_checks
        from checks.output_quality import run_output_quality_checks
        from checks.performance import run_performance_checks

        # All imports succeeded
        assert callable(run_accuracy_checks)
        assert callable(run_detection_checks)
        assert callable(run_freshness_checks)
        assert callable(run_iac_checks)
        assert callable(run_integration_checks)
        assert callable(run_output_quality_checks)
        assert callable(run_performance_checks)

    def test_check_modules_return_generators(self, sample_normalized_analysis):
        """Test that check modules return generators."""
        from checks.accuracy import run_accuracy_checks
        from checks.detection import run_detection_checks
        from checks.integration import run_integration_checks
        from checks.output_quality import run_output_quality_checks
        from checks.performance import run_performance_checks

        ground_truth = {}

        # Each should return a generator
        assert hasattr(run_accuracy_checks(sample_normalized_analysis, ground_truth), "__iter__")
        assert hasattr(run_detection_checks(sample_normalized_analysis, ground_truth), "__iter__")
        assert hasattr(run_integration_checks(sample_normalized_analysis, ground_truth), "__iter__")
        assert hasattr(run_output_quality_checks(sample_normalized_analysis, ground_truth), "__iter__")
        assert hasattr(run_performance_checks(sample_normalized_analysis, ground_truth), "__iter__")


class TestEvaluationPipeline:
    """Tests for the evaluation pipeline."""

    @pytest.fixture
    def trivy_root(self) -> Path:
        """Return the trivy tool root directory."""
        return Path(__file__).parent.parent.parent

    def test_evaluate_repository_function(self, trivy_root, temp_dir):
        """Test evaluate_repository function works with test data."""
        from evaluate import evaluate_repository

        # Create test analysis file
        analysis_data = {
            "schema_version": "1.0.0",
            "generated_at": "2026-01-15T10:00:00Z",
            "repo_name": "test",
            "repo_path": "/test",
            "results": {
                "tool": "trivy",
                "tool_version": "0.58.0",
                "repository": "test",
                "timestamp": "2026-01-15T10:00:00Z",
                "scan_time_ms": 100,
                "summary": {
                    "total_vulnerabilities": 5,
                    "critical_count": 1,
                    "high_count": 2,
                    "medium_count": 2,
                    "low_count": 0,
                    "unknown_count": 0,
                    "fix_available_count": 5,
                    "fix_available_pct": 100.0,
                    "dependency_count": 3,
                    "oldest_cve_days": 100,
                    "targets_scanned": 1,
                },
                "vulnerabilities": [
                    {
                        "id": "CVE-2021-0001",
                        "severity": "CRITICAL",
                        "package": "test-pkg",
                        "installed_version": "1.0.0",
                        "fix_available": True,
                        "target": "requirements.txt",
                        "age_days": 100,
                    }
                ],
                "targets": [{"path": "requirements.txt", "type": "pip"}],
                "directories": {"directory_count": 1, "directories": []},
                "iac_misconfigurations": {
                    "total_count": 0,
                    "critical_count": 0,
                    "high_count": 0,
                    "misconfigurations": [],
                },
                "sbom": {
                    "format": "trivy-json",
                    "total_packages": 3,
                    "vulnerable_packages": 1,
                    "clean_packages": 2,
                },
            },
        }

        # Create test ground truth
        ground_truth = {
            "expected_vulnerabilities": {"min": 1, "max": 10},
        }

        # Write files
        analysis_path = temp_dir / "analysis.json"
        gt_path = temp_dir / "gt.json"
        analysis_path.write_text(json.dumps(analysis_data))
        gt_path.write_text(json.dumps(ground_truth))

        # Run evaluation
        report = evaluate_repository(analysis_path, gt_path)

        # evaluate_repository returns a dict with scores and checks
        assert report is not None
        assert len(report.get("checks", [])) > 0
        assert report.get("scores", {}).get("overall", {}).get("total", 0) > 0
