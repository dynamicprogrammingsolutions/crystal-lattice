"""Line-oriented renderers for projected session and message query documents."""

from __future__ import annotations

import csv
from io import StringIO
import json
from typing import Any, Iterable, Mapping, TypeVar


MAX_QUERY_TEXT_VALUE_CHARS = 16_384
MAX_QUERY_TEXT_ROWS = 100_000
_Row = TypeVar("_Row", bound=tuple[str, ...])


def _one_line(value: Any) -> str:
    if isinstance(value, str):
        rendered = " ".join(value.split())
    elif value is None:
        rendered = "null"
    elif isinstance(value, bool):
        rendered = "true" if value else "false"
    elif isinstance(value, (int, float)):
        rendered = str(value)
    else:
        rendered = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        rendered = rendered.replace("\r", "\\r").replace("\n", "\\n")
    if len(rendered) <= MAX_QUERY_TEXT_VALUE_CHARS:
        return rendered
    return rendered[: MAX_QUERY_TEXT_VALUE_CHARS - 15] + "... [truncated]"


def _leaf_values(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, Mapping):
        if not value:
            yield prefix, {}
            return
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield from _leaf_values(child, path)
        return
    if isinstance(value, list):
        yield prefix, value
        return
    yield prefix, value


def _bounded_rows(rows: Iterable[_Row]) -> list[_Row]:
    result: list[_Row] = []
    for row in rows:
        if len(result) >= MAX_QUERY_TEXT_ROWS:
            raise ValueError(
                f"query text output exceeds {MAX_QUERY_TEXT_ROWS} rows; "
                "narrow the range or projection"
            )
        result.append(row)
    return result


def _sessions_rows(document: Any) -> list[tuple[str, str, str]]:
    if not isinstance(document, Mapping):
        return [("", "$", _one_line(document))]
    sessions = document.get("sessions")
    if not isinstance(sessions, list):
        return [
            ("", path or "$", _one_line(value))
            for path, value in _leaf_values(document)
        ]

    rows: list[tuple[str, str, str]] = []
    for item in sessions:
        if not isinstance(item, Mapping):
            rows.append(("", "$", _one_line(item)))
            continue
        session_id = item.get("session_id")
        identity = session_id if isinstance(session_id, str) else ""
        leaves = [
            (path, value) for path, value in _leaf_values(item) if path != "session_id"
        ]
        if not leaves and identity:
            rows.append((identity, "", ""))
            continue
        for path, value in leaves:
            rows.append((identity, path, _one_line(value)))
    return _bounded_rows(rows)


def _messages_rows(
    document: Any,
    *,
    session_id: str,
) -> list[tuple[str, str, str, str, str]]:
    if not isinstance(document, Mapping):
        return [(session_id, "", "", "$", _one_line(document))]
    messages = document.get("messages")
    if not isinstance(messages, list):
        return [
            (session_id, "", "", path or "$", _one_line(value))
            for path, value in _leaf_values(document)
        ]

    rows: list[tuple[str, str, str, str, str]] = []
    for item in messages:
        if not isinstance(item, Mapping):
            rows.append((session_id, "", "", "$", _one_line(item)))
            continue
        raw_index = item.get("index")
        index = str(raw_index) if isinstance(raw_index, int) else ""
        message = item.get("message")
        if not isinstance(message, Mapping):
            rows.append((session_id, index, "", "message", _one_line(message)))
            continue
        raw_role = message.get("role")
        role = raw_role if isinstance(raw_role, str) else ""
        leaves = [
            (path, value) for path, value in _leaf_values(message) if path != "role"
        ]
        if not leaves:
            rows.append((session_id, index, role, "", ""))
            continue
        for path, value in leaves:
            rows.append((session_id, index, role, path, _one_line(value)))
    return _bounded_rows(rows)


def _delimited(
    header: tuple[str, ...],
    rows: list[tuple[str, ...]],
    *,
    delimiter: str,
) -> str:
    output = StringIO()
    writer = csv.writer(
        output,
        delimiter=delimiter,
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writerow(header)
    writer.writerows(rows)
    return output.getvalue()


def render_sessions_document(document: Any, output_format: str) -> str:
    """Render a session collection as JSON or line-oriented text."""

    if output_format == "json":
        return json.dumps(document, ensure_ascii=False) + "\n"
    rows = _sessions_rows(document)
    if output_format == "text":
        lines = [
            (
                session_id
                if not path
                else f"{session_id + ' ' if session_id else ''}{path}: {value}"
            )
            for session_id, path, value in rows
        ]
        return "".join(f"{line}\n" for line in lines)
    if output_format == "tsv":
        return _delimited(("session_id", "path", "value"), rows, delimiter="\t")
    if output_format == "csv":
        return _delimited(("session_id", "path", "value"), rows, delimiter=",")
    raise ValueError(f"unsupported query output format: {output_format!r}")


def render_messages_document(
    document: Any,
    output_format: str,
    *,
    session_id: str,
) -> str:
    """Render one message-range document with stable identity context."""

    if output_format == "json":
        return json.dumps(document, ensure_ascii=False) + "\n"
    rows = _messages_rows(document, session_id=session_id)
    if output_format == "text":
        lines: list[str] = []
        for row_session_id, index, role, path, value in rows:
            context = row_session_id
            if index:
                context += f" [{index}]"
            if role:
                context += f" {role}"
            if path:
                context += f" {path}: {value}"
            lines.append(context)
        return "".join(f"{line}\n" for line in lines)
    if output_format == "tsv":
        return _delimited(
            ("session_id", "index", "role", "path", "value"),
            rows,
            delimiter="\t",
        )
    if output_format == "csv":
        return _delimited(
            ("session_id", "index", "role", "path", "value"),
            rows,
            delimiter=",",
        )
    raise ValueError(f"unsupported query output format: {output_format!r}")


__all__ = [
    "MAX_QUERY_TEXT_ROWS",
    "MAX_QUERY_TEXT_VALUE_CHARS",
    "render_messages_document",
    "render_sessions_document",
]
