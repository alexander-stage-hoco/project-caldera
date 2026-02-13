#!/usr/bin/env python3
"""License analyzer using pattern matching and SPDX detection."""
from __future__ import annotations

import argparse
import json
import re
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


# License detection patterns
LICENSE_PATTERNS = {
    "MIT": [
        r"MIT License",
        r"Permission is hereby granted, free of charge",
        r"SPDX-License-Identifier:\s*MIT",
    ],
    "Apache-2.0": [
        r"Apache License.*Version 2\.0",
        r"Licensed under the Apache License, Version 2\.0",
        r"SPDX-License-Identifier:\s*Apache-2\.0",
    ],
    "GPL-3.0-only": [
        r"GNU GENERAL PUBLIC LICENSE[\s\S]*?Version 3",
        r"GNU General Public License[\s\S]*?version 3",
        r"SPDX-License-Identifier:\s*GPL-3\.0(-only)?",
    ],
    "GPL-2.0-only": [
        r"GNU GENERAL PUBLIC LICENSE[\s\S]*?Version 2(?!\.1)",
        r"GNU General Public License[\s\S]*?version 2(?!\.1)",
        r"SPDX-License-Identifier:\s*GPL-2\.0(-only)?",
    ],
    "LGPL-2.1-only": [
        r"GNU LESSER GENERAL PUBLIC LICENSE[\s\S]*?Version 2\.1",
        r"GNU Lesser General Public License[\s\S]*?version 2\.1",
        r"SPDX-License-Identifier:\s*LGPL-2\.1(-only)?",
    ],
    "LGPL-3.0-only": [
        r"GNU LESSER GENERAL PUBLIC LICENSE[\s\S]*?Version 3",
        r"SPDX-License-Identifier:\s*LGPL-3\.0(-only)?",
    ],
    "BSD-3-Clause": [
        r"BSD 3-Clause License",
        r"Redistributions of source code must retain",
        r"SPDX-License-Identifier:\s*BSD-3-Clause",
    ],
    "BSD-2-Clause": [
        r"BSD 2-Clause License",
        r"SPDX-License-Identifier:\s*BSD-2-Clause",
    ],
    "ISC": [
        r"ISC License",
        r"SPDX-License-Identifier:\s*ISC",
    ],
    "MPL-2.0": [
        r"Mozilla Public License.*2\.0",
        r"SPDX-License-Identifier:\s*MPL-2\.0",
    ],
    "AGPL-3.0-only": [
        r"GNU AFFERO GENERAL PUBLIC LICENSE[\s\S]*?Version 3",
        r"SPDX-License-Identifier:\s*AGPL-3\.0(-only)?",
    ],
    "Unlicense": [
        r"This is free and unencumbered software released into the public domain",
        r"SPDX-License-Identifier:\s*Unlicense",
    ],
}

