#!/usr/bin/env python3
"""
PMD CPD Analyzer

Runs PMD CPD (Copy/Paste Detector) on a repository and normalizes output to JSON.
Supports token-based and semantic (--ignore-identifiers, --ignore-literals) modes.

Usage:
    python analyze.py /path/to/repo --output-dir outputs/run-id --pmd-home .pmd/pmd-bin-7.0.0
    python analyze.py /path/to/repo --output-dir outputs/run-id --pmd-home .pmd/pmd-bin-7.0.0 --ignore-identifiers
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

# Add src directory to path for common imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from shared.path_utils import normalize_file_path


# Language mapping: CPD language names -> file extensions
CPD_LANGUAGES = {
    "python": [".py"],
    "ecmascript": [".js", ".jsx", ".mjs"],
    "typescript": [".ts", ".tsx"],
    "cs": [".cs"],
    "java": [".java"],
    "go": [".go"],
    "rust": [".rs"],
    "cpp": [".cpp", ".cc", ".cxx", ".c", ".h", ".hpp"],
    "kotlin": [".kt", ".kts"],
    "swift": [".swift"],
    "ruby": [".rb"],
    "php": [".php"],
    "scala": [".scala"],
}

# Reverse mapping: extension -> CPD language
EXT_TO_LANGUAGE = {}
for lang, exts in CPD_LANGUAGES.items():
    for ext in exts:
        EXT_TO_LANGUAGE[ext] = lang


@dataclass
class DuplicationOccurrence:
    """A single occurrence of duplicated code."""

    file: str
    line_start: int
    line_end: int
    column_start: int = 0
    column_end: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "column_start": self.column_start,
            "column_end": self.column_end,
        }


@dataclass
class Duplication:
    """A detected code duplication (clone)."""

    clone_id: str
    lines: int
    tokens: int
    occurrences: list[DuplicationOccurrence] = field(default_factory=list)
    code_fragment: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "clone_id": self.clone_id,
            "lines": self.lines,
            "tokens": self.tokens,
            "occurrences": [o.to_dict() for o in self.occurrences],
            "code_fragment": self.code_fragment[:500] if self.code_fragment else "",
        }

    @property
    def is_cross_file(self) -> bool:
        """Check if this duplication spans multiple files."""
        files = {o.file for o in self.occurrences}
        return len(files) > 1


@dataclass
class FileMetrics:
    """Per-file duplication metrics."""

    path: str
    total_lines: int = 0
    duplicate_lines: int = 0
    duplicate_blocks: int = 0
    duplication_percentage: float = 0.0
    language: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "total_lines": self.total_lines,
            "duplicate_lines": self.duplicate_lines,
            "duplicate_blocks": self.duplicate_blocks,
            "duplication_percentage": round(self.duplication_percentage, 2),
            "language": self.language,
        }


@dataclass
class AnalysisResult:
    """Complete CPD analysis result."""

    # Caldera metadata fields
    run_id: str
    repo_id: str
    branch: str
    commit: str
    timestamp: str
    tool_version: str
    # Analysis configuration
    min_tokens: int
    ignore_identifiers: bool
    ignore_literals: bool
    elapsed_seconds: float
    # Results
    summary: dict[str, Any]
    files: list[FileMetrics]
    duplications: list[Duplication]
    statistics: dict[str, Any]
    errors: list[str] = field(default_factory=list)

    def to_caldera_envelope(self) -> dict[str, Any]:
        """Convert to Caldera envelope format."""
        return {
            "metadata": {
                "tool_name": "pmd-cpd",
                "tool_version": self.tool_version,
                "run_id": self.run_id,
                "repo_id": self.repo_id,
                "branch": self.branch,
                "commit": self.commit,
                "timestamp": self.timestamp,
                "schema_version": "1.0.0",
            },
            "data": {
                "tool": "pmd-cpd",
                "config": {
                    "min_tokens": self.min_tokens,
                    "ignore_identifiers": self.ignore_identifiers,
                    "ignore_literals": self.ignore_literals,
                },
                "elapsed_seconds": self.elapsed_seconds,
                "summary": self.summary,
                "files": [f.to_dict() for f in self.files],
                "duplications": [d.to_dict() for d in self.duplications],
                "statistics": self.statistics,
                "errors": self.errors,
            },
        }


def detect_language(file_path: str) -> str:
    """Detect language from file extension."""
    ext = Path(file_path).suffix.lower()
    return EXT_TO_LANGUAGE.get(ext, "unknown")


def count_lines(file_path: Path) -> int:
    """Count lines in a file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def generate_clone_id(index: int) -> str:
    """Generate a unique clone ID."""
    return f"CPD-{index:04d}"


