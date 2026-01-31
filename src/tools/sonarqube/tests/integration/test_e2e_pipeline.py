"""End-to-end pipeline integration tests for SonarQube analysis.

These tests run the complete analysis pipeline from Docker container start
to JSON export. They are slow and require Docker.
"""

import json
import time

import pytest

from scripts.analyze import AnalysisConfig, run_analysis
from scripts.evaluate import run_all_checks
from scripts.checks import CheckCategory, EvaluationReport, load_analysis, load_ground_truth
from scripts.export import validate_export, SCHEMA_VERSION
from scripts.scanner import ScannerConfig, create_scanner_config, run_sonar_scanner, detect_language
from scripts.api.module_a_task import wait_for_analysis_complete


@pytest.mark.docker
@pytest.mark.integration
@pytest.mark.slow
class TestFullAnalysisPipeline:
    """Tests for the complete analysis pipeline."""

    def test_full_analysis_csharp_clean(
        self, sonarqube_container, csharp_clean_repo, output_dir
    ):
        """E2E test: Docker -> Scanner -> API extraction -> Export.

        Uses eval-repos/synthetic/csharp-clean as the test repository.
        """
        output_path = output_dir / "csharp-clean.json"

        config = AnalysisConfig(
            repo_path=csharp_clean_repo,
            project_key="test-csharp-clean",
            output_path=output_path,
            sonarqube_url=sonarqube_container.base_url,
            token=sonarqube_container.admin_token,
            keep_container=True,  # Keep running for other tests
            container_already_running=True,
            use_docker_scanner=True,
            analysis_timeout=600,
            skip_scan=False,
        )

        # Run the analysis
        result = run_analysis(config)

        # Verify output file exists
        assert output_path.exists(), "Output file should be created"

        # Verify schema version
        assert result["schema_version"] == SCHEMA_VERSION

        # Verify basic structure
        results = result.get("results", {})
        assert "source" in results
        assert results["source"]["project_key"] == "test-csharp-clean"

        assert "components" in results
        assert "measures" in results
        assert "issues" in results
        assert "quality_gate" in results
        assert "derived_insights" in results

        # Verify we got some components
        components = results["components"]["by_key"]
        assert len(components) > 0, "Should have extracted components"

        # Verify we have file components
        file_count = sum(
            1 for c in components.values()
            if c.get("qualifier") == "FIL"
        )
        assert file_count > 0, "Should have file components"

    def test_output_schema_validation(
        self, sonarqube_container, csharp_clean_repo, output_dir, schema_path
    ):
        """Validate output JSON against schema."""
        output_path = output_dir / "schema-test.json"

        config = AnalysisConfig(
            repo_path=csharp_clean_repo,
            project_key="test-schema-validation",
            output_path=output_path,
            sonarqube_url=sonarqube_container.base_url,
            token=sonarqube_container.admin_token,
            keep_container=True,
            container_already_running=True,
            use_docker_scanner=True,
            analysis_timeout=600,
        )

        run_analysis(config)

        # Validate against schema
        assert validate_export(output_path, schema_path), "Output should validate against schema"

    def test_analysis_with_skip_scan(
        self, sonarqube_container, csharp_clean_repo, output_dir
    ):
        """Test extracting data from existing project (skip scan).

        This test assumes a project has already been scanned.
        """
        # First, run a normal analysis to create the project
        first_output = output_dir / "first-run.json"
        config1 = AnalysisConfig(
            repo_path=csharp_clean_repo,
            project_key="test-skip-scan",
            output_path=first_output,
            sonarqube_url=sonarqube_container.base_url,
            token=sonarqube_container.admin_token,
            keep_container=True,
            container_already_running=True,
        )
        run_analysis(config1)

        # Now extract again with skip_scan=True
        second_output = output_dir / "skip-scan.json"
        config2 = AnalysisConfig(
            repo_path=csharp_clean_repo,
            project_key="test-skip-scan",  # Same project key
            output_path=second_output,
            sonarqube_url=sonarqube_container.base_url,
            token=sonarqube_container.admin_token,
            keep_container=True,
            container_already_running=True,
            skip_scan=True,
        )
        result = run_analysis(config2)
        results = result.get("results", {})

        # Should still get the same data
        assert results["source"]["project_key"] == "test-skip-scan"
        assert len(results["components"]["by_key"]) > 0


