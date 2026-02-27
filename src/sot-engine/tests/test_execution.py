"""Tests for execution backend abstraction."""
from __future__ import annotations

import io
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from execution import (
    DockerBackend,
    DockerConfig,
    ExecutionConfig,
    ExecutionMode,
    ExecutionResult,
    LocalBackend,
    ToolTask,
    _default_output_path,
    _execute_parallel,
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


class TestDockerConfig:
    def test_frozen(self):
        dc = DockerConfig()
        with pytest.raises(AttributeError):
            dc.image_prefix = "x"  # type: ignore[misc]

    def test_defaults(self):
        dc = DockerConfig()
        assert dc.image_prefix == "caldera-tool-"
        assert dc.network == "caldera_default"
        assert dc.repo_volume == "caldera-repo"
        assert dc.artifacts_volume == "caldera-artifacts"
        assert dc.container_repo_path == "/repo"
        assert dc.container_artifacts_path == "/artifacts"

    def test_custom_values(self):
        dc = DockerConfig(image_prefix="my-", network="my-net")
        assert dc.image_prefix == "my-"
        assert dc.network == "my-net"


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
# _execute_parallel tests
# ---------------------------------------------------------------------------

def _make_config(tmp_path: Path, max_parallel: int = 1) -> ExecutionConfig:
    return ExecutionConfig(
        repo_path=tmp_path / "repo",
        repo_name="repo",
        run_id="run-1",
        repo_id="repo-1",
        branch="main",
        commit="0" * 40,
        output_root=tmp_path / "outputs",
        max_parallel=max_parallel,
    )


class TestExecuteParallel:
    def test_sequential_fallback(self, tmp_path: Path):
        """max_parallel=1 runs tasks in order."""
        config = _make_config(tmp_path, max_parallel=1)
        tasks = [ToolTask(f"t{i}", tmp_path) for i in range(3)]
        order: list[str] = []

        def execute_one(task: ToolTask) -> ExecutionResult:
            order.append(task.name)
            return ExecutionResult(
                tool_name=task.name, status="success", duration_seconds=0.01,
                output_path=tmp_path / task.name / "output.json",
                output_exists=True, output_bytes=10,
            )

        results = _execute_parallel(tasks, config, execute_one)
        assert [r.tool_name for r in results] == ["t0", "t1", "t2"]
        assert order == ["t0", "t1", "t2"]

    def test_parallel(self, tmp_path: Path):
        """max_parallel=3 with 6 tasks — all complete."""
        config = _make_config(tmp_path, max_parallel=3)
        tasks = [ToolTask(f"t{i}", tmp_path) for i in range(6)]

        def execute_one(task: ToolTask) -> ExecutionResult:
            time.sleep(0.01)
            return ExecutionResult(
                tool_name=task.name, status="success", duration_seconds=0.01,
                output_path=tmp_path / task.name / "output.json",
                output_exists=True, output_bytes=10,
            )

        results = _execute_parallel(tasks, config, execute_one)
        assert len(results) == 6
        assert all(r.status == "success" for r in results)

    def test_callback_invoked(self, tmp_path: Path):
        """on_complete is called once per task."""
        config = _make_config(tmp_path, max_parallel=2)
        tasks = [ToolTask(f"t{i}", tmp_path) for i in range(3)]
        callbacks: list[tuple[str, str, float]] = []

        def execute_one(task: ToolTask) -> ExecutionResult:
            return ExecutionResult(
                tool_name=task.name, status="success", duration_seconds=0.01,
                output_path=tmp_path / task.name / "output.json",
                output_exists=True, output_bytes=10,
            )

        def on_complete(name: str, status: str, dur: float) -> None:
            callbacks.append((name, status, dur))

        _execute_parallel(tasks, config, execute_one, on_complete)
        assert len(callbacks) == 3
        assert {c[0] for c in callbacks} == {"t0", "t1", "t2"}

    def test_exception_produces_failed_result(self, tmp_path: Path):
        """An exception in execute_one yields a failed result; others succeed."""
        config = _make_config(tmp_path, max_parallel=2)
        tasks = [ToolTask("ok", tmp_path), ToolTask("boom", tmp_path)]

        def execute_one(task: ToolTask) -> ExecutionResult:
            if task.name == "boom":
                raise RuntimeError("kaboom")
            return ExecutionResult(
                tool_name=task.name, status="success", duration_seconds=0.01,
                output_path=tmp_path / task.name / "output.json",
                output_exists=True, output_bytes=10,
            )

        results = _execute_parallel(tasks, config, execute_one)
        by_name = {r.tool_name: r for r in results}
        assert by_name["ok"].status == "success"
        assert by_name["boom"].status == "failed"
        assert "kaboom" in by_name["boom"].error

    def test_order_preserved(self, tmp_path: Path):
        """Results are in original task order regardless of completion order."""
        config = _make_config(tmp_path, max_parallel=4)
        tasks = [ToolTask(f"t{i}", tmp_path) for i in range(8)]

        def execute_one(task: ToolTask) -> ExecutionResult:
            # Vary sleep so completion order differs from submission order
            time.sleep(0.02 if int(task.name[1]) % 2 == 0 else 0.01)
            return ExecutionResult(
                tool_name=task.name, status="success", duration_seconds=0.01,
                output_path=tmp_path / task.name / "output.json",
                output_exists=True, output_bytes=10,
            )

        results = _execute_parallel(tasks, config, execute_one)
        assert [r.tool_name for r in results] == [f"t{i}" for i in range(8)]

    def test_sequential_exception_produces_failed_result(self, tmp_path: Path):
        """Sequential path (max_parallel=1) also catches exceptions."""
        config = _make_config(tmp_path, max_parallel=1)
        tasks = [ToolTask("boom", tmp_path)]

        def execute_one(task: ToolTask) -> ExecutionResult:
            raise RuntimeError("fail")

        results = _execute_parallel(tasks, config, execute_one)
        assert len(results) == 1
        assert results[0].status == "failed"
        assert "fail" in results[0].error


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

    def test_execute_batch_parallel(self, monkeypatch, tmp_path: Path):
        """Should execute tasks in parallel when max_parallel > 1."""
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
            max_parallel=2,
        )

        tasks = [ToolTask("tool-a", tool1), ToolTask("tool-b", tool2)]
        results = backend.execute_batch(tasks, config, io.StringIO())

        assert len(results) == 2
        assert {r.tool_name for r in results} == {"tool-a", "tool-b"}
        assert all(r.status == "success" for r in results)


