from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple


class ToolInteropError(ValueError):
    pass


JsonObject = Dict[str, Any]

TOOL_INTEROP_REGISTRY_CONFIG_KEY = "_tool_interop_registry"
TOOL_SCHEMA_TARGET_FORMATS_CONFIG_KEY = "_tool_schema_target_formats"


@dataclass(frozen=True)
class ToolInteropTarget:
    """Identifies a wire format target."""

    name: str


@dataclass(frozen=True)
class ToolInteropContribution:
    schema_accessors: Tuple["ToolSchemaAccessor", ...] = ()
    call_accessors: Tuple["ToolCallAccessor", ...] = ()
    schema_adapters: Tuple["ToolSchemaAdapter", ...] = ()
    call_adapters: Tuple["ToolCallAdapter", ...] = ()


@dataclass(frozen=True)
class InspectedToolSchema:
    raw: JsonObject
    accessor: "ToolSchemaAccessor"
    format_id: Optional[str]
    tool_type: Optional[str]
    tool_name: Optional[str]
    tool_kind: Optional[str]
    description: Optional[str]
    parameters_schema: Optional[JsonObject]


@dataclass(frozen=True)
class InspectedToolCall:
    raw: JsonObject
    accessor: "ToolCallAccessor"
    format_id: Optional[str]
    call_id: Optional[str]
    tool_type: Optional[str]
    tool_name: Optional[str]
    payload: Any
    payload_kind: Optional[str]
    payload_format: Optional[str]
    payload_metadata: Dict[str, Any]


class ToolSchemaAdapter(Protocol):
    source_format: str
    target_format: str
    priority: int

    def can_handle(self, schema: Any) -> bool:
        ...

    def convert(self, schema: JsonObject, *, target: ToolInteropTarget) -> JsonObject:
        ...


class ToolCallAdapter(Protocol):
    source_format: str
    target_format: str
    priority: int

    def can_handle(self, call: Any) -> bool:
        ...

    def convert(self, call: JsonObject, *, target: ToolInteropTarget) -> JsonObject:
        ...


class ToolSchemaAccessor(Protocol):
    format: str
    format_id: str
    priority: int

    def can_handle(self, schema: Any) -> bool:
        ...

    def get_tool_type(self, schema: JsonObject) -> str:
        ...

    def get_tool_name(self, schema: JsonObject) -> Optional[str]:
        ...

    def get_description(self, schema: JsonObject) -> Optional[str]:
        ...

    def get_parameters_schema(self, schema: JsonObject) -> Optional[JsonObject]:
        ...

    def get_tool_kind(self, schema: JsonObject) -> Optional[str]:
        ...

    def get_schema_format(self, schema: JsonObject) -> Optional[str]:
        ...


class ToolCallAccessor(Protocol):
    format: str
    format_id: str
    priority: int

    def can_handle(self, call: Any) -> bool:
        ...

    def get_call_id(self, call: JsonObject) -> Optional[str]:
        ...

    def get_tool_type(self, call: JsonObject) -> str:
        ...

    def get_tool_name(self, call: JsonObject) -> Optional[str]:
        ...

    def get_arguments(self, call: JsonObject) -> Any:
        ...

    def get_payload(self, call: JsonObject) -> Any:
        ...

    def get_payload_kind(self, call: JsonObject) -> Optional[str]:
        ...

    def get_payload_format(self, call: JsonObject) -> Optional[str]:
        ...

    def get_payload_metadata(self, call: JsonObject) -> Optional[JsonObject]:
        ...


def _priority(value: Any) -> int:
    raw = getattr(value, "priority", 100)
    return raw if isinstance(raw, int) else 100


def _format_id(value: Any) -> Optional[str]:
    raw = getattr(value, "format_id", None)
    if isinstance(raw, str) and raw:
        return raw
    raw = getattr(value, "format", None)
    return raw if isinstance(raw, str) and raw else None