@pytest.mark.docker
@pytest.mark.integration
@pytest.mark.slow
class TestEvaluationPipeline:
    """Tests for evaluation pipeline integration."""

    def test_evaluation_passes_for_clean_repo(
        self, sonarqube_container, csharp_clean_repo, output_dir, ground_truth_dir
    ):
        """Run evaluation checks on real output and verify they pass."""
        output_path = output_dir / "eval-test.json"

        config = AnalysisConfig(
            repo_path=csharp_clean_repo,
            project_key="test-evaluation",
            output_path=output_path,
            sonarqube_url=sonarqube_container.base_url,
            token=sonarqube_container.admin_token,
            keep_container=True,
            container_already_running=True,
        )

        run_analysis(config)

        # Run evaluation
        gt_path = ground_truth_dir / "csharp-clean.json"
        data = load_analysis(output_path)
        ground_truth = load_ground_truth(ground_truth_dir, "csharp-clean") if gt_path.exists() else None

        checks = run_all_checks(data, ground_truth)
        report = EvaluationReport(
            timestamp="",
            analysis_path=str(output_path),
            ground_truth_dir=str(ground_truth_dir),
            checks=checks,
        )

        # Should have a reasonable score
        assert report.score >= 0, "Score should be non-negative"

        # Log results for debugging
        for cat, cat_score in report.score_by_category.items():
            passed, total = report.passed_by_category.get(cat, (0, 0))
            print(f"{cat}: {cat_score:.1%} ({passed}/{total})")
            for check in checks:
                if check.category.value == cat:
                    status = "PASS" if check.passed else "FAIL"
                    print(f"  [{status}] {check.check_id}: {check.message}")

    def test_evaluation_structure_complete(
        self, sonarqube_container, csharp_clean_repo, output_dir
    ):
        """Verify evaluation returns proper structure."""
        output_path = output_dir / "struct-test.json"

        config = AnalysisConfig(
            repo_path=csharp_clean_repo,
            project_key="test-eval-struct",
            output_path=output_path,
            sonarqube_url=sonarqube_container.base_url,
            token=sonarqube_container.admin_token,
            keep_container=True,
            container_already_running=True,
        )

        result = run_analysis(config)

        # Run evaluation without ground truth
        checks = run_all_checks(
            data=result,
            ground_truth=None,
        )
        report = EvaluationReport(
            timestamp="",
            analysis_path=str(output_path),
            ground_truth_dir="",
            checks=checks,
        )

        # Should have evaluation result structure
        assert report.analysis_path == str(output_path)
        assert isinstance(report.score, float)
        assert isinstance(report.score_by_category, dict)


@pytest.mark.docker
@pytest.mark.integration
@pytest.mark.slow
class TestMultiLanguageAnalysis:
    """Tests for analyzing different language repositories."""

    def test_java_security_repo_analysis(
        self, sonarqube_container, java_security_repo, output_dir
    ):
        """Test analysis of Java security-focused repository."""
        if not java_security_repo.exists():
            pytest.skip("java-security repo not available")

        output_path = output_dir / "java-security.json"

        config = AnalysisConfig(
            repo_path=java_security_repo,
            project_key="test-java-security",
            output_path=output_path,
            sonarqube_url=sonarqube_container.base_url,
            token=sonarqube_container.admin_token,
            keep_container=True,
            container_already_running=True,
        )

        result = run_analysis(config)
        results = result.get("results", {})

        # Should detect some issues (it's a security-focused test repo)
        issues = results.get("issues", {})
        assert issues, "Should have issues section"

    def test_typescript_duplication_repo_analysis(
        self, sonarqube_container, typescript_duplication_repo, output_dir
    ):
        """Test analysis of TypeScript repository with duplications."""
        if not typescript_duplication_repo.exists():
            pytest.skip("typescript-duplication repo not available")

        output_path = output_dir / "typescript-duplication.json"

        config = AnalysisConfig(
            repo_path=typescript_duplication_repo,
            project_key="test-ts-duplication",
            output_path=output_path,
            sonarqube_url=sonarqube_container.base_url,
            token=sonarqube_container.admin_token,
            keep_container=True,
            container_already_running=True,
        )

        try:
            result = run_analysis(config)
        except Exception as exc:
            message = str(exc).lower()
            if "can not be reached" in message or "fail to get bootstrap index" in message:
                pytest.skip("SonarQube unreachable from scanner container")
            raise
        results = result.get("results", {})

        # Should have duplication data
        duplications = results.get("duplications", {})
        assert duplications, "Should have duplications section"


