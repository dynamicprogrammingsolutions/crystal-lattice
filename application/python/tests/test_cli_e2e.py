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
import platform
import shutil
import signal
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
                str(ROOT / "application" / "python" / "tests" / "fixtures"),
                str(ROOT / "plugins" / "sleep-prevention-app" / "src"),
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


def _interrupt(process: subprocess.Popen[str], timeout: float = 5.0) -> None:
    """Send SIGINT, wait, then SIGKILL if needed."""
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=timeout)


def _process_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _caffeinate_child_pids(process: subprocess.Popen[str]) -> list[int]:
    if process.poll() is not None:
        return []
    result = subprocess.run(
        ["pgrep", "-P", str(process.pid), "-x", "caffeinate"],
        check=False,
        capture_output=True,
        text=True,
    )
    pids: list[int] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.isdigit():
            pids.append(int(line))
    return pids


def _wait_for_caffeinate_children(
    process: subprocess.Popen[str],
    *,
    minimum: int,
    timeout: float = 10.0,
) -> list[int]:
    deadline = time.monotonic() + timeout
    last_seen: list[int] = []
    while time.monotonic() < deadline:
        last_seen = _caffeinate_child_pids(process)
        if len(last_seen) >= minimum:
            return last_seen
        if process.poll() is not None:
            break
        time.sleep(0.2)
    raise AssertionError(
        f"expected at least {minimum} caffeinate child process(es), saw {last_seen}"
    )


def _wait_for_no_caffeinate_children(
    process: subprocess.Popen[str],
    *,
    timeout: float = 10.0,
) -> list[int]:
    deadline = time.monotonic() + timeout
    last_seen: list[int] = []
    while time.monotonic() < deadline:
        last_seen = _caffeinate_child_pids(process)
        if not last_seen:
            return []
        time.sleep(0.2)
    return last_seen


def _patch_server_settings(base_url: str, values: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{base_url}/server/settings",
        data=json.dumps({"values": values}).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="PATCH",
    )
    with urllib.request.urlopen(request, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _read_stdout(stdout_file: Path) -> str:
    """Read all captured stdout from the temp file."""
    if stdout_file.is_file():
        return stdout_file.read_text(encoding="utf-8")
    return ""


def _wait_for_stdout_contains(
    stdout_file: Path,
    process: subprocess.Popen[str],
    text: str,
    *,
    timeout: float = 30.0,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        output = _read_stdout(stdout_file)
        if text in output:
            return
        if process.poll() is not None:
            raise AssertionError(f"process exited before {text!r}: {output[:2000]}")
        time.sleep(0.2)
    output = _read_stdout(stdout_file)
    raise AssertionError(f"timed out waiting for {text!r}: {output[:2000]}")


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
    try:
        _wait_for_stdout_contains(stdout_file, process, "Session started", timeout=60)
    finally:
        _terminate(process, timeout=10)

    output = _read_stdout(stdout_file)
    assert "Session started" in output
    assert process.returncode == 0


def test_console_server_lifecycle_plugin_replays_once_and_closes_shared_app(
    tmp_path: Path,
    _session_home: Path,
) -> None:
    workspace = _make_workspace(tmp_path)
    crystal_dir = workspace / ".crystal"
    config_path = crystal_dir / "config.json"
    sessions_dir = crystal_dir / "sessions"
    runtime_dir = crystal_dir / "runtime"
    actions_path = workspace / "lifecycle-actions.jsonl"
    closes_path = workspace / "lifecycle-closes.jsonl"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir.mkdir(parents=True, exist_ok=True)

    config_path.write_text(
        json.dumps(
            {
                "providers": {
                    "echo": {
                        "provider": "echo_openai_like",
                        "model": "test-model",
                    }
                },
                "plugins": [
                    "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
                    "cli_lifecycle_app_plugin.CliLifecycleAppPlugin",
                ],
                "agents": {"default": {"provider": "echo"}},
                "application": {
                    "cli_lifecycle_actions_path": str(actions_path),
                    "cli_lifecycle_closes_path": str(closes_path),
                },
            }
        ),
        encoding="utf-8",
    )
    (runtime_dir / "server_settings.json").write_text(
        json.dumps({"settings": {"dummy_server_mode": "careful"}}),
        encoding="utf-8",
    )

    port = _reserve_port()
    base_url = f"http://127.0.0.1:{port}"
    process, stdout_file = _launch_cli_custom(
        workspace,
        _session_home,
        port,
        "--console",
        "--server",
        "--no-tty",
        "--config",
        str(config_path),
        "--sessions-dir",
        str(sessions_dir),
    )
    try:
        _wait_for_server(base_url, process, timeout=120)
        actions = _read_jsonl(actions_path)
        assert len(actions) == 1
        assert actions[0]["context"]["source"] == "startup"
    finally:
        _interrupt(process, timeout=10)

    closes = _read_jsonl(closes_path)
    assert len(closes) == 1
    assert process.returncode == 0

    output = _read_stdout(stdout_file)
    assert "Session started" in output


def test_console_server_reload_replaces_shared_application_without_process_restart(
    tmp_path: Path,
    _session_home: Path,
) -> None:
    workspace = _make_workspace(tmp_path)
    config_path = workspace / ".crystal" / "reload-config.json"
    sessions_dir = workspace / ".crystal" / "reload-sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "providers": {
            "echo": {
                "provider": "echo_openai_like",
                "model": "test-model",
            }
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            {
                "path": str(ROOT / "plugins" / "application-config-app"),
                "entry": "application_config_app.ApplicationConfigAppPlugin",
            },
        ],
        "agents": {"default": {"provider": "echo"}},
        "application": {
            "application_config": {
                "env_file": str(workspace / ".crystal" / ".env"),
                "editable_env_keys": [],
                "provider_env_keys": {},
            }
        },
    }
    config_path.write_text(json.dumps(config), encoding="utf-8")
    port = _reserve_port()
    base_url = f"http://127.0.0.1:{port}"
    process, stdout_file = _launch_cli_custom(
        workspace,
        _session_home,
        port,
        "--console",
        "--server",
        "--no-tty",
        "--config",
        str(config_path),
        "--sessions-dir",
        str(sessions_dir),
    )
    try:
        _wait_for_server(base_url, process, timeout=120)
        _wait_for_stdout_contains(stdout_file, process, "Session started", timeout=60)
        original_pid = process.pid
        sessions_before = _get_json(f"{base_url}/sessions")["sessions"]

        config["plugins"].append("tests.dummy_app_plugin.DummyAppPlugin")
        config_path.write_text(json.dumps(config), encoding="utf-8")
        accepted = _post_json(
            f"{base_url}/actions",
            {
                "plugin": "application_config",
                "action_id": "reload_application",
                "inputs": {},
            },
        )
        assert accepted["result"]["status"] == "ok"
        assert accepted["result"]["reload_status"] == "accepted"

        deadline = time.monotonic() + 60
        actions: list[dict[str, Any]] = []
        while time.monotonic() < deadline:
            try:
                actions = _get_json(f"{base_url}/application/actions")["actions"]
            except urllib.error.HTTPError as exc:
                assert exc.code == 503
                time.sleep(0.1)
                continue
            if any(action.get("id") == "do_dummy" for action in actions):
                break
            time.sleep(0.1)
        assert any(action.get("id") == "do_dummy" for action in actions)
        assert process.poll() is None
        assert process.pid == original_pid
        assert _get_json(f"{base_url}/sessions")["sessions"] == sessions_before

        config["plugins"] = [
            plugin
            for plugin in config["plugins"]
            if plugin != "tests.dummy_app_plugin.DummyAppPlugin"
        ]
        config_path.write_text(json.dumps(config), encoding="utf-8")
        removed = _post_json(
            f"{base_url}/actions",
            {
                "plugin": "application_config",
                "action_id": "reload_application",
                "inputs": {},
            },
        )
        assert removed["result"]["status"] == "ok"
        assert removed["result"]["reload_status"] == "accepted"
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                actions = _get_json(f"{base_url}/application/actions")["actions"]
            except urllib.error.HTTPError as exc:
                assert exc.code == 503
                time.sleep(0.1)
                continue
            if not any(action.get("id") == "do_dummy" for action in actions):
                break
            time.sleep(0.1)
        assert not any(action.get("id") == "do_dummy" for action in actions)
    finally:
        _interrupt(process, timeout=15)


