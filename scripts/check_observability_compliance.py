#!/usr/bin/env python3
"""
Check LLM observability compliance across the codebase.

This script verifies that:
1. No direct anthropic.Anthropic().messages.create() calls outside shared module
2. No subprocess.run(["claude"...]) calls outside shared module
3. All tool base.py files import from shared (no local invoke_claude)
4. Orchestrators call require_observability()

Exit codes:
    0 = All checks pass
    1 = Violations found

Usage:
    python scripts/check_observability_compliance.py
    python scripts/check_observability_compliance.py --verbose
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def find_python_files(root: Path, exclude_patterns: list[str] | None = None) -> list[Path]:
    """Find all Python files under root, excluding specified patterns."""
    exclude_patterns = exclude_patterns or []
    files = []
    for path in root.rglob("*.py"):
        excluded = False
        for pattern in exclude_patterns:
            if pattern in str(path):
                excluded = True
                break
        if not excluded:
            files.append(path)
    return files


def check_direct_anthropic_calls(files: list[Path], verbose: bool = False) -> list[str]:
    """Check for direct anthropic SDK calls outside shared module."""
    violations = []
    # Pattern to match: anthropic.Anthropic(...).messages.create or client.messages.create
    pattern = re.compile(r"messages\.create\s*\(")

    # Allowed locations for direct API calls (infrastructure layer)
    allowed_paths = [
        "shared/evaluation/base_judge.py",  # Shared judge base
        "insights/evaluation/llm/providers/",  # Provider infrastructure
        "insights/evaluation/llm/observable_provider.py",  # Observable wrapper
    ]

    for path in files:
        path_str = str(path)

        # Skip allowed locations
        skip = False
        for allowed in allowed_paths:
            if allowed in path_str:
                skip = True
                break
        if skip:
            continue

        # Skip test files
        if "test_" in path.name or path.parent.name == "tests":
            continue

        try:
            content = path.read_text()
            if pattern.search(content):
                violations.append(f"Direct anthropic messages.create() call in {path}")
                if verbose:
                    # Find line number
                    for i, line in enumerate(content.splitlines(), 1):
                        if "messages.create" in line:
                            violations[-1] += f" (line {i})"
                            break
        except Exception as e:
            if verbose:
                print(f"Warning: Could not read {path}: {e}", file=sys.stderr)

    return violations


def check_direct_claude_cli(files: list[Path], verbose: bool = False) -> list[str]:
    """Check for direct subprocess Claude CLI calls outside shared module."""
    violations = []
    # Pattern to match subprocess calls with "claude"
    patterns = [
        re.compile(r'subprocess\.run\s*\(\s*\[?\s*["\']claude["\']'),
        re.compile(r'subprocess\.Popen\s*\(\s*\[?\s*["\']claude["\']'),
    ]

    for path in files:
        # Skip the shared module
        if "shared/evaluation/base_judge.py" in str(path):
            continue
        # Skip test files
        if "test_" in path.name or path.parent.name == "tests":
            continue

        try:
            content = path.read_text()
            for pattern in patterns:
                if pattern.search(content):
                    violations.append(f"Direct subprocess Claude CLI call in {path}")
                    if verbose:
                        for i, line in enumerate(content.splitlines(), 1):
                            if "subprocess" in line and "claude" in line.lower():
                                violations[-1] += f" (line {i})"
                                break
                    break
        except Exception:
            pass

    return violations


def check_tool_base_imports(tools_dir: Path, verbose: bool = False) -> list[str]:
    """Check that tool base.py files import from shared."""
    violations = []

    # Find all tool base.py files
    for base_file in tools_dir.rglob("evaluation/llm/judges/base.py"):
        try:
            content = base_file.read_text()

            # Check for shared import
            if "from shared.evaluation import" not in content:
                violations.append(f"Tool base.py does not import from shared: {base_file}")
                continue

            # Check that it doesn't have its own invoke_claude implementation
            # (it's OK to have an override that calls super())
            if "def invoke_claude(self, prompt: str)" in content:
                # Check if it's an override that calls super
                if "super().invoke_claude" not in content:
                    # Allow overrides that just add test mode support
                    if "return super().invoke_claude(prompt)" not in content and \
                       "SCC_TEST_MODE" not in content:
                        violations.append(
                            f"Tool base.py has local invoke_claude without calling super: {base_file}"
                        )

            if verbose:
                print(f"✓ {base_file.relative_to(tools_dir)}", file=sys.stderr)

        except Exception as e:
            if verbose:
                print(f"Warning: Could not check {base_file}: {e}", file=sys.stderr)

    return violations


def check_orchestrator_enforcement(tools_dir: Path, verbose: bool = False) -> list[str]:
    """Check that orchestrators call require_observability()."""
    violations = []

    for orch_file in tools_dir.rglob("evaluation/llm/orchestrator.py"):
        try:
            content = orch_file.read_text()

            # Check for import
            if "require_observability" not in content:
                violations.append(f"Orchestrator missing require_observability import: {orch_file}")
                continue

            # Check for actual call
            if "require_observability()" not in content:
                violations.append(f"Orchestrator does not call require_observability(): {orch_file}")
                continue

            if verbose:
                print(f"✓ {orch_file.relative_to(tools_dir)}", file=sys.stderr)

        except Exception as e:
            if verbose:
                print(f"Warning: Could not check {orch_file}: {e}", file=sys.stderr)

    return violations


def main():
    parser = argparse.ArgumentParser(
        description="Check LLM observability compliance across the codebase"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed progress and passing files"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Project root directory"
    )
    args = parser.parse_args()

    root = args.root
    tools_dir = root / "src" / "tools"
    src_dir = root / "src"

    if not tools_dir.exists():
        print(f"Error: Tools directory not found: {tools_dir}", file=sys.stderr)
        sys.exit(1)

    all_violations: list[str] = []

    # Find all Python files in src (excluding venv, __pycache__, etc.)
    exclude_patterns = [
        "__pycache__",
        ".venv",
        "venv",
        "site-packages",
        ".git",
    ]
    all_files = find_python_files(src_dir, exclude_patterns)

    print("=" * 60)
    print("LLM Observability Compliance Check")
    print("=" * 60)
    print()

    # Check 1: Direct anthropic SDK calls
    print("Checking for direct anthropic SDK calls...")
    violations = check_direct_anthropic_calls(all_files, args.verbose)
    all_violations.extend(violations)
    print(f"  Found: {len(violations)} violation(s)")
    print()

    # Check 2: Direct Claude CLI calls
    print("Checking for direct subprocess Claude CLI calls...")
    violations = check_direct_claude_cli(all_files, args.verbose)
    all_violations.extend(violations)
    print(f"  Found: {len(violations)} violation(s)")
    print()

    # Check 3: Tool base.py imports
    print("Checking tool base.py imports from shared...")
    violations = check_tool_base_imports(tools_dir, args.verbose)
    all_violations.extend(violations)
    print(f"  Found: {len(violations)} violation(s)")
    print()

    # Check 4: Orchestrator enforcement
    print("Checking orchestrator require_observability() calls...")
    violations = check_orchestrator_enforcement(tools_dir, args.verbose)
    all_violations.extend(violations)
    print(f"  Found: {len(violations)} violation(s)")
    print()

    # Summary
    print("=" * 60)
    if all_violations:
        print(f"FAILED: {len(all_violations)} violation(s) found")
        print("=" * 60)
        print()
        for violation in all_violations:
            print(f"  ✗ {violation}")
        print()
        sys.exit(1)
    else:
        print("PASSED: All observability compliance checks passed")
        print("=" * 60)
        sys.exit(0)


if __name__ == "__main__":
    main()
