"""
Import dependencies section - File-level import pattern analysis.

Uses stg_file_imports_file_metrics and stg_lz_file_imports to identify
which files are the heaviest importers, the static/dynamic mix, and
which files are the most depended-upon (breaking change risk).
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class ImportDependenciesSection(BaseSection):
    """File-level import dependency analysis using symbol-scanner data."""

    config = SectionConfig(
        name="import_dependencies",
        title="Import Dependencies",
        description="File-level import pattern analysis identifying heavy importers, dynamic imports, and most-depended-upon files.",
        priority=6.8,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch import dependency data.

        Returns data including:
        - top_importers: Top 30 files by import count
        - most_imported_targets: Top 30 most-imported files
        - summary: Total files, avg imports, dynamic count, max imports
        - risk flags for template rendering
        """
        try:
            top_importers = fetcher.fetch("import_dependencies", run_pk, limit=30)
        except Exception:
            top_importers = []

        try:
            most_imported = fetcher.fetch("import_dependencies_targets", run_pk, limit=30)
        except Exception:
            most_imported = []

        # Calculate summary statistics
        total_files = len(top_importers)
        import_counts = []
        total_dynamic = 0
        total_side_effect = 0
        max_import_count = 0
        files_over_20 = []
        files_with_dynamic = []

        for f in top_importers:
            count = f.get("import_count", 0)
            import_counts.append(count)
            if count > max_import_count:
                max_import_count = count

            dynamic = f.get("dynamic_import_count", 0)
            side_effect = f.get("side_effect_import_count", 0)
            total_dynamic += dynamic
            total_side_effect += side_effect

            if count > 20:
                files_over_20.append(f)
            if dynamic > 0:
                files_with_dynamic.append(f)

        avg_imports = round(sum(import_counts) / len(import_counts), 1) if import_counts else 0

        # Identify most-depended-upon files (imported by many others)
        high_dependency_targets = [
            t for t in most_imported
            if t.get("importing_files", 0) >= 5
        ]

        summary = {
            "total_files": total_files,
            "avg_imports_per_file": avg_imports,
            "max_import_count": max_import_count,
            "total_dynamic_imports": total_dynamic,
            "total_side_effect_imports": total_side_effect,
            "files_over_20_imports": len(files_over_20),
            "files_with_dynamic_imports": len(files_with_dynamic),
            "most_depended_upon_count": len(high_dependency_targets),
        }

        return {
            "top_importers": top_importers,
            "most_imported_targets": most_imported,
            "high_dependency_targets": high_dependency_targets,
            "files_over_20": files_over_20,
            "files_with_dynamic": files_with_dynamic,
            "summary": summary,
            "has_data": len(top_importers) > 0 or len(most_imported) > 0,
            "has_heavy_importers": len(files_over_20) > 0,
            "has_dynamic_imports": total_dynamic > 0,
            "has_high_dependency_targets": len(high_dependency_targets) > 0,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "import_dependencies.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []
        if not data.get("has_data"):
            errors.append("No import dependency data available - symbol-scanner tool may not have run")
        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "top_importers": [],
            "most_imported_targets": [],
            "high_dependency_targets": [],
            "files_over_20": [],
            "files_with_dynamic": [],
            "summary": {
                "total_files": 0,
                "avg_imports_per_file": 0,
                "max_import_count": 0,
                "total_dynamic_imports": 0,
                "total_side_effect_imports": 0,
                "files_over_20_imports": 0,
                "files_with_dynamic_imports": 0,
                "most_depended_upon_count": 0,
            },
            "has_data": False,
            "has_heavy_importers": False,
            "has_dynamic_imports": False,
            "has_high_dependency_targets": False,
        }
