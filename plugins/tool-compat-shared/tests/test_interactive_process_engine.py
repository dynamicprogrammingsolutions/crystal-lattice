"""Tests for the interactive process engine (unified exec sessions)."""

from __future__ import annotations

import os
import signal
import time
from pathlib import Path

import pytest

from tool_compat_shared.interactive_process_engine import (
    DEFAULT_MAX_SESSIONS,
    DEFAULT_SESSION_TTL_SECONDS,
    InteractiveProcessError,
    InteractiveProcessManager,
    InteractiveSpawnSpec,
    SessionLimitError,
    StdinClosedError,
    get_default_manager,
)
from tool_compat_shared.shell_engine import ShellInfo, detect_shell


def _shell() -> ShellInfo:
    return detect_shell()


def _wait_until(condition, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return
        time.sleep(0.02)
    raise AssertionError("condition not met within timeout")


def _collect_until(
    session,
    predicate=lambda output: True,
    *,
    timeout: float = 5.0,
    include_final: bool = True,
) -> str:
    """Drain a session until the predicate matches or it exits."""

    output = ""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        output += session.drain()
        if predicate(output):
            return output
        if not session.alive:
            if include_final:
                output += session.collect_final_output()
            return output
        time.sleep(0.02)
    return output


class TestPipeSessions:
    def test_short_command_finishes_with_output_and_exit_code(self):
        manager = InteractiveProcessManager(register_atexit=False)
        session = manager.spawn(
            InteractiveSpawnSpec(command="echo engine-test", shell=_shell())
        )
        assert session.session_id >= 1
        assert session.tty is False
        _wait_until(lambda: not session.alive)
        output = session.collect_final_output()
        session.terminate()
        assert "engine-test" in output
        assert session.exit_code == 0

    def test_drain_returns_incremental_output(self):
        manager = InteractiveProcessManager(register_atexit=False)
        session = manager.spawn(
            InteractiveSpawnSpec(
                command="echo first; sleep 0.3; echo second", shell=_shell()
            )
        )
        output = _collect_until(
            session, lambda out: out.count("first") >= 1 and "second" in out
        )
        session.terminate()
        assert "first" in output
        assert "second" in output

    def test_nonzero_exit_code_visible(self):
        manager = InteractiveProcessManager(register_atexit=False)
        session = manager.spawn(
            InteractiveSpawnSpec(command="exit 3", shell=_shell())
        )
        _wait_until(lambda: not session.alive)
        session.collect_final_output()
        session.terminate()
        assert session.exit_code == 3

    def test_stderr_is_captured(self):
        manager = InteractiveProcessManager(register_atexit=False)
        session = manager.spawn(
            InteractiveSpawnSpec(
                command="echo err-msg >&2; sleep 0.2", shell=_shell()
            )
        )
        output = _collect_until(session, lambda out: "err-msg" in out)
        session.terminate()
        assert "err-msg" in output

    def test_workdir_is_used(self, tmp_path: Path):
        manager = InteractiveProcessManager(register_atexit=False)
        session = manager.spawn(
            InteractiveSpawnSpec(
                command="pwd", workdir=str(tmp_path), shell=_shell()
            )
        )
        _wait_until(lambda: not session.alive)
        output = session.collect_final_output()
        session.terminate()
        assert str(tmp_path) in output

    def test_write_to_pipe_session_rejected(self):
        manager = InteractiveProcessManager(register_atexit=False)
        session = manager.spawn(
            InteractiveSpawnSpec(command="sleep 1", shell=_shell())
        )
        try:
            with pytest.raises(StdinClosedError):
                session.write("hello")
        finally:
            session.terminate()

    def test_interrupt_pipe_session_sends_sigint(self):
        manager = InteractiveProcessManager(register_atexit=False)
        session = manager.spawn(
            InteractiveSpawnSpec(command="sleep 30", shell=_shell())
        )
        session.interrupt()
        _wait_until(lambda: not session.alive)
        session.terminate()
        assert session.exit_code == -signal.SIGINT


class TestPtySessions:
    def test_pty_session_echoes_and_writes(self):
        manager = InteractiveProcessManager(register_atexit=False)
        session = manager.spawn(
            InteractiveSpawnSpec(command="cat", tty=True, shell=_shell())
        )
        assert session.tty is True
        try:
            session.write("pty-line\n")
            # Both the PTY echo and cat's own output eventually appear.
            output = _collect_until(
                session, lambda out: out.count("pty-line") >= 2
            )
            assert output.count("pty-line") >= 2
        finally:
            session.terminate()

    def test_pty_session_eof_ends_process(self):
        manager = InteractiveProcessManager(register_atexit=False)
        session = manager.spawn(
            InteractiveSpawnSpec(command="cat", tty=True, shell=_shell())
        )
        session.write("\x04")  # EOF
        _wait_until(lambda: not session.alive)
        session.terminate()
        assert session.exit_code == 0


class TestManager:
    def test_session_ids_increase_monotonically(self):
        manager = InteractiveProcessManager(register_atexit=False)
        first = manager.spawn(
            InteractiveSpawnSpec(command="true", shell=_shell())
        )
        second = manager.spawn(
            InteractiveSpawnSpec(command="true", shell=_shell())
        )
        assert second.session_id == first.session_id + 1
        manager.terminate_all()

    def test_get_and_remove(self):
        manager = InteractiveProcessManager(register_atexit=False)
        session = manager.spawn(
            InteractiveSpawnSpec(command="sleep 5", shell=_shell())
        )
        assert manager.get(session.session_id) is session
        assert manager.get(99999) is None
        removed = manager.remove(session.session_id)
        assert removed is session
        assert manager.get(session.session_id) is None
        session.terminate()

    def test_finished_session_removed_from_registry(self):
        manager = InteractiveProcessManager(register_atexit=False)
        session = manager.spawn(
            InteractiveSpawnSpec(command="true", shell=_shell())
        )
        _wait_until(lambda: not session.alive)
        session.collect_final_output()
        # The manager keeps finished sessions until observed or reaped,
        # matching upstream so a final write_stdin poll can collect them.
        assert manager.get(session.session_id) is session
        manager.remove(session.session_id)
        session.terminate()
        assert manager.get(session.session_id) is None

    def test_session_limit_enforced(self):
        manager = InteractiveProcessManager(
            max_sessions=2, register_atexit=False
        )
        first = manager.spawn(
            InteractiveSpawnSpec(command="sleep 30", shell=_shell())
        )
        second = manager.spawn(
            InteractiveSpawnSpec(command="sleep 30", shell=_shell())
        )
        with pytest.raises(SessionLimitError):
            manager.spawn(InteractiveSpawnSpec(command="true", shell=_shell()))
        manager.remove(first.session_id)
        first.terminate()
        third = manager.spawn(
            InteractiveSpawnSpec(command="true", shell=_shell())
        )
        third.collect_final_output()
        third.terminate()
        manager.remove(second.session_id)
        second.terminate()

    def test_limit_counts_dead_sessions_until_reaped(self):
        manager = InteractiveProcessManager(
            max_sessions=1, session_ttl_seconds=60.0, register_atexit=False
        )
        session = manager.spawn(
            InteractiveSpawnSpec(command="true", shell=_shell())
        )
        _wait_until(lambda: not session.alive)
        session.collect_final_output()
        # Dead-but-registered session still counts toward the cap.
        with pytest.raises(SessionLimitError):
            manager.spawn(InteractiveSpawnSpec(command="true", shell=_shell()))

    def test_reap_idle_terminates_and_drops(self):
        manager = InteractiveProcessManager(
            session_ttl_seconds=0.05, register_atexit=False
        )
        session = manager.spawn(
            InteractiveSpawnSpec(command="sleep 30", shell=_shell())
        )
        time.sleep(0.1)
        reaped = manager.reap_idle()
        assert session.session_id in reaped
        _wait_until(lambda: not session.alive)
        assert manager.get(session.session_id) is None

    def test_reap_idle_keeps_active_sessions(self):
        manager = InteractiveProcessManager(
            session_ttl_seconds=60.0, register_atexit=False
        )
        session = manager.spawn(
            InteractiveSpawnSpec(command="sleep 30", shell=_shell())
        )
        reaped = manager.reap_idle()
        assert reaped == []
        assert manager.get(session.session_id) is session
        session.terminate()

    def test_terminate_all_cleans_up(self):
        manager = InteractiveProcessManager(register_atexit=False)
        sessions = [
            manager.spawn(
                InteractiveSpawnSpec(command="sleep 30", shell=_shell())
            )
            for _ in range(3)
        ]
        manager.terminate_all()
        for session in sessions:
            _wait_until(lambda: not session.alive)
        assert manager.session_count() == 0

    def test_spawn_without_shell_raises(self):
        manager = InteractiveProcessManager(register_atexit=False)
        with pytest.raises(InteractiveProcessError):
            manager.spawn(InteractiveSpawnSpec(command="true"))

    def test_spawn_bad_shell_reports_error(self):
        manager = InteractiveProcessManager(register_atexit=False)
        shell = ShellInfo(
            name="nope", path="/nonexistent/shell-binary", args=("-c",)
        )
        with pytest.raises(InteractiveProcessError):
            manager.spawn(
                InteractiveSpawnSpec(command="true", shell=shell)
            )

    def test_defaults(self):
        assert DEFAULT_MAX_SESSIONS == 8
        assert DEFAULT_SESSION_TTL_SECONDS == 900.0

    def test_no_child_processes_leak_after_terminate_all(self):
        manager = InteractiveProcessManager(register_atexit=False)
        session = manager.spawn(
            InteractiveSpawnSpec(command="sleep 30", shell=_shell())
        )
        pid = session.process.pid
        manager.terminate_all()
        _wait_until(lambda: not session.alive)

        def _gone() -> bool:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return True
            except OSError:
                return True
            return False

        # The child may be a zombie until reaped; poll() reaps it.
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            if _gone():
                break
            session.process.poll()
            time.sleep(0.05)
        assert _gone()


class TestDefaultManager:
    def test_default_manager_is_shared(self):
        assert get_default_manager() is get_default_manager()
        assert isinstance(get_default_manager(), InteractiveProcessManager)
