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
import subprocess
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


REQUIRED_FIELDS = (
    "task",
    "external_id",
    "internal_id",
    "priority",
    "status",
    "declared_dependencies",
    "inferred_dependencies",
)
SEMANTIC_FIELDS = frozenset(REQUIRED_FIELDS)
PRESENTATION_FIELDS = ("readiness", "blocking_dependencies")
PRIORITIES = {"must have", "should have", "good to have"}
STATUSES = {"pending", "in progress", "review", "done"}
DATED_NAME_RE = re.compile(r"^(?P<date>\d{8})-(?P<slug>.+)$")
NUMBERED_MARKDOWN_RE = re.compile(
    r"^(?P<number>\d{3})-(?P<name>.+)\.md$"
)
INTERNAL_ID_RE = re.compile(r"^[A-Z0-9]+(?:-[A-Z0-9]+)*$")
READINESS_LINK_COLORS = {
    "done": "#188038",
    "active": "#A64B00",
    "ready": "#1967D2",
    "queued": "#7B1FA2",
    "blocked": "#5F6368",
}


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
    priority: str
    status: str
    declared_dependencies: tuple[str, ...]
    inferred_dependencies: tuple[str, ...]
    fields: tuple[tuple[str, str], ...]
    task_kind: str
    link_target: str | None
    previous_internal_id: str

    @property
    def display_id(self) -> str:
        return self.internal_id

    def field_value(self, name: str) -> str:
        for field_name, value in self.fields:
            if field_name == name:
                return value
        return ""


@dataclass(frozen=True)
class NormalizedRoadmap:
    headers: tuple[str, ...]
    rows: list[Row]
    text: str
    changed: bool
    warnings: tuple[str, ...] = ()


def arbitrary_headers(headers: Iterable[str]) -> tuple[str, ...]:
    return tuple(header for header in headers if header not in SEMANTIC_FIELDS)


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


def classify_task(
    value: str,
    repo_root: Path,
    *,
    task_directory_entry: str = "000-main.md",
) -> TaskIdentity:
    task = value.strip()
    if not task:
        raise RoadmapError("task must not be empty")

    if task.lower().endswith(".md"):
        normalized, resolved = _safe_repository_path(task, repo_root)
        if not resolved.is_file():
            raise RoadmapError(f"task Markdown file does not exist: {normalized}")
        parent_match = DATED_NAME_RE.fullmatch(resolved.parent.name)
        file_match = NUMBERED_MARKDOWN_RE.fullmatch(resolved.name)
        if parent_match and file_match:
            return TaskIdentity(
                normalized=normalized,
                kind="markdown",
                link_target=normalized,
                date=parent_match.group("date"),
                slug=parent_match.group("slug"),
                number=file_match.group("number"),
            )
        standalone_match = DATED_NAME_RE.fullmatch(resolved.stem)
        if standalone_match:
            return TaskIdentity(
                normalized=normalized,
                kind="markdown",
                link_target=normalized,
                date=standalone_match.group("date"),
                slug=standalone_match.group("slug"),
            )
        return TaskIdentity(
            normalized=normalized,
            kind="markdown",
            link_target=normalized,
            slug=resolved.stem,
        )

    normalized_slashes = task.rstrip("/")
    normalized, resolved = _safe_repository_path(
        normalized_slashes, repo_root
    )
    if resolved.is_dir():
        entry_path = resolved / task_directory_entry
        if not entry_path.is_file():
            raise RoadmapError(
                f"task directory has no {task_directory_entry}: {normalized}"
            )
        directory_match = DATED_NAME_RE.fullmatch(resolved.name)
        return TaskIdentity(
            normalized=normalized,
            kind="directory",
            link_target=(Path(normalized) / task_directory_entry).as_posix(),
            date=(
                directory_match.group("date")
                if directory_match is not None
                else None
            ),
            slug=(
                directory_match.group("slug")
                if directory_match is not None
                else resolved.name
            ),
        )
    if "/" in normalized_slashes:
        raise RoadmapError(f"task directory does not exist: {normalized}")

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
) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    reader = csv.DictReader(source.splitlines())
    if reader.fieldnames is None:
        raise RoadmapError(f"{source_name}: CSV has no header")
    headers = tuple(reader.fieldnames)
    if any(not header.strip() for header in headers):
        raise RoadmapError(f"{source_name}: CSV headers must not be empty")
    duplicate_headers = _find_duplicates(headers)
    if duplicate_headers:
        raise RoadmapError(
            f"{source_name}: duplicate CSV headers: "
            + ", ".join(sorted(duplicate_headers))
        )
    header_keys = {header.casefold() for header in headers}
    missing = [
        field for field in REQUIRED_FIELDS if field.casefold() not in header_keys
    ]
    if missing:
        raise RoadmapError(
            f"{source_name}: CSV is missing required headers: "
            + ", ".join(missing)
        )
    reserved = [
        field for field in PRESENTATION_FIELDS if field.casefold() in header_keys
    ]
    if reserved:
        raise RoadmapError(
            f"{source_name}: CSV uses reserved presentation headers: "
            + ", ".join(reserved)
        )
    if any(field not in headers for field in REQUIRED_FIELDS):
        raise RoadmapError(
            f"{source_name}: required headers must use exact lowercase names"
        )

    records: list[dict[str, str]] = []
    for line_number, raw in enumerate(reader, start=2):
        extra_values = raw.get(None)
        if extra_values:
            raise RoadmapError(
                f"{source_name}:{line_number}: CSV row has unexpected extra columns"
            )
        values = {header: (raw.get(header) or "").strip() for header in headers}
        for required in ("task", "priority", "status"):
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
    return headers, records


