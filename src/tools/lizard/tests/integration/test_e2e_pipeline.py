"""End-to-end integration tests for the Lizard analysis pipeline."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


class TestE2EPipeline:
    """End-to-end tests for the full analysis pipeline."""

    @pytest.fixture
    def lizard_root(self) -> Path:
        """Return the lizard tool root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def scripts_dir(self, lizard_root) -> Path:
        """Return the scripts directory."""
        return lizard_root / "scripts"

    @pytest.fixture
    def venv_python(self, lizard_root) -> Path:
        """Return the virtual environment Python path."""
        return lizard_root / ".venv" / "bin" / "python"

    def test_lizard_module_exists(self, venv_python):
        """Test that the lizard module is installed and callable."""
        if not venv_python.exists():
            pytest.skip("Virtual environment not found")

        result = subprocess.run(
            [str(venv_python), "-m", "lizard", "--version"],
            capture_output=True,
            text=True,
        )

        # Lizard should either return version or help text
        assert result.returncode == 0 or "lizard" in result.stdout.lower() or "lizard" in result.stderr.lower()

    def test_lizard_xml_output(self, venv_python, lizard_root):
        """Test that lizard can produce XML output."""
        if not venv_python.exists():
            pytest.skip("Virtual environment not found")

        synthetic_dir = lizard_root / "eval-repos" / "synthetic" / "python"
        if not synthetic_dir.exists():
            pytest.skip("Synthetic Python repo not found")

        result = subprocess.run(
            [str(venv_python), "-m", "lizard", str(synthetic_dir), "--xml"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should produce XML output
        assert result.returncode == 0
        assert "<?xml" in result.stdout or "<cppncss>" in result.stdout

    def test_analyze_script_exists(self, scripts_dir):
        """Test that analyze.py script exists."""
        analyze_script = scripts_dir / "analyze.py"
        assert analyze_script.exists(), f"analyze.py not found at {analyze_script}"

    def test_evaluate_script_exists(self, scripts_dir):
        """Test that evaluate.py script exists."""
        evaluate_script = scripts_dir / "evaluate.py"
        assert evaluate_script.exists(), f"evaluate.py not found at {evaluate_script}"

    def test_function_analyzer_exists(self, scripts_dir):
        """Test that function_analyzer.py exists."""
        analyzer_script = scripts_dir / "function_analyzer.py"
        assert analyzer_script.exists(), f"function_analyzer.py not found at {analyzer_script}"

    def test_output_schema_exists(self, lizard_root):
        """Test that output schema exists and is valid JSON."""
        schema_path = lizard_root / "schemas" / "output.schema.json"
        assert schema_path.exists(), f"Schema not found at {schema_path}"

        # Verify it's valid JSON
        schema = json.loads(schema_path.read_text())
        assert "$schema" in schema or "type" in schema

    def test_ground_truth_files_exist(self, lizard_root):
        """Test that ground truth files exist for all 7 languages."""
        gt_dir = lizard_root / "evaluation" / "ground-truth"
        assert gt_dir.exists(), f"Ground truth dir not found: {gt_dir}"

        expected_languages = ["python", "csharp", "java", "javascript", "typescript", "go", "rust"]
        gt_files = [f.stem for f in gt_dir.glob("*.json")]

        for lang in expected_languages:
            assert lang in gt_files, f"Missing ground truth for {lang}"

    def test_synthetic_repos_exist(self, lizard_root):
        """Test that synthetic repos exist for all 7 languages."""
        repos_dir = lizard_root / "eval-repos" / "synthetic"
        assert repos_dir.exists(), f"Synthetic repos dir not found: {repos_dir}"

        expected_languages = ["python", "csharp", "java", "javascript", "typescript", "go", "rust"]
        repos = [d.name for d in repos_dir.iterdir() if d.is_dir()]

        for lang in expected_languages:
            assert lang in repos, f"Missing synthetic repo for {lang}"


class TestOutputValidation:
    """Tests for output file validation."""

    @pytest.fixture
    def lizard_root(self) -> Path:
        """Return the lizard tool root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def output_dir(self, lizard_root) -> Path:
        """Return the output directory."""
        return lizard_root / "output"

    def _find_analysis_files(self, output_dir: Path):
        """Find output.json files in the output directory."""
        if not output_dir.exists():
            return []
        return list(output_dir.glob("output.json"))

    def test_output_files_valid_json(self, output_dir):
        """Test that existing output.json files are valid JSON."""
        analysis_files = self._find_analysis_files(output_dir)
        if not analysis_files:
            pytest.skip("No output files found")

        for output_file in analysis_files:
            try:
                data = json.loads(output_file.read_text())
                assert isinstance(data, dict), f"{output_file.name} is not a dict"
            except json.JSONDecodeError as e:
                pytest.fail(f"{output_file.name} is not valid JSON: {e}")

    def test_output_files_have_required_fields(self, output_dir):
        """Test that output files have required top-level fields."""
        analysis_files = self._find_analysis_files(output_dir)
        if not analysis_files:
            pytest.skip("No output files found")

        for output_file in analysis_files:
            data = json.loads(output_file.read_text())

            assert "metadata" in data, f"{output_file.name} missing metadata envelope"
            assert "data" in data, f"{output_file.name} missing data payload"

    def test_output_summary_has_metrics(self, output_dir):
        """Test that output summary has required metrics."""
        analysis_files = self._find_analysis_files(output_dir)
        if not analysis_files:
            pytest.skip("No output files found")

        for output_file in analysis_files:
            data = json.loads(output_file.read_text())
            summary = data.get("data", {}).get("summary", {})

            if summary:
                assert "total_files" in summary, f"{output_file.name} summary missing total_files"
                assert "total_functions" in summary, f"{output_file.name} summary missing total_functions"


class TestChecksModuleIntegration:
    """Integration tests for the checks module."""

    @pytest.fixture
    def lizard_root(self) -> Path:
        """Return the lizard tool root directory."""
        return Path(__file__).parent.parent.parent

    def test_all_check_modules_importable(self, lizard_root):
        """Test that all check modules can be imported."""
        from scripts.checks import CheckResult, CheckCategory, CheckSeverity
        from scripts.checks.accuracy import run_accuracy_checks
        from scripts.checks.coverage import run_coverage_checks
        from scripts.checks.edge_cases import run_edge_case_checks
        from scripts.checks.performance import run_performance_checks

        # All imports succeeded
        assert callable(run_accuracy_checks)
        assert callable(run_coverage_checks)
        assert callable(run_edge_case_checks)
        assert callable(run_performance_checks)

    def test_check_modules_return_lists(self, lizard_root, sample_analysis, sample_ground_truth):
        """Test that check modules return lists of results."""
        from scripts.checks.accuracy import run_accuracy_checks
        from scripts.checks.coverage import run_coverage_checks
        from scripts.checks.edge_cases import run_edge_case_checks

        # Each should return a list
        accuracy_results = run_accuracy_checks(sample_analysis, sample_ground_truth)
        assert isinstance(accuracy_results, list)

        # coverage checks only takes analysis (no ground truth)
        coverage_results = run_coverage_checks(sample_analysis)
        assert isinstance(coverage_results, list)

        edge_results = run_edge_case_checks(sample_analysis, sample_ground_truth)
        assert isinstance(edge_results, list)


class TestEvaluationPipeline:
    """Tests for the evaluation pipeline."""

    @pytest.fixture
    def lizard_root(self) -> Path:
        """Return the lizard tool root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def temp_dir(self, tmp_path) -> Path:
        """Return a temporary directory for test files."""
        return tmp_path

    def test_run_evaluation_function(self, lizard_root, temp_dir):
        """Test run_evaluation function works with test data."""
        scripts_dir = lizard_root / "scripts"
        sys.path.insert(0, str(scripts_dir))

        try:
            from evaluate import run_evaluation

            # Create test analysis file
            analysis_data = {
                "metadata": {
                    "tool_name": "lizard",
                    "tool_version": "1.17.10",
                    "run_id": "550e8400-e29b-41d4-a716-446655440000",
                    "repo_id": "660e8400-e29b-41d4-a716-446655440001",
                    "branch": "main",
                    "commit": "abc123def456789012345678901234567890abcd",
                    "timestamp": "2026-01-15T10:00:00Z",
                    "schema_version": "1.0.0",
                },
                "data": {
                    "tool": "lizard",
                    "tool_version": "1.17.10",
                    "run_id": "550e8400-e29b-41d4-a716-446655440000",
                    "timestamp": "2026-01-15T10:00:00Z",
                    "root_path": "test",
                    "lizard_version": "lizard 1.17.10",
                    "files": [
                        {
                            "path": "simple.py",
                            "language": "Python",
                            "nloc": 50,
                            "function_count": 3,
                            "total_ccn": 5,
                            "avg_ccn": 1.67,
                            "max_ccn": 2,
                            "functions": [
                                {"name": "add", "ccn": 1, "nloc": 3, "parameter_count": 2, "start_line": 1, "end_line": 3},
                                {"name": "sub", "ccn": 1, "nloc": 3, "parameter_count": 2, "start_line": 5, "end_line": 7},
                                {"name": "div", "ccn": 2, "nloc": 5, "parameter_count": 2, "start_line": 9, "end_line": 13},
                            ],
                        }
                    ],
                    "summary": {
                        "total_files": 1,
                        "total_functions": 3,
                        "total_nloc": 50,
                        "total_ccn": 5,
                        "avg_ccn": 1.67,
                        "max_ccn": 2,
                        "functions_over_threshold": 0,
                    },
                    "directories": [],
                },
            }

            # Create test ground truth directory with python.json
            gt_dir = temp_dir / "ground-truth"
            gt_dir.mkdir()

            ground_truth = {
                "language": "python",
                "generated_at": "2026-01-15T10:00:00Z",
                "lizard_version": "lizard 1.19.0",
                "total_files": 1,
                "total_functions": 3,
                "total_ccn": 5,
                "files": {
                    "simple.py": {
                        "expected_functions": 3,
                        "total_ccn": 5,
                        "functions": {
                            "add": {"ccn": 1, "nloc": 3, "params": 2, "start_line": 1, "end_line": 3},
                            "sub": {"ccn": 1, "nloc": 3, "params": 2, "start_line": 5, "end_line": 7},
                            "div": {"ccn": 2, "nloc": 5, "params": 2, "start_line": 9, "end_line": 13},
                        },
                    },
                },
            }

            # Write files
            analysis_path = temp_dir / "output.json"
            analysis_path.write_text(json.dumps(analysis_data))
            (gt_dir / "python.json").write_text(json.dumps(ground_truth))

            # Run evaluation (takes ground truth directory, not file)
            report = run_evaluation(analysis_path, gt_dir)

            assert report is not None
            assert report.total_checks > 0
        finally:
            if str(scripts_dir) in sys.path:
                sys.path.remove(str(scripts_dir))
