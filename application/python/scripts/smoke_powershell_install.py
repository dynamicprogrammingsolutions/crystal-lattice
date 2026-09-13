#!/usr/bin/env python3
from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Iterator

if os.name == "nt":
    import winreg
else:  # pragma: no cover - imported only so non-Windows help/errors stay clear
    winreg = None  # type: ignore[assignment]

from boot_smoke import (
    assert_config_boot,
    assert_plugin_not_preinstalled,
    prepare_smoke_config,
)
from distribution_support import (
    archive_package_stem,
    assert_archive_matches_current_platform,
    read_project_version,
    resolve_powershell,
)
from download_server import serve_directory
from progress import StepLogger


ROOT = Path(__file__).resolve().parents[3]
INSTALL_SCRIPT = Path(__file__).resolve().parent / "install.ps1"
DYNAMIC_PLUGIN_PROBE = "generic-callback-app"
COMMAND_NAME = "crystal-lattice"
USER_ENVIRONMENT_KEY = r"Environment"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: smoke_powershell_install.py <archive>")
    if os.name != "nt":
        raise RuntimeError("The PowerShell installer smoke requires Windows")
    archive = Path(sys.argv[1]).expanduser().resolve()
    smoke_test_powershell_install(archive)
    print(f"PowerShell-installer smoke test passed: {archive}")


def smoke_test_powershell_install(archive: Path) -> None:
    if os.name != "nt":
        raise RuntimeError("The PowerShell installer smoke requires Windows")
    if not archive.is_file():
        raise RuntimeError(f"Archive does not exist: {archive}")
    assert_archive_matches_current_platform(archive)

    progress = StepLogger(total_steps=4)
    with tempfile.TemporaryDirectory(prefix="crystal-powershell-install-smoke-") as tmp:
        temp_dir = Path(tmp)
        progress.step("Preparing isolated PowerShell-installer state")
        home_dir = temp_dir / "home"
        local_app_data = home_dir / "AppData" / "Local"
        local_app_data.mkdir(parents=True)
        bin_dir = local_app_data / "Programs" / "Crystal Lattice" / "bin"
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
        shutil.copy2(INSTALL_SCRIPT, serve_dir / "install.ps1")
        shutil.copy2(archive, serve_dir / archive.name)
        (serve_dir / "latest.txt").write_text(
            f"crystal-lattice-cli-v{read_project_version()}\n",
            encoding="utf-8",
        )

        powershell = resolve_powershell()
        with preserved_user_path():
            with serve_directory(serve_dir) as download_base:
                installer_env = installer_environment(
                    home_dir=home_dir,
                    local_app_data=local_app_data,
                    download_base=download_base,
                )
                progress.step("Running the public PowerShell installer with defaults")
                progress.run_visible(
                    [
                        powershell,
                        "-NoLogo",
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-Command",
                        (
                            "Invoke-RestMethod -Uri "
                            '"$env:CRYSTAL_LATTICE_DOWNLOAD_BASE_URL/install.ps1" '
                            "| Invoke-Expression; "
                            "$command = (Get-Command crystal-lattice.cmd "
                            "-CommandType Application -ErrorAction Stop).Source; "
                            "& $command --runtime-layout-json *> $null; "
                            "if ($LASTEXITCODE -ne 0) { "
                            "throw 'installed command did not execute in PowerShell' }"
                        ),
                    ],
                    cwd=ROOT,
                    env=installer_env,
                    timeout=300,
                )

            if not installed_bundle.is_dir():
                raise RuntimeError(
                    f"PowerShell installer did not create bundle: {installed_bundle}"
                )
            if (installed_bundle / "stale-target").exists():
                raise RuntimeError(
                    "PowerShell installer did not replace the stale target directory"
                )
            if staging_bundle.exists():
                raise RuntimeError(
                    "PowerShell installer did not remove the stale staging directory"
                )
            if not (bin_dir / f"{COMMAND_NAME}.cmd").is_file():
                raise RuntimeError(
                    f"PowerShell installer did not create command: {bin_dir}"
                )

            user_path = read_user_path()
            if count_path_entry(user_path, bin_dir) != 1:
                raise RuntimeError(
                    "PowerShell installer did not add its command directory "
                    "exactly once to the user PATH"
                )
            fresh_env = {
                **installer_env,
                "PATH": str(bin_dir.resolve())
                + os.pathsep
                + installer_env.get("PATH", ""),
            }

            progress.step("Resolving the installed command in fresh native terminals")
            verify_native_command_resolution(
                fresh_env,
                powershell=powershell,
                progress=progress,
            )
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
            progress.step(
                "Booting the PowerShell-installed command and installing the probe plugin"
            )
            assert_config_boot(
                [COMMAND_NAME],
                config_path=config_path,
                workspace=temp_dir / "workspace",
                home_dir=home_dir,
                plugin_cache_expectation="populated",
                expected_plugin_id=DYNAMIC_PLUGIN_PROBE,
                base_env=fresh_env,
                timeout_seconds=300,
                progress=progress.detail,
            )


