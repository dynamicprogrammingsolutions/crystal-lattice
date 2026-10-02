"""Consolidation core: label-based selection and per-cell sample statistics."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence


RECORD_PATTERNS = (
    "*/runs/*/records/{name}",
    "runs/*/records/{name}",
    "*/records/{name}",
    "records/{name}",
)
PROVENANCE_RECORD_NAME = "run-model.json"


def record_paths(artifact_root: Path, record_name: str) -> tuple[Path, ...]:
    """Return record files without traversing transient run workspaces."""

    values: set[Path] = set()
    for pattern in RECORD_PATTERNS:
        values.update(artifact_root.glob(pattern.format(name=record_name)))
    return tuple(sorted(values))


@dataclass(frozen=True)
class CellRecord:
    """One record of a cell, resolved to its run label and provenance."""

    cell: str
    label: str
    run_id: str | None
    cache_hit: bool
    sample_index: int
    managed: bool
    value: Mapping[str, Any]
    path: Path
    modified: float


def select_cell_records(
    artifact_root: Path,
    *,
    record_name: str,
    cell_identity: Callable[[Mapping[str, Any]], str],
    labels: Sequence[str] | None = None,
) -> dict[str, tuple[CellRecord, ...]]:
    """Select the records of every cell by run label.

    With ``labels`` the selection takes all records of the listed labels:
    every record of a cell becomes one sample of that cell. Without
    ``labels`` the selection takes the latest label of each cell — the most
    recent batch, all of its samples. Records without any resolvable label
    are skipped.

    Managed records (written by :class:`~agent_eval.runner.RunModel`) keep
    every genuine execution as a sample and drop cache-replay duplicates.
    Legacy records (no provenance sibling) keep the latest record per cell
    and label, matching the historical single-record behavior.
    """

    grouped: dict[str, dict[str, list[CellRecord]]] = {}
    for path in record_paths(artifact_root, record_name):
        value = _load_json(path)
        if not isinstance(value, dict):
            continue
        metadata = _provenance(path.parent)
        label = _resolve_label(value, metadata)
        if label is None:
            continue
        record = CellRecord(
            cell=cell_identity(value),
            label=label,
            run_id=_run_id(metadata, path),
            cache_hit=metadata.get("cache_hit") is True,
            sample_index=_sample_index(metadata),
            managed=bool(metadata),
            value=value,
            path=path,
            modified=path.stat().st_mtime,
        )
        grouped.setdefault(record.cell, {}).setdefault(label, []).append(record)

    selected: dict[str, tuple[CellRecord, ...]] = {}
    for cell, by_label in grouped.items():
        if labels is None:
            wanted = [
                max(
                    by_label,
                    key=lambda name: max(record.modified for record in by_label[name]),
                )
            ]
        else:
            wanted = [name for name in labels if name in by_label]
        samples: list[CellRecord] = []
        for name in wanted:
            samples.extend(_label_samples(by_label[name]))
        if samples:
            selected[cell] = tuple(samples)
    return selected


def render_selection(cells: Mapping[str, tuple[CellRecord, ...]]) -> str:
    """Render the per-cell selection for confirmation before freezing."""

    lines = []
    for cell in sorted(cells):
        counts: dict[str, int] = {}
        for record in cells[cell]:
            counts[record.label] = counts.get(record.label, 0) + 1
        summary = ", ".join(
            f"{label} x{count}" for label, count in sorted(counts.items())
        )
        lines.append(f"- {cell}: {summary}")
    return "\n".join(lines) + ("\n" if lines else "")


def aggregate_metric(values: Sequence[float]) -> dict[str, Any]:
    """Aggregate one metric across the samples of a cell."""

    if not values:
        raise ValueError("aggregation requires at least one sample")
    return {
        "count": len(values),
        "mean": sum(values) / len(values),
        "min": min(values),
        "max": max(values),
        "spread": max(values) - min(values),
    }


def cell_statistics(
    cells: Mapping[str, tuple[CellRecord, ...]],
    *,
    metric: Callable[[Mapping[str, Any]], float],
) -> dict[str, dict[str, Any]]:
    """Aggregate a caller-chosen metric per cell with per-sample provenance."""

    statistics: dict[str, dict[str, Any]] = {}
    for cell, records in cells.items():
        samples = [
            {
                "label": record.label,
                "run_id": record.run_id,
                "value": metric(record.value),
            }
            for record in records
        ]
        statistics[cell] = {
            **aggregate_metric([sample["value"] for sample in samples]),
            "samples": samples,
        }
    return statistics


def completeness(
    expected: Iterable[str],
    observed: Iterable[str],
) -> dict[str, Any]:
    """Compare observed cells against the expected cell set."""

    expected_set = set(expected)
    observed_set = set(observed)
    return {
        "expected": len(expected_set),
        "present": len(observed_set),
        "missing": sorted(expected_set - observed_set),
    }


def _label_samples(records: list[CellRecord]) -> list[CellRecord]:
    managed = [record for record in records if record.managed]
    if managed:
        genuine = [record for record in managed if not record.cache_hit]
        pool = genuine or managed
        return sorted(pool, key=lambda record: (record.sample_index, record.modified))
    return [max(records, key=lambda record: record.modified)]


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _provenance(records_dir: Path) -> Mapping[str, Any]:
    metadata = _load_json(records_dir / PROVENANCE_RECORD_NAME)
    return metadata if isinstance(metadata, dict) else {}


def _resolve_label(
    value: Mapping[str, Any],
    metadata: Mapping[str, Any],
) -> str | None:
    for source in (
        value.get("run_label"),
        metadata.get("label"),
        value.get("run_attempt"),
    ):
        if isinstance(source, str) and source:
            return source
    return None


def _run_id(metadata: Mapping[str, Any], path: Path) -> str | None:
    run_id = metadata.get("run_id")
    if isinstance(run_id, str) and run_id:
        return run_id
    parts = path.parts
    if "runs" in parts:
        index = parts.index("runs")
        if index + 1 < len(parts):
            return parts[index + 1]
    return None


def _sample_index(metadata: Mapping[str, Any]) -> int:
    raw = metadata.get("sample_index")
    if isinstance(raw, int) and raw >= 0:
        return raw
    return 0
