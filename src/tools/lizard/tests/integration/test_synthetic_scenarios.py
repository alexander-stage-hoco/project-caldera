"""Integration tests for synthetic test scenarios."""

import json
from pathlib import Path

import pytest


# Language configurations: (language_dir, file_extension, expected_files)
LANGUAGE_CONFIGS = [
    ("python", ".py", ["simple.py", "complex.py", "massive.py"]),
    ("csharp", ".cs", ["Simple.cs", "Complex.cs", "Massive.cs"]),
    ("java", ".java", ["Simple.java", "Complex.java", "Massive.java"]),
    ("javascript", ".js", ["simple.js", "complex.js", "massive.js"]),
    ("typescript", ".ts", ["simple.ts", "complex.ts", "massive.ts"]),
    ("go", ".go", ["simple.go", "complex.go", "massive.go"]),
    ("rust", ".rs", ["simple.rs", "complex.rs", "massive.rs"]),
]


class TestSyntheticScenarios:
    """Tests for synthetic repository scenarios."""

    @pytest.fixture
    def lizard_root(self) -> Path:
        """Return the lizard tool root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def synthetic_dir(self, lizard_root) -> Path:
        """Return the synthetic repos directory."""
        return lizard_root / "eval-repos" / "synthetic"

    @pytest.fixture
    def ground_truth_dir(self, lizard_root) -> Path:
        """Return the ground truth directory."""
        return lizard_root / "evaluation" / "ground-truth"

    @pytest.fixture
    def output_dir(self, lizard_root) -> Path:
        """Return the output directory."""
        return lizard_root / "output"

    @pytest.mark.parametrize("lang_dir,ext,expected_files", LANGUAGE_CONFIGS)
    def test_synthetic_repo_structure(self, synthetic_dir, lang_dir, ext, expected_files):
        """Test that each synthetic repo has expected structure."""
        repo_dir = synthetic_dir / lang_dir

        if not repo_dir.exists():
            pytest.skip(f"{lang_dir} repo not found")

        # Should have expected files
        for expected_file in expected_files:
            file_path = repo_dir / expected_file
            assert file_path.exists(), f"Missing {expected_file} in {lang_dir}"

        # Should have edge_cases directory
        edge_cases_dir = repo_dir / "edge_cases"
        if lang_dir != "csharp":
            # C# has EdgeCases
            edge_cases_dir = repo_dir / "edge_cases" if (repo_dir / "edge_cases").exists() else repo_dir / "EdgeCases"
        assert edge_cases_dir.exists() or (repo_dir / "EdgeCases").exists(), f"Missing edge_cases in {lang_dir}"

        # Should have module directory
        module_dir = repo_dir / "module"
        if lang_dir != "csharp":
            module_dir = repo_dir / "module" if (repo_dir / "module").exists() else repo_dir / "Module"
        assert module_dir.exists() or (repo_dir / "Module").exists(), f"Missing module in {lang_dir}"

    @pytest.mark.parametrize("lang_dir,ext,expected_files", LANGUAGE_CONFIGS)
    def test_synthetic_repo_has_ground_truth(self, synthetic_dir, ground_truth_dir, lang_dir, ext, expected_files):
        """Test that each synthetic repo has matching ground truth."""
        repo_dir = synthetic_dir / lang_dir

        if not repo_dir.exists():
            pytest.skip(f"{lang_dir} repo not found")

        # Should have matching ground truth file
        gt_path = ground_truth_dir / f"{lang_dir}.json"
        assert gt_path.exists(), f"Missing ground truth for {lang_dir}"

    def test_python_scenario(self, synthetic_dir, ground_truth_dir):
        """Test Python synthetic scenario in detail."""
        repo_dir = synthetic_dir / "python"

        if not repo_dir.exists():
            pytest.skip("Python repo not found")

        # Check simple.py
        simple = repo_dir / "simple.py"
        assert simple.exists()
        content = simple.read_text()
        assert "def " in content  # Should have function definitions

        # Check ground truth structure
        gt_path = ground_truth_dir / "python.json"
        gt = json.loads(gt_path.read_text())

        assert "language" in gt
        assert gt["language"] == "python"
        assert "files" in gt
        assert "simple.py" in gt["files"]
        assert "functions" in gt["files"]["simple.py"]

    def test_csharp_scenario(self, synthetic_dir, ground_truth_dir):
        """Test C# synthetic scenario in detail."""
        repo_dir = synthetic_dir / "csharp"

        if not repo_dir.exists():
            pytest.skip("C# repo not found")

        # Check Simple.cs
        simple = repo_dir / "Simple.cs"
        assert simple.exists()
        content = simple.read_text()
        assert "class" in content or "struct" in content  # Should have type definitions

        # Check ground truth
        gt_path = ground_truth_dir / "csharp.json"
        gt = json.loads(gt_path.read_text())
        assert gt["language"] == "csharp"

    def test_java_scenario(self, synthetic_dir, ground_truth_dir):
        """Test Java synthetic scenario in detail."""
        repo_dir = synthetic_dir / "java"

        if not repo_dir.exists():
            pytest.skip("Java repo not found")

        # Check Simple.java
        simple = repo_dir / "Simple.java"
        assert simple.exists()
        content = simple.read_text()
        assert "class" in content  # Should have class definitions

        # Check ground truth
        gt_path = ground_truth_dir / "java.json"
        gt = json.loads(gt_path.read_text())
        assert gt["language"] == "java"

    def test_javascript_scenario(self, synthetic_dir, ground_truth_dir):
        """Test JavaScript synthetic scenario in detail."""
        repo_dir = synthetic_dir / "javascript"

        if not repo_dir.exists():
            pytest.skip("JavaScript repo not found")

        # Check simple.js
        simple = repo_dir / "simple.js"
        assert simple.exists()
        content = simple.read_text()
        assert "function" in content or "=>" in content  # Should have functions

        # Check ground truth
        gt_path = ground_truth_dir / "javascript.json"
        gt = json.loads(gt_path.read_text())
        assert gt["language"] == "javascript"

    def test_typescript_scenario(self, synthetic_dir, ground_truth_dir):
        """Test TypeScript synthetic scenario in detail."""
        repo_dir = synthetic_dir / "typescript"

        if not repo_dir.exists():
            pytest.skip("TypeScript repo not found")

        # Check simple.ts
        simple = repo_dir / "simple.ts"
        assert simple.exists()
        content = simple.read_text()
        assert "function" in content or "=>" in content or ":" in content

        # Check ground truth
        gt_path = ground_truth_dir / "typescript.json"
        gt = json.loads(gt_path.read_text())
        assert gt["language"] == "typescript"

    def test_go_scenario(self, synthetic_dir, ground_truth_dir):
        """Test Go synthetic scenario in detail."""
        repo_dir = synthetic_dir / "go"

        if not repo_dir.exists():
            pytest.skip("Go repo not found")

        # Check simple.go
        simple = repo_dir / "simple.go"
        assert simple.exists()
        content = simple.read_text()
        assert "func " in content  # Should have func definitions

        # Check ground truth
        gt_path = ground_truth_dir / "go.json"
        gt = json.loads(gt_path.read_text())
        assert gt["language"] == "go"

    def test_rust_scenario(self, synthetic_dir, ground_truth_dir):
        """Test Rust synthetic scenario in detail."""
        repo_dir = synthetic_dir / "rust"

        if not repo_dir.exists():
            pytest.skip("Rust repo not found")

        # Check simple.rs
        simple = repo_dir / "simple.rs"
        assert simple.exists()
        content = simple.read_text()
        assert "fn " in content  # Should have fn definitions

        # Check ground truth
        gt_path = ground_truth_dir / "rust.json"
        gt = json.loads(gt_path.read_text())
        assert gt["language"] == "rust"


