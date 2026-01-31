"""
SCC Comparison Checks.

Compares layout scanner output with SCC (Succinct Code Counter) output
to validate language detection and file counts.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from . import CheckCategory, CheckResult, register_check


@dataclass
class LanguageComparison:
    """Comparison of language detection between layout scanner and SCC."""

    language: str
    layout_count: int
    scc_count: int
    count_difference: int
    in_layout: bool
    in_scc: bool

    @property
    def matches(self) -> bool:
        """Whether both tools detected this language with same count."""
        return self.in_layout and self.in_scc and self.count_difference == 0


@dataclass
class ComparisonResult:
    """Result of comparing layout scanner with SCC output."""

    layout_total_files: int
    scc_total_files: int
    total_file_difference: int
    layout_languages: Set[str] = field(default_factory=set)
    scc_languages: Set[str] = field(default_factory=set)
    common_languages: Set[str] = field(default_factory=set)
    layout_only_languages: Set[str] = field(default_factory=set)
    scc_only_languages: Set[str] = field(default_factory=set)
    language_comparisons: List[LanguageComparison] = field(default_factory=list)
    language_agreement_rate: float = 0.0
    count_agreement_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "layout_total_files": self.layout_total_files,
            "scc_total_files": self.scc_total_files,
            "total_file_difference": self.total_file_difference,
            "layout_languages": list(self.layout_languages),
            "scc_languages": list(self.scc_languages),
            "common_languages": list(self.common_languages),
            "layout_only_languages": list(self.layout_only_languages),
            "scc_only_languages": list(self.scc_only_languages),
            "language_agreement_rate": self.language_agreement_rate,
            "count_agreement_rate": self.count_agreement_rate,
            "language_comparisons": [
                {
                    "language": lc.language,
                    "layout_count": lc.layout_count,
                    "scc_count": lc.scc_count,
                    "count_difference": lc.count_difference,
                    "in_layout": lc.in_layout,
                    "in_scc": lc.in_scc,
                }
                for lc in self.language_comparisons
            ],
        }


# Language name normalization mapping
# Maps SCC language names to layout scanner language names
LANGUAGE_NORMALIZATION = {
    # Case variations
    "C#": "C#",
    "csharp": "C#",
    "CSharp": "C#",
    # JavaScript variants
    "JavaScript": "JavaScript",
    "javascript": "JavaScript",
    "js": "JavaScript",
    # TypeScript
    "TypeScript": "TypeScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    # Python
    "Python": "Python",
    "python": "Python",
    # Go
    "Go": "Go",
    "go": "Go",
    "Golang": "Go",
    # Rust
    "Rust": "Rust",
    "rust": "Rust",
    # Java
    "Java": "Java",
    "java": "Java",
    # Ruby
    "Ruby": "Ruby",
    "ruby": "Ruby",
    # C/C++
    "C": "C",
    "c": "C",
    "C++": "C++",
    "cpp": "C++",
    "Cpp": "C++",
    # Shell
    "Shell": "Shell",
    "Bash": "Shell",
    "bash": "Shell",
    "sh": "Shell",
    # PowerShell (case variations)
    "PowerShell": "PowerShell",
    "Powershell": "PowerShell",
    "powershell": "PowerShell",
    # Others
    "JSON": "JSON",
    "json": "JSON",
    "YAML": "YAML",
    "yaml": "YAML",
    "Markdown": "Markdown",
    "markdown": "Markdown",
    "HTML": "HTML",
    "html": "HTML",
    "CSS": "CSS",
    "css": "CSS",
    "SQL": "SQL",
    "sql": "SQL",
    "XML": "XML",
    "xml": "XML",
    "TOML": "TOML",
    "toml": "TOML",
    # SCC-specific build/project formats
    "MSBuild": "MSBuild",
    "msbuild": "MSBuild",
    "nuspec": "nuspec",
    "NuSpec": "nuspec",
    # Template languages
    "TemplateToolkit": "TemplateToolkit",
    # SCC special categories
    "License": "License",
    "Plain Text": "Plain Text",
    "plaintext": "Plain Text",
}


def normalize_language(lang: str) -> str:
    """Normalize a language name for comparison."""
    return LANGUAGE_NORMALIZATION.get(lang, lang)


def parse_scc_output(scc_output: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Parse SCC output into language -> file count mapping.

    Args:
        scc_output: List of SCC language entries.

    Returns:
        Dictionary mapping normalized language names to file counts.

    Example SCC entry:
        {
            "Name": "Python",
            "Bytes": 26520,
            "Lines": 892,
            "Code": 765,
            "Comment": 58,
            "Blank": 69,
            "Complexity": 56,
            "Count": 9
        }
    """
    language_counts: Dict[str, int] = {}

    for entry in scc_output:
        lang = entry.get("Name", "")
        count = entry.get("Count", 0)

        if not lang or count == 0:
            continue

        normalized = normalize_language(lang)

        # Accumulate counts for languages that normalize to the same name
        language_counts[normalized] = language_counts.get(normalized, 0) + count

    return language_counts


