"""Tests for execution backend abstraction."""
from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from execution import (
    ExecutionConfig,
    ExecutionMode,
    ExecutionResult,
    LocalBackend,
    ToolTask,
    _default_output_path,
    _is_git_commit,
    get_backend,
    run_tool_make,
)


# ---------------------------------------------------------------------------
# Dataclass tests
# ---------------------------------------------------------------------------

class TestToolTask:
    def test_frozen(self):
        task = ToolTask(name="scc", tool_root=Path("/t"))
        with pytest.raises(AttributeError):
            task.name = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

class TestDefaultOutputPath:
    def test_with_output_root(self, tmp_path: Path):
        task = ToolTask("scc", Path("/tools/scc"))
        result = _default_output_path(task, "run-1", tmp_path)
        assert result == (tmp_path / "scc" / "output.json").resolve()

    def test_without_output_root(self):
        task = ToolTask("scc", Path("/tools/scc"))
        result = _default_output_path(task, "run-1", None)
        assert result == Path("/tools/scc/outputs/run-1/output.json").resolve()


class TestIsGitCommit:
    def test_fallback_commit(self):
        assert _is_git_commit(Path("/tmp"), "0" * 40) is False

    def test_empty_commit(self):
        assert _is_git_commit(Path("/tmp"), "") is False


# ---------------------------------------------------------------------------
# run_tool_make tests
# ---------------------------------------------------------------------------

class TestRunToolMake:
    def test_sets_env_correctly(self, monkeypatch, tmp_path: Path):
        tool_root = tmp_path / "tool"
        tool_root.mkdir()
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        captured_env: dict[str, str] = {}

        def fake_run(cmd, **kwargs):
            if cmd[:2] == ["git", "-C"]:
                return subprocess.CompletedProcess(args=cmd, returncode=128)
            if cmd[:2] == ["make", "analyze"]:
                captured_env.update(kwargs.get("env", {}))
                return subprocess.CompletedProcess(args=cmd, returncode=0)
            raise AssertionError(f"Unexpected: {cmd}")

        monkeypatch.setattr(subprocess, "run", fake_run)

        sink = io.StringIO()
        run_tool_make(
            tool_root, repo_path, "repo", "run-1", "repo-1", "main",
            "a" * 40, tmp_path / "out", sink,
        )

        assert captured_env["REPO_PATH"] == str(repo_path)
        assert captured_env["RUN_ID"] == "run-1"
        assert captured_env["COMMIT"] == "0" * 40  # non-git → sentinel


# ---------------------------------------------------------------------------
# LocalBackend tests
# ---------------------------------------------------------------------------

class TestLocalBackend:
    def test_execute_batch_success(self, monkeypatch, tmp_path: Path):
        tool_root = tmp_path / "tool"
        tool_root.mkdir()
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        def fake_run(cmd, **kwargs):
            if cmd[:2] == ["git", "-C"]:
                return subprocess.CompletedProcess(args=cmd, returncode=128)
            if cmd[:2] == ["make", "analyze"]:
                # Simulate tool writing output
                out_dir = Path(kwargs["env"]["OUTPUT_DIR"])
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "output.json").write_text('{"data": {}}')
                return subprocess.CompletedProcess(args=cmd, returncode=0)
            raise AssertionError(f"Unexpected: {cmd}")

        monkeypatch.setattr(subprocess, "run", fake_run)

        backend = LocalBackend()
        config = ExecutionConfig(
            repo_path=repo_path,
            repo_name="repo",
            run_id="run-1",
            repo_id="repo-1",
            branch="main",
            commit="0" * 40,
            output_root=tmp_path / "outputs",
        )

        tasks = [ToolTask("test-tool", tool_root)]
        sink = io.StringIO()
        results = backend.execute_batch(tasks, config, sink)

        assert len(results) == 1
        assert results[0].status == "success"
        assert results[0].output_exists is True
        assert results[0].output_bytes > 0

    def test_execute_batch_failure(self, monkeypatch, tmp_path: Path):
        tool_root = tmp_path / "tool"
        tool_root.mkdir()
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        def fake_run(cmd, **kwargs):
            if cmd[:2] == ["git", "-C"]:
                return subprocess.CompletedProcess(args=cmd, returncode=128)
            if cmd[:2] == ["make", "analyze"]:
                raise subprocess.CalledProcessError(2, cmd)
            raise AssertionError(f"Unexpected: {cmd}")

        monkeypatch.setattr(subprocess, "run", fake_run)

        backend = LocalBackend()
        config = ExecutionConfig(
            repo_path=repo_path,
            repo_name="repo",
            run_id="run-1",
            repo_id="repo-1",
            branch="main",
            commit="0" * 40,
            output_root=tmp_path / "outputs",
        )

        tasks = [ToolTask("fail-tool", tool_root)]
        sink = io.StringIO()
        results = backend.execute_batch(tasks, config, sink)

        assert len(results) == 1
        assert results[0].status == "failed"
        assert results[0].error is not None

    def test_execute_batch_multiple(self, monkeypatch, tmp_path: Path):
        """Should execute multiple tasks sequentially."""
        tool1 = tmp_path / "t1"
        tool2 = tmp_path / "t2"
        tool1.mkdir()
        tool2.mkdir()
        repo = tmp_path / "repo"
        repo.mkdir()

        def fake_run(cmd, **kwargs):
            if cmd[:2] == ["git", "-C"]:
                return subprocess.CompletedProcess(args=cmd, returncode=128)
            if cmd[:2] == ["make", "analyze"]:
                out_dir = Path(kwargs["env"]["OUTPUT_DIR"])
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "output.json").write_text('{}')
                return subprocess.CompletedProcess(args=cmd, returncode=0)
            raise AssertionError(f"Unexpected: {cmd}")

        monkeypatch.setattr(subprocess, "run", fake_run)

        backend = LocalBackend()
        config = ExecutionConfig(
            repo_path=repo, repo_name="repo", run_id="run-1",
            repo_id="repo-1", branch="main", commit="0" * 40,
            output_root=tmp_path / "outputs",
        )

        tasks = [ToolTask("tool-a", tool1), ToolTask("tool-b", tool2)]
        results = backend.execute_batch(tasks, config, io.StringIO())

        assert len(results) == 2
        assert results[0].tool_name == "tool-a"
        assert results[1].tool_name == "tool-b"
        assert all(r.status == "success" for r in results)


# ---------------------------------------------------------------------------
# get_backend factory tests
# ---------------------------------------------------------------------------

class TestGetBackend:
    def test_local(self):
        backend = get_backend(ExecutionMode.LOCAL)
        assert isinstance(backend, LocalBackend)

    def test_invalid_mode_raises(self):
        """Passing a mode not handled by get_backend must raise ValueError."""
        # Create a fake enum member that get_backend does not support.
        # We cannot pass a raw string because the function expects ExecutionMode,
        # so we dynamically add a temporary member to exercise the else branch.
        import enum
        fake_mode = object.__new__(ExecutionMode)
        fake_mode._name_ = "FAKE"
        fake_mode._value_ = "fake"
        with pytest.raises(ValueError, match="Unsupported execution mode"):
            get_backend(fake_mode)
