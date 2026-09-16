#!/usr/bin/env python3
"""Compile committed documentation-standard guidance fixture sets."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path


FIXTURE_ROOT = Path(__file__).resolve().parent
SOURCES_ROOT = FIXTURE_ROOT / "sources"
SETS_ROOT = FIXTURE_ROOT / "sets"

BASE_SET_ID = "option-a-checkpoint"
GUIDANCE_PATHS = (
    "AGENTS.md",
    "docs/development/index.md",
    "docs/development/documentation.md",
    "docs/development/crystal-lattice-documentation.md",
    "plugins/AGENTS.md",
    "plugins/docs/AGENTS.md",
)
FAMILIES = (
    "abstract",
    "action-first",
    "file-centered",
    "explicit-contexts",
    "contextual",
)
RULE_MODES = ("generic", "specific")
SPECIFIC_RULES_MARKER = "<!-- SPECIFIC_RULES -->"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_base_files() -> dict[str, bytes]:
    base_root = SETS_ROOT / BASE_SET_ID
    missing = [
        relative for relative in GUIDANCE_PATHS if not (base_root / relative).is_file()
    ]
    if missing:
        raise RuntimeError(
            f"base guidance set {BASE_SET_ID!r} is incomplete: {', '.join(missing)}"
        )
    return {
        relative: (base_root / relative).read_bytes() for relative in GUIDANCE_PATHS
    }


def _replace_section(
    text: str,
    *,
    start_marker: str,
    end_marker: str,
    replacement: str,
) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[:start] + replacement.rstrip() + "\n\n" + text[end:]


def _candidate_files(
    base_files: dict[str, bytes],
    *,
    family: str,
    rule_mode: str,
) -> dict[str, bytes]:
    documentation_section = (
        SOURCES_ROOT / family / "documentation-section.md"
    ).read_text(encoding="utf-8")
    agents_section = (SOURCES_ROOT / family / "agents-section.md").read_text(
        encoding="utf-8"
    )
    if documentation_section.count(SPECIFIC_RULES_MARKER) != 1:
        raise ValueError(
            f"{family} documentation section must contain one "
            f"{SPECIFIC_RULES_MARKER!r}"
        )
    marker_block = f"\n\n{SPECIFIC_RULES_MARKER}\n\n"
    if documentation_section.count(marker_block) != 1:
        raise ValueError(
            f"{family} documentation section must surround "
            f"{SPECIFIC_RULES_MARKER!r} with blank lines"
        )

    if rule_mode == "generic":
        documentation_section = documentation_section.replace(
            marker_block,
            "\n\n",
        )
    elif rule_mode == "specific":
        specific_rules = (SOURCES_ROOT / "specific-rules.md").read_text(
            encoding="utf-8"
        )
        documentation_section = documentation_section.replace(
            marker_block,
            f"\n\n{specific_rules.rstrip()}\n\n",
        )
    else:
        raise ValueError(f"unsupported rule mode: {rule_mode}")

    files = dict(base_files)
    guide_path = "docs/development/documentation.md"
    guide = files[guide_path].decode("utf-8")
    files[guide_path] = _replace_section(
        guide,
        start_marker="## Write pages readers can use",
        end_marker="## Specifications, requirements, and tasks",
        replacement=documentation_section,
    ).encode("utf-8")

    agents = files["AGENTS.md"].decode("utf-8")
    files["AGENTS.md"] = _replace_section(
        agents,
        start_marker="Treat wording from prompts",
        end_marker="Change generated documentation",
        replacement=agents_section,
    ).encode("utf-8")
    return files


def _guidance_file_records(files: dict[str, bytes]) -> list[dict[str, str]]:
    return [
        {
            "path": relative,
            "sha256": _sha256(files[relative]),
        }
        for relative in GUIDANCE_PATHS
    ]


def _combined_sha256(records: list[dict[str, str]]) -> str:
    payload = json.dumps(records, sort_keys=True, separators=(",", ":"))
    return _sha256(payload.encode("utf-8"))


def _root_policy_word_count(agents: str) -> int:
    start = agents.index("## Documentation ownership and routing")
    end = agents.index("**Auxiliary directories**", start)
    return len(agents[start:end].split())


def _manifest(
    files: dict[str, bytes],
    *,
    set_id: str,
    family: str,
    rule_mode: str,
) -> bytes:
    records = _guidance_file_records(files)
    guide = files["docs/development/documentation.md"].decode("utf-8")
    agents = files["AGENTS.md"].decode("utf-8")
    source_files = {}
    if family in FAMILIES:
        source_paths = (
            SOURCES_ROOT / family / "documentation-section.md",
            SOURCES_ROOT / family / "agents-section.md",
        )
        if rule_mode == "specific":
            source_paths += (SOURCES_ROOT / "specific-rules.md",)
        source_files = {
            str(path.relative_to(FIXTURE_ROOT)): _sha256(path.read_bytes())
            for path in source_paths
        }

    payload = {
        "schema": 1,
        "set_id": set_id,
        "family": family,
        "rule_mode": rule_mode,
        "base_set": BASE_SET_ID,
        "combined_sha256": _combined_sha256(records),
        "files": records,
        "source_files": source_files,
        "word_counts": {
            "portable_guide": len(guide.split()),
            "root_documentation_policy": _root_policy_word_count(agents),
        },
    }
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_set(
    root: Path,
    *,
    set_id: str,
    family: str,
    rule_mode: str,
    files: dict[str, bytes],
) -> None:
    target_root = root / set_id
    for relative in GUIDANCE_PATHS:
        target = target_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(files[relative])
    (target_root / "guidance-set.json").write_bytes(
        _manifest(
            files,
            set_id=set_id,
            family=family,
            rule_mode=rule_mode,
        )
    )


def _render(root: Path) -> None:
    base_files = _read_base_files()
    _write_set(
        root,
        set_id=BASE_SET_ID,
        family="checkpoint",
        rule_mode="snapshot",
        files=base_files,
    )
    for family in FAMILIES:
        for rule_mode in RULE_MODES:
            set_id = f"{family}-{rule_mode}"
            _write_set(
                root,
                set_id=set_id,
                family=family,
                rule_mode=rule_mode,
                files=_candidate_files(
                    base_files,
                    family=family,
                    rule_mode=rule_mode,
                ),
            )


def _files_by_path(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        return {}
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _check(rendered_root: Path) -> None:
    rendered = _files_by_path(rendered_root)
    committed = _files_by_path(SETS_ROOT)
    missing = sorted(rendered.keys() - committed.keys())
    extra = sorted(committed.keys() - rendered.keys())
    changed = sorted(
        relative
        for relative in rendered.keys() & committed.keys()
        if rendered[relative] != committed[relative]
    )
    if missing or extra or changed:
        details = []
        if missing:
            details.append("missing committed files: " + ", ".join(missing))
        if extra:
            details.append("unexpected committed files: " + ", ".join(extra))
        if changed:
            details.append("changed committed files: " + ", ".join(changed))
        raise SystemExit("\n".join(details))


def _replace_sets(rendered_root: Path) -> None:
    if SETS_ROOT.exists():
        shutil.rmtree(SETS_ROOT)
    shutil.copytree(rendered_root, SETS_ROOT)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify committed guidance sets match the sources",
    )
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(
        prefix=".guidance-sets-",
        dir=FIXTURE_ROOT,
    ) as temporary:
        rendered_root = Path(temporary) / "sets"
        _render(rendered_root)
        if args.check:
            _check(rendered_root)
        else:
            _replace_sets(rendered_root)


if __name__ == "__main__":
    main()
