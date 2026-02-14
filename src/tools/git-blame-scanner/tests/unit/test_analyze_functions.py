"""Unit tests for git-blame-scanner analyze.py functions.

Tests cover the uncovered logic in analyze.py:
- compute_content_hash: deterministic hashing for non-git repos
- resolve_commit: commit resolution with fallback
- get_tracked_files: git ls-files wrapper
- get_file_blame_stats: blame parsing (porcelain format)
- get_file_last_modified: last-modified date extraction
- get_commit_activity: churn map building
- analyze_file: single-file analysis pipeline
- analyze_repo: full repo analysis with summary/silo computation
- main: CLI entry point
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from scripts.analyze import (
    FileBlameStats,
    compute_content_hash,
    resolve_commit,
    get_tracked_files,
    get_file_blame_stats,
    get_file_last_modified,
    get_commit_activity,
    analyze_file,
    analyze_repo,
    compute_author_stats,
    main,
)


# ---------------------------------------------------------------------------
# compute_content_hash
# ---------------------------------------------------------------------------

class TestComputeContentHash:
    """Tests for compute_content_hash."""

    def test_hash_is_deterministic(self, tmp_path: Path):
        """Same files should produce the same hash."""
        (tmp_path / "a.py").write_text("hello")
        (tmp_path / "b.py").write_text("world")

        h1 = compute_content_hash(tmp_path)
        h2 = compute_content_hash(tmp_path)
        assert h1 == h2

    def test_hash_changes_with_content(self, tmp_path: Path):
        """Different content should produce different hashes."""
        (tmp_path / "a.py").write_text("hello")
        h1 = compute_content_hash(tmp_path)

        (tmp_path / "a.py").write_text("goodbye")
        h2 = compute_content_hash(tmp_path)
        assert h1 != h2

    def test_hash_is_40_hex_chars(self, tmp_path: Path):
        """Hash should be a valid SHA-1 hex digest (40 chars)."""
        (tmp_path / "f.txt").write_text("data")
        h = compute_content_hash(tmp_path)
        assert len(h) == 40
        assert all(c in "0123456789abcdef" for c in h)

    def test_skips_git_directory(self, tmp_path: Path):
        """Files inside .git/ should be ignored."""
        (tmp_path / "a.py").write_text("code")
        git_dir = tmp_path / ".git" / "objects"
        git_dir.mkdir(parents=True)
        (git_dir / "pack").write_text("binary junk")

        h_with_git = compute_content_hash(tmp_path)

        # Remove .git and recompute -- should be the same
        import shutil
        shutil.rmtree(tmp_path / ".git")
        h_without_git = compute_content_hash(tmp_path)
        assert h_with_git == h_without_git

    def test_empty_directory(self, tmp_path: Path):
        """An empty directory should still produce a valid hash."""
        h = compute_content_hash(tmp_path)
        assert len(h) == 40

    def test_skips_unreadable_files(self, tmp_path: Path):
        """Files that raise OSError on read should be skipped gracefully."""
        (tmp_path / "ok.py").write_text("fine")
        bad_file = tmp_path / "bad.bin"
        bad_file.write_text("data")

        # Make the file unreadable by mocking Path.read_bytes
        with patch.object(Path, "read_bytes", side_effect=[b"fine", OSError("perm denied")]):
            h = compute_content_hash(tmp_path)
            assert len(h) == 40


# ---------------------------------------------------------------------------
# resolve_commit
# ---------------------------------------------------------------------------

class TestResolveCommit:
    """Tests for resolve_commit."""

    def test_explicit_40char_sha_returned_as_is(self, tmp_path: Path):
        """A 40-char commit arg is returned directly."""
        sha = "a" * 40
        assert resolve_commit(tmp_path, sha) == sha

    def test_short_commit_arg_triggers_git_call(self, tmp_path: Path):
        """Non-40-char commit falls through to git rev-parse."""
        expected = "b" * 40
        proc = MagicMock(stdout=f"  {expected}  \n", returncode=0)
        with patch("scripts.analyze.subprocess.run", return_value=proc) as mock_run:
            result = resolve_commit(tmp_path, "abc123")
        assert result == expected
        mock_run.assert_called_once()

    def test_none_commit_arg_triggers_git_call(self, tmp_path: Path):
        """None commit falls through to git rev-parse."""
        expected = "c" * 40
        proc = MagicMock(stdout=f"{expected}\n", returncode=0)
        with patch("scripts.analyze.subprocess.run", return_value=proc):
            result = resolve_commit(tmp_path, None)
        assert result == expected

    def test_git_failure_falls_back_to_content_hash(self, tmp_path: Path):
        """CalledProcessError triggers content hash fallback."""
        (tmp_path / "x.py").write_text("x")
        with patch(
            "scripts.analyze.subprocess.run",
            side_effect=subprocess.CalledProcessError(128, "git"),
        ):
            result = resolve_commit(tmp_path, None)
        # Should be a valid 40-char SHA-1 from content hash
        assert len(result) == 40


# ---------------------------------------------------------------------------
# get_tracked_files
# ---------------------------------------------------------------------------

class TestGetTrackedFiles:
    """Tests for get_tracked_files."""

    def test_returns_file_list(self, tmp_path: Path):
        """Parses newline-separated git ls-files output."""
        proc = MagicMock(stdout="src/a.py\nsrc/b.py\nREADME.md\n", returncode=0)
        with patch("scripts.analyze.subprocess.run", return_value=proc):
            files = get_tracked_files(tmp_path)
        assert files == ["src/a.py", "src/b.py", "README.md"]

    def test_filters_empty_lines(self, tmp_path: Path):
        """Empty lines in output should be removed."""
        proc = MagicMock(stdout="a.py\n\n\nb.py\n\n", returncode=0)
        with patch("scripts.analyze.subprocess.run", return_value=proc):
            files = get_tracked_files(tmp_path)
        assert files == ["a.py", "b.py"]

    def test_empty_repo_returns_empty_list(self, tmp_path: Path):
        """Empty git output returns empty list."""
        proc = MagicMock(stdout="", returncode=0)
        with patch("scripts.analyze.subprocess.run", return_value=proc):
            files = get_tracked_files(tmp_path)
        assert files == []


# ---------------------------------------------------------------------------
# get_file_blame_stats
# ---------------------------------------------------------------------------

class TestGetFileBlameStats:
    """Tests for git blame porcelain parsing."""

    def _make_porcelain(self, entries: list[tuple[str, str]]) -> bytes:
        """Build minimal --line-porcelain output.

        entries: list of (author_email, content_line)
        """
        lines = []
        for i, (email, content) in enumerate(entries):
            lines.append(f"abcd1234 {i+1} {i+1} 1")
            lines.append(f"author-mail <{email}>")
            lines.append(f"\t{content}")
        return "\n".join(lines).encode("utf-8")

    def test_single_author(self, tmp_path: Path):
        """Single author gets all lines."""
        porcelain = self._make_porcelain([
            ("alice@ex.com", "line 1"),
            ("alice@ex.com", "line 2"),
            ("alice@ex.com", "line 3"),
        ])
        proc = MagicMock(stdout=porcelain, returncode=0)
        with patch("scripts.analyze.subprocess.run", return_value=proc):
            result = get_file_blame_stats(tmp_path, "src/main.py")
        assert result == {"alice@ex.com": 3}

    def test_multiple_authors(self, tmp_path: Path):
        """Multiple authors get correct line counts."""
        porcelain = self._make_porcelain([
            ("alice@ex.com", "line 1"),
            ("bob@ex.com", "line 2"),
            ("alice@ex.com", "line 3"),
            ("carol@ex.com", "line 4"),
        ])
        proc = MagicMock(stdout=porcelain, returncode=0)
        with patch("scripts.analyze.subprocess.run", return_value=proc):
            result = get_file_blame_stats(tmp_path, "f.py")
        assert result == {"alice@ex.com": 2, "bob@ex.com": 1, "carol@ex.com": 1}

    def test_binary_file_returns_none(self, tmp_path: Path):
        """CalledProcessError (binary file) returns None."""
        with patch(
            "scripts.analyze.subprocess.run",
            side_effect=subprocess.CalledProcessError(128, "git blame"),
        ):
            assert get_file_blame_stats(tmp_path, "img.png") is None

    def test_empty_blame_returns_none(self, tmp_path: Path):
        """Empty blame output (no author-mail lines) returns None."""
        proc = MagicMock(stdout=b"", returncode=0)
        with patch("scripts.analyze.subprocess.run", return_value=proc):
            assert get_file_blame_stats(tmp_path, "empty.py") is None

    def test_email_angle_brackets_stripped(self, tmp_path: Path):
        """Angle brackets around email are stripped."""
        porcelain = self._make_porcelain([
            ("user@domain.com", "code"),
        ])
        proc = MagicMock(stdout=porcelain, returncode=0)
        with patch("scripts.analyze.subprocess.run", return_value=proc):
            result = get_file_blame_stats(tmp_path, "f.py")
        assert "user@domain.com" in result


# ---------------------------------------------------------------------------
# get_file_last_modified
# ---------------------------------------------------------------------------

class TestGetFileLastModified:
    """Tests for get_file_last_modified."""

    def test_returns_date_string(self, tmp_path: Path):
        """Normal git log output returns a date string."""
        proc = MagicMock(stdout="2025-06-15\n", returncode=0)
        with patch("scripts.analyze.subprocess.run", return_value=proc):
            result = get_file_last_modified(tmp_path, "src/main.py")
        assert result == "2025-06-15"

    def test_empty_output_returns_none(self, tmp_path: Path):
        """Empty git log output returns None."""
        proc = MagicMock(stdout="\n", returncode=0)
        with patch("scripts.analyze.subprocess.run", return_value=proc):
            result = get_file_last_modified(tmp_path, "nonexistent.py")
        assert result is None

    def test_error_returns_none(self, tmp_path: Path):
        """CalledProcessError returns None."""
        with patch(
            "scripts.analyze.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "git log"),
        ):
            assert get_file_last_modified(tmp_path, "bad.py") is None


# ---------------------------------------------------------------------------
# get_commit_activity
# ---------------------------------------------------------------------------

class TestGetCommitActivity:
    """Tests for churn map building."""

    def test_counts_file_commits(self, tmp_path: Path):
        """Multiple mentions of same file increments count."""
        output = "src/a.py\nsrc/b.py\n\nsrc/a.py\n\nsrc/a.py\n"
        proc = MagicMock(stdout=output, returncode=0)
        with patch("scripts.analyze.subprocess.run", return_value=proc):
            result = get_commit_activity(tmp_path, 30)
        assert result == {"src/a.py": 3, "src/b.py": 1}

    def test_empty_history(self, tmp_path: Path):
        """No commits in the window returns empty dict."""
        proc = MagicMock(stdout="\n", returncode=0)
        with patch("scripts.analyze.subprocess.run", return_value=proc):
            result = get_commit_activity(tmp_path, 90)
        assert result == {}

    def test_git_error_returns_empty_dict(self, tmp_path: Path):
        """CalledProcessError returns empty dict."""
        with patch(
            "scripts.analyze.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "git log"),
        ):
            result = get_commit_activity(tmp_path, 30)
        assert result == {}


# ---------------------------------------------------------------------------
# analyze_file
# ---------------------------------------------------------------------------

class TestAnalyzeFile:
    """Tests for analyze_file which orchestrates blame + churn."""

    def test_normal_file(self, tmp_path: Path):
        """Happy path: blame data + churn maps produce FileBlameStats."""
        blame_data = {"alice@ex.com": 80, "bob@ex.com": 20}
        churn_30d = {"src/main.py": 3}
        churn_90d = {"src/main.py": 7}

        with patch("scripts.analyze.get_file_blame_stats", return_value=blame_data), \
             patch("scripts.analyze.get_file_last_modified", return_value="2025-06-01"):
            result = analyze_file(tmp_path, "src/main.py", churn_30d, churn_90d)

        assert result is not None
        assert result.relative_path == "src/main.py"
        assert result.total_lines == 100
        assert result.unique_authors == 2
        assert result.top_author == "alice@ex.com"
        assert result.top_author_lines == 80
        assert result.top_author_pct == 80.0
        assert result.churn_30d == 3
        assert result.churn_90d == 7
        assert result.last_modified == "2025-06-01"

    def test_no_blame_returns_none(self, tmp_path: Path):
        """If blame returns None, analyze_file returns None."""
        with patch("scripts.analyze.get_file_blame_stats", return_value=None):
            result = analyze_file(tmp_path, "binary.png", {}, {})
        assert result is None

    def test_missing_churn_defaults_to_zero(self, tmp_path: Path):
        """Files not in churn maps default to 0."""
        blame_data = {"alice@ex.com": 50}
        with patch("scripts.analyze.get_file_blame_stats", return_value=blame_data), \
             patch("scripts.analyze.get_file_last_modified", return_value="2025-01-01"):
            result = analyze_file(tmp_path, "quiet.py", {}, {})

        assert result is not None
        assert result.churn_30d == 0
        assert result.churn_90d == 0

    def test_last_modified_unknown_fallback(self, tmp_path: Path):
        """If last_modified is None, falls back to 'unknown'."""
        blame_data = {"alice@ex.com": 10}
        with patch("scripts.analyze.get_file_blame_stats", return_value=blame_data), \
             patch("scripts.analyze.get_file_last_modified", return_value=None):
            result = analyze_file(tmp_path, "orphan.py", {}, {})

        assert result is not None
        assert result.last_modified == "unknown"

    def test_single_author_ownership_100(self, tmp_path: Path):
        """Single-author file has top_author_pct == 100."""
        blame_data = {"sole@owner.com": 200}
        with patch("scripts.analyze.get_file_blame_stats", return_value=blame_data), \
             patch("scripts.analyze.get_file_last_modified", return_value="2025-03-15"):
            result = analyze_file(tmp_path, "solo.py", {}, {})

        assert result is not None
        assert result.unique_authors == 1
        assert result.top_author_pct == 100.0


# ---------------------------------------------------------------------------
# analyze_repo
# ---------------------------------------------------------------------------

class TestAnalyzeRepo:
    """Tests for the full repo analysis."""

    def _make_stats(
        self,
        path: str,
        total_lines: int,
        unique_authors: int,
        top_author: str,
        top_pct: float,
        churn_30d: int = 0,
        churn_90d: int = 0,
        last_modified: str = "2025-01-01",
        authors: dict[str, int] | None = None,
    ) -> FileBlameStats:
        if authors is None:
            authors = {top_author: total_lines}
        return FileBlameStats(
            relative_path=path,
            total_lines=total_lines,
            unique_authors=unique_authors,
            top_author=top_author,
            top_author_lines=int(total_lines * top_pct / 100),
            top_author_pct=top_pct,
            last_modified=last_modified,
            churn_30d=churn_30d,
            churn_90d=churn_90d,
            authors=authors,
        )

    def test_summary_metrics(self, tmp_path: Path):
        """Tests summary counters: single-author, high-concentration, stale, silos."""
        stats_list = [
            # Single author, >100 lines => knowledge silo
            self._make_stats("big_solo.py", 150, 1, "alice@ex.com", 100.0,
                             churn_90d=0, last_modified="2024-01-01"),
            # Single author, <100 lines => NOT a silo
            self._make_stats("small_solo.py", 50, 1, "alice@ex.com", 100.0,
                             churn_90d=2),
            # Multiple authors, high concentration >= 80%
            self._make_stats("concentrated.py", 200, 2, "alice@ex.com", 90.0,
                             churn_30d=1, churn_90d=3,
                             authors={"alice@ex.com": 180, "bob@ex.com": 20}),
            # Multiple authors, low concentration
            self._make_stats("balanced.py", 100, 3, "carol@ex.com", 40.0,
                             churn_30d=5, churn_90d=10,
                             authors={"carol@ex.com": 40, "alice@ex.com": 30, "bob@ex.com": 30}),
        ]

        with patch("scripts.analyze.get_tracked_files", return_value=[s.relative_path for s in stats_list]), \
             patch("scripts.analyze.get_commit_activity", return_value={}), \
             patch("scripts.analyze.analyze_file", side_effect=stats_list), \
             patch("scripts.analyze.normalize_file_path", side_effect=lambda p, r: p):
            data = analyze_repo(tmp_path)

        summary = data["summary"]
        assert summary["total_files_analyzed"] == 4
        # single-author files: big_solo.py, small_solo.py
        assert summary["single_author_files"] == 2
        assert summary["single_author_pct"] == 50.0
        # high-concentration files (>=80%): big_solo.py (100%), small_solo.py (100%), concentrated.py (90%)
        assert summary["high_concentration_files"] == 3
        # stale: churn_90d==0 and last_modified != "unknown" => big_solo.py
        assert summary["stale_files_90d"] == 1
        # knowledge silos: single author AND >100 lines => big_solo.py
        assert summary["knowledge_silo_count"] == 1
        assert "big_solo.py" in data["knowledge_silos"]

    def test_empty_repo(self, tmp_path: Path):
        """Repo with no tracked files produces empty-but-valid data."""
        with patch("scripts.analyze.get_tracked_files", return_value=[]), \
             patch("scripts.analyze.get_commit_activity", return_value={}), \
             patch("scripts.analyze.normalize_file_path", side_effect=lambda p, r: p):
            data = analyze_repo(tmp_path)

        assert data["files"] == []
        assert data["authors"] == []
        assert data["summary"]["total_files_analyzed"] == 0
        assert data["summary"]["single_author_pct"] == 0
        assert data["summary"]["avg_authors_per_file"] == 0

    def test_authors_sorted_by_total_lines_descending(self, tmp_path: Path):
        """Author list should be sorted by total_lines descending."""
        stats_list = [
            self._make_stats("a.py", 100, 2, "alice@ex.com", 60.0,
                             authors={"alice@ex.com": 60, "bob@ex.com": 40}),
            self._make_stats("b.py", 200, 2, "bob@ex.com", 75.0,
                             authors={"bob@ex.com": 150, "alice@ex.com": 50}),
        ]

        with patch("scripts.analyze.get_tracked_files", return_value=["a.py", "b.py"]), \
             patch("scripts.analyze.get_commit_activity", return_value={}), \
             patch("scripts.analyze.analyze_file", side_effect=stats_list), \
             patch("scripts.analyze.normalize_file_path", side_effect=lambda p, r: p):
            data = analyze_repo(tmp_path)

        # bob has 190 lines, alice has 110 => bob first
        assert data["authors"][0]["author_email"] == "bob@ex.com"
        assert data["authors"][1]["author_email"] == "alice@ex.com"

    def test_knowledge_silos_capped_at_20(self, tmp_path: Path):
        """At most 20 knowledge silos are reported."""
        stats_list = [
            self._make_stats(f"silo_{i}.py", 200, 1, "alice@ex.com", 100.0)
            for i in range(25)
        ]

        with patch("scripts.analyze.get_tracked_files", return_value=[s.relative_path for s in stats_list]), \
             patch("scripts.analyze.get_commit_activity", return_value={}), \
             patch("scripts.analyze.analyze_file", side_effect=stats_list), \
             patch("scripts.analyze.normalize_file_path", side_effect=lambda p, r: p):
            data = analyze_repo(tmp_path)

        assert len(data["knowledge_silos"]) == 20
        assert data["summary"]["knowledge_silo_count"] == 25


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

class TestMain:
    """Tests for the CLI entry point."""

    def test_missing_repo_path(self, tmp_path: Path):
        """Non-existent repo path returns exit code 1."""
        bad_path = tmp_path / "nonexistent"
        args = [
            "--repo-path", str(bad_path),
            "--repo-name", "test",
            "--output-dir", str(tmp_path / "out"),
            "--run-id", "r1",
            "--repo-id", "test",
        ]
        with patch("sys.argv", ["analyze.py"] + args):
            rc = main()
        assert rc == 1

    def test_not_a_git_repo(self, tmp_path: Path):
        """Directory without .git returns exit code 1."""
        args = [
            "--repo-path", str(tmp_path),
            "--repo-name", "test",
            "--output-dir", str(tmp_path / "out"),
            "--run-id", "r1",
            "--repo-id", "test",
        ]
        with patch("sys.argv", ["analyze.py"] + args):
            rc = main()
        assert rc == 1

    def test_successful_run_writes_output(self, tmp_path: Path):
        """Happy path: main writes output.json and returns 0."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()  # Fake .git

        out_dir = tmp_path / "out"
        args = [
            "--repo-path", str(repo),
            "--repo-name", "test-repo",
            "--output-dir", str(out_dir),
            "--run-id", "run-1",
            "--repo-id", "test-repo",
            "--commit", "a" * 40,
        ]

        fake_data = {
            "tool": "git-blame-scanner",
            "tool_version": "1.0.0",
            "files": [],
            "authors": [],
            "summary": {
                "total_files_analyzed": 0,
                "total_authors": 0,
                "single_author_files": 0,
                "single_author_pct": 0,
                "high_concentration_files": 0,
                "high_concentration_pct": 0,
                "stale_files_90d": 0,
                "knowledge_silo_count": 0,
                "avg_authors_per_file": 0,
            },
            "knowledge_silos": [],
        }

        with patch("sys.argv", ["analyze.py"] + args), \
             patch("scripts.analyze.analyze_repo", return_value=fake_data):
            rc = main()

        assert rc == 0
        output_path = out_dir / "output.json"
        assert output_path.exists()
        envelope = json.loads(output_path.read_text())
        assert envelope["metadata"]["tool_name"] == "git-blame-scanner"
        assert envelope["metadata"]["commit"] == "a" * 40
        assert envelope["data"] == fake_data
