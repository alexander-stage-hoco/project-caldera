"""Unit tests for git-sizer binary manager."""

import platform
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.binary_manager import (
    get_platform_suffix,
    get_download_url,
    get_binary_path,
    is_binary_installed,
    GIT_SIZER_VERSION,
)


class TestGetPlatformSuffix:
    """Tests for get_platform_suffix function."""

    @patch("platform.system")
    @patch("platform.machine")
    def test_darwin_arm64(self, mock_machine, mock_system):
        """Test macOS ARM64 detection."""
        mock_system.return_value = "Darwin"
        mock_machine.return_value = "arm64"

        suffix = get_platform_suffix()
        assert suffix == "darwin-arm64"

    @patch("platform.system")
    @patch("platform.machine")
    def test_darwin_x86(self, mock_machine, mock_system):
        """Test macOS x86_64 detection."""
        mock_system.return_value = "Darwin"
        mock_machine.return_value = "x86_64"

        suffix = get_platform_suffix()
        assert suffix == "darwin-amd64"

    @patch("platform.system")
    @patch("platform.machine")
    def test_linux_x86(self, mock_machine, mock_system):
        """Test Linux x86_64 detection."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "x86_64"

        suffix = get_platform_suffix()
        assert suffix == "linux-amd64"

    @patch("platform.system")
    @patch("platform.machine")
    def test_linux_386(self, mock_machine, mock_system):
        """Test Linux 32-bit detection."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "i386"

        suffix = get_platform_suffix()
        assert suffix == "linux-386"

    @patch("platform.system")
    def test_windows_unsupported(self, mock_system):
        """Test Windows raises error."""
        mock_system.return_value = "Windows"

        with pytest.raises(RuntimeError) as exc_info:
            get_platform_suffix()
        assert "Unsupported platform" in str(exc_info.value)


class TestGetDownloadUrl:
    """Tests for get_download_url function."""

    @patch("scripts.binary_manager.get_platform_suffix")
    def test_url_format(self, mock_suffix):
        """Test download URL format."""
        mock_suffix.return_value = "darwin-arm64"

        url = get_download_url()
        assert "darwin-arm64" in url
        assert GIT_SIZER_VERSION in url
        assert url.endswith(".zip")
        assert "github.com/github/git-sizer" in url

    @patch("scripts.binary_manager.get_platform_suffix")
    def test_linux_url(self, mock_suffix):
        """Test Linux AMD64 download URL."""
        mock_suffix.return_value = "linux-amd64"

        url = get_download_url()
        assert "linux-amd64" in url
        assert url.endswith(".zip")


class TestGetBinaryPath:
    """Tests for binary path configuration."""

    def test_binary_path_is_path(self):
        """Test get_binary_path returns a Path."""
        path = get_binary_path()
        assert isinstance(path, Path)

    def test_binary_path_in_bin_dir(self):
        """Test binary is in bin directory."""
        path = get_binary_path()
        assert path.parent.name == "bin"
        assert path.name == "git-sizer"


class TestIsBinaryInstalled:
    """Tests for binary installation detection."""

    @patch("scripts.binary_manager.get_binary_path")
    @patch("os.access")
    def test_installed_when_exists_and_executable(self, mock_access, mock_path):
        """Test detection when binary exists and is executable."""
        mock_path_obj = MagicMock()
        mock_path_obj.exists.return_value = True
        mock_path.return_value = mock_path_obj
        mock_access.return_value = True

        assert is_binary_installed() is True

    @patch("scripts.binary_manager.get_binary_path")
    def test_not_installed_when_missing(self, mock_path):
        """Test detection when binary doesn't exist."""
        mock_path_obj = MagicMock()
        mock_path_obj.exists.return_value = False
        mock_path.return_value = mock_path_obj

        assert is_binary_installed() is False