def parse_layout_output(layout_output: Dict[str, Any]) -> Dict[str, int]:
    """
    Parse layout scanner output into language -> file count mapping.

    Args:
        layout_output: Layout scanner output dictionary.

    Returns:
        Dictionary mapping normalized language names to file counts.
    """
    # Get by_language from statistics section
    stats = layout_output.get("statistics", {})
    by_language = stats.get("by_language", {})

    language_counts: Dict[str, int] = {}

    for lang, count in by_language.items():
        if not lang or count == 0:
            continue

        # Skip "unknown" language
        if lang.lower() == "unknown":
            continue

        normalized = normalize_language(lang)
        language_counts[normalized] = language_counts.get(normalized, 0) + count

    return language_counts


def compare_with_scc(
    layout_output: Dict[str, Any],
    scc_output: List[Dict[str, Any]],
) -> ComparisonResult:
    """
    Compare layout scanner output with SCC output.

    Compares:
    - Total file counts
    - Language detection (which languages detected by each tool)
    - File counts per language

    Args:
        layout_output: Layout scanner output dictionary.
        scc_output: SCC output list (array of language entries).

    Returns:
        ComparisonResult with detailed comparison metrics.
    """
    # Parse outputs
    layout_langs = parse_layout_output(layout_output)
    scc_langs = parse_scc_output(scc_output)

    # Get total file counts
    layout_stats = layout_output.get("statistics", {})
    layout_total = layout_stats.get("total_files", 0)
    scc_total = sum(scc_langs.values())

    # Compute language sets
    layout_lang_set = set(layout_langs.keys())
    scc_lang_set = set(scc_langs.keys())
    common_langs = layout_lang_set & scc_lang_set
    layout_only = layout_lang_set - scc_lang_set
    scc_only = scc_lang_set - layout_lang_set

    # Build language comparisons
    all_langs = layout_lang_set | scc_lang_set
    comparisons: List[LanguageComparison] = []

    for lang in sorted(all_langs):
        layout_count = layout_langs.get(lang, 0)
        scc_count = scc_langs.get(lang, 0)

        comparisons.append(LanguageComparison(
            language=lang,
            layout_count=layout_count,
            scc_count=scc_count,
            count_difference=layout_count - scc_count,
            in_layout=lang in layout_lang_set,
            in_scc=lang in scc_lang_set,
        ))

    # Compute agreement rates
    total_langs = len(all_langs)
    language_agreement_rate = len(common_langs) / total_langs if total_langs > 0 else 0.0

    # Count agreement: among common languages, what % have exact counts
    exact_matches = sum(1 for c in comparisons if c.matches)
    count_agreement_rate = exact_matches / len(common_langs) if common_langs else 0.0

    return ComparisonResult(
        layout_total_files=layout_total,
        scc_total_files=scc_total,
        total_file_difference=layout_total - scc_total,
        layout_languages=layout_lang_set,
        scc_languages=scc_lang_set,
        common_languages=common_langs,
        layout_only_languages=layout_only,
        scc_only_languages=scc_only,
        language_comparisons=comparisons,
        language_agreement_rate=round(language_agreement_rate, 4),
        count_agreement_rate=round(count_agreement_rate, 4),
    )


