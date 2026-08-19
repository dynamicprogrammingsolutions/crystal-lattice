#!/usr/bin/env python3
"""Normalize a roadmap CSV and generate its dependency-ordered Markdown."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from roadmap_config import (
    RoadmapConfigError,
    load_registry,
    resolve_csv_argument,
)


FIELDS = (
    "task",
    "external_id",
    "internal_id",
    "title",
    "purpose",
    "priority",
    "status",
    "declared_dependencies",
    "inferred_dependencies",
    "notes",
)
PRIORITIES = {"must have", "should have", "good to have"}
STATUSES = {"pending", "in progress", "review", "done"}
DATED_TASK_DIR_RE = re.compile(
    r"^tasks/(?P<date>\d{8})-(?P<slug>[^/]+)/"
    r"(?P<number>\d{3})-(?P<name>[^/]+)\.md$"
)
DATED_TASK_DIRECTORY_RE = re.compile(
    r"^tasks/(?P<date>\d{8})-(?P<slug>[^/]+)$"
)
DATED_STANDALONE_RE = re.compile(
    r"^tasks/(?P<date>\d{8})-(?P<slug>[^/]+)\.md$"
)
INTERNAL_ID_RE = re.compile(r"^[A-Z0-9]+(?:-[A-Z0-9]+)*$")


class RoadmapError(ValueError):
    """Raised when a roadmap source is invalid."""


@dataclass(frozen=True)
class TaskIdentity:
    normalized: str
    kind: str
    link_target: str | None
    date: str | None = None
    slug: str | None = None
    number: str | None = None


@dataclass(frozen=True)
class Row:
    task: str
    external_id: str
    internal_id: str
    title: str
    purpose: str
    priority: str
    status: str
    declared_dependencies: tuple[str, ...]
    inferred_dependencies: tuple[str, ...]
    notes: str
    task_kind: str
    link_target: str | None
    previous_internal_id: str

    @property
    def display_id(self) -> str:
        return self.internal_id


@dataclass(frozen=True)
class NormalizedRoadmap:
    rows: list[Row]
    text: str
    changed: bool


def _split_dependencies(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(";") if part.strip())


def _words(value: str) -> list[str]:
    return [word for word in re.split(r"[^A-Za-z0-9]+", value) if word]


def _dated_base(date: str, slug: str) -> str:
    words = _words(slug)
    if not words:
        raise RoadmapError(f"cannot derive an internal ID from slug {slug!r}")
    initials = "".join(word[0].upper() for word in words[:2])
    return f"{date[4:8]}-{initials}"


def _free_name_base(value: str) -> str:
    words = _words(value)
    if not words:
        raise RoadmapError(f"cannot derive an internal ID from task {value!r}")
    return "-".join(word[:3].upper() for word in words[:2])


def _normalize_external_id(value: str) -> str:
    if not value.strip():
        return ""
    normalized = "-".join(_words(value.upper()))
    if not normalized or not INTERNAL_ID_RE.fullmatch(normalized):
        raise RoadmapError(f"invalid external ID {value!r}")
    return normalized


def _safe_repository_path(value: str, repo_root: Path) -> tuple[str, Path]:
    raw_path = Path(value)
    if raw_path.is_absolute():
        raise RoadmapError(f"task path must be repository-relative: {value}")
    resolved = (repo_root / raw_path).resolve()
    try:
        relative = resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise RoadmapError(
            f"task path escapes the repository: {value}"
        ) from exc
    return relative.as_posix(), resolved


def classify_task(value: str, repo_root: Path) -> TaskIdentity:
    task = value.strip()
    if not task:
        raise RoadmapError("task must not be empty")

    if task.lower().endswith(".md"):
        normalized, resolved = _safe_repository_path(task, repo_root)
        if not resolved.is_file():
            raise RoadmapError(f"task Markdown file does not exist: {normalized}")
        dated_subtask = DATED_TASK_DIR_RE.fullmatch(normalized)
        if dated_subtask:
            return TaskIdentity(
                normalized=normalized,
                kind="markdown",
                link_target=normalized,
                date=dated_subtask.group("date"),
                slug=dated_subtask.group("slug"),
                number=dated_subtask.group("number"),
            )
        dated_standalone = DATED_STANDALONE_RE.fullmatch(normalized)
        if dated_standalone:
            return TaskIdentity(
                normalized=normalized,
                kind="markdown",
                link_target=normalized,
                date=dated_standalone.group("date"),
                slug=dated_standalone.group("slug"),
            )
        return TaskIdentity(
            normalized=normalized,
            kind="markdown",
            link_target=normalized,
            slug=resolved.stem,
        )

    normalized_slashes = task.rstrip("/")
    if normalized_slashes == "tasks" or normalized_slashes.startswith("tasks/"):
        normalized, resolved = _safe_repository_path(
            normalized_slashes, repo_root
        )
        if not resolved.is_dir():
            raise RoadmapError(f"task directory does not exist: {normalized}")
        main_task = resolved / "000-main.md"
        if not main_task.is_file():
            raise RoadmapError(
                f"task directory has no 000-main.md: {normalized}"
            )
        dated_directory = DATED_TASK_DIRECTORY_RE.fullmatch(normalized)
        return TaskIdentity(
            normalized=normalized,
            kind="directory",
            link_target=(Path(normalized) / "000-main.md").as_posix(),
            date=(
                dated_directory.group("date")
                if dated_directory is not None
                else None
            ),
            slug=(
                dated_directory.group("slug")
                if dated_directory is not None
                else resolved.name
            ),
        )

    return TaskIdentity(
        normalized=task,
        kind="free",
        link_target=None,
        slug=task,
    )


def _candidate_internal_id(
    identity: TaskIdentity,
    external_id: str,
) -> str:
    if external_id:
        base = external_id
    elif identity.date and identity.slug:
        base = _dated_base(identity.date, identity.slug)
    else:
        base = _free_name_base(identity.slug or identity.normalized)
    if identity.number and identity.number != "000":
        return f"{base}-{identity.number}"
    return base


def _collision_suffix(task: str) -> str:
    return hashlib.sha256(task.encode("utf-8")).hexdigest()[:4].upper()


def _find_duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        key = value.casefold()
        if key in seen:
            duplicates.add(value)
        seen.add(key)
    return duplicates


def _parse_records(
    source: str,
    *,
    source_name: str,
) -> list[dict[str, str]]:
    reader = csv.DictReader(source.splitlines())
    if reader.fieldnames is None:
        raise RoadmapError(f"{source_name}: CSV has no header")
    if tuple(reader.fieldnames) != FIELDS:
        raise RoadmapError(
            f"{source_name}: CSV header must be exactly:\n" + ",".join(FIELDS)
        )
    records: list[dict[str, str]] = []
    for line_number, raw in enumerate(reader, start=2):
        extra_values = raw.get(None)
        if extra_values:
            raise RoadmapError(
                f"{source_name}:{line_number}: CSV row has unexpected extra columns"
            )
        values = {field: (raw.get(field) or "").strip() for field in FIELDS}
        for required in ("task", "title", "purpose", "priority", "status"):
            if not values[required]:
                raise RoadmapError(
                    f"{source_name}:{line_number}: {required} must not be empty"
                )
        if values["priority"] not in PRIORITIES:
            raise RoadmapError(
                f"{source_name}:{line_number}: invalid priority "
                f"{values['priority']!r}"
            )
        if values["status"] not in STATUSES:
            raise RoadmapError(
                f"{source_name}:{line_number}: invalid status "
                f"{values['status']!r}"
            )
        records.append(values)
    if not records:
        raise RoadmapError(f"{source_name}: CSV contains no task rows")
    return records


def _generate_rows(
    records: list[dict[str, str]],
    *,
    repo_root: Path,
) -> list[Row]:
    identities = [classify_task(record["task"], repo_root) for record in records]
    duplicate_tasks = _find_duplicates(identity.normalized for identity in identities)
    if duplicate_tasks:
        raise RoadmapError(
            "duplicate task identity: " + ", ".join(sorted(duplicate_tasks))
        )

    external_ids = [
        _normalize_external_id(record["external_id"]) for record in records
    ]
    candidates = [
        _candidate_internal_id(identity, external_id)
        for identity, external_id in zip(identities, external_ids, strict=True)
    ]
    candidate_counts: dict[str, int] = {}
    for candidate in candidates:
        key = candidate.casefold()
        candidate_counts[key] = candidate_counts.get(key, 0) + 1

    internal_ids: list[str] = []
    for identity, candidate in zip(identities, candidates, strict=True):
        internal_id = candidate
        if candidate_counts[candidate.casefold()] > 1:
            internal_id = f"{candidate}-{_collision_suffix(identity.normalized)}"
        if not INTERNAL_ID_RE.fullmatch(internal_id):
            raise RoadmapError(f"generated invalid internal ID {internal_id!r}")
        internal_ids.append(internal_id)
    duplicate_internal_ids = _find_duplicates(internal_ids)
    if duplicate_internal_ids:
        raise RoadmapError(
            "internal ID collision remains after disambiguation: "
            + ", ".join(sorted(duplicate_internal_ids))
        )

    canonical_map = {
        internal_id.casefold(): index
        for index, internal_id in enumerate(internal_ids)
    }
    previous_map: dict[str, list[int]] = {}
    task_map = {
        identity.normalized.casefold(): index
        for index, identity in enumerate(identities)
    }
    external_map: dict[str, list[int]] = {}
    for index, (record, external_id) in enumerate(
        zip(records, external_ids, strict=True)
    ):
        previous = record["internal_id"].strip()
        if previous:
            previous_map.setdefault(previous.casefold(), []).append(index)
        if external_id:
            external_map.setdefault(external_id.casefold(), []).append(index)
    ambiguous_previous = {
        alias: matches
        for alias, matches in previous_map.items()
        if len(matches) > 1
    }
    if ambiguous_previous:
        alias, matches = next(iter(ambiguous_previous.items()))
        canonical = ", ".join(internal_ids[index] for index in matches)
        raise RoadmapError(
            f"ambiguous previous internal ID {alias!r}: {canonical}"
        )

    def resolve(token: str, owner_index: int) -> str:
        key = token.casefold()
        target_index = canonical_map.get(key)
        if target_index is None:
            previous_matches = previous_map.get(key, [])
            if previous_matches:
                target_index = previous_matches[0]
        if target_index is None:
            target_index = task_map.get(key)
        if target_index is None:
            normalized_external = _normalize_external_id(token)
            external_matches = external_map.get(
                normalized_external.casefold(), []
            )
            if len(external_matches) > 1:
                matches = ", ".join(
                    internal_ids[index] for index in external_matches
                )
                raise RoadmapError(
                    f"ambiguous external ID {token!r}: {matches}"
                )
            if external_matches:
                target_index = external_matches[0]
        if target_index is None:
            raise RoadmapError(f"unknown dependency alias {token!r}")
        if target_index == owner_index:
            raise RoadmapError(
                f"{internal_ids[owner_index]} cannot depend on itself"
            )
        return internal_ids[target_index]

    rows: list[Row] = []
    for index, (record, identity, external_id, internal_id) in enumerate(
        zip(records, identities, external_ids, internal_ids, strict=True)
    ):
        declared = tuple(
            resolve(token, index)
            for token in _split_dependencies(
                record["declared_dependencies"]
            )
        )
        inferred = tuple(
            resolve(token, index)
            for token in _split_dependencies(
                record["inferred_dependencies"]
            )
        )
        rows.append(
            Row(
                task=identity.normalized,
                external_id=external_id,
                internal_id=internal_id,
                title=record["title"],
                purpose=record["purpose"],
                priority=record["priority"],
                status=record["status"],
                declared_dependencies=declared,
                inferred_dependencies=inferred,
                notes=record["notes"],
                task_kind=identity.kind,
                link_target=identity.link_target,
                previous_internal_id=record["internal_id"].strip(),
            )
        )
    _validate_rows(rows)
    return rows


def _validate_rows(rows: list[Row]) -> None:
    seen_non_done = False
    positions = {
        row.internal_id.casefold(): index for index, row in enumerate(rows)
    }
    for index, row in enumerate(rows):
        if row.status == "done":
            if seen_non_done:
                raise RoadmapError("all done rows must be at the top")
        else:
            seen_non_done = True
        overlap = {
            value.casefold() for value in row.declared_dependencies
        } & {value.casefold() for value in row.inferred_dependencies}
        if overlap:
            raise RoadmapError(
                f"{row.internal_id}: dependencies cannot be both declared "
                "and inferred: " + ", ".join(sorted(overlap))
            )
        combined = (*row.declared_dependencies, *row.inferred_dependencies)
        duplicates = _find_duplicates(combined)
        if duplicates:
            raise RoadmapError(
                f"{row.internal_id}: duplicate dependencies: "
                + ", ".join(sorted(duplicates))
            )
        for dependency in combined:
            dependency_index = positions.get(dependency.casefold())
            if dependency_index is None:
                raise RoadmapError(
                    f"{row.internal_id}: unresolved dependency {dependency!r}"
                )
            if dependency_index >= index:
                raise RoadmapError(
                    f"{row.internal_id}: dependency {dependency!r} "
                    "must appear above it"
                )


def rows_to_csv_text(rows: list[Row]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=FIELDS,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "task": row.task,
                "external_id": row.external_id,
                "internal_id": row.internal_id,
                "title": row.title,
                "purpose": row.purpose,
                "priority": row.priority,
                "status": row.status,
                "declared_dependencies": ";".join(
                    row.declared_dependencies
                ),
                "inferred_dependencies": ";".join(
                    row.inferred_dependencies
                ),
                "notes": row.notes,
            }
        )
    return buffer.getvalue()


def normalize_csv_text(
    source: str,
    *,
    source_name: str,
    repo_root: Path,
) -> NormalizedRoadmap:
    records = _parse_records(source, source_name=source_name)
    rows = _generate_rows(records, repo_root=repo_root.resolve())
    text = rows_to_csv_text(rows)
    return NormalizedRoadmap(rows=rows, text=text, changed=text != source)


def normalize_csv(path: Path, *, repo_root: Path) -> NormalizedRoadmap:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RoadmapError(f"cannot read {path}: {exc}") from exc
    return normalize_csv_text(
        source,
        source_name=str(path),
        repo_root=repo_root,
    )


def _read_rows(csv_path: Path, repo_root: Path) -> list[Row]:
    return normalize_csv(csv_path, repo_root=repo_root).rows


def _atomic_write(path: Path, content: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _markdown_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def _roadmap_title(stem: str) -> str:
    words = stem.split("-")
    rendered: list[str] = []
    for index, word in enumerate(words):
        if word.lower() == "ios":
            rendered.append("iOS")
        elif index > 0 and word.lower() in {"and", "or"}:
            rendered.append(word.lower())
        else:
            rendered.append(word.capitalize())
    return " ".join(rendered)


def _id_reference(row: Row, output_path: Path, repo_root: Path) -> str:
    label = row.internal_id
    if row.link_target is None:
        return label
    relative = os.path.relpath(
        repo_root / row.link_target, output_path.parent
    )
    return f"[{label}]({Path(relative).as_posix()})"


def _dependency_reference(
    dependency: Row,
    output_path: Path,
    repo_root: Path,
    *,
    inferred: bool,
) -> str:
    blocking = dependency.status != "done"
    if dependency.link_target is not None:
        relative = os.path.relpath(
            repo_root / dependency.link_target, output_path.parent
        )
        href = Path(relative).as_posix()
        if blocking:
            rendered = (
                '<a style="color:red" href="'
                + html.escape(href, quote=True)
                + '">'
                + html.escape(dependency.internal_id)
                + "</a>"
            )
        else:
            rendered = f"[{dependency.internal_id}]({href})"
    else:
        rendered = (
            f'<span style="color:red">{html.escape(dependency.internal_id)}</span>'
            if blocking
            else dependency.internal_id
        )
    return rendered + (" *(inferred)*" if inferred else "")


def derive_readiness(rows: list[Row]) -> dict[str, tuple[str, tuple[str, ...]]]:
    by_id = {row.internal_id.casefold(): row for row in rows}
    derived: dict[str, tuple[str, tuple[str, ...]]] = {}
    for row in rows:
        blockers = tuple(
            dependency
            for dependency in (
                *row.declared_dependencies,
                *row.inferred_dependencies,
            )
            if by_id[dependency.casefold()].status != "done"
        )
        if row.status == "done":
            readiness = "done"
        elif row.status in {"in progress", "review"}:
            readiness = "active"
        elif row.status == "pending" and not blockers:
            readiness = "ready"
        elif row.status == "pending" and all(
            derived.get(dependency.casefold(), ("blocked", ()))[0]
            in {"ready", "active"}
            for dependency in blockers
        ):
            readiness = "queued"
        elif row.status == "pending":
            readiness = "blocked"
        else:
            readiness = ""
        derived[row.internal_id.casefold()] = (readiness, blockers)
    return derived


def render_markdown(
    csv_path: Path, rows: list[Row], repo_root: Path
) -> str:
    output_path = csv_path.with_suffix(".md")
    title = _roadmap_title(csv_path.stem)
    by_id = {row.internal_id.casefold(): row for row in rows}
    lines = [
        f"# {title}",
        "",
        f"> Generated from [{csv_path.name}]({csv_path.name}). "
        "Do not edit this Markdown directly. "
        "See [Updating roadmaps](docs/updating-roadmaps.md).",
        "",
        "Tasks without a dependency relationship may proceed in parallel. "
        "List position is the current priority recommendation.",
        "",
        "| Order | ID | Task | Purpose | Dependencies | External ID | Priority | Status | Notes |",
        "|---:|---|---|---|---|---|---|---|---|",
    ]
    for order, row in enumerate(rows, start=1):
        dependencies = [
            _dependency_reference(
                by_id[key.casefold()],
                output_path,
                repo_root,
                inferred=False,
            )
            for key in row.declared_dependencies
        ]
        dependencies.extend(
            _dependency_reference(
                by_id[key.casefold()],
                output_path,
                repo_root,
                inferred=True,
            )
            for key in row.inferred_dependencies
        )
        lines.append(
            "| "
            + " | ".join(
                (
                    str(order),
                    _id_reference(row, output_path, repo_root),
                    _markdown_text(row.title),
                    _markdown_text(row.purpose),
                    ", ".join(dependencies) if dependencies else "—",
                    (
                        f"`{_markdown_text(row.external_id)}`"
                        if row.external_id
                        else "—"
                    ),
                    _markdown_text(row.priority),
                    _markdown_text(row.status),
                    _markdown_text(row.notes) if row.notes else "—",
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def generate(
    csv_path: Path,
    *,
    repo_root: Path,
    check: bool = False,
) -> Path:
    csv_path = csv_path.resolve()
    repo_root = repo_root.resolve()
    normalized = normalize_csv(csv_path, repo_root=repo_root)
    rendered = render_markdown(csv_path, normalized.rows, repo_root)
    output_path = csv_path.with_suffix(".md")

    if check:
        if normalized.changed:
            raise RoadmapError(f"roadmap CSV requires normalization: {csv_path}")
        try:
            current = output_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise RoadmapError(
                f"generated roadmap is missing: {output_path}"
            ) from exc
        if current != rendered:
            raise RoadmapError(
                f"generated roadmap is stale: {output_path}"
            )
    else:
        if normalized.changed:
            _atomic_write(csv_path, normalized.text)
        _atomic_write(output_path, rendered)
    return output_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        help="named roadmap config; defaults to roadmaps/config.json",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if CSV normalization or generated Markdown is stale",
    )
    parser.add_argument("roadmap", help="named roadmap key or CSV path")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    try:
        registry = load_registry(args.config)
        csv_path = resolve_csv_argument(args.roadmap, registry)
        output = generate(
            csv_path,
            repo_root=repo_root,
            check=args.check,
        )
    except (RoadmapError, RoadmapConfigError) as exc:
        print(f"roadmap error: {exc}", file=sys.stderr)
        return 1
    action = "checked" if args.check else "generated"
    print(f"{action}: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())