def _safe_call(value: Any, name: str, *args: Any) -> Any:
    fn = getattr(value, name, None)
    if callable(fn):
        return fn(*args)
    return None


def _sorted_items(values: Sequence[Any]) -> List[Any]:
    return sorted(list(values), key=_priority)


def _merge_ordered(*groups: Sequence[Any]) -> List[Any]:
    merged: List[Any] = []
    for group in groups:
        merged.extend(_sorted_items(group))
    return merged


def get_registry_from_config(config: Dict[str, Any]) -> "ToolInteropRegistry":
    registry = config.get(TOOL_INTEROP_REGISTRY_CONFIG_KEY)
    if isinstance(registry, ToolInteropRegistry):
        return registry
    return DEFAULT_TOOL_INTEROP_REGISTRY


def get_schema_target_formats_from_config(config: Dict[str, Any]) -> List[str]:
    raw = config.get(TOOL_SCHEMA_TARGET_FORMATS_CONFIG_KEY)
    if isinstance(raw, list):
        return [value for value in raw if isinstance(value, str) and value]
    return []


def compose_tool_interop_registry(
    *,
    explicit: Sequence[ToolInteropContribution] = (),
    contributed: Sequence[ToolInteropContribution] = (),
    defaults: Optional["ToolInteropRegistry"] = None,
) -> "ToolInteropRegistry":
    default_registry = defaults or DEFAULT_TOOL_INTEROP_REGISTRY
    return ToolInteropRegistry(
        schema_adapters=_merge_ordered(
            *(c.schema_adapters for c in explicit),
            *(c.schema_adapters for c in contributed),
            default_registry._schema_adapters,
        ),
        call_adapters=_merge_ordered(
            *(c.call_adapters for c in explicit),
            *(c.call_adapters for c in contributed),
            default_registry._call_adapters,
        ),
        schema_accessors=_merge_ordered(
            *(c.schema_accessors for c in explicit),
            *(c.schema_accessors for c in contributed),
            default_registry._schema_accessors,
        ),
        call_accessors=_merge_ordered(
            *(c.call_accessors for c in explicit),
            *(c.call_accessors for c in contributed),
            default_registry._call_accessors,
        ),
    )


class _IdentitySchemaAdapter:
    priority = 0

    def __init__(self, format_id: str) -> None:
        self.source_format = format_id
        self.target_format = format_id

    def can_handle(self, schema: Any) -> bool:
        return isinstance(schema, dict)

    def convert(self, schema: JsonObject, *, target: ToolInteropTarget) -> JsonObject:
        return dict(schema)


class _IdentityCallAdapter:
    priority = 0

    def __init__(self, format_id: str) -> None:
        self.source_format = format_id
        self.target_format = format_id

    def can_handle(self, call: Any) -> bool:
        return isinstance(call, dict)

    def convert(self, call: JsonObject, *, target: ToolInteropTarget) -> JsonObject:
        return dict(call)


class _ComposedSchemaAdapter:
    priority = 0

    def __init__(self, chain: Sequence[ToolSchemaAdapter]) -> None:
        if not chain:
            raise ToolInteropError("Composed schema adapter requires at least one step")
        self._chain = list(chain)
        self.source_format = self._chain[0].source_format
        self.target_format = self._chain[-1].target_format

    def can_handle(self, schema: Any) -> bool:
        return self._chain[0].can_handle(schema)

    def convert(self, schema: JsonObject, *, target: ToolInteropTarget) -> JsonObject:
        current = dict(schema)
        for adapter in self._chain:
            current = adapter.convert(current, target=target)
        return current


class _ComposedCallAdapter:
    priority = 0

    def __init__(self, chain: Sequence[ToolCallAdapter]) -> None:
        if not chain:
            raise ToolInteropError("Composed call adapter requires at least one step")
        self._chain = list(chain)
        self.source_format = self._chain[0].source_format
        self.target_format = self._chain[-1].target_format

    def can_handle(self, call: Any) -> bool:
        return self._chain[0].can_handle(call)

    def convert(self, call: JsonObject, *, target: ToolInteropTarget) -> JsonObject:
        current = dict(call)
        for adapter in self._chain:
            current = adapter.convert(current, target=target)
        return current


