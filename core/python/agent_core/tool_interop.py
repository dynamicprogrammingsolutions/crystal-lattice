from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Sequence


class ToolInteropError(ValueError):
    pass


JsonObject = Dict[str, Any]


@dataclass(frozen=True)
class ToolInteropTarget:
    """Identifies a wire format target."""

    name: str


class ToolSchemaAdapter(Protocol):
    source_format: str
    target_format: str

    def can_handle(self, schema: Any) -> bool:
        ...

    def convert(self, schema: JsonObject, *, target: ToolInteropTarget) -> JsonObject:
        ...


class ToolCallAdapter(Protocol):
    source_format: str
    target_format: str

    def can_handle(self, call: Any) -> bool:
        ...

    def convert(self, call: JsonObject, *, target: ToolInteropTarget) -> JsonObject:
        ...


class ToolSchemaAccessor(Protocol):
    format: str

    def can_handle(self, schema: Any) -> bool:
        ...

    def get_tool_type(self, schema: JsonObject) -> str:
        ...

    def get_tool_name(self, schema: JsonObject) -> str:
        ...

    def get_description(self, schema: JsonObject) -> Optional[str]:
        ...

    def get_parameters_schema(self, schema: JsonObject) -> Optional[JsonObject]:
        ...


class ToolCallAccessor(Protocol):
    format: str

    def can_handle(self, call: Any) -> bool:
        ...

    def get_call_id(self, call: JsonObject) -> str:
        ...

    def get_tool_type(self, call: JsonObject) -> str:
        ...

    def get_tool_name(self, call: JsonObject) -> str:
        ...

    def get_arguments(self, call: JsonObject) -> Any:
        ...


class ToolInteropRegistry:
    def __init__(
        self,
        *,
        schema_adapters: Sequence[ToolSchemaAdapter] = (),
        call_adapters: Sequence[ToolCallAdapter] = (),
        schema_accessors: Sequence[ToolSchemaAccessor] = (),
        call_accessors: Sequence[ToolCallAccessor] = (),
    ) -> None:
        self._schema_adapters = list(schema_adapters)
        self._call_adapters = list(call_adapters)
        self._schema_accessors = list(schema_accessors)
        self._call_accessors = list(call_accessors)

    def get_schema_accessor(self, schema: JsonObject) -> ToolSchemaAccessor:
        for accessor in self._schema_accessors:
            if accessor.can_handle(schema):
                return accessor
        raise ToolInteropError(f"No schema accessor matched: keys={list(schema.keys())}")

    def get_call_accessor(self, call: JsonObject) -> ToolCallAccessor:
        for accessor in self._call_accessors:
            if accessor.can_handle(call):
                return accessor
        raise ToolInteropError(f"No call accessor matched: keys={list(call.keys())}")

    def convert_schemas(
        self,
        schemas: List[JsonObject],
        *,
        adapters: Sequence[ToolSchemaAdapter],
        target: ToolInteropTarget,
    ) -> List[JsonObject]:
        converted: List[JsonObject] = []
        for schema in schemas:
            adapter = next((a for a in adapters if a.can_handle(schema)), None)
            if adapter is None:
                raise ToolInteropError(
                    f"No schema adapter matched (target={target.name}): keys={list(schema.keys())}"
                )
            converted.append(adapter.convert(schema, target=target))
        return converted

    def convert_tool_calls(
        self,
        calls: List[JsonObject],
        *,
        adapters: Sequence[ToolCallAdapter],
        target: ToolInteropTarget,
    ) -> List[JsonObject]:
        converted: List[JsonObject] = []
        for call in calls:
            adapter = next((a for a in adapters if a.can_handle(call)), None)
            if adapter is None:
                raise ToolInteropError(
                    f"No call adapter matched (target={target.name}): keys={list(call.keys())}"
                )
            converted.append(adapter.convert(call, target=target))
        return converted


# ---------------------------------------------------------------------------
# Strict accessors: canonical internal (OpenAI chat-completions style)
# ---------------------------------------------------------------------------


class OpenAIChatToolSchemaAccessor:
    format = "openai.chat_completions.tool_schema"

    def can_handle(self, schema: Any) -> bool:
        if not isinstance(schema, dict):
            return False
        if schema.get("type") != "function":
            return False
        fn = schema.get("function")
        if not isinstance(fn, dict):
            return False
        name = fn.get("name")
        return isinstance(name, str) and bool(name.strip())

    def get_tool_type(self, schema: JsonObject) -> str:
        tool_type = schema.get("type")
        if tool_type != "function":
            raise ToolInteropError(f"Unsupported tool schema type: {tool_type!r}")
        return "function"

    def get_tool_name(self, schema: JsonObject) -> str:
        fn = schema.get("function")
        if not isinstance(fn, dict):
            raise ToolInteropError("Tool schema missing 'function' object")
        name = fn.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ToolInteropError("Tool schema missing 'function.name'")
        return name

    def get_description(self, schema: JsonObject) -> Optional[str]:
        fn = schema.get("function")
        if not isinstance(fn, dict):
            raise ToolInteropError("Tool schema missing 'function' object")
        desc = fn.get("description")
        return desc if isinstance(desc, str) else None

    def get_parameters_schema(self, schema: JsonObject) -> Optional[JsonObject]:
        fn = schema.get("function")
        if not isinstance(fn, dict):
            raise ToolInteropError("Tool schema missing 'function' object")
        params = fn.get("parameters")
        return params if isinstance(params, dict) else None


