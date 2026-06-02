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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smoke-test a Crystal Lattice bundled-Python runtime archive."
    )
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()

    archive = args.archive.expanduser().resolve()
    with tempfile.TemporaryDirectory(prefix="crystal-python-runtime-smoke-") as tmp:
        extract_dir = Path(tmp) / "extract"
        extract_archive(archive, extract_dir)
        package_dir = find_package_dir(extract_dir)
        validate_package(package_dir)
        print(f"Bundled-Python runtime smoke test passed: {package_dir}")


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
    required = [
        launcher,
        python_path(package_dir),
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


def launcher_path(package_dir: Path) -> Path:
    if os.name == "nt":
        return package_dir / "Scripts" / "crystal-lattice.cmd"
    return package_dir / "bin" / "crystal-lattice"


def python_path(package_dir: Path) -> Path:
    windows_python = package_dir / "python" / "python.exe"
    if windows_python.exists():
        return windows_python
    return package_dir / "python" / "bin" / "python"


if __name__ == "__main__":
    main()
