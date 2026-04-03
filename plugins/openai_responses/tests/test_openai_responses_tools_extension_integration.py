from __future__ import annotations

import json
from typing import Any, Dict, List

from agent_core import AgentCore
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
from openai_responses_plugins.openai_responses_tools_extension import (
    OpenAIResponsesToolsExtension,
)
from plugins.math_tools import MathTools
from plugins.tool_call_preview_feature import ToolCallPreviewFeature


class _ScriptedResponse:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def model_dump(self, mode: str = "python") -> Dict[str, Any]:
        _ = mode
        return self._payload


class _ScriptedResponsesResource:
    def __init__(self, payloads: List[Dict[str, Any]]) -> None:
        self._payloads = list(payloads)
        self.calls: List[Dict[str, Any]] = []
        self._cursor = 0

    def create(self, **kwargs: Any) -> _ScriptedResponse:
        self.calls.append(kwargs)
        if self._cursor >= len(self._payloads):
            raise RuntimeError("no scripted response remaining")
        payload = self._payloads[self._cursor]
        self._cursor += 1
        return _ScriptedResponse(payload)


class _ScriptedClient:
    def __init__(self, payloads: List[Dict[str, Any]]) -> None:
        self.responses = _ScriptedResponsesResource(payloads)


class _ScriptedToolsProvider(OpenAIResponsesProvider):
    scripted_payloads: List[Dict[str, Any]] = []
    last_client: _ScriptedClient | None = None

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        state = super().init(config)
        if type(self).last_client is None:
            type(self).last_client = _ScriptedClient(list(type(self).scripted_payloads))
        state["client"] = type(self).last_client
        return state


class _PreviewAddTool:
    name = "preview_add_tool"
    version = "1.0.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {}

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
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
        ]

    def execute_tool(
        self,
        tool_name: str,
        payload: Any,
        state: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        _ = tool_name, state, kwargs
        if not isinstance(payload, dict):
            return {"success": False, "error": "invalid payload"}
        return {"success": True, "result": payload.get("a", 0) + payload.get("b", 0)}

    def format_tool_call_preview(
        self,
        tool_name: str,
        payload: Any,
        state: Dict[str, Any],
        **kwargs: Any,
    ) -> str:
        _ = tool_name, state, kwargs
        if not isinstance(payload, dict):
            return ""
        return f"add({payload.get('a')}, {payload.get('b')})"


def _config() -> Dict[str, Any]:
    return {
        "model": "gpt-5-mini",
        "api_key": "test_key",
        "base_url": "https://api.openai.com/v1",
        "timeout": 30,
    }


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        _ScriptedToolsProvider,
        extensions=[OpenAIResponsesToolsExtension],
    )
    core.register_tool(MathTools)
    return core


def _build_preview_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        _ScriptedToolsProvider,
        extensions=[OpenAIResponsesToolsExtension],
    )
    core.register_feature(ToolCallPreviewFeature)
    core.register_tool(_PreviewAddTool)
    return core


def test_single_turn_tool_loop_with_scripted_responses_provider() -> None:
    _ScriptedToolsProvider.last_client = None
    _ScriptedToolsProvider.scripted_payloads = [
        {
            "id": "resp_tool_1",
            "output": [
                {
                    "type": "function_call",
                    "call_id": "call_add_1",
                    "name": "add",
                    "arguments": json.dumps({"a": 2, "b": 3}),
                },
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Using tool."}],
                },
            ],
        }
    ]

    core = _build_core()
    session = core.create_session()
    session = core.add_message(session, "user", "What is 2 + 3?")

    _new_session, responses = core.send_request(session, _config())

    assert responses
    assistant = responses[-1]
    assert assistant.get("role") == "assistant"

    metadata = assistant.get("metadata") or {}
    tool_calls = metadata.get("tool_calls") or []
    assert len(tool_calls) == 1
    assert tool_calls[0]["id"] == "call_add_1"
    assert (tool_calls[0].get("function") or {}).get("name") == "add"
    assert json.loads((tool_calls[0].get("function") or {}).get("arguments", "{}")) == {
        "a": 2,
        "b": 3,
    }

    tool_results = core.execute_tool_calls(tool_calls, _config())
    assert len(tool_results) == 1
    assert tool_results[0].get("role") == "tool"
    assert tool_results[0].get("content") == "5"
    tool_result_metadata = tool_results[0].get("metadata") or {}
    assert tool_result_metadata.get("tool_call_id") == "call_add_1"
    assert tool_result_metadata.get("tool_name") == "add"
    assert tool_result_metadata.get("tool_plugin") == "math_tools"

    client = _ScriptedToolsProvider.last_client
    assert client is not None
    first_call = client.responses.calls[0]
    assert first_call["stream"] is False
    assert isinstance(first_call.get("tools"), list)
    assert len(first_call["tools"]) == 3
    assert {tool.get("name") for tool in first_call["tools"]} == {"add", "multiply", "square"}


