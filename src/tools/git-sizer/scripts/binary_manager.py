#!/usr/bin/env python3
"""Binary manager for git-sizer.

Downloads and manages the git-sizer binary from GitHub releases.
"""
from __future__ import annotations

import os
import platform
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

# git-sizer release URL patterns
GIT_SIZER_VERSION = "1.5.0"
GITHUB_RELEASE_BASE = f"https://github.com/github/git-sizer/releases/download/v{GIT_SIZER_VERSION}"


def get_platform_suffix() -> str:
    """Get the platform-specific suffix for git-sizer download."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        if machine == "arm64":
            return "darwin-arm64"
        return "darwin-amd64"
    elif system == "linux":
        if machine in ("x86_64", "amd64"):
            return "linux-amd64"
        return "linux-386"
    else:
        raise RuntimeError(f"Unsupported platform: {system} {machine}")


def get_download_url() -> str:
    """Get the download URL for the current platform."""
    suffix = get_platform_suffix()
    return f"{GITHUB_RELEASE_BASE}/git-sizer-{GIT_SIZER_VERSION}-{suffix}.zip"


def get_binary_path() -> Path:
    """Get the path to the local git-sizer binary."""
    return Path(__file__).parent.parent / "bin" / "git-sizer"


def is_binary_installed() -> bool:
    """Check if git-sizer binary is installed and executable."""
    binary_path = get_binary_path()
    return binary_path.exists() and os.access(binary_path, os.X_OK)


def get_version() -> str:
    """Get the installed git-sizer version."""
    binary_path = get_binary_path()
    if not binary_path.exists():
        return "not installed"

    try:
        result = subprocess.run(
            [str(binary_path), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def download() -> None:
    """Download and install git-sizer binary."""
    binary_path = get_binary_path()
    bin_dir = binary_path.parent
    bin_dir.mkdir(parents=True, exist_ok=True)

    url = get_download_url()
    zip_path = bin_dir / "git-sizer.zip"

    print(f"Downloading git-sizer from {url}...")
    urlretrieve(url, zip_path)

    print("Extracting...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(bin_dir)

    # Make executable
    binary_path.chmod(0o755)

    # Clean up zip
    zip_path.unlink()

    print(f"git-sizer installed to {binary_path}")
    print(f"Version: {get_version()}")


def ensure_binary() -> Path:
    """Ensure git-sizer binary is available, downloading if needed.

    Returns:
        Path to the git-sizer binary
    """
    binary_path = get_binary_path()
    if not is_binary_installed():
        download()
    return binary_path


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Manage git-sizer binary")
    parser.add_argument(
        "command",
        choices=["download", "check", "version", "path"],
        help="Command to run",
    )
    args = parser.parse_args()

    if args.command == "download":
        download()
    elif args.command == "check":
        if is_binary_installed():
            print(f"git-sizer is installed: {get_binary_path()}")
            print(f"Version: {get_version()}")
            sys.exit(0)
        else:
            print("git-sizer is not installed")
            sys.exit(1)
    elif args.command == "version":
        print(get_version())
    elif args.command == "path":
        print(get_binary_path())


if __name__ == "__main__":
    main()
