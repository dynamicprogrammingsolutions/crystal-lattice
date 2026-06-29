"""End-to-end integration tests for the CLI entrypoint.

These tests launch ``python -m agent_terminal_app`` as a subprocess and
verify the real CLI behavior: startup summary, profile persistence, server
reachability, Bonjour/Bridge summary lines, and logging.

Marked ``integration`` so they are excluded from the default ``pytest`` run.
Run with::

    pytest application/python/tests/test_cli_e2e.py -m integration -v
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest


pytestmark = pytest.mark.integration


ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def _session_home() -> Path:
    """Use the real HOME directory for the plugin cache.

    The plugin cache at ``~/.crystal/.plugin_cache`` is already warm from
    normal development usage, so tests don't need to re-install plugins.
    Profile entries in ``~/.crystal/projects.json`` are keyed by project
    directory path (temp dirs), so they don't interfere with real entries.
    """
    return Path.home()


def _reserve_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _pythonpath_env() -> dict[str, str]:
    return {
        "PYTHONPATH": os.pathsep.join(
            [
                str(ROOT / "core" / "python"),
                str(ROOT / "application" / "python"),
            ]
        ),
    }


def _make_env(home_dir: Path, workspace: Path) -> dict[str, str]:
    """Build the environment for a CLI subprocess."""
    return {
        **os.environ,
        "HOME": str(home_dir),
        **_pythonpath_env(),
        # Provide dummy API keys so plugin discovery doesn't fail.
        "OPENROUTER_API_KEY": "test-key",
        "OPENAI_API_KEY": "test-key",
        "GEMINI_API_KEY": "test-key",
        # Force unbuffered stdout so print() output is immediately
        # flushed to the file (avoids missing startup summary in tests).
        "PYTHONUNBUFFERED": "1",
    }


def _launch_cli(
    workspace: Path,
    home_dir: Path,
    port: int,
    *extra_args: str,
) -> tuple[subprocess.Popen[str], Path]:
    """Launch the CLI as a subprocess with isolated HOME and cwd."""
    stdout_file = workspace / "stdout.log"
    env = _make_env(home_dir, workspace)
    process = subprocess.Popen(
        [
            "python",
            "-m",
            "agent_terminal_app",
            "--server",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            *extra_args,
        ],
        cwd=str(workspace),
        env=env,
        stdout=open(stdout_file, "w"),
        stderr=subprocess.STDOUT,
        text=True,
    )
    return process, stdout_file


def _launch_cli_custom(
    workspace: Path,
    home_dir: Path,
    port: int,
    *cli_args: str,
) -> tuple[subprocess.Popen[str], Path]:
    """Launch the CLI with custom args (not prefixed with --server)."""
    stdout_file = workspace / "stdout.log"
    env = _make_env(home_dir, workspace)
    process = subprocess.Popen(
        [
            "python",
            "-m",
            "agent_terminal_app",
            *cli_args,
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=str(workspace),
        env=env,
        stdout=open(stdout_file, "w"),
        stderr=subprocess.STDOUT,
        text=True,
    )
    return process, stdout_file


def _wait_for_server(
    base_url: str,
    process: subprocess.Popen[str],
    timeout: float = 30.0,
) -> None:
    """Poll ``/api/hello`` until it responds or the process exits."""
    deadline = time.monotonic() + timeout
    last_error = ""
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(f"server exited early (code {process.returncode})")
        try:
            with urllib.request.urlopen(f"{base_url}/api/hello", timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception as exc:
            last_error = str(exc)
        time.sleep(0.5)
    raise AssertionError(f"server did not become ready: {last_error}")


def _terminate(process: subprocess.Popen[str], timeout: float = 5.0) -> None:
    """Send SIGTERM, wait, then SIGKILL if needed."""
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=timeout)


def _read_stdout(stdout_file: Path) -> str:
    """Read all captured stdout from the temp file."""
    if stdout_file.is_file():
        return stdout_file.read_text(encoding="utf-8")
    return ""


def _read_profile(home_dir: Path) -> dict[str, Any]:
    """Read ~/.crystal/projects.json, returning the parsed contents."""
    profile_path = home_dir / ".crystal" / "projects.json"
    if not profile_path.is_file():
        return {}
    return json.loads(profile_path.read_text(encoding="utf-8"))


def _make_workspace(tmp_path: Path) -> Path:
    """Create a workspace directory under tmp_path.

    Pre-creates ``.crystal/`` in the workspace so the default log file
    path (``.crystal/crystal.log``) is valid when the CLI configures logging.
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / ".crystal").mkdir(exist_ok=True)
    return workspace


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_server_only_startup_and_profile_persistence(
    tmp_path: Path, _session_home: Path
) -> None:
    """--server: startup summary printed, server reachable, profile persisted."""
    workspace = _make_workspace(tmp_path)
    port = _reserve_port()
    base_url = f"http://127.0.0.1:{port}"

    process, stdout_file = _launch_cli(workspace, _session_home, port)
    try:
        _wait_for_server(base_url, process)
        with urllib.request.urlopen(f"{base_url}/api/hello", timeout=5) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            assert body["message"] == "Hello from Bonjour Server!"
    finally:
        _terminate(process)

    output = _read_stdout(stdout_file)
    assert "[crystal-lattice] Starting" in output
    assert f"http://127.0.0.1:{port}" in output
    assert "Config:" in output
    assert "Sessions:" in output

    profile = _read_profile(_session_home)
    assert "projects" in profile
    projects = profile["projects"]
    assert len(projects) == 1
    entry = list(projects.values())[0]
    # Port is NOT persisted when --port is passed via CLI (by design).
    # Name and bridge_server_id are persisted.
    assert "name" in entry
    assert "bridge_server_id" in entry