def run_cpd(
    repo_path: Path,
    pmd_home: Path,
    language: str,
    min_tokens: int = 50,
    ignore_identifiers: bool = False,
    ignore_literals: bool = False,
) -> tuple[str, str]:
    """Run PMD CPD for a specific language and return XML output."""
    cpd_cmd = [
        str(pmd_home / "bin" / "pmd"),
        "cpd",
        "--format",
        "xml",
        "--minimum-tokens",
        str(min_tokens),
        "--language",
        language,
        "--dir",
        str(repo_path),
    ]

    if ignore_identifiers:
        cpd_cmd.append("--ignore-identifiers")
    if ignore_literals:
        cpd_cmd.append("--ignore-literals")

    try:
        env = os.environ.copy()
        java_path = find_java()
        if java_path:
            env["PATH"] = f"{Path(java_path).parent}:{env.get('PATH', '')}"

        result = subprocess.run(
            cpd_cmd,
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )
        if result.stdout.strip():
            return result.stdout, ""
        if result.returncode != 0:
            return "", result.stderr or result.stdout
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return "", f"CPD timed out for language {language}"
    except Exception as e:
        return "", str(e)


def parse_cpd_xml(
    xml_content: str, repo_root: Path, start_id: int = 0
) -> list[Duplication]:
    """Parse CPD XML output into Duplication objects."""
    duplications = []

    if not xml_content.strip():
        return duplications

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        return duplications

    for idx, dup_elem in enumerate(root.findall(".//duplication")):
        lines = int(dup_elem.get("lines", 0))
        tokens = int(dup_elem.get("tokens", 0))

        occurrences = []
        for file_elem in dup_elem.findall("file"):
            raw_path = file_elem.get("path", "")
            normalized_path = normalize_file_path(raw_path, repo_root)
            line = int(file_elem.get("line", 0))
            column = int(file_elem.get("column", 0))
            end_line = int(file_elem.get("endline", line + lines - 1))
            end_column = int(file_elem.get("endcolumn", 0))

            occurrences.append(
                DuplicationOccurrence(
                    file=normalized_path,
                    line_start=line,
                    line_end=end_line,
                    column_start=column,
                    column_end=end_column,
                )
            )

        # Extract code fragment
        code_elem = dup_elem.find("codefragment")
        code_fragment = code_elem.text if code_elem is not None and code_elem.text else ""

        duplications.append(
            Duplication(
                clone_id=generate_clone_id(start_id + idx),
                lines=lines,
                tokens=tokens,
                occurrences=occurrences,
                code_fragment=code_fragment,
            )
        )

    return duplications


def collect_files(repo_path: Path) -> dict[str, list[Path]]:
    """Collect all source files by language."""
    files_by_lang: dict[str, list[Path]] = {}

    for file_path in repo_path.rglob("*"):
        if not file_path.is_file():
            continue

        # Skip hidden directories and common non-source directories
        parts = file_path.parts
        if any(
            p.startswith(".")
            or p in ("node_modules", "vendor", "target", "bin", "obj", "__pycache__")
            for p in parts
        ):
            continue

        ext = file_path.suffix.lower()
        if ext in EXT_TO_LANGUAGE:
            lang = EXT_TO_LANGUAGE[ext]
            if lang not in files_by_lang:
                files_by_lang[lang] = []
            files_by_lang[lang].append(file_path)

    return files_by_lang


