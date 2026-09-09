#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from crystal_lattice_distribution import ARCHIVE_ENV, current_platform_archive


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_crystal_lattice_python_runtime_archive.py"),
        ],
        cwd=str(ROOT),
        check=True,
    )
    archive = current_platform_archive().resolve()
    if not archive.is_file():
        raise RuntimeError(f"Current-platform archive does not exist: {archive}")
    env = dict(os.environ)
    env[ARCHIVE_ENV] = archive.as_posix()
    subprocess.run(
        ["bash", str(ROOT / "scripts" / "install.sh")],
        cwd=str(ROOT),
        env=env,
        check=True,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
