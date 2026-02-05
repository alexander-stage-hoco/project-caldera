"""Shared CLI argument parsing utilities for tool analysis scripts.

Provides standardized argument definitions and validation for the common CLI
arguments used by all Caldera tools:
- --repo-path: Path to repository to analyze
- --repo-name: Repository name for output naming
- --output-dir: Directory to write analysis output
- --run-id: Run identifier (required)
- --repo-id: Repository identifier (required)
- --branch: Branch analyzed
- --commit: Commit SHA (auto-detected if not provided)
"""
from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import Self
import os

from .git_utilities import resolve_commit


@dataclass(frozen=True)
class CommonArgs:
    """Validated common CLI arguments.

    All fields are validated and ready to use - no further processing needed.
    """

    repo_path: Path
    """Resolved path to the repository (validated to exist)."""

    repo_name: str
    """Repository name (derived from repo_path if not provided)."""

    output_dir: Path
    """Output directory (created if create_output_dir=True during validation)."""

    output_path: Path
    """Full path to output.json file."""

    run_id: str
    """Run identifier (required, validated non-empty)."""

    repo_id: str
    """Repository identifier (required, validated non-empty)."""

    branch: str
    """Git branch name."""

    commit: str
    """Resolved commit SHA."""


@dataclass
class CommitResolutionConfig:
    """Configuration for commit resolution behavior.

    Controls how commits are validated when resolving CLI arguments.
    """

    strict: bool
    """If True, raise/exit when commit not found. If False, trust orchestrator."""

    fallback_repo: Path | None
    """Optional secondary repository to check for the commit."""

    @classmethod
    def strict_with_fallback(cls, tool_dir: Path) -> Self:
        """Create strict config with fallback to tool directory.

        Used by tools that need strict commit validation but may analyze
        subdirectories of a larger repository.

        Args:
            tool_dir: Path to the tool directory (typically Path(__file__).parent.parent).

        Returns:
            CommitResolutionConfig with strict=True and fallback_repo set.
        """
        return cls(strict=True, fallback_repo=tool_dir)

    @classmethod
    def lenient(cls) -> Self:
        """Create lenient config that trusts orchestrator-provided commits.

        Used by tools that run in trusted environments where the orchestrator
        has already validated the commit.

        Returns:
            CommitResolutionConfig with strict=False and no fallback.
        """
        return cls(strict=False, fallback_repo=None)

    @classmethod
    def strict_no_fallback(cls) -> Self:
        """Create strict config without fallback repository.

        Used by tools that require commits to exist in the target repo only.

        Returns:
            CommitResolutionConfig with strict=True and no fallback.
        """
        return cls(strict=True, fallback_repo=None)


class ValidationError(Exception):
    """Raised when CLI argument validation fails."""

    pass


def add_common_args(
    parser: ArgumentParser,
    *,
    default_repo_path: str | None = "eval-repos/synthetic",
) -> None:
    """Add common Caldera CLI arguments to a parser.

    This function adds the standard set of CLI arguments used by all Caldera
    tools. Tools can add their own tool-specific arguments after calling this.

    Args:
        parser: ArgumentParser to add arguments to.
        default_repo_path: Default value for --repo-path. Set to None to make
            --repo-path required (no default). Defaults to "eval-repos/synthetic".

    Example:
        parser = argparse.ArgumentParser(description="My tool")
        add_common_args(parser)
        parser.add_argument("--my-option", help="Tool-specific option")
        args = parser.parse_args()
    """
    parser.add_argument(
        "--repo-path",
        default=os.environ.get("REPO_PATH", default_repo_path),
        help="Path to repository to analyze",
    )
    parser.add_argument(
        "--repo-name",
        default=os.environ.get("REPO_NAME", ""),
        help="Repository name for output naming",
    )
    parser.add_argument(
        "--output-dir",
        default=os.environ.get("OUTPUT_DIR"),
        help="Directory to write analysis output (default: outputs/<run-id>)",
    )
    parser.add_argument(
        "--run-id",
        default=os.environ.get("RUN_ID", ""),
        help="Run identifier (required)",
    )
    parser.add_argument(
        "--repo-id",
        default=os.environ.get("REPO_ID", ""),
        help="Repository identifier (required)",
    )
    parser.add_argument(
        "--branch",
        default=os.environ.get("BRANCH", "main"),
        help="Branch analyzed",
    )
    parser.add_argument(
        "--commit",
        default=os.environ.get("COMMIT", ""),
        help="Commit SHA (auto-detected if not provided)",
    )


def validate_common_args_raising(
    args: Namespace,
    *,
    commit_config: CommitResolutionConfig | None = None,
    create_output_dir: bool = True,
) -> CommonArgs:
    """Validate CLI arguments and return CommonArgs. Raises exceptions on error.

    This variant raises exceptions for validation failures, suitable for tools
    that want to handle errors with try/except blocks.

    Args:
        args: Parsed argument namespace from argparse.
        commit_config: Configuration for commit resolution. Defaults to lenient mode.
        create_output_dir: If True, creates the output directory. Defaults to True.

    Returns:
        Validated CommonArgs dataclass ready for use.

    Raises:
        ValidationError: When a required argument is missing or invalid.
        FileNotFoundError: When repo_path does not exist.
        ValueError: When commit resolution fails in strict mode.

    Example:
        args = parser.parse_args()
        try:
            common = validate_common_args_raising(args)
        except (ValidationError, FileNotFoundError, ValueError) as e:
            raise ValueError(str(e)) from e
    """
    if commit_config is None:
        commit_config = CommitResolutionConfig.lenient()

    # Validate repo_path
    if not args.repo_path:
        raise ValidationError("--repo-path is required")

    repo_path = Path(args.repo_path)
    if not repo_path.exists():
        raise FileNotFoundError(f"Repository not found at {repo_path}")

    # Derive repo_name
    repo_name = args.repo_name or repo_path.resolve().name

    # Validate required identifiers
    if not args.run_id:
        raise ValidationError("--run-id is required")
    if not args.repo_id:
        raise ValidationError("--repo-id is required")

    # Resolve commit (may raise ValueError in strict mode)
    commit = resolve_commit(
        repo_path.resolve(),
        args.commit or None,
        fallback_repo=commit_config.fallback_repo,
        strict=commit_config.strict,
    )

    # Determine output directory
    output_dir = Path(args.output_dir) if args.output_dir else Path("outputs") / args.run_id
    if create_output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "output.json"

    return CommonArgs(
        repo_path=repo_path,
        repo_name=repo_name,
        output_dir=output_dir,
        output_path=output_path,
        run_id=args.run_id,
        repo_id=args.repo_id,
        branch=args.branch,
        commit=commit,
    )


def validate_common_args(
    args: Namespace,
    *,
    commit_config: CommitResolutionConfig | None = None,
    create_output_dir: bool = True,
) -> CommonArgs:
    """Validate CLI arguments and return CommonArgs. Exits on error.

    This variant prints error messages to stderr and calls sys.exit(1) on
    validation failures, suitable for tools that use simple exit-on-error
    error handling.

    Args:
        args: Parsed argument namespace from argparse.
        commit_config: Configuration for commit resolution. Defaults to lenient mode.
        create_output_dir: If True, creates the output directory. Defaults to True.

    Returns:
        Validated CommonArgs dataclass ready for use.

    Example:
        args = parser.parse_args()
        common = validate_common_args(args)
        # If we get here, all arguments are valid
        print(f"Analyzing: {common.repo_path}")
    """
    try:
        return validate_common_args_raising(
            args,
            commit_config=commit_config,
            create_output_dir=create_output_dir,
        )
    except (ValidationError, FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
