"""Prune raw run directories while retaining the selected runs.

Every executed request writes one run directory under
``<artifact-root>/<profile>/runs/<UTC-timestamp>-<stage>-...`` holding its
records, raw diagnostics, and result pages. Nothing prunes them
automatically. This command classifies every run directory by the
consolidation semantics and reports — or, with ``--execute``, deletes —
the ones no freeze or collection can select again:

- a run directory is kept when one of its records is selected for the
  kept labels: for managed records (with a ``run-model.json`` provenance
  sibling) every genuine execution of a kept label — or, when a cell has
  only replays, its replays; for legacy records the latest per cell and
  label;
- run directories without readable records are kept and reported (they
  may be in flight or broken);
- ``--cache`` (with ``--execute``) clears the execution cache; every kept
  request then re-executes on its next invocation.

The default mode is a dry run: it only reports.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
for import_root in (REPOSITORY_ROOT, PACKAGE_ROOT / "src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from agent_eval.runner import record_paths  # noqa: E402

from .configuration import DEFAULT_ARTIFACT_ROOT  # noqa: E402
from .handoff_semantic import handoff_assessment_subject_identity  # noqa: E402
from .semantic import (  # noqa: E402
    assessment_subject_identity,
    continuation_cell_identity,
    handoff_cell_identity,
    producer_cell_identity,
)
from .stages import STAGES  # noqa: E402

# Record name to cell identity, matching the consolidation groups.
_RECORD_IDENTITIES = (
    (STAGES["task-creation"].record, producer_cell_identity),
    (STAGES["handoff-plan"].record, handoff_cell_identity),
    (STAGES["continuation"].record, continuation_cell_identity),
    (STAGES["negative-control"].record, handoff_cell_identity),
    (STAGES["task-creation-assessment"].record, assessment_subject_identity),
    (STAGES["handoff-assessment"].record, handoff_assessment_subject_identity),
)


@dataclass(frozen=True)
class _Record:
    path: Path
    run_dir: Path
    record_name: str
    cell: str
    label: str
    managed: bool
    cache_hit: bool
    modified: float


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _resolve_label(value: Mapping[str, Any], metadata: Mapping[str, Any]) -> str | None:
    for source in (
        value.get("run_label"),
        metadata.get("label"),
        value.get("run_attempt"),
    ):
        if isinstance(source, str) and source:
            return source
    return None


def _scan(artifact_root: Path) -> tuple[list[_Record], list[Path]]:
    """Scan stage records; return resolvable records and bare run dirs."""

    records: list[_Record] = []
    scanned: set[Path] = set()
    for record_name, identity_of in _RECORD_IDENTITIES:
        for path in record_paths(artifact_root, record_name):
            run_dir = path.parents[1]
            scanned.add(run_dir)
            value = _load_json(path)
            if not isinstance(value, dict):
                continue
            metadata = _load_json(path.parent / "run-model.json")
            metadata = metadata if isinstance(metadata, dict) else {}
            label = _resolve_label(value, metadata)
            if label is None:
                continue
            records.append(
                _Record(
                    path=path,
                    run_dir=run_dir,
                    record_name=record_name,
                    cell=identity_of(value),
                    label=label,
                    managed=bool(metadata),
                    cache_hit=metadata.get("cache_hit") is True,
                    modified=path.stat().st_mtime,
                )
            )
    run_dirs = sorted(
        run_dir
        for profile in _profile_dirs(artifact_root)
        for run_dir in (profile / "runs").glob("*")
        if run_dir.is_dir()
    )
    bare = [run_dir for run_dir in run_dirs if run_dir not in scanned]
    return records, bare


def _profile_dirs(artifact_root: Path) -> list[Path]:
    return sorted(
        path
        for path in artifact_root.iterdir()
        if path.is_dir() and (path / "runs").is_dir()
    )


def _selected(records: list[_Record], keep: set[str]) -> set[Path]:
    """Mirror the consolidation selection over the kept labels."""

    groups: dict[tuple[str, str, str], list[_Record]] = {}
    for record in records:
        if record.label in keep:
            groups.setdefault(
                (record.record_name, record.cell, record.label), []
            ).append(record)
    selected: set[Path] = set()
    for group in groups.values():
        managed = [record for record in group if record.managed]
        if managed:
            genuine = [record for record in managed if not record.cache_hit]
            pool = genuine or managed
        else:
            pool = [max(group, key=lambda record: record.modified)]
        selected.update(record.path for record in pool)
    return selected


def _tree_size(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _format_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


def _drop_reason(record: _Record, selected: set[Path]) -> str:
    if record.path in selected:
        return ""
    if record.managed and record.cache_hit:
        return "cache replay"
    return "superseded by a newer record of the same cell"


def plan(
    artifact_root: Path,
    *,
    keep_labels: Sequence[str],
) -> tuple[list[tuple[Path, str]], list[Path], list[Path]]:
    """Classify run directories into drops, keeps, and unclassified runs."""

    keep = {label for label in keep_labels if label}
    records, bare = _scan(artifact_root)
    selected = _selected(records, keep)
    by_dir: dict[Path, list[_Record]] = {}
    for record in records:
        by_dir.setdefault(record.run_dir, []).append(record)
    drops: list[tuple[Path, str]] = []
    for run_dir in sorted(set(by_dir) | set(bare)):
        group = by_dir.get(run_dir, [])
        if not group:
            continue  # unclassified: no readable records; keep and report
        if any(record.path in selected for record in group):
            continue
        if all(record.label not in keep for record in group):
            labels = ", ".join(sorted({record.label for record in group}))
            drops.append((run_dir, f"label(s) not kept: {labels}"))
        else:
            reasons = [
                reason
                for record in group
                if record.label in keep and (reason := _drop_reason(record, selected))
            ]
            drops.append((run_dir, reasons[0] if reasons else "not selected"))
    keeps = sorted(set(by_dir) - {path for path, _ in drops})
    return drops, keeps, bare


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument(
        "--keep-labels",
        required=True,
        help="comma-separated run labels to retain",
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        help="also clear the execution cache (with --execute)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="delete the reported run directories (default: report only)",
    )
    args = parser.parse_args(argv)
    artifact_root = args.artifact_root.expanduser().resolve()
    keep_labels = [item.strip() for item in args.keep_labels.split(",") if item.strip()]
    drops, keeps, bare = plan(artifact_root, keep_labels=keep_labels)

    for run_dir, reason in drops:
        profile = run_dir.parent.parent.name
        print(
            f"drop {profile}/{run_dir.name} ({_format_size(_tree_size(run_dir))}) — {reason}"
        )
    for run_dir in bare:
        profile = run_dir.parent.parent.name
        print(f"keep (unclassified) {profile}/{run_dir.name} — no readable records")
    print(
        f"{len(drops)} run directory(ies) would be removed,"
        f" {len(keeps)} kept ({_format_size(sum(_tree_size(path) for path, _ in drops))}"
        " reclaimable)"
    )
    cache_root = artifact_root / "cache"
    if cache_root.is_dir():
        print(
            f"execution cache: {_format_size(_tree_size(cache_root))}"
            " — pass --cache --execute to clear it"
        )
    if not args.execute:
        print("dry run: nothing deleted")
        return 0
    for run_dir, _ in drops:
        shutil.rmtree(run_dir)
    if args.cache and cache_root.is_dir():
        shutil.rmtree(cache_root)
        print("execution cache cleared")
    print(f"removed {len(drops)} run directory(ies)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
