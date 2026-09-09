#!/usr/bin/env python3
from __future__ import annotations

from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from typing import Iterator

from crystal_lattice_cli_boot import (
    assert_config_boot,
    assert_plugin_not_preinstalled,
    prepare_smoke_config,
)
from crystal_lattice_distribution import (
    archive_package_stem,
    assert_archive_matches_current_platform,
    read_project_version,
    resolve_bash,
)


ROOT = Path(__file__).resolve().parents[1]
INSTALL_SCRIPT = ROOT / "scripts" / "install.sh"
DYNAMIC_PLUGIN_PROBE = "generic-callback-app"
COMMAND_NAME = "crystal-lattice"


class QuietFileHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = format, args


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "usage: smoke_test_crystal_lattice_default_install.py <archive>"
        )
    archive = Path(sys.argv[1]).expanduser().resolve()
    smoke_test_default_install(archive)
    print(f"Default-installer smoke test passed: {archive}")


def smoke_test_default_install(archive: Path) -> None:
    if not archive.is_file():
        raise RuntimeError(f"Archive does not exist: {archive}")
    assert_archive_matches_current_platform(archive)

    with tempfile.TemporaryDirectory(prefix="crystal-default-install-smoke-") as tmp:
        temp_dir = Path(tmp)
        home_dir = temp_dir / "home"
        bin_dir = home_dir / ".local" / "bin"
        bin_dir.mkdir(parents=True)
        install_root = home_dir / ".local" / "opt" / "crystal-lattice-cli"
        package_stem = archive_package_stem(archive)
        installed_bundle = install_root / package_stem
        staging_bundle = install_root / f".{package_stem}.staging"
        installed_bundle.mkdir(parents=True)
        staging_bundle.mkdir()
        (installed_bundle / "stale-target").write_text("stale", encoding="utf-8")
        (staging_bundle / "stale-staging").write_text("stale", encoding="utf-8")

        serve_dir = temp_dir / "download"
        serve_dir.mkdir()
        shutil.copy2(INSTALL_SCRIPT, serve_dir / "install.sh")
        shutil.copy2(archive, serve_dir / archive.name)
        (serve_dir / "latest.txt").write_text(
            f"crystal-lattice-cli-v{read_project_version()}\n",
            encoding="utf-8",
        )

        with serve_directory(serve_dir) as download_base:
            installer_env = installer_environment(
                home_dir=home_dir,
                bin_dir=bin_dir,
                download_base=download_base,
            )
            bash = resolve_bash(env=installer_env)
            run(
                [
                    bash,
                    "-c",
                    'curl -fsSL "$CRYSTAL_LATTICE_DOWNLOAD_BASE_URL/install.sh" '
                    "| bash",
                ],
                env=installer_env,
                timeout=300,
            )

        if not installed_bundle.is_dir():
            raise RuntimeError(f"Installer did not create bundle: {installed_bundle}")
        if (installed_bundle / "stale-target").exists():
            raise RuntimeError("Installer did not replace the stale target directory")
        if staging_bundle.exists():
            raise RuntimeError("Installer did not remove the stale staging directory")

        verify_command_name_resolution(installer_env, bash=bash)
        assert_plugin_not_preinstalled(
            installed_bundle / "preinstalled-plugins.json",
            DYNAMIC_PLUGIN_PROBE,
        )
        config_path = prepare_smoke_config(
            installed_bundle
            / "application"
            / "python"
            / "agent_terminal_app"
            / "default_config",
            destination_dir=temp_dir / "config",
            additional_plugin_name=DYNAMIC_PLUGIN_PROBE,
        )
        assert_config_boot(
            [COMMAND_NAME],
            config_path=config_path,
            workspace=temp_dir / "workspace",
            home_dir=home_dir,
            plugin_cache_expectation="populated",
            expected_plugin_id=DYNAMIC_PLUGIN_PROBE,
            base_env=installer_env,
            timeout_seconds=300,
        )


def installer_environment(
    *,
    home_dir: Path,
    bin_dir: Path,
    download_base: str,
) -> dict[str, str]:
    env = dict(os.environ)
    for name in (
        "BIN_DIR",
        "COMMAND_NAME",
        "CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE",
        "DOWNLOAD_BASE_URL",
        "INSTALL_ROOT",
        "VERSION",
        "VIRTUAL_ENV",
    ):
        env.pop(name, None)
    env["HOME"] = home_dir.as_posix()
    env["USERPROFILE"] = str(home_dir.resolve())
    inherited_path = os.pathsep.join(
        entry
        for entry in env.get("PATH", "").split(os.pathsep)
        if not any(
            (Path(entry) / name).exists()
            for name in (
                COMMAND_NAME,
                f"{COMMAND_NAME}.cmd",
                f"{COMMAND_NAME}.exe",
            )
        )
    )
    env["PATH"] = str(bin_dir.resolve()) + os.pathsep + inherited_path
    env["CRYSTAL_LATTICE_DOWNLOAD_BASE_URL"] = download_base
    return env


def verify_command_name_resolution(env: dict[str, str], *, bash: str) -> None:
    run(
        [
            bash,
            "-c",
            "command -v crystal-lattice >/dev/null && "
            "crystal-lattice --runtime-layout-json >/dev/null",
        ],
        env=env,
        timeout=60,
    )
    if os.name == "nt":
        comspec = env.get("COMSPEC") or os.environ.get("COMSPEC", "cmd.exe")
        run(
            [
                comspec,
                "/d",
                "/s",
                "/c",
                "crystal-lattice --runtime-layout-json >NUL",
            ],
            env=env,
            timeout=60,
        )


@contextmanager
def serve_directory(directory: Path) -> Iterator[str]:
    handler = partial(QuietFileHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        address = server.server_address
        host = str(address[0])
        port = int(address[1])
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)
        if thread.is_alive():
            raise RuntimeError("Download server did not stop")


def run(
    command: list[str],
    *,
    env: dict[str, str],
    timeout: float,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=str(ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with status {result.returncode}: "
            f"{subprocess.list2cmdline(command)}\n{result.stdout}"
        )
    return result


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