class ToolInteropRegistry:
    def __init__(
        self,
        *,
        schema_adapters: Sequence[ToolSchemaAdapter] = (),
        call_adapters: Sequence[ToolCallAdapter] = (),
        schema_accessors: Sequence[ToolSchemaAccessor] = (),
        call_accessors: Sequence[ToolCallAccessor] = (),
    ) -> None:
        self._schema_adapters = _sorted_items(schema_adapters)
        self._call_adapters = _sorted_items(call_adapters)
        self._schema_accessors = _sorted_items(schema_accessors)
        self._call_accessors = _sorted_items(call_accessors)

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

    def inspect_schema(self, schema: JsonObject) -> InspectedToolSchema:
        accessor = self.get_schema_accessor(schema)
        return InspectedToolSchema(
            raw=schema,
            accessor=accessor,
            format_id=_format_id(accessor),
            tool_type=_safe_call(accessor, "get_tool_type", schema),
            tool_name=_safe_call(accessor, "get_tool_name", schema),
            tool_kind=_safe_call(accessor, "get_tool_kind", schema)
            or _safe_call(accessor, "get_tool_type", schema),
            description=_safe_call(accessor, "get_description", schema),
            parameters_schema=_safe_call(accessor, "get_parameters_schema", schema),
        )

    def inspect_call(self, call: JsonObject) -> InspectedToolCall:
        accessor = self.get_call_accessor(call)
        payload = self._get_call_payload(accessor, call)
        metadata = _safe_call(accessor, "get_payload_metadata", call)
        payload_metadata = metadata if isinstance(metadata, dict) else {}
        return InspectedToolCall(
            raw=call,
            accessor=accessor,
            format_id=_format_id(accessor),
            call_id=_safe_call(accessor, "get_call_id", call),
            tool_type=_safe_call(accessor, "get_tool_type", call),
            tool_name=_safe_call(accessor, "get_tool_name", call),
            payload=payload,
            payload_kind=_safe_call(accessor, "get_payload_kind", call)
            or self._infer_payload_kind(payload),
            payload_format=_safe_call(accessor, "get_payload_format", call),
            payload_metadata=payload_metadata,
        )

    def _infer_payload_kind(self, payload: Any) -> str:
        if payload is None:
            return "none"
        if isinstance(payload, dict):
            return "object"
        if isinstance(payload, list):
            return "array"
        if isinstance(payload, str):
            return "text"
        return type(payload).__name__

    def _get_call_payload(self, accessor: ToolCallAccessor, call: JsonObject) -> Any:
        payload = _safe_call(accessor, "get_payload", call)
        if payload is not None:
            return payload
        payload = _safe_call(accessor, "get_arguments", call)
        if isinstance(payload, str):
            try:
                return json.loads(payload)
            except Exception:
                return payload
        if payload is None:
            return {}
        return payload

    def _match_schema_format(self, schema: JsonObject) -> Optional[str]:
        try:
            return self.inspect_schema(schema).format_id
        except ToolInteropError:
            for adapter in self._schema_adapters:
                if adapter.can_handle(schema):
                    return adapter.source_format
        return None

    def _match_call_format(self, call: JsonObject) -> Optional[str]:
        try:
            return self.inspect_call(call).format_id
        except ToolInteropError:
            for adapter in self._call_adapters:
                if adapter.can_handle(call):
                    return adapter.source_format
        return None

    def _resolve_schema_adapter(
        self,
        schema: JsonObject,
        *,
        adapters: Sequence[ToolSchemaAdapter],
        target_formats: Sequence[str],
    ) -> ToolSchemaAdapter:
        source_format = self._match_schema_format(schema)
        if source_format is None:
            raise ToolInteropError(f"Could not determine schema format: keys={list(schema.keys())}")
        if target_formats and source_format in target_formats:
            return _IdentitySchemaAdapter(source_format)

        direct = [
            adapter
            for adapter in adapters
            if adapter.source_format == source_format
            and adapter.can_handle(schema)
            and (not target_formats or adapter.target_format in target_formats)
        ]
        if direct:
            return direct[0]

        chain = self._find_schema_adapter_chain(
            source_format=source_format,
            target_formats=target_formats,
            adapters=adapters,
        )
        if chain is not None:
            return _ComposedSchemaAdapter(chain)

        raise ToolInteropError(
            f"No schema adapter matched source={source_format!r} targets={list(target_formats)!r}"
        )

    def _resolve_call_adapter(
        self,
        call: JsonObject,
        *,
        adapters: Sequence[ToolCallAdapter],
        target_formats: Sequence[str],
    ) -> ToolCallAdapter:
        source_format = self._match_call_format(call)
        if source_format is None:
            raise ToolInteropError(f"Could not determine call format: keys={list(call.keys())}")
        if target_formats and source_format in target_formats:
            return _IdentityCallAdapter(source_format)

        direct = [
            adapter
            for adapter in adapters
            if adapter.source_format == source_format
            and adapter.can_handle(call)
            and (not target_formats or adapter.target_format in target_formats)
        ]
        if direct:
            return direct[0]

        chain = self._find_call_adapter_chain(
            source_format=source_format,
            target_formats=target_formats,
            adapters=adapters,
        )
        if chain is not None:
            return _ComposedCallAdapter(chain)

        raise ToolInteropError(
            f"No call adapter matched source={source_format!r} targets={list(target_formats)!r}"
        )

    def _find_schema_adapter_chain(
        self,
        *,
        source_format: str,
        target_formats: Sequence[str],
        adapters: Sequence[ToolSchemaAdapter],
    ) -> Optional[List[ToolSchemaAdapter]]:
        if not target_formats:
            return None
        queue: List[Tuple[str, List[ToolSchemaAdapter]]] = [(source_format, [])]
        seen = {source_format}
        while queue:
            current, chain = queue.pop(0)
            for adapter in adapters:
                if adapter.source_format != current:
                    continue
                next_chain = [*chain, adapter]
                if adapter.target_format in target_formats:
                    return next_chain
                if adapter.target_format in seen:
                    continue
                seen.add(adapter.target_format)
                queue.append((adapter.target_format, next_chain))
        return None

    def _find_call_adapter_chain(
        self,
        *,
        source_format: str,
        target_formats: Sequence[str],
        adapters: Sequence[ToolCallAdapter],
    ) -> Optional[List[ToolCallAdapter]]:
        if not target_formats:
            return None
        queue: List[Tuple[str, List[ToolCallAdapter]]] = [(source_format, [])]
        seen = {source_format}
        while queue:
            current, chain = queue.pop(0)
            for adapter in adapters:
                if adapter.source_format != current:
                    continue
                next_chain = [*chain, adapter]
                if adapter.target_format in target_formats:
                    return next_chain
                if adapter.target_format in seen:
                    continue
                seen.add(adapter.target_format)
                queue.append((adapter.target_format, next_chain))
        return None

    def convert_schemas(
        self,
        schemas: List[JsonObject],
        *,
        adapters: Sequence[ToolSchemaAdapter] = (),
        target: Optional[ToolInteropTarget] = None,
        target_formats: Sequence[str] = (),
    ) -> List[JsonObject]:
        effective_adapters = _merge_ordered(adapters, self._schema_adapters)
        requested_formats = list(target_formats)
        converted: List[JsonObject] = []
        for schema in schemas:
            adapter = self._resolve_schema_adapter(
                schema,
                adapters=effective_adapters,
                target_formats=requested_formats,
            )
            converted.append(adapter.convert(schema, target=target or ToolInteropTarget("tool_interop")))
        return converted

    def convert_tool_calls(
        self,
        calls: List[JsonObject],
        *,
        adapters: Sequence[ToolCallAdapter] = (),
        target: Optional[ToolInteropTarget] = None,
        target_formats: Sequence[str] = (),
    ) -> List[JsonObject]:
        effective_adapters = _merge_ordered(adapters, self._call_adapters)
        requested_formats = list(target_formats)
        converted: List[JsonObject] = []
        for call in calls:
            adapter = self._resolve_call_adapter(
                call,
                adapters=effective_adapters,
                target_formats=requested_formats,
            )
            converted.append(adapter.convert(call, target=target or ToolInteropTarget("tool_interop")))
        return converted