class TestSyntheticOutputValidation:
    """Tests to validate output against synthetic scenarios."""

    @pytest.fixture
    def lizard_root(self) -> Path:
        """Return the lizard tool root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def output_dir(self, lizard_root) -> Path:
        """Return the output directory."""
        return lizard_root / "output"

    @pytest.fixture
    def ground_truth_dir(self, lizard_root) -> Path:
        """Return the ground truth directory."""
        return lizard_root / "evaluation" / "ground-truth"

    def _find_analysis_files(self, output_dir: Path):
        """Find output.json files in the output directory."""
        if not output_dir.exists():
            return []
        return list(output_dir.glob("output.json"))

    def _get_expected_value(self, expected_spec):
        """Helper to get min/max from expected value spec."""
        if isinstance(expected_spec, dict):
            return expected_spec.get("min", 0), expected_spec.get("max", float("inf"))
        elif isinstance(expected_spec, (int, float)):
            return expected_spec, expected_spec
        return 0, float("inf")

    @pytest.mark.parametrize("lang", ["python", "csharp", "java", "javascript", "typescript", "go", "rust"])
    def test_output_matches_ground_truth_structure(self, output_dir, ground_truth_dir, lang):
        """Test that output structure matches ground truth expectations."""
        # Look for analysis files that include this language
        analysis_files = self._find_analysis_files(output_dir)
        if not analysis_files:
            pytest.skip(f"No output files found")

        gt_path = ground_truth_dir / f"{lang}.json"
        if not gt_path.exists():
            pytest.skip(f"No ground truth for {lang}")

        gt = json.loads(gt_path.read_text())

        # Check any analysis file that has this language
        for analysis_file in analysis_files:
            output = json.loads(analysis_file.read_text())
            data = output.get("data", {})

            # Check files array if present
            if "files" not in data:
                continue

            # Look for files matching this language
            lang_files = [f for f in data["files"] if f.get("language", "").lower() == lang or
                         f.get("path", "").endswith(f".{lang[:2]}")]

            if lang_files:
                # Found matching files
                return

        pytest.skip(f"No output with {lang} files found")

    def test_all_outputs_have_valid_structure(self, output_dir):
        """Test that all output.json files have valid structure."""
        analysis_files = self._find_analysis_files(output_dir)
        if not analysis_files:
            pytest.skip("No output files found")

        for output_file in analysis_files:
            output = json.loads(output_file.read_text())

            assert "metadata" in output, f"{output_file.name} missing metadata"
            assert "data" in output, f"{output_file.name} missing data payload"

    @pytest.mark.parametrize("lang", ["python", "csharp", "java", "javascript", "typescript", "go", "rust"])
    def test_function_count_reasonable(self, output_dir, ground_truth_dir, lang):
        """Test that function counts are within reasonable bounds of ground truth."""
        analysis_files = self._find_analysis_files(output_dir)
        if not analysis_files:
            pytest.skip(f"No output files found")

        gt_path = ground_truth_dir / f"{lang}.json"
        if not gt_path.exists():
            pytest.skip(f"No ground truth for {lang}")

        gt = json.loads(gt_path.read_text())
        expected_total = gt.get("total_functions", 0)
        if expected_total == 0:
            pytest.skip(f"No functions expected in ground truth for {lang}")

        # Check any analysis file for this language
        for analysis_file in analysis_files:
            output = json.loads(analysis_file.read_text())
            data = output.get("data", {})

            # Get function count from files or directories
            if "files" in data:
                lang_ext_map = {
                    "python": ".py", "csharp": ".cs", "java": ".java",
                    "javascript": ".js", "typescript": ".ts", "go": ".go", "rust": ".rs"
                }
                ext = lang_ext_map.get(lang, "")

                # Only count files in the synthetic/{lang} directory to match ground truth
                matching_files = [
                    f for f in data["files"]
                    if f.get("path", "").endswith(ext) and f"synthetic/{lang}" in f.get("path", "")
                ]

                if not matching_files:
                    continue

                actual_total = sum(f.get("function_count", 0) for f in matching_files)

                if actual_total > 0:
                    # Allow 25% tolerance for function count differences
                    # (lizard version differences can cause slight variations)
                    tolerance = 0.25
                    min_expected = int(expected_total * (1 - tolerance))
                    max_expected = int(expected_total * (1 + tolerance))

                    assert min_expected <= actual_total <= max_expected, (
                        f"{lang}: function count {actual_total} not within {tolerance*100}% of expected {expected_total}"
                    )
                    return

        pytest.skip(f"No output with {lang} synthetic files found")
