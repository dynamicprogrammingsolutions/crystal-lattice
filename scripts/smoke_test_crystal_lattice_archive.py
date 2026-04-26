#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smoke-test a Crystal Lattice binary release archive."
    )
    parser.add_argument("archive", type=Path, help="release archive to validate")
    args = parser.parse_args()

    archive = args.archive.resolve()
    if not archive.is_file():
        raise RuntimeError(f"Archive does not exist: {archive}")

    with tempfile.TemporaryDirectory(prefix="crystal-lattice-smoke-") as temp_dir:
        extract_dir = Path(temp_dir)
        extract_archive(archive, extract_dir)
        bundle_dir = find_bundle_dir(extract_dir)
        validate_bundle(bundle_dir)
        print(f"Bundle smoke test passed: {bundle_dir}")


def extract_archive(archive: Path, extract_dir: Path) -> None:
    if archive.name.endswith(".tar.gz"):
        with tarfile.open(archive, "r:gz") as tar:
            safe_extract_tar(tar, extract_dir)
        return

    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as zip_file:
            safe_extract_zip(zip_file, extract_dir)
        return

    raise RuntimeError(f"Unsupported archive format: {archive}")


def safe_extract_tar(tar: tarfile.TarFile, extract_dir: Path) -> None:
    base = extract_dir.resolve()
    for member in tar.getmembers():
        target = (extract_dir / member.name).resolve()
        if not is_relative_to(target, base):
            raise RuntimeError(
                f"Archive member escapes extraction directory: {member.name}"
            )
    tar.extractall(extract_dir)


def safe_extract_zip(zip_file: zipfile.ZipFile, extract_dir: Path) -> None:
    base = extract_dir.resolve()
    for member in zip_file.namelist():
        target = (extract_dir / member).resolve()
        if not is_relative_to(target, base):
            raise RuntimeError(f"Archive member escapes extraction directory: {member}")
    zip_file.extractall(extract_dir)


def is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


def find_bundle_dir(extract_dir: Path) -> Path:
    directories = [path for path in extract_dir.iterdir() if path.is_dir()]
    if len(directories) != 1:
        names = ", ".join(sorted(path.name for path in directories))
        raise RuntimeError(
            f"Expected exactly one extracted bundle directory, found: {names}"
        )
    return directories[0]


def validate_bundle(bundle_dir: Path) -> None:
    executable = bundle_dir / executable_name()
    required_paths = [
        executable,
        bundle_dir / "_internal" / "agent_terminal_app" / "runtime_layout.json",
        bundle_dir
        / "_internal"
        / "agent_terminal_app"
        / "default_config"
        / "config.json",
        bundle_dir / "_internal" / "plugins" / "openrouter" / "agent_plugin.json",
        bundle_dir / "_internal" / "plugins" / "codex-tools" / "agent_plugin.json",
        bundle_dir
        / "_internal"
        / "plugins"
        / "feature-system-message"
        / "agent_plugin.json",
    ]
    for path in required_paths:
        if not path.exists():
            raise RuntimeError(f"Expected bundled path is missing: {path}")

    if not os.name == "nt" and not os.access(executable, os.X_OK):
        raise RuntimeError(f"Bundled executable is not executable: {executable}")

    forbidden_paths = [
        bundle_dir / "_internal" / "agent_terminal_app" / "default_config" / "auth",
        bundle_dir
        / "_internal"
        / "agent_terminal_app"
        / "default_config"
        / ".plugin_cache",
    ]
    for path in forbidden_paths:
        if path.exists():
            raise RuntimeError(f"Forbidden generated/private path was bundled: {path}")

    run([str(executable), "--help"])
    layout = json.loads(run([str(executable), "--runtime-layout-json"]).stdout)
    if layout.get("layout") != "bundled":
        raise RuntimeError(
            f"Expected bundled runtime layout, got: {layout.get('layout')!r}"
        )

    env_overrides = layout.get("env_overrides")
    if not isinstance(env_overrides, dict) or "BUILTIN_PLUGINS" not in env_overrides:
        raise RuntimeError("Runtime layout did not expose BUILTIN_PLUGINS")

    expected_plugins = (bundle_dir / "_internal" / "plugins").resolve()
    actual_plugins = Path(env_overrides["BUILTIN_PLUGINS"]).resolve()
    if actual_plugins != expected_plugins:
        raise RuntimeError(
            "BUILTIN_PLUGINS points to the wrong path: "
            f"expected {expected_plugins}, got {actual_plugins}"
        )


def executable_name() -> str:
    return "crystal-lattice.exe" if os.name == "nt" else "crystal-lattice"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
