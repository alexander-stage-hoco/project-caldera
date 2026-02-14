"""Extended unit tests for scripts.binary_manager — covering get_version, download,
ensure_binary, and main CLI."""
from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from scripts.binary_manager import (
    download,
    ensure_binary,
    get_binary_path,
    get_version,
    is_binary_installed,
    main,
    GIT_SIZER_VERSION,
)


# ---------------------------------------------------------------------------
# get_version
# ---------------------------------------------------------------------------

class TestGetVersion:
    @patch("scripts.binary_manager.get_binary_path")
    def test_returns_not_installed_when_missing(self, mock_path):
        mock_path_obj = MagicMock()
        mock_path_obj.exists.return_value = False
        mock_path.return_value = mock_path_obj
        assert get_version() == "not installed"

    @patch("scripts.binary_manager.get_binary_path")
    @patch("subprocess.run")
    def test_returns_version_string(self, mock_run, mock_path):
        mock_path_obj = MagicMock()
        mock_path_obj.exists.return_value = True
        mock_path.return_value = mock_path_obj

        mock_result = MagicMock()
        mock_result.stdout = "git-sizer release 1.5.0\n"
        mock_run.return_value = mock_result

        assert get_version() == "git-sizer release 1.5.0"

    @patch("scripts.binary_manager.get_binary_path")
    @patch("subprocess.run", side_effect=Exception("timeout"))
    def test_returns_unknown_on_error(self, mock_run, mock_path):
        mock_path_obj = MagicMock()
        mock_path_obj.exists.return_value = True
        mock_path.return_value = mock_path_obj
        assert get_version() == "unknown"


# ---------------------------------------------------------------------------
# download
# ---------------------------------------------------------------------------

class TestDownload:
    @patch("scripts.binary_manager.get_version", return_value="1.5.0")
    @patch("scripts.binary_manager.get_download_url", return_value="https://example.com/git-sizer.zip")
    @patch("scripts.binary_manager.get_binary_path")
    @patch("scripts.binary_manager.urlretrieve")
    def test_download_flow(self, mock_retrieve, mock_path, mock_url, mock_version, tmp_path: Path):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        binary_path = bin_dir / "git-sizer"
        mock_path.return_value = binary_path

        # Create a fake zip that urlretrieve "downloads"
        zip_path = bin_dir / "git-sizer.zip"

        def fake_retrieve(url, dest):
            with zipfile.ZipFile(dest, "w") as zf:
                zf.writestr("git-sizer", "#!/bin/sh\necho fake")

        mock_retrieve.side_effect = fake_retrieve

        download()

        # Verify the binary was extracted and made executable
        assert binary_path.exists()
        assert os.access(binary_path, os.X_OK)
        # Zip should be cleaned up
        assert not zip_path.exists()


# ---------------------------------------------------------------------------
# ensure_binary
# ---------------------------------------------------------------------------

class TestEnsureBinary:
    @patch("scripts.binary_manager.is_binary_installed", return_value=True)
    @patch("scripts.binary_manager.get_binary_path")
    def test_returns_path_when_installed(self, mock_path, mock_installed):
        expected = Path("/usr/local/bin/git-sizer")
        mock_path.return_value = expected
        result = ensure_binary()
        assert result == expected

    @patch("scripts.binary_manager.download")
    @patch("scripts.binary_manager.is_binary_installed", return_value=False)
    @patch("scripts.binary_manager.get_binary_path")
    def test_downloads_when_not_installed(self, mock_path, mock_installed, mock_download):
        expected = Path("/tmp/bin/git-sizer")
        mock_path.return_value = expected
        result = ensure_binary()
        assert result == expected
        mock_download.assert_called_once()


# ---------------------------------------------------------------------------
# main (CLI)
# ---------------------------------------------------------------------------

class TestMainCLI:
    @patch("scripts.binary_manager.is_binary_installed", return_value=True)
    @patch("scripts.binary_manager.get_binary_path", return_value=Path("/bin/git-sizer"))
    @patch("scripts.binary_manager.get_version", return_value="1.5.0")
    def test_check_installed(self, mock_ver, mock_path, mock_installed, capsys):
        with patch("sys.argv", ["binary_manager", "check"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "installed" in captured.out

    @patch("scripts.binary_manager.is_binary_installed", return_value=False)
    def test_check_not_installed(self, mock_installed, capsys):
        with patch("sys.argv", ["binary_manager", "check"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "not installed" in captured.out

    @patch("scripts.binary_manager.get_version", return_value="1.5.0")
    def test_version_command(self, mock_ver, capsys):
        with patch("sys.argv", ["binary_manager", "version"]):
            main()
        captured = capsys.readouterr()
        assert "1.5.0" in captured.out

    @patch("scripts.binary_manager.get_binary_path", return_value=Path("/bin/git-sizer"))
    def test_path_command(self, mock_path, capsys):
        with patch("sys.argv", ["binary_manager", "path"]):
            main()
        captured = capsys.readouterr()
        assert "git-sizer" in captured.out

    @patch("scripts.binary_manager.download")
    def test_download_command(self, mock_download):
        with patch("sys.argv", ["binary_manager", "download"]):
            main()
        mock_download.assert_called_once()
