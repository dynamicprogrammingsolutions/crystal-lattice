from __future__ import annotations

import json
import os
import platform
import subprocess
import tarfile
import time
import zipfile
from pathlib import Path

import pytest


pytestmark = pytest.mark.integration


ROOT = Path(__file__).resolve().parents[3]


def test_frozen_installed_bundle_rejects_optional_builtin_plugin_install(
    tmp_path: Path,
) -> None:
    archive_raw = os.environ.get("CRYSTAL_LATTICE_BUNDLE_ARCHIVE")
    if not archive_raw:
        pytest.skip("CRYSTAL_LATTICE_BUNDLE_ARCHIVE not set")
    archive_path = Path(archive_raw).expanduser().resolve()
    if not archive_path.is_file():
        pytest.skip(f"CRYSTAL_LATTICE_BUNDLE_ARCHIVE is not a file: {archive_path}")
    if not _archive_matches_current_platform(archive_path):
        pytest.skip(
            f"Bundle archive does not match current platform: {archive_path.name}"
        )

    bundle_dir = _extract_bundle_archive(archive_path, tmp_path / "bundle")
    executable = bundle_dir / (
        "crystal-lattice.exe" if os.name == "nt" else "crystal-lattice"
    )
    assert executable.is_file()

    internal_dir = bundle_dir / "_internal"
    bundled_plugins = internal_dir / "bundled_plugins"
    _assert_selected_and_optional_plugin_layout(bundled_plugins)

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    plugin_cache = tmp_path / "plugin-cache"
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "plugin_cache_dir": str(plugin_cache),
                "plugins": [
                    "path:${env:BUILTIN_PLUGINS}/message-export-actions",
                ],
                "providers": {},
                "agents": {},
            }
        ),
        encoding="utf-8",
    )

    port = _reserve_port()
    server = subprocess.Popen(
        [
            str(executable),
            "--config",
            str(config_path),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=str(workspace),
        env={**os.environ, "CONFIG_DIR": str(config_path.parent)},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        output = _wait_for_process_exit(server, timeout_seconds=90)
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=20)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=20)

    assert server.returncode != 0
    assert (
        "Dynamic plugin installation is not supported in this frozen runtime" in output
    )
    assert "message-export-actions" in output
    assert not any(plugin_cache.glob("message-export-actions@*"))


def _assert_selected_and_optional_plugin_layout(bundled_plugins: Path) -> None:
    selected = json.loads(
        (bundled_plugins / "codex-tools" / "agent_plugin.json").read_text(
            encoding="utf-8"
        )
    )
    optional = json.loads(
        (bundled_plugins / "message-export-actions" / "agent_plugin.json").read_text(
            encoding="utf-8"
        )
    )

    assert selected["preinstalled"] is True
    assert not (bundled_plugins / "codex-tools" / "src").exists()
    assert optional.get("preinstalled") is not True
    assert (bundled_plugins / "message-export-actions" / "pyproject.toml").is_file()
    assert (
        bundled_plugins
        / "message-export-actions"
        / "src"
        / "message_export_actions"
        / "__init__.py"
    ).is_file()


def _archive_matches_current_platform(path: Path) -> bool:
    name = path.name.lower()
    system = platform.system().lower()
    machine = platform.machine().lower()
    expected_platform = (
        "darwin"
        if system == "darwin"
        else "windows" if system == "windows" else "linux"
    )
    expected_arch = "arm64" if machine in {"arm64", "aarch64"} else "amd64"
    return f"-{expected_platform}-{expected_arch}" in name


def _extract_bundle_archive(archive_path: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True)
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(target_dir)
    else:
        with tarfile.open(archive_path, "r:gz") as archive:
            archive.extractall(target_dir)
    directories = [path for path in target_dir.iterdir() if path.is_dir()]
    assert len(directories) == 1, directories
    return directories[0]


def _reserve_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_process_exit(
    process: subprocess.Popen[str], *, timeout_seconds: float
) -> str:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if process.poll() is not None:
            return process.stdout.read() if process.stdout is not None else ""
        time.sleep(0.2)
    output = process.stdout.read() if process.stdout is not None else ""
    raise AssertionError(f"Timed out waiting for frozen bundle to exit\n{output}")
