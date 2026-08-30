from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from agent_terminal_app.event_rendering import TerminalRenderContext
from agent_terminal_app.terminal_app import TerminalApplication


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


@pytest.fixture
def terminal_app(tmp_path: Path) -> TerminalApplication:
    import agent_terminal_app.terminal as terminal

    config_path = Path(terminal.__file__).resolve().parent / "config_echo_app.json"
    app = TerminalApplication(
        config_path=str(config_path),
        session_root=str(tmp_path / "sessions"),
    )
    app.start_new_session(agent_id="default")
    return app


def _renderer(app: TerminalApplication) -> TerminalRenderContext:
    return TerminalRenderContext(
        app=app,
        footer_elements_supplier=lambda: [],
        one_line_supplier=lambda: False,
    )


@pytest.mark.parametrize(
    ("index", "message", "expected_header"),
    [
        (3, {"role": "user", "content": "hello", "metadata": {}}, "[3] User:"),
        (
            4,
            {"role": "system", "content": "instructions", "metadata": {}},
            "[4] System:",
        ),
        (
            5,
            {"role": "assistant", "content": "response", "metadata": {}},
            "[5] Assistant:",
        ),
        (6, {"role": "tool", "content": "result", "metadata": {}}, "[6] Tool:"),
    ],
)
def test_list_message_headers_have_separator_and_index(
    terminal_app: TerminalApplication,
    index: int,
    message: dict[str, Any],
    expected_header: str,
) -> None:
    lines: list[str] = []

    _renderer(terminal_app).render_message(index, message, lines.append)

    assert [_strip_ansi(line) for line in lines[:2]] == ["", expected_header]


@pytest.mark.parametrize("role", ["user", "system"])
def test_live_appended_message_header_uses_event_index(
    terminal_app: TerminalApplication,
    role: str,
) -> None:
    lines: list[str] = []

    _renderer(terminal_app).render_event(
        {
            "type": "message_appended",
            "index": 17,
            "role": role,
            "message": {"role": role, "content": "content", "metadata": {}},
        },
        lines.append,
    )

    assert [_strip_ansi(line) for line in lines[:2]] == [
        "",
        f"[17] {role.capitalize()}:",
    ]


def test_live_assistant_header_uses_reserved_message_index(
    terminal_app: TerminalApplication,
) -> None:
    lines: list[str] = []

    _renderer(terminal_app).render_event(
        {
            "type": "assistant_message",
            "phase": "start",
            "message_index": 174,
        },
        lines.append,
    )

    assert [_strip_ansi(line) for line in lines] == ["", "[174] Assistant:"]


def test_live_assistant_header_without_index_remains_backward_compatible(
    terminal_app: TerminalApplication,
) -> None:
    lines: list[str] = []

    _renderer(terminal_app).render_event(
        {"type": "assistant_message", "phase": "start"},
        lines.append,
    )

    assert [_strip_ansi(line) for line in lines] == ["", "Assistant:"]


def test_live_tool_header_has_one_separator_per_call(
    terminal_app: TerminalApplication,
) -> None:
    lines: list[str] = []
    renderer = _renderer(terminal_app)

    renderer.render_event(
        {
            "type": "tool_partial",
            "request_id": "request-1",
            "tool_call_id": "call-1",
            "phase": "stream",
            "payload": {"part": {"type": "text", "content": "first"}},
        },
        lines.append,
    )
    renderer.render_event(
        {
            "type": "tool_partial",
            "request_id": "request-1",
            "tool_call_id": "call-1",
            "phase": "stream",
            "payload": {"part": {"type": "text", "content": "second"}},
        },
        lines.append,
    )

    assert [_strip_ansi(line) for line in lines] == ["", "Tool:"]
