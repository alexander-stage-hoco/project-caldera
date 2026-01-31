"""Integration tests for ground truth validation."""

import json
import sys
from pathlib import Path

import pytest


class TestGroundTruthStructure:
    """Tests for ground truth file structure validation."""

    @pytest.fixture
    def lizard_root(self) -> Path:
        """Return the lizard tool root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def ground_truth_dir(self, lizard_root) -> Path:
        """Return the ground truth directory."""
        return lizard_root / "evaluation" / "ground-truth"

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

    def test_ground_truth_files_have_language(self, ground_truth_dir):
        """Test that ground truth files have language field."""
        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())

            assert "language" in data, f"{gt_file.name} missing language field"
            assert data["language"] == gt_file.stem, (
                f"{gt_file.name} language mismatch: {data['language']} != {gt_file.stem}"
            )

    def test_ground_truth_files_have_files(self, ground_truth_dir):
        """Test that ground truth files have files field."""
        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())

            assert "files" in data, f"{gt_file.name} missing files field"
            assert isinstance(data["files"], dict), f"{gt_file.name} files is not a dict"

    def test_ground_truth_files_have_totals(self, ground_truth_dir):
        """Test that ground truth files have total counts."""
        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())

            assert "total_files" in data, f"{gt_file.name} missing total_files"
            assert "total_functions" in data, f"{gt_file.name} missing total_functions"
            assert "total_ccn" in data, f"{gt_file.name} missing total_ccn"


class TestGroundTruthFunctions:
    """Tests for ground truth function entries."""

    @pytest.fixture
    def lizard_root(self) -> Path:
        """Return the lizard tool root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def ground_truth_dir(self, lizard_root) -> Path:
        """Return the ground truth directory."""
        return lizard_root / "evaluation" / "ground-truth"

    def test_function_entries_have_ccn(self, ground_truth_dir):
        """Test that function entries have CCN field."""
        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())

            for file_name, file_data in data.get("files", {}).items():
                for func_name, func_data in file_data.get("functions", {}).items():
                    assert "ccn" in func_data, (
                        f"{gt_file.name} {file_name}:{func_name} missing ccn"
                    )

    def test_function_entries_have_nloc(self, ground_truth_dir):
        """Test that function entries have NLOC field."""
        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())

            for file_name, file_data in data.get("files", {}).items():
                for func_name, func_data in file_data.get("functions", {}).items():
                    assert "nloc" in func_data, (
                        f"{gt_file.name} {file_name}:{func_name} missing nloc"
                    )

    def test_function_entries_have_params(self, ground_truth_dir):
        """Test that function entries have params field."""
        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())

            for file_name, file_data in data.get("files", {}).items():
                for func_name, func_data in file_data.get("functions", {}).items():
                    assert "params" in func_data, (
                        f"{gt_file.name} {file_name}:{func_name} missing params"
                    )

    def test_ccn_values_non_negative(self, ground_truth_dir):
        """Test that CCN values are non-negative integers."""
        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())

            for file_name, file_data in data.get("files", {}).items():
                for func_name, func_data in file_data.get("functions", {}).items():
                    ccn = func_data.get("ccn", 0)
                    assert isinstance(ccn, int), (
                        f"{gt_file.name} {file_name}:{func_name} ccn is not int"
                    )
                    assert ccn >= 0, (
                        f"{gt_file.name} {file_name}:{func_name} ccn is negative: {ccn}"
                    )

    def test_ccn_minimum_is_one_for_functions(self, ground_truth_dir):
        """Test that CCN is at least 1 for actual functions."""
        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())

            for file_name, file_data in data.get("files", {}).items():
                for func_name, func_data in file_data.get("functions", {}).items():
                    ccn = func_data.get("ccn", 0)
                    # CCN should be at least 1 for any actual function
                    assert ccn >= 1, (
                        f"{gt_file.name} {file_name}:{func_name} ccn < 1: {ccn}"
                    )

    def test_nloc_values_non_negative(self, ground_truth_dir):
        """Test that NLOC values are non-negative."""
        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())

            for file_name, file_data in data.get("files", {}).items():
                for func_name, func_data in file_data.get("functions", {}).items():
                    nloc = func_data.get("nloc", 0)
                    assert nloc >= 0, (
                        f"{gt_file.name} {file_name}:{func_name} nloc is negative: {nloc}"
                    )

    def test_params_values_non_negative(self, ground_truth_dir):
        """Test that params values are non-negative."""
        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())

            for file_name, file_data in data.get("files", {}).items():
                for func_name, func_data in file_data.get("functions", {}).items():
                    params = func_data.get("params", 0)
                    assert params >= 0, (
                        f"{gt_file.name} {file_name}:{func_name} params is negative: {params}"
                    )


