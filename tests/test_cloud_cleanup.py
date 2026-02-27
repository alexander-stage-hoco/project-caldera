"""Tests for scripts/cloud_cleanup.py — orphan VM cleanup."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts/ to import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from cloud_cleanup import destroy_server, list_caldera_servers, main, server_age_hours


def _iso_now_minus(hours: float) -> str:
    """Return an ISO timestamp *hours* in the past."""
    dt = datetime.now(timezone.utc) - timedelta(hours=hours)
    return dt.isoformat()


def _make_server(name: str = "caldera-abc", server_id: int = 42, hours_old: float = 1.0) -> dict:
    return {
        "id": server_id,
        "name": name,
        "status": "running",
        "created": _iso_now_minus(hours_old),
        "server_type": {"name": "cx33"},
    }


class TestServerAgeHours:
    def test_recent_server(self) -> None:
        server = _make_server(hours_old=2.0)
        age = server_age_hours(server)
        assert 1.9 < age < 2.2  # allow small timing drift

    def test_missing_created(self) -> None:
        assert server_age_hours({"created": ""}) == 0.0

    def test_invalid_timestamp(self) -> None:
        assert server_age_hours({"created": "not-a-date"}) == 0.0


class TestListCalderaServers:
    @patch("cloud_cleanup._run_hcloud")
    def test_returns_parsed_servers(self, mock_hcloud: MagicMock) -> None:
        servers = [_make_server()]
        mock_hcloud.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=json.dumps(servers), stderr="",
        )
        result = list_caldera_servers()
        assert len(result) == 1
        assert result[0]["name"] == "caldera-abc"

    @patch("cloud_cleanup._run_hcloud")
    def test_hcloud_failure(self, mock_hcloud: MagicMock) -> None:
        mock_hcloud.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="auth error",
        )
        assert list_caldera_servers() == []


class TestDestroyServer:
    @patch("cloud_cleanup._run_hcloud")
    def test_success(self, mock_hcloud: MagicMock) -> None:
        mock_hcloud.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        assert destroy_server(42, "caldera-abc") is True

    @patch("cloud_cleanup._run_hcloud")
    def test_failure(self, mock_hcloud: MagicMock) -> None:
        mock_hcloud.return_value = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="error")
        assert destroy_server(42, "caldera-abc") is False


class TestMain:
    @patch("cloud_cleanup.shutil.which", return_value=None)
    def test_missing_hcloud_cli(self, _mock_which: MagicMock) -> None:
        sys.argv = ["cloud_cleanup.py"]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    @patch("cloud_cleanup.list_caldera_servers", return_value=[])
    @patch("cloud_cleanup.shutil.which", return_value="/usr/local/bin/hcloud")
    def test_no_servers_found(self, _w: MagicMock, _l: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
        sys.argv = ["cloud_cleanup.py"]
        main()
        assert "No Caldera servers found" in capsys.readouterr().out

    @patch("cloud_cleanup.list_caldera_servers")
    @patch("cloud_cleanup.shutil.which", return_value="/usr/local/bin/hcloud")
    def test_no_orphaned_servers(self, _w: MagicMock, mock_list: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
        mock_list.return_value = [_make_server(hours_old=1.0)]
        sys.argv = ["cloud_cleanup.py", "--ttl-hours", "4"]
        main()
        assert "No orphaned servers to destroy" in capsys.readouterr().out

    @patch("cloud_cleanup.destroy_server")
    @patch("cloud_cleanup.list_caldera_servers")
    @patch("cloud_cleanup.shutil.which", return_value="/usr/local/bin/hcloud")
    def test_dry_run_lists_orphans(
        self, _w: MagicMock, mock_list: MagicMock, mock_destroy: MagicMock, capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_list.return_value = [_make_server(hours_old=10.0)]
        sys.argv = ["cloud_cleanup.py", "--ttl-hours", "4", "--dry-run"]
        main()
        output = capsys.readouterr().out
        assert "[DRY RUN]" in output
        mock_destroy.assert_not_called()

    @patch("cloud_cleanup.destroy_server", return_value=True)
    @patch("cloud_cleanup.list_caldera_servers")
    @patch("cloud_cleanup.shutil.which", return_value="/usr/local/bin/hcloud")
    def test_destroy_orphaned_servers(
        self, _w: MagicMock, mock_list: MagicMock, mock_destroy: MagicMock, capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_list.return_value = [_make_server(name="caldera-old", server_id=99, hours_old=10.0)]
        sys.argv = ["cloud_cleanup.py", "--ttl-hours", "4"]
        main()
        mock_destroy.assert_called_once_with(99, "caldera-old")
        assert "Destroyed 1/1" in capsys.readouterr().out
