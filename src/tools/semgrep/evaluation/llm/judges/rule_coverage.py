"""Rule Coverage Judge - Evaluates breadth of smell detection rules."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


# DD Smell Categories (base categories always evaluated)
DD_CATEGORIES_BASE = [
    "size_complexity",
    "refactoring",
    "dependency",
    "error_handling",
    "async_concurrency",
    "resource_management",
    "nullability",
    "api_design",
    "dead_code",
    "security",  # SQL injection, SSRF, etc.
]

# Additional categories when multi-language rulesets are enabled
DD_CATEGORIES_MULTI_LANG = [
    "correctness",
    "best_practice",
    "performance",
]

# Additional categories when Elttam audit rules are enabled
DD_CATEGORIES_ELTTAM = [
    "entrypoint_discovery",
    "audit",
]

# Target languages (base)
TARGET_LANGUAGES_BASE = ["python", "javascript", "typescript", "csharp"]

# Additional languages when multi-language rulesets are enabled
TARGET_LANGUAGES_MULTI_LANG = ["java", "go"]

# Additional languages when Elttam rules are enabled (Rust support)
TARGET_LANGUAGES_ELTTAM = ["rust"]


def get_enabled_categories() -> list[str]:
    """Get the list of DD categories based on enabled rulesets."""
    categories = list(DD_CATEGORIES_BASE)
    if os.environ.get("SEMGREP_USE_MULTI_LANG", "0") == "1":
        categories.extend(DD_CATEGORIES_MULTI_LANG)
    if os.environ.get("SEMGREP_USE_ELTTAM", "0") == "1":
        categories.extend(DD_CATEGORIES_ELTTAM)
    return categories


def get_target_languages() -> list[str]:
    """Get the list of target languages based on enabled rulesets."""
    languages = list(TARGET_LANGUAGES_BASE)
    if os.environ.get("SEMGREP_USE_MULTI_LANG", "0") == "1":
        languages.extend(TARGET_LANGUAGES_MULTI_LANG)
    if os.environ.get("SEMGREP_USE_ELTTAM", "0") == "1":
        languages.extend(TARGET_LANGUAGES_ELTTAM)
    return languages


# For backwards compatibility, provide the full lists
DD_CATEGORIES = DD_CATEGORIES_BASE + DD_CATEGORIES_MULTI_LANG + DD_CATEGORIES_ELTTAM
TARGET_LANGUAGES = TARGET_LANGUAGES_BASE + TARGET_LANGUAGES_MULTI_LANG + TARGET_LANGUAGES_ELTTAM


class RuleCoverageJudge(BaseJudge):
    """Evaluates rule coverage breadth.

    Validates that:
    - All 7 target languages are covered
    - All 9 DD smell categories are addressed
    - Rule variety is sufficient
    - Critical smell types are detected
    """

    @property
    def dimension_name(self) -> str:
        return "rule_coverage"

    @property
    def weight(self) -> float:
        return 0.25  # 25% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and assess coverage."""
        # Get enabled categories and languages based on current configuration
        enabled_categories = get_enabled_categories()
        target_languages = get_target_languages()

        # Load from all output files
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        # Aggregate files from all repos
        all_files = []
        for repo_name, repo_analysis in all_results.items():
            for file_info in self.extract_files(repo_analysis):
                file_info["_repo"] = repo_name
                all_files.append(file_info)
        analysis = {"files": all_files}

        # Language coverage
        language_stats = {}
        for file_info in analysis.get("files", []):
            lang = file_info.get("language", "unknown")
            if lang not in language_stats:
                language_stats[lang] = {
                    "file_count": 0,
                    "smell_count": 0,
                    "categories_found": set(),
                    "sample_rules": set(),
                }
            language_stats[lang]["file_count"] += 1
            language_stats[lang]["smell_count"] += file_info.get("smell_count", 0)
            for smell in file_info.get("smells", []):
                cat = smell.get("dd_category", "")
                if cat:
                    language_stats[lang]["categories_found"].add(cat)
                language_stats[lang]["sample_rules"].add(smell.get("rule_id", "")[:60])

        # Convert sets to lists
        for lang in language_stats:
            language_stats[lang]["categories_found"] = list(language_stats[lang]["categories_found"])
            language_stats[lang]["sample_rules"] = list(language_stats[lang]["sample_rules"])[:10]

        # Category coverage (use enabled categories)
        category_stats = {cat: {"count": 0, "languages": set(), "rules": set()} for cat in enabled_categories}
        for file_info in analysis.get("files", []):
            lang = file_info.get("language", "unknown")
            for smell in file_info.get("smells", []):
                cat = smell.get("dd_category", "")
                if cat in category_stats:
                    category_stats[cat]["count"] += 1
                    category_stats[cat]["languages"].add(lang)
                    category_stats[cat]["rules"].add(smell.get("rule_id", "")[:60])

        # Convert sets to lists
        for cat in category_stats:
            category_stats[cat]["languages"] = list(category_stats[cat]["languages"])
            category_stats[cat]["rules"] = list(category_stats[cat]["rules"])[:5]

        # Unique rules used
        all_rules = set()
        for file_info in analysis.get("files", []):
            for smell in file_info.get("smells", []):
                all_rules.add(smell.get("rule_id", ""))

        # Coverage metrics (use dynamic targets)
        languages_covered = [l for l in target_languages if l in language_stats]
        languages_missing = [l for l in target_languages if l not in language_stats]

        categories_covered = [c for c in enabled_categories if category_stats[c]["count"] > 0]
        categories_missing = [c for c in enabled_categories if category_stats[c]["count"] == 0]

        summary = analysis.get("summary", {})

        # Configuration info
        config_info = {
            "multi_lang_enabled": os.environ.get("SEMGREP_USE_MULTI_LANG", "0") == "1",
            "elttam_enabled": os.environ.get("SEMGREP_USE_ELTTAM", "0") == "1",
            "target_languages": target_languages,
            "enabled_categories": enabled_categories,
        }

        evidence: dict[str, Any] = {
            "evaluation_mode": self.evaluation_mode,
            "language_stats": language_stats,
            "category_stats": category_stats,
            "languages_covered": languages_covered,
            "languages_missing": languages_missing,
            "categories_covered": categories_covered,
            "categories_missing": categories_missing,
            "total_unique_rules": len(all_rules),
            "sample_rules": list(all_rules)[:30],
            "total_smells": summary.get("total_smells", 0),
            "total_files": summary.get("total_files", 0),
            "language_coverage_pct": len(languages_covered) / len(target_languages) * 100 if target_languages else 0,
            "category_coverage_pct": len(categories_covered) / len(enabled_categories) * 100 if enabled_categories else 0,
            "configuration": config_info,
        }

        # Inject synthetic context for real-world evaluation
        if self.evaluation_mode == "real_world":
            synthetic_context = self.load_synthetic_evaluation_context()
            if synthetic_context:
                evidence["synthetic_baseline"] = synthetic_context
                evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                    synthetic_context
                )
            else:
                evidence["synthetic_baseline"] = "No synthetic baseline available"
                evidence["interpretation_guidance"] = (
                    "Evaluate based on ground truth comparison only"
                )
        else:
            evidence["synthetic_baseline"] = (
                "N/A - synthetic mode uses direct ground truth comparison"
            )
            evidence["interpretation_guidance"] = "Strict ground truth evaluation"

        return evidence

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Validate minimum coverage requirements.

        In real_world mode with a validated synthetic baseline, strict coverage
        requirements are relaxed because zero/low findings indicate a clean
        codebase, not tool failure (the tool was already validated via synthetic).
        """
        failures = []

        # In real_world mode with validated synthetic baseline, skip strict assertions
        # Zero findings in real-world is acceptable when synthetic validation passed
        if self.evaluation_mode == "real_world":
            synthetic_context = self.load_synthetic_evaluation_context()
            if synthetic_context and synthetic_context.get("decision") in ("STRONG_PASS", "PASS"):
                # Tool validated via synthetic - let LLM evaluate real-world coverage
                return True, []

        # Get enabled targets based on current configuration
        target_languages = get_target_languages()
        enabled_categories = get_enabled_categories()

        # Load from all output files
        all_results = self.load_all_analysis_results()
        if not all_results:
            failures.append(f"No analysis files found in {self.output_dir}")
            return False, failures

        # Aggregate files from all repos
        all_files = []
        for repo_name, repo_analysis in all_results.items():
            for file_info in self.extract_files(repo_analysis):
                all_files.append(file_info)
        analysis = {"files": all_files}

        # Check minimum language coverage (at least 3 languages or 50% of targets)
        languages_found = set()
        for file_info in analysis.get("files", []):
            lang = file_info.get("language", "")
            if lang in target_languages:
                languages_found.add(lang)

        min_languages = min(3, max(1, len(target_languages) // 2))
        if len(languages_found) < min_languages:
            failures.append(f"Only {len(languages_found)} languages covered, minimum {min_languages} required (of {len(target_languages)} targets)")

        # Check minimum category coverage (at least 3 categories or 30% of enabled)
        categories_found = set()
        for file_info in analysis.get("files", []):
            for smell in file_info.get("smells", []):
                cat = smell.get("dd_category", "")
                if cat in enabled_categories:
                    categories_found.add(cat)

        min_categories = min(3, max(1, len(enabled_categories) // 3))
        if len(categories_found) < min_categories:
            failures.append(f"Only {len(categories_found)} DD categories covered, minimum {min_categories} required (of {len(enabled_categories)} enabled)")

        # Check minimum rule variety (at least 5 unique rules)
        rules_found = set()
        for file_info in analysis.get("files", []):
            for smell in file_info.get("smells", []):
                rules_found.add(smell.get("rule_id", ""))

        if len(rules_found) < 5:
            failures.append(f"Only {len(rules_found)} unique rules used, minimum 5 required")

        return len(failures) == 0, failures

    def get_default_prompt(self) -> str:
        return '''# Rule Coverage Judge

You are evaluating the **breadth of rule coverage** in Semgrep's code smell detection.

## Evaluation Dimension
**Rule Coverage (25% weight)**: Does Semgrep cover all target languages and DD smell categories?

## Background
DD Platform targets 7 languages and 9 smell categories:

**Languages**: Python, JavaScript, TypeScript, C#, Java, Go, Rust

**DD Categories**:
1. size_complexity - Method/class size issues
2. refactoring - Code needing restructure
3. dependency - Coupling problems
4. error_handling - Exception handling issues
5. async_concurrency - Async/threading issues
6. resource_management - Resource leaks
7. nullability - Null handling problems
8. api_design - Interface issues
9. dead_code - Unreachable code
10. security - SQL injection, SSRF, hardcoded credentials

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | 100% language + category coverage, rich rule variety |
| 4 | 85%+ coverage, minor gaps in niche categories |
| 3 | 60%+ coverage, gaps in 2-3 categories/languages |
| 2 | 40%+ coverage, significant gaps |
| 1 | <40% coverage, critical gaps |

## Sub-Dimensions
1. **Language Coverage (40%)**: All 7 target languages detected
2. **Category Coverage (35%)**: All 9 DD categories addressed
3. **Rule Variety (25%)**: Sufficient rule diversity

## Evidence to Evaluate

### Language Statistics
```json
{{ language_stats }}
```

### Category Statistics
```json
{{ category_stats }}
```

### Coverage Summary
- Languages covered: {{ languages_covered }}
- Languages missing: {{ languages_missing }}
- Categories covered: {{ categories_covered }}
- Categories missing: {{ categories_missing }}
- Language coverage: {{ language_coverage_pct }}%
- Category coverage: {{ category_coverage_pct }}%

### Rule Variety
- Total unique rules: {{ total_unique_rules }}
- Sample rules: {{ sample_rules }}

### Overall Statistics
- Total smells: {{ total_smells }}
- Total files: {{ total_files }}

## Evaluation Questions
1. Are all 7 target languages represented with smells detected?
2. Are all 9 DD categories addressed?
3. Is there sufficient rule variety for each language?
4. Are critical categories (error_handling, security) well covered?

## Required Output Format
Respond with ONLY a JSON object:
```json
{
  "dimension": "rule_coverage",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of coverage assessment",
  "evidence_cited": ["specific languages, categories, and rules examined"],
  "recommendations": ["improvements for coverage"],
  "sub_scores": {
    "language_coverage": <1-5>,
    "category_coverage": <1-5>,
    "rule_variety": <1-5>
  }
}
```
'''
    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline.

        Delegates to base class implementation which:
        1. Collects evidence via collect_evidence()
        2. Builds prompt from template
        3. Invokes Claude for evaluation
        4. Parses response into JudgeResult
        """
        return super().evaluate()
