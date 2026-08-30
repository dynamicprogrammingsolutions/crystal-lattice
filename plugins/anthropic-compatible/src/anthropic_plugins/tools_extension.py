"""Anthropic tool schema, call, and result extension."""

from __future__ import annotations

from typing import Any

from agent_core.tool_interop import (
    OpenAIChatToolSchemaAccessor,
    ToolInteropError,
    ToolInteropContribution,
    ToolInteropTarget,
    get_registry_from_context,
    get_schema_target_formats_from_context,
)
from agent_core.types import ProviderExtensionPlugin

ANTHROPIC_SCHEMA_FORMAT = "anthropic.messages.tool_schema"
ANTHROPIC_CALL_FORMAT = "anthropic.messages.tool_use"


class AnthropicToolSchemaAccessor:
    format_id = ANTHROPIC_SCHEMA_FORMAT
    format = format_id
    priority = 50

    def can_handle(self, schema: Any) -> bool:
        return (
            isinstance(schema, dict)
            and isinstance(schema.get("name"), str)
            and bool(schema["name"])
            and isinstance(schema.get("input_schema"), dict)
        )

    def get_tool_type(self, schema: dict[str, Any]) -> str:
        return "tool"

    def get_tool_name(self, schema: dict[str, Any]) -> str:
        name = schema.get("name")
        if not isinstance(name, str) or not name:
            raise ToolInteropError("Anthropic tool schema missing name")
        return name

    def get_description(self, schema: dict[str, Any]) -> str | None:
        value = schema.get("description")
        return value if isinstance(value, str) else None

    def get_parameters_schema(self, schema: dict[str, Any]) -> dict[str, Any] | None:
        value = schema.get("input_schema")
        return value if isinstance(value, dict) else None

    def get_tool_kind(self, schema: dict[str, Any]) -> str:
        return "tool"

    def get_schema_format(self, schema: dict[str, Any]) -> str:
        return self.format_id


class AnthropicToolUseAccessor:
    format_id = ANTHROPIC_CALL_FORMAT
    format = format_id
    priority = 50

    def can_handle(self, call: Any) -> bool:
        return (
            isinstance(call, dict)
            and call.get("type") == "tool_use"
            and isinstance(call.get("id"), str)
            and bool(call["id"])
            and isinstance(call.get("name"), str)
            and bool(call["name"])
        )

    def get_call_id(self, call: dict[str, Any]) -> str:
        value = call.get("id")
        if not isinstance(value, str) or not value:
            raise ToolInteropError("Anthropic tool_use missing id")
        return value

    def get_tool_type(self, call: dict[str, Any]) -> str:
        return "tool_use"

    def get_tool_name(self, call: dict[str, Any]) -> str:
        value = call.get("name")
        if not isinstance(value, str) or not value:
            raise ToolInteropError("Anthropic tool_use missing name")
        return value

    def get_payload(self, call: dict[str, Any]) -> Any:
        value = call.get("input")
        return value if isinstance(value, dict) else {}

    def get_payload_kind(self, call: dict[str, Any]) -> str:
        return "object"

    def get_payload_format(self, call: dict[str, Any]) -> str:
        return "json"

    def get_payload_metadata(self, call: dict[str, Any]) -> dict[str, Any]:
        return {}

    def sanitize_call(self, call: dict[str, Any]) -> dict[str, Any]:
        value = dict(call)
        if not isinstance(value.get("input"), dict):
            value["input"] = {}
        return value


class OpenAIChatSchemaToAnthropicSchema:
    source_format = OpenAIChatToolSchemaAccessor.format_id
    target_format = ANTHROPIC_SCHEMA_FORMAT
    priority = 50

    _accessor = OpenAIChatToolSchemaAccessor()

    def can_handle(self, schema: Any) -> bool:
        return self._accessor.can_handle(schema)

    def convert(
        self, schema: dict[str, Any], *, target: ToolInteropTarget
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self._accessor.get_tool_name(schema),
            "input_schema": self._accessor.get_parameters_schema(schema)
            or {"type": "object", "properties": {}},
        }
        description = self._accessor.get_description(schema)
        if isinstance(description, str):
            result["description"] = description
        return result