# ---------------------------------------------------------------------------
# Strict accessors: canonical OpenAI chat-completions function tools
# ---------------------------------------------------------------------------


class OpenAIChatToolSchemaAccessor:
    format_id = "openai.chat_completions.function.tool_schema"
    format = format_id
    priority = 100

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

    def get_tool_kind(self, schema: JsonObject) -> str:
        return "function"

    def get_schema_format(self, schema: JsonObject) -> str:
        return self.format_id


class OpenAIResponsesFunctionToolSchemaAccessor:
    format_id = "openai.responses.function.tool_schema"
    format = format_id
    priority = 100

    def can_handle(self, schema: Any) -> bool:
        if not isinstance(schema, dict):
            return False
        if schema.get("type") != "function":
            return False
        name = schema.get("name")
        return isinstance(name, str) and bool(name.strip())

    def get_tool_type(self, schema: JsonObject) -> str:
        if schema.get("type") != "function":
            raise ToolInteropError("Responses function schema missing type='function'")
        return "function"

    def get_tool_name(self, schema: JsonObject) -> str:
        name = schema.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ToolInteropError("Responses function schema missing 'name'")
        return name

    def get_description(self, schema: JsonObject) -> Optional[str]:
        desc = schema.get("description")
        return desc if isinstance(desc, str) else None

    def get_parameters_schema(self, schema: JsonObject) -> Optional[JsonObject]:
        params = schema.get("parameters")
        return params if isinstance(params, dict) else None

    def get_tool_kind(self, schema: JsonObject) -> str:
        return "function"

    def get_schema_format(self, schema: JsonObject) -> str:
        return self.format_id


