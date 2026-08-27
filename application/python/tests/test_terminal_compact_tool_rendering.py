"""Tests for live one-line tool results and /tool-output.

Covers:

- ToolRenderer.render_event one-line mode: streamed phases suppressed, end
  phase renders a tool header plus one compact result line
  (preferring ``metadata.display.single_line``).
- Full mode remains the full header/content/footer rendering.
- Mid-call toggling never mixes modes for a call.
- The /tool-output slash command reports/sets ``ui_state`` and the
  config-driven startup default.
- Expanding a stored tool message in full via /list <index>.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
APP_PY = os.path.join(ROOT, "application/python")
if APP_PY not in sys.path:
    sys.path.insert(0, APP_PY)
CORE_PY = os.path.join(ROOT, "core/python")
if CORE_PY not in sys.path:
    sys.path.insert(0, CORE_PY)


def _strip_ansi(text: str) -> str:
    import re

    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _make_terminal_app(tmp_path: Path):
    from agent_terminal_app import terminal as term_mod

    base_dir = Path(term_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"
    app = term_mod.TerminalApplication(
        config_path=str(config_path),
        session_root=str(session_root),
    )
    app.start_new_session(agent_id="default")
    return app


def _make_renderer(app, one_line_flag: dict):
    from agent_terminal_app.event_rendering import TerminalRenderContext

    return TerminalRenderContext(
        app=app,
        footer_elements_supplier=lambda: [],
        one_line_supplier=lambda: bool(one_line_flag.get("on")),
    )


def _tool_end_event(
    *,
    call_id: str | None = "c1",
    request_id: str = "r1",
    message_index: int | None = 5,
    content: str = "line1\nline2\nline3",
    single_line: str | None = "read_file README.md",
    tool_name: str = "read_file",
) -> dict:
    display: dict = {"type": "text", "content": content}
    if single_line is not None:
        display["single_line"] = single_line
    event: dict = {
        "type": "tool_partial",
        "tool_call_id": call_id,
        "request_id": request_id,
        "phase": "end",
        "payload": {
            "result": {
                "role": "tool",
                "content": content,
                "metadata": {
                    "tool_name": tool_name,
                    "tool_call_id": call_id,
                    "display": display,
                },
            }
        },
    }
    if message_index is not None:
        event["message_index"] = message_index
    return event


def _tool_stream_event(
    *,
    call_id: str | None = "c1",
    request_id: str = "r1",
    content: str = "chunk\n",
) -> dict:
    return {
        "type": "tool_partial",
        "tool_call_id": call_id,
        "request_id": request_id,
        "phase": "stream",
        "payload": {"part": {"type": "text", "content": content}},
    }


def test_compact_off_renders_full_end_event(tmp_path: Path) -> None:
    app = _make_terminal_app(tmp_path)
    renderer = _make_renderer(app, {"on": False})

    lines: list[str] = []
    renderer.render_event(_tool_end_event(), lines.append)

    joined = _strip_ansi("\n".join(lines))
    assert "Tool:" in joined
    # Full multi-line content and footer metadata are rendered.
    assert "line1" in joined
    assert "line3" in joined
    assert "tool_call_id: c1" in joined
    # No compact index prefix.
    assert "[5]" not in joined


def test_one_line_mode_renders_tool_header_and_result_line(tmp_path: Path) -> None:
    app = _make_terminal_app(tmp_path)
    renderer = _make_renderer(app, {"on": True})

    lines: list[str] = []
    renderer.render_event(_tool_stream_event(), lines.append)
    renderer.render_event(_tool_stream_event(content="more\n"), lines.append)
    renderer.render_event(_tool_end_event(), lines.append)

    # Streamed phases produce no output; end phase yields a separated block.
    assert [_strip_ansi(line) for line in lines] == [
        "",
        "[5] Tool: read_file",
        "    read_file README.md",
    ]
    # single_line from metadata.display is preferred over content.
    assert "line1" not in "\n".join(lines)
    # Footer metadata is not repeated on the compact line.
    assert "tool_call_id" not in "\n".join(lines)


def test_compact_on_without_index_omits_bracket(tmp_path: Path) -> None:
    app = _make_terminal_app(tmp_path)
    renderer = _make_renderer(app, {"on": True})

    lines: list[str] = []
    renderer.render_event(
        _tool_end_event(message_index=None, single_line=None, content="only line"),
        lines.append,
    )

    assert [_strip_ansi(line) for line in lines] == [
        "",
        "Tool: read_file",
        "    only line",
    ]
    # Falls back to the condensed content when no single_line exists.
    assert "only line" in _strip_ansi(lines[2])


def test_compact_line_condenses_long_content(tmp_path: Path) -> None:
    app = _make_terminal_app(tmp_path)
    renderer = _make_renderer(app, {"on": True})

    long_content = "\n".join(f"row {i}" for i in range(200))
    lines: list[str] = []
    renderer.render_event(
        _tool_end_event(single_line=None, content=long_content), lines.append
    )

    assert len(lines) == 3
    text = _strip_ansi(lines[2])
    assert "\n" not in text
    # Condensed to the short char limit (200 in the echo config) plus
    # the fixed prefix; the raw content is far longer.
    assert len(text) < 300
    assert text.endswith("...")


def test_toggle_mid_call_does_not_mix_modes(tmp_path: Path) -> None:
    app = _make_terminal_app(tmp_path)

    # Start full, flip to compact before end: the call stays full.
    flag = {"on": False}
    renderer = _make_renderer(app, flag)
    lines: list[str] = []
    renderer.render_event(_tool_stream_event(), lines.append)
    flag["on"] = True
    renderer.render_event(_tool_end_event(), lines.append)
    joined = _strip_ansi("\n".join(lines))
    assert "tool_call_id: c1" in joined  # full-mode footer
    assert "[5] Tool:" not in joined

    # Start compact, flip to full before end: the call stays compact.
    flag = {"on": True}
    renderer = _make_renderer(app, flag)
    lines = []
    renderer.render_event(_tool_stream_event(call_id="c2"), lines.append)
    flag["on"] = False
    renderer.render_event(_tool_end_event(call_id="c2"), lines.append)
    assert len(lines) == 3
    assert _strip_ansi(lines[0]) == ""
    assert _strip_ansi(lines[1]) == "[5] Tool: read_file"


def test_compact_mode_reset_between_calls(tmp_path: Path) -> None:
    app = _make_terminal_app(tmp_path)
    flag = {"on": True}
    renderer = _make_renderer(app, flag)

    lines: list[str] = []
    renderer.render_event(_tool_end_event(call_id="c1"), lines.append)
    # Turning compact off applies to the next call.
    flag["on"] = False
    renderer.render_event(_tool_end_event(call_id="c2"), lines.append)

    first_block = [_strip_ansi(line) for line in lines[:3]]
    rest = _strip_ansi("\n".join(lines[3:]))
    assert first_block == [
        "",
        "[5] Tool: read_file",
        "    read_file README.md",
    ]
    assert "tool_call_id: c2" in rest


@pytest.mark.asyncio
async def test_tool_output_command_reports_and_sets_mode(tmp_path: Path) -> None:
    from agent_terminal_app import terminal as term_mod

    app = _make_terminal_app(tmp_path)
    outputs: list[str] = []
    ui_state: dict = {"tool_output_one_line": False}

    await term_mod._cmd_tool_output(app, "", outputs.append, ui_state)
    assert ui_state["tool_output_one_line"] is False
    assert "[tool-output] full" in outputs[-1]

    await term_mod._cmd_tool_output(app, "one-line", outputs.append, ui_state)
    assert ui_state["tool_output_one_line"] is True
    assert "/list <index>" in outputs[-1]

    await term_mod._cmd_tool_output(app, "full", outputs.append, ui_state)
    assert ui_state["tool_output_one_line"] is False

    # Invalid arguments surface a user error via the shared handler.
    await term_mod._handle_slash_command(
        app, "/tool-output bogus", outputs.append, ui_state
    )
    assert any("usage: /tool-output [one-line|full]" in line for line in outputs)
    assert ui_state["tool_output_one_line"] is False
    assert term_mod.get_slash_command("compact") is None
    assert term_mod.get_slash_command("tool-output") is not None
    assert [
        completion.text for completion in term_mod._tool_output_completion(app, "")
    ] == ["one-line", "full"]


def test_initial_tool_output_state_from_config(tmp_path: Path) -> None:
    from agent_terminal_app import terminal as term_mod

    base_dir = Path(term_mod.__file__).resolve().parent
    base_cfg = json.loads(
        (base_dir / "config_echo_app.json").read_text(encoding="utf-8")
    )

    # Both configs live in the same directory so the runtime env overlay
    # (CONFIG_DIR) does not conflict between the two applications.
    default_path = tmp_path / "config_default.json"
    default_path.write_text(json.dumps(base_cfg), encoding="utf-8")
    app_default = term_mod.TerminalApplication(
        config_path=str(default_path),
        session_root=str(tmp_path / "sessions_default"),
    )
    # Default: no tool_output_live_one_line key in the echo config.
    assert term_mod._initial_tool_output_one_line_state(app_default) is False

    # Explicitly enabled via application config.
    cfg = dict(base_cfg)
    cfg["application"] = {
        **base_cfg.get("application", {}),
        "tool_output_live_one_line": True,
    }
    cfg_path = tmp_path / "config_compact_on.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    app_on = term_mod.TerminalApplication(
        config_path=str(cfg_path),
        session_root=str(tmp_path / "sessions_on"),
    )
    assert term_mod._initial_tool_output_one_line_state(app_on) is True


@pytest.mark.asyncio
async def test_list_index_expands_tool_message_in_full(tmp_path: Path) -> None:
    from agent_terminal_app import terminal as term_mod

    app = _make_terminal_app(tmp_path)
    session_id = app.session_id
    app.append_user_message("hello")
    app.add_message(
        session_id,
        role="tool",
        content="line1\nline2\nline3",
        metadata={
            "tool_call_id": "c9",
            "tool_name": "read_file",
            "display": {
                "type": "text",
                "content": "line1\nline2\nline3",
                "single_line": "read_file README.md",
            },
        },
    )

    outputs: list[str] = []
    ui_state: dict = {"tool_output_one_line": True}
    # The tool message is at index 1 (user message at 0), matching the
    # index a compact live line would display.
    await term_mod._cmd_list(app, "1", outputs.append, ui_state)

    joined = _strip_ansi("\n".join(outputs))
    # Full expansion: multi-line content plus footer, not the one-liner.
    assert "line1" in joined
    assert "line3" in joined
    assert "tool_call_id: c9" in joined
