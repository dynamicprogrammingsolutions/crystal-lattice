"""Tests for the agent_terminal_app FastAPI/JSON application.

These tests mirror the style of the example application tests under
``core/python/examples/tests``. They import the route handler functions
from :mod:`agent_terminal_app.server` directly and call them as regular
Python functions instead of going through an HTTP client.

The application is configured to use the in-process
``EchoOpenAILikeProvider`` by default via ``config_echo_app.json`` so no
network access is required.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


# Make the application and core packages importable when running tests
# from the repository root.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
APP_PY = os.path.join(ROOT, "application/python")
if APP_PY not in sys.path:
    sys.path.insert(0, APP_PY)
CORE_PY = os.path.join(ROOT, "core/python")
if CORE_PY not in sys.path:
    sys.path.insert(0, CORE_PY)


def _import_server_module():
    """Import the agent_terminal_app server module.

    This helper mirrors the pattern used by the example tests so that
    the import remains robust when tests are run from different working
    directories.
    """

    return __import__("agent_terminal_app.server", fromlist=["app"])


def test_agent_terminal_app_flow_with_echo_provider(tmp_path: Path) -> None:
    """End-to-end flow through agent_terminal_app using the echo provider.

    The test reconfigures the application to use a temporary session
    root so that no files are written into the source tree, then calls
    ``create_session``, ``add_message``, and ``send_request`` directly
    and asserts the echo-style response and basic event emission.
    """

    mod = _import_server_module()

    configure_application = getattr(mod, "configure_application")
    create_session = getattr(mod, "create_session")
    add_message = getattr(mod, "add_message")
    send_request = getattr(mod, "send_request")
    get_event_store = getattr(mod, "get_event_store")

    # Reconfigure application to use a temporary session root.
    session_root = tmp_path / "sessions"
    config_path = Path(mod.__file__).resolve().parent / "config_echo_app.json"
    configure_application(config_path=config_path, session_root=session_root, reset=True)

    system_message = "You are a helpful echo assistant."
    user_message = "hello from the agent_terminal_app test"

    # 1) Create a new session with a system message.
    created = create_session({"agent_id": "default", "system_message": system_message})
    session = created["session"]
    session_id = session["session_id"]
    assert isinstance(session_id, str) and session_id

    # 2) Add a user message.
    updated = add_message(session_id, {"role": "user", "content": user_message})
    assert updated["session"]["session_id"] == session_id

    # 3) Send a request and verify the echo provider behaviour.
    result = send_request(session_id, {})

    messages = result.get("messages") or []
    assert messages, "expected at least one final message"
    last = messages[-1]
    content = last.get("content", "")
    assert isinstance(content, str)

    # EchoOpenAILikeProvider returns "SYS=<system> | USER=<user>".
    assert "SYS=" in content and "USER=" in content
    assert system_message in content
    assert user_message in content

    # 4) Basic check that events were recorded for this session.
    store = get_event_store()
    events = store.list(session_id=session_id, limit=100)
    kinds = {ev.get("type") for ev in events}
    assert "session_created" in kinds
    assert "message_appended" in kinds
    assert "request_started" in kinds or "final" in kinds
