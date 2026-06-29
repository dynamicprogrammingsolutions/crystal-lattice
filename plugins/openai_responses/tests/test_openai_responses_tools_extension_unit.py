from __future__ import annotations

import json
from typing import Any, Dict

from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
from openai_responses_plugins.openai_responses_tools_extension import (
    OpenAIResponsesToolsExtension,
)


def _chat_tool_schema() -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "add",
            "description": "Add two numbers",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"},
                },
                "required": ["a", "b"],
            },
        },
    }


def _chat_tool_call() -> Dict[str, Any]:
    return {
        "id": "call_add_1",
        "type": "function",
        "function": {
            "name": "add",
            "arguments": json.dumps({"a": 2, "b": 3}),
        },
    }


def _custom_tool_schema() -> Dict[str, Any]:
    return {
        "type": "custom",
        "name": "apply_patch",
        "description": "Apply a freeform patch",
        "format": {
            "type": "grammar",
            "syntax": "lark",
            "definition": "start: /.+/",
        },
    }


def test_initialize_request_converts_tool_schemas_into_responses_payload() -> None:
    ext = OpenAIResponsesToolsExtension()

    state = ext.init({"tools": [_chat_tool_schema()]}, {})
    native_after, new_state = ext.initialize_request(
        [],
        {
            **state,
            "request": {
                "payload": {
                    "model": "gpt-5-mini",
                }
            },
        },
    )

    assert native_after == []

    payload = new_state["request"]["payload"]
    assert payload["model"] == "gpt-5-mini"
    assert payload["tool_choice"] == "auto"
    assert payload["tools"] == [
        {
            "type": "function",
            "name": "add",
            "description": "Add two numbers",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"},
                },
                "required": ["a", "b"],
            },
        }
    ]


def test_initialize_request_passes_through_responses_custom_tool_schemas() -> None:
    ext = OpenAIResponsesToolsExtension()

    state = ext.init({"tools": [_custom_tool_schema()]}, {})
    native_after, new_state = ext.initialize_request(
        [],
        {
            **state,
            "config": {"tools": [_custom_tool_schema()]},
            "request": {
                "payload": {
                    "model": "gpt-5.2",
                }
            },
        },
    )

    assert native_after == []
    payload = new_state["request"]["payload"]
    assert payload["tool_choice"] == "auto"
    assert payload["tools"] == [_custom_tool_schema()]


def test_process_chunk_trusts_provider_finals_and_leaves_state_unchanged() -> None:
    ext = OpenAIResponsesToolsExtension()
    state = ext.init({}, {})

    partials: list[Dict[str, Any]] = []
    finals: list[Dict[str, Any]] = [
        {
            "type": "function_call",
            "call_id": "call_add_1",
            "name": "add",
            "arguments": json.dumps({"a": 2, "b": 3}),
            "_metadata": {"response_id": "resp_1"},
        }
    ]
    native_messages: list[Dict[str, Any]] = []

    new_partials, new_finals, new_native_messages, new_state = ext.process_chunk(
        {
            "type": "response.function_call_arguments.delta",
            "item_id": "fc_1",
            "delta": '"ignored": true',
        },
        partials,
        finals,
        native_messages,
        state,
    )

    assert new_partials == partials
    assert new_finals == finals
    assert new_native_messages == native_messages
    assert new_state == state


