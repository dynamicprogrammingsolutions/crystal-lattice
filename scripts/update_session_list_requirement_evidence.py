#!/usr/bin/env python3
"""Update generated test links in the session-list requirement tables."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Iterable, Sequence


_EVIDENCE_MARKER = "<!-- test-evidence -->"
_REQUIREMENT_ID = re.compile(r"SLIST-\d{3}")
_ANNOTATION = re.compile(r"^\s*#\s*-\s*(SLIST-\d{3}):\s*(\S(?:.*\S)?)\s*$")
_TEST_DEFINITION = re.compile(r"^\s*(?:async\s+)?def\s+(test_[A-Za-z0-9_]+)\s*\(")
_INTEGRATION_MARKER = re.compile(r"^\s*@pytest\.mark\.integration(?:\(|\s*$)")


@dataclass(frozen=True)
class TestEvidence:
    requirement_id: str
    path: Path
    line: int
    test_name: str
    description: str


def _parse_test_evidence(path: Path) -> list[TestEvidence]:
    pending: list[tuple[str, str]] = []
    evidence: list[TestEvidence] = []
    in_requirements = False
    integration_marked = False

    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if line.strip() == "# Requirements:":
            pending = []
            in_requirements = True
            integration_marked = False
            continue

        annotation = _ANNOTATION.match(line)
        if in_requirements and annotation is not None:
            pending.append((annotation.group(1), annotation.group(2)))
            continue

        if in_requirements and _INTEGRATION_MARKER.match(line):
            integration_marked = True
            continue

        definition = _TEST_DEFINITION.match(line)
        if definition is not None:
            if not pending:
                in_requirements = False
                continue
            if not integration_marked:
                raise ValueError(
                    f"{path}:{line_number} has SLIST evidence annotations "
                    "but is not marked pytest.mark.integration"
                )
            for requirement_id, description in pending:
                evidence.append(
                    TestEvidence(
                        requirement_id=requirement_id,
                        path=path,
                        line=line_number,
                        test_name=definition.group(1),
                        description=description,
                    )
                )
            pending = []
            in_requirements = False
            integration_marked = False
            continue

        stripped = line.strip()
        if in_requirements and (
            not stripped or stripped.startswith("#") or stripped.startswith("@")
        ):
            continue
        pending = []
        in_requirements = False
        integration_marked = False

    return evidence


def _find_repository_root(path: Path) -> Path:
    for candidate in (path, *path.parents):
        if (candidate / ".git").exists():
            return candidate
    raise ValueError(f"Could not find repository root from {path}")


def _find_package_root(requirements_path: Path, repository_root: Path) -> Path:
    for candidate in requirements_path.parents:
        if candidate == repository_root:
            break
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return repository_root


def _display_path(
    test_path: Path,
    *,
    package_root: Path,
    repository_root: Path,
) -> str:
    try:
        return test_path.relative_to(package_root).as_posix()
    except ValueError:
        return test_path.relative_to(repository_root).as_posix()


def _test_link(
    evidence: TestEvidence,
    *,
    requirements_path: Path,
    package_root: Path,
    repository_root: Path,
) -> str:
    display = _display_path(
        evidence.path,
        package_root=package_root,
        repository_root=repository_root,
    )
    relative_target = Path(
        os.path.relpath(evidence.path, requirements_path.parent)
    ).as_posix()
    title = f"{evidence.test_name} — {evidence.description}".replace(
        "\\", "\\\\"
    ).replace('"', '\\"')
    return (
        f"[{display}:{evidence.line}]" f'({relative_target}#L{evidence.line} "{title}")'
    )


def _group_evidence(
    items: Iterable[TestEvidence],
) -> dict[str, list[TestEvidence]]:
    grouped: dict[str, list[TestEvidence]] = {}
    for item in items:
        grouped.setdefault(item.requirement_id, []).append(item)
    for requirement_items in grouped.values():
        requirement_items.sort(
            key=lambda item: (item.path.as_posix(), item.line, item.test_name)
        )
    return grouped


def update_requirements(
    *,
    requirements_path: Path,
    test_paths: Sequence[Path],
) -> str:
    requirements_path = requirements_path.resolve()
    resolved_tests = [path.resolve() for path in test_paths]
    repository_root = _find_repository_root(requirements_path)
    package_root = _find_package_root(requirements_path, repository_root)
    grouped = _group_evidence(
        evidence
        for test_path in resolved_tests
        for evidence in _parse_test_evidence(test_path)
    )

    lines = requirements_path.read_text(encoding="utf-8").splitlines()
    requirement_ids = {
        match.group(0)
        for line in lines
        if line.startswith("| SLIST-")
        for match in [_REQUIREMENT_ID.search(line)]
        if match is not None
    }
    unknown = sorted(set(grouped).difference(requirement_ids))
    if unknown:
        raise ValueError(
            "Test annotations reference unknown requirements: " + ", ".join(unknown)
        )

    updated: list[str] = []
    seen: set[str] = set()
    for line in lines:
        if not line.startswith("| SLIST-"):
            updated.append(line)
            continue
        cells = line.split("|")
        requirement_id = cells[1].strip()
        evidence_cell = cells[-2].strip()
        if _EVIDENCE_MARKER not in evidence_cell:
            raise ValueError(f"{requirement_id} evidence is missing {_EVIDENCE_MARKER}")
        _manual, _marker, _generated = evidence_cell.partition(_EVIDENCE_MARKER)
        links = [
            _test_link(
                item,
                requirements_path=requirements_path,
                package_root=package_root,
                repository_root=repository_root,
            )
            for item in grouped.get(requirement_id, [])
        ]
        generated = "; ".join(links) if links else "No tagged test evidence."
        cells[-2] = f" {_EVIDENCE_MARKER} {generated} "
        updated.append("|".join(cells))
        seen.add(requirement_id)

    missing = sorted(requirement_ids.difference(seen))
    if missing:
        raise ValueError("Requirements were not updated: " + ", ".join(missing))
    return "\n".join(updated) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Regenerate line-numbered test evidence links from structured "
            "SLIST comments immediately above integration test functions."
        )
    )
    parser.add_argument(
        "--requirements",
        required=True,
        type=Path,
        help="Requirements Markdown file to update.",
    )
    parser.add_argument(
        "--test",
        action="append",
        required=True,
        type=Path,
        dest="tests",
        help="Integration test file to scan; repeat for every evidence source.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when the requirements file is not already current.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    generated = update_requirements(
        requirements_path=args.requirements,
        test_paths=args.tests,
    )
    current = args.requirements.read_text(encoding="utf-8")
    if args.check:
        if generated != current:
            raise SystemExit(
                "Session-list requirement test evidence is stale; "
                "run the updater without --check."
            )
        return 0
    args.requirements.write_text(generated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