# ---------------------------------------------------------------------------
# DockerBackend tests
# ---------------------------------------------------------------------------

class TestDockerBackend:
    def test_success(self, monkeypatch, tmp_path: Path):
        """Mock docker run returning 0 with output.json present."""
        def fake_run(cmd, **kwargs):
            if cmd[0] == "docker":
                # Simulate the tool writing output.json
                # In real usage the container writes to a volume; here we write to output_root
                out_dir = tmp_path / "outputs" / "test-tool"
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "output.json").write_text('{"data": {}}')
                return subprocess.CompletedProcess(
                    args=cmd, returncode=0,
                    stdout=b"ok\n", stderr=b"",
                )
            raise AssertionError(f"Unexpected: {cmd}")

        monkeypatch.setattr(subprocess, "run", fake_run)

        backend = DockerBackend()
        config = ExecutionConfig(
            repo_path=tmp_path / "repo",
            repo_name="repo",
            run_id="run-1",
            repo_id="repo-1",
            branch="main",
            commit="0" * 40,
            output_root=tmp_path / "outputs",
        )

        tasks = [ToolTask("test-tool", tmp_path / "tool")]
        results = backend.execute_batch(tasks, config, io.StringIO())

        assert len(results) == 1
        assert results[0].status == "success"
        assert results[0].output_exists is True
        assert results[0].output_bytes > 0

    def test_failure(self, monkeypatch, tmp_path: Path):
        """Mock docker run returning non-zero."""
        def fake_run(cmd, **kwargs):
            if cmd[0] == "docker":
                return subprocess.CompletedProcess(
                    args=cmd, returncode=1,
                    stdout=b"", stderr=b"error\n",
                )
            raise AssertionError(f"Unexpected: {cmd}")

        monkeypatch.setattr(subprocess, "run", fake_run)

        backend = DockerBackend()
        config = ExecutionConfig(
            repo_path=tmp_path / "repo",
            repo_name="repo",
            run_id="run-1",
            repo_id="repo-1",
            branch="main",
            commit="0" * 40,
            output_root=tmp_path / "outputs",
        )

        tasks = [ToolTask("fail-tool", tmp_path / "tool")]
        results = backend.execute_batch(tasks, config, io.StringIO())

        assert len(results) == 1
        assert results[0].status == "failed"
        assert results[0].returncode == 1
        assert "Container exited with code 1" in results[0].error

    def test_command_construction(self, monkeypatch, tmp_path: Path):
        """Verify volume mounts, network, and image name in docker run command."""
        captured_cmd: list[str] = []

        def fake_run(cmd, **kwargs):
            if cmd[0] == "docker":
                captured_cmd.extend(cmd)
                # Write output.json so the result is success
                out_dir = tmp_path / "outputs" / "scc"
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "output.json").write_text('{}')
                return subprocess.CompletedProcess(
                    args=cmd, returncode=0,
                    stdout=b"", stderr=b"",
                )
            raise AssertionError(f"Unexpected: {cmd}")

        monkeypatch.setattr(subprocess, "run", fake_run)

        dc = DockerConfig(
            image_prefix="my-prefix-",
            network="my-net",
            repo_volume="my-repo-vol",
            artifacts_volume="my-art-vol",
        )
        backend = DockerBackend(dc)
        config = ExecutionConfig(
            repo_path=tmp_path / "repo",
            repo_name="repo",
            run_id="run-1",
            repo_id="repo-1",
            branch="main",
            commit="abc123",
            output_root=tmp_path / "outputs",
        )

        backend.execute_batch([ToolTask("scc", tmp_path)], config, io.StringIO())

        assert "docker" in captured_cmd[0]
        assert "--network" in captured_cmd
        net_idx = captured_cmd.index("--network")
        assert captured_cmd[net_idx + 1] == "my-net"

        # Check volume mounts
        assert "my-repo-vol:/repo:ro" in " ".join(captured_cmd)
        assert "my-art-vol:/artifacts" in " ".join(captured_cmd)

        # Check image name
        assert "my-prefix-scc" in captured_cmd

        # Check env args passed to container
        assert "RUN_ID=run-1" in captured_cmd
        assert "REPO_ID=repo-1" in captured_cmd
        assert "BRANCH=main" in captured_cmd
        assert "COMMIT=abc123" in captured_cmd

    def test_custom_config(self, monkeypatch, tmp_path: Path):
        """Non-default DockerConfig is reflected in the command."""
        captured_cmd: list[str] = []

        def fake_run(cmd, **kwargs):
            if cmd[0] == "docker":
                captured_cmd.extend(cmd)
                out_dir = tmp_path / "outputs" / "lizard"
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "output.json").write_text('{}')
                return subprocess.CompletedProcess(
                    args=cmd, returncode=0,
                    stdout=b"", stderr=b"",
                )
            raise AssertionError(f"Unexpected: {cmd}")

        monkeypatch.setattr(subprocess, "run", fake_run)

        dc = DockerConfig(
            image_prefix="custom-tool-",
            network="custom-net",
            repo_volume="custom-repo",
            artifacts_volume="custom-art",
            container_repo_path="/data/repo",
            container_artifacts_path="/data/artifacts",
        )
        backend = DockerBackend(dc)
        config = ExecutionConfig(
            repo_path=tmp_path / "repo",
            repo_name="repo",
            run_id="run-1",
            repo_id="repo-1",
            branch="main",
            commit="0" * 40,
            output_root=tmp_path / "outputs",
        )

        backend.execute_batch([ToolTask("lizard", tmp_path)], config, io.StringIO())

        cmd_str = " ".join(captured_cmd)
        assert "custom-tool-lizard" in cmd_str
        assert "custom-net" in cmd_str
        assert "custom-repo:/data/repo:ro" in cmd_str
        assert "custom-art:/data/artifacts" in cmd_str

    def test_missing_output_after_success(self, monkeypatch, tmp_path: Path):
        """Container exits 0 but doesn't write output.json → failed result."""
        def fake_run(cmd, **kwargs):
            if cmd[0] == "docker":
                # Don't write output.json
                out_dir = tmp_path / "outputs" / "bad-tool"
                out_dir.mkdir(parents=True, exist_ok=True)
                return subprocess.CompletedProcess(
                    args=cmd, returncode=0,
                    stdout=b"", stderr=b"",
                )
            raise AssertionError(f"Unexpected: {cmd}")

        monkeypatch.setattr(subprocess, "run", fake_run)

        backend = DockerBackend()
        config = ExecutionConfig(
            repo_path=tmp_path / "repo",
            repo_name="repo",
            run_id="run-1",
            repo_id="repo-1",
            branch="main",
            commit="0" * 40,
            output_root=tmp_path / "outputs",
        )

        results = backend.execute_batch(
            [ToolTask("bad-tool", tmp_path)], config, io.StringIO(),
        )
        assert len(results) == 1
        assert results[0].status == "failed"
        assert "did not produce output" in results[0].error


# ---------------------------------------------------------------------------
# get_backend factory tests
# ---------------------------------------------------------------------------

class TestGetBackend:
    def test_local(self):
        backend = get_backend(ExecutionMode.LOCAL)
        assert isinstance(backend, LocalBackend)

    def test_docker(self):
        backend = get_backend(ExecutionMode.DOCKER)
        assert isinstance(backend, DockerBackend)

    def test_docker_with_config(self):
        dc = DockerConfig(image_prefix="test-", network="test-net")
        backend = get_backend(ExecutionMode.DOCKER, docker_config=dc)
        assert isinstance(backend, DockerBackend)
        assert backend._dc.image_prefix == "test-"
        assert backend._dc.network == "test-net"

    def test_invalid_mode_raises(self):
        """Passing a mode not handled by get_backend must raise ValueError."""
        fake_mode = object.__new__(ExecutionMode)
        fake_mode._name_ = "FAKE"
        fake_mode._value_ = "fake"
        with pytest.raises(ValueError, match="Unsupported execution mode"):
            get_backend(fake_mode)
