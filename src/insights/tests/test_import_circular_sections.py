"""Tests for ImportDependenciesSection and CircularDependenciesSection fetch_data."""

from unittest.mock import MagicMock

from insights.sections.import_dependencies import ImportDependenciesSection
from insights.sections.circular_dependencies import CircularDependenciesSection


class TestImportDependenciesFetchData:
    """Tests for ImportDependenciesSection.fetch_data with mocked fetcher."""

    def test_fetch_data_no_data(self):
        """Test fetch_data when fetcher raises Exception → fallback."""
        section = ImportDependenciesSection()
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.side_effect = Exception("No data")

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert data["has_data"] is False
        assert data["top_importers"] == []
        assert data["most_imported_targets"] == []
        assert data["summary"]["total_files"] == 0

    def test_fetch_data_with_importers(self):
        """Test fetch_data with importer and target data."""
        section = ImportDependenciesSection()
        mock_fetcher = MagicMock()

        mock_fetcher.fetch.side_effect = [
            # import_dependencies query (top importers)
            [
                {
                    "relative_path": "src/main.py",
                    "import_count": 25,
                    "unique_imports": 20,
                    "static_import_count": 23,
                    "dynamic_import_count": 2,
                    "side_effect_import_count": 0,
                },
                {
                    "relative_path": "src/utils.py",
                    "import_count": 10,
                    "unique_imports": 8,
                    "static_import_count": 10,
                    "dynamic_import_count": 0,
                    "side_effect_import_count": 1,
                },
                {
                    "relative_path": "src/models.py",
                    "import_count": 5,
                    "unique_imports": 5,
                    "static_import_count": 5,
                    "dynamic_import_count": 0,
                    "side_effect_import_count": 0,
                },
            ],
            # import_dependencies_targets query (most imported)
            [
                {
                    "imported_path": "src/config.py",
                    "reference_count": 30,
                    "importing_files": 8,
                },
                {
                    "imported_path": "src/utils.py",
                    "reference_count": 15,
                    "importing_files": 5,
                },
            ],
        ]

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert data["has_data"] is True
        assert len(data["top_importers"]) == 3
        assert data["summary"]["total_files"] == 3
        assert data["summary"]["avg_imports_per_file"] == round((25 + 10 + 5) / 3, 1)
        assert data["summary"]["max_import_count"] == 25
        assert data["summary"]["total_dynamic_imports"] == 2
        assert data["summary"]["total_side_effect_imports"] == 1

    def test_heavy_importers_identified(self):
        """Test that files with >20 imports populate files_over_20."""
        section = ImportDependenciesSection()
        mock_fetcher = MagicMock()

        mock_fetcher.fetch.side_effect = [
            [
                {
                    "relative_path": "src/heavy.py",
                    "import_count": 30,
                    "unique_imports": 28,
                    "static_import_count": 30,
                    "dynamic_import_count": 0,
                    "side_effect_import_count": 0,
                },
                {
                    "relative_path": "src/light.py",
                    "import_count": 5,
                    "unique_imports": 5,
                    "static_import_count": 5,
                    "dynamic_import_count": 0,
                    "side_effect_import_count": 0,
                },
            ],
            [],  # no targets
        ]

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert data["has_heavy_importers"] is True
        assert len(data["files_over_20"]) == 1
        assert data["files_over_20"][0]["relative_path"] == "src/heavy.py"
        assert data["summary"]["files_over_20_imports"] == 1

    def test_dynamic_imports_detected(self):
        """Test that files with dynamic imports are flagged."""
        section = ImportDependenciesSection()
        mock_fetcher = MagicMock()

        mock_fetcher.fetch.side_effect = [
            [
                {
                    "relative_path": "src/loader.py",
                    "import_count": 10,
                    "unique_imports": 8,
                    "static_import_count": 7,
                    "dynamic_import_count": 3,
                    "side_effect_import_count": 0,
                },
                {
                    "relative_path": "src/static_only.py",
                    "import_count": 5,
                    "unique_imports": 5,
                    "static_import_count": 5,
                    "dynamic_import_count": 0,
                    "side_effect_import_count": 0,
                },
            ],
            [],  # no targets
        ]

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert data["has_dynamic_imports"] is True
        assert len(data["files_with_dynamic"]) == 1
        assert data["files_with_dynamic"][0]["relative_path"] == "src/loader.py"
        assert data["summary"]["total_dynamic_imports"] == 3

    def test_high_dependency_targets(self):
        """Test that targets with importing_files >= 5 are flagged."""
        section = ImportDependenciesSection()
        mock_fetcher = MagicMock()

        mock_fetcher.fetch.side_effect = [
            [],  # no importers
            [
                {
                    "imported_path": "src/shared/config.py",
                    "reference_count": 50,
                    "importing_files": 12,
                },
                {
                    "imported_path": "src/shared/utils.py",
                    "reference_count": 20,
                    "importing_files": 5,
                },
                {
                    "imported_path": "src/models/base.py",
                    "reference_count": 8,
                    "importing_files": 3,
                },
            ],
        ]

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert data["has_high_dependency_targets"] is True
        assert len(data["high_dependency_targets"]) == 2
        assert data["summary"]["most_depended_upon_count"] == 2