def run_scc_comparison_checks(
    layout_output: Dict[str, Any],
    scc_output: List[Dict[str, Any]],
    tolerance_percent: float = 0.1,
) -> List[CheckResult]:
    """
    Run all SCC comparison checks.

    Args:
        layout_output: Layout scanner output dictionary.
        scc_output: SCC output list.
        tolerance_percent: Acceptable percentage difference for counts.

    Returns:
        List of check results.
    """
    checks = []

    comparison = compare_with_scc(layout_output, scc_output)

    checks.append(check_total_file_count(comparison, tolerance_percent))
    checks.append(check_language_detection_coverage(comparison))
    checks.append(check_language_count_accuracy(comparison, tolerance_percent))
    checks.append(check_major_language_agreement(comparison))

    return checks


@register_check("SCC-1")
def check_total_file_count(
    comparison: ComparisonResult,
    tolerance_percent: float = 0.1,
) -> CheckResult:
    """
    SCC-1: Total file count is within tolerance of SCC count.

    Note: Layout scanner may count more files than SCC because SCC only
    counts files with recognized languages, while layout scanner counts
    all files including config, generated, etc.
    """
    layout_total = comparison.layout_total_files
    scc_total = comparison.scc_total_files
    diff = comparison.total_file_difference

    # Calculate percentage difference relative to larger count
    max_count = max(layout_total, scc_total, 1)
    diff_percent = abs(diff) / max_count

    # Layout scanner counting more is expected; SCC counting more is concerning
    if scc_total > layout_total:
        return CheckResult(
            check_id="SCC-1",
            name="Total File Count vs SCC",
            category=CheckCategory.ACCURACY,
            passed=False,
            score=0.5,
            message=f"SCC found more files than layout scanner: SCC={scc_total}, Layout={layout_total}",
            evidence={
                "layout_total": layout_total,
                "scc_total": scc_total,
                "difference": diff,
                "difference_percent": round(diff_percent * 100, 2),
            },
        )

    # If layout counts more, that's expected (SCC only counts code files)
    return CheckResult(
        check_id="SCC-1",
        name="Total File Count vs SCC",
        category=CheckCategory.ACCURACY,
        passed=True,
        score=1.0,
        message=f"File count consistent: Layout={layout_total}, SCC={scc_total} (Layout includes non-code files)",
        evidence={
            "layout_total": layout_total,
            "scc_total": scc_total,
            "difference": diff,
            "difference_percent": round(diff_percent * 100, 2),
        },
    )


@register_check("SCC-2")
def check_language_detection_coverage(comparison: ComparisonResult) -> CheckResult:
    """
    SCC-2: Layout scanner detects all languages that SCC detects.

    Layout scanner should detect at least all languages SCC detects.
    It's okay if layout scanner detects additional languages.
    """
    scc_only = comparison.scc_only_languages
    common = comparison.common_languages

    if scc_only:
        # Calculate what percentage of SCC languages we're missing
        scc_total = len(comparison.scc_languages)
        coverage = len(common) / scc_total if scc_total > 0 else 0

        return CheckResult(
            check_id="SCC-2",
            name="Language Detection Coverage",
            category=CheckCategory.ACCURACY,
            passed=False,
            score=coverage,
            message=f"Missing {len(scc_only)} languages detected by SCC: {sorted(scc_only)}",
            evidence={
                "missing_languages": sorted(scc_only),
                "common_languages": sorted(common),
                "coverage_percent": round(coverage * 100, 2),
            },
        )

    return CheckResult(
        check_id="SCC-2",
        name="Language Detection Coverage",
        category=CheckCategory.ACCURACY,
        passed=True,
        score=1.0,
        message=f"All {len(common)} SCC languages detected by layout scanner",
        evidence={
            "common_languages": sorted(common),
            "layout_only_languages": sorted(comparison.layout_only_languages),
        },
    )


