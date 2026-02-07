"""
InsightsGenerator - Main entry point for generating Caldera Insights reports.
"""

from __future__ import annotations

import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from .data_fetcher import DataFetcher
from .formatters.base import BaseFormatter
from .formatters.html import HtmlFormatter
from .formatters.markdown import MarkdownFormatter
from .sections.base import BaseSection, SectionData
from .sections.executive_summary import ExecutiveSummarySection
from .sections.repo_health import RepoHealthSection
from .sections.file_hotspots import FileHotspotsSection
from .sections.directory_analysis import DirectoryAnalysisSection
from .sections.vulnerabilities import VulnerabilitiesSection
from .sections.cross_tool import CrossToolSection
from .sections.language_coverage import LanguageCoverageSection
from .sections.distribution_insights import DistributionInsightsSection
from .sections.roslyn_violations import RoslynViolationsSection
from .sections.iac_misconfigs import IacMisconfigsSection
from .sections.code_inequality import CodeInequalitySection
from .sections.module_health import ModuleHealthSection
from .sections.secrets import SecretsSection
from .sections.tool_readiness import ToolReadinessSection


class InsightsGenerator:
    """Main entry point for generating Caldera Insights reports."""

    # Available sections, ordered by priority
    SECTIONS: dict[str, type[BaseSection]] = {
        "tool_readiness": ToolReadinessSection,
        "executive_summary": ExecutiveSummarySection,
        "repo_health": RepoHealthSection,
        "file_hotspots": FileHotspotsSection,
        "directory_analysis": DirectoryAnalysisSection,
        "vulnerabilities": VulnerabilitiesSection,
        "secrets": SecretsSection,
        "cross_tool": CrossToolSection,
        "language_coverage": LanguageCoverageSection,
        "distribution_insights": DistributionInsightsSection,
        "roslyn_violations": RoslynViolationsSection,
        "iac_misconfigs": IacMisconfigsSection,
        "module_health": ModuleHealthSection,
        "code_inequality": CodeInequalitySection,
    }

    def __init__(
        self,
        db_path: Path,
        dbt_project_dir: Path | None = None,
        templates_dir: Path | None = None,
    ):
        """
        Initialize the InsightsGenerator.

        Args:
            db_path: Path to the DuckDB database file.
            dbt_project_dir: Optional path to dbt project directory.
            templates_dir: Optional custom templates directory.
        """
        self.db_path = Path(db_path)
        self.fetcher = DataFetcher(db_path, dbt_project_dir)
        self.templates_dir = templates_dir

        # Initialize section instances
        self.sections: dict[str, BaseSection] = {
            name: cls() for name, cls in self.SECTIONS.items()
        }

        # Initialize formatters
        self._formatters: dict[str, BaseFormatter] = {
            "html": HtmlFormatter(templates_dir),
            "md": MarkdownFormatter(templates_dir),
        }

    def generate(
        self,
        run_pk: int,
        format: Literal["html", "md"] = "html",
        sections: list[str] | None = None,
        output_path: Path | None = None,
        title: str | None = None,
        skip_validation: bool = False,
    ) -> str:
        """
        Generate a complete report.

        Args:
            run_pk: The collection run primary key.
            format: Output format ('html' or 'md').
            sections: Optional list of section names to include.
            output_path: Optional path to write the report to.
            title: Optional custom report title.
            skip_validation: Skip data validation checks (not recommended).

        Returns:
            The generated report as a string.
        """
        # Validate report data before generating
        if not skip_validation:
            data_warnings = self.validate_report_data(run_pk)
            for warning in data_warnings:
                warnings.warn(warning, UserWarning, stacklevel=2)

        # Get formatter
        formatter = self._formatters.get(format)
        if not formatter:
            raise ValueError(f"Unknown format: {format}. Available: {list(self._formatters.keys())}")

        # Determine which sections to render
        section_names = sections or list(self.sections.keys())

        # Validate section names
        invalid_sections = set(section_names) - set(self.sections.keys())
        if invalid_sections:
            raise ValueError(f"Unknown sections: {invalid_sections}. Available: {list(self.sections.keys())}")

        # Sort sections by priority
        section_names = sorted(
            section_names,
            key=lambda name: self.sections[name].config.priority,
        )

        # Render each section
        rendered_sections: list[SectionData] = []
        for name in section_names:
            section = self.sections[name]
            section_data = self._render_section(section, run_pk, formatter)
            rendered_sections.append(section_data)

        # Get run info for metadata
        run_info = self.fetcher.get_run_info(run_pk)
        repository = run_info.get("repository_name", "Unknown") if run_info else "Unknown"

        # Build metadata
        metadata = {
            "run_pk": run_pk,
            "generated_at": datetime.now().isoformat(),
            "repository": repository,
            "format": format,
            "sections_included": section_names,
        }

        # Generate report title
        report_title = title or f"Insights Report: {repository}"

        # Format the complete report
        report = formatter.format_report(
            title=report_title,
            sections=rendered_sections,
            metadata=metadata,
        )

        # Write to file if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)

        return report

    def _render_section(
        self,
        section: BaseSection,
        run_pk: int,
        formatter: BaseFormatter,
    ) -> SectionData:
        """
        Render a single section.

        Args:
            section: The section instance to render.
            run_pk: The collection run primary key.
            formatter: The formatter to use.

        Returns:
            SectionData containing the rendered content.
        """
        # Fetch data
        try:
            data = section.fetch_data(self.fetcher, run_pk)
        except Exception as e:
            # Use fallback data on error
            data = section.get_fallback_data()
            data["_error"] = str(e)

        # Validate data
        validation_errors = section.validate_data(data)
        if validation_errors:
            data["_validation_errors"] = validation_errors

        # Get appropriate template name
        if isinstance(formatter, HtmlFormatter):
            template_name = section.get_template_name()
        else:
            template_name = section.get_markdown_template_name()

        # Format the section
        content = formatter.format_section(
            section_name=section.config.name,
            template_name=template_name,
            data=data,
        )

        return SectionData(
            id=section.config.name,
            title=section.config.title,
            content=content,
            data=data,
        )

    def generate_by_collection(
        self,
        collection_run_id: str,
        format: Literal["html", "md"] = "html",
        sections: list[str] | None = None,
        output_path: Path | None = None,
        title: str | None = None,
    ) -> str:
        """
        Generate a report for a collection run.

        This method auto-resolves the correct tool run_pk (SCC anchor) for the
        collection run, avoiding the confusion of needing to know which tool's
        run_pk to use.

        Args:
            collection_run_id: The collection run ID (UUID).
            format: Output format ('html' or 'md').
            sections: Optional list of section names to include.
            output_path: Optional path to write the report to.
            title: Optional custom report title.

        Returns:
            The generated report as a string.
        """
        # Resolve collection_run_id to SCC's run_pk (anchor for unified metrics)
        run_pk = self.fetcher.get_scc_run_pk_for_collection(collection_run_id)

        return self.generate(
            run_pk=run_pk,
            format=format,
            sections=sections,
            output_path=output_path,
            title=title,
        )

    def generate_section(
        self,
        section_name: str,
        run_pk: int,
        format: Literal["html", "md"] = "html",
    ) -> str:
        """
        Generate a single section.

        Args:
            section_name: Name of the section to generate.
            run_pk: The collection run primary key.
            format: Output format ('html' or 'md').

        Returns:
            The generated section as a string.
        """
        if section_name not in self.sections:
            raise ValueError(f"Unknown section: {section_name}. Available: {list(self.sections.keys())}")

        formatter = self._formatters.get(format)
        if not formatter:
            raise ValueError(f"Unknown format: {format}")

        section = self.sections[section_name]
        section_data = self._render_section(section, run_pk, formatter)

        return section_data.content

    def list_sections(self) -> list[dict[str, Any]]:
        """
        List available sections with their metadata.

        Returns:
            List of section info dictionaries.
        """
        return [
            {
                "name": name,
                "title": section.config.title,
                "description": section.config.description,
                "priority": section.config.priority,
            }
            for name, section in sorted(
                self.sections.items(),
                key=lambda x: x[1].config.priority,
            )
        ]

    def validate_database(self) -> dict[str, Any]:
        """
        Validate that required Caldera database tables exist.

        Returns:
            Dictionary with validation results.
        """
        # Caldera dbt mart tables
        required_tables = [
            "unified_file_metrics",
            "stg_lz_tool_runs",
        ]

        optional_tables = [
            "unified_run_summary",
            "repo_health_summary",
            "stg_trivy_vulnerabilities",
            "stg_semgrep_file_metrics",
            "stg_lz_scc_file_metrics",
            "stg_lz_lizard_file_metrics",
            "stg_lz_layout_files",
            "rollup_scc_directory_counts_recursive",
            "rollup_lizard_directory_counts_recursive",
            "rollup_semgrep_directory_counts_recursive",
            "rollup_trivy_directory_counts_recursive",
            "stg_roslyn_file_metrics",
            "stg_trivy_iac_misconfigs",
            "stg_lz_gitleaks_secrets",
            "stg_gitleaks_secrets",
        ]

        results = {
            "valid": True,
            "missing_required": [],
            "missing_optional": [],
        }

        for table in required_tables:
            if not self.fetcher.table_exists(table):
                results["missing_required"].append(table)
                results["valid"] = False

        for table in optional_tables:
            if not self.fetcher.table_exists(table):
                results["missing_optional"].append(table)

        return results

    def validate_report_data(self, run_pk: int) -> list[str]:
        """
        Validate that the report data looks reasonable.

        Checks for suspicious patterns like:
        - Total files = 0 (likely wrong run_pk)
        - Total LOC = 0 (likely wrong run_pk)
        - .NET project with 0 Roslyn violations (may need investigation)

        Args:
            run_pk: The tool run primary key.

        Returns:
            List of warning messages. Empty list if all checks pass.
        """
        warnings_list: list[str] = []

        # Check file count from unified_file_metrics
        try:
            file_count_sql = """
            SELECT COUNT(*) as file_count, COALESCE(SUM(lines), 0) as total_loc
            FROM unified_file_metrics
            WHERE run_pk = {{ run_pk }}
            """
            result = self.fetcher.fetch_raw(file_count_sql, run_pk=run_pk)
            if result:
                file_count = result[0].get("file_count", 0)
                total_loc = result[0].get("total_loc", 0)

                if file_count == 0:
                    warnings_list.append(
                        f"No files found for run_pk={run_pk}. "
                        f"This may indicate the wrong run_pk was used. "
                        f"Use 'insights runs --db <path>' to verify the correct run_pk."
                    )
                elif total_loc == 0:
                    warnings_list.append(
                        f"Total LOC is 0 for run_pk={run_pk} despite {file_count} files. "
                        f"This may indicate a data issue."
                    )
        except Exception:
            pass  # Don't fail validation if query errors

        # Check if this is a .NET project with 0 Roslyn violations
        try:
            dotnet_check_sql = """
            SELECT
                COUNT(CASE WHEN language IN ('C#', 'csharp', 'cs') THEN 1 END) as csharp_files,
                COALESCE(SUM(CASE WHEN language IN ('C#', 'csharp', 'cs') THEN lines END), 0) as csharp_loc
            FROM unified_file_metrics
            WHERE run_pk = {{ run_pk }}
            """
            result = self.fetcher.fetch_raw(dotnet_check_sql, run_pk=run_pk)
            if result and result[0].get("csharp_files", 0) > 0:
                csharp_loc = result[0].get("csharp_loc", 0)

                # Check Roslyn violations
                if self.fetcher.table_exists("stg_roslyn_file_metrics"):
                    roslyn_sql = """
                    SELECT COUNT(*) as violation_count
                    FROM stg_roslyn_file_metrics
                    WHERE run_pk = {{ run_pk }}
                    """
                    roslyn_result = self.fetcher.fetch_raw(roslyn_sql, run_pk=run_pk)
                    if roslyn_result and roslyn_result[0].get("violation_count", 0) == 0:
                        if csharp_loc > 1000:  # Only warn for significant C# codebases
                            warnings_list.append(
                                f"Found {csharp_loc} LOC of C# code but 0 Roslyn violations. "
                                f"This may indicate Roslyn analyzers weren't run or produced no output."
                            )
        except Exception:
            pass  # Don't fail validation if query errors

        return warnings_list

    def get_tool_run_info(self, run_pk: int) -> dict[str, Any]:
        """
        Get information about the tool run and related collection.

        Useful for debugging run_pk selection issues.

        Args:
            run_pk: The tool run primary key.

        Returns:
            Dictionary with tool run and collection information.
        """
        sql = """
        SELECT
            t.run_pk,
            t.tool_name,
            t.collection_run_id,
            t.repo_id,
            t.branch,
            t.commit,
            t.timestamp,
            (SELECT COUNT(*) FROM lz_tool_runs WHERE collection_run_id = t.collection_run_id) as tools_in_collection
        FROM stg_lz_tool_runs t
        WHERE t.run_pk = {{ run_pk }}
        """
        results = self.fetcher.fetch_raw(sql, run_pk=run_pk)
        return results[0] if results else {}
