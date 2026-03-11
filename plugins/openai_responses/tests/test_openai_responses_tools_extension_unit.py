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


def test_process_chunk_accumulates_function_call_argument_deltas_and_patches_finals() -> None:
    ext = OpenAIResponsesToolsExtension()
    state = ext.init({}, {})

    partials: list[Dict[str, Any]] = []
    finals: list[Dict[str, Any]] = []
    native_messages: list[Dict[str, Any]] = []

    events = [
        {
            "type": "response.output_item.added",
            "output_index": 0,
            "item": {
                "id": "fc_1",
                "type": "function_call",
                "call_id": "call_add_1",
                "name": "add",
                "arguments": "",
            },
        },
        {
            "type": "response.function_call_arguments.delta",
            "item_id": "fc_1",
            "delta": '{"a": 2, ',
        },
        {
            "type": "response.function_call_arguments.delta",
            "item_id": "fc_1",
            "delta": '"b": 3}',
        },
    ]

    for event in events:
        partials, finals, native_messages, state = ext.process_chunk(
            event,
            partials,
            finals,
            native_messages,
            state,
        )

    provider_finals = [
        {
            "type": "function_call",
            "call_id": "call_add_1",
            "name": "add",
            "arguments": "",
            "_metadata": {"response_id": "resp_1"},
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "Using tool."}],
            "_metadata": {"response_id": "resp_1"},
        },
    ]

    _partials, patched_finals, _native_messages, state = ext.process_chunk(
        {
            "type": "response.completed",
            "response": {
                "id": "resp_1",
                "output": [
                    {
                        "id": "fc_1",
                        "type": "function_call",
                        "call_id": "call_add_1",
                        "name": "add",
                        "arguments": "",
                    }
                ],
            },
        },
        partials,
        provider_finals,
        native_messages,
        state,
    )

    assert patched_finals[0]["type"] == "function_call"
    assert patched_finals[0]["call_id"] == "call_add_1"
    assert json.loads(patched_finals[0]["arguments"]) == {"a": 2, "b": 3}

    stream_state = state["_openai_responses_tools_stream"]
    assert stream_state["entries"] == {}


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
        msg for msg in rebuilt_core if isinstance(msg, dict) and msg.get("role") == "assistant"
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

    tool_message = next(msg for msg in rebuilt_core if isinstance(msg, dict) and msg.get("role") == "tool")
    assert (tool_message.get("metadata") or {}).get("tool_call_id") == "call_add_1"