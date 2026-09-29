"""Synchronize portable guidance from a Crystal Lattice checkout into a
consuming repository.

This script is vendored unchanged into each consumer's guidance directory
next to ``compiler.py``. The consumer describes itself in ``sync.toml``
placed in the same directory:

    format = 1
    consumer_id = "example"

    [sync]
    sections = ["documentation", "requirements", "testing-strategy", "tasks-v7"]

    [[sync.files]]
    source = "docs/development/documentation.md"
    destinations = ["docs/development/documentation.md"]

    [[sync.roots]]
    path = "../.."          # relative to this script's directory

Each root receives every configured file destination; bundle sections and
the vendored compiler always land inside the guidance directory itself.
``roots`` may be omitted when only sections are synchronized.

The sync also refreshes the vendored copy of this script and rewrites
``current/bundle.toml`` from the configured section list, and records
source revision and hashes in ``sync-lock.json``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tomllib
from pathlib import Path


GUIDANCE_ROOT = Path(__file__).resolve().parent
PLATFORM_GUIDANCE = Path("maintainer/guidance")
PORTABLE_TOOLING = ("compiler.py", "consumer_sync.py")
LOCK_NAME = "sync-lock.json"


class ConsumerConfigError(ValueError):
    pass


def _load_config(guidance_root: Path) -> dict[str, object]:
    config_path = guidance_root / "sync.toml"
    if not config_path.is_file():
        raise ConsumerConfigError(f"missing consumer config: {config_path}")
    with config_path.open("rb") as stream:
        config = tomllib.load(stream)
    consumer_id = config.get("consumer_id")
    if not isinstance(consumer_id, str) or not consumer_id:
        raise ConsumerConfigError("sync.toml requires a consumer_id string")
    sync = config.get("sync")
    if not isinstance(sync, dict):
        raise ConsumerConfigError("sync.toml requires a [sync] table")
    sections = sync.get("sections")
    if not isinstance(sections, list) or not all(
        isinstance(name, str) and name for name in sections
    ):
        raise ConsumerConfigError(
            "[sync] requires a sections list of section names"
        )
    files = sync.get("files", [])
    if not isinstance(files, list):
        raise ConsumerConfigError("[sync] files must be a list of tables")
    for entry in files:
        if not isinstance(entry, dict):
            raise ConsumerConfigError("[sync] files entries must be tables")
        if not isinstance(entry.get("source"), str):
            raise ConsumerConfigError("file entries require a source path")
        destinations = entry.get("destinations")
        if not isinstance(destinations, list) or not all(
            isinstance(destination, str) for destination in destinations
        ):
            raise ConsumerConfigError(
                "file entries require a destinations path list"
            )
    roots = sync.get("roots", [])
    if not isinstance(roots, list):
        raise ConsumerConfigError("[sync] roots must be a list of tables")
    for root in roots:
        if not isinstance(root, dict) or not isinstance(root.get("path"), str):
            raise ConsumerConfigError("root entries require a path string")
    return config


def _bundle_manifest(consumer_id: str, sections: list[str]) -> str:
    lines = ["format = 1", f'id = "{consumer_id}"', "", "[sections]"]
    lines.extend(f'{name} = "sections/{name}.md"' for name in sections)
    return "\n".join(lines) + "\n"


def _sources(platform: Path, config: dict[str, object]) -> dict[Path, tuple[Path, ...]]:
    sync = config["sync"]
    assert isinstance(sync, dict)
    sections = sync["sections"]
    assert isinstance(sections, list)
    current = platform / PLATFORM_GUIDANCE / "current"
    with (current / "bundle.toml").open("rb") as stream:
        manifest = tomllib.load(stream)
    manifest_sections = manifest.get("sections", {})
    if not isinstance(manifest_sections, dict):
        raise ValueError("Crystal Lattice current bundle lacks [sections]")

    mapping: dict[Path, tuple[Path, ...]] = {}
    for name in PORTABLE_TOOLING:
        source = platform / PLATFORM_GUIDANCE / name
        mapping[source] = (GUIDANCE_ROOT / name,)
    for name in sections:
        relative = manifest_sections.get(name)
        if not isinstance(relative, str) or not relative:
            raise ValueError(
                f"Crystal Lattice current bundle lacks section {name!r}"
            )
        mapping[current / relative] = (GUIDANCE_ROOT / "current" / "sections" / f"{name}.md",)
    roots = [
        (GUIDANCE_ROOT / root["path"]).resolve()
        for root in sync.get("roots", [])
    ]
    for entry in sync.get("files", []):
        destinations = tuple(
            root / destination
            for root in roots
            for destination in entry["destinations"]
        )
        if not destinations:
            raise ConsumerConfigError(
                f"file {entry['source']!r} has no destination roots"
            )
        mapping[platform / entry["source"]] = destinations
    return mapping


def _revision(platform: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=platform,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synchronize(platform: Path, *, check: bool) -> bool:
    config = _load_config(GUIDANCE_ROOT)
    consumer_id = config["consumer_id"]
    assert isinstance(consumer_id, str)
    sync = config["sync"]
    assert isinstance(sync, dict)
    sections = sync["sections"]
    assert isinstance(sections, list)

    mapping = _sources(platform, config)
    changed = False
    records: list[dict[str, object]] = []
    manifest = GUIDANCE_ROOT / "current" / "bundle.toml"
    manifest_content = _bundle_manifest(consumer_id, [str(name) for name in sections]).encode()
    manifest_matches = (
        manifest.is_file() and manifest.read_bytes() == manifest_content
    )
    if not manifest_matches:
        changed = True
        if not check:
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_bytes(manifest_content)

    for source, destinations in mapping.items():
        if not source.is_file():
            raise FileNotFoundError(source)
        content = source.read_bytes()
        for destination in destinations:
            matches = (
                destination.is_file() and destination.read_bytes() == content
            )
            records.append(
                {
                    "source": source.relative_to(platform).as_posix(),
                    "destination": str(destination),
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "matches": matches,
                }
            )
            if matches:
                continue
            changed = True
            if not check:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)

    if check and changed:
        raise ValueError(
            "synced guidance differs; run without --check:\n"
            + json.dumps(records, indent=2, sort_keys=True)
        )

    if not check:
        lock = {
            "schema_version": 2,
            "source_revision": _revision(platform),
            "files": [
                {
                    "source": source.relative_to(platform).as_posix(),
                    "sha256": _sha256(source),
                }
                for source in mapping
            ],
        }
        (GUIDANCE_ROOT / LOCK_NAME).write_text(
            json.dumps(lock, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Synchronize portable guidance from a Crystal Lattice checkout."
        ),
    )
    parser.add_argument(
        "platform_repo",
        type=Path,
        help="Path to the Crystal Lattice repository or worktree",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report drift without writing files",
    )
    args = parser.parse_args()
    source = args.platform_repo.expanduser().resolve()
    if not source.is_dir():
        parser.error(f"not a directory: {source}")
    try:
        changed = synchronize(source, check=args.check)
    except (ConsumerConfigError, FileNotFoundError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    if args.check:
        print("Portable guidance is synchronized.")
    elif changed:
        print("Synchronized portable guidance. Recompile outputs next.")
    else:
        print("Portable guidance was already synchronized.")


if __name__ == "__main__":
    main()
