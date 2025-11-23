"""Ollama thinking extension for OpenAI-compatible provider.

Adds `think: true` to requests when enabled and extracts reasoning/thinking
content from Ollama's OpenAI-compatible responses, exposing it in metadata.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


class OllamaThinkingExtension:
    """Minimal provider extension to enable Ollama thinking.

    Responsibilities:
    - Add "think": true to the request payload when enabled via config.
    - Accumulate reasoning text from streaming chunks.
    - Attach reasoning into metadata on final assistant messages.
    - Emit partial reasoning updates during streaming via metadata.
    """

    name: str = "ollama_thinking"
    version: str = "0.1.0"
    target_provider: str = "openai_compatible"

    def get_config_schema(self) -> Dict[str, Any]:
        return {"think": {"type": "boolean", "required": False, "default": False}}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return []

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        enabled = bool(config.get("think"))
        if not enabled:
            return state
        return {
            **state,
            "ollama_think_enabled": True,
            "ollama_reasoning": state.get("ollama_reasoning", ""),
        }

    def update_state(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        # No special runtime UI state; passthrough.
        return {**state, **updates}

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Stateless identity transform.
        return list(native_messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Stateless identity transform.
        return list(messages)

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not state.get("ollama_think_enabled"):
            return state
        request = state.get("request") or {}
        payload = dict(request.get("payload", {}))
        payload["think"] = True
        new_request = {**request, "payload": payload}
        return {**state, "request": new_request}

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        if not state.get("ollama_think_enabled") or native_chunk is None:
            return partial_messages, final_messages, native_messages, state

        reasoning_buffer = state.get("ollama_reasoning", "")
        new_reasoning_fragment = ""

        choices = native_chunk.get("choices") or []
        if choices:
            choice = choices[0] or {}
            message = choice.get("message") or {}
            delta = choice.get("delta") or {}
            if "reasoning" in message:
                new_reasoning_fragment = str(message.get("reasoning") or "")
            if "reasoning" in delta:
                new_reasoning_fragment = str(delta.get("reasoning") or "")

        if new_reasoning_fragment:
            reasoning_buffer = f"{reasoning_buffer}{new_reasoning_fragment}"

            # Attach incremental reasoning to the latest partial, or create a new one
            if partial_messages:
                base = dict(partial_messages[-1])
                prefix = partial_messages[:-1]
            else:
                base = {"role": "assistant", "content": ""}
                prefix = []
            metadata = dict(base.get("metadata") or {})
            metadata["reasoning"] = reasoning_buffer
            base["metadata"] = metadata
            partial_messages = [*prefix, base]

        # Ensure any final messages for this chunk expose the
        # accumulated reasoning so the final assistant message
        # in streaming mode carries it.
        if reasoning_buffer and final_messages:
            new_finals: List[Dict[str, Any]] = []
            for msg in final_messages:
                md = dict(msg.get("metadata") or {})
                md["reasoning"] = reasoning_buffer
                new_finals.append({**msg, "metadata": md})
            final_messages = new_finals

        new_state = {
            **{k: v for k, v in state.items() if k != "ollama_reasoning"},
            "ollama_reasoning": reasoning_buffer,
        }
        return partial_messages, final_messages, native_messages, new_state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        if not state.get("ollama_think_enabled"):
            return final_messages, native_messages, state

        reasoning_text = state.get("ollama_reasoning", "")

        def _collect_reasoning(msgs: List[Dict[str, Any]]) -> str:
            parts: List[str] = []
            for m in msgs:
                if not isinstance(m, dict):
                    continue
                # Direct reasoning on the message dict
                if "reasoning" in m:
                    parts.append(str(m.get("reasoning") or ""))
                # Reasoning nested under a "message" field
                inner = m.get("message")
                if isinstance(inner, Dict) and "reasoning" in inner:
                    parts.append(str(inner.get("reasoning") or ""))
                # Reasoning inside a chat completion object from Ollama/OpenAI
                choices = m.get("choices") if isinstance(m.get("choices"), list) else None
                if choices:
                    choice0 = choices[0] if choices else None
                    if isinstance(choice0, dict):
                        inner_msg = choice0.get("message")
                        if isinstance(inner_msg, dict) and "reasoning" in inner_msg:
                            parts.append(str(inner_msg.get("reasoning") or ""))
            return "".join(parts)

        if not reasoning_text:
            reasoning_text = _collect_reasoning(final_messages) or _collect_reasoning(
                native_messages
            )

        if not reasoning_text:
            return final_messages, native_messages, state

        new_finals: List[Dict[str, Any]] = []
        for msg in final_messages:
            metadata = dict(msg.get("metadata") or {})
            metadata["reasoning"] = reasoning_text
            new_msg = {**msg, "metadata": metadata}
            new_finals.append(new_msg)

        new_state = {**state, "ollama_reasoning": reasoning_text}
        return new_finals, native_messages, new_state