class TestCircularDependenciesFetchData:
    """Tests for CircularDependenciesSection.fetch_data with mocked fetcher."""

    def test_fetch_data_no_data(self):
        """Test fetch_data when fetcher raises Exception → fallback."""
        section = CircularDependenciesSection()
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.side_effect = Exception("No data")

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert data["has_data"] is False
        assert data["cycles"] == []
        assert data["summary"]["total_cycles"] == 0

    def test_fetch_data_with_cycles(self):
        """Test fetch_data with mixed severity cycles."""
        section = CircularDependenciesSection()
        mock_fetcher = MagicMock()

        mock_fetcher.fetch.return_value = [
            {
                "start_file": "src/a.py",
                "cycle_path": "src/a.py -> src/b.py -> src/a.py",
                "cycle_length": 2,
                "severity": "critical",
            },
            {
                "start_file": "src/c.py",
                "cycle_path": "src/c.py -> src/d.py -> src/e.py -> src/c.py",
                "cycle_length": 3,
                "severity": "high",
            },
            {
                "start_file": "src/f.py",
                "cycle_path": "src/f.py -> src/g.py -> src/h.py -> src/i.py -> src/f.py",
                "cycle_length": 4,
                "severity": "medium",
            },
        ]

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert data["has_data"] is True
        assert len(data["cycles"]) == 3
        assert data["severity_counts"]["critical"] == 1
        assert data["severity_counts"]["high"] == 1
        assert data["severity_counts"]["medium"] == 1
        assert data["severity_counts"]["low"] == 0
        assert data["summary"]["total_cycles"] == 3
        assert data["summary"]["files_involved"] == 3

    def test_critical_cycles_flagged(self):
        """Test that critical severity cycles set has_critical_cycles flag."""
        section = CircularDependenciesSection()
        mock_fetcher = MagicMock()

        mock_fetcher.fetch.return_value = [
            {
                "start_file": "src/a.py",
                "cycle_path": "src/a.py -> src/b.py -> src/a.py",
                "cycle_length": 2,
                "severity": "critical",
            },
        ]

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert data["has_critical_cycles"] is True
        assert data["summary"]["critical_count"] == 1

    def test_multi_cycle_files_detected(self):
        """Test that files appearing in multiple cycles are identified."""
        section = CircularDependenciesSection()
        mock_fetcher = MagicMock()

        mock_fetcher.fetch.return_value = [
            {
                "start_file": "src/hub.py",
                "cycle_path": "src/hub.py -> src/a.py -> src/hub.py",
                "cycle_length": 2,
                "severity": "critical",
            },
            {
                "start_file": "src/hub.py",
                "cycle_path": "src/hub.py -> src/b.py -> src/c.py -> src/hub.py",
                "cycle_length": 3,
                "severity": "high",
            },
            {
                "start_file": "src/other.py",
                "cycle_path": "src/other.py -> src/d.py -> src/other.py",
                "cycle_length": 2,
                "severity": "low",
            },
        ]

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert data["has_multi_cycle_files"] is True
        assert len(data["multi_cycle_files"]) == 1
        assert data["multi_cycle_files"][0][0] == "src/hub.py"
        assert data["multi_cycle_files"][0][1] == 2  # appears in 2 cycles
        assert data["summary"]["multi_cycle_file_count"] == 1

    def test_avg_cycle_length(self):
        """Test correct average cycle length calculation."""
        section = CircularDependenciesSection()
        mock_fetcher = MagicMock()

        mock_fetcher.fetch.return_value = [
            {
                "start_file": "src/a.py",
                "cycle_path": "src/a.py -> src/b.py -> src/a.py",
                "cycle_length": 2,
                "severity": "critical",
            },
            {
                "start_file": "src/c.py",
                "cycle_path": "src/c.py -> src/d.py -> src/e.py -> src/c.py",
                "cycle_length": 3,
                "severity": "high",
            },
            {
                "start_file": "src/f.py",
                "cycle_path": "src/f.py -> src/g.py -> src/h.py -> src/i.py -> src/j.py -> src/f.py",
                "cycle_length": 5,
                "severity": "low",
            },
        ]

        data = section.fetch_data(mock_fetcher, run_pk=1)

        # Average of [2, 3, 5] = 10/3 = 3.3333... → rounded to 3.3
        expected_avg = round((2 + 3 + 5) / 3, 1)
        assert data["summary"]["avg_cycle_length"] == expected_avg
