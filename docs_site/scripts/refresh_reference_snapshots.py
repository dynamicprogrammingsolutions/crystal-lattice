#!/usr/bin/env python3
"""Refresh inspectable reference Markdown from an existing MkDocs build."""

from __future__ import annotations

import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_SITE_DIR = REPO_ROOT / "docs_site"
DIST_REFERENCE_DIR = DOCS_SITE_DIR / "dist" / "reference"
DOCS_REFERENCE_DIR = REPO_ROOT / "docs" / "reference"


def remove_and_recreate(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def target_for_generated_reference(source: Path) -> Path | None:
    relative = source.relative_to(DIST_REFERENCE_DIR)
    if relative.name != "index.md":
        return None
    parent = relative.parent
    if parent == Path("."):
        return DOCS_REFERENCE_DIR / "index.md"
    return DOCS_REFERENCE_DIR / parent.with_suffix(".md")


def refresh_reference_snapshots() -> None:
    remove_and_recreate(DOCS_REFERENCE_DIR)
    if not DIST_REFERENCE_DIR.exists():
        raise FileNotFoundError(
            f"Missing built reference output: {DIST_REFERENCE_DIR}. "
            "Run `cd docs_site && mkdocs build` first."
        )

    for source in sorted(DIST_REFERENCE_DIR.rglob("index.md")):
        target = target_for_generated_reference(source)
        if target is None:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def main() -> int:
    refresh_reference_snapshots()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())