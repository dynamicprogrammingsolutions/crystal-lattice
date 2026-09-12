"""Sanitize persisted OpenAI Responses usage attribution from session JSON."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from uuid import uuid4

from agent_core import AgentCore
from agent_core.types import Session

from .openai_responses_usage_extension import sanitize_usage_for_persistence


_RAW_USAGE_METADATA_KEY = "_openai_responses_usage_raw"
_COUNT_KEYS = ("core", "phase", "native", "private")


def _is_target_usage(value: Any) -> bool:
    if not isinstance(value, dict) or "attribution" not in value:
        return False
    return any(
        key in value for key in ("input_tokens", "output_tokens", "total_tokens")
    )


def _sanitize_metadata_usage(
    metadata: Dict[str, Any],
    *,
    location: str,
    counts: Dict[str, int],
) -> Tuple[Dict[str, Any], bool]:
    updated = metadata
    changed = False

    usage = metadata.get("usage")
    if isinstance(usage, dict) and _is_target_usage(usage):
        updated = {
            **updated,
            "usage": sanitize_usage_for_persistence(usage),
        }
        counts[location] += 1
        changed = True

    raw_usage = metadata.get(_RAW_USAGE_METADATA_KEY)
    if isinstance(raw_usage, dict) and _is_target_usage(raw_usage):
        if not changed:
            updated = dict(updated)
        updated[_RAW_USAGE_METADATA_KEY] = sanitize_usage_for_persistence(raw_usage)
        counts["private"] += 1
        changed = True

    return updated, changed


def _sanitize_core_message(
    message: Dict[str, Any],
    counts: Dict[str, int],
) -> Tuple[Dict[str, Any], bool]:
    metadata = message.get("metadata")
    if not isinstance(metadata, dict):
        return message, False

    updated_metadata, changed = _sanitize_metadata_usage(
        metadata,
        location="core",
        counts=counts,
    )

    phase_messages = metadata.get("phase_messages")
    if isinstance(phase_messages, list):
        updated_phases: List[Any] = []
        phases_changed = False
        for phase_message in phase_messages:
            if not isinstance(phase_message, dict):
                updated_phases.append(phase_message)
                continue
            phase_metadata = phase_message.get("metadata")
            if not isinstance(phase_metadata, dict):
                updated_phases.append(phase_message)
                continue
            sanitized_phase_metadata, phase_changed = _sanitize_metadata_usage(
                phase_metadata,
                location="phase",
                counts=counts,
            )
            updated_phases.append(
                {**phase_message, "metadata": sanitized_phase_metadata}
                if phase_changed
                else phase_message
            )
            phases_changed = phases_changed or phase_changed
        if phases_changed:
            updated_metadata = {
                **updated_metadata,
                "phase_messages": updated_phases,
            }
            changed = True

    if not changed:
        return message, False
    return {**message, "metadata": updated_metadata}, True


def _sanitize_native_item(
    item: Dict[str, Any],
    counts: Dict[str, int],
) -> Tuple[Dict[str, Any], bool]:
    metadata = item.get("_metadata")
    if not isinstance(metadata, dict):
        return item, False
    updated_metadata, changed = _sanitize_metadata_usage(
        metadata,
        location="native",
        counts=counts,
    )
    if not changed:
        return item, False
    return {**item, "_metadata": updated_metadata}, True


def sanitize_session_payload(
    payload: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """Return a session payload without persisted OpenAI usage attribution."""

    counts = {key: 0 for key in _COUNT_KEYS}
    updated_payload = payload
    changed = False

    messages = payload.get("messages")
    if isinstance(messages, list):
        updated_messages: List[Any] = []
        messages_changed = False
        for message in messages:
            if not isinstance(message, dict):
                updated_messages.append(message)
                continue
            updated_message, message_changed = _sanitize_core_message(message, counts)
            updated_messages.append(updated_message)
            messages_changed = messages_changed or message_changed
        if messages_changed:
            updated_payload = {**updated_payload, "messages": updated_messages}
            changed = True

    session_metadata = payload.get("metadata")
    if isinstance(session_metadata, dict):
        native_messages = session_metadata.get("native_messages")
        if isinstance(native_messages, list):
            updated_native: List[Any] = []
            native_changed = False
            for item in native_messages:
                if not isinstance(item, dict):
                    updated_native.append(item)
                    continue
                updated_item, item_changed = _sanitize_native_item(item, counts)
                updated_native.append(updated_item)
                native_changed = native_changed or item_changed
            if native_changed:
                updated_metadata = {
                    **session_metadata,
                    "native_messages": updated_native,
                }
                updated_payload = {**updated_payload, "metadata": updated_metadata}
                changed = True

    return (updated_payload if changed else payload), counts


def _validate_session_payload(payload: Dict[str, Any]) -> Session:
    session = Session.from_dict(payload)
    AgentCore()._verify_native_integrity(session)
    return session


def _canonical_payload_paths(
    session_root: Path,
    session_ids: Optional[Sequence[str]],
) -> Iterable[Tuple[Path, str]]:
    if session_ids:
        for session_id in session_ids:
            if not session_id or Path(session_id).name != session_id:
                raise ValueError(f"invalid session id: {session_id!r}")
            yield session_root / f"{session_id}.json", "session"
            snapshot_root = session_root / ".snapshots"
            for path in sorted(snapshot_root.glob(f"{session_id}.*.json")):
                if not path.name.endswith(".selected.json"):
                    yield path, "snapshot"
        return

    for path in sorted(session_root.glob("*.json")):
        if ".tool-loop-conflict." in path.name:
            continue
        yield path, "session"

    snapshot_root = session_root / ".snapshots"
    for path in sorted(snapshot_root.glob("*.json")):
        if path.name.endswith(".selected.json"):
            continue
        yield path, "snapshot"


def _serialize_payload(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, indent=2).encode("utf-8")


def _write_bytes_durable(path: Path, data: bytes) -> None:
    with path.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _write_gzip_backup(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as compressed:
            compressed.write(data)
        raw.flush()
        os.fsync(raw.fileno())


def _sanitize_file(
    path: Path,
    *,
    record_kind: str,
    apply: bool,
    backup_dir: Optional[Path],
) -> Dict[str, Any]:
    if not path.is_file():
        return {
            "path": str(path),
            "record_kind": record_kind,
            "status": "missing",
        }

    original = path.read_bytes()
    source_sha256 = hashlib.sha256(original).hexdigest()
    try:
        payload = json.loads(original)
    except Exception as exc:
        return {
            "path": str(path),
            "record_kind": record_kind,
            "status": "invalid_json",
            "error": str(exc),
        }
    if not isinstance(payload, dict):
        return {
            "path": str(path),
            "record_kind": record_kind,
            "status": "not_session_object",
        }

    session_id = payload.get("session_id")
    if record_kind == "session":
        is_canonical = session_id == path.stem
    else:
        snapshot_id = payload.get("snapshot_id")
        is_canonical = (
            isinstance(session_id, str)
            and bool(session_id)
            and snapshot_id == path.stem
            and path.name.startswith(f"{session_id}.")
        )
    if not is_canonical:
        return {
            "path": str(path),
            "record_kind": record_kind,
            "status": "noncanonical_session_file",
        }

    try:
        _validate_session_payload(payload)
    except Exception as exc:
        return {
            "path": str(path),
            "record_kind": record_kind,
            "status": "invalid_session",
            "error": str(exc),
        }

    sanitized, counts = sanitize_session_payload(payload)
    occurrence_count = sum(counts.values())
    if occurrence_count == 0:
        return {
            "path": str(path),
            "record_kind": record_kind,
            "session_id": str(session_id),
            "status": "unchanged",
            "occurrences": counts,
            "original_bytes": len(original),
            "projected_bytes": len(original),
            "bytes_saved": 0,
        }

    replacement = _serialize_payload(sanitized)
    try:
        validated = json.loads(replacement)
        if not isinstance(validated, dict):
            raise ValueError("serialized session is not an object")
        _validate_session_payload(validated)
    except Exception as exc:
        return {
            "path": str(path),
            "record_kind": record_kind,
            "session_id": str(session_id),
            "status": "replacement_validation_failed",
            "error": str(exc),
            "occurrences": counts,
        }

    report: Dict[str, Any] = {
        "path": str(path),
        "record_kind": record_kind,
        "session_id": str(session_id),
        "status": "would_change" if not apply else "pending",
        "occurrences": counts,
        "original_bytes": len(original),
        "projected_bytes": len(replacement),
        "bytes_saved": len(original) - len(replacement),
    }
    if not apply:
        return report
    if backup_dir is None:
        raise ValueError("backup_dir is required in apply mode")

    temp_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    backup_path = backup_dir / f"{record_kind}s" / f"{path.name}.gz"
    try:
        _write_bytes_durable(temp_path, replacement)
        current = path.read_bytes()
        if hashlib.sha256(current).hexdigest() != source_sha256:
            report["status"] = "source_changed"
            return report
        if backup_path.exists():
            report["status"] = "backup_exists"
            return report
        _write_gzip_backup(backup_path, original)
        current = path.read_bytes()
        if hashlib.sha256(current).hexdigest() != source_sha256:
            report["status"] = "source_changed"
            return report
        os.replace(temp_path, path)
        published = json.loads(path.read_bytes())
        if not isinstance(published, dict):
            raise ValueError("published session is not an object")
        _validate_session_payload(published)
        report["status"] = "changed"
        report["backup_path"] = str(backup_path)
        return report
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


def run_sanitizer(
    *,
    session_root: Path,
    session_ids: Optional[Sequence[str]] = None,
    apply: bool = False,
    backup_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    root = session_root.expanduser().resolve()
    if apply:
        if backup_dir is None:
            raise ValueError("backup_dir is required in apply mode")
        resolved_backup_dir = backup_dir.expanduser().resolve()
        if resolved_backup_dir == root or root in resolved_backup_dir.parents:
            raise ValueError("backup_dir must be outside the live session root")
    else:
        resolved_backup_dir = None

    files = [
        _sanitize_file(
            path,
            record_kind=record_kind,
            apply=apply,
            backup_dir=resolved_backup_dir,
        )
        for path, record_kind in _canonical_payload_paths(root, session_ids)
    ]
    statuses_in_totals = {"changed", "would_change", "unchanged"}
    totals = {
        "files_scanned": len(files),
        "files_changed": sum(item.get("status") == "changed" for item in files),
        "files_would_change": sum(
            item.get("status") == "would_change" for item in files
        ),
        "files_scanned_by_kind": {
            record_kind: sum(item.get("record_kind") == record_kind for item in files)
            for record_kind in ("session", "snapshot")
        },
        "files_changed_by_kind": {
            record_kind: sum(
                item.get("record_kind") == record_kind
                and item.get("status") == "changed"
                for item in files
            )
            for record_kind in ("session", "snapshot")
        },
        "files_would_change_by_kind": {
            record_kind: sum(
                item.get("record_kind") == record_kind
                and item.get("status") == "would_change"
                for item in files
            )
            for record_kind in ("session", "snapshot")
        },
        "occurrences": {
            key: sum(int((item.get("occurrences") or {}).get(key, 0)) for item in files)
            for key in _COUNT_KEYS
        },
        "original_bytes": sum(
            int(item.get("original_bytes", 0))
            for item in files
            if item.get("status") in statuses_in_totals
        ),
        "projected_bytes": sum(
            int(item.get("projected_bytes", 0))
            for item in files
            if item.get("status") in statuses_in_totals
        ),
        "bytes_saved": sum(
            int(item.get("bytes_saved", 0))
            for item in files
            if item.get("status") in {"changed", "would_change"}
        ),
    }
    return {
        "mode": "apply" if apply else "dry_run",
        "session_root": str(root),
        "backup_dir": str(resolved_backup_dir) if resolved_backup_dir else None,
        "totals": totals,
        "files": files,
    }


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove persisted OpenAI Responses usage attribution from sessions."
    )
    parser.add_argument(
        "--session-root",
        type=Path,
        default=Path("~/.crystal/sessions"),
    )
    parser.add_argument("--session-id", action="append", dest="session_ids")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-dir", type=Path)
    parser.add_argument("--report-path", type=Path)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        report = run_sanitizer(
            session_root=args.session_root,
            session_ids=args.session_ids,
            apply=args.apply,
            backup_dir=args.backup_dir,
        )
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 2
    serialized_report = json.dumps(report, indent=2)
    if args.report_path is not None:
        report_path = args.report_path.expanduser()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(serialized_report, encoding="utf-8")
    print(serialized_report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