class TestGroundTruthCompleteness:
    """Tests for ground truth coverage completeness."""

    @pytest.fixture
    def lizard_root(self) -> Path:
        """Return the lizard tool root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def ground_truth_dir(self, lizard_root) -> Path:
        """Return the ground truth directory."""
        return lizard_root / "evaluation" / "ground-truth"

    @pytest.fixture
    def synthetic_dir(self, lizard_root) -> Path:
        """Return the synthetic repos directory."""
        return lizard_root / "eval-repos" / "synthetic"

    def test_all_synthetic_repos_have_ground_truth(self, synthetic_dir, ground_truth_dir):
        """Test that every synthetic repo has a ground truth file."""
        if not synthetic_dir.exists():
            pytest.skip("Synthetic repos directory not found")

        synthetic_repos = [d.name for d in synthetic_dir.iterdir() if d.is_dir()]
        gt_files = [f.stem for f in ground_truth_dir.glob("*.json")]

        missing = []
        for repo in synthetic_repos:
            if repo not in gt_files:
                missing.append(repo)

        assert not missing, f"Synthetic repos without ground truth: {missing}"

    def test_ground_truth_count(self, ground_truth_dir):
        """Test that we have expected number of ground truth files."""
        gt_files = list(ground_truth_dir.glob("*.json"))

        # We expect 7 ground truth files (one per language)
        assert len(gt_files) == 7, (
            f"Expected 7 ground truth files, found {len(gt_files)}: {[f.name for f in gt_files]}"
        )

    def test_all_languages_covered(self, ground_truth_dir):
        """Test that ground truth files cover all 7 languages."""
        expected_languages = {"python", "csharp", "java", "javascript", "typescript", "go", "rust"}
        gt_files = {f.stem for f in ground_truth_dir.glob("*.json")}

        missing = expected_languages - gt_files
        assert not missing, f"Missing ground truth for languages: {missing}"


class TestGroundTruthLineRanges:
    """Tests for ground truth line range information."""

    @pytest.fixture
    def lizard_root(self) -> Path:
        """Return the lizard tool root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def ground_truth_dir(self, lizard_root) -> Path:
        """Return the ground truth directory."""
        return lizard_root / "evaluation" / "ground-truth"

    def test_function_entries_have_line_ranges(self, ground_truth_dir):
        """Test that function entries have start_line and end_line."""
        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())

            for file_name, file_data in data.get("files", {}).items():
                for func_name, func_data in file_data.get("functions", {}).items():
                    assert "start_line" in func_data, (
                        f"{gt_file.name} {file_name}:{func_name} missing start_line"
                    )
                    assert "end_line" in func_data, (
                        f"{gt_file.name} {file_name}:{func_name} missing end_line"
                    )

    def test_line_ranges_valid(self, ground_truth_dir):
        """Test that line ranges are valid (start <= end, both positive)."""
        for gt_file in ground_truth_dir.glob("*.json"):
            data = json.loads(gt_file.read_text())

            for file_name, file_data in data.get("files", {}).items():
                for func_name, func_data in file_data.get("functions", {}).items():
                    start = func_data.get("start_line", 0)
                    end = func_data.get("end_line", 0)

                    assert start > 0, (
                        f"{gt_file.name} {file_name}:{func_name} start_line <= 0: {start}"
                    )
                    assert end >= start, (
                        f"{gt_file.name} {file_name}:{func_name} end_line < start_line: {end} < {start}"
                    )


class TestGroundTruthEvaluation:
    """Tests for running evaluation against ground truth."""

    @pytest.fixture
    def lizard_root(self) -> Path:
        """Return the lizard tool root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def ground_truth_dir(self, lizard_root) -> Path:
        """Return the ground truth directory."""
        return lizard_root / "evaluation" / "ground-truth"

    @pytest.fixture
    def output_dir(self, lizard_root) -> Path:
        """Return the output directory."""
        return lizard_root / "output"

    def _find_analysis_files(self, output_dir: Path):
        """Find output.json files in the output directory."""
        if not output_dir.exists():
            return []
        return list(output_dir.glob("output.json"))

    def test_evaluate_against_ground_truth(self, lizard_root, output_dir, ground_truth_dir):
        """Test that evaluation can run against ground truth."""
        scripts_dir = lizard_root / "scripts"
        sys.path.insert(0, str(scripts_dir))

        try:
            from evaluate import run_evaluation

            analysis_files = self._find_analysis_files(output_dir)
            if not analysis_files:
                pytest.skip("No output files found")

            # Run evaluation on first available analysis file
            analysis_path = analysis_files[0]
            report = run_evaluation(analysis_path, ground_truth_dir)

            assert report is not None
            assert report.total_checks > 0
        finally:
            if str(scripts_dir) in sys.path:
                sys.path.remove(str(scripts_dir))

    def test_evaluation_report_structure(self, lizard_root, output_dir, ground_truth_dir):
        """Test that evaluation report has expected structure."""
        scripts_dir = lizard_root / "scripts"
        sys.path.insert(0, str(scripts_dir))

        try:
            from evaluate import run_evaluation

            analysis_files = self._find_analysis_files(output_dir)
            if not analysis_files:
                pytest.skip("No output files found")

            # Run evaluation on first available analysis file
            analysis_path = analysis_files[0]
            report = run_evaluation(analysis_path, ground_truth_dir)

            # Check report structure
            assert hasattr(report, "total_checks")
            assert hasattr(report, "passed_checks")
            assert hasattr(report, "failed_checks")
            assert hasattr(report, "overall_score")
            assert hasattr(report, "checks")

            # Score should be between 0 and 1
            assert 0.0 <= report.overall_score <= 1.0
        finally:
            if str(scripts_dir) in sys.path:
                sys.path.remove(str(scripts_dir))
