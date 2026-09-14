"""
Tests for Example 10's FastAPI/JSON application.

These tests exercise the minimal application built around
``agent_core.AgentCore`` and the OpenAI-compatible provider. For
predictable behaviour in tests, they override the provider to use the
in-process ``EchoOpenAILikeProvider`` via config_overrides.

The test calls the route handler functions directly instead of going
through an HTTP client so that it remains lightweight.
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
CORE_PY = os.path.join(ROOT, "core/python")
if CORE_PY not in sys.path:
    sys.path.insert(0, CORE_PY)


def _import_example_module():
    """Import the example10 module."""

    return __import__("examples.example10_fastapi_console_ollama", fromlist=["app"])


def test_example10_application_flow_direct_calls_with_echo_provider():
    """End-to-end flow through example10 using the echo provider.

    The application is configured by default for Ollama via the
    OpenAI-compatible provider, but tests use config_overrides to select
    the EchoOpenAILikeProvider so that no network access is required.
    """

    mod = _import_example_module()

    create_session = getattr(mod, "create_session")
    add_message = getattr(mod, "add_message")
    send_request = getattr(mod, "send_request")

    system_message = "You are a helpful echo assistant."
    user_message = "hello from the test"

    # 1) Create a new session with a system message.
    created = create_session({"system_message": system_message})
    session = created["session"]
    session_id = session["session_id"]

    # 2) Add a user message.
    updated = add_message(session_id, {"role": "user", "content": user_message})
    assert updated["session"]["session_id"] == session_id

    # 3) Send a request and verify the echo provider behaviour by
    # overriding the provider and model in the per-request config.
    result = send_request(
        session_id,
        {
            "config_overrides": {
                "provider": "echo_openai_like",
                "model": "test-echo-model",
            }
        },
    )

    messages = result.get("messages") or []
    assert messages, "expected at least one final message"
    last = messages[-1]
    content = last.get("content", "")
    assert isinstance(content, str)
    # EchoOpenAILikeProvider returns "SYS=<system> | USER=<user>".
    assert "SYS=" in content and "USER=" in content
    assert system_message in content
    assert user_message in content
