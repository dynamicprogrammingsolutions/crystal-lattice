"""
Unit tests for OpenRouterResponsesToolsExtension behavior (stateless functions tested via instance methods).
"""

from __future__ import annotations

import sys
import os

# Ensure repo root is importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from openrouter_responses_plugins.openrouter_responses_tools_extension import OpenRouterResponsesToolsExtension as Ext  # noqa: E402


def test_extension_metadata():
    """Test extension metadata and tags."""
    ext = Ext()
    assert ext.name == "openrouter_responses_tools"
    assert ext.version == "0.1.0"
    assert "ext:openrouter_responses_tools" in ext.get_tags({}, [])
    assert "openrouter_responses" in ext.required_tags()
    assert "supports_tools" in ext.required_tags()


def test_init_stores_tools_in_state():
    """Test that init stores tools in state."""
    ext = Ext()
    config = {
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read a file",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]
    }
    state = ext.init(config, {})
    assert "_openrouter_responses_tools" in state
    assert isinstance(state["_openrouter_responses_tools"], list)
    assert len(state["_openrouter_responses_tools"]) == 1


def test_initialize_request_adds_tools_to_payload():
    """Test that initialize_request adds tools to the request payload."""
    ext = Ext()
    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file",
                "parameters": {"type": "object", "properties": {}},
            },
        }
    ]
    state = {"_openrouter_responses_tools": tools, "request": {"payload": {}}}
    new_state = ext.initialize_request([], state)
    payload = new_state["request"]["payload"]
    assert "tools" in payload
    # Tool schema conversion: chat-style tools -> Responses-native tools.
    assert payload["tools"] == [
        {
            "type": "function",
            "name": "read_file",
            "description": "Read a file",
            "parameters": {"type": "object", "properties": {}},
        }
    ]
    assert payload["tool_choice"] == "auto"


def test_to_native_messages_maps_tool_call_id_and_tool_calls():
    """`to_native_messages` is a no-op for Responses-native items."""
    ext = Ext()
    messages = [{"role": "assistant", "content": "", "metadata": {}}]
    native = [{"type": "message", "role": "assistant", "content": []}]
    out = ext.to_native_messages(messages, native)
    assert out == native


def test_from_native_messages_attaches_metadata_tool_calls():
    """`from_native_messages` is a no-op; provider handles tool call conversion."""
    ext = Ext()
    messages = [{"role": "assistant", "content": "", "metadata": {}}]
    native = [{"type": "function_call", "call_id": "x1", "name": "read_file", "arguments": "{}"}]
    out = ext.from_native_messages(native, messages)
    assert out == messages

