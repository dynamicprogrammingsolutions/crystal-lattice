#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import zipfile

from boot_smoke import (
    assert_config_boot,
    assert_plugin_not_preinstalled,
    prepare_smoke_config,
)
from distribution_support import normalize_arch, normalize_platform
from headless_access_smoke import assert_headless_access
from progress import StepLogger


DYNAMIC_PLUGIN_PROBE = "generic-callback-app"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smoke-test a Crystal Lattice bundled-Python runtime archive."
    )
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()

    archive = args.archive.expanduser().resolve()
    smoke_test_archive(archive)
    print(f"Extracted-archive smoke test passed: {archive}")


def smoke_test_archive(archive: Path) -> None:
    if not archive.is_file():
        raise RuntimeError(f"Archive does not exist: {archive}")

    progress = StepLogger(total_steps=5)
    with tempfile.TemporaryDirectory(prefix="crystal-python-runtime-smoke-") as tmp:
        temp_dir = Path(tmp)
        extract_dir = temp_dir / "extract"
        progress.step("Extracting the bundled-Python runtime archive")
        extract_archive(archive, extract_dir)
        package_dir = find_package_dir(extract_dir)

        progress.step("Validating the extracted runtime package")
        validate_package(package_dir)
        assert_plugin_not_preinstalled(
            package_dir / "preinstalled-plugins.json",
            DYNAMIC_PLUGIN_PROBE,
        )
        progress.step("Preparing a clean config with the dynamic plugin probe")
        config_path = prepare_smoke_config(
            package_dir
            / "application"
            / "python"
            / "agent_terminal_app"
            / "default_config",
            destination_dir=temp_dir / "config",
            additional_plugin_name=DYNAMIC_PLUGIN_PROBE,
        )
        progress.step("Booting the archive launcher and installing the probe plugin")
        assert_config_boot(
            [launcher_path(package_dir)],
            config_path=config_path,
            workspace=temp_dir / "workspace",
            home_dir=temp_dir / "home",
            plugin_cache_expectation="populated",
            expected_plugin_id=DYNAMIC_PLUGIN_PROBE,
            timeout_seconds=300,
            progress=progress.detail,
        )
        progress.step("Verifying archive CLI and Python SDK headless access")
        assert_headless_access(
            [launcher_path(package_dir)],
            python=python_path(package_dir),
            config_path=config_path,
            workspace=temp_dir / "headless access workspace",
            home_dir=temp_dir / "headless access home",
        )


def extract_archive(archive: Path, extract_dir: Path) -> None:
    extract_dir.mkdir(parents=True)
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as zip_archive:
            zip_archive.extractall(extract_dir)
        return
    with tarfile.open(archive, "r:gz") as tar_archive:
        tar_archive.extractall(extract_dir)


def find_package_dir(extract_dir: Path) -> Path:
    directories = [path for path in extract_dir.iterdir() if path.is_dir()]
    if len(directories) != 1:
        names = ", ".join(path.name for path in directories)
        raise RuntimeError(f"Expected exactly one extracted package, found: {names}")
    return directories[0]


