#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import time
from typing import Any, Literal, Mapping, Sequence
import urllib.error
import urllib.request


PluginCacheExpectation = Literal["empty", "populated"]
ConfigMode = Literal["explicit", "local-default"]

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
    plugin_metadata_ids: tuple[str, ...]
    pip_cache: Path
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
    config_path: Path,
    *,
    home_dir: Path,
    base_env: Mapping[str, str] | None = None,
) -> tuple[dict[str, str], set[str]]:
    """Build a child environment isolated at the config-loader boundary."""

    placeholder_names = collect_env_placeholder_names(config_path)
    env = dict(os.environ if base_env is None else base_env)
    for name in placeholder_names | _RUNTIME_ISOLATION_ENV_NAMES:
        env.pop(name, None)

    home = str(home_dir.resolve())
    env["HOME"] = home
    env["USERPROFILE"] = home
    env["PIP_CACHE_DIR"] = str((home_dir / ".cache" / "pip").resolve())
    return env, placeholder_names


def prepare_smoke_config(
    default_config_template: Path,
    *,
    destination_dir: Path,
    additional_plugin_name: str | None = None,
) -> Path:
    """Copy the shipped default config and optionally add one packaged plugin."""

    source_dir = (
        default_config_template
        if default_config_template.is_dir()
        else default_config_template.parent
    )
    source_config = (
        source_dir / "config.json"
        if default_config_template.is_dir()
        else default_config_template
    )
    if not source_config.is_file():
        raise ValueError(f"Default config does not exist: {source_config}")

    _prepare_empty_directory(destination_dir, label="config directory")
    shutil.copytree(
        source_dir,
        destination_dir,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            ".plugin_cache",
            "auth",
            "__pycache__",
            "*.pyc",
        ),
    )
    config_path = destination_dir / source_config.name
    if additional_plugin_name is not None:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("Default config root must be an object")
        plugins = config.get("plugins")
        if not isinstance(plugins, list):
            raise ValueError("Default config plugins must be a list")
        plugin_spec = f"path:${{env:BUILTIN_PLUGINS}}/{additional_plugin_name}"
        if plugin_spec in plugins:
            raise ValueError(
                f"Dynamic plugin probe is already selected: {additional_plugin_name}"
            )
        plugins.append(plugin_spec)
        config_path.write_text(
            json.dumps(config, indent=2) + "\n",
            encoding="utf-8",
        )
    (destination_dir / ".env").write_text("", encoding="utf-8")
    return config_path


def assert_plugin_not_preinstalled(
    preinstalled_manifest: Path,
    plugin_name: str,
) -> None:
    manifest = json.loads(preinstalled_manifest.read_text(encoding="utf-8"))
    raw_plugins = manifest.get("plugins") if isinstance(manifest, dict) else None
    if not isinstance(raw_plugins, list):
        raise ValueError("Preinstalled plugin manifest must contain a plugins list")
    names = {
        item.get("name")
        for item in raw_plugins
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    if plugin_name in names:
        raise ValueError(f"Dynamic plugin probe is already preinstalled: {plugin_name}")


def assert_config_boot(
    command: Sequence[str | os.PathLike[str]],
    *,
    config_path: Path,
    workspace: Path,
    home_dir: Path,
    plugin_cache_expectation: PluginCacheExpectation,
    config_mode: ConfigMode = "explicit",
    expected_plugin_id: str | None = None,
    base_env: Mapping[str, str] | None = None,
    timeout_seconds: float = 600,
) -> BootResult:
    """Boot one CLI command with clean state and assert its configured agents."""

    _prepare_empty_directory(workspace, label="workspace")
    home_dir.mkdir(parents=True, exist_ok=True)
    (workspace / ".env").write_text("", encoding="utf-8")

    env, placeholder_names = build_isolated_cli_environment(
        config_path,
        home_dir=home_dir,
        base_env=base_env,
    )
    port = reserve_loopback_port()
    log_path = workspace.parent / f"{workspace.name}-server.log"
    full_command = [
        *(str(part) for part in command),
        "--server",
        *(
            ["--config-local"]
            if config_mode == "local-default"
            else ["--config", str(config_path)]
        ),
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]

    process: subprocess.Popen[Any] | None = None
    failure: Exception | None = None
    cleanup_failure: Exception | None = None
    agents: tuple[str, ...] = ()
    plugin_metadata_ids: tuple[str, ...] = ()
    generated_config = (
        workspace / ".crystal" / "config.json"
        if config_mode == "local-default"
        else config_path
    )
    plugin_cache = (
        workspace / ".crystal" / ".plugin_cache" / "plugins"
        if config_mode == "local-default"
        else config_path.parent / ".plugin_cache" / "plugins"
    )
    pip_cache = Path(env["PIP_CACHE_DIR"])
    _assert_plugin_cache_initially_empty(plugin_cache)

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
            plugin_metadata_ids = _assert_plugin_cache(
                plugin_cache,
                plugin_cache_expectation,
                expected_plugin_id=expected_plugin_id,
            )
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
        plugin_metadata_ids=plugin_metadata_ids,
        pip_cache=pip_cache,
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
) -> subprocess.Popen[Any]:
    process_command = command
    kwargs: dict[str, Any] = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        resolved = shutil.which(command[0], path=env.get("PATH"))
        command_path = Path(resolved or command[0])
        if command_path.suffix.lower() in {".bat", ".cmd"}:
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
    *,
    expected_plugin_id: str | None,
) -> tuple[str, ...]:
    metadata_ids = _plugin_metadata_ids(plugin_cache)
    if expectation == "populated":
        if not metadata_ids:
            raise AssertionError(
                f"Expected dynamically installed plugin metadata under {plugin_cache}"
            )
        if expected_plugin_id is not None and metadata_ids != (expected_plugin_id,):
            raise AssertionError(
                f"Expected only plugin {expected_plugin_id!r} in {plugin_cache}, "
                f"found {metadata_ids!r}"
            )
        return metadata_ids

    entries = list(plugin_cache.iterdir()) if plugin_cache.is_dir() else []
    if entries:
        raise AssertionError(
            f"Expected an empty user plugin cache, found: "
            f"{[entry.name for entry in entries]}"
        )
    return ()


def _assert_plugin_cache_initially_empty(plugin_cache: Path) -> None:
    entries = list(plugin_cache.iterdir()) if plugin_cache.is_dir() else []
    if entries:
        raise ValueError(
            f"Plugin cache must be empty before boot: "
            f"{[entry.name for entry in entries]}"
        )


def _plugin_metadata_ids(plugin_cache: Path) -> tuple[str, ...]:
    ids: list[str] = []
    for metadata_path in sorted(plugin_cache.rglob("plugin_metadata.json")):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        plugin_id = metadata.get("id") if isinstance(metadata, dict) else None
        if not isinstance(plugin_id, str) or not plugin_id:
            raise AssertionError(
                f"Plugin metadata does not contain an id: {metadata_path}"
            )
        ids.append(plugin_id)
    return tuple(sorted(ids))


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
            process.send_signal(getattr(signal, "CTRL_BREAK_EVENT"))
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
    "ConfigMode",
    "PluginCacheExpectation",
    "assert_config_boot",
    "assert_plugin_not_preinstalled",
    "build_isolated_cli_environment",
    "collect_env_placeholder_names",
    "prepare_smoke_config",
    "read_log_tail",
    "reserve_loopback_port",
    "stop_process_tree",
]
