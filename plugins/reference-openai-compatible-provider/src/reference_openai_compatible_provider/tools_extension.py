from __future__ import annotations

from typing import Any

from agent_core.tool_interop import (
    OpenAIChatToolCallAccessor,
    OpenAIChatToolSchemaAccessor,
    ToolInteropTarget,
    get_registry_from_context,
    get_schema_target_formats_from_context,
)
from agent_core.types import ProviderExtensionPlugin

from reference_openai_compatible_provider._extension_accumulator import (
    AccumulatorExtensionMixin,
    _merge_delta_content,
)


def _merge_shallow(
    current: dict[str, Any],
    delta: dict[str, Any],
    *,
    exclude: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {**current, **{k: v for k, v in delta.items() if k not in exclude}}


def _merge_tool_call(current: dict[str, Any], delta: dict[str, Any]) -> dict[str, Any]:
    out = _merge_shallow(current, delta, exclude=("index", "function"))
    func_delta = delta.get("function")
    if isinstance(func_delta, dict):
        func_current = out.get("function")
        func_current = func_current if isinstance(func_current, dict) else {}
        out["function"] = _merge_delta_content(
            func_current,
            func_delta,
            override=("name",),
            accumulate=("arguments",),
        )
    return out


def _merge_tool_calls(
    existing: list[dict[str, Any]], deltas: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    merged = [dict(tc) for tc in existing]
    for d in deltas:
        if not isinstance(d, dict):
            continue
        i = d.get("index")
        i = i if isinstance(i, int) and i >= 0 else len(merged)
        while len(merged) <= i:
            merged.append({})
        # If the delta carries a different id than what's already at this
        # index, it's a new tool call (some providers send multiple complete
        # tool calls in a single chunk with the same index).  Append it
        # instead of merging into the existing slot.
        delta_id = d.get("id")
        current_id = merged[i].get("id")
        if (
            isinstance(delta_id, str)
            and delta_id
            and isinstance(current_id, str)
            and current_id
            and delta_id != current_id
        ):
            merged.append(_merge_tool_call({}, d))
        else:
            merged[i] = _merge_tool_call(merged[i], d)
    return merged


class OpenAICompatibleToolsExtension(
    AccumulatorExtensionMixin, ProviderExtensionPlugin
):
    name = "reference_openai_tools"
    version = "0.1.0"

    def required_tags(self) -> list[str]:
        return ["provider:openai_compatible", "supports_tools"]

    def accepted_tool_schema_formats(
        self,
        config: dict[str, Any],
        state: dict[str, Any] | None = None,
    ) -> list[str]:
        return [OpenAIChatToolSchemaAccessor.format_id]

    def emitted_tool_call_formats(
        self,
        config: dict[str, Any],
        state: dict[str, Any] | None = None,
    ) -> list[str]:
        return [OpenAIChatToolCallAccessor.format_id]

    def init(self, config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        tools = config.get("tools")
        return {**state, "_tools": tools if isinstance(tools, list) else []}

    def initialize_request(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ):
        tools = state.get("_tools") or []
        if not tools:
            return native_messages, state

        req = state.get("request") or {}
        payload = dict(req.get("payload") or {})
        if "tools" not in payload:
            registry = get_registry_from_context(context)
            target_formats = get_schema_target_formats_from_context(context)
            if not target_formats:
                target_formats = self.accepted_tool_schema_formats(
                    state.get("config") or {},
                    state,
                )
            payload["tools"] = registry.convert_schemas(
                [tool for tool in tools if isinstance(tool, dict)],
                target=ToolInteropTarget("openai.chat_completions"),
                target_formats=target_formats,
            )
            payload["tool_choice"] = payload.get("tool_choice", "auto")
        return native_messages, {**state, "request": {**req, "payload": payload}}

    def extract_delta(self, native_chunk: dict[str, Any]) -> dict[str, Any]:
        choice0 = (native_chunk.get("choices") or [{}])[0]
        return choice0 if isinstance(choice0, dict) else {}

    def process_delta(self, delta: dict[str, Any], accumulated: dict[str, Any] | None):
        base = accumulated or {}
        d = delta.get("delta") or delta.get("message") or {}
        tool_deltas = d.get("tool_calls") if isinstance(d, dict) else None
        if not isinstance(tool_deltas, list) or not tool_deltas:
            return None, base

        existing = (
            base.get("tool_calls") if isinstance(base.get("tool_calls"), list) else []
        )
        merged = _merge_tool_calls(
            existing=[tc for tc in existing if isinstance(tc, dict)],
            deltas=[tc for tc in tool_deltas if isinstance(tc, dict)],
        )
        new_acc = {**base, "tool_calls": merged}
        return {"tool_calls": merged}, new_acc

    def to_native_messages(
        self, messages: list[dict[str, Any]], native_messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if len(messages) != len(native_messages):
            return native_messages

        out: list[dict[str, Any]] = []
        for msg, nm in zip(messages, native_messages):
            nm = dict(nm)
            md = msg.get("metadata") or {}

            if msg.get("role") == "assistant" and isinstance(
                md.get("tool_calls"), list
            ):
                nm["tool_calls"] = md["tool_calls"]

            if msg.get("role") == "tool" and isinstance(md, dict):
                if isinstance(md.get("tool_call_id"), str):
                    nm["tool_call_id"] = md["tool_call_id"]
                # Re-add display/tool_plugin/tool_name into _metadata for tool
                # messages. The provider pops display from the generic
                # _metadata carry, so the extension must re-add it here to
                # preserve it across native-history rebuilds (matching the
                # OpenRouter tools extension pattern).
                extra: dict[str, Any] = {}
                for key in ("tool_plugin", "tool_name", "display"):
                    value = md.get(key)
                    if value is not None:
                        extra[key] = value
                if extra:
                    base_meta = nm.get("_metadata")
                    merged = (
                        {**base_meta, **extra} if isinstance(base_meta, dict) else extra
                    )
                    nm["_metadata"] = merged

            out.append(nm)
        return out

    def from_native_messages(
        self, native_messages: list[dict[str, Any]], messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if len(messages) != len(native_messages):
            return messages

        out: list[dict[str, Any]] = []
        for msg, nm in zip(messages, native_messages):
            md = dict(msg.get("metadata") or {})
            if isinstance(nm.get("tool_calls"), list) and nm["tool_calls"]:
                md["tool_calls"] = nm["tool_calls"]
            if isinstance(nm.get("tool_call_id"), str) and nm["tool_call_id"]:
                md.setdefault("tool_call_id", nm["tool_call_id"])
            out.append({**msg, "metadata": md})
        return out

    def finalize(
        self,
        final_messages: list[dict[str, Any]],
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ):
        accumulator = state.get("accumulator")
        if isinstance(accumulator, dict):
            tool_calls = accumulator.get("tool_calls")
            if isinstance(tool_calls, list):
                registry = get_registry_from_context(context)
                accumulator["tool_calls"] = [
                    registry.sanitize_tool_call(tool_call)
                    for tool_call in tool_calls
                    if isinstance(tool_call, dict)
                ]
        return final_messages, native_messages, state
