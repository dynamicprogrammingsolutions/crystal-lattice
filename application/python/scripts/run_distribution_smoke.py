#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

from distribution_support import (
    assert_archive_matches_current_platform,
    current_platform_archive,
    resolve_configured_archive,
)
from progress import StepLogger


ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parent
SCENARIO_SCRIPTS = {
    "source-install": SCRIPT_DIR / "smoke_source_install.py",
    "archive": SCRIPT_DIR / "smoke_runtime_archive.py",
    "default-install": SCRIPT_DIR / "smoke_default_install.py",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one direct Crystal Lattice CLI distribution smoke."
    )
    parser.add_argument("scenario", choices=sorted(SCENARIO_SCRIPTS))
    args = parser.parse_args()

    progress = StepLogger(
        total_steps=2 if args.scenario in {"archive", "default-install"} else 1
    )
    command = [sys.executable, str(SCENARIO_SCRIPTS[args.scenario])]
    if args.scenario in {"archive", "default-install"}:
        progress.step("Resolving the current-platform bundled-Python archive")
        archive = resolve_archive(progress=progress)
        progress.detail(f"archive: {archive}")
        command.append(str(archive))

    progress.step(f"Running the {scenario_label(args.scenario)}")
    run(command, progress=progress)


def scenario_label(scenario: str) -> str:
    return {
        "source-install": "source-installation smoke",
        "archive": "extracted-archive smoke",
        "default-install": "default-installer smoke",
    }[scenario]


def resolve_archive(*, progress: StepLogger | None = None) -> Path:
    archive = resolve_configured_archive()
    if archive is None:
        if progress is not None:
            progress.detail("No prebuilt archive supplied; building one now")
        run(
            [
                sys.executable,
                str(SCRIPT_DIR / "build_runtime_archive.py"),
            ],
            progress=progress,
        )
        archive = current_platform_archive().resolve()

    if not archive.is_file():
        raise RuntimeError(f"Bundled-Python archive does not exist: {archive}")
    assert_archive_matches_current_platform(archive)
    return archive


def run(
    command: list[str],
    *,
    progress: StepLogger | None = None,
) -> None:
    if progress is not None:
        progress.command(command)
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
