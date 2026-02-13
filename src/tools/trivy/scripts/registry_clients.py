"""Package registry clients for freshness checking.

Provides functions to query PyPI, npm, and other package registries
to determine the latest available versions for dependency analysis.
"""
from __future__ import annotations

import concurrent.futures
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from packaging.version import Version, InvalidVersion

logger = logging.getLogger(__name__)

# Timeout for registry API calls (seconds)
DEFAULT_TIMEOUT = 5.0


def fetch_pypi_latest(package_name: str, timeout: float = DEFAULT_TIMEOUT) -> dict | None:
    """Fetch latest version info from PyPI.

    API: https://pypi.org/pypi/{package}/json

    Args:
        package_name: The Python package name
        timeout: Request timeout in seconds

    Returns:
        Dict with latest_version and released_date, or None on failure
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()

        latest = data["info"]["version"]
        releases = data.get("releases", {})
        release_info = releases.get(latest, [{}])

        # Get upload time from first file in release
        released_date = None
        if release_info and isinstance(release_info, list) and release_info[0]:
            released_date = release_info[0].get("upload_time")

        return {
            "latest_version": latest,
            "released_date": released_date,
        }
    except httpx.HTTPStatusError as e:
        logger.debug(f"PyPI API error for {package_name}: {e.response.status_code}")
        return None
    except Exception as e:
        logger.debug(f"Failed to fetch PyPI info for {package_name}: {e}")
        return None


def fetch_npm_latest(package_name: str, timeout: float = DEFAULT_TIMEOUT) -> dict | None:
    """Fetch latest version info from npm registry.

    API: https://registry.npmjs.org/{package}

    Args:
        package_name: The npm package name
        timeout: Request timeout in seconds

    Returns:
        Dict with latest_version and released_date, or None on failure
    """
    # Handle scoped packages (e.g., @types/node -> %40types%2Fnode)
    encoded_name = package_name.replace("/", "%2F")
    url = f"https://registry.npmjs.org/{encoded_name}"

    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()

        latest = data.get("dist-tags", {}).get("latest")
        if not latest:
            return None

        time_data = data.get("time", {})
        released_date = time_data.get(latest)

        return {
            "latest_version": latest,
            "released_date": released_date,
        }
    except httpx.HTTPStatusError as e:
        logger.debug(f"npm API error for {package_name}: {e.response.status_code}")
        return None
    except Exception as e:
        logger.debug(f"Failed to fetch npm info for {package_name}: {e}")
        return None


def fetch_go_latest(module_name: str, timeout: float = DEFAULT_TIMEOUT) -> dict | None:
    """Fetch latest version info from Go module proxy.

    API: https://proxy.golang.org/{module}/@latest

    Args:
        module_name: The Go module path (e.g., github.com/gin-gonic/gin)
        timeout: Request timeout in seconds

    Returns:
        Dict with latest_version and released_date, or None on failure
    """
    # Escape module name for URL (lowercase, escape special chars)
    escaped = module_name.lower()
    url = f"https://proxy.golang.org/{escaped}/@latest"

    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()

        return {
            "latest_version": data.get("Version", "").lstrip("v"),
            "released_date": data.get("Time"),
        }
    except httpx.HTTPStatusError as e:
        logger.debug(f"Go proxy API error for {module_name}: {e.response.status_code}")
        return None
    except Exception as e:
        logger.debug(f"Failed to fetch Go info for {module_name}: {e}")
        return None


def fetch_nuget_latest(package_name: str, timeout: float = DEFAULT_TIMEOUT) -> dict | None:
    """Fetch latest version info from NuGet registry.

    API: https://api.nuget.org/v3-flatcontainer/{package}/index.json

    Args:
        package_name: The NuGet package name (e.g., Newtonsoft.Json)
        timeout: Request timeout in seconds

    Returns:
        Dict with latest_version and released_date, or None on failure
    """
    # NuGet package names are case-insensitive, API requires lowercase
    package_lower = package_name.lower()
    url = f"https://api.nuget.org/v3-flatcontainer/{package_lower}/index.json"

    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()

        versions = data.get("versions", [])
        if not versions:
            return None

        # Filter out prerelease versions and get latest stable
        stable_versions = [v for v in versions if "-" not in v]
        latest = stable_versions[-1] if stable_versions else versions[-1]

        # NuGet index.json doesn't include dates, fetch from registration API
        released_date = _fetch_nuget_release_date(package_lower, latest, timeout)

        return {
            "latest_version": latest,
            "released_date": released_date,
        }
    except httpx.HTTPStatusError as e:
        logger.debug(f"NuGet API error for {package_name}: {e.response.status_code}")
        return None
    except Exception as e:
        logger.debug(f"Failed to fetch NuGet info for {package_name}: {e}")
        return None


def _fetch_nuget_release_date(
    package_name: str, version: str, timeout: float = DEFAULT_TIMEOUT
) -> str | None:
    """Fetch release date for a specific NuGet package version.

    Args:
        package_name: Lowercase package name
        version: Version string
        timeout: Request timeout

    Returns:
        ISO date string or None
    """
    url = f"https://api.nuget.org/v3/registration5-semver1/{package_name}/{version}.json"
    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()
        return data.get("published")
    except Exception:
        return None


def fetch_maven_latest(package_name: str, timeout: float = DEFAULT_TIMEOUT) -> dict | None:
    """Fetch latest version info from Maven Central.

    API: https://search.maven.org/solrsearch/select?q=g:{group}+AND+a:{artifact}

    Args:
        package_name: Maven coordinates in format "groupId:artifactId"
                      (e.g., "com.google.guava:guava")
        timeout: Request timeout in seconds

    Returns:
        Dict with latest_version and released_date, or None on failure
    """
    # Split group:artifact format
    if ":" not in package_name:
        logger.debug(f"Invalid Maven coordinates (missing ':'): {package_name}")
        return None

    parts = package_name.split(":")
    if len(parts) < 2:
        return None

    group_id = parts[0]
    artifact_id = parts[1]

    url = (
        f"https://search.maven.org/solrsearch/select?"
        f"q=g:{group_id}+AND+a:{artifact_id}&rows=1&wt=json"
    )

    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()

        docs = data.get("response", {}).get("docs", [])
        if not docs:
            return None

        doc = docs[0]
        latest = doc.get("latestVersion") or doc.get("v")
        timestamp = doc.get("timestamp")

        # Convert timestamp (milliseconds since epoch) to ISO date
        released_date = None
        if timestamp:
            try:
                dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                released_date = dt.isoformat()
            except (ValueError, OSError):
                pass

        return {
            "latest_version": latest,
            "released_date": released_date,
        }
    except httpx.HTTPStatusError as e:
        logger.debug(f"Maven API error for {package_name}: {e.response.status_code}")
        return None
    except Exception as e:
        logger.debug(f"Failed to fetch Maven info for {package_name}: {e}")
        return None


def calculate_version_delta(installed: str, latest: str) -> dict[str, Any]:
    """Calculate how many major/minor versions behind.

    Args:
        installed: Currently installed version string
        latest: Latest available version string

    Returns:
        Dict with major_behind, minor_behind, patch_behind, is_outdated
    """
    try:
        # Clean version strings (remove leading v, etc.)
        installed_clean = installed.lstrip("vV")
        latest_clean = latest.lstrip("vV")

        v_installed = Version(installed_clean)
        v_latest = Version(latest_clean)

        major_behind = max(0, v_latest.major - v_installed.major)
        minor_behind = 0
        patch_behind = 0

        if major_behind == 0:
            minor_behind = max(0, v_latest.minor - v_installed.minor)
            if minor_behind == 0:
                patch_behind = max(0, v_latest.micro - v_installed.micro)

        return {
            "major_behind": major_behind,
            "minor_behind": minor_behind,
            "patch_behind": patch_behind,
            "is_outdated": v_latest > v_installed,
        }
    except InvalidVersion:
        # If versions can't be parsed, do simple string comparison
        return {
            "major_behind": 0,
            "minor_behind": 0,
            "patch_behind": 0,
            "is_outdated": installed != latest,
        }


def calculate_days_since(date_str: str | None) -> int:
    """Calculate days since a given ISO date string.

    Args:
        date_str: ISO format date string (e.g., "2024-01-15T10:30:00Z")

    Returns:
        Number of days since the date, or 0 if date is invalid/None
    """
    if not date_str:
        return 0

    try:
        # Handle various date formats
        if "T" in date_str:
            # ISO format: 2024-01-15T10:30:00Z or 2024-01-15T10:30:00
            if date_str.endswith("Z"):
                release_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            elif "+" in date_str or date_str.count("-") > 2:
                release_date = datetime.fromisoformat(date_str)
            else:
                release_date = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
        else:
            # Simple date: 2024-01-15
            release_date = datetime.strptime(date_str[:10], "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )

        now = datetime.now(timezone.utc)
        delta = now - release_date
        return max(0, delta.days)
    except (ValueError, TypeError):
        return 0


def get_registry_fetcher(package_type: str):
    """Get the appropriate registry fetcher for a package type.

    Args:
        package_type: Package manager type (pip, npm, go, nuget, pom, etc.)

    Returns:
        Fetcher function or None if unsupported
    """
    fetchers = {
        # Python
        "pip": fetch_pypi_latest,
        "poetry": fetch_pypi_latest,
        "pipenv": fetch_pypi_latest,
        # JavaScript/Node.js
        "npm": fetch_npm_latest,
        "nodejs": fetch_npm_latest,
        "yarn": fetch_npm_latest,
        "pnpm": fetch_npm_latest,
        # Go
        "gomod": fetch_go_latest,
        "go": fetch_go_latest,
        # .NET/NuGet
        "nuget": fetch_nuget_latest,
        "dotnet-deps": fetch_nuget_latest,
        "packages-config": fetch_nuget_latest,
        # Java/Maven
        "pom": fetch_maven_latest,
        "gradle-lockfile": fetch_maven_latest,
        "jar": fetch_maven_latest,
    }
    return fetchers.get(package_type.lower())


def fetch_freshness_batch(
    packages: list[dict], package_type: str, max_workers: int = 5
) -> dict[str, dict]:
    """Fetch freshness info for multiple packages in parallel.

    Args:
        packages: List of package dicts with 'Name' and 'Version' keys
        package_type: Package manager type
        max_workers: Max concurrent API requests

    Returns:
        Dict mapping package name to freshness info
    """
    fetcher = get_registry_fetcher(package_type)
    if not fetcher:
        logger.debug(f"No registry fetcher available for package type: {package_type}")
        return {}

    results = {}

    def fetch_one(pkg: dict) -> tuple[str, dict | None]:
        name = pkg.get("Name", "")
        installed = pkg.get("Version", "unknown")
        latest_info = fetcher(name)

        if latest_info:
            delta = calculate_version_delta(installed, latest_info["latest_version"])
            days_since = calculate_days_since(latest_info.get("released_date"))

            return name, {
                "installed_version": installed,
                "latest_version": latest_info["latest_version"],
                "released_date": latest_info.get("released_date"),
                "days_since_latest": days_since,
                **delta,
            }
        return name, None

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_one, pkg): pkg for pkg in packages}
        for future in concurrent.futures.as_completed(futures):
            try:
                name, info = future.result()
                if info:
                    results[name] = info
            except Exception as e:
                pkg = futures[future]
                logger.debug(f"Error fetching freshness for {pkg.get('Name')}: {e}")

    return results
