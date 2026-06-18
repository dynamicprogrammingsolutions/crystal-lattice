from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


class _ReasoningExtensionExample:
    """Minimal example of storing reasoning in provider-native ``_metadata``."""

    name = "reasoning_example"
    version = "0.0.0"

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        accumulator = state.get("accumulator")
        if not isinstance(accumulator, dict) or not isinstance(native_chunk, dict):
            return partial_messages, final_messages, native_messages, state

        frag = native_chunk.get("reasoning")
        if not isinstance(frag, str) or not frag:
            return partial_messages, final_messages, native_messages, state

        internal = (
            accumulator.get("_metadata")
            if isinstance(accumulator.get("_metadata"), dict)
            else {}
        )
        prior = internal.get("reasoning")
        prior_text = prior if isinstance(prior, str) else ""
        internal = {**internal, "reasoning": prior_text + frag}

        return (
            partial_messages,
            final_messages,
            native_messages,
            {**state, "accumulator": {**accumulator, "_metadata": internal}},
        )

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for native, msg in zip(native_messages, messages):
            md = dict(msg.get("metadata") or {})
            internal = (
                native.get("_metadata")
                if isinstance(native.get("_metadata"), dict)
                else {}
            )
            reasoning = internal.get("reasoning")
            if isinstance(reasoning, str) and reasoning:
                md["reasoning"] = reasoning
            out.append({**msg, "metadata": md})
        return out


class _ToolsExtensionExample:
    """Minimal example of mapping tool call fields to/from core metadata."""

    name = "tools_example"
    version = "0.0.0"

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not messages:
            return list(native_messages)

        out = list(native_messages)
        tail = out[-len(messages) :] if len(out) >= len(messages) else out
        for core_msg, native_msg in zip(messages, tail):
            if not isinstance(core_msg, dict) or not isinstance(native_msg, dict):
                continue
            md = core_msg.get("metadata") or {}
            if core_msg.get("role") == "assistant":
                tool_calls = md.get("tool_calls") if isinstance(md, dict) else None
                if isinstance(tool_calls, list) and tool_calls:
                    native_msg["tool_calls"] = tool_calls
            if core_msg.get("role") == "tool":
                tool_call_id = md.get("tool_call_id") if isinstance(md, dict) else None
                if isinstance(tool_call_id, str) and tool_call_id:
                    native_msg["tool_call_id"] = tool_call_id
        return out

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for native, msg in zip(native_messages, messages):
            md = dict(msg.get("metadata") or {})
            tool_calls = native.get("tool_calls")
            if isinstance(tool_calls, list) and tool_calls:
                md["tool_calls"] = tool_calls
            tool_call_id = native.get("tool_call_id")
            if isinstance(tool_call_id, str) and tool_call_id:
                md["tool_call_id"] = tool_call_id
            out.append({**msg, "metadata": md})
        return out


class _UsageExtensionExample:
    """Minimal example of attaching usage data via native ``_metadata``."""

    name = "usage_example"
    version = "0.0.0"

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        accumulator = state.get("accumulator")
        if not isinstance(accumulator, dict) or not isinstance(native_chunk, dict):
            return partial_messages, final_messages, native_messages, state

        usage = native_chunk.get("usage")
        if not isinstance(usage, dict) or not usage:
            return partial_messages, final_messages, native_messages, state

        internal = (
            accumulator.get("_metadata")
            if isinstance(accumulator.get("_metadata"), dict)
            else {}
        )
        internal = {**internal, "usage": usage}
        return (
            partial_messages,
            final_messages,
            native_messages,
            {**state, "accumulator": {**accumulator, "_metadata": internal}},
        )

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for native, msg in zip(native_messages, messages):
            md = dict(msg.get("metadata") or {})
            internal = (
                native.get("_metadata")
                if isinstance(native.get("_metadata"), dict)
                else {}
            )
            usage = internal.get("usage")
            if isinstance(usage, dict) and usage:
                md["usage"] = usage
            out.append({**msg, "metadata": md})
        return out


def test_reasoning_accumulates_into_partial_metadata() -> None:
    ext = _ReasoningExtensionExample()
    state = {"accumulator": {"role": "assistant", "content": "", "_metadata": {}}}

    _, _, _, state = ext.process_chunk({"reasoning": "Step 1. "}, [], [], [], state)
    _, _, _, state = ext.process_chunk({"reasoning": "Step 2."}, [], [], [], state)

    internal = state["accumulator"]["_metadata"]
    assert internal["reasoning"] == "Step 1. Step 2."


def test_reasoning_surfaces_from_native_metadata() -> None:
    ext = _ReasoningExtensionExample()

    native = [
        {"role": "assistant", "content": "Answer", "_metadata": {"reasoning": "R"}}
    ]
    core = [{"role": "assistant", "content": "Answer", "metadata": {}}]

    out = ext.from_native_messages(native, core)
    assert out[0]["metadata"]["reasoning"] == "R"


def test_tools_maps_tool_call_fields_round_trip() -> None:
    ext = _ToolsExtensionExample()

    tool_calls = [
        {
            "id": "c1",
            "type": "function",
            "function": {"name": "add", "arguments": '{"a": 1, "b": 2}'},
        }
    ]

    messages = [
        {"role": "assistant", "content": "", "metadata": {"tool_calls": tool_calls}},
        {"role": "tool", "content": "3", "metadata": {"tool_call_id": "c1"}},
    ]
    native = [
        {"role": "assistant", "content": ""},
        {"role": "tool", "content": "3"},
    ]

    native_out = ext.to_native_messages(messages, native)
    assert native_out[0]["tool_calls"][0]["function"]["name"] == "add"
    assert native_out[1]["tool_call_id"] == "c1"

    core_rebuilt = [
        {"role": "assistant", "content": "", "metadata": {}},
        {"role": "tool", "content": "3", "metadata": {}},
    ]
    out = ext.from_native_messages(native_out, core_rebuilt)
    assert out[0]["metadata"]["tool_calls"][0]["id"] == "c1"
    assert out[1]["metadata"]["tool_call_id"] == "c1"


def test_usage_attaches_via_internal_metadata() -> None:
    ext = _UsageExtensionExample()
    state = {"accumulator": {"role": "assistant", "content": "", "_metadata": {}}}

    native_chunk = {"usage": {"total_tokens": 10, "cost": 0.1}}
    _, _, _, new_state = ext.process_chunk(native_chunk, [], [], [], state)
    assert new_state["accumulator"]["_metadata"]["usage"]["total_tokens"] == 10

    native = [
        {
            "role": "assistant",
            "content": "Hi",
            "_metadata": {"usage": {"total_tokens": 10}},
        }
    ]
    core = [{"role": "assistant", "content": "Hi", "metadata": {}}]
    out = ext.from_native_messages(native, core)
    assert out[0]["metadata"]["usage"]["total_tokens"] == 10
