from __future__ import annotations

import json
from typing import Any, Dict, List

from agent_core import AgentCore
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
from openai_responses_plugins.openai_responses_tools_extension import (
    OpenAIResponsesToolsExtension,
)
from plugins.math_tools import MathTools


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