def test_multi_turn_tool_loop_with_function_call_output_continuity() -> None:
    _ScriptedToolsProvider.last_client = None
    _ScriptedToolsProvider.scripted_payloads = [
        {
            "id": "resp_tool_1",
            "output": [
                {
                    "type": "function_call",
                    "call_id": "call_add_1",
                    "name": "add",
                    "arguments": json.dumps({"a": 2, "b": 3}),
                },
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Using tool."}],
                },
            ],
        },
        {
            "id": "resp_tool_2",
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Final answer: 5"}],
                }
            ],
        },
    ]

    core = _build_core()
    cfg = _config()

    session = core.create_session()
    session = core.add_message(session, "user", "Compute 2 + 3 with tools.")

    session, first_responses = core.send_request(session, cfg)
    tool_calls = (first_responses[-1].get("metadata") or {}).get("tool_calls") or []
    assert len(tool_calls) == 1

    for tool_message in core.execute_tool_calls(tool_calls, cfg):
        session = core.add_message(
            session,
            role=tool_message.get("role", "tool"),
            content=tool_message.get("content", ""),
            metadata=tool_message.get("metadata"),
            config=cfg,
        )

    _session_after_tools, second_responses = core.send_request(session, cfg)
    assert second_responses
    assert second_responses[-1].get("role") == "assistant"
    assert "Final answer: 5" in (second_responses[-1].get("content") or "")

    client = _ScriptedToolsProvider.last_client
    assert client is not None
    assert len(client.responses.calls) == 2

    second_input = client.responses.calls[1]["input"]
    assert any(
        isinstance(item, dict)
        and item.get("type") == "function_call_output"
        and item.get("call_id") == "call_add_1"
        and item.get("output") == "5"
        for item in second_input
    )


def test_tool_call_preview_feature_persists_on_openai_responses_tool_calls() -> None:
    _ScriptedToolsProvider.last_client = None
    _ScriptedToolsProvider.scripted_payloads = [
        {
            "id": "resp_tool_preview_1",
            "output": [
                {
                    "type": "function_call",
                    "call_id": "call_add_1",
                    "name": "add",
                    "arguments": json.dumps({"a": 2, "b": 3}),
                },
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Using tool."}],
                },
            ],
        }
    ]

    core = _build_preview_core()
    cfg = _config()
    session = core.create_session()
    session = core.add_message(session, "user", "What is 2 + 3?")

    next_session, responses = core.send_request(session, cfg)

    assistant = responses[-1]
    metadata = assistant.get("metadata") or {}
    assert metadata.get("tool_call_previews") == [{"id": "call_add_1", "preview": "add(2, 3)"}]

    native_messages = next_session.metadata.get("native_messages") or []
    preview_anchors = [
        item
        for item in native_messages
        if isinstance(item, dict)
        and isinstance(item.get("_metadata"), dict)
        and "tool_call_previews" in item.get("_metadata", {})
    ]
    assert len(preview_anchors) == 1
    assert (preview_anchors[0].get("_metadata") or {}).get("tool_call_previews") == [
        {"id": "call_add_1", "preview": "add(2, 3)"}
    ]

    rebuilt_messages, _ = core._rebuild_core_from_native(native_messages, cfg)
    rebuilt_assistant = rebuilt_messages[-1].to_dict()
    rebuilt_metadata = rebuilt_assistant.get("metadata") or {}
    assert rebuilt_metadata.get("tool_call_previews") == [
        {"id": "call_add_1", "preview": "add(2, 3)"}
    ]