def test_round_trip_metadata_mapping_preserves_tool_calls_and_tool_call_ids() -> None:
    provider = OpenAIResponsesProvider()
    ext = OpenAIResponsesToolsExtension()

    core_messages = [
        {
            "role": "assistant",
            "content": "I will call add.",
            "metadata": {
                "response_id": "resp_tool_1",
                "tool_calls": [_chat_tool_call()],
            },
        },
        {
            "role": "tool",
            "content": "5",
            "metadata": {
                "tool_call_id": "call_add_1",
            },
        },
    ]

    native_from_provider = provider.to_native_messages(core_messages, {})
    native_with_tools = ext.to_native_messages(core_messages, native_from_provider)

    assert any(
        isinstance(item, dict)
        and item.get("type") == "function_call"
        and item.get("call_id") == "call_add_1"
        for item in native_with_tools
    )
    assert any(
        isinstance(item, dict)
        and item.get("type") == "function_call_output"
        and item.get("call_id") == "call_add_1"
        for item in native_with_tools
    )

    core_from_provider = provider.from_native_messages(native_with_tools, {})
    rebuilt_core = ext.from_native_messages(native_with_tools, core_from_provider)

    assistant_message = next(
        msg
        for msg in rebuilt_core
        if isinstance(msg, dict) and msg.get("role") == "assistant"
    )
    assistant_metadata = assistant_message.get("metadata") or {}
    tool_calls = assistant_metadata.get("tool_calls") or []
    assert tool_calls
    assert tool_calls[0]["id"] == "call_add_1"
    assert (tool_calls[0].get("function") or {}).get("name") == "add"
    assert json.loads((tool_calls[0].get("function") or {}).get("arguments", "{}")) == {
        "a": 2,
        "b": 3,
    }

    tool_message = next(
        msg
        for msg in rebuilt_core
        if isinstance(msg, dict) and msg.get("role") == "tool"
    )
    assert (tool_message.get("metadata") or {}).get("tool_call_id") == "call_add_1"


def test_round_trip_preserves_display_and_namespaced_metadata_on_tool_messages() -> (
    None
):
    """``display`` and namespaced tool metadata (e.g. ``bash.end_cwd``) must
    survive a provider + tools-extension round-trip on tool-result messages.

    The provider pops ``display`` from the generic ``_metadata`` carry, so the
    tools extension must re-add it. Namespaced keys like ``bash.end_cwd`` are
    not in the provider's pop-list and ride through automatically. This test
    guards against regressions in either path."""
    provider = OpenAIResponsesProvider()
    ext = OpenAIResponsesToolsExtension()

    display_payload = {"type": "text", "content": "Bash command", "single_line": True}
    core_messages = [
        {
            "role": "assistant",
            "content": "I will call Bash.",
            "metadata": {
                "response_id": "resp_bash_1",
                "tool_calls": [
                    {
                        "id": "call_bash_1",
                        "type": "function",
                        "function": {
                            "name": "Bash",
                            "arguments": json.dumps({"command": "pwd"}),
                        },
                    }
                ],
            },
        },
        {
            "role": "tool",
            "content": "/workspace",
            "metadata": {
                "tool_call_id": "call_bash_1",
                "tool_name": "Bash",
                "tool_plugin": "claude_bash_tool",
                "display": display_payload,
                "bash": {"end_cwd": "."},
            },
        },
    ]

    native_from_provider = provider.to_native_messages(core_messages, {})
    native_with_tools = ext.to_native_messages(core_messages, native_from_provider)

    # Find the function_call_output item and verify _metadata carries display
    # and bash.end_cwd.
    fc_output = next(
        item
        for item in native_with_tools
        if isinstance(item, dict) and item.get("type") == "function_call_output"
    )
    internal_md = fc_output.get("_metadata") or {}
    assert internal_md.get("display") == display_payload
    assert internal_md.get("tool_name") == "Bash"
    assert internal_md.get("tool_plugin") == "claude_bash_tool"
    assert internal_md.get("bash") == {"end_cwd": "."}

    core_from_provider = provider.from_native_messages(native_with_tools, {})
    rebuilt_core = ext.from_native_messages(native_with_tools, core_from_provider)

    tool_message = next(
        msg
        for msg in rebuilt_core
        if isinstance(msg, dict) and msg.get("role") == "tool"
    )
    metadata = tool_message.get("metadata") or {}
    assert metadata.get("tool_call_id") == "call_bash_1"
    assert metadata.get("display") == display_payload
    assert metadata.get("tool_name") == "Bash"
    assert metadata.get("tool_plugin") == "claude_bash_tool"
    assert metadata.get("bash") == {"end_cwd": "."}