def calculate_file_metrics(
    repo_path: Path,
    duplications: list[Duplication],
    files_by_lang: dict[str, list[Path]],
) -> list[FileMetrics]:
    """Calculate per-file duplication metrics."""
    # Initialize file metrics
    file_metrics: dict[str, FileMetrics] = {}
    duplicate_line_map: dict[str, set[int]] = {}

    for lang, files in files_by_lang.items():
        for file_path in files:
            rel_path = normalize_file_path(str(file_path), repo_path)
            total_lines = count_lines(file_path)
            file_metrics[rel_path] = FileMetrics(
                path=rel_path,
                total_lines=total_lines,
                language=lang,
            )
            duplicate_line_map[rel_path] = set()

    # Calculate duplication for each file
    for dup in duplications:
        for occ in dup.occurrences:
            if occ.file in file_metrics:
                fm = file_metrics[occ.file]
                fm.duplicate_blocks += 1
                if occ.line_start and occ.line_end and occ.line_end >= occ.line_start:
                    duplicate_line_map[occ.file].update(
                        range(occ.line_start, occ.line_end + 1)
                    )

    # Calculate percentages
    for fm in file_metrics.values():
        fm.duplicate_lines = len(duplicate_line_map.get(fm.path, set()))
        if fm.total_lines > 0:
            # Cap at 100% since overlapping clones can exceed total lines
            fm.duplication_percentage = min(
                100.0, (fm.duplicate_lines / fm.total_lines) * 100
            )

    return sorted(file_metrics.values(), key=lambda x: -x.duplication_percentage)


def calculate_statistics(duplications: list[Duplication]) -> dict[str, Any]:
    """Calculate overall statistics."""
    by_language: dict[str, dict[str, int]] = {}
    cross_file_clones = 0
    total_tokens = 0
    total_lines = 0

    for dup in duplications:
        if dup.is_cross_file:
            cross_file_clones += 1

        total_tokens += dup.tokens
        total_lines += dup.lines

        # Count by language
        for occ in dup.occurrences:
            lang = detect_language(occ.file)
            if lang not in by_language:
                by_language[lang] = {"clone_count": 0, "total_lines": 0}
            by_language[lang]["clone_count"] += 1
            by_language[lang]["total_lines"] += occ.line_end - occ.line_start + 1

    return {
        "cross_file_clones": cross_file_clones,
        "total_tokens": total_tokens,
        "total_duplicate_lines": total_lines,
        "by_language": by_language,
    }


def analyze(
    repo_path: str,
    pmd_home: str,
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
    min_tokens: int = 50,
    ignore_identifiers: bool = False,
    ignore_literals: bool = False,
) -> AnalysisResult:
    """Run complete CPD analysis on a repository."""
    repo_path_obj = Path(repo_path).resolve()
    pmd_home_obj = Path(pmd_home).resolve()
    timestamp = datetime.now(timezone.utc).isoformat()

    start_time = time.time()
    errors: list[str] = []

    if not find_java():
        return AnalysisResult(
            run_id=run_id,
            repo_id=repo_id,
            branch=branch,
            commit=commit,
            timestamp=timestamp,
            tool_version="7.0.0",
            min_tokens=min_tokens,
            ignore_identifiers=ignore_identifiers,
            ignore_literals=ignore_literals,
            elapsed_seconds=0.0,
            summary={
                "total_files": 0,
                "total_clones": 0,
                "duplication_percentage": 0.0,
            },
            files=[],
            duplications=[],
            statistics={},
            errors=["Java runtime not found in PATH. Install Java 11+ and retry."],
        )

    # Collect source files
    files_by_lang = collect_files(repo_path_obj)

    if not files_by_lang:
        return AnalysisResult(
            run_id=run_id,
            repo_id=repo_id,
            branch=branch,
            commit=commit,
            timestamp=timestamp,
            tool_version="7.0.0",
            min_tokens=min_tokens,
            ignore_identifiers=ignore_identifiers,
            ignore_literals=ignore_literals,
            elapsed_seconds=0.0,
            summary={
                "total_files": 0,
                "total_clones": 0,
                "duplication_percentage": 0.0,
            },
            files=[],
            duplications=[],
            statistics={},
            errors=["No source files found"],
        )

    # Run CPD for each language
    all_duplications: list[Duplication] = []

    for lang in files_by_lang:
        xml_output, stderr = run_cpd(
            repo_path_obj,
            pmd_home_obj,
            lang,
            min_tokens,
            ignore_identifiers,
            ignore_literals,
        )

        if stderr:
            errors.append(f"CPD error for {lang}: {stderr.strip()[:200]}")

        dups = parse_cpd_xml(xml_output, repo_path_obj, len(all_duplications))
        all_duplications.extend(dups)

    # Calculate metrics
    file_metrics = calculate_file_metrics(repo_path_obj, all_duplications, files_by_lang)
    statistics = calculate_statistics(all_duplications)

    # Calculate overall duplication percentage
    total_lines = sum(fm.total_lines for fm in file_metrics)
    total_dup_lines = sum(fm.duplicate_lines for fm in file_metrics)
    overall_dup_pct = (total_dup_lines / total_lines * 100) if total_lines > 0 else 0.0

    elapsed = time.time() - start_time

    return AnalysisResult(
        run_id=run_id,
        repo_id=repo_id,
        branch=branch,
        commit=commit,
        timestamp=timestamp,
        tool_version="7.0.0",
        min_tokens=min_tokens,
        ignore_identifiers=ignore_identifiers,
        ignore_literals=ignore_literals,
        elapsed_seconds=round(elapsed, 2),
        summary={
            "total_files": len(file_metrics),
            "total_clones": len(all_duplications),
            "duplication_percentage": round(overall_dup_pct, 2),
            "cross_file_clones": statistics.get("cross_file_clones", 0),
        },
        files=file_metrics,
        duplications=all_duplications,
        statistics=statistics,
        errors=errors,
    )