@register_check("SCC-3")
def check_language_count_accuracy(
    comparison: ComparisonResult,
    tolerance_percent: float = 0.1,
) -> CheckResult:
    """
    SCC-3: File counts per language are within tolerance.

    For languages detected by both tools, counts should be similar.
    """
    if not comparison.common_languages:
        return CheckResult(
            check_id="SCC-3",
            name="Language Count Accuracy",
            category=CheckCategory.ACCURACY,
            passed=False,
            score=0.0,
            message="No common languages to compare",
        )

    discrepancies: List[Dict[str, Any]] = []
    accurate_count = 0

    for lc in comparison.language_comparisons:
        if not lc.in_layout or not lc.in_scc:
            continue

        max_count = max(lc.layout_count, lc.scc_count, 1)
        diff_percent = abs(lc.count_difference) / max_count

        if diff_percent > tolerance_percent:
            discrepancies.append({
                "language": lc.language,
                "layout_count": lc.layout_count,
                "scc_count": lc.scc_count,
                "difference": lc.count_difference,
                "difference_percent": round(diff_percent * 100, 2),
            })
        else:
            accurate_count += 1

    total_common = len(comparison.common_languages)
    accuracy_rate = accurate_count / total_common if total_common > 0 else 0

    if discrepancies:
        return CheckResult(
            check_id="SCC-3",
            name="Language Count Accuracy",
            category=CheckCategory.ACCURACY,
            passed=accuracy_rate >= 0.8,  # 80% of languages should match
            score=accuracy_rate,
            message=f"{len(discrepancies)}/{total_common} languages have count discrepancies beyond {tolerance_percent*100}%",
            evidence={
                "discrepancies": discrepancies,
                "accurate_count": accurate_count,
                "accuracy_rate": round(accuracy_rate * 100, 2),
            },
        )

    return CheckResult(
        check_id="SCC-3",
        name="Language Count Accuracy",
        category=CheckCategory.ACCURACY,
        passed=True,
        score=1.0,
        message=f"All {total_common} common languages have accurate file counts",
        evidence={
            "accurate_count": accurate_count,
            "tolerance_percent": tolerance_percent * 100,
        },
    )


@register_check("SCC-4")
def check_major_language_agreement(comparison: ComparisonResult) -> CheckResult:
    """
    SCC-4: Major languages (>5% of files) have exact count match.

    Languages that represent a significant portion of the codebase
    should have exact agreement between tools.
    """
    if not comparison.scc_total_files:
        return CheckResult(
            check_id="SCC-4",
            name="Major Language Agreement",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0,
            message="No files counted by SCC",
        )

    major_threshold = 0.05  # 5% of total files
    min_files = max(comparison.scc_total_files * major_threshold, 5)

    major_languages: List[LanguageComparison] = []
    for lc in comparison.language_comparisons:
        if lc.scc_count >= min_files:
            major_languages.append(lc)

    if not major_languages:
        return CheckResult(
            check_id="SCC-4",
            name="Major Language Agreement",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0,
            message=f"No languages exceed threshold of {int(min_files)} files",
        )

    mismatches: List[Dict[str, Any]] = []
    matches = 0

    for lc in major_languages:
        if lc.matches:
            matches += 1
        else:
            mismatches.append({
                "language": lc.language,
                "layout_count": lc.layout_count,
                "scc_count": lc.scc_count,
                "difference": lc.count_difference,
            })

    total_major = len(major_languages)
    agreement_rate = matches / total_major if total_major > 0 else 0

    if mismatches:
        return CheckResult(
            check_id="SCC-4",
            name="Major Language Agreement",
            category=CheckCategory.ACCURACY,
            passed=agreement_rate >= 0.8,
            score=agreement_rate,
            message=f"{len(mismatches)}/{total_major} major languages have count mismatches",
            evidence={
                "mismatches": mismatches,
                "matches": matches,
                "agreement_rate": round(agreement_rate * 100, 2),
            },
        )

    return CheckResult(
        check_id="SCC-4",
        name="Major Language Agreement",
        category=CheckCategory.ACCURACY,
        passed=True,
        score=1.0,
        message=f"All {total_major} major languages have exact count agreement",
        evidence={
            "major_languages": [lc.language for lc in major_languages],
        },
    )


__all__ = [
    "ComparisonResult",
    "LanguageComparison",
    "compare_with_scc",
    "parse_scc_output",
    "parse_layout_output",
    "normalize_language",
    "run_scc_comparison_checks",
    "check_total_file_count",
    "check_language_detection_coverage",
    "check_language_count_accuracy",
    "check_major_language_agreement",
    "LANGUAGE_NORMALIZATION",
]
