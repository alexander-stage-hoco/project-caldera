"""
File hotspots section - top files by complexity, size, and smells.
"""

from __future__ import annotations

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


# Remediation guidance constants
REMEDIATION_GUIDANCE = {
    "complexity": {
        "title": "High Complexity",
        "description": "Files with high cyclomatic complexity are difficult to test and maintain.",
        "actions": [
            "Extract complex logic into smaller, focused functions",
            "Reduce nesting depth by using early returns",
            "Consider using strategy or state patterns for complex branching",
            "Add unit tests before refactoring to ensure correctness",
        ],
    },
    "size": {
        "title": "Large File Size",
        "description": "Large files are harder to navigate and often indicate too many responsibilities.",
        "actions": [
            "Split into smaller, cohesive modules by responsibility",
            "Extract reusable utilities into separate files",
            "Consider if the file is doing too many things (Single Responsibility)",
            "Move related constants and types to dedicated files",
        ],
    },
    "smells": {
        "title": "Code Smells",
        "description": "Code smells indicate areas where code quality can be improved.",
        "actions": [
            "Address smells incrementally during regular development",
            "Use IDE refactoring tools to safely transform code",
            "Focus on smells that impact readability and maintainability first",
            "Consider pair programming for complex refactoring",
        ],
    },
    "compound": {
        "title": "Multiple Issues (Critical)",
        "description": "Files appearing in multiple categories require immediate attention.",
        "actions": [
            "Prioritize these files for refactoring in the next sprint",
            "Consider breaking the file into multiple smaller modules",
            "Add comprehensive tests before making changes",
            "Assign dedicated time for tech debt reduction",
        ],
    },
}


