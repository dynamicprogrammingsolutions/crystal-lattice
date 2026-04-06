from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent_core.tool_interop import (
    OpenAIResponsesCustomToolCallAccessor,
    OpenAIResponsesCustomToolSchemaAccessor,
    OpenAIResponsesFunctionCallAccessor,
    OpenAIResponsesFunctionToolSchemaAccessor,
    ToolInteropTarget,
    get_registry_from_config,
    get_schema_target_formats_from_config,
)
from agent_core.types import ProviderExtensionPlugin


class OpenRouterResponsesToolsExtension(ProviderExtensionPlugin):
    """Tools extension for the OpenRouter `/responses` provider.

    Responsibilities:
    - Convert `config["tools"]` (OpenAI chat-style schemas) into Responses-native
      tool schema objects and inject them into the request payload.
    - Preserve tool_call ids on outbound tool messages (`tool_call_id`).

    Note: tool-call *parsing* is handled by the provider's streaming reducer
    (Responses emits different streaming event shapes than chat-completions).
    """

    name: str = "openrouter_responses_tools"
    version: str = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return []

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        return ["ext:openrouter_responses_tools"]

    def required_tags(self) -> List[str]:
        return ["openrouter_responses", "supports_tools"]

    def accepted_tool_schema_formats(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any] | None = None,
    ) -> List[str]:
        return [
            OpenAIResponsesFunctionToolSchemaAccessor.format_id,
            OpenAIResponsesCustomToolSchemaAccessor.format_id,
        ]

    def emitted_tool_call_formats(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any] | None = None,
    ) -> List[str]:
        return [
            OpenAIResponsesFunctionCallAccessor.format_id,
            OpenAIResponsesCustomToolCallAccessor.format_id,
        ]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        tools = config.get("tools")
        return {
            **state,
            "_openrouter_responses_tools": tools if isinstance(tools, list) else [],
        }

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Provider-native history for `/responses` is a list of Responses items.
        # Tool schemas are request-payload-only; tool call parsing and
        # tool-call-id preservation are handled by the provider's
        # core<->native conversions.
        return list(native_messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        request = state.get("request") or {}
        payload = dict(request.get("payload", {}))
        tools: List[Dict[str, Any]] = state.get("_openrouter_responses_tools") or []
        if tools and "tools" not in payload:
            registry = get_registry_from_config(state.get("config") or {})
            target_formats = get_schema_target_formats_from_config(
                state.get("config") or {}
            )
            if not target_formats:
                target_formats = self.accepted_tool_schema_formats(
                    state.get("config") or {}, state
                )
            payload_tools = registry.convert_schemas(
                [t for t in tools if isinstance(t, dict)],
                target=ToolInteropTarget("openai.responses"),
                target_formats=target_formats,
            )
            payload = {
                **payload,
                "tools": payload_tools,
                **({"tool_choice": payload.get("tool_choice", "auto")}),
            }

        return {**state, "request": {**request, "payload": payload}}
