from __future__ import annotations

"""Integration-style tests for AssistantRenderer web citations.

These tests exercise the terminal event rendering pipeline end to end
for assistant messages that contain web citation metadata
(``metadata.url_citations``), without relying on a live provider.

They ensure that:

- AssistantRenderer.render_message prints a citations line when
  url_citations are present in metadata.
- AssistantRenderer.render_event prints the same citations line on the
  final event of a streamed assistant message.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))


# Load TerminalApplication from source so the tests do not depend on an
# installed package.
import importlib.util

_term_app_path = APP_PY / "agent_terminal_app" / "terminal_app.py"
_term_app_spec = importlib.util.spec_from_file_location(
    "agent_terminal_app.terminal_app",
    str(_term_app_path),
)
if _term_app_spec is None or _term_app_spec.loader is None:  # pragma: no cover - defensive
    raise ImportError("cannot load TerminalApplication module")
_term_app_mod = importlib.util.module_from_spec(_term_app_spec)
_term_app_spec.loader.exec_module(_term_app_mod)
TerminalApplication = getattr(_term_app_mod, "TerminalApplication")


_event_render_path = APP_PY / "agent_terminal_app" / "event_rendering.py"
_event_spec = importlib.util.spec_from_file_location(
    "agent_terminal_app.event_rendering",
    str(_event_render_path),
)
if _event_spec is None or _event_spec.loader is None:  # pragma: no cover - defensive
    raise ImportError("cannot load event_rendering module")
_event_mod = importlib.util.module_from_spec(_event_spec)
_event_spec.loader.exec_module(_event_mod)
TerminalRenderContext = getattr(_event_mod, "TerminalRenderContext")


def _make_terminal_app(tmp_path: Path) -> TerminalApplication:
    """Create a minimal TerminalApplication using the echo config.

    The echo config avoids any real provider calls; these tests only
    exercise local rendering of synthetic assistant messages.
    """

    config_path = APP_PY / "agent_terminal_app" / "config_echo_app.json"
    session_root = tmp_path / "sessions"
    return TerminalApplication(
        config_path=str(config_path),
        session_root=str(session_root),
    )


@pytest.fixture
def terminal_app(tmp_path: Path) -> TerminalApplication:
    app = _make_terminal_app(tmp_path)
    # Start a session so that current_agent_id() has context.
    app.start_new_session(agent_id="default")
    return app


def _make_assistant_message() -> Dict[str, Any]:
    return {
        "role": "assistant",
        "content": "Here are some sources.",
        "metadata": {
            "url_citations": [
                {
                    "url": "https://example.com/a",
                    "title": "Example A",
                },
                {
                    "url": "https://example.com/b",
                },
            ],
            "web_search_sources": [
                {
                    "url": "https://example.com/full-a",
                    "title": "Full Source A",
                },
                {
                    "url": "https://example.com/full-b",
                },
            ],
        },
    }


def test_assistant_renderer_renders_citations_in_list_view(terminal_app: TerminalApplication) -> None:
    """render_message prints a citations line when url_citations exist."""

    lines: List[str] = []

    def write(text: str) -> None:
        lines.append(text)

    renderer = TerminalRenderContext(
        app=terminal_app,
        footer_elements_supplier=lambda: terminal_app.message_footer_elements(),
    )

    msg = _make_assistant_message()

    renderer.render_message(0, msg, write, short=False)

    rendered = "\n".join(lines)
    assert "citations:" in rendered
    assert "https://example.com/a" in rendered
    assert "https://example.com/b" in rendered
    assert "sources:" in rendered
    assert "https://example.com/full-a" in rendered
    assert "https://example.com/full-b" in rendered


def test_assistant_renderer_renders_citations_on_final_event(terminal_app: TerminalApplication) -> None:
    """render_event prints citations line for final assistant event."""

    lines: List[str] = []

    def write(text: str) -> None:
        lines.append(text)

    renderer = TerminalRenderContext(
        app=terminal_app,
        footer_elements_supplier=lambda: terminal_app.message_footer_elements(),
    )

    msg = _make_assistant_message()

    events: List[Dict[str, Any]] = [
        {"type": "assistant_message", "phase": "start"},
        {"type": "final", "messages": [msg]},
    ]

    for ev in events:
        renderer.render_event(ev, write)

    rendered = "\n".join(lines)
    assert "citations:" in rendered
    assert "https://example.com/a" in rendered
    assert "https://example.com/b" in rendered
    assert "sources:" in rendered
    assert "https://example.com/full-a" in rendered
    assert "https://example.com/full-b" in rendered
