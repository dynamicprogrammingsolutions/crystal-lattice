"""Portable Crystal Lattice session snapshots."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from agent_core import Session

if TYPE_CHECKING:
    from .context import CrystalLatticeContext


CrystalSnapshotter = Callable[["CrystalLatticeContext"], object]


@dataclass(frozen=True)
class CrystalLatticeSnapshot:
    """JSON-serializable application session continuation state."""

    schema: int
    session: dict[str, object] | None
    workspace_root: str | None
    request_defaults: dict[str, object]

    def to_bytes(self) -> bytes:
        return (
            json.dumps(
                {
                    "schema": self.schema,
                    "session": self.session,
                    "workspace_root": self.workspace_root,
                    "request_defaults": self.request_defaults,
                },
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            + "\n"
        ).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> "CrystalLatticeSnapshot":
        value = json.loads(data.decode("utf-8"))
        if not isinstance(value, dict) or value.get("schema") != 1:
            raise ValueError("unsupported Crystal Lattice snapshot")
        raw_session = value.get("session")
        if raw_session is not None and not isinstance(raw_session, dict):
            raise TypeError("snapshot session must be an object or null")
        workspace_root = value.get("workspace_root")
        if workspace_root is not None and not isinstance(workspace_root, str):
            raise TypeError("snapshot workspace_root must be a string or null")
        request_defaults = value.get("request_defaults") or {}
        if not isinstance(request_defaults, dict):
            raise TypeError("snapshot request_defaults must be an object")
        return cls(
            schema=1,
            session=raw_session,
            workspace_root=workspace_root,
            request_defaults=request_defaults,
        )


def application_session_snapshot(
    context: "CrystalLatticeContext",
) -> CrystalLatticeSnapshot:
    """Capture the current immutable session and workspace root."""

    session = context.session_or_none
    return CrystalLatticeSnapshot(
        schema=1,
        session=session.to_dict() if isinstance(session, Session) else None,
        workspace_root=(
            str(context.workspace) if context.workspace is not None else None
        ),
        request_defaults=dict(context.config),
    )


def restore_session(
    snapshot: CrystalLatticeSnapshot,
    *,
    workspace_root: str | None,
) -> Session | None:
    if snapshot.session is None:
        return None
    rebased = _rebase_value(
        snapshot.session,
        old_root=snapshot.workspace_root,
        new_root=workspace_root,
    )
    if not isinstance(rebased, dict):
        raise TypeError("rebased snapshot session must be an object")
    if rebased != snapshot.session:
        metadata = rebased.get("metadata")
        if isinstance(metadata, dict):
            metadata.pop("native_messages", None)
            metadata.pop("native_messages_integrity", None)
    return Session.from_dict(rebased)


def _rebase_value(
    value: object,
    *,
    old_root: str | None,
    new_root: str | None,
) -> object:
    if isinstance(value, str) and old_root and new_root and old_root in value:
        return value.replace(old_root, new_root)
    if isinstance(value, list):
        return [
            _rebase_value(item, old_root=old_root, new_root=new_root) for item in value
        ]
    if isinstance(value, dict):
        return {
            key: _rebase_value(item, old_root=old_root, new_root=new_root)
            for key, item in value.items()
        }
    return value