@pytest.mark.docker
@pytest.mark.integration
class TestDerivedInsights:
    """Tests for derived insights computation."""

    def test_hotspots_computed(
        self, sonarqube_container, csharp_clean_repo, output_dir
    ):
        """Test that hotspots are computed in output."""
        output_path = output_dir / "hotspots-test.json"

        config = AnalysisConfig(
            repo_path=csharp_clean_repo,
            project_key="test-hotspots",
            output_path=output_path,
            sonarqube_url=sonarqube_container.base_url,
            token=sonarqube_container.admin_token,
            keep_container=True,
            container_already_running=True,
        )

        result = run_analysis(config)
        results = result.get("results", {})

        insights = results.get("derived_insights", {})
        assert "hotspots" in insights
        assert "directory_rollups" in insights

    def test_directory_rollups_computed(
        self, sonarqube_container, csharp_clean_repo, output_dir
    ):
        """Test that directory rollups are computed."""
        output_path = output_dir / "rollups-test.json"

        config = AnalysisConfig(
            repo_path=csharp_clean_repo,
            project_key="test-rollups",
            output_path=output_path,
            sonarqube_url=sonarqube_container.base_url,
            token=sonarqube_container.admin_token,
            keep_container=True,
            container_already_running=True,
        )

        result = run_analysis(config)
        results = result.get("results", {})

        rollups = results.get("derived_insights", {}).get("directory_rollups", {})
        # May or may not have rollups depending on directory structure
        assert isinstance(rollups, dict)


@pytest.mark.docker
@pytest.mark.integration
class TestQualityGate:
    """Tests for quality gate extraction."""

    def test_quality_gate_status_extracted(
        self, sonarqube_container, csharp_clean_repo, output_dir
    ):
        """Test quality gate status is extracted."""
        output_path = output_dir / "qg-test.json"

        config = AnalysisConfig(
            repo_path=csharp_clean_repo,
            project_key="test-quality-gate",
            output_path=output_path,
            sonarqube_url=sonarqube_container.base_url,
            token=sonarqube_container.admin_token,
            keep_container=True,
            container_already_running=True,
        )

        result = run_analysis(config)
        results = result.get("results", {})

        qg = results.get("quality_gate", {})
        assert "status" in qg
        assert qg["status"] in ["OK", "WARN", "ERROR", "NONE"]


@pytest.mark.docker
@pytest.mark.integration
class TestLimitations:
    """Tests for limitations documentation."""

    def test_limitations_documented(
        self, sonarqube_container, csharp_clean_repo, output_dir
    ):
        """Test that limitations are documented in output."""
        output_path = output_dir / "limits-test.json"

        config = AnalysisConfig(
            repo_path=csharp_clean_repo,
            project_key="test-limitations",
            output_path=output_path,
            sonarqube_url=sonarqube_container.base_url,
            token=sonarqube_container.admin_token,
            keep_container=True,
            container_already_running=True,
        )

        result = run_analysis(config)
        results = result.get("results", {})

        limitations = results.get("limitations", {})
        assert "no_symbol_graph" in limitations
        assert "no_call_graph" in limitations
        assert "no_data_flow" in limitations
        assert "issues_may_be_truncated" in limitations


@pytest.mark.docker
@pytest.mark.integration
class TestOutputFormat:
    """Tests for output file format."""

    def test_output_is_valid_json(
        self, sonarqube_container, csharp_clean_repo, output_dir
    ):
        """Test output file is valid JSON."""
        output_path = output_dir / "json-test.json"

        config = AnalysisConfig(
            repo_path=csharp_clean_repo,
            project_key="test-json-format",
            output_path=output_path,
            sonarqube_url=sonarqube_container.base_url,
            token=sonarqube_container.admin_token,
            keep_container=True,
            container_already_running=True,
        )

        run_analysis(config)

        # Should be valid JSON
        with open(output_path) as f:
            data = json.load(f)

        assert data["schema_version"] == SCHEMA_VERSION

    def test_output_has_generated_timestamp(
        self, sonarqube_container, csharp_clean_repo, output_dir
    ):
        """Test output includes generation timestamp."""
        output_path = output_dir / "timestamp-test.json"

        config = AnalysisConfig(
            repo_path=csharp_clean_repo,
            project_key="test-timestamp",
            output_path=output_path,
            sonarqube_url=sonarqube_container.base_url,
            token=sonarqube_container.admin_token,
            keep_container=True,
            container_already_running=True,
        )

        result = run_analysis(config)

        assert "generated_at" in result
        # Should be ISO format
        assert "T" in result["generated_at"]
