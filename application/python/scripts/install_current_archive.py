#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import sys

from distribution_support import (
    ARCHIVE_ENV,
    current_platform_archive,
    resolve_bash,
    resolve_configured_archive,
)
from progress import StepLogger


ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parent


def main() -> None:
    progress = StepLogger(total_steps=2)
    progress.step("Resolving the bundled-Python archive to install")
    archive = resolve_configured_archive()
    if archive is None:
        progress.detail("No prebuilt archive supplied; building one now")
        progress.run_visible(
            [
                sys.executable,
                str(SCRIPT_DIR / "build_runtime_archive.py"),
            ],
            cwd=ROOT,
        )
        archive = current_platform_archive().resolve()
    else:
        progress.detail(f"archive: {archive}")
    if not archive.is_file():
        raise RuntimeError(f"Current-platform archive does not exist: {archive}")
    env = dict(os.environ)
    env[ARCHIVE_ENV] = archive.as_posix()
    progress.step("Installing the archive through the public installer")
    progress.run_visible(
        [resolve_bash(env=env), str(SCRIPT_DIR / "install.sh")],
        cwd=ROOT,
        env=env,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
