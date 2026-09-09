#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import time
from typing import Any, Literal, Sequence
import urllib.error
import urllib.request


PluginCacheExpectation = Literal["empty", "populated"]

_ENV_PLACEHOLDER_RE = re.compile(r"\$\{env:([^}]+)\}")
_RUNTIME_ISOLATION_ENV_NAMES = frozenset(
    {
        "BUILTIN_PLUGINS",
        "CONFIG_DIR",
        "CRYSTAL_PLUGIN_PYTHON",
        "CRYSTAL_PREINSTALLED_PLUGIN_MANIFEST",
        "CRYSTAL_RUNTIME_LAYOUT",
        "PLUGIN_CACHE_DIR",
        "PYTHONHOME",
        "PYTHONPATH",
        "VIRTUAL_ENV",
        "WORKING_DIR",
    }
)


@dataclass(frozen=True)
class BootResult:
    agents: tuple[str, ...]
    generated_config: Path
    log_path: Path
    plugin_cache: Path
    removed_placeholder_names: tuple[str, ...]


def collect_env_placeholder_names(config_path: Path) -> set[str]:
    """Return environment placeholders resolved by the config loader.

    Values wrapped in the loader's exact ``{"$raw": ...}`` escape are
    intentionally ignored.
    """

    config = json.loads(config_path.read_text(encoding="utf-8"))
    names: set[str] = set()

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            if set(value) == {"$raw"}:
                return
            for nested in value.values():
                collect(nested)
            return
        if isinstance(value, list):
            for nested in value:
                collect(nested)
            return
        if isinstance(value, str):
            names.update(_ENV_PLACEHOLDER_RE.findall(value))

    collect(config)
    return names


def build_isolated_cli_environment(
    default_config_template: Path,
    *,
    home_dir: Path,
) -> tuple[dict[str, str], set[str]]:
    """Build a child environment isolated at the config-loader boundary."""

    placeholder_names = collect_env_placeholder_names(default_config_template)
    env = dict(os.environ)
    for name in placeholder_names | _RUNTIME_ISOLATION_ENV_NAMES:
        env.pop(name, None)

    home = str(home_dir.resolve())
    env["HOME"] = home
    env["USERPROFILE"] = home
    return env, placeholder_names


def assert_default_config_boot(
    command: Sequence[str | os.PathLike[str]],
    *,
    default_config_template: Path,
    workspace: Path,
    home_dir: Path,
    plugin_cache_expectation: PluginCacheExpectation,
    timeout_seconds: float = 600,
) -> BootResult:
    """Boot one CLI command with clean state and assert its default agents."""

    _prepare_empty_directory(workspace, label="workspace")
    _prepare_empty_directory(home_dir, label="home")
    (workspace / ".env").write_text("", encoding="utf-8")

    env, placeholder_names = build_isolated_cli_environment(
        default_config_template,
        home_dir=home_dir,
    )
    port = reserve_loopback_port()
    log_path = workspace.parent / f"{workspace.name}-server.log"
    full_command = [
        *(str(part) for part in command),
        "--server",
        "--config-local",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]

    process: subprocess.Popen[bytes] | None = None
    failure: Exception | None = None
    cleanup_failure: Exception | None = None
    agents: tuple[str, ...] = ()
    generated_config = workspace / ".crystal" / "config.json"
    plugin_cache = workspace / ".crystal" / ".plugin_cache" / "plugins"

    with log_path.open("wb") as log_file:
        try:
            process = _start_process(
                full_command,
                cwd=workspace,
                env=env,
                log_file=log_file,
            )
            base_url = f"http://127.0.0.1:{port}"
            _wait_for_server(base_url, process, timeout_seconds=timeout_seconds)
            agents = _assert_agents(base_url, generated_config)
            _assert_plugin_cache(plugin_cache, plugin_cache_expectation)
        except Exception as exc:
            failure = exc
        finally:
            if process is not None:
                try:
                    stop_process_tree(process, port=port)
                except Exception as exc:
                    cleanup_failure = exc

    if failure is not None or cleanup_failure is not None:
        details = []
        if failure is not None:
            details.append(str(failure))
        if cleanup_failure is not None:
            details.append(f"process cleanup failed: {cleanup_failure}")
        log_tail = read_log_tail(log_path)
        if log_tail:
            details.append(f"server log tail:\n{log_tail}")
        raise AssertionError("\n".join(details)) from (failure or cleanup_failure)

    return BootResult(
        agents=agents,
        generated_config=generated_config,
        log_path=log_path,
        plugin_cache=plugin_cache,
        removed_placeholder_names=tuple(sorted(placeholder_names)),
    )


def reserve_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def stop_process_tree(
    process: subprocess.Popen[Any],
    *,
    port: int,
    graceful_timeout_seconds: float = 10,
    closed_timeout_seconds: float = 10,
) -> None:
    """Stop the full process tree and prove its loopback listener closed."""

    if os.name == "nt":
        _stop_windows_process_tree(
            process,
            port=port,
            graceful_timeout_seconds=graceful_timeout_seconds,
        )
    else:
        _stop_posix_process_tree(
            process,
            port=port,
            graceful_timeout_seconds=graceful_timeout_seconds,
        )

    _wait_for_port_closed(port, timeout_seconds=closed_timeout_seconds)


