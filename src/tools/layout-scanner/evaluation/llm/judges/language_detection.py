"""Language Detection Judge for Layout Scanner evaluation.

Evaluates the accuracy of programming language detection for files.
"""

from __future__ import annotations

from typing import Any

from .base import BaseJudge


class LanguageDetectionJudge(BaseJudge):
    """Judge that evaluates language detection accuracy.

    Focuses on:
    - Extension-based language identification
    - Ambiguous file handling
    - Language distribution accuracy
    - Edge case handling (no extension, special files)
    """

    @property
    def dimension_name(self) -> str:
        return "language_detection"

    @property
    def weight(self) -> float:
        return 0.20  # 20% of total LLM score

    def get_default_prompt(self) -> str:
        """Return the default prompt template."""
        return """# Language Detection Evaluation

You are evaluating the Layout Scanner's programming language detection accuracy.

## Evaluation Dimension: Language Detection (Weight: 20%)

### What to Evaluate

1. **Extension-Based Detection** (40%)
   - Are common extensions correctly mapped? (.py -> Python, .ts -> TypeScript)
   - Are language names properly normalized? (python not PYTHON)
   - Are multi-language extensions handled? (.h -> C/C++)

2. **Special File Detection** (25%)
   - Are Makefiles detected as "makefile"?
   - Are Dockerfiles detected as "dockerfile"?
   - Are shell scripts detected (shebang parsing)?

3. **Edge Cases** (20%)
   - Are files without extensions handled gracefully?
   - Are binary files excluded from language detection?
   - Are vendor files still assigned languages?

4. **Language Distribution** (15%)
   - Is the per-directory language_distribution accurate?
   - Are totals consistent with file counts?

## Evidence

### File Language Samples
{{ language_samples }}

### Language Statistics
{{ language_statistics }}

### Ground Truth
{{ ground_truth }}

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | All common extensions correct, special files detected, edge cases handled |
| 4 | 95%+ correct, minor issues with ambiguous extensions |
| 3 | 90%+ correct, some special files missed |
| 2 | 80%+ correct, significant detection gaps |
| 1 | <80% correct, language detection unreliable |

## Required Output

Return a JSON object with this structure:
```json
{
    "dimension": "language_detection",
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "sub_scores": {
        "extension_detection": <1-5>,
        "special_files": <1-5>,
        "edge_cases": <1-5>,
        "distribution_accuracy": <1-5>
    },
    "evidence_cited": ["<specific examples from the output>"],
    "recommendations": ["<improvements if score < 5>"]
}
```
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence for language detection evaluation."""
        outputs = self._load_output_files()
        ground_truths = self._load_ground_truth_files()

        language_samples = []
        language_statistics: dict[str, int] = {}

        for output in outputs:
            repo = output.get("repository", "unknown")
            files = output.get("files", {})

            # Sample files with their language info
            for f in list(files.values())[:20]:
                language_samples.append(
                    {
                        "repository": repo,
                        "path": f.get("path"),
                        "extension": f.get("extension"),
                        "language": f.get("language"),
                        "classification": f.get("classification"),
                    }
                )

                # Aggregate language stats
                lang = f.get("language", "unknown")
                language_statistics[lang] = language_statistics.get(lang, 0) + 1

        # Collect ground truth language expectations
        gt_expectations = []
        for gt in ground_truths:
            expected = gt.get("expected", {})
            specific_files = expected.get("specific_files", {})

            file_expectations = []
            for path, info in specific_files.items():
                if "language" in info:
                    file_expectations.append(
                        {"path": path, "expected_language": info["language"]}
                    )

            if file_expectations:
                gt_expectations.append(
                    {
                        "repository": gt.get("repository"),
                        "files": file_expectations,
                    }
                )

        return {
            "language_samples": language_samples[:40],
            "language_statistics": language_statistics,
            "ground_truth": gt_expectations,
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions for language detection."""
        outputs = self._load_output_files()
        ground_truths = self._load_ground_truth_files()
        failures = []

        gt_by_repo = {gt.get("repository"): gt for gt in ground_truths}

        for output in outputs:
            repo = output.get("repository")
            gt = gt_by_repo.get(repo)

            if not gt:
                continue

            expected = gt.get("expected", {})
            specific_files = expected.get("specific_files", {})
            files = output.get("files", {})

            # Check specific file languages
            for path, expected_info in specific_files.items():
                expected_lang = expected_info.get("language")
                if not expected_lang:
                    continue

                # Find file by path
                actual_file = None
                for f in files.values():
                    if f.get("path") == path:
                        actual_file = f
                        break

                if actual_file is None:
                    # File not found - already checked by other judge
                    continue

                actual_lang = actual_file.get("language", "unknown")
                if actual_lang.lower() != expected_lang.lower():
                    failures.append(
                        f"{repo}: {path} detected as '{actual_lang}' "
                        f"but expected '{expected_lang}'"
                    )

        # Verify common extension mappings
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".md": "markdown",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
        }

        for output in outputs:
            repo = output.get("repository", "unknown")
            files = output.get("files", {})

            for f in files.values():
                ext = f.get("extension", "")
                lang = f.get("language", "unknown")

                if ext in extension_map:
                    expected = extension_map[ext]
                    if lang.lower() != expected.lower():
                        failures.append(
                            f"{repo}: {f.get('path')} has extension {ext} "
                            f"but language is '{lang}' (expected '{expected}')"
                        )

        return len(failures) == 0, failures[:20]