def find_java() -> str | None:
    """Locate a Java runtime binary, if available."""
    java = shutil.which("java")
    if java:
        return java

    candidates = [
        "/opt/homebrew/opt/openjdk/bin/java",
        "/usr/local/opt/openjdk/bin/java",
        "/opt/homebrew/opt/openjdk@17/bin/java",
        "/usr/local/opt/openjdk@17/bin/java",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return None


def main():
    parser = argparse.ArgumentParser(
        description="PMD CPD Analyzer - Token-based code duplication detection"
    )
    parser.add_argument("repo_path", help="Path to repository to analyze")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for results (output.json will be created here)",
    )
    parser.add_argument(
        "--pmd-home",
        required=True,
        help="Path to PMD installation directory",
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Unique run identifier (UUID)",
    )
    parser.add_argument(
        "--repo-id",
        required=True,
        help="Repository identifier (UUID)",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Git branch name (default: main)",
    )
    parser.add_argument(
        "--commit",
        default="0" * 40,
        help="Git commit SHA (40 hex characters)",
    )
    parser.add_argument(
        "--min-tokens",
        type=int,
        default=50,
        help="Minimum token count for duplication detection (default: 50)",
    )
    parser.add_argument(
        "--ignore-identifiers",
        action="store_true",
        help="Ignore identifier names when detecting duplicates (semantic mode)",
    )
    parser.add_argument(
        "--ignore-literals",
        action="store_true",
        help="Ignore literal values when detecting duplicates (semantic mode)",
    )

    args = parser.parse_args()

    # Validate inputs
    if not Path(args.repo_path).exists():
        print(f"Error: Repository path does not exist: {args.repo_path}")
        sys.exit(1)

    if not Path(args.pmd_home).exists():
        print(f"Error: PMD home does not exist: {args.pmd_home}")
        sys.exit(1)

    # Run analysis
    print(f"Analyzing {args.repo_path}...")

    result = analyze(
        args.repo_path,
        args.pmd_home,
        run_id=args.run_id,
        repo_id=args.repo_id,
        branch=args.branch,
        commit=args.commit,
        min_tokens=args.min_tokens,
        ignore_identifiers=args.ignore_identifiers,
        ignore_literals=args.ignore_literals,
    )

    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "output.json"

    # Write output in Caldera envelope format
    with open(output_path, "w") as f:
        json.dump(result.to_caldera_envelope(), f, indent=2)

    print(f"Analysis complete: {len(result.duplications)} clones found")
    print(f"Output written to: {output_path}")

    if result.errors:
        print(f"Warnings: {len(result.errors)}")
        for err in result.errors[:5]:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
