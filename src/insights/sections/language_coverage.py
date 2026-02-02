"""
Language coverage section showing distribution of languages in the codebase.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class LanguageCoverageSection(BaseSection):
    """Language distribution and coverage section."""

    config = SectionConfig(
        name="language_coverage",
        title="Language Coverage",
        description="Distribution of programming languages by files and lines of code.",
        priority=6,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch language coverage data.

        Returns data including:
        - languages: Language breakdown with file counts and LOC
        - primary_language: Most common language
        - total_files: Total file count
        - total_loc: Total lines of code
        - language_count: Number of distinct languages
        """
        try:
            languages = fetcher.fetch("language_coverage", run_pk)
        except Exception:
            languages = []

        # Calculate totals and percentages
        total_files = sum(lang.get("file_count", 0) for lang in languages)
        total_loc = sum(lang.get("loc", 0) for lang in languages)

        for lang in languages:
            file_count = lang.get("file_count", 0)
            loc = lang.get("loc", 0)
            lang["file_percent"] = (file_count / total_files * 100) if total_files > 0 else 0
            lang["loc_percent"] = (loc / total_loc * 100) if total_loc > 0 else 0

        # Identify primary language
        primary_language = languages[0]["language"] if languages else "Unknown"

        # Categorize languages
        categorized = self._categorize_languages(languages)

        return {
            "languages": languages,
            "primary_language": primary_language,
            "total_files": total_files,
            "total_loc": total_loc,
            "language_count": len(languages),
            "categories": categorized,
            "has_languages": len(languages) > 0,
        }

    def _categorize_languages(self, languages: list[dict]) -> dict[str, list[dict]]:
        """Categorize languages by type."""
        categories = {
            "compiled": [],
            "scripted": [],
            "markup": [],
            "config": [],
            "other": [],
        }

        compiled_langs = {"C#", "Java", "Go", "Rust", "C", "C++", "Kotlin", "Swift", "TypeScript"}
        scripted_langs = {"Python", "JavaScript", "Ruby", "PHP", "Perl", "Shell", "Bash", "PowerShell"}
        markup_langs = {"HTML", "XML", "Markdown", "CSS", "SCSS", "Less", "YAML", "JSON"}
        config_langs = {"TOML", "INI", "Properties", "Dockerfile", "Makefile"}

        for lang in languages:
            lang_name = lang.get("language", "")
            if lang_name in compiled_langs:
                categories["compiled"].append(lang)
            elif lang_name in scripted_langs:
                categories["scripted"].append(lang)
            elif lang_name in markup_langs:
                categories["markup"].append(lang)
            elif lang_name in config_langs:
                categories["config"].append(lang)
            else:
                categories["other"].append(lang)

        return categories

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "language_coverage.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []

        if not data.get("has_languages"):
            errors.append("No language data available")

        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "languages": [],
            "primary_language": "Unknown",
            "total_files": 0,
            "total_loc": 0,
            "language_count": 0,
            "categories": {
                "compiled": [],
                "scripted": [],
                "markup": [],
                "config": [],
                "other": [],
            },
            "has_languages": False,
        }
