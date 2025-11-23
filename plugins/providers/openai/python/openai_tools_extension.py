from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import json


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
    target_provider: str = "openai_compatible"

    # ---- Config/UI ----
    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return []

    # ---- Init/State ----
    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        tools = config.get("tools")
        return {**state, "_openai_tools": tools if isinstance(tools, list) else []}

    def update_state(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, **updates}

    # ---- Stateless transforms ----
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Copy assistant metadata.tool_calls to native.tool_calls as-is and map tool.tool_call_id
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
            elif role == "assistant":
                tcs = md.get("tool_calls")
                if isinstance(tcs, list) and tcs:
                    nm["tool_calls"] = tcs
            out.append(nm)
        return out

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Copy provider-native tool_calls directly into core metadata when aligned (no transformation)."""
        if len(messages) != len(native_messages):
            return messages

        enhanced: List[Dict[str, Any]] = []
        for msg, native in zip(messages, native_messages):
            tool_calls = native.get("tool_calls") if isinstance(native, dict) else None
            if tool_calls:
                #print("new tool calls:", tool_calls)
                metadata = dict(msg.get("metadata") or {})
                metadata["tool_calls"] = tool_calls
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
            payload = {**payload, "tools": tools, **({"tool_choice": payload.get("tool_choice", "auto")})}
        return {**state, "request": {**request, "payload": payload}}

    # ---- Streaming helpers ----
    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:
        if "choices" in native_chunk and native_chunk["choices"]:
            return dict(native_chunk["choices"][0])
        return {}

    def process_delta(
        self,
        delta: Dict[str, Any],
        current_partial: Dict[str, Any] | None = None,
        current_final: Dict[str, Any] | None = None,
        accumulated: Dict[str, Any] | None = None,
    ):
        """Accumulate tool_calls across deltas; merge into current partial/final and accumulator.
        Returns (new_partial, new_final, new_accumulated).
        """
        accumulated = accumulated or {"tool_calls": []}
        
        #print(f"process_delta: {delta}, partial: {current_partial}, final: {current_final}, accumulated: {accumulated}")

        # Full message update
        if "message" in delta and current_final is not None:
            msg = delta.get("message") or {}
            if isinstance(msg.get("tool_calls"), list) and msg["tool_calls"]:
                merged_final = dict(current_final)
                merged_final["tool_calls"] = [
                    *(current_final.get("tool_calls") or []), *msg["tool_calls"]
                ]
                # also accumulate
                acc_tc = list(accumulated.get("tool_calls") or [])
                acc_tc.extend(msg["tool_calls"])
                #print("accumulate:", accumulated, acc_tc)
                accumulated = {**accumulated, "tool_calls": acc_tc}
                return current_partial, merged_final, accumulated
            return current_partial, current_final, accumulated

        # Delta fragment: merge into partial and/or final when present
        if "delta" in delta:
            d = delta.get("delta") or {}
            if isinstance(d.get("tool_calls"), list) and d["tool_calls"]:
                acc_tc = list(accumulated.get("tool_calls") or [])
                acc_tc.extend(d["tool_calls"])
                #print("accumulate:", accumulated, acc_tc)
                accumulated = {**accumulated, "tool_calls": acc_tc}
                new_partial = current_partial
                new_final = current_final
                if current_final is not None:
                    merged_final = dict(current_final)
                    merged_final["tool_calls"] = [
                        *(current_final.get("tool_calls") or []), *d["tool_calls"]
                    ]
                    new_final = merged_final
                return new_partial, new_final, accumulated
            return current_partial, current_final, accumulated

        return current_partial, current_final, accumulated

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        state: Dict[str, Any],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        delta = self.extract_delta(native_chunk or {})

        new_partial_messages = partial_messages
        new_final_messages = final_messages
        new_native_messages = native_messages
        accumulated = state.get("partial", {})
        
        if len(final_messages) > 0:
            new_partial_message, new_final_message, accumulated = self.process_delta(
                delta=delta, current_final=final_messages[-1], accumulated=accumulated
            )
            new_final_messages = [*(final_messages[:-1] or []), new_final_message]
            new_native_messages = [*(native_messages[:-1] or []), new_final_message]

        if len(partial_messages) > 0:
            new_partial_message, new_final_message, accumulated = self.process_delta(
                delta=delta, current_partial=partial_messages[-1], accumulated=accumulated
            )
            # Do not write tool_calls into metadata for partial messages; emit native-only
            new_partial_messages = [*(partial_messages[:-1] or []), new_partial_message]

        #print(f"partials: {new_partial_messages}, final: {new_final_messages}, accumulated: {accumulated}")

        return new_partial_messages, new_final_messages, new_native_messages, {**state, "partial": accumulated}

    # ---- Finalize: attach accumulated tool_calls to last final and native ----
    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        accumulated = state.get("partial") or {}
        tc_list = accumulated.get("tool_calls") if isinstance(accumulated, dict) else None
        if tc_list:
            if final_messages:
                last_final = dict(final_messages[-1])
                last_final["tool_calls"] = [*(last_final.get("tool_calls") or []), *tc_list]
                final_messages = [*final_messages[:-1], last_final]
            if native_messages:
                last_native = dict(native_messages[-1])
                last_native["tool_calls"] = [*(last_native.get("tool_calls") or []), *tc_list]
                native_messages = [*native_messages[:-1], last_native]
                
        #print("Finalized messages:", final_messages)
        return final_messages, native_messages, state
