from __future__ import annotations

import json
from pathlib import Path

from agent_terminal_app.terminal_progress import (
    IDLE_PROGRESS,
    TerminalProgressState,
    format_terminal_progress,
    reduce_terminal_progress,
)
from agent_terminal_app import terminal as term_mod


def test_progress_tracks_request_llm_tool_and_completion() -> None:
    state = reduce_terminal_progress(
        IDLE_PROGRESS,
        {"type": "request_started", "request_id": "request-1"},
    )
    assert state == TerminalProgressState(
        phase="request",
        request_id="request-1",
    )

    state = reduce_terminal_progress(
        state,
        {
            "type": "assistant_message",
            "phase": "start",
            "request_id": "request-1",
        },
    )
    assert format_terminal_progress(state) == "Running: LLM"

    state = reduce_terminal_progress(
        state,
        {
            "type": "tool_calls",
            "request_id": "request-1",
            "tool_calls": [
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {"name": "read_file", "arguments": "{}"},
                },
                {
                    "id": "call-2",
                    "type": "function",
                    "function": {"name": "write_file", "arguments": "{}"},
                },
            ],
        },
    )
    assert format_terminal_progress(state) == "Running: tool read_file"

    state = reduce_terminal_progress(
        state,
        {
            "type": "tool_partial",
            "phase": "end",
            "request_id": "request-1",
            "tool_call_id": "call-1",
        },
    )
    assert format_terminal_progress(state) == "Running: tool write_file"

    state = reduce_terminal_progress(
        state,
        {
            "type": "tool_partial",
            "phase": "end",
            "request_id": "request-1",
            "tool_call_id": "call-2",
        },
    )
    assert format_terminal_progress(state) == "Running: request"

    state = reduce_terminal_progress(
        state,
        {"type": "request_completed", "request_id": "request-1"},
    )
    assert state == IDLE_PROGRESS
    assert format_terminal_progress(state) == ""


def test_progress_clears_on_cancel_error_and_session_reset() -> None:
    running = TerminalProgressState(
        phase="tool",
        request_id="request-1",
        tool_call_id="call-1",
        tool_name="shell",
        pending_tools=(("call-1", "shell"),),
    )

    for event in [
        {"type": "request_cancelled", "request_id": "request-1"},
        {"type": "error", "request_id": "request-1", "detail": "failed"},
        {"type": "session_created", "session_id": "session-2"},
    ]:
        assert reduce_terminal_progress(running, event) == IDLE_PROGRESS


def test_progress_ignores_terminal_event_for_another_request() -> None:
    running = TerminalProgressState(
        phase="llm",
        request_id="request-1",
    )

    assert (
        reduce_terminal_progress(
            running,
            {"type": "error", "request_id": "request-2", "detail": "failed"},
        )
        == running
    )


def test_progress_uses_request_fallback_for_tool_without_descriptor() -> None:
    state = TerminalProgressState(phase="request", request_id="request-1")
    state = reduce_terminal_progress(
        state,
        {
            "type": "tool_partial",
            "phase": "start",
            "request_id": "request-1",
            "tool_call_id": "unknown",
        },
    )

    assert format_terminal_progress(state) == "Running: tool tool"


def test_status_bar_includes_progress(tmp_path: Path) -> None:
    base_dir = Path(term_mod.__file__).resolve().parent
    app = term_mod.TerminalApplication(
        config_path=str(base_dir / "config_echo_app.json"),
        session_root=str(tmp_path / "sessions"),
    )
    app.start_new_session(agent_id="default")

    text = term_mod._status_bar_text(
        app,
        TerminalProgressState(
            phase="tool",
            request_id="request-1",
            tool_name="read_file",
        ),
    )

    assert "Running: tool read_file" in text


def test_startup_help_modes(tmp_path: Path) -> None:
    base_dir = Path(term_mod.__file__).resolve().parent
    base_config = json.loads(
        (base_dir / "config_echo_app.json").read_text(encoding="utf-8")
    )

    for mode, expected_lines in [
        ("summary", 4),
        ("hint", 1),
        ("off", 1),
    ]:
        config = {
            **base_config,
            "application": {
                **base_config.get("application", {}),
                "terminal_startup_help": mode,
            },
        }
        config_path = tmp_path / f"{mode}.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        app = term_mod.TerminalApplication(
            config_path=str(config_path),
            session_root=str(tmp_path / f"sessions-{mode}"),
        )
        lines = term_mod._startup_help_lines(app)
        assert len(lines) == expected_lines
        assert lines[0].startswith("Session started")

    assert "/tool-output" in "\n".join(
        term_mod._startup_help_lines(
            term_mod.TerminalApplication(
                config_path=str(tmp_path / "summary.json"),
                session_root=str(tmp_path / "sessions-summary-2"),
            )
        )
    )


def test_reset_terminal_transient_state_clears_progress_and_renderer(
    tmp_path: Path,
) -> None:
    base_dir = Path(term_mod.__file__).resolve().parent
    app = term_mod.TerminalApplication(
        config_path=str(base_dir / "config_echo_app.json"),
        session_root=str(tmp_path / "sessions"),
    )
    app.start_new_session(agent_id="default")
    from agent_terminal_app.event_rendering import TerminalRenderContext

    renderer = TerminalRenderContext(
        app=app,
        footer_elements_supplier=lambda: [],
        one_line_supplier=lambda: True,
    )
    renderer.render_event(
        {
            "type": "tool_partial",
            "request_id": "request-1",
            "tool_call_id": "call-1",
            "phase": "stream",
            "payload": {"part": {"type": "text", "content": "partial"}},
        },
        lambda _line: None,
    )
    invalidations: list[bool] = []
    ui_state = {
        "renderer": renderer,
        "progress_state": TerminalProgressState(
            phase="tool",
            request_id="request-1",
            tool_call_id="call-1",
        ),
        "active_request_id": "request-1",
        "invalidate": lambda: invalidations.append(True),
    }

    term_mod._reset_terminal_transient_state(ui_state)

    assert ui_state["progress_state"] == IDLE_PROGRESS
    assert ui_state["active_request_id"] is None
    assert invalidations == [True]
    assert not renderer._tool_renderer._call_modes