def installer_environment(
    *,
    home_dir: Path,
    local_app_data: Path,
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
    env["HOME"] = str(home_dir.resolve())
    env["USERPROFILE"] = str(home_dir.resolve())
    env["LOCALAPPDATA"] = str(local_app_data.resolve())
    env["TEMP"] = str((home_dir / "Temp").resolve())
    env["TMP"] = env["TEMP"]
    Path(env["TEMP"]).mkdir(parents=True)
    env["PATH"] = os.pathsep.join(
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
    env["CRYSTAL_LATTICE_DOWNLOAD_BASE_URL"] = download_base
    return env


def verify_native_command_resolution(
    env: dict[str, str],
    *,
    powershell: str,
    progress: StepLogger,
) -> None:
    progress.run_visible(
        [
            powershell,
            "-NoLogo",
            "-NoProfile",
            "-Command",
            (
                "$command = (Get-Command crystal-lattice.cmd "
                "-CommandType Application -ErrorAction Stop).Source; "
                "& $command --runtime-layout-json *> $null; "
                "if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }"
            ),
        ],
        cwd=ROOT,
        env=env,
        timeout=60,
    )
    comspec = env.get("COMSPEC") or os.environ.get("COMSPEC", "cmd.exe")
    progress.run_visible(
        [
            comspec,
            "/d",
            "/s",
            "/c",
            "where crystal-lattice >NUL && "
            "crystal-lattice --runtime-layout-json >NUL",
        ],
        cwd=ROOT,
        env=env,
        timeout=60,
    )


def read_user_path() -> str:
    if winreg is None:
        raise RuntimeError("Windows registry is unavailable")
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, USER_ENVIRONMENT_KEY) as key:
            value, _value_type = winreg.QueryValueEx(key, "Path")
    except FileNotFoundError:
        return ""
    return str(value)


def count_path_entry(path_value: str, directory: Path) -> int:
    requested = os.path.normcase(os.path.normpath(str(directory.resolve())))
    return sum(
        os.path.normcase(os.path.normpath(os.path.expandvars(entry.strip())))
        == requested
        for entry in path_value.split(os.pathsep)
        if entry.strip()
    )


@contextmanager
def preserved_user_path() -> Iterator[None]:
    if winreg is None:
        raise RuntimeError("Windows registry is unavailable")
    existed = True
    value = ""
    value_type = winreg.REG_EXPAND_SZ
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, USER_ENVIRONMENT_KEY) as key:
            value, value_type = winreg.QueryValueEx(key, "Path")
    except FileNotFoundError:
        existed = False

    try:
        yield
    finally:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, USER_ENVIRONMENT_KEY) as key:
            if existed:
                winreg.SetValueEx(key, "Path", 0, value_type, value)
            else:
                try:
                    winreg.DeleteValue(key, "Path")
                except FileNotFoundError:
                    pass


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