# License categories
LICENSE_CATEGORIES = {
    "permissive": ["MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "ISC", "Unlicense"],
    "weak-copyleft": ["LGPL-2.1-only", "LGPL-3.0-only", "MPL-2.0"],
    "copyleft": ["GPL-2.0-only", "GPL-3.0-only", "AGPL-3.0-only"],
}

# Risk levels for license categories
CATEGORY_RISK = {
    "permissive": "low",
    "weak-copyleft": "medium",
    "copyleft": "critical",
    "unknown": "high",
}

# Common license file names
LICENSE_FILES = [
    "LICENSE",
    "LICENSE.txt",
    "LICENSE.md",
    "LICENCE",
    "LICENCE.txt",
    "COPYING",
    "COPYING.txt",
    "UNLICENSE",
]

# SPDX expression patterns with WITH clauses
# These are checked before simple patterns to capture full expressions
SPDX_WITH_PATTERNS = {
    "GPL-2.0-only WITH Classpath-exception-2.0": [
        r"SPDX-License-Identifier:\s*GPL-2\.0(-only)?\s+WITH\s+Classpath-exception-2\.0",
    ],
    "GPL-3.0-only WITH GCC-exception-3.1": [
        r"SPDX-License-Identifier:\s*GPL-3\.0(-only)?\s+WITH\s+GCC-exception-3\.1",
    ],
    "Apache-2.0 WITH LLVM-exception": [
        r"SPDX-License-Identifier:\s*Apache-2\.0\s+WITH\s+LLVM-exception",
    ],
}

# Exception category overrides - these modify the category of the base license
# when paired with the exception
EXCEPTION_CATEGORY_OVERRIDES = {
    "Classpath-exception-2.0": "weak-copyleft",  # GPL + Classpath = linking allowed
    "GCC-exception-3.1": "weak-copyleft",  # GPL + GCC = runtime linking allowed
    "LLVM-exception": "permissive",  # Apache + LLVM = fully permissive
}


def get_category_with_exception(spdx_id: str) -> str:
    """Determine category considering exceptions in SPDX expressions."""
    if " WITH " in spdx_id:
        parts = spdx_id.split(" WITH ")
        exception = parts[1] if len(parts) > 1 else None
        if exception and exception in EXCEPTION_CATEGORY_OVERRIDES:
            return EXCEPTION_CATEGORY_OVERRIDES[exception]
    # Fall back to base license category
    base_license = spdx_id.split(" WITH ")[0]
    return get_category(base_license)


@dataclass
class LicenseFinding:
    """A single license finding."""
    file_path: str
    spdx_id: str
    category: str
    confidence: float  # 0-1
    match_type: str  # "file", "header", "spdx"
    line_number: int = 0


@dataclass
class FileSummary:
    """Summary of licenses in a single file."""
    file_path: str
    licenses: list[str]
    category: str
    has_spdx_header: bool


@dataclass
class DirectoryStats:
    """License statistics for a directory."""
    file_count: int = 0
    files_with_licenses: int = 0
    license_counts: dict[str, int] = field(default_factory=dict)
    category_counts: dict[str, int] = field(default_factory=dict)
    has_copyleft: bool = False
    has_weak_copyleft: bool = False
    has_permissive: bool = False
    worst_risk: str = "unknown"


@dataclass
class DirectoryEntry:
    """Directory rollup entry."""
    path: str
    direct: DirectoryStats
    recursive: DirectoryStats


@dataclass
class LicenseAnalysis:
    """Complete analysis output."""
    schema_version: str = "1.0.0"
    repo_name: str = ""
    repo_path: str = ""
    generated_at: str = ""
    tool: str = "scancode"
    tool_version: str = "1.0.0"

    # Summary
    total_files_scanned: int = 0
    files_with_licenses: int = 0
    license_files_found: int = 0

    # License inventory
    licenses_found: list[str] = field(default_factory=list)
    license_counts: dict[str, int] = field(default_factory=dict)

    # Categories
    has_permissive: bool = False
    has_weak_copyleft: bool = False
    has_copyleft: bool = False
    has_unknown: bool = False

    # Risk assessment
    overall_risk: str = "unknown"
    risk_reasons: list[str] = field(default_factory=list)

    # Detailed findings
    findings: list[LicenseFinding] = field(default_factory=list)

    # File summaries
    files: dict[str, FileSummary] = field(default_factory=dict)

    # Directory rollups
    directories: list[DirectoryEntry] = field(default_factory=list)

    # Timing
    scan_time_ms: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        # Build results object with tool-specific data
        results = {
            "tool": self.tool,
            "tool_version": self.tool_version,
            "scan_time_ms": self.scan_time_ms,
            "total_files_scanned": self.total_files_scanned,
            "files_with_licenses": self.files_with_licenses,
            "license_files_found": self.license_files_found,
            "licenses_found": self.licenses_found,
            "license_counts": self.license_counts,
            "has_permissive": self.has_permissive,
            "has_weak_copyleft": self.has_weak_copyleft,
            "has_copyleft": self.has_copyleft,
            "has_unknown": self.has_unknown,
            "overall_risk": self.overall_risk,
            "risk_reasons": self.risk_reasons,
            "findings": [asdict(f) for f in self.findings],
            "files": {k: asdict(v) for k, v in self.files.items()},
            "directories": {
                "directory_count": len(self.directories),
                "directories": [
                    {
                        "path": d.path,
                        "direct": asdict(d.direct),
                        "recursive": asdict(d.recursive),
                    }
                    for d in self.directories
                ],
            },
        }

        # Build final output with standardized root fields
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "repo_name": self.repo_name,
            "repo_path": self.repo_path,
            "results": results,
        }


