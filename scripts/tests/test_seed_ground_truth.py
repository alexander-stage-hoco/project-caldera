"""Tests for the ground truth auto-seeding script."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from seed_ground_truth import (
    TOOL_SEEDERS,
    seed_ground_truth,
    seed_scc_ground_truth,
    seed_lizard_ground_truth,
    seed_semgrep_ground_truth,
    seed_layout_ground_truth,
    seed_roslyn_ground_truth,
    seed_trivy_ground_truth,
    seed_git_sizer_ground_truth,
)


class TestSccGroundTruthSeeder:
    """Tests for scc ground truth seeding."""

    def test_extracts_language_stats(self) -> None:
        """Test that language statistics are extracted from scc output."""
        data = {
            "directories": [
                {
                    "path": ".",
                    "recursive": {
                        "file_count": 10,
                        "code": 1000,
                        "complexity_total": 50,
                        "by_language": {
                            "Python": {"file_count": 5, "code": 600},
                            "JavaScript": {"file_count": 5, "code": 400},
                        },
                    },
                }
            ]
        }
        metadata = {"run_id": "test-run", "commit": "abc123", "timestamp": "2026-01-01T00:00:00Z"}

        result = seed_scc_ground_truth(data, metadata)

        assert "languages" in result
        assert "Python" in result["languages"]
        assert result["languages"]["Python"]["expected_file_count"] == 5
        # Check LOC range (10% variance)
        assert result["languages"]["Python"]["expected_loc_range"] == [540, 660]

    def test_extracts_aggregate_expectations(self) -> None:
        """Test that aggregate expectations are calculated."""
        data = {
            "directories": [
                {
                    "path": ".",
                    "recursive": {
                        "file_count": 10,
                        "code": 1000,
                        "complexity_total": 50,
                        "by_language": {"Python": {"file_count": 10, "code": 1000}},
                    },
                }
            ]
        }
        metadata = {"run_id": "test-run"}

        result = seed_scc_ground_truth(data, metadata)

        assert result["aggregate_expectations"]["total_files"] == 10
        assert result["aggregate_expectations"]["total_languages"] == 1
        assert result["aggregate_expectations"]["minimum_total_loc"] == 900
        assert result["aggregate_expectations"]["maximum_total_loc"] == 1100

    def test_includes_verification_status(self) -> None:
        """Test that verification status is pending_review."""
        data = {"directories": []}
        metadata = {"run_id": "test-run"}

        result = seed_scc_ground_truth(data, metadata)

        assert result["verification_status"] == "pending_review"

    def test_includes_seeded_from_metadata(self) -> None:
        """Test that seeded_from includes source metadata."""
        data = {"directories": []}
        metadata = {"run_id": "run-123", "commit": "abc123", "timestamp": "2026-01-01T00:00:00Z"}

        result = seed_scc_ground_truth(data, metadata)

        assert result["seeded_from"]["run_id"] == "run-123"
        assert result["seeded_from"]["commit"] == "abc123"


class TestLizardGroundTruthSeeder:
    """Tests for lizard ground truth seeding."""

    def test_extracts_file_metrics(self) -> None:
        """Test that file metrics are extracted from lizard output."""
        data = {
            "files": [
                {
                    "file_path": "src/main.py",
                    "functions": [
                        {"name": "main", "ccn": 5, "nloc": 20, "params": 2, "start_line": 1, "end_line": 20},
                        {"name": "helper", "ccn": 3, "nloc": 10, "params": 1, "start_line": 25, "end_line": 35},
                    ],
                }
            ]
        }
        metadata = {"run_id": "test-run"}

        result = seed_lizard_ground_truth(data, metadata)

        assert result["total_files"] == 1
        assert result["total_functions"] == 2
        assert result["total_ccn"] == 8
        assert "src/main.py" in result["files"]
        assert result["files"]["src/main.py"]["expected_functions"] == 2

    def test_extracts_function_details(self) -> None:
        """Test that individual function details are extracted."""
        data = {
            "files": [
                {
                    "file_path": "src/main.py",
                    "functions": [
                        {"name": "main", "ccn": 5, "nloc": 20, "params": 2, "start_line": 1, "end_line": 20},
                    ],
                }
            ]
        }
        metadata = {"run_id": "test-run"}

        result = seed_lizard_ground_truth(data, metadata)

        func = result["files"]["src/main.py"]["functions"]["main"]
        assert func["ccn"] == 5
        assert func["nloc"] == 20
        assert func["params"] == 2

    def test_handles_empty_files(self) -> None:
        """Test that empty files list is handled."""
        data = {"files": []}
        metadata = {"run_id": "test-run"}

        result = seed_lizard_ground_truth(data, metadata)

        assert result["verification_status"] == "pending_review"
        assert "total_files" not in result


class TestSemgrepGroundTruthSeeder:
    """Tests for semgrep ground truth seeding."""

    def test_aggregates_by_severity(self) -> None:
        """Test that findings are aggregated by severity."""
        data = {
            "findings": [
                {"severity": "WARNING", "rule_id": "rule1", "file_path": "src/a.py", "line_start": 1, "line_end": 1},
                {"severity": "WARNING", "rule_id": "rule2", "file_path": "src/b.py", "line_start": 2, "line_end": 2},
                {"severity": "ERROR", "rule_id": "rule3", "file_path": "src/c.py", "line_start": 3, "line_end": 3},
            ]
        }
        metadata = {"run_id": "test-run"}

        result = seed_semgrep_ground_truth(data, metadata)

        assert result["total_findings"] == 3
        assert result["findings_by_severity"]["WARNING"] == 2
        assert result["findings_by_severity"]["ERROR"] == 1

    def test_aggregates_by_rule(self) -> None:
        """Test that findings are aggregated by rule."""
        data = {
            "findings": [
                {"severity": "WARNING", "rule_id": "rule1", "file_path": "src/a.py", "line_start": 1, "line_end": 1},
                {"severity": "WARNING", "rule_id": "rule1", "file_path": "src/b.py", "line_start": 2, "line_end": 2},
                {"severity": "ERROR", "rule_id": "rule2", "file_path": "src/c.py", "line_start": 3, "line_end": 3},
            ]
        }
        metadata = {"run_id": "test-run"}

        result = seed_semgrep_ground_truth(data, metadata)

        assert result["findings_by_rule"]["rule1"] == 2
        assert result["findings_by_rule"]["rule2"] == 1

    def test_handles_empty_findings(self) -> None:
        """Test that empty findings list is handled."""
        data = {"findings": []}
        metadata = {"run_id": "test-run"}

        result = seed_semgrep_ground_truth(data, metadata)

        assert result["total_findings"] == 0


class TestLayoutGroundTruthSeeder:
    """Tests for layout-scanner ground truth seeding."""

    def test_counts_file_classifications(self) -> None:
        """Test that file classifications are counted."""
        data = {
            "files": [
                {"classification": "source", "language": "Python"},
                {"classification": "source", "language": "Python"},
                {"classification": "test", "language": "Python"},
            ],
            "directories": [],
        }
        metadata = {"run_id": "test-run"}

        result = seed_layout_ground_truth(data, metadata)

        assert result["file_expectations"]["total_files"] == 3
        assert result["file_expectations"]["classification_counts"]["source"] == 2
        assert result["file_expectations"]["classification_counts"]["test"] == 1

    def test_counts_directory_purposes(self) -> None:
        """Test that directory purposes are counted."""
        data = {
            "files": [],
            "directories": [
                {"purpose": "source"},
                {"purpose": "source"},
                {"purpose": "test"},
            ],
        }
        metadata = {"run_id": "test-run"}

        result = seed_layout_ground_truth(data, metadata)

        assert result["directory_expectations"]["total_directories"] == 3
        assert result["directory_expectations"]["purpose_counts"]["source"] == 2


class TestRoslynGroundTruthSeeder:
    """Tests for roslyn-analyzers ground truth seeding."""

    def test_aggregates_violations(self) -> None:
        """Test that violations are aggregated."""
        data = {
            "violations": [
                {"severity": "warning", "rule_id": "CS0001", "file_path": "Program.cs", "line": 10},
                {"severity": "warning", "rule_id": "CS0001", "file_path": "Program.cs", "line": 20},
                {"severity": "error", "rule_id": "CS0002", "file_path": "Helper.cs", "line": 5},
            ]
        }
        metadata = {"run_id": "test-run"}

        result = seed_roslyn_ground_truth(data, metadata)

        assert result["total_violations"] == 3
        assert result["violations_by_severity"]["warning"] == 2
        assert result["violations_by_severity"]["error"] == 1

    def test_handles_empty_violations(self) -> None:
        """Test that empty violations list is handled."""
        data = {"violations": []}
        metadata = {"run_id": "test-run"}

        result = seed_roslyn_ground_truth(data, metadata)

        assert result["total_violations"] == 0


class TestTrivyGroundTruthSeeder:
    """Tests for trivy ground truth seeding."""

    def test_extracts_vulnerability_expectations(self) -> None:
        """Test that vulnerability expectations are extracted."""
        data = {
            "vulnerabilities": [
                {"severity": "HIGH", "package_name": "openssl"},
                {"severity": "MEDIUM", "package_name": "openssl"},
                {"severity": "HIGH", "package_name": "curl"},
            ],
            "misconfigurations": [],
        }
        metadata = {"run_id": "test-run"}

        result = seed_trivy_ground_truth(data, metadata)

        assert result["vulnerability_expectations"]["total_vulnerabilities"] == 3
        assert result["vulnerability_expectations"]["by_severity"]["HIGH"] == 2
        assert result["vulnerability_expectations"]["by_package"]["openssl"] == 2

    def test_extracts_misconfiguration_expectations(self) -> None:
        """Test that misconfiguration expectations are extracted."""
        data = {
            "vulnerabilities": [],
            "misconfigurations": [
                {"severity": "MEDIUM", "type": "kubernetes"},
                {"severity": "HIGH", "type": "dockerfile"},
            ],
        }
        metadata = {"run_id": "test-run"}

        result = seed_trivy_ground_truth(data, metadata)

        assert result["misconfiguration_expectations"]["total_misconfigurations"] == 2


class TestGitSizerGroundTruthSeeder:
    """Tests for git-sizer ground truth seeding."""

    def test_extracts_metric_expectations(self) -> None:
        """Test that metric expectations are extracted."""
        data = {
            "metrics": {
                "repository": {"commits": 100, "branches": 5},
                "blobs": {"count": 1000},
            },
            "violations": [],
            "lfs_candidates": [],
        }
        metadata = {"run_id": "test-run"}

        result = seed_git_sizer_ground_truth(data, metadata)

        assert "repository" in result["metric_expectations"]
        assert result["metric_expectations"]["repository"]["commits"]["expected_value"] == 100

    def test_extracts_violation_expectations(self) -> None:
        """Test that violation expectations are extracted."""
        data = {
            "metrics": {},
            "violations": [
                {"level": "warning"},
                {"level": "critical"},
                {"level": "warning"},
            ],
            "lfs_candidates": [],
        }
        metadata = {"run_id": "test-run"}

        result = seed_git_sizer_ground_truth(data, metadata)

        assert result["violation_expectations"]["total_violations"] == 3
        assert result["violation_expectations"]["by_level"]["warning"] == 2


class TestSeedGroundTruthFunction:
    """Tests for the main seed_ground_truth function."""

    def test_raises_for_unsupported_tool(self, tmp_path: Path) -> None:
        """Test that unsupported tools raise ValueError."""
        output_path = tmp_path / "output.json"
        output_path.write_text('{"metadata": {}, "data": {}}')

        with pytest.raises(ValueError, match="Unsupported tool"):
            seed_ground_truth("unknown-tool", output_path)

    def test_raises_for_missing_file(self, tmp_path: Path) -> None:
        """Test that missing files raise ValueError."""
        with pytest.raises(ValueError, match="not found"):
            seed_ground_truth("scc", tmp_path / "nonexistent.json")

    def test_raises_for_invalid_json(self, tmp_path: Path) -> None:
        """Test that invalid JSON raises ValueError."""
        output_path = tmp_path / "output.json"
        output_path.write_text("not valid json")

        with pytest.raises(ValueError, match="Invalid JSON"):
            seed_ground_truth("scc", output_path)

    def test_raises_for_missing_sections(self, tmp_path: Path) -> None:
        """Test that missing metadata/data sections raise ValueError."""
        output_path = tmp_path / "output.json"
        output_path.write_text('{"metadata": {}}')  # Missing data

        with pytest.raises(ValueError, match="metadata.*data"):
            seed_ground_truth("scc", output_path)

    def test_calls_correct_seeder(self, tmp_path: Path) -> None:
        """Test that the correct seeder is called based on tool name."""
        output_path = tmp_path / "output.json"
        output = {
            "metadata": {"run_id": "test"},
            "data": {"files": [{"file_path": "main.py", "functions": []}]},
        }
        output_path.write_text(json.dumps(output))

        result = seed_ground_truth("lizard", output_path)

        # Lizard seeder should produce total_files key for files data
        assert result["schema_version"] == "2.0"


class TestToolSeedersRegistry:
    """Tests for the TOOL_SEEDERS registry."""

    def test_all_expected_tools_registered(self) -> None:
        """Test that all expected tools have seeders registered."""
        expected_tools = {"scc", "lizard", "semgrep", "layout-scanner", "roslyn-analyzers", "trivy", "git-sizer"}
        assert set(TOOL_SEEDERS.keys()) == expected_tools

    def test_seeders_are_callable(self) -> None:
        """Test that all seeders are callable."""
        for tool_name, seeder in TOOL_SEEDERS.items():
            assert callable(seeder), f"{tool_name} seeder is not callable"
