"""OpenAI Responses tools extension.

Extension responsibilities:
- inject Responses-native tool schemas into request payloads
- map assistant tool_calls <-> Responses function_call items
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from agent_core.tool_interop import (
    DEFAULT_TOOL_INTEROP_REGISTRY,
    OpenAIChatToolSchemaToOpenAIResponsesToolSchema,
    OpenAIResponsesToolCallToOpenAIChatToolCall,
    ToolInteropError,
    ToolInteropTarget,
)
from agent_core.types import ProviderExtensionPlugin


_TOOLS_STATE_KEY = "_openai_responses_tools"


class OpenAIResponsesToolsExtension(ProviderExtensionPlugin):
    name: str = "openai_responses_tools"
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

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        return ["ext:openai_responses_tools"]

    def required_tags(self) -> List[str]:
        return ["openai_responses", "supports_tools"]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        tools = config.get("tools")
        stored = tools if isinstance(tools, list) else []
        return {**state, _TOOLS_STATE_KEY: stored}

    def _native_internal_from_core_metadata(self, metadata: Any) -> Dict[str, Any]:
        if not isinstance(metadata, dict):
            return {}
        out = dict(metadata)
        out.pop("native_indices", None)
        out.pop("tool_calls", None)
        return out

    def _stringify_arguments(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        if value is None:
            return ""
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return ""

    def _assistant_tool_calls_to_native_items(
        self,
        tool_calls: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        native_internal_md = self._native_internal_from_core_metadata(metadata)

        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue
            try:
                accessor = DEFAULT_TOOL_INTEROP_REGISTRY.get_call_accessor(tool_call)
                call_id = accessor.get_call_id(tool_call)
                tool_name = accessor.get_tool_name(tool_call)
                arguments = self._stringify_arguments(accessor.get_arguments(tool_call))
            except ToolInteropError:
                continue

            native_item: Dict[str, Any] = {
                "type": "function_call",
                "call_id": call_id,
                "name": tool_name,
                "arguments": arguments,
            }
            if native_internal_md:
                native_item["_metadata"] = dict(native_internal_md)
            out.append(native_item)
        return out

    def _is_empty_assistant_native_message(
        self,
        core_message: Dict[str, Any],
        native_message: Dict[str, Any],
    ) -> bool:
        if native_message.get("type") != "message" or native_message.get("role") != "assistant":
            return False

        native_content = native_message.get("content")
        if isinstance(native_content, list) and native_content:
            return False

        content = core_message.get("content")
        if isinstance(content, str) and content.strip():
            return False

        multipart = core_message.get("multipartContent")
        if isinstance(multipart, list) and multipart:
            return False

        metadata = core_message.get("metadata")
        if isinstance(metadata, dict) and isinstance(metadata.get("phase"), str):
            return False

        return True

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not messages or not native_messages:
            return list(native_messages)

        out: List[Dict[str, Any]] = []
        for idx, native_message in enumerate(native_messages):
            if not isinstance(native_message, dict):
                continue

            out.append(native_message)
            if idx >= len(messages):
                continue

            message = messages[idx]
            if not isinstance(message, dict):
                continue

            role = message.get("role")
            metadata = message.get("metadata")

            if role == "assistant" and isinstance(metadata, dict):
                tool_calls = metadata.get("tool_calls")
                if isinstance(tool_calls, list) and tool_calls:
                    native_tool_items = self._assistant_tool_calls_to_native_items(
                        [tc for tc in tool_calls if isinstance(tc, dict)],
                        metadata,
                    )
                    if native_tool_items:
                        if self._is_empty_assistant_native_message(message, native_message):
                            out.pop()
                        out.extend(native_tool_items)

            if role == "tool" and isinstance(metadata, dict):
                tool_call_id = metadata.get("tool_call_id")
                if (
                    isinstance(tool_call_id, str)
                    and tool_call_id
                    and out
                    and out[-1].get("type") == "function_call_output"
                ):
                    out[-1] = {**out[-1], "call_id": tool_call_id}

        return out

    def _response_id_from_native_item(self, item: Dict[str, Any]) -> Optional[str]:
        metadata = item.get("_metadata")
        if not isinstance(metadata, dict):
            return None
        response_id = metadata.get("response_id")
        if isinstance(response_id, str) and response_id:
            return response_id
        return None

    def _native_function_call_to_chat_tool_call(
        self,
        item: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        try:
            converted = DEFAULT_TOOL_INTEROP_REGISTRY.convert_tool_calls(
                [item],
                adapters=[OpenAIResponsesToolCallToOpenAIChatToolCall()],
                target=ToolInteropTarget("openai.chat_completions"),
            )
        except ToolInteropError:
            return None
        if not converted:
            return None
        tool_call = converted[0]
        return tool_call if isinstance(tool_call, dict) else None

    def _dedupe_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deduped: List[Dict[str, Any]] = []
        seen: set[Tuple[str, str, str]] = set()
        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue
            call_id = tool_call.get("id")
            function = tool_call.get("function")
            tool_name = function.get("name") if isinstance(function, dict) else None
            arguments = function.get("arguments") if isinstance(function, dict) else None
            key = (
                call_id if isinstance(call_id, str) else "",
                tool_name if isinstance(tool_name, str) else "",
                arguments if isinstance(arguments, str) else self._stringify_arguments(arguments),
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(tool_call)
        return deduped

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        tool_call_records: List[Tuple[int, Optional[str], Dict[str, Any]]] = []
        calls_by_response: Dict[str, List[Dict[str, Any]]] = {}

        for idx, native_item in enumerate(native_messages):
            if not isinstance(native_item, dict) or native_item.get("type") != "function_call":
                continue

            tool_call = self._native_function_call_to_chat_tool_call(native_item)
            if tool_call is None:
                continue

            response_id = self._response_id_from_native_item(native_item)
            tool_call_records.append((idx, response_id, tool_call))
            if response_id:
                calls_by_response.setdefault(response_id, []).append(tool_call)

        if not tool_call_records:
            return list(messages)

        out: List[Dict[str, Any]] = []
        for message in messages:
            if not isinstance(message, dict) or message.get("role") != "assistant":
                out.append(message)
                continue

            metadata_raw = message.get("metadata")
            metadata = dict(metadata_raw) if isinstance(metadata_raw, dict) else {}

            selected: List[Dict[str, Any]] = []
            native_indices = metadata.get("native_indices")
            if isinstance(native_indices, list):
                index_set = {i for i in native_indices if isinstance(i, int)}
                if index_set:
                    selected = [tc for idx, _rid, tc in tool_call_records if idx in index_set]

            if not selected:
                response_id = metadata.get("response_id")
                if isinstance(response_id, str) and response_id:
                    selected = list(calls_by_response.get(response_id) or [])

            if not selected:
                out.append(message)
                continue

            existing = metadata.get("tool_calls")
            existing_calls = [tc for tc in existing if isinstance(tc, dict)] if isinstance(existing, list) else []
            metadata["tool_calls"] = self._dedupe_tool_calls([*existing_calls, *selected])
            out.append({**message, "metadata": metadata})

        return out

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        request = state.get("request")
        if not isinstance(request, dict):
            return list(native_messages), state

        payload = dict(request.get("payload") or {})

        tools: List[Dict[str, Any]] = state.get(_TOOLS_STATE_KEY) or []
        if tools and "tools" not in payload:
            payload_tools = DEFAULT_TOOL_INTEROP_REGISTRY.convert_schemas(
                [tool for tool in tools if isinstance(tool, dict)],
                adapters=[OpenAIChatToolSchemaToOpenAIResponsesToolSchema()],
                target=ToolInteropTarget("openai.responses"),
            )
            payload = {
                **payload,
                "tools": payload_tools,
                "tool_choice": payload.get("tool_choice", "auto"),
            }

        return list(native_messages), {
            **state,
            "request": {**request, "payload": payload},
        }

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return (
            list(partial_messages),
            list(final_messages),
            list(native_messages),
            dict(state),
        )
