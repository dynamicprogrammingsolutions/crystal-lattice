#!/usr/bin/env python3
"""Bump the crystal-lattice-cli version for a release preparation commit.

Updates the authoritative version in ``application/python/pyproject.toml`` and
syncs the previous version string in the documentation files that reference it
(the root README status line, the application README install/archive examples,
and the deploy runbook examples).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Tuple


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = Path("application") / "python" / "pyproject.toml"
DOC_PATHS = (
    Path("README.md"),
    Path("application") / "python" / "README.md",
    Path("deploy") / "aws-cli-downloads" / "README.md",
)
VERSION_LINE_RE = re.compile(r'^version = "(\d+)\.(\d+)\.(\d+)"$')
# Lines mentioning agent-core carry the independent core package version and
# must never receive a CLI version replacement.
CORE_REFERENCE_MARKER = "agent-core"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Bump the crystal-lattice-cli version in application/python/"
            "pyproject.toml and sync the previous version string in the "
            "documentation files that reference it."
        )
    )
    parser.add_argument(
        "--bump",
        choices=("patch", "minor", "major"),
        default="patch",
        help="version segment to bump (default: patch)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=ROOT,
        help="repository root (default: the repository containing this script)",
    )
    return parser.parse_args(argv)


def bump_version(version: Tuple[int, int, int], segment: str) -> Tuple[int, int, int]:
    major, minor, patch = version
    if segment == "patch":
        return major, minor, patch + 1
    if segment == "minor":
        return major, minor + 1, 0
    return major + 1, 0, 0


def replace_doc_versions(text: str, old: str, new: str) -> tuple[str, int]:
    """Replace CLI version references in ``text`` with digit guards.

    Neighboring digits block a match so a future ``0.1.10`` is never corrupted
    by a ``0.1.1`` replacement, and lines referencing ``agent-core`` keep the
    independent core package version.
    """

    pattern = re.compile(rf"(?<!\d){re.escape(old)}(?!\d)")
    updated_lines: list[str] = []
    count = 0
    for line in text.splitlines(keepends=True):
        if CORE_REFERENCE_MARKER in line:
            updated_lines.append(line)
            continue
        updated_line, line_count = pattern.subn(new, line)
        count += line_count
        updated_lines.append(updated_line)
    return "".join(updated_lines), count


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.expanduser().resolve()
    pyproject = repo_root / PYPROJECT_PATH
    if not pyproject.is_file():
        print(f"Could not find {pyproject}", file=sys.stderr)
        return 1

    lines = pyproject.read_text(encoding="utf-8").splitlines(keepends=True)
    version_indexes = [
        index for index, line in enumerate(lines) if VERSION_LINE_RE.match(line)
    ]
    if len(version_indexes) != 1:
        print(
            f"Expected exactly one 'version = \"X.Y.Z\"' line in {pyproject}, "
            f"found {len(version_indexes)}",
            file=sys.stderr,
        )
        return 1

    index = version_indexes[0]
    match = VERSION_LINE_RE.match(lines[index])
    assert match is not None  # guaranteed by the scan above
    current = tuple(int(part) for part in match.groups())
    updated = bump_version(current, args.bump)
    old_version = ".".join(str(part) for part in current)
    new_version = ".".join(str(part) for part in updated)

    ending = "\n" if lines[index].endswith("\n") else ""
    lines[index] = f'version = "{new_version}"{ending}'
    pyproject.write_text("".join(lines), encoding="utf-8")

    print(f"crystal-lattice-cli {old_version} -> {new_version}")
    print(f"  {PYPROJECT_PATH.as_posix()}: version updated")
    for relative in DOC_PATHS:
        doc_path = repo_root / relative
        if not doc_path.is_file():
            continue
        doc_text = doc_path.read_text(encoding="utf-8")
        updated_text, count = replace_doc_versions(doc_text, old_version, new_version)
        if count:
            doc_path.write_text(updated_text, encoding="utf-8")
        print(f"  {relative.as_posix()}: {count} reference(s) updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