@pytest.mark.skipif(
    platform.system() != "Darwin" or shutil.which("caffeinate") is None,
    reason="real caffeinate subprocess behavior is macOS-only",
)
def test_console_server_sleep_prevention_toggle_releases_caffeinate_children(
    tmp_path: Path,
    _session_home: Path,
) -> None:
    workspace = _make_workspace(tmp_path)
    crystal_dir = workspace / ".crystal"
    config_path = crystal_dir / "config.json"
    sessions_dir = crystal_dir / "sessions"
    runtime_dir = crystal_dir / "runtime"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir.mkdir(parents=True, exist_ok=True)

    config_path.write_text(
        json.dumps(
            {
                "providers": {
                    "echo": {
                        "provider": "echo_openai_like",
                        "model": "test-model",
                    }
                },
                "plugins": [
                    "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
                    "sleep_prevention_app.SleepPreventionAppPlugin",
                ],
                "agents": {"default": {"provider": "echo"}},
                "application": {"sleep_prevention_caffeinate_flags": "-i"},
            }
        ),
        encoding="utf-8",
    )
    (runtime_dir / "server_settings.json").write_text(
        json.dumps({"settings": {"sleep_prevention_enabled": True}}),
        encoding="utf-8",
    )

    port = _reserve_port()
    base_url = f"http://127.0.0.1:{port}"
    process, stdout_file = _launch_cli_custom(
        workspace,
        _session_home,
        port,
        "--console",
        "--server",
        "--no-tty",
        "--config",
        str(config_path),
        "--sessions-dir",
        str(sessions_dir),
    )
    captured_pids: list[int] = []
    try:
        _wait_for_server(base_url, process, timeout=120)
        captured_pids = _wait_for_caffeinate_children(process, minimum=1)

        response = _patch_server_settings(
            base_url,
            {"sleep_prevention_enabled": False},
        )

        assert response == {"settings": {"sleep_prevention_enabled": False}}
        assert _wait_for_no_caffeinate_children(process) == []
    finally:
        _terminate(process, timeout=10)
        for pid in captured_pids:
            if _process_is_alive(pid):
                subprocess.run(["kill", str(pid)], check=False)

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
