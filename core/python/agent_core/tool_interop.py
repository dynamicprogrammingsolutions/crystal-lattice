from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple


class ToolInteropError(ValueError):
    pass


JsonObject = Dict[str, Any]

TOOL_SCHEMA_TARGET_FORMATS_CONFIG_KEY = "_tool_schema_target_formats"
TOOL_INTEROP_CONTEXT_KEY = "tool_interop"
TOOL_INTEROP_REGISTRY_CONTEXT_KEY = "registry"
TOOL_SCHEMA_TARGET_FORMATS_CONTEXT_KEY = "schema_target_formats"
CORE_TOOL_RESULT_TYPE = "tool_result"
PROVIDER_NATIVE_TOOL_RESULT_TYPE = "provider_native_tool_result"
CORE_TEXT_TOOL_RESULT_FORMAT_ID = "core.tool_result.text"
CORE_TEXT_TOOL_RESULT_PLAIN_FORMAT_ID = "core.tool_result.plain_text"
PROVIDER_NATIVE_TOOL_RESULT_FORMAT_ID = "provider_native.tool_result"
OPENAI_CHAT_TOOL_RESULT_FORMAT_ID = "openai.chat_completions.tool_result"
OPENAI_RESPONSES_TOOL_RESULT_FORMAT_ID = "openai.responses.tool_result"
ANTHROPIC_MESSAGES_TOOL_RESULT_FORMAT_ID = "anthropic.messages.tool_result"
OPENAI_CHAT_TOOL_RESULT_FORMAT = "openai.chat_completions"
OPENAI_RESPONSES_TOOL_RESULT_FORMAT = "openai.responses"
ANTHROPIC_MESSAGES_TOOL_RESULT_FORMAT = "anthropic.messages"
SESSION_ASSET_DOWNLOAD_PLUGIN_ID = "session_asset_attachments"


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
    result_accessors: Tuple["ToolResultAccessor", ...] = ()
    result_adapters: Tuple["ToolResultAdapter", ...] = ()


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


@dataclass(frozen=True)
class InspectedToolResult:
    raw: Any
    accessor: "ToolResultAccessor"
    format_id: Optional[str]
    result_type: Optional[str]
    payload: Any
    payload_kind: Optional[str]
    text: str
    display: Optional[JsonObject]
    metadata: Dict[str, Any]


class ToolSchemaAdapter(Protocol):
    source_format: str
    target_format: str
    priority: int

    def can_handle(self, schema: Any) -> bool: ...

    def convert(
        self, schema: JsonObject, *, target: ToolInteropTarget
    ) -> JsonObject: ...


class ToolCallAdapter(Protocol):
    source_format: str
    target_format: str
    priority: int

    def can_handle(self, call: Any) -> bool: ...

    def convert(self, call: JsonObject, *, target: ToolInteropTarget) -> JsonObject: ...


class ToolResultAdapter(Protocol):
    source_format: str
    target_format: str
    priority: int

    def can_handle(self, result: Any) -> bool: ...

    def convert(self, result: Any, *, target: ToolInteropTarget) -> Any: ...


class ToolSchemaAccessor(Protocol):
    format: str
    format_id: str
    priority: int

    def can_handle(self, schema: Any) -> bool: ...

    def get_tool_type(self, schema: JsonObject) -> str: ...

    def get_tool_name(self, schema: JsonObject) -> Optional[str]: ...

    def get_description(self, schema: JsonObject) -> Optional[str]: ...

    def get_parameters_schema(self, schema: JsonObject) -> Optional[JsonObject]: ...

    def get_tool_kind(self, schema: JsonObject) -> Optional[str]: ...

    def get_schema_format(self, schema: JsonObject) -> Optional[str]: ...


class ToolCallAccessor(Protocol):
    format: str
    format_id: str
    priority: int

    def can_handle(self, call: Any) -> bool: ...

    def get_call_id(self, call: JsonObject) -> Optional[str]: ...

    def get_tool_type(self, call: JsonObject) -> str: ...

    def get_tool_name(self, call: JsonObject) -> Optional[str]: ...

    def get_payload(self, call: JsonObject) -> Any: ...

    def get_payload_kind(self, call: JsonObject) -> Optional[str]: ...

    def get_payload_format(self, call: JsonObject) -> Optional[str]: ...

    def get_payload_metadata(self, call: JsonObject) -> Optional[JsonObject]: ...

    def sanitize_call(self, call: JsonObject) -> JsonObject:
        """Return a sanitized copy of the call with valid arguments.

        Used before storing in history to ensure subsequent API calls
        don't fail due to corrupted JSON. Returns the call unchanged
        if no sanitization is needed for this format.

        Implementations should return a new dict, not mutate the input.
        """
        ...