def _generate_rows(
    headers: tuple[str, ...],
    records: list[dict[str, str]],
    *,
    repo_root: Path,
    task_directory_entry: str,
) -> tuple[list[Row], tuple[str, ...]]:
    identities = [
        classify_task(
            record["task"],
            repo_root,
            task_directory_entry=task_directory_entry,
        )
        for record in records
    ]
    duplicate_tasks = _find_duplicates(
        identity.normalized for identity in identities
    )
    if duplicate_tasks:
        raise RoadmapError(
            "duplicate task identity: " + ", ".join(sorted(duplicate_tasks))
        )

    external_ids = [
        _normalize_external_id(record["external_id"]) for record in records
    ]
    candidates = [
        _candidate_internal_id(identity, external_id)
        for identity, external_id in zip(
            identities, external_ids, strict=True
        )
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

    def resolve(token: str, owner_index: int) -> str | None:
        key = token.casefold()
        target_index = canonical_map.get(key)
        if target_index is None:
            previous_matches = previous_map.get(key, [])
            if previous_matches:
                target_index = previous_matches[0]
        if target_index is None:
            target_index = task_map.get(key)
        if target_index is None:
            try:
                normalized_external = _normalize_external_id(token)
            except RoadmapError:
                normalized_external = ""
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
            return None
        if target_index == owner_index:
            raise RoadmapError(
                f"{internal_ids[owner_index]} cannot depend on itself"
            )
        return internal_ids[target_index]

    warnings: list[str] = []

    def dependencies(
        raw_value: str,
        *,
        owner_index: int,
        field: str,
    ) -> tuple[str, ...]:
        resolved: list[str] = []
        for token in _split_dependencies(raw_value):
            dependency = resolve(token, owner_index)
            if dependency is None:
                warnings.append(
                    f"{internal_ids[owner_index]}: removed missing "
                    f"{field} dependency {token!r}"
                )
                continue
            resolved.append(dependency)
        return tuple(resolved)

    custom_headers = arbitrary_headers(headers)
    rows: list[Row] = []
    for index, (record, identity, external_id, internal_id) in enumerate(
        zip(records, identities, external_ids, internal_ids, strict=True)
    ):
        rows.append(
            Row(
                task=identity.normalized,
                external_id=external_id,
                internal_id=internal_id,
                priority=record["priority"],
                status=record["status"],
                declared_dependencies=dependencies(
                    record["declared_dependencies"],
                    owner_index=index,
                    field="declared",
                ),
                inferred_dependencies=dependencies(
                    record["inferred_dependencies"],
                    owner_index=index,
                    field="inferred",
                ),
                fields=tuple(
                    (header, record[header]) for header in custom_headers
                ),
                task_kind=identity.kind,
                link_target=identity.link_target,
                previous_internal_id=record["internal_id"].strip(),
            )
        )
    _validate_rows(rows)
    return rows, tuple(warnings)


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


def _row_values(row: Row) -> dict[str, str]:
    values = {
        "task": row.task,
        "external_id": row.external_id,
        "internal_id": row.internal_id,
        "priority": row.priority,
        "status": row.status,
        "declared_dependencies": ";".join(row.declared_dependencies),
        "inferred_dependencies": ";".join(row.inferred_dependencies),
    }
    values.update(row.fields)
    return values


def rows_to_csv_text(headers: tuple[str, ...], rows: list[Row]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=headers,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(_row_values(row))
    return buffer.getvalue()


def normalize_csv_text(
    source: str,
    *,
    source_name: str,
    repo_root: Path,
    task_directory_entry: str = "000-main.md",
) -> NormalizedRoadmap:
    headers, records = _parse_records(source, source_name=source_name)
    rows, warnings = _generate_rows(
        headers,
        records,
        repo_root=repo_root.resolve(),
        task_directory_entry=task_directory_entry,
    )
    text = rows_to_csv_text(headers, rows)
    return NormalizedRoadmap(
        headers=headers,
        rows=rows,
        text=text,
        changed=text != source,
        warnings=warnings,
    )


def normalize_csv(
    path: Path,
    *,
    repo_root: Path,
    task_directory_entry: str = "000-main.md",
) -> NormalizedRoadmap:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RoadmapError(f"cannot read {path}: {exc}") from exc
    return normalize_csv_text(
        source,
        source_name=str(path),
        repo_root=repo_root,
        task_directory_entry=task_directory_entry,
    )


def _read_rows(
    csv_path: Path,
    repo_root: Path,
    *,
    task_directory_entry: str = "000-main.md",
) -> list[Row]:
    return normalize_csv(
        csv_path,
        repo_root=repo_root,
        task_directory_entry=task_directory_entry,
    ).rows


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


def _id_reference(
    row: Row,
    readiness: str,
    output_path: Path,
    repo_root: Path,
) -> str:
    label = html.escape(row.internal_id)
    color = READINESS_LINK_COLORS.get(readiness)
    style = f' style="color:{color}"' if color else ""
    if row.link_target is None:
        return f"<span{style}>{label}</span>" if style else label
    relative = os.path.relpath(
        repo_root / row.link_target, output_path.parent
    )
    href = html.escape(Path(relative).as_posix(), quote=True)
    return f'<a{style} href="{href}">{label}</a>'


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
    csv_path: Path,
    rows: list[Row],
    repo_root: Path,
    headers: tuple[str, ...],
) -> str:
    output_path = csv_path.with_suffix(".md")
    title = _roadmap_title(csv_path.stem)
    by_id = {row.internal_id.casefold(): row for row in rows}
    readiness = derive_readiness(rows)
    custom_headers = arbitrary_headers(headers)
    display_headers = (
        "Order",
        "ID",
        *custom_headers,
        "Dependencies",
        "External ID",
        "Priority",
        "Status",
    )
    legend = " · ".join(
        f'<span style="color:{color}">{name}</span>'
        for name, color in READINESS_LINK_COLORS.items()
    )
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
        f"ID colors: {legend}.",
        "",
        "| " + " | ".join(_markdown_text(name) for name in display_headers) + " |",
        "|---:|" + "---|" * (len(display_headers) - 1),
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
        state = readiness[row.internal_id.casefold()][0]
        custom_values = tuple(
            _markdown_text(row.field_value(header))
            if row.field_value(header)
            else "—"
            for header in custom_headers
        )
        lines.append(
            "| "
            + " | ".join(
                (
                    str(order),
                    _id_reference(row, state, output_path, repo_root),
                    *custom_values,
                    ", ".join(dependencies) if dependencies else "—",
                    (
                        f"`{_markdown_text(row.external_id)}`"
                        if row.external_id
                        else "—"
                    ),
                    _markdown_text(row.priority),
                    _markdown_text(row.status),
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _print_warnings(warnings: tuple[str, ...]) -> None:
    for warning in warnings:
        print(f"roadmap warning: {warning}", file=sys.stderr)


def generate(
    csv_path: Path,
    *,
    repo_root: Path,
    task_directory_entry: str = "000-main.md",
    check: bool = False,
) -> Path:
    csv_path = csv_path.resolve()
    repo_root = repo_root.resolve()
    normalized = normalize_csv(
        csv_path,
        repo_root=repo_root,
        task_directory_entry=task_directory_entry,
    )
    _print_warnings(normalized.warnings)
    rendered = render_markdown(
        csv_path,
        normalized.rows,
        repo_root,
        normalized.headers,
    )
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
        help="named roadmap config; defaults beside this script",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if CSV normalization or generated Markdown is stale",
    )
    parser.add_argument("roadmap", help="named roadmap key or CSV path")
    return parser.parse_args()


def _direct_csv_path(value: str) -> Path | None:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    if path.suffix.lower() == ".csv" or path.exists():
        return path.resolve()
    return None


def _discover_repository_root(csv_path: Path) -> Path:
    override = os.environ.get("ROADMAP_REPOSITORY_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(csv_path.parent),
                "rev-parse",
                "--show-toplevel",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return Path.cwd().resolve()
    return Path(completed.stdout.strip()).resolve()


def main() -> int:
    args = _parse_args()
    try:
        direct_path = (
            _direct_csv_path(args.roadmap)
            if args.config is None
            else None
        )
        if direct_path is not None:
            csv_path = direct_path
            repo_root = _discover_repository_root(csv_path)
            task_directory_entry = os.environ.get(
                "ROADMAP_TASK_DIRECTORY_ENTRY",
                "000-main.md",
            )
            if Path(task_directory_entry).name != task_directory_entry:
                raise RoadmapError(
                    "ROADMAP_TASK_DIRECTORY_ENTRY must be a file name"
                )
        else:
            registry = load_registry(args.config)
            csv_path = resolve_csv_argument(args.roadmap, registry)
            repo_root = registry.repository_root
            task_directory_entry = registry.task_directory_entry
        output = generate(
            csv_path,
            repo_root=repo_root,
            task_directory_entry=task_directory_entry,
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