def _fallback_schema(schema: dict[str, Any]) -> dict[str, Any] | None:
    if isinstance(schema.get("name"), str) and isinstance(
        schema.get("input_schema"), dict
    ):
        return dict(schema)
    if schema.get("type") == "function" and isinstance(schema.get("function"), dict):
        function = schema["function"]
        name = function.get("name")
        if not isinstance(name, str) or not name:
            return None
        result = {
            "name": name,
            "input_schema": function.get("parameters")
            or {
                "type": "object",
                "properties": {},
            },
        }
        if isinstance(function.get("description"), str):
            result["description"] = function["description"]
        return result
    return None


def _tool_use_blocks(native: dict[str, Any]) -> list[dict[str, Any]]:
    content = native.get("content")
    if not isinstance(content, list):
        return []
    return [
        dict(block)
        for block in content
        if isinstance(block, dict) and block.get("type") == "tool_use"
    ]


class AnthropicToolsExtension(ProviderExtensionPlugin):
    name = "anthropic_tools"
    version = "0.1.0"
    priority = 40

    def required_tags(self) -> list[str]:
        return ["provider:anthropic", "supports_tools"]

    def get_tool_interop_contribution(
        self,
        config: dict[str, Any],
        state: dict[str, Any] | None = None,
    ) -> ToolInteropContribution:
        return ToolInteropContribution(
            schema_accessors=(AnthropicToolSchemaAccessor(),),
            call_accessors=(AnthropicToolUseAccessor(),),
            schema_adapters=(OpenAIChatSchemaToAnthropicSchema(),),
        )

    def accepted_tool_schema_formats(
        self,
        config: dict[str, Any],
        state: dict[str, Any] | None = None,
    ) -> list[str]:
        return [ANTHROPIC_SCHEMA_FORMAT]

    def emitted_tool_call_formats(
        self,
        config: dict[str, Any],
        state: dict[str, Any] | None = None,
    ) -> list[str]:
        return [ANTHROPIC_CALL_FORMAT]

    def init(self, config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        tools = config.get("tools")
        return {
            **state,
            "anthropic_tools": {
                "tools": (
                    [dict(tool) for tool in tools if isinstance(tool, dict)]
                    if isinstance(tools, list)
                    else []
                ),
            },
        }

    def initialize_request(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ):
        extension_state = dict(state.get("anthropic_tools") or {})
        tools = extension_state.get("tools")
        if not isinstance(tools, list) or not tools:
            return list(native_messages), state
        registry = get_registry_from_context(context)
        target_formats = get_schema_target_formats_from_context(context)
        if not target_formats:
            target_formats = [ANTHROPIC_SCHEMA_FORMAT]
        try:
            converted = registry.convert_schemas(
                tools,
                target=ToolInteropTarget("anthropic.messages"),
                target_formats=target_formats,
            )
        except Exception:
            converted = [
                result
                for schema in tools
                if (result := _fallback_schema(schema)) is not None
            ]
        request = dict(state.get("request") or {})
        payload = dict(request.get("payload") or {})
        if converted:
            payload["tools"] = converted
            tool_choice = (state.get("config") or {}).get("tool_choice")
            if isinstance(tool_choice, dict):
                payload["tool_choice"] = dict(tool_choice)
        return list(native_messages), {
            **state,
            "request": {**request, "payload": payload},
        }

    def to_native_messages(
        self,
        messages: list[dict[str, Any]],
        native_messages: list[dict[str, Any]],
        state: dict[str, Any] | None = None,
        *,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if len(messages) != len(native_messages):
            return list(native_messages)
        output: list[dict[str, Any]] = []
        for message, native in zip(messages, native_messages):
            if message.get("role") != "tool":
                output.append(dict(native))
                continue
            metadata = dict(message.get("metadata") or {})
            call_id = metadata.get("tool_call_id")
            if not isinstance(call_id, str) or not call_id:
                raise ValueError("Anthropic tool result requires metadata.tool_call_id")
            content: Any = message.get("content", "")
            result = message.get("toolResult")
            native_result_block: dict[str, Any] | None = None
            if (
                isinstance(result, dict)
                and result.get("format") == "anthropic.messages"
            ):
                result_content = result.get("content")
                if isinstance(result_content, list):
                    if (
                        len(result_content) == 1
                        and isinstance(result_content[0], dict)
                        and result_content[0].get("type") == "tool_result"
                    ):
                        native_result_block = {
                            **result_content[0],
                            "tool_use_id": call_id,
                        }
                    else:
                        content = result_content
            block = native_result_block or {
                "type": "tool_result",
                "tool_use_id": call_id,
                "content": content,
            }
            output.append(
                {
                    "role": "user",
                    "content": [block],
                    "_metadata": {
                        **metadata,
                        "core_role": "tool",
                    },
                }
            )
        return output

    def from_native_messages(
        self,
        native_messages: list[dict[str, Any]],
        messages: list[dict[str, Any]],
        state: dict[str, Any] | None = None,
        *,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if len(messages) != len(native_messages):
            return list(messages)
        output: list[dict[str, Any]] = []
        for native, message in zip(native_messages, messages):
            metadata = dict(message.get("metadata") or {})
            calls = _tool_use_blocks(native)
            if calls:
                metadata["tool_calls"] = calls
            content = native.get("content")
            result_blocks = (
                [
                    block
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "tool_result"
                ]
                if isinstance(content, list)
                else []
            )
            if result_blocks and len(result_blocks) == 1:
                block = result_blocks[0]
                metadata["tool_call_id"] = block.get("tool_use_id")
                text = block.get("content")
                if isinstance(text, list):
                    text = "\n".join(
                        str(part.get("text") or "")
                        for part in text
                        if isinstance(part, dict)
                    )
                output.append(
                    {
                        **message,
                        "role": "tool",
                        "content": str(text or ""),
                        "metadata": metadata,
                    }
                )
                continue
            output.append({**message, "metadata": metadata})
        return output

    def process_chunk(
        self,
        native_chunk: dict[str, Any] | None,
        partial_messages: list[dict[str, Any]],
        final_messages: list[dict[str, Any]],
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ):
        event = native_chunk or {}
        if event.get("type") != "content_block_stop":
            return (
                list(partial_messages),
                list(final_messages),
                list(native_messages),
                state,
            )
        accumulator = state.get("accumulator")
        calls = _tool_use_blocks(accumulator if isinstance(accumulator, dict) else {})
        if not calls or not partial_messages:
            return (
                list(partial_messages),
                list(final_messages),
                list(native_messages),
                state,
            )
        patched = [
            *partial_messages[:-1],
            {
                **partial_messages[-1],
                "_metadata": {
                    **dict(partial_messages[-1].get("_metadata") or {}),
                    "tool_calls": calls,
                },
            },
        ]
        return patched, list(final_messages), list(native_messages), state

    def finalize(
        self,
        final_messages: list[dict[str, Any]],
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ):
        sanitized: list[dict[str, Any]] = []
        for message in final_messages:
            content = message.get("content")
            blocks: list[dict[str, Any]] = []
            for block in content if isinstance(content, list) else []:
                if not isinstance(block, dict):
                    continue
                item = dict(block)
                if item.get("type") == "tool_use" and not isinstance(
                    item.get("input"), dict
                ):
                    item["input"] = {}
                blocks.append(item)
            sanitized.append({**message, "content": blocks})
        if not sanitized:
            return list(final_messages), list(native_messages), state
        history = [*native_messages[: -len(final_messages)], *sanitized]
        return sanitized, history, state