def validate_package(package_dir: Path) -> None:
    launcher = launcher_path(package_dir)
    manifest = json.loads(
        (package_dir / "runtime-package.json").read_text(encoding="utf-8")
    )
    required = [
        launcher,
        python_path(package_dir),
        package_dir / "preinstalled-plugins.json",
        package_dir / "runtime-package.json",
        package_dir / "application" / "python" / "agent_terminal_app" / "__main__.py",
        package_dir
        / "application"
        / "python"
        / "agent_terminal_app"
        / "runtime_layout.json",
        package_dir / "core" / "python" / "agent_app",
        package_dir / "core" / "python" / "agent_core",
        package_dir / "plugins" / "message-export-actions" / "agent_plugin.json",
        package_dir / "scripts" / "build_crystal_lattice_binary.py",
    ]
    for path in required:
        if not path.exists():
            raise RuntimeError(f"Expected package path is missing: {path}")

    validate_native_python_identity(package_dir, manifest)
    validate_portable_python_links(package_dir, manifest)

    output = subprocess.check_output(
        [str(launcher), "--runtime-layout-json"],
        cwd=str(package_dir),
        text=True,
    )
    layout = json.loads(output)
    if layout.get("layout") != "python-runtime":
        raise RuntimeError(
            f"Expected python-runtime layout, got: {layout.get('layout')}"
        )
    env_overrides = layout.get("env_overrides")
    if not isinstance(env_overrides, dict):
        raise RuntimeError("Runtime layout output missing env_overrides")
    if (
        Path(env_overrides.get("BUILTIN_PLUGINS", "")).resolve()
        != (package_dir / "plugins").resolve()
    ):
        raise RuntimeError("Runtime layout does not point BUILTIN_PLUGINS at plugins/")
    if (
        Path(env_overrides.get("CRYSTAL_PLUGIN_PYTHON", "")).resolve()
        != python_path(package_dir).resolve()
    ):
        raise RuntimeError(
            "Runtime layout does not point CRYSTAL_PLUGIN_PYTHON at packaged Python"
        )
    if (
        Path(env_overrides.get("CRYSTAL_PREINSTALLED_PLUGIN_MANIFEST", "")).resolve()
        != (package_dir / "preinstalled-plugins.json").resolve()
    ):
        raise RuntimeError(
            "Runtime layout does not point "
            "CRYSTAL_PREINSTALLED_PLUGIN_MANIFEST at preinstalled-plugins.json"
        )


def validate_native_python_identity(
    package_dir: Path, manifest: dict[str, object]
) -> None:
    output = subprocess.check_output(
        [
            str(python_path(package_dir)),
            "-c",
            (
                "import json, platform, sys; "
                "print(json.dumps({'platform': sys.platform, "
                "'machine': platform.machine()}))"
            ),
        ],
        cwd=str(package_dir),
        text=True,
    )
    identity = json.loads(output)
    actual_platform = normalize_platform(str(identity.get("platform", "")))
    actual_arch = normalize_arch(str(identity.get("machine", "")))
    expected_platform = normalize_platform(str(manifest.get("platform", "")))
    expected_arch = normalize_arch(str(manifest.get("arch", "")))
    if (actual_platform, actual_arch) != (expected_platform, expected_arch):
        raise RuntimeError(
            "Packaged Python identity does not match runtime manifest: "
            f"expected {expected_platform}-{expected_arch}, "
            f"got {actual_platform}-{actual_arch}"
        )


def validate_portable_python_links(
    package_dir: Path, manifest: dict[str, object]
) -> None:
    if manifest.get("platform") != "darwin":
        return
    unsafe: list[tuple[Path, str]] = []
    for binary in iter_macos_native_binaries(package_dir):
        output = subprocess.check_output(["otool", "-L", str(binary)], text=True)
        unsafe.extend(
            (binary, dependency)
            for dependency in (
                line.strip().split(" ", 1)[0] for line in output.splitlines()[1:]
            )
            if Path(dependency).name != binary.name
            and is_unsafe_macos_library_reference(dependency)
        )
    if unsafe:
        formatted = "\n".join(
            f"- {binary.relative_to(package_dir)} -> {dependency}"
            for binary, dependency in unsafe
        )
        raise RuntimeError(
            "Packaged macOS native files have non-portable library references:\n"
            f"{formatted}"
        )


def iter_macos_native_binaries(package_dir: Path) -> list[Path]:
    candidates = {
        python_path(package_dir),
        *package_dir.rglob("*.dylib"),
        *package_dir.rglob("*.so"),
    }
    return sorted(
        path for path in candidates if path.is_file() and not path.is_symlink()
    )


def is_unsafe_macos_library_reference(path: str) -> bool:
    return path.startswith("/") and not (
        path.startswith("/System/Library/") or path.startswith("/usr/lib/")
    )


def launcher_path(package_dir: Path) -> Path:
    if os.name == "nt":
        return package_dir / "Scripts" / "crystal-lattice.cmd"
    return package_dir / "bin" / "crystal-lattice"


def python_path(package_dir: Path) -> Path:
    windows_python = package_dir / "python" / "python.exe"
    if windows_python.exists():
        return windows_python
    windows_venv_python = package_dir / "python" / "Scripts" / "python.exe"
    if windows_venv_python.exists():
        return windows_venv_python
    return package_dir / "python" / "bin" / "python"


if __name__ == "__main__":
    main()