def read_log_tail(path: Path, *, max_chars: int = 20_000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return text[-max_chars:]


def _prepare_empty_directory(path: Path, *, label: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    entries = list(path.iterdir())
    if entries:
        raise ValueError(f"{label} must be empty: {path}")


def _start_process(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    log_file: Any,
) -> subprocess.Popen[bytes]:
    process_command = command
    kwargs: dict[str, Any] = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        if Path(command[0]).suffix.lower() in {".bat", ".cmd"}:
            command_line = subprocess.list2cmdline(command)
            process_command = [
                env.get("COMSPEC") or os.environ.get("COMSPEC", "cmd.exe"),
                "/d",
                "/s",
                "/c",
                command_line,
            ]
    else:
        kwargs["start_new_session"] = True

    return subprocess.Popen(
        process_command,
        cwd=str(cwd),
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        **kwargs,
    )


def _wait_for_server(
    base_url: str,
    process: subprocess.Popen[Any],
    *,
    timeout_seconds: float,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error = ""
    while time.monotonic() < deadline:
        return_code = process.poll()
        if return_code is not None:
            raise RuntimeError(f"CLI exited before readiness with status {return_code}")
        try:
            _json_request(f"{base_url}/api/hello", timeout=2)
            return
        except Exception as exc:
            last_error = str(exc)
            time.sleep(0.25)
    raise TimeoutError(f"CLI did not become ready: {last_error}")


def _assert_agents(base_url: str, generated_config: Path) -> tuple[str, ...]:
    config = json.loads(generated_config.read_text(encoding="utf-8"))
    configured_agents = config.get("agents")
    if not isinstance(configured_agents, dict):
        raise AssertionError("Generated default config does not define agents")
    expected = tuple(sorted(str(name) for name in configured_agents))

    payload = _json_request(f"{base_url}/agents", timeout=10)
    actual_raw = payload.get("agents") if isinstance(payload, dict) else None
    if not isinstance(actual_raw, list) or not all(
        isinstance(name, str) for name in actual_raw
    ):
        raise AssertionError(f"Invalid /agents response: {payload!r}")
    actual = tuple(sorted(actual_raw))
    if actual != expected:
        raise AssertionError(
            f"Default agents differ: expected {expected!r}, got {actual!r}"
        )
    return actual


def _assert_plugin_cache(
    plugin_cache: Path,
    expectation: PluginCacheExpectation,
) -> None:
    if expectation == "populated":
        metadata = list(plugin_cache.rglob("plugin_metadata.json"))
        if not metadata:
            raise AssertionError(
                f"Expected dynamically installed plugin metadata under {plugin_cache}"
            )
        return

    entries = list(plugin_cache.iterdir()) if plugin_cache.is_dir() else []
    if entries:
        raise AssertionError(
            f"Expected an empty user plugin cache, found: "
            f"{[entry.name for entry in entries]}"
        )


def _json_request(url: str, *, timeout: float) -> Any:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc
    return json.loads(body) if body else None


def _stop_posix_process_tree(
    process: subprocess.Popen[Any],
    *,
    port: int,
    graceful_timeout_seconds: float,
) -> None:
    if process.poll() is None or _port_is_open(port):
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    _wait_for_process(process, timeout_seconds=graceful_timeout_seconds)
    if process.poll() is None or _port_is_open(port):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        _wait_for_process(process, timeout_seconds=graceful_timeout_seconds)
    if process.poll() is None:
        raise RuntimeError(f"Could not stop POSIX process group {process.pid}")


def _stop_windows_process_tree(
    process: subprocess.Popen[Any],
    *,
    port: int,
    graceful_timeout_seconds: float,
) -> None:
    if process.poll() is None:
        try:
            process.send_signal(signal.CTRL_BREAK_EVENT)
        except (OSError, ValueError):
            pass
        _wait_for_process(process, timeout_seconds=graceful_timeout_seconds)

    if process.poll() is None or _port_is_open(port):
        result = subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        _wait_for_process(process, timeout_seconds=graceful_timeout_seconds)
        if process.poll() is None:
            raise RuntimeError(
                f"taskkill did not stop process tree {process.pid}: {result.stdout}"
            )


def _wait_for_process(
    process: subprocess.Popen[Any],
    *,
    timeout_seconds: float,
) -> None:
    if process.poll() is not None:
        return
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        return


def _wait_for_port_closed(port: int, *, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not _port_is_open(port):
            return
        time.sleep(0.1)
    raise RuntimeError(f"Loopback port {port} remained open after process cleanup")


def _port_is_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return True
    except OSError:
        return False


__all__ = [
    "BootResult",
    "PluginCacheExpectation",
    "assert_default_config_boot",
    "build_isolated_cli_environment",
    "collect_env_placeholder_names",
    "read_log_tail",
    "reserve_loopback_port",
    "stop_process_tree",
]
