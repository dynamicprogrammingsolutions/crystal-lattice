"""Canonical JSON envelopes used by session and message query adapters."""

from __future__ import annotations

from typing import Any

from agent_core import Session


def normalize_message_range(
    message_count: int,
    start: int | None,
    end: int | None,
) -> tuple[int, int]:
    """Return concrete slice-style bounds or reject an empty selection."""

    if isinstance(message_count, bool) or not isinstance(message_count, int):
        raise ValueError("message_count must be an integer")
    if message_count < 0:
        raise ValueError("message_count must be non-negative")
    for name, value in (("start", start), ("end", end)):
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int)
        ):
            raise ValueError(f"{name} must be an integer or null")

    start_index, end_index, _step = slice(start, end).indices(message_count)
    if start_index >= end_index:
        raise ValueError("range selects no messages")
    return start_index, end_index


def serialize_session_messages(
    session: Session,
    *,
    start: int | None = None,
    end: int | None = None,
) -> dict[str, Any]:
    """Serialize one canonical indexed-message range."""

    if not session.messages:
        return {"messages": []}
    start_index, end_index = normalize_message_range(
        len(session.messages),
        start,
        end,
    )
    return {
        "messages": [
            {
                "index": index,
                "message": session.messages[index].to_dict(),
            }
            for index in range(start_index, end_index)
        ]
    }


__all__ = [
    "normalize_message_range",
    "serialize_session_messages",
]
