#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import platform
import subprocess
import sys

from install_crystal_lattice_archive import (
    current_platform_archive,
    normalize_arch,
    normalize_platform,
)


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_ENV = "CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE"
TEST_IDS = {
    "clean-env": (
        "application/python/tests/test_cli_distribution_levels.py::"
        "test_level_1_clean_python_environment_boots_default_config"
    ),
    "bundle": (
        "application/python/tests/test_cli_distribution_levels.py::"
        "test_level_2_bundled_python_archive_boots_default_config"
    ),
    "install": (
        "application/python/tests/test_cli_distribution_levels.py::"
        "test_level_3_installed_wrapper_boots_default_config"
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one Crystal Lattice CLI distribution test level."
    )
    parser.add_argument("level", choices=sorted(TEST_IDS))
    args = parser.parse_args()

    env = dict(os.environ)
    if args.level in {"bundle", "install"}:
        archive = resolve_archive()
        env[ARCHIVE_ENV] = str(archive)
        print(f"[cli-distribution] Using archive: {archive}", flush=True)

    run(
        [
            sys.executable,
            "-m",
            "pytest",
            TEST_IDS[args.level],
            "-q",
            "-m",
            "integration and slow_integration",
        ],
        env=env,
    )


def resolve_archive() -> Path:
    configured = os.environ.get(ARCHIVE_ENV)
    if configured:
        archive = Path(configured).expanduser().resolve()
    else:
        print(
            "[cli-distribution] Building archive in an isolated Nox environment",
            flush=True,
        )
        run([sys.executable, "-m", "nox", "-s", "build_bundle"])
        archive = current_platform_archive().resolve()

    if not archive.is_file():
        raise RuntimeError(f"Bundled-Python archive does not exist: {archive}")
    assert_archive_matches_current_platform(archive)
    return archive


def assert_archive_matches_current_platform(archive: Path) -> None:
    target = (
        f"{normalize_platform(platform.system())}-"
        f"{normalize_arch(platform.machine())}"
    )
    if f"-{target}." not in archive.name:
        raise RuntimeError(
            f"Archive {archive.name!r} does not match current platform {target!r}"
        )


def run(
    command: list[str],
    *,
    env: dict[str, str] | None = None,
) -> None:
    result = subprocess.run(
        command,
        cwd=str(ROOT),
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with status {result.returncode}: "
            f"{subprocess.list2cmdline(command)}"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