class ToolResultAccessor(Protocol):
    format: str
    format_id: str
    priority: int

    def can_handle(self, result: Any) -> bool: ...

    def get_result_type(self, result: Any) -> Optional[str]: ...

    def get_payload(self, result: Any) -> Any: ...

    def get_payload_kind(self, result: Any) -> Optional[str]: ...

    def get_text(self, result: Any) -> str: ...

    def get_display(self, result: Any) -> Optional[JsonObject]: ...

    def get_metadata(self, result: Any) -> Optional[JsonObject]: ...


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


def get_schema_target_formats_from_config(config: Dict[str, Any]) -> List[str]:
    raw = config.get(TOOL_SCHEMA_TARGET_FORMATS_CONFIG_KEY)
    if isinstance(raw, list):
        return [value for value in raw if isinstance(value, str) and value]
    return []


def get_registry_from_context(
    context: Optional[Dict[str, Any]],
) -> "ToolInteropRegistry":
    if isinstance(context, dict):
        tool_interop = context.get(TOOL_INTEROP_CONTEXT_KEY)
        if isinstance(tool_interop, dict):
            registry = tool_interop.get(TOOL_INTEROP_REGISTRY_CONTEXT_KEY)
            if isinstance(registry, ToolInteropRegistry):
                return registry
    return DEFAULT_TOOL_INTEROP_REGISTRY


