#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

from crystal_lattice_distribution import (
    assert_archive_matches_current_platform,
    current_platform_archive,
    resolve_configured_archive,
)


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_SCRIPTS = {
    "source-install": ROOT / "scripts" / "smoke_test_crystal_lattice_source_install.py",
    "archive": ROOT
    / "scripts"
    / "smoke_test_crystal_lattice_python_runtime_archive.py",
    "default-install": ROOT
    / "scripts"
    / "smoke_test_crystal_lattice_default_install.py",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one direct Crystal Lattice CLI distribution smoke."
    )
    parser.add_argument("scenario", choices=sorted(SCENARIO_SCRIPTS))
    args = parser.parse_args()

    command = [sys.executable, str(SCENARIO_SCRIPTS[args.scenario])]
    if args.scenario in {"archive", "default-install"}:
        archive = resolve_archive()
        print(f"[cli-distribution] Using archive: {archive}", flush=True)
        command.append(str(archive))

    run(command)


def resolve_archive() -> Path:
    archive = resolve_configured_archive()
    if archive is None:
        print(
            "[cli-distribution] Building archive with a managed Python runtime",
            flush=True,
        )
        run(
            [
                sys.executable,
                str(
                    ROOT / "scripts" / "build_crystal_lattice_python_runtime_archive.py"
                ),
            ]
        )
        archive = current_platform_archive().resolve()

    if not archive.is_file():
        raise RuntimeError(f"Bundled-Python archive does not exist: {archive}")
    assert_archive_matches_current_platform(archive)
    return archive


def run(
    command: list[str],
) -> None:
    result = subprocess.run(
        command,
        cwd=str(ROOT),
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