def get_category(spdx_id: str) -> str:
    """Get license category from SPDX ID."""
    for category, licenses in LICENSE_CATEGORIES.items():
        if spdx_id in licenses:
            return category
    return "unknown"


def detect_license_in_content(content: str, file_path: str) -> list[LicenseFinding]:
    """Detect licenses in file content."""
    findings = []
    matched_spdx_ids: set[str] = set()  # Track matched licenses to avoid duplicates

    # First, check for SPDX WITH patterns (compound expressions)
    for spdx_id, patterns in SPDX_WITH_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                # Find line number
                line_number = 1
                for i, line in enumerate(content.split("\n"), 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        line_number = i
                        break

                findings.append(LicenseFinding(
                    file_path=file_path,
                    spdx_id=spdx_id,
                    category=get_category_with_exception(spdx_id),
                    confidence=0.95,
                    match_type="spdx",
                    line_number=line_number,
                ))
                matched_spdx_ids.add(spdx_id)
                # Also mark base license as matched to avoid duplicate detection
                base_license = spdx_id.split(" WITH ")[0]
                matched_spdx_ids.add(base_license)
                break  # Only match once per license type per file

    # Then check standard patterns (skip if already matched via WITH pattern)
    for spdx_id, patterns in LICENSE_PATTERNS.items():
        if spdx_id in matched_spdx_ids:
            continue  # Skip if already matched (e.g., as part of a WITH expression)

        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                # Determine match type
                if "SPDX-License-Identifier" in pattern:
                    match_type = "spdx"
                    confidence = 0.95
                elif (file_path.upper().startswith("LICENSE") or
                      file_path.upper().startswith("COPYING") or
                      file_path.upper().startswith("UNLICENSE")):
                    match_type = "file"
                    confidence = 0.90
                else:
                    match_type = "header"
                    confidence = 0.80

                # Find line number
                line_number = 1
                for i, line in enumerate(content.split("\n"), 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        line_number = i
                        break

                findings.append(LicenseFinding(
                    file_path=file_path,
                    spdx_id=spdx_id,
                    category=get_category(spdx_id),
                    confidence=confidence,
                    match_type=match_type,
                    line_number=line_number,
                ))
                matched_spdx_ids.add(spdx_id)
                break  # Only match once per license type per file

    return findings


def analyze_repository(repo_path: Path) -> LicenseAnalysis:
    """Analyze a repository for licenses."""
    repo_name = repo_path.name
    start_time = time.time()

    analysis = LicenseAnalysis(
        repo_name=repo_name,
        repo_path=str(repo_path.resolve()),
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )

    # Collect all files
    all_findings: list[LicenseFinding] = []
    license_files_found = 0
    files_with_licenses: set[str] = set()
    total_files = 0

    # First, scan license files
    for license_name in LICENSE_FILES:
        for license_file in repo_path.rglob(license_name):
            if license_file.is_file():
                license_files_found += 1
                rel_path = str(license_file.relative_to(repo_path))
                try:
                    content = license_file.read_text(errors="ignore")
                    findings = detect_license_in_content(content, rel_path)
                    all_findings.extend(findings)
                    if findings:
                        files_with_licenses.add(rel_path)
                except Exception:
                    pass

    # Also scan for LICENSE.* variants
    for license_file in repo_path.rglob("LICENSE.*"):
        if license_file.is_file():
            license_files_found += 1
            rel_path = str(license_file.relative_to(repo_path))
            try:
                content = license_file.read_text(errors="ignore")
                findings = detect_license_in_content(content, rel_path)
                all_findings.extend(findings)
                if findings:
                    files_with_licenses.add(rel_path)
            except Exception:
                pass

    # Also scan for LICENSE-* variants (e.g., LICENSE-MIT, LICENSE-APACHE)
    for license_file in repo_path.rglob("LICENSE-*"):
        if license_file.is_file():
            license_files_found += 1
            rel_path = str(license_file.relative_to(repo_path))
            try:
                content = license_file.read_text(errors="ignore")
                findings = detect_license_in_content(content, rel_path)
                all_findings.extend(findings)
                if findings:
                    files_with_licenses.add(rel_path)
            except Exception:
                pass

    # Scan source files for SPDX headers
    source_extensions = {".py", ".js", ".ts", ".java", ".cs", ".go", ".rs", ".c", ".cpp", ".h"}
    for src_file in repo_path.rglob("*"):
        if src_file.is_file() and src_file.suffix in source_extensions:
            total_files += 1
            rel_path = str(src_file.relative_to(repo_path))
            try:
                # Only read first 50 lines for SPDX headers
                with open(src_file, "r", errors="ignore") as f:
                    header = "".join(f.readline() for _ in range(50))

                findings = detect_license_in_content(header, rel_path)
                all_findings.extend(findings)
                if findings:
                    files_with_licenses.add(rel_path)
            except Exception:
                pass

    # Build analysis summary
    analysis.findings = all_findings
    analysis.total_files_scanned = total_files + license_files_found
    analysis.license_files_found = license_files_found
    analysis.files_with_licenses = len(files_with_licenses)

    # Count licenses
    license_counts: dict[str, int] = defaultdict(int)
    unique_licenses: set[str] = set()

    for finding in all_findings:
        license_counts[finding.spdx_id] += 1
        unique_licenses.add(finding.spdx_id)

    analysis.licenses_found = sorted(unique_licenses)
    analysis.license_counts = dict(license_counts)

    # Determine categories present
    categories_present: set[str] = set()
    for finding in all_findings:
        categories_present.add(finding.category)

    analysis.has_permissive = "permissive" in categories_present
    analysis.has_weak_copyleft = "weak-copyleft" in categories_present
    analysis.has_copyleft = "copyleft" in categories_present
    analysis.has_unknown = "unknown" in categories_present or not all_findings

    # Build file summaries
    file_findings: dict[str, list[LicenseFinding]] = defaultdict(list)
    for finding in all_findings:
        file_findings[finding.file_path].append(finding)

    for file_path, findings_list in file_findings.items():
        licenses = list(set(f.spdx_id for f in findings_list))
        categories = list(set(f.category for f in findings_list))

        # Determine file category (worst case)
        if "copyleft" in categories:
            file_category = "copyleft"
        elif "weak-copyleft" in categories:
            file_category = "weak-copyleft"
        elif "permissive" in categories:
            file_category = "permissive"
        else:
            file_category = "unknown"

        has_spdx = any(f.match_type == "spdx" for f in findings_list)

        analysis.files[file_path] = FileSummary(
            file_path=file_path,
            licenses=licenses,
            category=file_category,
            has_spdx_header=has_spdx,
        )

    # Determine overall risk
    risk_reasons = []

    if not all_findings:
        analysis.overall_risk = "high"
        risk_reasons.append("No license found - all rights reserved by default")
    elif analysis.has_copyleft:
        analysis.overall_risk = "critical"
        copyleft_licenses = [l for l in unique_licenses if get_category(l) == "copyleft"]
        risk_reasons.append(f"Copyleft license(s) found: {', '.join(copyleft_licenses)}")
        risk_reasons.append("Derivative works must be released under same license")
    elif analysis.has_weak_copyleft:
        analysis.overall_risk = "medium"
        weak_copyleft = [l for l in unique_licenses if get_category(l) == "weak-copyleft"]
        risk_reasons.append(f"Weak copyleft license(s) found: {', '.join(weak_copyleft)}")
        risk_reasons.append("May require source disclosure for modifications")
    else:
        analysis.overall_risk = "low"
        risk_reasons.append("Only permissive licenses found")

    analysis.risk_reasons = risk_reasons

    # Compute directory rollups
    analysis.directories = compute_directory_rollups(analysis.files)

    analysis.scan_time_ms = (time.time() - start_time) * 1000

    return analysis


def _build_directory_stats(files: list[FileSummary]) -> DirectoryStats:
    """Build directory statistics from a list of file summaries."""
    if not files:
        return DirectoryStats()

    license_counts: dict[str, int] = defaultdict(int)
    category_counts: dict[str, int] = defaultdict(int)

    for f in files:
        for lic in f.licenses:
            license_counts[lic] += 1
        category_counts[f.category] += 1

    has_copyleft = "copyleft" in category_counts
    has_weak_copyleft = "weak-copyleft" in category_counts
    has_permissive = "permissive" in category_counts

    if has_copyleft:
        worst_risk = "critical"
    elif has_weak_copyleft:
        worst_risk = "medium"
    elif has_permissive:
        worst_risk = "low"
    else:
        worst_risk = "unknown"

    return DirectoryStats(
        file_count=len(files),
        files_with_licenses=sum(1 for f in files if f.licenses),
        license_counts=dict(license_counts),
        category_counts=dict(category_counts),
        has_copyleft=has_copyleft,
        has_weak_copyleft=has_weak_copyleft,
        has_permissive=has_permissive,
        worst_risk=worst_risk,
    )


def compute_directory_rollups(files: dict[str, FileSummary]) -> list[DirectoryEntry]:
    """Compute direct and recursive directory rollups."""
    dir_direct: dict[str, list[FileSummary]] = defaultdict(list)
    dir_recursive: dict[str, list[FileSummary]] = defaultdict(list)

    for file_path, file_summary in files.items():
        path = Path(file_path)
        parent = str(path.parent) if str(path.parent) != "." else "/"
        dir_direct[parent].append(file_summary)

        for ancestor in path.parents:
            ancestor_str = str(ancestor) if str(ancestor) != "." else "/"
            dir_recursive[ancestor_str].append(file_summary)

    all_dirs = set(dir_direct.keys()) | set(dir_recursive.keys())
    directories: list[DirectoryEntry] = []

    for dir_path in sorted(all_dirs):
        direct_files = dir_direct.get(dir_path, [])
        recursive_files = dir_recursive.get(dir_path, [])

        directories.append(DirectoryEntry(
            path=dir_path,
            direct=_build_directory_stats(direct_files),
            recursive=_build_directory_stats(recursive_files),
        ))

    return directories


def analyze_all_repos(
    repos_dir: Path, output_dir: Path
) -> dict[str, LicenseAnalysis]:
    """Analyze all repositories in a directory."""
    results = {}

    for repo_path in sorted(repos_dir.iterdir()):
        if not repo_path.is_dir():
            continue
        if repo_path.name.startswith("."):
            continue

        print(f"Analyzing: {repo_path.name}")
        analysis = analyze_repository(repo_path)
        results[repo_path.name] = analysis

        # Save individual result
        output_path = output_dir / f"{repo_path.name}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(analysis.to_dict(), indent=2, default=str)
        )
        print(f"  Licenses: {analysis.licenses_found or ['none']}")
        print(f"  Risk: {analysis.overall_risk}")
        print(f"  Output: {output_path}")

    return results


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze repositories for licenses")
    parser.add_argument(
        "path",
        type=Path,
        help="Repository or directory of repositories to analyze",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("output/runs"),
        help="Output directory for results",
    )

    args = parser.parse_args()

    print("License Analyzer")
    print("=" * 60)
    print()

    # Determine if path is single repo or directory of repos
    has_files = any(entry.is_file() for entry in args.path.iterdir())
    if (args.path / ".git").exists() or has_files:
        # Single repository
        print(f"Analyzing single repository: {args.path}")
        analysis = analyze_repository(args.path)

        # Check if output is a file path (.json) or directory
        is_file_output = str(args.output).endswith('.json')
        if is_file_output:
            output_path = args.output
        else:
            output_path = args.output / f"{args.path.name}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(analysis.to_dict(), indent=2, default=str))

        print(f"Licenses: {analysis.licenses_found or ['none']}")
        print(f"Risk: {analysis.overall_risk}")
        print(f"Output: {output_path}")
    else:
        # Directory of repositories
        print(f"Analyzing all repositories in: {args.path}")
        print()

        output_dir = args.output
        if str(output_dir).endswith('.json'):
            output_dir = output_dir.parent
        results = analyze_all_repos(args.path, output_dir)

        print()
        print("=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"Repositories analyzed: {len(results)}")

        # Risk breakdown
        by_risk: dict[str, list[str]] = defaultdict(list)
        for name, analysis in results.items():
            by_risk[analysis.overall_risk].append(name)

        print("\nBy risk level:")
        for risk in ["critical", "high", "medium", "low"]:
            if risk in by_risk:
                print(f"  {risk}: {', '.join(by_risk[risk])}")


if __name__ == "__main__":
    main()