def get_schema_target_formats_from_context(
    context: Optional[Dict[str, Any]],
) -> List[str]:
    if isinstance(context, dict):
        tool_interop = context.get(TOOL_INTEROP_CONTEXT_KEY)
        if isinstance(tool_interop, dict):
            raw = tool_interop.get(TOOL_SCHEMA_TARGET_FORMATS_CONTEXT_KEY)
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
        result_adapters=_merge_ordered(
            *(c.result_adapters for c in explicit),
            *(c.result_adapters for c in contributed),
            default_registry._result_adapters,
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
        result_accessors=_merge_ordered(
            *(c.result_accessors for c in explicit),
            *(c.result_accessors for c in contributed),
            default_registry._result_accessors,
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


class _IdentityResultAdapter:
    priority = 0

    def __init__(self, format_id: str) -> None:
        self.source_format = format_id
        self.target_format = format_id

    def can_handle(self, result: Any) -> bool:
        return True

    def convert(self, result: Any, *, target: ToolInteropTarget) -> Any:
        return result


class _ComposedResultAdapter:
    priority = 0

    def __init__(self, chain: Sequence[ToolResultAdapter]) -> None:
        if not chain:
            raise ToolInteropError("Composed result adapter requires at least one step")
        self._chain = list(chain)
        self.source_format = self._chain[0].source_format
        self.target_format = self._chain[-1].target_format

    def can_handle(self, result: Any) -> bool:
        return self._chain[0].can_handle(result)

    def convert(self, result: Any, *, target: ToolInteropTarget) -> Any:
        current = result
        for adapter in self._chain:
            current = adapter.convert(current, target=target)
        return current


class ToolInteropRegistry:
    def __init__(
        self,
        *,
        schema_adapters: Sequence[ToolSchemaAdapter] = (),
        call_adapters: Sequence[ToolCallAdapter] = (),
        result_adapters: Sequence[ToolResultAdapter] = (),
        schema_accessors: Sequence[ToolSchemaAccessor] = (),
        call_accessors: Sequence[ToolCallAccessor] = (),
        result_accessors: Sequence[ToolResultAccessor] = (),
    ) -> None:
        self._schema_adapters = _sorted_items(schema_adapters)
        self._call_adapters = _sorted_items(call_adapters)
        self._result_adapters = _sorted_items(result_adapters)
        self._schema_accessors = _sorted_items(schema_accessors)
        self._call_accessors = _sorted_items(call_accessors)
        self._result_accessors = _sorted_items(result_accessors)

    def get_schema_accessor(self, schema: JsonObject) -> ToolSchemaAccessor:
        for accessor in self._schema_accessors:
            if accessor.can_handle(schema):
                return accessor
        raise ToolInteropError(
            f"No schema accessor matched: keys={list(schema.keys())}"
        )

    def get_call_accessor(self, call: JsonObject) -> ToolCallAccessor:
        for accessor in self._call_accessors:
            if accessor.can_handle(call):
                return accessor
        raise ToolInteropError(f"No call accessor matched: keys={list(call.keys())}")

    def get_result_accessor(self, result: Any) -> ToolResultAccessor:
        for accessor in self._result_accessors:
            if accessor.can_handle(result):
                return accessor
        raise ToolInteropError(f"No result accessor matched: type={type(result).__name__}")

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

    def inspect_result(self, result: Any) -> InspectedToolResult:
        accessor = self.get_result_accessor(result)
        payload = _safe_call(accessor, "get_payload", result)
        payload_kind = _safe_call(accessor, "get_payload_kind", result)
        display = _safe_call(accessor, "get_display", result)
        metadata = _safe_call(accessor, "get_metadata", result)
        raw_text = _safe_call(accessor, "get_text", result)
        text = raw_text if isinstance(raw_text, str) else ""
        raw_result_type = _safe_call(accessor, "get_result_type", result)
        return InspectedToolResult(
            raw=result,
            accessor=accessor,
            format_id=_format_id(accessor),
            result_type=raw_result_type if isinstance(raw_result_type, str) else None,
            payload=payload,
            payload_kind=payload_kind if isinstance(payload_kind, str) and payload_kind else self._infer_payload_kind(payload),
            text=text,
            display=display if isinstance(display, dict) else None,
            metadata=metadata if isinstance(metadata, dict) else {},
        )

    def sanitize_tool_call(self, call: JsonObject) -> JsonObject:
        """Sanitize a tool call before storing in history.

        Returns a sanitized copy with valid arguments. If the call format
        is not recognized or no sanitization is needed, returns the call unchanged.

        This is used to prevent corrupted JSON arguments from being stored
        in history and causing subsequent API calls to fail.
        """
        try:
            accessor = self.get_call_accessor(call)
        except ToolInteropError:
            return call
        return accessor.sanitize_call(call)

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
        """Get the parsed payload from a tool call using the accessor.

        Delegates to the accessor's get_payload method, which handles
        format-specific parsing (JSON for function calls, raw text for custom tools).
        """
        payload = _safe_call(accessor, "get_payload", call)
        if payload is not None:
            return payload
        return {}

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

    def _match_result_format(self, result: Any) -> Optional[str]:
        try:
            return self.inspect_result(result).format_id
        except ToolInteropError:
            for adapter in self._result_adapters:
                if adapter.can_handle(result):
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
            raise ToolInteropError(
                f"Could not determine schema format: keys={list(schema.keys())}"
            )
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
            raise ToolInteropError(
                f"Could not determine call format: keys={list(call.keys())}"
            )
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

    def _resolve_result_adapter(
        self,
        result: Any,
        *,
        adapters: Sequence[ToolResultAdapter],
        target_formats: Sequence[str],
    ) -> ToolResultAdapter:
        source_format = self._match_result_format(result)
        if source_format is None:
            raise ToolInteropError(
                f"Could not determine result format: type={type(result).__name__}"
            )
        if target_formats and source_format in target_formats:
            return _IdentityResultAdapter(source_format)

        direct = [
            adapter
            for adapter in adapters
            if adapter.source_format == source_format
            and adapter.can_handle(result)
            and (not target_formats or adapter.target_format in target_formats)
        ]
        if direct:
            return direct[0]

        chain = self._find_result_adapter_chain(
            source_format=source_format,
            target_formats=target_formats,
            adapters=adapters,
        )
        if chain is not None:
            return _ComposedResultAdapter(chain)

        raise ToolInteropError(
            f"No result adapter matched source={source_format!r} targets={list(target_formats)!r}"
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

    def _find_result_adapter_chain(
        self,
        *,
        source_format: str,
        target_formats: Sequence[str],
        adapters: Sequence[ToolResultAdapter],
    ) -> Optional[List[ToolResultAdapter]]:
        if not target_formats:
            return None
        queue: List[Tuple[str, List[ToolResultAdapter]]] = [(source_format, [])]
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
            converted.append(
                adapter.convert(
                    schema, target=target or ToolInteropTarget("tool_interop")
                )
            )
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
            converted.append(
                adapter.convert(
                    call, target=target or ToolInteropTarget("tool_interop")
                )
            )
        return converted

    def convert_tool_result(
        self,
        result: Any,
        *,
        adapters: Sequence[ToolResultAdapter] = (),
        target: Optional[ToolInteropTarget] = None,
        target_formats: Sequence[str] = (),
    ) -> Any:
        effective_adapters = _merge_ordered(adapters, self._result_adapters)
        requested_formats = list(target_formats)
        adapter = self._resolve_result_adapter(
            result,
            adapters=effective_adapters,
            target_formats=requested_formats,
        )
        return adapter.convert(
            result, target=target or ToolInteropTarget("tool_interop")
        )


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

    def get_payload(self, call: JsonObject) -> Any:
        """Parse and return the tool call arguments as a dict.

        Returns an empty dict if arguments are missing, not a dict/string,
        or if JSON parsing fails.
        """
        fn = call.get("function")
        if not isinstance(fn, dict):
            return {}
        arguments = fn.get("arguments")
        if isinstance(arguments, dict):
            return arguments
        if isinstance(arguments, str):
            try:
                parsed = json.loads(arguments)
                return parsed if isinstance(parsed, dict) else {}
            except (json.JSONDecodeError, Exception):
                return {}
        return {}

    def get_payload_kind(self, call: JsonObject) -> str:
        return "object"

    def get_payload_format(self, call: JsonObject) -> Optional[str]:
        return None

    def get_payload_metadata(self, call: JsonObject) -> JsonObject:
        return {}

    def sanitize_call(self, call: JsonObject) -> JsonObject:
        """Return a sanitized copy with valid JSON arguments.

        If the arguments field contains invalid JSON, returns a copy
        with arguments set to "{}". Otherwise returns the call unchanged.
        """
        fn = call.get("function")
        if not isinstance(fn, dict):
            return call
        arguments = fn.get("arguments")
        if isinstance(arguments, str):
            try:
                json.loads(arguments)
            except (json.JSONDecodeError, Exception):
                # Return copy with sanitized empty arguments
                return {
                    **call,
                    "function": {**fn, "arguments": "{}"},
                }
        return call


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

    def get_payload(self, call: JsonObject) -> Any:
        """Parse and return the tool call arguments as a dict.

        Returns an empty dict if arguments are missing, not a dict/string,
        or if JSON parsing fails.
        """
        arguments = call.get("arguments", "{}")
        if isinstance(arguments, dict):
            return arguments
        if isinstance(arguments, str):
            try:
                parsed = json.loads(arguments)
                return parsed if isinstance(parsed, dict) else {}
            except (json.JSONDecodeError, Exception):
                return {}
        return {}

    def get_payload_kind(self, call: JsonObject) -> str:
        return "object"

    def get_payload_format(self, call: JsonObject) -> Optional[str]:
        return None

    def get_payload_metadata(self, call: JsonObject) -> JsonObject:
        metadata = call.get("_metadata")
        return dict(metadata) if isinstance(metadata, dict) else {}

    def sanitize_call(self, call: JsonObject) -> JsonObject:
        """Return a sanitized copy with valid JSON arguments.

        If the arguments field contains invalid JSON, returns a copy
        with arguments set to "{}". Otherwise returns the call unchanged.
        """
        arguments = call.get("arguments")
        if isinstance(arguments, str):
            try:
                json.loads(arguments)
            except (json.JSONDecodeError, Exception):
                return {**call, "arguments": "{}"}
        return call


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

    def get_payload(self, call: JsonObject) -> Any:
        """Return the custom tool input as a string.

        Custom tool payloads are text, not JSON objects, so no parsing needed.
        """
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

    def sanitize_call(self, call: JsonObject) -> JsonObject:
        """Return the call unchanged.

        Custom tool payloads are text, not JSON, so no sanitization needed.
        """
        return call


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


class OpenAIResponsesFunctionToolSchemaToOpenAIChatToolSchema:
    source_format = OpenAIResponsesFunctionToolSchemaAccessor.format_id
    target_format = OpenAIChatToolSchemaAccessor.format_id
    priority = 100

    _schema_accessor = OpenAIResponsesFunctionToolSchemaAccessor()

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
        strict = schema.get("strict")
        if isinstance(strict, bool):
            fn["strict"] = strict

        return {"type": "function", "function": fn}


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
            if isinstance(maybe_item, dict) and self._call_accessor.can_handle(
                maybe_item
            ):
                item = maybe_item
            else:
                raise ToolInteropError("Unsupported Responses tool call object")

        call_id = self._call_accessor.get_call_id(item)
        name = self._call_accessor.get_tool_name(item)
        payload = self._call_accessor.get_payload(item)
        # Serialize payload to JSON string for OpenAI chat format
        if isinstance(payload, dict):
            arguments = json.dumps(payload)
        else:
            arguments = "{}"
        return {
            "id": call_id,
            "type": "function",
            "function": {
                "name": name,
                "arguments": arguments,
            },
        }


def _is_provider_native_tool_result(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("type") == PROVIDER_NATIVE_TOOL_RESULT_TYPE
        and isinstance(value.get("format"), str)
        and bool(value.get("format"))
    )


def _provider_native_tool_result_format(value: Any) -> Optional[str]:
    if not _is_provider_native_tool_result(value):
        return None
    fmt = value.get("format")
    return fmt if isinstance(fmt, str) else None


def _text_from_openai_chat_content(content: Any) -> str:
    if not isinstance(content, list):
        return ""
    text_parts: List[str] = []
    for part in content:
        if not isinstance(part, dict) or part.get("type") != "text":
            continue
        text = part.get("text")
        if isinstance(text, str) and text:
            text_parts.append(text)
    return "\n".join(text_parts)


def _text_from_openai_responses_output(output: Any) -> str:
    if not isinstance(output, list):
        return ""
    text_parts: List[str] = []
    for part in output:
        if not isinstance(part, dict):
            continue
        if part.get("type") not in {"input_text", "output_text", "text"}:
            continue
        text = part.get("text")
        if isinstance(text, str) and text:
            text_parts.append(text)
    return "\n".join(text_parts)


def _chat_image_url_to_responses_image_url(value: Any) -> Any:
    if isinstance(value, dict):
        url = value.get("url")
        if isinstance(url, str) and url:
            return url
        return dict(value)
    return value if isinstance(value, str) and value else None


def _openai_chat_content_to_responses_output(
    content: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for part in content:
        part_type = part.get("type")
        if part_type == "text":
            text = part.get("text")
            if isinstance(text, str) and text:
                output.append({"type": "input_text", "text": text})
            continue
        if part_type == "image_url":
            image_url = part.get("image_url")
            converted = _chat_image_url_to_responses_image_url(image_url)
            if converted is not None:
                output.append({"type": "input_image", "image_url": converted})
            continue
        if part_type in {"input_text", "input_image"}:
            output.append(dict(part))
    return output


def _openai_responses_output_to_chat_content(
    output: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    content: List[Dict[str, Any]] = []
    for part in output:
        part_type = part.get("type")
        if part_type in {"input_text", "output_text", "text"}:
            text = part.get("text")
            if isinstance(text, str) and text:
                content.append({"type": "text", "text": text})
            continue
        if part_type == "input_image":
            image_url = part.get("image_url")
            if isinstance(image_url, str) and image_url:
                content.append({"type": "image_url", "image_url": {"url": image_url}})
                continue
            if isinstance(image_url, dict) and image_url:
                content.append({"type": "image_url", "image_url": dict(image_url)})
            continue
        if part_type == "image_url":
            image_url = part.get("image_url")
            if isinstance(image_url, dict):
                content.append({"type": "image_url", "image_url": dict(image_url)})
            elif isinstance(image_url, str) and image_url:
                content.append({"type": "image_url", "image_url": {"url": image_url}})
    return content


def _anthropic_image_block_to_openai_chat_content(
    part: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    source = part.get("source")
    if not isinstance(source, dict):
        return None
    media_type = source.get("media_type")
    data = source.get("data")
    if not isinstance(media_type, str) or not media_type:
        return None
    if not isinstance(data, str) or not data:
        return None
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{media_type};base64,{data}"},
    }


def _anthropic_content_parts_to_openai_chat_content(content: Any) -> List[Dict[str, Any]]:
    parts: List[Dict[str, Any]] = []
    if isinstance(content, str):
        if content:
            parts.append({"type": "text", "text": content})
        return parts
    if not isinstance(content, list):
        return parts
    for part in content:
        if not isinstance(part, dict):
            continue
        part_type = part.get("type")
        if part_type == "text":
            text = part.get("text")
            if isinstance(text, str) and text:
                parts.append({"type": "text", "text": text})
            continue
        if part_type == "image":
            converted = _anthropic_image_block_to_openai_chat_content(part)
            if converted is not None:
                parts.append(converted)
            continue
        if part_type == "tool_result":
            parts.extend(
                _anthropic_content_parts_to_openai_chat_content(part.get("content"))
            )
    return parts


def _provider_native_tool_result_text(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    explicit_text = value.get("text")
    if isinstance(explicit_text, str):
        return explicit_text
    fmt = _provider_native_tool_result_format(value)
    if fmt == OPENAI_CHAT_TOOL_RESULT_FORMAT:
        return _text_from_openai_chat_content(value.get("content"))
    if fmt == OPENAI_RESPONSES_TOOL_RESULT_FORMAT:
        return _text_from_openai_responses_output(value.get("output"))
    if fmt == ANTHROPIC_MESSAGES_TOOL_RESULT_FORMAT:
        return _text_from_openai_chat_content(
            _anthropic_content_parts_to_openai_chat_content(value.get("content"))
        )
    return ""


def _provider_native_tool_result_image_content(value: Any) -> Optional[Dict[str, Any]]:
    inspected = _provider_native_tool_result_to_openai_chat_content(value)
    if inspected is None:
        return None
    for part in inspected:
        if not isinstance(part, dict) or part.get("type") != "image_url":
            continue
        image_url = part.get("image_url")
        if isinstance(image_url, dict) and image_url:
            return dict(image_url)
        if isinstance(image_url, str) and image_url:
            return {"url": image_url}
    return None


def _provider_native_tool_result_display(value: Any) -> Optional[JsonObject]:
    image_content = _provider_native_tool_result_image_content(value)
    if image_content is None:
        return None
    text = _provider_native_tool_result_text(value)
    display: JsonObject = {
        "type": "image",
        "content": image_content,
    }
    if isinstance(image_content.get("asset_ref"), dict):
        display["metadata"] = {
            "download_plugin_id": SESSION_ASSET_DOWNLOAD_PLUGIN_ID,
        }
    if isinstance(text, str) and text:
        display["content_text"] = text
        display["text_fallback"] = text
    return display


def _provider_native_tool_result_to_openai_chat_content(
    value: Any,
) -> Optional[List[Dict[str, Any]]]:
    fmt = _provider_native_tool_result_format(value)
    if fmt == OPENAI_CHAT_TOOL_RESULT_FORMAT:
        content = value.get("content") if isinstance(value, dict) else None
        if isinstance(content, list) and all(isinstance(item, dict) for item in content):
            return content
        return None
    if fmt == OPENAI_RESPONSES_TOOL_RESULT_FORMAT:
        output = value.get("output") if isinstance(value, dict) else None
        if not (isinstance(output, list) and all(isinstance(item, dict) for item in output)):
            return None
        return _openai_responses_output_to_chat_content(output)
    if fmt == ANTHROPIC_MESSAGES_TOOL_RESULT_FORMAT:
        content = value.get("content") if isinstance(value, dict) else None
        if isinstance(content, list) and all(isinstance(item, dict) for item in content):
            return _anthropic_content_parts_to_openai_chat_content(content)
    return None


def _provider_native_tool_result_to_openai_responses_output(
    value: Any,
) -> Optional[List[Dict[str, Any]]]:
    fmt = _provider_native_tool_result_format(value)
    if fmt == OPENAI_RESPONSES_TOOL_RESULT_FORMAT:
        output = value.get("output") if isinstance(value, dict) else None
        if isinstance(output, list) and all(isinstance(item, dict) for item in output):
            return output
        return None
    content = _provider_native_tool_result_to_openai_chat_content(value)
    if content is None:
        return None
    return _openai_chat_content_to_responses_output(content)


class PlainTextToolResultAccessor:
    format_id = CORE_TEXT_TOOL_RESULT_PLAIN_FORMAT_ID
    format = format_id
    priority = 1000

    def can_handle(self, result: Any) -> bool:
        return True

    def get_result_type(self, result: Any) -> str:
        return CORE_TOOL_RESULT_TYPE

    def get_payload(self, result: Any) -> str:
        return self.get_text(result)

    def get_payload_kind(self, result: Any) -> str:
        return "text"

    def get_text(self, result: Any) -> str:
        if result is None:
            return ""
        return result if isinstance(result, str) else str(result)

    def get_display(self, result: Any) -> JsonObject:
        return {"type": "text", "content": self.get_text(result)}

    def get_metadata(self, result: Any) -> JsonObject:
        return {}


class CoreTextToolResultAccessor:
    format_id = CORE_TEXT_TOOL_RESULT_FORMAT_ID
    format = format_id
    priority = 10

    def can_handle(self, result: Any) -> bool:
        return (
            isinstance(result, dict)
            and result.get("type") == CORE_TOOL_RESULT_TYPE
            and isinstance(result.get("text"), str)
        )

    def get_result_type(self, result: Any) -> str:
        return CORE_TOOL_RESULT_TYPE

    def get_payload(self, result: Any) -> str:
        return self.get_text(result)

    def get_payload_kind(self, result: Any) -> str:
        return "text"

    def get_text(self, result: Any) -> str:
        if not isinstance(result, dict):
            return ""
        text = result.get("text")
        return text if isinstance(text, str) else ""

    def get_display(self, result: Any) -> JsonObject:
        return {"type": "text", "content": self.get_text(result)}

    def get_metadata(self, result: Any) -> JsonObject:
        metadata = result.get("metadata") if isinstance(result, dict) else None
        return dict(metadata) if isinstance(metadata, dict) else {}


class ProviderNativeToolResultAccessor:
    format_id = PROVIDER_NATIVE_TOOL_RESULT_FORMAT_ID
    format = format_id
    priority = 200

    def can_handle(self, result: Any) -> bool:
        return _is_provider_native_tool_result(result)

    def get_result_type(self, result: Any) -> str:
        return PROVIDER_NATIVE_TOOL_RESULT_TYPE

    def get_payload(self, result: Any) -> Any:
        if not isinstance(result, dict):
            return None
        if isinstance(result.get("content"), list):
            return result.get("content")
        if isinstance(result.get("output"), list):
            return result.get("output")
        return result.get("text")

    def get_payload_kind(self, result: Any) -> str:
        payload = self.get_payload(result)
        if isinstance(payload, list):
            return "array"
        if isinstance(payload, dict):
            return "object"
        return "text"

    def get_text(self, result: Any) -> str:
        return _provider_native_tool_result_text(result)

    def get_display(self, result: Any) -> Optional[JsonObject]:
        return _provider_native_tool_result_display(result)

    def get_metadata(self, result: Any) -> JsonObject:
        metadata = result.get("metadata") if isinstance(result, dict) else None
        return dict(metadata) if isinstance(metadata, dict) else {}


class OpenAIChatToolResultAccessor:
    format_id = OPENAI_CHAT_TOOL_RESULT_FORMAT_ID
    format = format_id
    priority = 50

    def can_handle(self, result: Any) -> bool:
        return _provider_native_tool_result_format(result) == OPENAI_CHAT_TOOL_RESULT_FORMAT

    def get_result_type(self, result: Any) -> str:
        return PROVIDER_NATIVE_TOOL_RESULT_TYPE

    def get_payload(self, result: Any) -> Any:
        if not isinstance(result, dict):
            return None
        return result.get("content")

    def get_payload_kind(self, result: Any) -> str:
        return "array"

    def get_text(self, result: Any) -> str:
        return _provider_native_tool_result_text(result)

    def get_display(self, result: Any) -> Optional[JsonObject]:
        return _provider_native_tool_result_display(result)

    def get_metadata(self, result: Any) -> JsonObject:
        metadata = result.get("metadata") if isinstance(result, dict) else None
        return dict(metadata) if isinstance(metadata, dict) else {}


class OpenAIResponsesToolResultAccessor:
    format_id = OPENAI_RESPONSES_TOOL_RESULT_FORMAT_ID
    format = format_id
    priority = 50

    def can_handle(self, result: Any) -> bool:
        return _provider_native_tool_result_format(result) == OPENAI_RESPONSES_TOOL_RESULT_FORMAT

    def get_result_type(self, result: Any) -> str:
        return PROVIDER_NATIVE_TOOL_RESULT_TYPE

    def get_payload(self, result: Any) -> Any:
        if not isinstance(result, dict):
            return None
        return result.get("output")

    def get_payload_kind(self, result: Any) -> str:
        return "array"

    def get_text(self, result: Any) -> str:
        return _provider_native_tool_result_text(result)

    def get_display(self, result: Any) -> Optional[JsonObject]:
        return _provider_native_tool_result_display(result)

    def get_metadata(self, result: Any) -> JsonObject:
        metadata = result.get("metadata") if isinstance(result, dict) else None
        return dict(metadata) if isinstance(metadata, dict) else {}


class AnthropicMessagesToolResultAccessor:
    format_id = ANTHROPIC_MESSAGES_TOOL_RESULT_FORMAT_ID
    format = format_id
    priority = 50

    def can_handle(self, result: Any) -> bool:
        return _provider_native_tool_result_format(result) == ANTHROPIC_MESSAGES_TOOL_RESULT_FORMAT

    def get_result_type(self, result: Any) -> str:
        return PROVIDER_NATIVE_TOOL_RESULT_TYPE

    def get_payload(self, result: Any) -> Any:
        if not isinstance(result, dict):
            return None
        return result.get("content")

    def get_payload_kind(self, result: Any) -> str:
        return "array"

    def get_text(self, result: Any) -> str:
        return _provider_native_tool_result_text(result)

    def get_display(self, result: Any) -> Optional[JsonObject]:
        return _provider_native_tool_result_display(result)

    def get_metadata(self, result: Any) -> JsonObject:
        metadata = result.get("metadata") if isinstance(result, dict) else None
        return dict(metadata) if isinstance(metadata, dict) else {}


class PlainTextToolResultToCoreTextToolResult:
    source_format = CORE_TEXT_TOOL_RESULT_PLAIN_FORMAT_ID
    target_format = CORE_TEXT_TOOL_RESULT_FORMAT_ID
    priority = 10

    _accessor = PlainTextToolResultAccessor()

    def can_handle(self, result: Any) -> bool:
        return self._accessor.can_handle(result)

    def convert(self, result: Any, *, target: ToolInteropTarget) -> JsonObject:
        _ = target
        return {
            "type": CORE_TOOL_RESULT_TYPE,
            "text": self._accessor.get_text(result),
        }


class OpenAIChatToolResultToOpenAIResponsesToolResult:
    source_format = OPENAI_CHAT_TOOL_RESULT_FORMAT_ID
    target_format = OPENAI_RESPONSES_TOOL_RESULT_FORMAT_ID
    priority = 100

    _accessor = OpenAIChatToolResultAccessor()

    def can_handle(self, result: Any) -> bool:
        return self._accessor.can_handle(result)

    def convert(self, result: Any, *, target: ToolInteropTarget) -> JsonObject:
        _ = target
        content = _provider_native_tool_result_to_openai_chat_content(result) or []
        return {
            "type": PROVIDER_NATIVE_TOOL_RESULT_TYPE,
            "format": OPENAI_RESPONSES_TOOL_RESULT_FORMAT,
            "output": _openai_chat_content_to_responses_output(content),
            "text": _provider_native_tool_result_text(result),
        }


class OpenAIResponsesToolResultToOpenAIChatToolResult:
    source_format = OPENAI_RESPONSES_TOOL_RESULT_FORMAT_ID
    target_format = OPENAI_CHAT_TOOL_RESULT_FORMAT_ID
    priority = 100

    _accessor = OpenAIResponsesToolResultAccessor()

    def can_handle(self, result: Any) -> bool:
        return self._accessor.can_handle(result)

    def convert(self, result: Any, *, target: ToolInteropTarget) -> JsonObject:
        _ = target
        output = _provider_native_tool_result_to_openai_responses_output(result) or []
        return {
            "type": PROVIDER_NATIVE_TOOL_RESULT_TYPE,
            "format": OPENAI_CHAT_TOOL_RESULT_FORMAT,
            "content": _openai_responses_output_to_chat_content(output),
            "text": _provider_native_tool_result_text(result),
        }


class AnthropicMessagesToolResultToOpenAIChatToolResult:
    source_format = ANTHROPIC_MESSAGES_TOOL_RESULT_FORMAT_ID
    target_format = OPENAI_CHAT_TOOL_RESULT_FORMAT_ID
    priority = 50

    _accessor = AnthropicMessagesToolResultAccessor()

    def can_handle(self, result: Any) -> bool:
        return self._accessor.can_handle(result)

    def convert(self, result: Any, *, target: ToolInteropTarget) -> JsonObject:
        _ = target
        return {
            "type": PROVIDER_NATIVE_TOOL_RESULT_TYPE,
            "format": OPENAI_CHAT_TOOL_RESULT_FORMAT,
            "content": _provider_native_tool_result_to_openai_chat_content(result) or [],
            "text": _provider_native_tool_result_text(result),
        }


# Fallback-only registry for contexts where no request/runtime interop bundle exists.
# Runtime code should prefer ``get_registry_from_context(...)`` so core-owned,
# config-specific contributions are respected.
DEFAULT_TOOL_INTEROP_REGISTRY = ToolInteropRegistry(
    schema_adapters=[
        OpenAIChatToolSchemaToOpenAIResponsesToolSchema(),
        OpenAIResponsesFunctionToolSchemaToOpenAIChatToolSchema(),
    ],
    call_adapters=[OpenAIResponsesToolCallToOpenAIChatToolCall()],
    result_adapters=[
        PlainTextToolResultToCoreTextToolResult(),
        OpenAIChatToolResultToOpenAIResponsesToolResult(),
        OpenAIResponsesToolResultToOpenAIChatToolResult(),
        AnthropicMessagesToolResultToOpenAIChatToolResult(),
    ],
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
    result_accessors=[
        CoreTextToolResultAccessor(),
        OpenAIChatToolResultAccessor(),
        OpenAIResponsesToolResultAccessor(),
        AnthropicMessagesToolResultAccessor(),
        ProviderNativeToolResultAccessor(),
        PlainTextToolResultAccessor(),
    ],
)
