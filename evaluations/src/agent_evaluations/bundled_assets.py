from __future__ import annotations

import gzip
from pathlib import Path
import shutil
import subprocess
from typing import Iterable


BUNDLED_PLUGINS_DIRNAME = "bundled_plugins"
EXCLUDED_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
    "node_modules",
    "tests",
}
EXCLUDED_FILE_SUFFIXES = {
    ".log",
    ".pyc",
    ".pyo",
}
EXCLUDED_FILE_NAMES = {
    ".coverage",
}


def copytree_sanitized(
    source: Path,
    destination: Path,
    *,
    excluded_dir_names: Iterable[str] = (),
) -> None:
    excluded_dirs = set(excluded_dir_names).union(EXCLUDED_DIR_NAMES)

    def ignore(_directory: str, names: list[str]) -> set[str]:
        ignored: set[str] = set()
        for name in names:
            path = Path(name)
            if name in excluded_dirs or name.endswith(".egg-info"):
                ignored.add(name)
            elif name in EXCLUDED_FILE_NAMES:
                ignored.add(name)
            elif path.suffix in EXCLUDED_FILE_SUFFIXES:
                ignored.add(name)
        return ignored

    shutil.copytree(source, destination, ignore=ignore)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def create_git_tracked_source_bundle(
    output_path: Path,
    *,
    root: Path | None = None,
    revision: str = "HEAD",
) -> Path:
    repo = (root or repo_root()).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tar_path = output_path.with_suffix("")
    if tar_path.suffix == ".tar":
        tar_output = tar_path
    else:
        tar_output = output_path.parent / f"{output_path.stem}.tar"

    if tar_output.exists():
        tar_output.unlink()
    if output_path.exists():
        output_path.unlink()

    subprocess.run(
        [
            "git",
            "archive",
            "--format=tar",
            f"--output={tar_output}",
            revision,
        ],
        cwd=str(repo),
        check=True,
    )

    with tar_output.open("rb") as source, gzip.open(output_path, "wb") as destination:
        shutil.copyfileobj(source, destination)
    tar_output.unlink()
    return output_path