def test_second_run_reuses_persisted_port(tmp_path: Path, _session_home: Path) -> None:
    """Second --server run in same workspace reuses persisted port and bridge-server-id."""
    workspace = _make_workspace(tmp_path)
    port = _reserve_port()
    base_url = f"http://127.0.0.1:{port}"

    # First run.
    process1, stdout_file1 = _launch_cli(workspace, _session_home, port)
    try:
        _wait_for_server(base_url, process1)
    finally:
        _terminate(process1)
    _read_stdout(stdout_file1)

    profile1 = _read_profile(_session_home)
    entry1 = list(profile1["projects"].values())[0]

    # Second run — same port, should reuse persisted values.
    process2, stdout_file2 = _launch_cli(workspace, _session_home, port)
    try:
        _wait_for_server(base_url, process2)
    finally:
        _terminate(process2)

    profile2 = _read_profile(_session_home)
    entry2 = list(profile2["projects"].values())[0]

    # Port is the same because we pass it explicitly both times.
    # Name and bridge_server_id should be reused from the first run.
    assert entry2["bridge_server_id"] == entry1["bridge_server_id"]
    assert entry2["name"] == entry1["name"]


def test_console_server_no_tty(tmp_path: Path, _session_home: Path) -> None:
    """--console --server --no-tty: console runs, server reachable, clean SIGTERM exit."""
    workspace = _make_workspace(tmp_path)
    port = _reserve_port()
    base_url = f"http://127.0.0.1:{port}"

    process, stdout_file = _launch_cli_custom(
        workspace,
        _session_home,
        port,
        "--console",
        "--server",
        "--no-tty",
    )
    try:
        _wait_for_server(base_url, process, timeout=120)
        with urllib.request.urlopen(f"{base_url}/api/hello", timeout=5) as resp:
            assert resp.status == 200
    finally:
        _terminate(process, timeout=10)

    output = _read_stdout(stdout_file)
    assert (
        "[crystal-lattice] Starting" in output
    ), f"Missing startup summary:\n{output[:2000]}"
    assert "Session started" in output, f"Missing 'Session started':\n{output[:2000]}"
    assert process.returncode == 0


def test_console_no_tty_without_server(tmp_path: Path, _session_home: Path) -> None:
    """--console --no-tty (no --server): console starts, prints 'Session started', exits on SIGTERM."""
    workspace = _make_workspace(tmp_path)
    port = _reserve_port()

    process, stdout_file = _launch_cli_custom(
        workspace, _session_home, port, "--console", "--no-tty"
    )
    # Give the console time to start and print "Session started".
    time.sleep(5)
    _terminate(process, timeout=10)

    output = _read_stdout(stdout_file)
    assert "Session started" in output
    assert process.returncode == 0


def test_enable_bonjour_startup_summary(tmp_path: Path, _session_home: Path) -> None:
    """--server --enable-bonjour: summary includes Bonjour line."""
    try:
        import zeroconf  # noqa: F401
    except ImportError:
        pytest.skip("zeroconf is not installed")

    workspace = _make_workspace(tmp_path)
    port = _reserve_port()
    base_url = f"http://127.0.0.1:{port}"

    process, stdout_file = _launch_cli(
        workspace, _session_home, port, "--enable-bonjour"
    )
    try:
        _wait_for_server(base_url, process, timeout=60)
    finally:
        _terminate(process, timeout=10)

    output = _read_stdout(stdout_file)
    assert "[crystal-lattice] Starting" in output
    assert "Bonjour:" in output
    assert "discoverable on local network" in output


def test_enable_bridge_startup_summary(tmp_path: Path, _session_home: Path) -> None:
    """--server --enable-bridge with bridge_url in .crystal/profile.json: summary includes Bridge line."""
    workspace = _make_workspace(tmp_path)
    port = _reserve_port()
    base_url = f"http://127.0.0.1:{port}"

    # Write a local override profile with a bridge URL.
    crystal_dir = workspace / ".crystal"
    crystal_dir.mkdir(exist_ok=True)
    profile_json = crystal_dir / "profile.json"
    profile_json.write_text(
        json.dumps({"bridge_url": "ws://localhost:4000/ws/websocket"}),
        encoding="utf-8",
    )

    process, stdout_file = _launch_cli(
        workspace, _session_home, port, "--enable-bridge"
    )
    try:
        _wait_for_server(base_url, process, timeout=60)
    finally:
        _terminate(process, timeout=10)

    output = _read_stdout(stdout_file)
    assert "[crystal-lattice] Starting" in output
    assert "Bridge:" in output
    assert "ws://localhost:4000/ws/websocket" in output


def test_default_log_file_created(tmp_path: Path, _session_home: Path) -> None:
    """--server (no --log-file): .crystal/crystal.log is created and non-empty."""
    workspace = _make_workspace(tmp_path)
    port = _reserve_port()
    base_url = f"http://127.0.0.1:{port}"

    process, stdout_file = _launch_cli(workspace, _session_home, port)
    try:
        _wait_for_server(base_url, process)
    finally:
        _terminate(process)

    log_file = workspace / ".crystal" / "crystal.log"
    assert log_file.is_file()
    content = log_file.read_text(encoding="utf-8")
    assert len(content) > 0


def test_no_log_file_disables_logging(tmp_path: Path, _session_home: Path) -> None:
    """--server --no-log-file: no .crystal/crystal.log created."""
    workspace = _make_workspace(tmp_path)
    port = _reserve_port()
    base_url = f"http://127.0.0.1:{port}"

    process, stdout_file = _launch_cli(workspace, _session_home, port, "--no-log-file")
    try:
        _wait_for_server(base_url, process)
    finally:
        _terminate(process)

    log_file = workspace / ".crystal" / "crystal.log"
    assert not log_file.exists()
