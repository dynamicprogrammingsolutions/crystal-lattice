from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Collection, Dict, Iterable

from agent_core import Message, Session


_MESSAGE_ROLES = frozenset({"system", "user", "assistant", "tool"})


@dataclass(frozen=True)
class CompactMessage:
    index: int
    role: str
    content: str
    content_length: int
    content_truncated: bool
    content_omitted: bool
    tool_name: str | None = None
    tool_call_id: str | None = None
    tool_status: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "role": self.role,
            "content": self.content,
            "content_length": self.content_length,
            "content_truncated": self.content_truncated,
            "content_omitted": self.content_omitted,
            "tool_name": self.tool_name,
            "tool_call_id": self.tool_call_id,
            "tool_status": self.tool_status,
        }


@dataclass(frozen=True)
class CompactHistory:
    session_id: str
    messages: tuple[CompactMessage, ...]
    selected_message_count: int
    omitted_message_count: int
    content_characters: int
    max_messages: int
    max_content_chars: int
    max_total_content_chars: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "messages": [message.to_dict() for message in self.messages],
            "selected_message_count": self.selected_message_count,
            "omitted_message_count": self.omitted_message_count,
            "content_characters": self.content_characters,
            "max_messages": self.max_messages,
            "max_content_chars": self.max_content_chars,
            "max_total_content_chars": self.max_total_content_chars,
        }


@dataclass(frozen=True)
class _ProjectedContent:
    content: str
    content_length: int
    summarized: bool
    source_content_present: bool


def _require_nonnegative_int(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _require_positive_int(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _normalize_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())


def _metadata(message: Message) -> Dict[str, Any]:
    return message.metadata if isinstance(message.metadata, dict) else {}


def _tool_display_content(message: Message) -> _ProjectedContent:
    canonical = message.content if isinstance(message.content, str) else ""
    canonical_normalized = _normalize_text(canonical)
    metadata = _metadata(message)
    display = metadata.get("display")

    if isinstance(display, dict):
        candidates: Iterable[Any] = (
            display.get("single_line"),
            (
                display.get("content")
                if display.get("type") == "text"
                else display.get("content_text")
            ),
            display.get("text_fallback"),
        )
        for candidate in candidates:
            normalized = _normalize_text(candidate)
            if normalized:
                return _ProjectedContent(
                    content=normalized,
                    content_length=len(canonical),
                    summarized=normalized != canonical_normalized,
                    source_content_present=message.content not in (None, ""),
                )

    return _ProjectedContent(
        content=canonical_normalized,
        content_length=len(canonical),
        summarized=False,
        source_content_present=message.content not in (None, ""),
    )


def _message_content(message: Message) -> _ProjectedContent:
    if message.role == "tool":
        return _tool_display_content(message)
    canonical = message.content if isinstance(message.content, str) else ""
    return _ProjectedContent(
        content=_normalize_text(canonical),
        content_length=len(canonical),
        summarized=False,
        source_content_present=message.content not in (None, ""),
    )


def _string_metadata_value(metadata: Dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    if isinstance(value, str) and value:
        return value
    return None


def _tool_status(message: Message, metadata: Dict[str, Any]) -> str | None:
    status = _string_metadata_value(metadata, "status")
    if status is not None:
        return status
    success = metadata.get("success")
    if isinstance(success, bool):
        return "succeeded" if success else "failed"
    result = message.tool_result
    if isinstance(result, dict):
        result_status = result.get("status")
        if isinstance(result_status, str) and result_status:
            return result_status
        result_success = result.get("success")
        if isinstance(result_success, bool):
            return "succeeded" if result_success else "failed"
    return None


def _project_message(
    index: int,
    message: Message,
    *,
    content_limit: int,
) -> CompactMessage:
    projected = _message_content(message)
    allowed = min(content_limit, len(projected.content))
    content = projected.content[:allowed]
    has_source_content = projected.source_content_present
    omitted = has_source_content and allowed == 0
    truncated = (
        projected.summarized
        or allowed < len(projected.content)
        or (has_source_content and not projected.content)
    )
    metadata = _metadata(message)

    return CompactMessage(
        index=index,
        role=message.role,
        content=content,
        content_length=projected.content_length,
        content_truncated=truncated,
        content_omitted=omitted,
        tool_name=_string_metadata_value(metadata, "tool_name"),
        tool_call_id=_string_metadata_value(metadata, "tool_call_id"),
        tool_status=_tool_status(message, metadata),
    )


def project_session_history(
    session: Session,
    *,
    start: int | None = None,
    end: int | None = None,
    roles: Collection[str] | None = None,
    max_messages: int = 100,
    max_content_chars: int = 500,
    max_total_content_chars: int = 20_000,
) -> CompactHistory:
    """Return a deterministic bounded projection of canonical session history."""

    max_messages = _require_positive_int("max_messages", max_messages)
    max_content_chars = _require_nonnegative_int(
        "max_content_chars",
        max_content_chars,
    )
    max_total_content_chars = _require_nonnegative_int(
        "max_total_content_chars",
        max_total_content_chars,
    )

    normalized_roles: frozenset[str] | None = None
    if roles is not None:
        role_values = list(roles)
        invalid_roles = [
            role
            for role in role_values
            if not isinstance(role, str) or role not in _MESSAGE_ROLES
        ]
        if invalid_roles:
            raise ValueError("roles must contain only system, user, assistant, or tool")
        normalized_roles = frozenset(role_values)

    message_count = len(session.messages)
    start_index, end_index, _step = slice(start, end).indices(message_count)
    selected = [
        (index, session.messages[index])
        for index in range(start_index, end_index)
        if normalized_roles is None or session.messages[index].role in normalized_roles
    ]
    selected_count = len(selected)
    retained = selected[-max_messages:]
    omitted_count = selected_count - len(retained)

    remaining_content = max_total_content_chars
    projected_reverse: list[CompactMessage] = []
    for index, message in reversed(retained):
        content_limit = min(max_content_chars, remaining_content)
        projected = _project_message(
            index,
            message,
            content_limit=content_limit,
        )
        projected_reverse.append(projected)
        remaining_content -= len(projected.content)

    projected_messages = tuple(reversed(projected_reverse))
    content_characters = sum(len(message.content) for message in projected_messages)
    return CompactHistory(
        session_id=session.session_id,
        messages=projected_messages,
        selected_message_count=selected_count,
        omitted_message_count=omitted_count,
        content_characters=content_characters,
        max_messages=max_messages,
        max_content_chars=max_content_chars,
        max_total_content_chars=max_total_content_chars,
    )


def get_canonical_message(session: Session, index: int) -> Dict[str, Any]:
    """Serialize one explicitly selected canonical message."""

    if isinstance(index, bool) or not isinstance(index, int):
        raise ValueError("index must be an integer")
    message_count = len(session.messages)
    normalized = index if index >= 0 else message_count + index
    if normalized < 0 or normalized >= message_count:
        raise IndexError("message index out of range")
    return {
        "index": normalized,
        "message": session.messages[normalized].to_dict(),
    }


__all__ = [
    "CompactHistory",
    "CompactMessage",
    "get_canonical_message",
    "project_session_history",
]
