from __future__ import annotations

from typing import Any, Dict, List

from agent_terminal_app.event_rendering import ToolRenderer


class _DummyAgentApp:
    def get_application_config(self) -> Dict[str, Any]:
        return {}


class _DummyTerminalApp:
    def __init__(self) -> None:
        self.agent_app = _DummyAgentApp()


def _capture_writer(lines: List[str]):
    def write(text: str) -> None:
        lines.append(text)

    return write


def test_tool_renderer_prefers_display_text_over_content() -> None:
    app = _DummyTerminalApp()
    renderer = ToolRenderer(app)  # type: ignore[arg-type]

    lines: List[str] = []
    write = _capture_writer(lines)

    message = {
        "role": "tool",
        "content": "ORIGINAL CONTENT",
        "metadata": {
            "display": {"type": "text", "content": "DISPLAY PAYLOAD"},
        },
    }

    renderer.render_message(0, message, write)

    rendered = "\n".join(lines)
    assert "Tool:" in rendered
    assert "DISPLAY PAYLOAD" in rendered
    assert "ORIGINAL CONTENT" not in rendered


def test_tool_renderer_falls_back_to_content_when_no_display() -> None:
    app = _DummyTerminalApp()
    renderer = ToolRenderer(app)  # type: ignore[arg-type]

    lines: List[str] = []
    write = _capture_writer(lines)

    message = {
        "role": "tool",
        "content": "ONLY CONTENT",
        "metadata": {},
    }

    renderer.render_message(1, message, write)

    rendered = "\n".join(lines)
    assert "Tool:" in rendered
    assert "ONLY CONTENT" in rendered


def test_tool_renderer_uses_display_in_streaming_end_event() -> None:
    """Non-streaming tools should use display payload during streaming.

    When a tool does not stream partials, the tool loop emits a single
    ``tool_partial`` event with ``phase == "end"`` and the final tool
    message under ``payload.result``. ToolRenderer should render the
    display-aware content (metadata.display) for this case so that
    streaming output matches the history view.
    """

    app = _DummyTerminalApp()
    renderer = ToolRenderer(app)  # type: ignore[arg-type]

    lines: List[str] = []
    write = _capture_writer(lines)

    result: Dict[str, Any] = {
        "role": "tool",
        "content": "PLAIN CONTENT",
        "metadata": {
            "tool_name": "dummy",
            "tool_call_id": "call-1",
            "display": {"type": "text", "content": "DISPLAY CONTENT"},
        },
    }

    event: Dict[str, Any] = {
        "type": "tool_partial",
        "tool_call_id": "call-1",
        "phase": "end",
        "payload": {"result": result},
    }

    renderer.render_event(event, write)

    rendered = "\n".join(lines)
    # Header and footer should still be present.
    assert "Tool:" in rendered
    assert "dummy" in rendered
    # Display payload should be used instead of the plain content.
    assert "DISPLAY CONTENT" in rendered
    assert "PLAIN CONTENT" not in rendered
