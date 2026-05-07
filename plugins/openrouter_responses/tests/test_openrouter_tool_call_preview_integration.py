from __future__ import annotations

import json
from typing import Any, Dict, List

from agent_core import AgentCore
from openrouter_responses_plugins.openrouter_responses_provider import (
    OpenRouterResponsesProvider,
)
from openrouter_responses_plugins.openrouter_responses_tools_extension import (
    OpenRouterResponsesToolsExtension,
)
from plugins.tool_call_preview_feature import ToolCallPreviewFeature


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


class _ScriptedOpenRouterProvider(OpenRouterResponsesProvider):
    scripted_payloads: List[Dict[str, Any]] = []
    cursor: int = 0

    def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        model = config.get("model") or "openai/gpt-5-mini"
        return [{"id": model, "supported_parameters": ["tools"]}]

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        state = super().init(config)
        type(self).cursor = 0
        return state

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ):
        if type(self).cursor >= len(type(self).scripted_payloads):
            raise RuntimeError("no scripted payload remaining")
        payload = type(self).scripted_payloads[type(self).cursor]
        type(self).cursor += 1

        output = payload.get("output")
        output_items = output if isinstance(output, list) else []
        output_items = [item for item in output_items if isinstance(item, dict)]
        internal = self._response_internal_metadata(payload if isinstance(payload, dict) else {})
        annotated = self._attach_internal_metadata_to_output(output_items, internal)
        return [], annotated, [*native_messages, *annotated], state


def _config() -> Dict[str, Any]:
    return {
        "model": "openai/gpt-5-mini",
        "api_key": "test-key",
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 30,
    }


def test_tool_call_preview_feature_persists_on_openrouter_tool_calls() -> None:
    _ScriptedOpenRouterProvider.scripted_payloads = [
        {
            "id": "resp_openrouter_preview_1",
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

    core = AgentCore()
    core.register_provider(
        _ScriptedOpenRouterProvider,
        extensions=[OpenRouterResponsesToolsExtension],
    )
    core.register_feature(ToolCallPreviewFeature)
    core.register_tool(_PreviewAddTool)

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