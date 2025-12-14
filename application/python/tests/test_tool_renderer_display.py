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