class OpenAIChatToolCallAccessor:
    format = "openai.chat_completions.tool_call"

    def can_handle(self, call: Any) -> bool:
        if not isinstance(call, dict):
            return False
        if call.get("type") != "function":
            return False
        call_id = call.get("id")
        if not isinstance(call_id, str) or not call_id.strip():
            return False
        fn = call.get("function")
        if not isinstance(fn, dict):
            return False
        name = fn.get("name")
        return isinstance(name, str) and bool(name.strip())

    def get_call_id(self, call: JsonObject) -> str:
        call_id = call.get("id")
        if not isinstance(call_id, str) or not call_id.strip():
            raise ToolInteropError("Tool call missing 'id'")
        return call_id

    def get_tool_type(self, call: JsonObject) -> str:
        tool_type = call.get("type")
        if tool_type != "function":
            raise ToolInteropError(f"Unsupported tool call type: {tool_type!r}")
        return "function"

    def get_tool_name(self, call: JsonObject) -> str:
        fn = call.get("function")
        if not isinstance(fn, dict):
            raise ToolInteropError("Tool call missing 'function' object")
        name = fn.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ToolInteropError("Tool call missing 'function.name'")
        return name

    def get_arguments(self, call: JsonObject) -> Any:
        fn = call.get("function")
        if not isinstance(fn, dict):
            raise ToolInteropError("Tool call missing 'function' object")
        # Arguments may be a JSON string (OpenAI-native) or a parsed dict (tests/tools).
        return fn.get("arguments", {})


# ---------------------------------------------------------------------------
# Adapters for OpenAI Responses API interop
# ---------------------------------------------------------------------------


class OpenAIChatToolSchemaToOpenAIResponsesToolSchema:
    source_format = "openai.chat_completions.tool_schema"
    target_format = "openai.responses.tool_schema"

    _schema_accessor = OpenAIChatToolSchemaAccessor()

    def can_handle(self, schema: Any) -> bool:
        return self._schema_accessor.can_handle(schema)

    def convert(self, schema: JsonObject, *, target: ToolInteropTarget) -> JsonObject:
        name = self._schema_accessor.get_tool_name(schema)
        out: JsonObject = {"type": "function", "name": name}

        desc = self._schema_accessor.get_description(schema)
        if desc is not None:
            out["description"] = desc
        params = self._schema_accessor.get_parameters_schema(schema)
        if params is not None:
            out["parameters"] = params
        return out


class OpenAIResponsesFunctionCallAccessor:
    """Accessor for OpenAI Responses output items of type function_call."""

    format = "openai.responses.function_call"

    def can_handle(self, call: Any) -> bool:
        if not isinstance(call, dict):
            return False
        if call.get("type") != "function_call":
            return False
        call_id = call.get("call_id")
        if not isinstance(call_id, str) or not call_id.strip():
            return False
        name = call.get("name")
        return isinstance(name, str) and bool(name.strip())

    def get_call_id(self, call: JsonObject) -> str:
        call_id = call.get("call_id")
        if not isinstance(call_id, str) or not call_id.strip():
            raise ToolInteropError("Responses function_call missing 'call_id'")
        return call_id

    def get_tool_type(self, call: JsonObject) -> str:
        tool_type = call.get("type")
        if tool_type != "function_call":
            raise ToolInteropError(f"Unsupported responses call type: {tool_type!r}")
        return "function_call"

    def get_tool_name(self, call: JsonObject) -> str:
        name = call.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ToolInteropError("Responses function_call missing 'name'")
        return name

    def get_arguments(self, call: JsonObject) -> Any:
        return call.get("arguments", "{}")


class OpenAIResponsesToolCallToOpenAIChatToolCall:
    source_format = "openai.responses.function_call"
    target_format = "openai.chat_completions.tool_call"

    _call_accessor = OpenAIResponsesFunctionCallAccessor()

    def can_handle(self, call: Any) -> bool:
        # Accept either a raw function_call item or an event wrapper with `item`.
        if self._call_accessor.can_handle(call):
            return True
        if isinstance(call, dict) and self._call_accessor.can_handle(call.get("item")):
            return True
        return False

    def convert(self, call: JsonObject, *, target: ToolInteropTarget) -> JsonObject:
        item = call
        if not self._call_accessor.can_handle(item):
            maybe_item = call.get("item")
            if isinstance(maybe_item, dict) and self._call_accessor.can_handle(maybe_item):
                item = maybe_item
            else:
                raise ToolInteropError("Unsupported Responses tool call object")

        call_id = self._call_accessor.get_call_id(item)
        name = self._call_accessor.get_tool_name(item)
        arguments = self._call_accessor.get_arguments(item)
        return {
            "id": call_id,
            "type": "function",
            "function": {
                "name": name,
                "arguments": arguments,
            },
        }


DEFAULT_TOOL_INTEROP_REGISTRY = ToolInteropRegistry(
    schema_adapters=[OpenAIChatToolSchemaToOpenAIResponsesToolSchema()],
    call_adapters=[OpenAIResponsesToolCallToOpenAIChatToolCall()],
    schema_accessors=[OpenAIChatToolSchemaAccessor()],
    call_accessors=[OpenAIChatToolCallAccessor(), OpenAIResponsesFunctionCallAccessor()],
)