class FileHotspotsSection(BaseSection):
    """File-level hotspots section."""

    config = SectionConfig(
        name="file_hotspots",
        title="File Hotspots",
        description="Top files by cyclomatic complexity, lines of code, and code smells.",
        priority=2,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch file hotspot data.

        Returns data including:
        - complexity_hotspots: Top files by cyclomatic complexity
        - size_hotspots: Top files by LOC
        - smell_hotspots: Top files by code smell count
        - compound_hotspots: Files that appear in multiple categories
        - remediation_guidance: Guidance for each category
        """
        try:
            complexity_hotspots = fetcher.fetch(
                "file_hotspots",
                run_pk,
                order_by="complexity",
                limit=20,
            )
        except Exception:
            complexity_hotspots = []

        try:
            size_hotspots = fetcher.fetch(
                "file_hotspots",
                run_pk,
                order_by="loc",
                limit=20,
            )
        except Exception:
            size_hotspots = []

        try:
            smell_hotspots = fetcher.fetch(
                "file_hotspots",
                run_pk,
                order_by="smells",
                limit=20,
            )
        except Exception:
            smell_hotspots = []

        # Find compound hotspots (files in multiple categories)
        compound_hotspots = self._find_compound_hotspots(
            complexity_hotspots,
            size_hotspots,
            smell_hotspots,
        )

        # Add remediation suggestions to each file
        self._add_file_remediation(complexity_hotspots, "complexity")
        self._add_file_remediation(size_hotspots, "size")
        self._add_file_remediation(smell_hotspots, "smells")
        self._add_compound_remediation(compound_hotspots)

        return {
            "complexity_hotspots": complexity_hotspots,
            "size_hotspots": size_hotspots,
            "smell_hotspots": smell_hotspots,
            "compound_hotspots": compound_hotspots,
            "has_complexity": len(complexity_hotspots) > 0,
            "has_size": len(size_hotspots) > 0,
            "has_smells": len(smell_hotspots) > 0,
            "has_compound": len(compound_hotspots) > 0,
            "remediation_guidance": REMEDIATION_GUIDANCE,
        }

    def _add_file_remediation(
        self, hotspots: list[dict[str, Any]], category: str
    ) -> None:
        """Add remediation suggestion to each file based on its metrics."""
        for file in hotspots:
            file["remediation"] = self._get_file_remediation(file, category)

    def _get_file_remediation(
        self, file: dict[str, Any], category: str
    ) -> str:
        """Generate specific remediation suggestion for a file based on context."""
        language = file.get("language", "") or ""
        path = file.get("relative_path", "") or ""
        func_count = file.get("function_count", 0) or 0
        max_ccn = file.get("max_ccn", 0) or 0

        # Infer file role from path
        role = self._infer_file_role(path)

        if category == "complexity":
            ccn = file.get("complexity", 0) or 0

            # Determine complexity pattern
            if max_ccn > 0 and ccn > 0 and max_ccn < ccn:
                concentration = max_ccn / ccn
                if concentration > 0.4:
                    pattern = "concentrated in one function"
                else:
                    pattern = "distributed across functions"
            else:
                pattern = None

            # Language-specific advice
            if language in ("C#", "Java"):
                extract_advice = "extract into separate classes"
            elif language in ("Python", "Ruby"):
                extract_advice = "extract into modules or helper functions"
            elif language in ("JavaScript", "TypeScript"):
                extract_advice = "extract into separate modules"
            else:
                extract_advice = "extract into smaller units"

            if ccn > 50:
                if pattern == "concentrated in one function":
                    return f"Critical: Complexity {pattern}. Refactor the high-CCN function first, then {extract_advice}."
                elif func_count > 0 and func_count < 5:
                    return f"Critical: Few large functions ({func_count}). Split each function and {extract_advice}."
                else:
                    return f"Critical: High total complexity. {extract_advice.capitalize()} to target CCN<30 per file."
            elif ccn > 30:
                if role == "controller":
                    return "High priority: Move business logic out of controller into service classes."
                elif role == "model":
                    return "High priority: Extract validation and business rules into separate concerns."
                else:
                    return f"High priority: Break down into smaller units. {extract_advice.capitalize()}."
            elif ccn > 20:
                if pattern == "concentrated in one function":
                    return f"Consider splitting the complex function ({max_ccn} CCN) into smaller pieces."
                else:
                    return "Monitor complexity; consider refactoring if adding features."
            else:
                return "Complexity acceptable; maintain current patterns."

        elif category == "size":
            loc = file.get("loc_total", 0) or 0

            if loc > 2000:
                if role == "model":
                    return "Critical: Split model by domain. Extract nested classes or related entities."
                elif role == "controller":
                    return "Critical: Split controller by feature area. Move shared logic to services."
                elif role == "test":
                    return "Critical: Split tests by feature or scenario. Use test fixtures."
                else:
                    return f"Critical: {loc} lines. Identify 3-4 cohesive sections to extract as modules."
            elif loc > 1000:
                if func_count > 0 and loc / func_count > 100:
                    return f"High priority: Functions average {loc // func_count} lines. Break down large functions."
                else:
                    return "High priority: Group related functions and extract as separate modules."
            elif loc > 500:
                if role == "utility":
                    return "Consider grouping utilities by domain (string, date, validation)."
                else:
                    return "Moderate size; extract if adding significant new functionality."
            else:
                return "Size acceptable; maintain current structure."

        elif category == "smells":
            smells = file.get("smell_count", 0) or 0

            if smells > 20:
                if role == "test":
                    return "Critical: Refactor test structure. Extract common setup, use parameterized tests."
                elif language in ("Python", "JavaScript", "TypeScript"):
                    return "Critical: Run linter auto-fix first, then address remaining issues manually."
                else:
                    return "Critical: Address smells systematically. Start with IDE quick-fixes."
            elif smells > 10:
                if role == "model":
                    return "High priority: Focus on naming and encapsulation smells first."
                else:
                    return "High priority: Fix smells during code review. Target 2-3 per PR."
            elif smells > 5:
                return "Address smells opportunistically when modifying this file."
            else:
                return "Minor issues; fix during routine maintenance."

        return ""

    def _infer_file_role(self, path: str) -> str:
        """Infer the role of a file from its path."""
        path_lower = path.lower()

        if "test" in path_lower or "spec" in path_lower:
            return "test"
        elif "controller" in path_lower or "handler" in path_lower or "endpoint" in path_lower:
            return "controller"
        elif "model" in path_lower or "entity" in path_lower or "domain" in path_lower:
            return "model"
        elif "util" in path_lower or "helper" in path_lower or "common" in path_lower:
            return "utility"
        elif "service" in path_lower:
            return "service"
        else:
            return "general"

    def _add_compound_remediation(self, compound_hotspots: list[dict[str, Any]]) -> None:
        """Add remediation for compound hotspots."""
        for file in compound_hotspots:
            categories = file.get("categories", [])
            category_count = len(categories)

            if category_count >= 3:
                file["remediation"] = (
                    "CRITICAL: This file needs immediate refactoring attention. "
                    "Consider complete restructuring or rewrite."
                )
                file["priority"] = "critical"
            elif category_count == 2:
                if "complexity" in categories and "size" in categories:
                    file["remediation"] = (
                        "High priority: Large complex file - split by extracting "
                        "complex logic into separate modules."
                    )
                elif "complexity" in categories and "smells" in categories:
                    file["remediation"] = (
                        "High priority: Complex file with smells - simplify logic "
                        "and address code quality issues together."
                    )
                else:
                    file["remediation"] = (
                        "Medium priority: Address size and smell issues by splitting "
                        "and cleaning up the file."
                    )
                file["priority"] = "high"
            else:
                file["remediation"] = "Review and address as part of regular maintenance."
                file["priority"] = "medium"

    def _find_compound_hotspots(
        self,
        complexity: list[dict],
        size: list[dict],
        smells: list[dict],
    ) -> list[dict]:
        """Find files that appear in multiple hotspot categories."""
        # Get top 10 from each category
        complexity_paths = {h.get("relative_path") for h in complexity[:10]}
        size_paths = {h.get("relative_path") for h in size[:10]}
        smell_paths = {h.get("relative_path") for h in smells[:10]}

        # Find files in 2+ categories
        all_paths = complexity_paths | size_paths | smell_paths
        compound = []

        for path in all_paths:
            categories = []
            if path in complexity_paths:
                categories.append("complexity")
            if path in size_paths:
                categories.append("size")
            if path in smell_paths:
                categories.append("smells")

            if len(categories) >= 2:
                # Find the full data for this file
                file_data = None
                for h in complexity + size + smells:
                    if h.get("relative_path") == path:
                        file_data = h.copy()
                        break

                if file_data:
                    file_data["categories"] = categories
                    file_data["category_count"] = len(categories)
                    compound.append(file_data)

        # Sort by category count (more categories = higher priority)
        compound.sort(key=lambda x: x["category_count"], reverse=True)
        return compound

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "file_hotspots.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []

        # At least one category should have data
        if not (data.get("has_complexity") or data.get("has_size") or data.get("has_smells")):
            errors.append("No file hotspot data available")

        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "complexity_hotspots": [],
            "size_hotspots": [],
            "smell_hotspots": [],
            "compound_hotspots": [],
            "has_complexity": False,
            "has_size": False,
            "has_smells": False,
            "has_compound": False,
        }