class OpenAIResponsesCustomToolSchemaAccessor:
    format_id = "openai.responses.custom.tool_schema"
    format = format_id
    priority = 100

    def can_handle(self, schema: Any) -> bool:
        if not isinstance(schema, dict):
            return False
        if schema.get("type") != "custom":
            return False
        name = schema.get("name")
        return isinstance(name, str) and bool(name.strip())

    def get_tool_type(self, schema: JsonObject) -> str:
        if schema.get("type") != "custom":
            raise ToolInteropError("Responses custom schema missing type='custom'")
        return "custom"

    def get_tool_name(self, schema: JsonObject) -> str:
        name = schema.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ToolInteropError("Responses custom schema missing 'name'")
        return name

    def get_description(self, schema: JsonObject) -> Optional[str]:
        desc = schema.get("description")
        return desc if isinstance(desc, str) else None

    def get_parameters_schema(self, schema: JsonObject) -> Optional[JsonObject]:
        return None

    def get_tool_kind(self, schema: JsonObject) -> str:
        return "custom"

    def get_schema_format(self, schema: JsonObject) -> str:
        return self.format_id


class OpenAIChatToolCallAccessor:
    format_id = "openai.chat_completions.function.tool_call"
    format = format_id
    priority = 100

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
        return fn.get("arguments", {})

    def get_payload(self, call: JsonObject) -> Any:
        arguments = self.get_arguments(call)
        if isinstance(arguments, str):
            try:
                parsed = json.loads(arguments)
                return parsed if isinstance(parsed, dict) else {}
            except Exception:
                return {}
        return arguments if isinstance(arguments, dict) else {}

    def get_payload_kind(self, call: JsonObject) -> str:
        return "object"

    def get_payload_format(self, call: JsonObject) -> Optional[str]:
        return None

    def get_payload_metadata(self, call: JsonObject) -> JsonObject:
        return {}


