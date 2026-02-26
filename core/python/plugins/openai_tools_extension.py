from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


class OpenAIToolsExtension:
    """OpenAI tools extension for OpenAI-compatible provider.

    Mirrors the structure of the thinking extension in a functional style:
    - Adds tool schemas to the request payload (from config["tools"])
    - Maps outbound tool messages to include provider-native tool_call_id
    - Accumulates tool_calls across streaming chunks
    - Attaches normalized tool_calls into assistant metadata at finalize
    - Adds tool_calls to core messages during from_native_messages when aligned
    """

    name: str = "openai_tools"
    version: str = "0.2.0"

    # ---- Config/UI ----
    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return []

    # ---- Models / capabilities ----
    # Uses adapter default get_models (no-op on models)

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Identify this extension in the global tag set."""
        return ["ext:openai_tools"]

    def required_tags(self) -> List[str]:
        """Require tool-calling support from the provider/models."""
        return ["supports_tools", "provider:openai_compatible"]

    # ---- Init/State ----
    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:

        tools = config.get("tools")
        return {**state, "_openai_tools": tools if isinstance(tools, list) else []}

    # ---- Stateless transforms ----
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Copy assistant metadata.tool_calls to native.tool_calls as-is and map tool.tool_call_id.
        # Also propagate tool-related metadata (tool_plugin, tool_name, display) into
        # provider-native _metadata so that it can be preserved in native history.
        if len(messages) != len(native_messages):
            return native_messages
        out: List[Dict[str, Any]] = []
        for msg, native in zip(messages, native_messages):
            nm = dict(native)
            role = msg.get("role")
            md = msg.get("metadata") or {}
            if role == "tool":
                tcid = md.get("tool_call_id")
                if tcid:
                    nm["tool_call_id"] = tcid
                # Optional tool metadata for display and reconstruction
                extra: Dict[str, Any] = {}
                tool_plugin = md.get("tool_plugin")
                tool_name = md.get("tool_name")
                display = md.get("display")
                if tool_plugin is not None:
                    extra["tool_plugin"] = tool_plugin
                if tool_name is not None:
                    extra["tool_name"] = tool_name
                if display is not None:
                    extra["display"] = display
                if extra:
                    base_meta = nm.get("_metadata") or {}
                    merged = {**base_meta, **extra} if isinstance(base_meta, dict) else extra
                    nm["_metadata"] = merged
            elif role == "assistant":
                tcs = md.get("tool_calls")
                if isinstance(tcs, list) and tcs:
                    nm["tool_calls"] = tcs
            out.append(nm)
        return out

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Copy provider-native tool_calls and _metadata into core metadata when aligned."""
        if len(messages) != len(native_messages):
            return messages

        enhanced: List[Dict[str, Any]] = []
        for msg, native in zip(messages, native_messages):
            metadata = dict(msg.get("metadata") or {})
            tool_calls = native.get("tool_calls") if isinstance(native, dict) else None
            if tool_calls:
                metadata["tool_calls"] = tool_calls
            extra = native.get("_metadata") if isinstance(native, dict) else None
            if isinstance(extra, dict) and extra:
                metadata.update(extra)
            # Preserve provider-native tool_call_id on core messages so that
            # operations that rebuild from native history (e.g. slice_session,
            # modify_message) keep the explicit link between assistant
            # tool_calls[*].id and role=="tool" messages.
            tcid = native.get("tool_call_id") if isinstance(native, dict) else None
            if isinstance(tcid, str) and tcid and "tool_call_id" not in metadata:
                metadata["tool_call_id"] = tcid
            if metadata:
                enhanced.append({**msg, "metadata": metadata})
            else:
                enhanced.append(msg)
        return enhanced

    # ---- Request init ----
    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        request = state.get("request") or {}
        payload = dict(request.get("payload", {}))
        tools: List[Dict[str, Any]] = state.get("_openai_tools") or []
        if tools:
            payload = {
                **payload,
                "tools": tools,
                **({"tool_choice": payload.get("tool_choice", "auto")}),
            }
        return {**state, "request": {**request, "payload": payload}}

    # ---- Streaming helpers ----
    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:
        if "choices" in native_chunk and native_chunk["choices"]:
            return native_chunk["choices"][0]
        return {}

    def process_delta(
        self,
        delta: Dict[str, Any],
        current_partial: Dict[str, Any] | None = None,
        accumulated: Dict[str, Any] | None = None,
    ):
        """Accumulate tool_calls across deltas into the shared accumulator.

        Updates only the accumulator (``state["partial"]``) and leaves
        partial/final messages to the provider.
        """
        accumulated = accumulated or {"tool_calls": []}

        d = delta.get("message") or delta.get("delta") or {}

        if isinstance(d.get("tool_calls"), list) and d["tool_calls"]:
            acc_tc = list(accumulated.get("tool_calls") or [])

            # Merge tool_calls by index (streaming sends fragments with index field)
            for tc_delta in d["tool_calls"]:
                index = tc_delta.get("index", len(acc_tc))
                # Ensure list is long enough
                while len(acc_tc) <= index:
                    acc_tc.append({})
                # Merge this delta into the tool_call at the given index
                existing = acc_tc[index]
                # Merge top-level fields
                for key in ["id", "type"]:
                    if key in tc_delta:
                        existing[key] = tc_delta[key]
                # Merge function object
                if "function" in tc_delta:
                    if "function" not in existing:
                        existing["function"] = {}
                    func_delta = tc_delta["function"]
                    if "name" in func_delta:
                        existing["function"]["name"] = func_delta["name"]
                    if "arguments" in func_delta:
                        # Accumulate arguments (they're sent as string fragments)
                        existing["function"]["arguments"] = (
                            existing["function"].get("arguments", "")
                            + func_delta["arguments"]
                        )
                acc_tc[index] = existing

            new_accumulated = {**accumulated, "tool_calls": acc_tc}
            return current_partial, new_accumulated

        return current_partial, accumulated

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Update the accumulator with tool_calls for each streaming chunk.

        This extension does not emit its own finals or mutate history; it only
        enriches the shared accumulator so that the provider's final message
        (built from state["partial"]) carries the full tool_calls list.
        """
        delta = self.extract_delta(native_chunk or {})

        new_partial_messages = partial_messages
        accumulated = state.get("partial", {})

        if partial_messages:
            _current_partial = partial_messages[-1]
            _unused_partial, accumulated = self.process_delta(
                delta=delta,
                current_partial=_current_partial,
                accumulated=accumulated,
            )

        return (
            new_partial_messages,
            final_messages,
            native_messages,
            {**state, "partial": accumulated},
        )

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return final_messages, native_messages, state
