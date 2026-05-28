# Copyright 2026 Dynamic Programming Solutions Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from agent_core.tool_interop import (
    OpenAIChatToolCallAccessor,
    OpenAIChatToolSchemaAccessor,
    ToolInteropContribution,
    ToolInteropError,
    ToolInteropTarget,
)


JsonObject = Dict[str, Any]


class AnthropicToolSchemaAccessor:
    format_id = "anthropic.messages.tool_schema"
    format = format_id
    priority = 50

    def can_handle(self, schema: Any) -> bool:
        if not isinstance(schema, dict):
            return False
        name = schema.get("name")
        input_schema = schema.get("input_schema")
        return (
            isinstance(name, str)
            and bool(name.strip())
            and isinstance(input_schema, dict)
        )

    def get_tool_type(self, schema: JsonObject) -> str:
        return "tool"

    def get_tool_name(self, schema: JsonObject) -> str:
        name = schema.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ToolInteropError("Anthropic tool schema missing 'name'")
        return name

    def get_description(self, schema: JsonObject) -> Optional[str]:
        desc = schema.get("description")
        return desc if isinstance(desc, str) else None

    def get_parameters_schema(self, schema: JsonObject) -> Optional[JsonObject]:
        params = schema.get("input_schema")
        return params if isinstance(params, dict) else None

    def get_tool_kind(self, schema: JsonObject) -> str:
        return "tool"

    def get_schema_format(self, schema: JsonObject) -> str:
        return self.format_id


class AnthropicToolUseAccessor:
    format_id = "anthropic.messages.tool_use"
    format = format_id
    priority = 50

    def can_handle(self, call: Any) -> bool:
        if not isinstance(call, dict):
            return False
        if call.get("type") != "tool_use":
            return False
        call_id = call.get("id")
        name = call.get("name")
        return (
            isinstance(call_id, str)
            and bool(call_id.strip())
            and isinstance(name, str)
            and bool(name.strip())
        )

    def get_call_id(self, call: JsonObject) -> str:
        call_id = call.get("id")
        if not isinstance(call_id, str) or not call_id.strip():
            raise ToolInteropError("Anthropic tool_use missing 'id'")
        return call_id

    def get_tool_type(self, call: JsonObject) -> str:
        if call.get("type") != "tool_use":
            raise ToolInteropError("Anthropic tool call missing type='tool_use'")
        return "tool_use"

    def get_tool_name(self, call: JsonObject) -> str:
        name = call.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ToolInteropError("Anthropic tool_use missing 'name'")
        return name

    def get_payload(self, call: JsonObject) -> Any:
        payload = call.get("input")
        return payload if isinstance(payload, dict) else {}

    def get_payload_kind(self, call: JsonObject) -> str:
        return "object"

    def get_payload_format(self, call: JsonObject) -> str:
        return "json"

    def get_payload_metadata(self, call: JsonObject) -> JsonObject:
        return {}


class AnthropicToolSchemaToOpenAIChatToolSchema:
    source_format = AnthropicToolSchemaAccessor.format_id
    target_format = OpenAIChatToolSchemaAccessor.format_id
    priority = 50

    _schema_accessor = AnthropicToolSchemaAccessor()

    def can_handle(self, schema: Any) -> bool:
        return self._schema_accessor.can_handle(schema)

    def convert(self, schema: JsonObject, *, target: ToolInteropTarget) -> JsonObject:
        fn: JsonObject = {"name": self._schema_accessor.get_tool_name(schema)}
        desc = self._schema_accessor.get_description(schema)
        if desc is not None:
            fn["description"] = desc
        params = self._schema_accessor.get_parameters_schema(schema)
        if params is not None:
            fn["parameters"] = params
        return {"type": "function", "function": fn}


class OpenAIChatToolCallToAnthropicToolUse:
    source_format = OpenAIChatToolCallAccessor.format_id
    target_format = AnthropicToolUseAccessor.format_id
    priority = 50

    _call_accessor = OpenAIChatToolCallAccessor()

    def can_handle(self, call: Any) -> bool:
        return self._call_accessor.can_handle(call)

    def convert(self, call: JsonObject, *, target: ToolInteropTarget) -> JsonObject:
        payload = self._call_accessor.get_payload(call)
        if not isinstance(payload, dict):
            payload = {}
        return {
            "type": "tool_use",
            "id": self._call_accessor.get_call_id(call),
            "name": self._call_accessor.get_tool_name(call),
            "input": payload,
        }


class AnthropicToolUseToOpenAIChatToolCall:
    source_format = AnthropicToolUseAccessor.format_id
    target_format = OpenAIChatToolCallAccessor.format_id
    priority = 50

    _call_accessor = AnthropicToolUseAccessor()

    def can_handle(self, call: Any) -> bool:
        return self._call_accessor.can_handle(call)

    def convert(self, call: JsonObject, *, target: ToolInteropTarget) -> JsonObject:
        payload = self._call_accessor.get_payload(call)
        return {
            "id": self._call_accessor.get_call_id(call),
            "type": "function",
            "function": {
                "name": self._call_accessor.get_tool_name(call),
                "arguments": json.dumps(payload if isinstance(payload, dict) else {}),
            },
        }


def claude_tool_interop_contribution() -> ToolInteropContribution:
    return ToolInteropContribution(
        schema_accessors=(AnthropicToolSchemaAccessor(),),
        call_accessors=(AnthropicToolUseAccessor(),),
        schema_adapters=(AnthropicToolSchemaToOpenAIChatToolSchema(),),
        call_adapters=(
            OpenAIChatToolCallToAnthropicToolUse(),
            AnthropicToolUseToOpenAIChatToolCall(),
        ),
    )


__all__ = [
    "AnthropicToolSchemaAccessor",
    "AnthropicToolUseAccessor",
    "AnthropicToolSchemaToOpenAIChatToolSchema",
    "OpenAIChatToolCallToAnthropicToolUse",
    "AnthropicToolUseToOpenAIChatToolCall",
    "claude_tool_interop_contribution",
]