class OpenAIResponsesFunctionCallAccessor:
    """Accessor for OpenAI Responses output items of type function_call."""

    format_id = "openai.responses.function.tool_call"
    format = format_id
    priority = 100

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

    def get_payload(self, call: JsonObject) -> Any:
        arguments = self.get_arguments(call)
        if isinstance(arguments, str):
            try:
                parsed = json.loads(arguments)
                return parsed if isinstance(parsed, dict) else {}
            except Exception:
                return {}
        return arguments if isinstance(arguments, dict) else {}

    def get_payload_kind(self, call: JsonObject) -> str:
        return "object"

    def get_payload_format(self, call: JsonObject) -> Optional[str]:
        return None

    def get_payload_metadata(self, call: JsonObject) -> JsonObject:
        metadata = call.get("_metadata")
        return dict(metadata) if isinstance(metadata, dict) else {}


class OpenAIResponsesCustomToolCallAccessor:
    format_id = "openai.responses.custom.tool_call"
    format = format_id
    priority = 100

    def can_handle(self, call: Any) -> bool:
        if not isinstance(call, dict):
            return False
        if call.get("type") != "custom_tool_call":
            return False
        call_id = call.get("call_id")
        if not isinstance(call_id, str) or not call_id.strip():
            return False
        name = call.get("name")
        return isinstance(name, str) and bool(name.strip())

    def get_call_id(self, call: JsonObject) -> str:
        call_id = call.get("call_id")
        if not isinstance(call_id, str) or not call_id.strip():
            raise ToolInteropError("Responses custom_tool_call missing 'call_id'")
        return call_id

    def get_tool_type(self, call: JsonObject) -> str:
        tool_type = call.get("type")
        if tool_type != "custom_tool_call":
            raise ToolInteropError(f"Unsupported responses call type: {tool_type!r}")
        return "custom_tool_call"

    def get_tool_name(self, call: JsonObject) -> str:
        name = call.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ToolInteropError("Responses custom_tool_call missing 'name'")
        return name

    def get_arguments(self, call: JsonObject) -> Any:
        return call.get("input", "")

    def get_payload(self, call: JsonObject) -> Any:
        raw = call.get("input", "")
        return raw if isinstance(raw, str) else ""

    def get_payload_kind(self, call: JsonObject) -> str:
        return "text"

    def get_payload_format(self, call: JsonObject) -> Optional[str]:
        raw = call.get("input_format")
        return raw if isinstance(raw, str) and raw else None

    def get_payload_metadata(self, call: JsonObject) -> JsonObject:
        metadata = call.get("_metadata")
        return dict(metadata) if isinstance(metadata, dict) else {}


# ---------------------------------------------------------------------------
# Adapters for OpenAI Responses API interop
# ---------------------------------------------------------------------------


class OpenAIChatToolSchemaToOpenAIResponsesToolSchema:
    source_format = OpenAIChatToolSchemaAccessor.format_id
    target_format = OpenAIResponsesFunctionToolSchemaAccessor.format_id
    priority = 100

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


class OpenAIResponsesToolCallToOpenAIChatToolCall:
    source_format = OpenAIResponsesFunctionCallAccessor.format_id
    target_format = OpenAIChatToolCallAccessor.format_id
    priority = 100

    _call_accessor = OpenAIResponsesFunctionCallAccessor()

    def can_handle(self, call: Any) -> bool:
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
    schema_accessors=[
        OpenAIChatToolSchemaAccessor(),
        OpenAIResponsesFunctionToolSchemaAccessor(),
        OpenAIResponsesCustomToolSchemaAccessor(),
    ],
    call_accessors=[
        OpenAIChatToolCallAccessor(),
        OpenAIResponsesFunctionCallAccessor(),
        OpenAIResponsesCustomToolCallAccessor(),
    ],
)