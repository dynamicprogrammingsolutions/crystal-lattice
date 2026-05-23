from __future__ import annotations

import os
import shlex
import signal
import sys
import time
from pathlib import Path

from tool_compat_shared.background_processes import (
    BackgroundProcessRecord,
    BackgroundProcessRegistry,
    FilesystemBackgroundProcessStore,
)


def _sleep_command(seconds: float) -> str:
    script = f"import time; time.sleep({seconds})"
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(script)}"


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def test_background_process_store_round_trip(tmp_path: Path) -> None:
    store = FilesystemBackgroundProcessStore(tmp_path / "runtime")
    record = BackgroundProcessRecord(
        process_id="abc123xyz",
        pid=123,
        pgid=123,
        command="echo hello",
        cwd=str(tmp_path),
        shell="/bin/bash",
        status="running",
        ownership_mode="owned",
        shutdown_policy="terminate",
        started_at="2026-05-10T00:00:00+00:00",
        finished_at=None,
        exit_code=None,
        signal=None,
        termination_reason=None,
        output_path=store.output_path("abc123xyz"),
        completion_path=store.completion_path("abc123xyz"),
        last_observed_at="2026-05-10T00:00:00+00:00",
        agent_id="claude",
        session_id="sess_1",
        request_id="req_1",
        app_instance_id="app_1",
        manifest_path=store.manifest_path("abc123xyz"),
    )

    store.save_record(record)
    loaded = store.load_record("abc123xyz")

    assert loaded == record
    assert store.records_dir.exists()
    assert store.output_dir.exists()


def test_registry_reconciles_completed_process_after_restart(tmp_path: Path) -> None:
    root = tmp_path / "runtime"
    registry = BackgroundProcessRegistry(root, start_delay_seconds=0.05)
    record = registry.start_background_command(
        _sleep_command(0.4),
        working_directory=str(tmp_path),
        ownership_mode="tracked",
        shutdown_policy="leave_running",
    )

    assert record.status == "running"
    registry.close()

    time.sleep(1.2)

    restarted = BackgroundProcessRegistry(root, start_delay_seconds=0.05)
    refreshed = restarted.get_process(record.process_id)

    assert refreshed.status == "succeeded"
    assert refreshed.exit_code == 0


def test_registry_close_cancels_owned_processes(tmp_path: Path) -> None:
    root = tmp_path / "runtime"
    registry = BackgroundProcessRegistry(root, start_delay_seconds=0.05)
    record = registry.start_background_command(
        _sleep_command(60),
        working_directory=str(tmp_path),
        ownership_mode="owned",
        shutdown_policy="terminate",
    )

    assert record.status == "running"
    pid = record.pid

    registry.close()
    time.sleep(0.1)

    restarted = BackgroundProcessRegistry(root, start_delay_seconds=0.05)
    refreshed = restarted.get_process(record.process_id)

    assert refreshed.status == "cancelled"
    assert _alive(pid) is False


def test_registry_can_leave_owned_process_running_across_close(tmp_path: Path) -> None:
    root = tmp_path / "runtime"
    registry = BackgroundProcessRegistry(root, start_delay_seconds=0.05)
    record = registry.start_background_command(
        _sleep_command(60),
        working_directory=str(tmp_path),
        ownership_mode="owned",
        shutdown_policy="leave_running",
    )

    assert record.status == "running"
    pid = record.pid

    registry.close()
    assert _alive(pid) is True

    restarted = BackgroundProcessRegistry(root, start_delay_seconds=0.05)
    refreshed = restarted.get_process(record.process_id)
    try:
        assert refreshed.status == "running"
        cancelled = restarted.cancel_process(record.process_id, reason="test_cleanup")
        assert cancelled.status == "cancelled"
    finally:
        if _alive(pid):
            if os.name != "nt":
                try:
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass
            else:
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass